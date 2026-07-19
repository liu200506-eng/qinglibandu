with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'yield f"data: {json_module.dumps({',
    'yield "data: " + json_module.dumps({'
)

content = content.replace(
    '})}\\n\\n"',
    '}) + "\\n\\n"'
)

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')
