from database import SessionLocal
from models.database_models import Subject, KnowledgeNode

db = SessionLocal()

print('=== 检查科目 ===')
subjects = db.query(Subject).all()
for s in subjects:
    print(f'ID={s.id}, name={s.name}, description={s.description[:50] if s.description else ""}')

print()
print('=== 检查知识点 ===')
nodes = db.query(KnowledgeNode).all()
print(f'知识点总数: {len(nodes)}')

for s in subjects:
    subject_nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == s.id).all()
    print(f'\n科目 "{s.name}" 的知识点:')
    for n in subject_nodes[:5]:
        has_exercises = bool(n.exercises_json)
        has_lecture = bool(n.lecture_text)
        print(f'  ID={n.id}, name={n.name}, parent_id={n.parent_id}, 有讲义={has_lecture}, 有习题={has_exercises}')
    print(f'  ... 共 {len(subject_nodes)} 个')

db.close()
