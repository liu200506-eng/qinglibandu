import re

with open('api/db_routes.py', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'yield f"data: \{json_module\.dumps\((\{.*?\})\)}\\n\\n"',
    r'yield "data: " + json_module.dumps(\1) + "\n\n"',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'yield f"data: \{json_module\.dumps\((\{.*?\})\)}\\n\\n"',
    r'yield "data: " + json_module.dumps(\1) + "\n\n"',
    content,
    flags=re.DOTALL
)

content = content.replace(
    'yield f"data: {json_module.dumps({',
    'yield "data: " + json_module.dumps({'
).replace(
    '})}\n\n"',
    '}) + "\n\n"'
)

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')
