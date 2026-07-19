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
            if inner.strip().endswith('})}\n\n"'):
                inner = inner.strip().replace('})}\n\n"', '}) + "\\n\\n"\n')
                output.append(indent + '            ' + inner)
                i += 1
                break
            elif inner.strip().endswith('})}\n"'):
                inner = inner.strip().replace('})}\n"', '}) + "\\n\\n"\n')
                output.append(indent + '            ' + inner)
                i += 1
                break
            elif inner.strip().endswith('})}\"'):
                inner = inner.strip().replace('})}\"', '}) + "\\n\\n"\n')
                output.append(indent + '            ' + inner)
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

print('Fixed')
