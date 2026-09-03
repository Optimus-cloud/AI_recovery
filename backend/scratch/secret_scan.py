import os
import re

root = r"C:\Users\mvars\Desktop\AI_Recovery"

patterns = [
    re.compile(r'sk-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'AIzaSy[a-zA-Z0-9_-]{30,}'),
    re.compile(r'(?:api_key|apikey|secret|password|access_token|bearer)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{12,}["\']', re.IGNORECASE)
]

secrets_found = []
files_scanned = 0

for dirpath, dirnames, filenames in os.walk(root):
    if any(p in dirpath for p in ['venv', 'node_modules', '.git', '.cache', 'dist']):
        continue
    for f in filenames:
        if f.endswith(('.py', '.ts', '.tsx', '.js', '.json', '.html', '.md', '.env', '.example', '.yaml', '.yml')):
            files_scanned += 1
            filepath = os.path.join(dirpath, f)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                for line_no, line in enumerate(fp, 1):
                    for pat in patterns:
                        if pat.search(line):
                            secrets_found.append((f, line_no, line.strip()[:80]))

print(f"Scanned {files_scanned} source files.")
print(f"Secrets found count: {len(secrets_found)}")
for s in secrets_found:
    print(f" -> {s[0]} line {s[1]}: {s[2]}")
