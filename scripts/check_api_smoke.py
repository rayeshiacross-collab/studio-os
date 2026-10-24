"""Check API boot health independently of production renderer readiness."""
import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000/health')
    parser.add_argument('--expect-comfyui', choices=('reachable', 'unreachable'), required=True)
    parser.add_argument('--attempts', type=int, default=30)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error('--attempts must be positive')
    opener = build_opener(ProxyHandler({}))
    expected = (
        (200, {'status': 'ok', 'comfyui': 'reachable'})
        if args.expect_comfyui == 'reachable' else
        (503, {'detail': {'status': 'degraded', 'comfyui': 'unreachable'}})
    )
    diagnostic = 'No response'
    for attempt in range(args.attempts):
        try:
            try:
                response = opener.open(args.url, timeout=3)
            except HTTPError as exc:
                response = exc  # Preserve the 503 body; curl --fail discarded it.
            with response:
                status = response.code
                body = response.read(4096).decode('utf-8', errors='replace')
            diagnostic = f'HTTP {status}: {body}'
            if status == expected[0] and json.loads(body) == expected[1]:
                print(f'API boot verified; comfyui={args.expect_comfyui}; render_verified=false')
                return 0
        except (URLError, OSError, ValueError) as exc:
            diagnostic += f' ({exc})'
        if attempt + 1 < args.attempts:
            time.sleep(2)
    print(f'API smoke check failed after {args.attempts} attempt(s): {diagnostic}', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
