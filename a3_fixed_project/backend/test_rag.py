import urllib.request
import urllib.parse
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'http://localhost:8001/api/rag/query?' + urllib.parse.urlencode({'query': 'TCP三次握手'})
req = urllib.request.Request(url, method='POST')
r = urllib.request.urlopen(req)
result = json.loads(r.read().decode('utf-8'))

print(f'检索到 {len(result["results"])} 条结果')
for i, item in enumerate(result['results']):
    source = item.get('metadata', {}).get('source_file', '未知')
    text = item.get('text', '')[:150]
    score = item.get('score', 0)
    print(f'\n结果 {i+1} (得分: {score:.4f}):')
    print(f'来源: {source}')
    print(f'内容: {text}...')