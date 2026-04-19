import json
import re

with open('active_session.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'\"colors\":\s*(\{.*?\})', html, re.DOTALL)
if match:
    colors = json.loads(match.group(1))
    
    with open('web-client/src/app/globals.css', 'w', encoding='utf-8') as out:
        out.write('@import "tailwindcss";\n\n')
        out.write('@theme inline {\n')
        out.write('  --color-transparent: transparent;\n')
        out.write('  --color-current: currentColor;\n')
        out.write('  --color-black: #000;\n')
        out.write('  --color-white: #fff;\n')
        for k, v in colors.items():
            out.write(f'  --color-{k}: {v};\n')
        out.write('  --font-body: var(--font-inter);\n')
        out.write('  --font-headline: var(--font-manrope);\n')
        out.write('}\n\n')
        out.write('body {\n  font-family: var(--font-body), sans-serif;\n  background-color: var(--color-background);\n  color: var(--color-on-surface);\n}\n')
