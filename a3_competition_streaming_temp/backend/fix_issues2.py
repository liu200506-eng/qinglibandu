with open('api/db_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'yield "data: " + json_module.dumps(' in line and line.strip().endswith('+ "'):
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith('"'):
            j += 1
        if j < len(lines):
            line = line.rstrip() + lines[j-1].strip() + '\n'
            i = j
        else:
            i += 1
    else:
        i += 1
    result.append(line)

with open('api/db_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

print('Fixed')
