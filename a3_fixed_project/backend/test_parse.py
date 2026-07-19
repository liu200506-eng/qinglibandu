with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'File length: {len(content)}')
print(f'Number of lines: {content.count(chr(10))}')

try:
    import ast
    ast.parse(content)
    print('AST parse OK')
except SyntaxError as e:
    print(f'SyntaxError: {e}')
    line_num = e.lineno
    lines = content.split('\n')
    print(f'\nLine {line_num}: {repr(lines[line_num-1])}')
    if line_num > 1:
        print(f'Line {line_num-1}: {repr(lines[line_num-2])}')
    if line_num < len(lines):
        print(f'Line {line_num+1}: {repr(lines[line_num])}')
