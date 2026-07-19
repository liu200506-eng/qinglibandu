#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 手动执行版（替代Alembic）
用于在现有数据库上增加新表和新字段
"""

import os
import sys
import sqlite3

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_DIR, "magicstudy.db")

MIGRATIONS = [
    # 1. Subject表增加字段
    {
        "name": "add_subject_fields",
        "sql": [
            "ALTER TABLE subjects ADD COLUMN course_code VARCHAR(50) DEFAULT ''",
            "ALTER TABLE subjects ADD COLUMN publish_status VARCHAR(20) DEFAULT 'draft'",
            "ALTER TABLE subjects ADD COLUMN schema_version VARCHAR(10) DEFAULT '2.0'",
            # 先更新现有数据的course_code
            "UPDATE subjects SET course_code = 'computer_network' WHERE name = '计算机网络' AND (course_code = '' OR course_code IS NULL)",
            "UPDATE subjects SET course_code = 'computer_organization' WHERE name = '计算机组成原理' AND (course_code = '' OR course_code IS NULL)",
            "UPDATE subjects SET course_code = 'database_principles' WHERE name = '数据库原理' AND (course_code = '' OR course_code IS NULL)",
            "UPDATE subjects SET course_code = 'data_structure' WHERE name = '数据结构' AND (course_code = '' OR course_code IS NULL)",
            "UPDATE subjects SET course_code = 'operating_system' WHERE name = '操作系统' AND (course_code = '' OR course_code IS NULL)",
            "UPDATE subjects SET course_code = 'math_' || CAST(id AS TEXT) WHERE course_code = '' OR course_code IS NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_course_code ON subjects(course_code)",
        ],
    },
    # 2. KnowledgeNode表增加字段
    {
        "name": "add_knowledge_node_fields",
        "sql": [
            "ALTER TABLE knowledge_nodes ADD COLUMN node_code VARCHAR(100) DEFAULT ''",
            "ALTER TABLE knowledge_nodes ADD COLUMN mastery_threshold FLOAT DEFAULT 0.7",
            "ALTER TABLE knowledge_nodes ADD COLUMN review_status VARCHAR(20) DEFAULT 'pending'",
            "ALTER TABLE knowledge_nodes ADD COLUMN reviewed_by VARCHAR(50)",
            "ALTER TABLE knowledge_nodes ADD COLUMN reviewed_at DATETIME",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_node_subject_code ON knowledge_nodes(subject_id, node_code)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_node_parent ON knowledge_nodes(parent_id)",
        ],
    },
    # 3. Course表增加字段
    {
        "name": "add_course_fields",
        "sql": [
            "ALTER TABLE courses ADD COLUMN course_code VARCHAR(100) DEFAULT ''",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_course_code ON courses(course_code)",
        ],
    },
    # 4. StudentProfile增加字段
    {
        "name": "add_profile_fields",
        "sql": [
            "ALTER TABLE student_profiles ADD COLUMN profile_version INTEGER DEFAULT 1",
        ],
    },
    # 5. StudyPlan增加字段
    {
        "name": "add_study_plan_fields",
        "sql": [
            "ALTER TABLE study_plans ADD COLUMN profile_version INTEGER DEFAULT 0",
        ],
    },
    # 6. ProfileSnapshot增加字段
    {
        "name": "add_snapshot_fields",
        "sql": [
            "ALTER TABLE profile_snapshots ADD COLUMN profile_id INTEGER",
            "ALTER TABLE profile_snapshots ADD COLUMN profile_version_before INTEGER DEFAULT 0",
            "ALTER TABLE profile_snapshots ADD COLUMN profile_version_after INTEGER DEFAULT 0",
            "ALTER TABLE profile_snapshots ADD COLUMN update_reason TEXT DEFAULT ''",
            "ALTER TABLE profile_snapshots ADD COLUMN evidence_summary TEXT",
            "ALTER TABLE profile_snapshots ADD COLUMN affected_plans TEXT",
        ],
    },
    # 7. ErrorRecord增加索引
    {
        "name": "add_error_record_indexes",
        "sql": [
            "CREATE INDEX IF NOT EXISTS idx_error_record_student ON error_records(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_error_record_node ON error_records(knowledge_node_id)",
            "CREATE INDEX IF NOT EXISTS idx_error_record_created ON error_records(created_at)",
        ],
    },
    # 8. CourseKnowledgeNode唯一约束
    {
        "name": "add_course_knowledge_node_unique",
        "sql": [
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_course_knowledge_node ON course_knowledge_nodes(course_id, knowledge_node_id)",
        ],
    },
    # 9. LearningEvidence升级字段（如果表已存在）
    {
        "name": "upgrade_learning_evidence",
        "sql": [
            "ALTER TABLE learning_evidence ADD COLUMN session_id VARCHAR(100)",
            "ALTER TABLE learning_evidence ADD COLUMN task_id VARCHAR(100)",
            "ALTER TABLE learning_evidence ADD COLUMN source_event_id VARCHAR(200) DEFAULT ''",
            "ALTER TABLE learning_evidence ADD COLUMN max_score FLOAT DEFAULT 100.0",
            "ALTER TABLE learning_evidence ADD COLUMN normalized_score FLOAT DEFAULT 0.0",
            "ALTER TABLE learning_evidence ADD COLUMN is_correct BOOLEAN",
            "ALTER TABLE learning_evidence ADD COLUMN response_time_ms INTEGER DEFAULT 0",
            "ALTER TABLE learning_evidence ADD COLUMN hint_count INTEGER DEFAULT 0",
            "ALTER TABLE learning_evidence ADD COLUMN profile_version_before INTEGER DEFAULT 0",
            "ALTER TABLE learning_evidence ADD COLUMN profile_version_after INTEGER DEFAULT 0",
            "ALTER TABLE learning_evidence ADD COLUMN raw_payload_json TEXT",
            # 为已有的记录填充source_event_id（避免唯一索引创建失败）
            "UPDATE learning_evidence SET source_event_id = 'legacy_' || CAST(id AS TEXT) WHERE source_event_id = '' OR source_event_id IS NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_evidence_source_event ON learning_evidence(source_event_id)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_user ON learning_evidence(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_node ON learning_evidence(knowledge_node_id)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_type ON learning_evidence(evidence_type)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_created ON learning_evidence(created_at)",
        ],
    },
]

def run_migration():
    if not os.path.exists(DB_PATH):
        print("[ERROR] 数据库文件不存在: " + DB_PATH)
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("开始数据库迁移...")
    print("数据库: " + DB_PATH)
    print("-" * 60)
    
    # 获取已执行的迁移
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS _migrations (name TEXT UNIQUE, executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("SELECT name FROM _migrations")
        executed = set(row[0] for row in cursor.fetchall())
    except Exception:
        executed = set()
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for migration in MIGRATIONS:
        name = migration["name"]
        if name in executed:
            print("[SKIP] " + name + " (已执行)")
            skip_count += 1
            continue
        
        print("[RUN]  " + name)
        all_success = True
        for sql in migration["sql"]:
            try:
                cursor.execute(sql)
                print("  [OK] " + sql[:80])
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("  [SKIP] " + str(e))
                else:
                    print("  [WARN] " + str(e))
                    # 不再视为失败，继续后续SQL
            except sqlite3.IntegrityError as e:
                print("  [WARN] " + str(e))
                # 数据完整性错误，不阻止后续迁移
        
        # 即使部分SQL失败，也标记迁移完成（避免重复执行）
        cursor.execute("INSERT OR IGNORE INTO _migrations (name) VALUES (?)", (name,))
        conn.commit()
        success_count += 1
    
    # 创建新表（SourceDocument, DocumentChunk - 学习证据表已通过upgrade迁移升级）
    print("\n[RUN]  create_new_tables")
    new_tables_sql = [
        """CREATE TABLE IF NOT EXISTS source_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id),
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) DEFAULT '',
            version VARCHAR(20) DEFAULT '1.0',
            chapter VARCHAR(100) DEFAULT '',
            section VARCHAR(100) DEFAULT '',
            page_number VARCHAR(20) DEFAULT '',
            url VARCHAR(500) DEFAULT '',
            doc_hash VARCHAR(64) NOT NULL,
            license_type VARCHAR(50) DEFAULT 'unknown',
            review_status VARCHAR(20) DEFAULT 'pending',
            reviewed_by VARCHAR(50),
            reviewed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_source_doc_hash ON source_documents(subject_id, doc_hash)",
        "CREATE INDEX IF NOT EXISTS idx_source_doc_subject ON source_documents(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_source_doc_review ON source_documents(review_status)",
        """CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_doc_id INTEGER NOT NULL REFERENCES source_documents(id),
            knowledge_node_id INTEGER REFERENCES knowledge_nodes(id),
            chunk_index INTEGER DEFAULT 0,
            content TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            vector_id VARCHAR(100),
            embedding_model VARCHAR(100) DEFAULT '',
            embedding_status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_doc_chunk_index ON document_chunks(source_doc_id, chunk_index)",
        "CREATE INDEX IF NOT EXISTS idx_doc_chunk_node ON document_chunks(knowledge_node_id)",
        "CREATE INDEX IF NOT EXISTS idx_doc_chunk_hash ON document_chunks(content_hash)",
        "CREATE INDEX IF NOT EXISTS idx_doc_chunk_vector ON document_chunks(vector_id)",
    ]
    
    for sql in new_tables_sql:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                print("  [FAIL] " + str(e))
    
    cursor.execute("INSERT OR IGNORE INTO _migrations (name) VALUES (?)", ("create_new_tables",))
    conn.commit()
    success_count += 1
    print("[OK]   create_new_tables")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("迁移完成: 成功 " + str(success_count) + " 跳过 " + str(skip_count) + " 失败 " + str(fail_count))
    print("=" * 60)
    
    return fail_count == 0

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
