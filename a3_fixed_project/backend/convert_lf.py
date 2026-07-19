with open('api/db_routes.py', 'rb') as f:
    data = f.read()

data = data.replace(b'\r\n', b'\n')

with open('api/db_routes.py', 'wb') as f:
    f.write(data)

print('Converted to LF')
