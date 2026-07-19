with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip().startswith('yield f"data: {json_module.dumps({'):
        brace_count = 1
        j = i + 1
        while j < len(lines) and brace_count > 0:
            brace_count += lines[j].count('{') - lines[j].count('}')
            j += 1
        end_line = lines[j-1] if j-1 < len(lines) else ''
        if end_line.strip().endswith('})}\n\n"'):
            data_lines = lines[i:j]
            data_content = ''.join(data_lines)
            data_content = data_content.replace('yield f"data: {json_module.dumps({', '')
            data_content = data_content.replace('})}\n\n"', '')
            new_line = '            yield "data: " + json_module.dumps({' + data_content.strip() + '}) + "\\n\\n"\n'
            output.append(new_line)
            i = j
            continue
    output.append(line)
    i += 1

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print('Fixed')
