"""Fail on credential-shaped strings and local user paths; never print a match."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
patterns=[re.compile('api'+'key_'+r'[a-fA-F0-9]{20,}_[a-fA-F0-9]{20,}'),re.compile('/'+'Users'+r'/[^/\s]+'),re.compile('/'+'home'+r'/[^/\s]+'),re.compile(r'Bearer\s+[A-Za-z0-9_-]{24,}'),re.compile(r'(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}')]
problems=[];count=0
for p in ROOT.rglob('*'):
 if not p.is_file() or any(part in {'.git','.venv','__pycache__'} for part in p.relative_to(ROOT).parts):continue
 try:text=p.read_text()
 except UnicodeDecodeError:continue
 count+=1
 if any(pattern.search(text) for pattern in patterns):problems.append(str(p.relative_to(ROOT)))
if problems:raise SystemExit('Potential sensitive material in: '+', '.join(problems))
print(f'Privacy pattern checks passed for {count} text files. Synthetic provenance and metadata also require manual review.')
