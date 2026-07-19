import re

with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'yield f"data: \{json_module\.dumps\(\{',
    'yield "data: " + json_module.dumps({',
    content
)

content = re.sub(
    r'\}\)}\\n\\n"',
    '}) + "\\n\\n"',
    content
)

content = re.sub(
    r'\'message\': f\'([^\']*)\'',
    r"'message': '\1'",
    content
)

content = re.sub(
    r'\'message\': f"([^"]*)"',
    r'"message": "\1"',
    content
)

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed db_routes.py')
