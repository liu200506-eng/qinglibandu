import requests

print('=== 测试知识库API ===')
try:
    r = requests.get('http://localhost:8001/api/db/knowledge-tree/computer_network')
    print('API状态码:', r.status_code)
    data = r.json()
    print('返回状态:', data.get('status'))
    print('返回数据键:', list(data.keys())[:10])
    if 'nodes' in data:
        print('nodes数量:', len(data['nodes']))
    if 'sections' in data:
        print('sections数量:', len(data['sections']))
        for s in data['sections'][:3]:
            children = s.get('children', [])
            print(f'  - {s.get("name")}: {len(children)}个子节点')
            for child in children[:2]:
                has_exercises = len(child.get('exercises', [])) > 0
                print(f'    * {child.get("name")} (id={child.get("id")}, 有习题={has_exercises})')
except Exception as e:
    print('API请求失败:', e)
    import traceback
    traceback.print_exc()

print()
print('=== 测试节点习题API ===')
try:
    r = requests.get('http://localhost:8001/api/db/node/1/exercises')
    print('API状态码:', r.status_code)
    data = r.json()
    print('返回状态:', data.get('status'))
    print('节点名称:', data.get('node_name'))
    print('习题数量:', len(data.get('exercises', [])))
    if data.get('exercises'):
        print('第一题:', data['exercises'][0].get('question', '')[:50], '...')
except Exception as e:
    print('API请求失败:', e)
