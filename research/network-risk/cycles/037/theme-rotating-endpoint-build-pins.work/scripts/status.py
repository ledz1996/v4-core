"""Print a one-line status of every pinned run log in out/. Usage: python3 -I status.py <out dir>"""
import sys, json, glob, os
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.log'))):
    if not os.path.basename(f).startswith(('pin-', 'rounds-', 'prove-')): continue
    s = open(f).read()
    try:
        d = json.loads(s)
        print(os.path.basename(f), 'jobs', d['jobs'], 'mm', d['mismatches'], 'err', d['errors'], 'ref', d['refusals'],
              {k.split('/')[1][:14] if '/' in k else k[:20]: v for k, v in d['byBuild'].items()}, 'full', all(d['full'].values()))
    except Exception:
        print(os.path.basename(f), 'running', s[:150].replace('\n', ' '))
