"""课程发布状态管理脚本

状态：draft / review / published / demo_only / archived

策略：
- 计算机网络 -> published (核心示范)
- 计算机组成原理、数据库原理 -> review (通过检查后可设为published)
- 数据结构、操作系统 -> demo_only (前端不得显示为完整课程)
"""
import os
import json
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_DIR = os.path.join(BACKEND_DIR, 'knowledge_base')

# 课程发布状态映射
COURSE_PUBLISH_STATUS = {
    'computer_network': 'published',      # 核心示范课程
    'computer_organization': 'review',    # 完整扩展课程
    'database_principles': 'review',       # 完整扩展课程
    'data_structure': 'demo_only',         # 迁移展示课程
    'operating_system': 'demo_only',      # 迁移展示课程
}

# 前端显示策略
FRONTEND_DISPLAY = {
    'published': '完整显示',
    'review': '显示但标记审核中',
    'demo_only': '仅展示，不可作为完整课程学习',
    'draft': '不显示',
    'archived': '不显示',
}


def update_course_status(course_code: str, status: str) -> bool:
    """更新课程JSON文件的发布状态"""
    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code)
    course_file = os.path.join(course_dir, 'course.json')
    
    if not os.path.exists(course_file):
        print("[SKIP] " + course_code + " course.json 不存在")
        return False
    
    with open(course_file, 'r', encoding='utf-8') as f:
        course_data = json.load(f)
    
    old_status = course_data.get('publish_status', 'unknown')
    course_data['publish_status'] = status
    course_data['schema_version'] = '2.0'
    course_data['course_code'] = course_code
    
    with open(course_file, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, ensure_ascii=False, indent=2)
    
    print("[OK] " + course_code + ": " + old_status + " -> " + status + " (" + FRONTEND_DISPLAY.get(status, '') + ")")
    return True


def update_db_status():
    """更新数据库中Subject表的publish_status字段"""
    try:
        from database import SessionLocal
        from models.database_models import Subject
        
        db = SessionLocal()
        try:
            for course_code, status in COURSE_PUBLISH_STATUS.items():
                subject = db.query(Subject).filter(Subject.course_code == course_code).first()
                if subject:
                    old_status = subject.publish_status or 'unknown'
                    subject.publish_status = status
                    subject.schema_version = '2.0'
                    print("[DB] " + course_code + ": " + old_status + " -> " + status)
                else:
                    print("[WARN] 数据库中未找到课程: " + course_code)
            db.commit()
            print("\n数据库课程状态更新完成")
        finally:
            db.close()
    except Exception as e:
        print("[ERROR] 数据库更新失败: " + str(e))
        return False
    return True


def main():
    print("=" * 60)
    print("课程发布状态管理")
    print("=" * 60)
    
    print("\n[1/2] 更新JSON文件状态...")
    for course_code, status in COURSE_PUBLISH_STATUS.items():
        update_course_status(course_code, status)
    
    print("\n[2/2] 更新数据库状态...")
    update_db_status()
    
    print("\n" + "=" * 60)
    print("发布状态汇总:")
    print("-" * 60)
    for code, status in COURSE_PUBLISH_STATUS.items():
        print("  " + code.ljust(25) + " -> " + status.ljust(12) + " (" + FRONTEND_DISPLAY.get(status, '') + ")")
    print("=" * 60)


if __name__ == '__main__':
    main()
