import re
with open('api/db_routes.py', encoding='utf-8') as f:
    content = f.read()
matches = re.finditer(r'yield f"data: \{json_module\.dumps\(\{', content)
for m in matches:
    line_num = content[:m.start()].count('\n') + 1
    print(f'Line {line_num}')
