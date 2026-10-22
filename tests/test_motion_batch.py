import copy,hashlib,json,subprocess,tempfile,unittest,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from studio_os.motion_batch import validate_job,build_workflow,motion_check,preflight,render

class MotionBatchTest(unittest.TestCase):
 def setUp(self):
  text='One hand sets the telephone down and turns toward the door.'
  self.job={'version':1,'id':'fixture','motion_required':True,'dimensions':[432,768],'narration':text,'narration_sha256':hashlib.sha256(text.encode()).hexdigest(),'scenes':[{'id':'one','narration':text,'action':'set telephone down','prompt':'hand sets telephone down','character_present':False}]}
 def test_reject_changed_narration(self):
  validate_job(self.job);self.job['scenes'][0]['narration']='Different words.'
  with self.assertRaisesRegex(ValueError,'differs'):validate_job(self.job)
 def test_reject_unconditioned_cast(self):
  self.job['scenes'][0]['character_present']=True
  with self.assertRaisesRegex(ValueError,'object/environment'):validate_job(self.job)
 def test_explicit_workflow_bindings(self):
  template={'a':{'inputs':{'text':'','width':0,'height':0,'length':0,'seed':0,'fps':0}}}
  bindings={k:[['a',('text' if k=='prompt' else k)]] for k in ['prompt','width','height','length','seed','fps']}
  out=build_workflow(template,bindings,self.job['scenes'][0],[432,768],5,0)
  self.assertEqual(out['a']['inputs']['length'],81);self.assertEqual(out['a']['inputs']['seed'],0)
  self.assertEqual(template['a']['inputs']['length'],0)
  bad=copy.deepcopy(bindings);bad['prompt']=[['missing','text']]
  with self.assertRaisesRegex(ValueError,'Missing workflow'):build_workflow(template,bad,self.job['scenes'][0],[432,768],5,0)
 def test_no_server_no_fallback(self):
  template={'a':{'inputs':{k:0 for k in ['text','width','height','length','seed','fps']}}}
  bindings={k:[['a','text' if k=='prompt' else k]] for k in ['prompt','width','height','length','seed','fps']}
  with self.assertRaisesRegex(RuntimeError,'no still fallback'):preflight('http://127.0.0.1:1',template,bindings)
 def test_static_rejected_moving_passes(self):
  with tempfile.TemporaryDirectory() as d:
   static=Path(d)/'still.mp4';moving=Path(d)/'moving.mp4'
   for spec,path in [('color=c=black:s=128x128:r=16:d=2',static),('testsrc2=s=128x128:r=16:d=2',moving)]:
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',spec,'-c:v','libx264','-pix_fmt','yuv420p',str(path)],check=True)
   with self.assertRaisesRegex(ValueError,'Static'):motion_check(static)
   self.assertGreater(motion_check(moving)['active_transition_fraction'],.5)
 def test_assemble_through_local_comfy_fixture(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);clip=root/'clip.mp4';audio=root/'voice.wav'
   subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=s=432x768:r=16:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True)
   subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','sine=frequency=400:duration=2',str(audio)],check=True)
   video=clip.read_bytes();calls=[]
   class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
     if self.path.startswith('/view?'):body=video
     elif self.path=='/object_info':body=json.dumps({'FixtureNode':{}}).encode()
     else:body=json.dumps({'fixture':{'outputs':{'1':{'videos':[{'filename':'clip.mp4','subfolder':'','type':'output'}]}}}}).encode()
     self.send_response(200);self.end_headers();self.wfile.write(body)
    def do_POST(self):
     calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))));self.send_response(200);self.end_headers();self.wfile.write(b'{"prompt_id":"fixture"}')
   server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:
    template={'a':{'class_type':'FixtureNode','inputs':{k:0 for k in ['text','width','height','length','seed','fps']}}}
    bindings={k:[['a','text' if k=='prompt' else k]] for k in ['prompt','width','height','length','seed','fps']}
    url='http://127.0.0.1:'+str(server.server_port)
    report=render(self.job,audio,template,bindings,root/'output',url)
    self.assertFalse(report['published']);self.assertAlmostEqual(report['duration'],2,delta=.15)
    self.assertEqual(len(calls),1)
    render(self.job,audio,template,bindings,root/'output',url)
    self.assertEqual(len(calls),1,'Verified clips must be reused')
   finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
