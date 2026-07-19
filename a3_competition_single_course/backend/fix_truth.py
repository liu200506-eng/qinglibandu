with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]
    
    if 'yield f"data: {json_module.dumps({' in line:
        indent = line[:len(line) - len(line.lstrip())]
        output.append(indent + 'yield "data: " + json_module.dumps({\n')
        
        i += 1
        while i < len(lines):
            inner = lines[i]
            stripped = inner.strip()
            
            if stripped == '})}\n\n"':
                output.append(indent + '            }) + "\\n\\n"\n')
                i += 1
                break
            elif stripped == '})}\n"':
                output.append(indent + '            }) + "\\n\\n"\n')
                i += 1
                break
            elif stripped.endswith('})}\"'):
                output.append(indent + '            }) + "\\n\\n"\n')
                i += 1
                break
            elif stripped == '})}":':
                output.append(indent + '            }) + "\\n\\n":\n')
                i += 1
                break
            else:
                output.append(inner)
                i += 1
    else:
        output.append(line)
        i += 1

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print('Fixed all occurrences')
