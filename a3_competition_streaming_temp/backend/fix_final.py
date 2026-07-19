with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    if stripped.startswith('yield f"data: {json_module.dumps({'):
        result_lines = []
        result_lines.append('yield "data: " + json_module.dumps({')
        
        i += 1
        while i < len(lines):
            inner_line = lines[i]
            if inner_line.strip().endswith('})}\n\n"'):
                result_lines.append(inner_line.strip().replace('})}\n\n"', '}) + "\\n\\n"'))
                i += 1
                break
            elif inner_line.strip().endswith('})}\n"'):
                result_lines.append(inner_line.strip().replace('})}\n"', '}) + "\\n\\n"'))
                i += 1
                break
            else:
                result_lines.append(inner_line.rstrip('\n'))
                i += 1
        
        output.extend(r + '\n' for r in result_lines)
    else:
        output.append(line)
        i += 1

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print('Fixed')
