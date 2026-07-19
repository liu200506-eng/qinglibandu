import json
import os
import sys

migration_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(migration_dir)
sys.path.insert(0, backend_dir)

def import_knowledge(json_file=None, clear_existing=False):
    if json_file is None:
        json_file = os.path.join(migration_dir, 'knowledge_export.json')
    
    if not os.path.exists(json_file):
        print(f'错误: 文件不存在 {json_file}')
        return False
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    from database import SessionLocal, Base, engine
    from models.database_models import Subject, KnowledgeNode
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    if clear_existing:
        db.query(KnowledgeNode).delete()
        db.query(Subject).delete()
        db.commit()
        print('已清空现有科目和知识点数据')
    
    existing_subjects = {s.name: s.id for s in db.query(Subject).all()}
    
    subject_id_map = {}
    subject_count = 0
    node_count = 0
    
    for subj in data['subjects']:
        if subj['name'] in existing_subjects:
            subject_id_map[subj['id']] = existing_subjects[subj['name']]
            continue
        
        s = Subject(
            name=subj['name'],
            description=subj['description'],
            icon=subj['icon'],
            education_level=subj['education_level'],
            full_score=subj['full_score']
        )
        db.add(s)
        db.flush()
        subject_id_map[subj['id']] = s.id
        subject_count += 1
    
    existing_nodes = {(n.subject_id, n.name): n.id for n in db.query(KnowledgeNode).all()}
    node_id_map = {}
    
    for subj in data['subjects']:
        new_subj_id = subject_id_map[subj['id']]
        
        def add_nodes(nodes, parent_id=None):
            nonlocal node_count
            for node in nodes:
                if node.get('parent_id') is not None and node['parent_id'] not in node_id_map:
                    continue
                
                new_parent_id = node_id_map.get(node['parent_id']) if node.get('parent_id') else None
                
                key = (new_subj_id, node['name'])
                if key in existing_nodes:
                    node_id_map[node['id']] = existing_nodes[key]
                    continue
                
                n = KnowledgeNode(
                    subject_id=new_subj_id,
                    parent_id=new_parent_id,
                    name=node['name'],
                    description=node['description'],
                    difficulty=node['difficulty'],
                    mastery=node['mastery'],
                    education_level=node['education_level'],
                    grade=node['grade'],
                    lecture_text=node['lecture_text'],
                    exercises_json=json.dumps(node['exercises'], ensure_ascii=False) if node['exercises'] else None,
                    flash_cards_json=json.dumps(node['flash_cards'], ensure_ascii=False) if node['flash_cards'] else None
                )
                db.add(n)
                db.flush()
                node_id_map[node['id']] = n.id
                node_count += 1
                
                if node.get('children'):
                    add_nodes(node['children'], node['id'])
        
        add_nodes(subj['knowledge_nodes'])
    
    db.commit()
    db.close()
    
    print(f'导入完成！')
    print(f'新增科目: {subject_count}')
    print(f'新增知识点: {node_count}')
    return True

if __name__ == '__main__':
    import_knowledge()
