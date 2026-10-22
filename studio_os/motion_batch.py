"""Render reviewed scene plans through local ComfyUI; never substitute stills.

No publication or paid-service calls. Narration is an existing local audio file.
The workflow must be a tested ComfyUI API export with explicit input bindings.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, subprocess, time
from pathlib import Path
from urllib import request, parse


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args):
    return subprocess.check_output([str(x) for x in args], stderr=subprocess.STDOUT)


def probe(path):
    return json.loads(command(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path]))


def validate_job(job):
    if job.get('version') != 1 or job.get('motion_required') is not True:
        raise ValueError('A version 1 motion-required job is required')
    if not job.get('id') or not job.get('scenes'):
        raise ValueError('Missing job identity or scenes')
    text = ' '.join(s['narration'] for s in job['scenes'])
    if text.split() != job['narration'].split():
        raise ValueError('Scene narration differs from source')
    if hashlib.sha256(job['narration'].encode()).hexdigest() != job['narration_sha256']:
        raise ValueError('Source narration hash mismatch')
    ids = set()
    for scene in job['scenes']:
        if scene['id'] in ids or not scene.get('action') or not scene.get('prompt'):
            raise ValueError('Every scene needs a unique ID, action and prompt')
        if scene.get('character_present') is not False:
            raise ValueError('This batch contract supports object/environment scenes only; use registered character workflows for cast shots')
        ids.add(scene['id'])
    w,h = job['dimensions']
    if min(w,h)<256 or w%16 or h%16:
        raise ValueError('Dimensions must be multiples of 16, at least 256')


def build_workflow(template, bindings, scene, dimensions, seconds, seed):
    workflow=copy.deepcopy(template)
    # Bind only declared inputs; no invented model names or silent defaults.
    required={'prompt','width','height','length','seed','fps'}
    if set(bindings)!=required:
        raise ValueError('Bindings must define prompt, width, height, length, seed and fps')
    fps=16
    values=dict(prompt=scene['prompt'],width=dimensions[0],height=dimensions[1],
                length=4*math.ceil(seconds*fps/4)+1,seed=seed,fps=fps)
    for key,pairs in bindings.items():
        if not pairs:
            raise ValueError('Empty workflow binding: '+key)
        for node,field in pairs:
            if str(node) not in workflow or field not in workflow[str(node)].get('inputs',{}):
                raise ValueError(f'Missing workflow input {node}.{field}')
            workflow[str(node)]['inputs'][field]=values[key]
    return workflow


def json_http(url, payload=None, timeout=30):
    data=None if payload is None else json.dumps(payload).encode()
    req=request.Request(url,data=data,headers={'Content-Type':'application/json'})
    with request.urlopen(req,timeout=timeout) as response:
        return json.load(response)


def preflight(url, template, bindings):
    build_workflow(template,bindings,{'prompt':'preflight'},[480,832],4,42)
    try:
        info=json_http(url.rstrip('/')+'/object_info')
    except Exception as exc:
        raise RuntimeError('ComfyUI unavailable; no video generated and no still fallback used') from exc
    missing=sorted({n['class_type'] for n in template.values()}-set(info))
    if missing:
        raise ValueError('Workflow node classes unavailable: '+', '.join(missing))
    # Server validates full graph and installed model choices on submission.
    return {'connected':True,'workflow_classes_available':True}


def motion_check(path, minimum_change=.12):
    """Small grayscale temporal test. A moving camera can pass; art review remains required."""
    raw=command(['ffmpeg','-v','error','-i',path,'-vf','fps=4,scale=64:64,format=gray','-f','rawvideo','-'])
    frames=[raw[i:i+4096] for i in range(0,len(raw),4096) if len(raw[i:i+4096])==4096]
    if len(frames)<4:
        raise ValueError('Too few decoded frames for motion check')
    diffs=[sum(abs(a-b) for a,b in zip(x,y))/4096 for x,y in zip(frames,frames[1:])]
    active=sum(d>=minimum_change for d in diffs)/len(diffs)
    if active<.5:
        raise ValueError(f'Static/near-static output rejected ({active:.0%} active frame transitions)')
    return {'active_transition_fraction':round(active,4),'threshold':minimum_change,'semantic_review':'pending'}


def render_clip(url,workflow,path,timeout=1800):
    pid=json_http(url+'/prompt',{'prompt':workflow})['prompt_id']
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=json_http(url+'/history/'+parse.quote(pid,safe='')).get(pid)
        if result:
            if result.get('status',{}).get('status_str')=='error':
                raise RuntimeError('ComfyUI failed: '+str(result.get('status')))
            for node in result.get('outputs',{}).values():
                for kind in ['videos','gifs']:
                    for item in node.get(kind,[]):
                        if not item['filename'].lower().endswith(('.mp4','.webm','.mov','.mkv')):
                            continue
                        query=parse.urlencode({k:item.get(k,'output' if k=='type' else '') for k in ['filename','subfolder','type']})
                        with request.urlopen(url+'/view?'+query,timeout=120) as response:
                            path.write_bytes(response.read())
                        command(['ffmpeg','-v','error','-xerror','-i',path,'-f','null','-'])
                        return
        time.sleep(2)
    raise TimeoutError('ComfyUI render deadline exceeded; rerun reuses verified completed clips')


def render(job, audio, template, bindings, output, url):
    validate_job(job)
    audio=Path(audio).resolve();duration=float(probe(audio)['format']['duration'])
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('Narration audio has invalid duration')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    preflight(url,template,bindings)
    total=sum(len(s['narration'].split()) for s in job['scenes'])
    if not total:raise ValueError('Empty narration')
    clips=[];receipts=[]
    for i,scene in enumerate(job['scenes']):
        span=duration*len(scene['narration'].split())/total
        count=max(1,math.ceil(span/5));seconds=span/count
        if seconds<1:
            raise ValueError('Scene shorter than 1 second; combine narration units')
        for part in range(count):
            workflow=build_workflow(template,bindings,scene,job['dimensions'],seconds,42+i*100+part)
            key=hashlib.sha256(json.dumps(workflow,sort_keys=True).encode()).hexdigest()[:20]
            path=output/f'{i:03}_{part:02}_{key}.mp4';receipt_path=path.with_suffix('.json')
            if not (path.exists() and receipt_path.exists() and json.loads(receipt_path.read_text()).get('sha256')==sha(path)):
                render_clip(url.rstrip('/'),workflow,path)
                receipt={'sha256':sha(path),'motion':motion_check(path),'scene':scene['id'],'part':part}
                receipt_path.write_text(json.dumps(receipt,indent=2))
            else:motion_check(path)
            measured=float(probe(path)['format']['duration'])
            ratio=measured/seconds
            if not .85<=ratio<=1.15:
                raise ValueError('Clip duration incompatible with narration; no freeze or repeated-clip padding allowed')
            final=output/f'cut_{i:03}_{part:02}.mp4'
            command(['ffmpeg','-v','error','-y','-i',path,'-vf',f'setpts=PTS/{ratio:.9f},fps=24,scale={job.get("export_dimensions",job["dimensions"])[0]}:{job.get("export_dimensions",job["dimensions"])[1]},setsar=1','-an','-c:v','libx264','-pix_fmt','yuv420p',final])
            clips.append(final);receipts.append(json.loads(receipt_path.read_text()))
    # Files are generated internally with safe fixed names, never source-controlled shell strings.
    concat=output/'clips.txt';concat.write_text(''.join(f"file '{p.name}'\n" for p in clips))
    final=output/(job['id']+'_MOTION_REVIEW.mp4')
    command(['ffmpeg','-v','error','-y','-f','concat','-safe','1','-i',concat,'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',final])
    command(['ffmpeg','-v','error','-xerror','-i',final,'-f','null','-'])
    actual=float(probe(final)['format']['duration'])
    if abs(actual-duration)>.15:raise ValueError('Final audio/video duration mismatch')
    report={'id':job['id'],'duration':actual,'sha256':sha(final),'audio_sha256':sha(audio),'source_sha256':job['narration_sha256'],'clips':receipts,'narration_scene_alignment':'estimated by word count; review transitions','editorial_review':'pending','published':False}
    (output/'receipt.json').write_text(json.dumps(report,indent=2))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('job',type=Path);p.add_argument('--audio',type=Path);p.add_argument('--workflow',type=Path);p.add_argument('--bindings',type=Path);p.add_argument('--output',type=Path,default=Path('renders/motion'));p.add_argument('--comfyui',default='http://127.0.0.1:8188');p.add_argument('--validate-only',action='store_true');p.add_argument('--preflight',action='store_true');a=p.parse_args()
    job=json.loads(a.job.read_text());validate_job(job)
    if a.validate_only:print(json.dumps({'id':job['id'],'valid':True,'scenes':len(job['scenes']),'rendered':False}));return
    if not a.workflow or not a.bindings:p.error('Provide a tested ComfyUI API workflow and bindings; no still fallback exists')
    template=json.loads(a.workflow.read_text());bindings=json.loads(a.bindings.read_text())
    if a.preflight:print(json.dumps(preflight(a.comfyui,template,bindings)));return
    if not a.audio:p.error('Provide the reviewed narration audio; this command does not substitute a voice')
    print(json.dumps(render(job,a.audio,template,bindings,a.output,a.comfyui)))

if __name__=='__main__':main()
