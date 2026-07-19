with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
result = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'yield f"data: {json_module.dumps({' in line:
        data_lines = []
        data_lines.append(line.replace('yield f"data: {json_module.dumps({', ''))
        i += 1
        while i < len(lines) and '})}\n\n"' not in lines[i]:
            data_lines.append(lines[i])
            i += 1
        if i < len(lines) and '})}\n\n"' in lines[i]:
            last_line = lines[i].replace('})}\n\n"', '')
            data_lines.append(last_line)
            inner_content = '\n'.join(data_lines)
            result.append('            yield "data: " + json_module.dumps({' + inner_content + '}) + "\\n\\n"')
            i += 1
            continue
    if 'yield f"data: {json_module.dumps({' in line:
        result.append(line.replace('yield f"data: {json_module.dumps({', 'yield "data: " + json_module.dumps({').replace('})}\n\n"', '}) + "\\n\\n"'))
    else:
        result.append(line)
    i += 1

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))

print('Fixed all f-strings')
