import os
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
from models.database_models import Subject, KnowledgeNode

db = SessionLocal()

knowledge_base_dir = Path(__file__).parent / 'knowledge_base' / 'computer_network'

course_data = json.loads((knowledge_base_dir / 'course.json').read_text(encoding='utf-8'))
knowledge_tree = json.loads((knowledge_base_dir / 'knowledge_tree.json').read_text(encoding='utf-8'))
question_bank = json.loads((knowledge_base_dir / 'question_bank.json').read_text(encoding='utf-8'))
documents_dir = knowledge_base_dir / 'documents'

subject = db.query(Subject).filter(Subject.name == '计算机网络').first()
if not subject:
    subject = Subject(
        name='计算机网络',
        description=course_data.get('description', ''),
        icon='🌐',
        education_level='university',
        full_score=100
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

questions_by_kp = {}
for q in question_bank.get('questions', []):
    kp_id = q.get('knowledge_point_id', '')
    if kp_id not in questions_by_kp:
        questions_by_kp[kp_id] = []
    questions_by_kp[kp_id].append(q)

def normalize_name(name):
    return name.replace('/', '').replace('\\', '').replace(' ', '').replace('-', '')

def find_document_content(node_name):
    normalized_node_name = normalize_name(node_name)
    for doc_file in documents_dir.glob('*.md'):
        doc_name = doc_file.stem
        normalized_doc_name = normalize_name(doc_name)
        if normalized_node_name in normalized_doc_name or normalized_doc_name in normalized_node_name:
            try:
                return doc_file.read_text(encoding='utf-8')
            except:
                pass
    return None

def process_node(node, parent_id=None, depth=0):
    node_name = node.get('name', node.get('label', ''))
    node_id = node.get('id', '')
    
    existing_node = db.query(KnowledgeNode).filter(
        KnowledgeNode.subject_id == subject.id,
        KnowledgeNode.name == node_name
    ).first()
    
    if not existing_node:
        existing_node = KnowledgeNode(
            subject_id=subject.id,
            parent_id=parent_id,
            name=node_name,
            description=node.get('description', ''),
            difficulty=node.get('difficulty', 0.5),
            mastery=node.get('mastery', 0.0),
            education_level='university',
            grade=''
        )
        db.add(existing_node)
        db.commit()
        db.refresh(existing_node)
    
    content = find_document_content(node_name)
    if content and len(content) > 50:
        existing_node.lecture_text = content
    elif node.get('lecture_text') and 'error' not in node.get('lecture_text', '').lower():
        existing_node.lecture_text = node.get('lecture_text')
    
    node_kp_id = node.get('id', '')
    if node_kp_id in questions_by_kp:
        exercises = []
        for q in questions_by_kp[node_kp_id]:
            options = [opt.get('text', '') for opt in q.get('options', [])]
            exercises.append({
                'question': q.get('question', ''),
                'options': options,
                'answer': q.get('answer', ''),
                'explanation': q.get('analysis', ''),
                'difficulty': q.get('difficulty', 0.5)
            })
        if exercises:
            existing_node.exercises_json = json.dumps(exercises, ensure_ascii=False)
    
    db.commit()
    
    children = node.get('children', [])
    for child in children:
        process_node(child, parent_id=existing_node.id, depth=depth+1)

for chapter in knowledge_tree.get('roots', []):
    process_node(chapter)

print('✅ 知识库填充完成')
db.close()