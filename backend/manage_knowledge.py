#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青藜伴读 知识库一键管理工具

子命令:
  doctor                       环境健康检查
  init-db [--reset]            初始化数据库
  migrate-db                   数据库迁移检查
  rebuild <course_code>        从JSON源文件一键重建数据库（可复现）
  validate <course_code>       校验单个课程
  validate-all [--policy]      校验所有课程 (dev/release 策略)
  status                       查看所有课程状态
  diff <course_code>           显示课程差异
  publish <course_code>         发布课程（10 步流程，支持 --dry-run）
  unpublish <course_code>       撤回发布
  sync-vectors <course_code>   同步 Qdrant 向量索引
  review list|approve|reject|status <course_code>  内容审核工作流
  report [--format]            生成知识库报告

退出码:
  0  通过
  1  校验失败
  2  环境错误

使用示例:
  python backend/manage_knowledge.py doctor
  python backend/manage_knowledge.py init-db
  python backend/manage_knowledge.py rebuild computer_network
  python backend/manage_knowledge.py validate-all --policy dev
  python backend/manage_knowledge.py validate-all --policy release
  python backend/manage_knowledge.py validate computer_network
  python backend/manage_knowledge.py status
  python backend/manage_knowledge.py diff computer_network
  python backend/manage_knowledge.py publish computer_network --dry-run
  python backend/manage_knowledge.py publish computer_network
  python backend/manage_knowledge.py unpublish computer_network --to review
  python backend/manage_knowledge.py sync-vectors computer_network --dry-run
  python backend/manage_knowledge.py sync-vectors computer_network --prune
  python backend/manage_knowledge.py report --format json
  python backend/manage_knowledge.py report --format markdown
"""
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import Optional, List, Dict

# 添加 backend 目录到 sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

KNOWLEDGE_BASE_DIR = os.path.join(BACKEND_DIR, 'knowledge_base')

# 课程发布状态映射（合法状态）
VALID_PUBLISH_STATUS = ['draft', 'review', 'published', 'demo_only', 'archived']

# 默认课程发布状态策略
DEFAULT_PUBLISH_POLICY = {
    'computer_network': 'published',
    'computer_organization': 'review',
    'database_principles': 'review',
    'data_structure': 'demo_only',
    'operating_system': 'demo_only',
}

# 前端显示策略
FRONTEND_DISPLAY = {
    'published': '完整显示',
    'review': '显示但标记审核中',
    'demo_only': '仅展示，不可作为完整课程学习',
    'draft': '不显示',
    'archived': '不显示',
}


def list_courses() -> List[str]:
    """列出所有课程目录"""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return []
    courses = []
    for name in sorted(os.listdir(KNOWLEDGE_BASE_DIR)):
        course_dir = os.path.join(KNOWLEDGE_BASE_DIR, name)
        if os.path.isdir(course_dir) and os.path.exists(
            os.path.join(course_dir, 'course.json')
        ):
            courses.append(name)
    return courses


def run_etl_dry_run(course_code: str) -> Dict:
    """对单个课程运行 ETL --dry-run 校验"""
    cmd = [
        sys.executable,
        os.path.join(BACKEND_DIR, 'import_knowledge_from_files.py'),
        '--course', course_code,
        '--dry-run',
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            cwd=BACKEND_DIR,
        )
        return {
            'course_code': course_code,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'passed': result.returncode == 0,
        }
    except Exception as e:
        return {
            'course_code': course_code,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'passed': False,
        }


# ============== 子命令: validate-all ==============

def cmd_validate_all(args) -> int:
    """对所有课程运行分级校验

    支持 --policy dev|release:
      dev:     开发策略，demo_only 课程允许"带警告通过"
      release: 发布策略，严格校验所有非 archived 课程
    """
    policy = getattr(args, 'policy', 'dev') or 'dev'
    if policy not in ('dev', 'release'):
        print("[ERROR] 非法 policy: " + policy + " (允许: dev, release)")
        return 2

    try:
        from services.validation_service import ValidationService, Severity
    except ImportError as e:
        print("[ERROR] 无法加载校验服务: " + str(e))
        return 2

    courses = list_courses()
    if not courses:
        print("[ERROR] 未找到任何课程")
        return 1

    print("=" * 70)
    print("分级校验所有课程 (policy=" + policy + ")")
    print("=" * 70)
    print("待校验课程: " + ", ".join(courses))
    print()

    service = ValidationService(policy=policy)
    report = service.validate_all()

    # 输出每课程结果
    for result in report.results:
        print("\n" + "-" * 70)
        status_tag = result.course_code + " [" + result.publish_status + "]"
        if result.passed and not result.passed_with_warnings:
            print("[PASS] " + status_tag)
        elif result.passed_with_warnings:
            print("[WARN] " + status_tag + " (带警告通过)")
        else:
            print("[FAIL] " + status_tag)

        for issue in result.issues:
            sev_str = {
                Severity.ERROR: 'ERROR',
                Severity.WARNING: 'WARN ',
                Severity.INFO: 'INFO ',
            }.get(issue.severity, '?    ')
            line = "  [" + sev_str + "] " + issue.code + ": " + issue.message
            try:
                print(line)
            except UnicodeEncodeError:
                print(line.encode('gbk', errors='replace').decode('gbk'))

    # 汇总
    print("\n" + "=" * 70)
    print("校验汇总 (policy=" + policy + ")")
    print("=" * 70)
    print("课程总数: " + str(len(report.results)))
    print("错误总数: " + str(report.total_errors))
    print("警告总数: " + str(report.total_warnings))
    print("通过: " + str(sum(1 for r in report.results if r.passed and not r.passed_with_warnings)))
    print("带警告通过: " + str(sum(1 for r in report.results if r.passed_with_warnings)))
    print("失败: " + str(sum(1 for r in report.results if not r.passed)))
    print("=" * 70)

    # dev 策略下，带警告通过也算整体通过
    if policy == 'dev':
        return 0 if all(r.passed for r in report.results) else 1
    else:
        # release 策略下：必须 0 错误（警告允许，因为不能伪造 source）
        # published 课程运行全部严格检查（已由 ValidationService 保证）
        return 0 if report.total_errors == 0 else 1


# ============== 子命令: validate (单课程) ==============

def cmd_validate(args) -> int:
    """校验单个课程"""
    course_code = args.course_code
    policy = getattr(args, 'policy', 'dev') or 'dev'
    if policy not in ('dev', 'release'):
        print("[ERROR] 非法 policy: " + policy)
        return 2

    try:
        from services.validation_service import ValidationService, Severity
    except ImportError as e:
        print("[ERROR] 无法加载校验服务: " + str(e))
        return 2

    if course_code not in list_courses():
        print("[ERROR] 课程不存在: " + course_code)
        return 1

    print("=" * 70)
    print("校验课程: " + course_code + " (policy=" + policy + ")")
    print("=" * 70)

    service = ValidationService(policy=policy)
    result = service.validate_course(course_code)

    if result.passed and not result.passed_with_warnings:
        print("[PASS] " + course_code + " 校验通过")
    elif result.passed_with_warnings:
        print("[WARN] " + course_code + " 带警告通过")
    else:
        print("[FAIL] " + course_code + " 校验失败")

    for issue in result.issues:
        sev_str = {
            Severity.ERROR: 'ERROR',
            Severity.WARNING: 'WARN ',
            Severity.INFO: 'INFO ',
        }.get(issue.severity, '?    ')
        line = "  [" + sev_str + "] " + issue.code + ": " + issue.message
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode('gbk', errors='replace').decode('gbk'))

    return 0 if result.passed else 1


# ============== 子命令: publish ==============

def cmd_publish(args) -> int:
    """发布课程（10 步流程，支持 --dry-run）

    用法:
      publish <course_code>              完整发布流程
      publish <course_code> --dry-run    模拟发布，不修改任何状态
      publish <course_code> --status <status>  设置指定状态（仅限非 published）

    退出码:
      0  发布成功
      1  校验失败 / 发布失败
      2  环境错误（如数据库未初始化）
    """
    course_code = args.course_code
    dry_run = getattr(args, 'dry_run', False)
    status = getattr(args, 'status', None)

    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code)
    course_file = os.path.join(course_dir, 'course.json')

    if not os.path.exists(course_file):
        print("[ERROR] 课程不存在: " + course_code)
        print("可用课程: " + ", ".join(list_courses()))
        return 1

    # 非 published 状态的简单切换（不走 10 步流程）
    if status is not None and status != 'published':
        if status not in VALID_PUBLISH_STATUS:
            print("[ERROR] 非法发布状态: " + status)
            print("合法状态: " + ", ".join(VALID_PUBLISH_STATUS))
            return 1
        return _set_status_simple(course_code, status)

    # published 状态：走完整 10 步流程
    try:
        from services.publish_service import PublishService
        from services.path_utils import DATABASE_PATH
    except ImportError as e:
        print("[ERROR] 无法加载发布服务: " + str(e))
        return 2

    # 非 dry-run 模式下，数据库必须已初始化
    if not dry_run:
        if not os.path.exists(str(DATABASE_PATH)):
            print("[ERROR] 数据库尚未初始化，请先执行:")
            print("        python backend/manage_knowledge.py init-db")
            print("        或执行数据库迁移")
            return 2

    if dry_run:
        print("=" * 70)
        print("DRY-RUN: 模拟发布课程 " + course_code)
        print("=" * 70)

    inject_failure = getattr(args, 'inject_failure', None)
    service = PublishService(dry_run=dry_run, inject_failure=inject_failure)
    result = service.publish_course(course_code)

    # 输出步骤
    for step in result.steps:
        if step.passed:
            tag = "[OK]   "
        else:
            tag = "[FAIL] "
        line = tag + step.name + " - " + step.message
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode('gbk', errors='replace').decode('gbk'))
        if not step.passed and step.error:
            try:
                print("        错误: " + step.error)
            except UnicodeEncodeError:
                print(("        错误: " + step.error).encode('gbk', errors='replace').decode('gbk'))

    # 输出回滚动作（如有）
    if result.rollback_actions:
        print("\n回滚动作:")
        for action in result.rollback_actions:
            print("  - " + action)

    # 输出蓝绿与溯源元数据
    if result.success and not dry_run:
        print("\n" + "-" * 70)
        print("蓝绿发布元数据:")
        print("  release_id:          " + result.release_id)
        print("  git_commit:          " + result.git_commit)
        print("  schema_version:      " + result.schema_version)
        print("  embedding_model:     " + result.embedding_model)
        print("  embedding_dimension: " + str(result.embedding_dimension))
        print("  qdrant_image:        " + result.qdrant_image)
        print("  staging_collection:  " + result.staging_collection)
        print("  active_collection:   " + result.active_collection)
        print("  previous_collection: " + result.previous_collection)
        print("  alias_name:          " + result.alias_name)
        print("  database_chunk_count:" + str(result.database_chunk_count))
        print("  qdrant_vector_count: " + str(result.qdrant_vector_count))
        print("  published_at:        " + result.published_at)

        # 保存发布报告到文件（答辩证据）
        try:
            reports_dir = os.path.join(os.path.dirname(BACKEND_DIR), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            report_file = os.path.join(
                reports_dir,
                'publish_' + course_code + '_' +
                datetime.utcnow().strftime('%Y%m%d%H%M%S') + '.json'
            )
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            print("\n发布报告已保存: " + report_file)
        except Exception as e:
            print("[WARN] 保存发布报告失败: " + str(e))

    # 汇总
    print("\n" + "=" * 70)
    if result.success:
        if dry_run:
            print("[PASS] DRY-RUN 通过: 课程 " + course_code + " 可以发布")
        else:
            print("[PASS] 课程 " + course_code + " 发布成功")
        if result.backup_path:
            print("数据库备份: " + result.backup_path)
    else:
        if result.rollback_performed:
            print("[FAIL] 课程 " + course_code + " 发布失败，已回滚")
        else:
            print("[FAIL] 课程 " + course_code + " 发布失败")
        if result.error:
            try:
                print("失败原因: " + result.error)
            except UnicodeEncodeError:
                print(("失败原因: " + result.error).encode('gbk', errors='replace').decode('gbk'))
    print("=" * 70)

    return 0 if result.success else 1


def _set_status_simple(course_code: str, status: str) -> int:
    """简单状态切换（非 published 流程）"""
    course_file = os.path.join(KNOWLEDGE_BASE_DIR, course_code, 'course.json')
    with open(course_file, 'r', encoding='utf-8') as f:
        course_data = json.load(f)

    old_status = course_data.get('publish_status', 'unknown')
    course_data['publish_status'] = status
    course_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d')

    with open(course_file, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, ensure_ascii=False, indent=2)

    print("[OK] " + course_code + ": " + old_status + " -> " + status)

    # 同步数据库
    try:
        from database import SessionLocal
        from models.database_models import Subject
        db = SessionLocal()
        try:
            subject = db.query(Subject).filter(Subject.course_code == course_code).first()
            if subject:
                subject.publish_status = status
                db.commit()
                print("[OK] 数据库已同步")
        finally:
            db.close()
    except Exception as e:
        print("[WARN] 数据库同步失败: " + str(e))

    return 0


# ============== 子命令: unpublish ==============

def cmd_unpublish(args) -> int:
    """撤回发布（将课程状态改回 draft 或 review）

    用法:
      unpublish <course_code>                撤回到 review
      unpublish <course_code> --to <status>  撤回到指定状态
    """
    course_code = args.course_code
    to_status = getattr(args, 'to', 'review') or 'review'

    if to_status not in ('draft', 'review', 'demo_only', 'archived'):
        print("[ERROR] 非法目标状态: " + to_status)
        return 1

    course_file = os.path.join(KNOWLEDGE_BASE_DIR, course_code, 'course.json')
    if not os.path.exists(course_file):
        print("[ERROR] 课程不存在: " + course_code)
        return 1

    with open(course_file, 'r', encoding='utf-8') as f:
        course_data = json.load(f)

    old_status = course_data.get('publish_status', 'unknown')
    if old_status != 'published':
        print("[WARN] 课程 " + course_code + " 当前状态 " + old_status + " 非 published")

    course_data['publish_status'] = to_status
    course_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d')

    with open(course_file, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, ensure_ascii=False, indent=2)

    print("[OK] " + course_code + ": " + old_status + " -> " + to_status)

    try:
        from database import SessionLocal
        from models.database_models import Subject
        db = SessionLocal()
        try:
            subject = db.query(Subject).filter(Subject.course_code == course_code).first()
            if subject:
                subject.publish_status = to_status
                db.commit()
                print("[OK] 数据库已同步")
        finally:
            db.close()
    except Exception as e:
        print("[WARN] 数据库同步失败: " + str(e))

    return 0


# ============== 子命令: sync-vectors ==============

def cmd_sync_vectors(args) -> int:
    """同步 Qdrant 向量索引（基于 course_code + chunk_hash 唯一标识）

    用法:
      sync-vectors <course_code>                增量同步
      sync-vectors <course_code> --dry-run      仅模拟，不写入
      sync-vectors <course_code> --prune        清理该课程孤立向量
      sync-vectors <course_code> --skip-embedding  跳过 Embedding
    """
    course_code = args.course_code
    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code)
    dry_run = getattr(args, 'dry_run', False)
    prune = getattr(args, 'prune', False)
    skip_embedding = getattr(args, 'skip_embedding', False)

    if not os.path.exists(course_dir):
        print("[ERROR] 课程目录不存在: " + course_code)
        return 1

    print("=" * 70)
    print("同步 Qdrant 向量索引: " + course_code)
    print("模式: " + ("DRY-RUN" if dry_run else "实际同步") +
          (" + PRUNE" if prune else ""))
    print("=" * 70)

    try:
        from database import SessionLocal
        from models.database_models import Subject, KnowledgeNode, SourceDocument, DocumentChunk
        from services.qdrant_sync_service import get_qdrant_sync_service

        db = SessionLocal()
        try:
            subject = db.query(Subject).filter(Subject.course_code == course_code).first()
            if not subject:
                print("[ERROR] 数据库中未找到课程: " + course_code)
                print("请先运行: python backend/import_knowledge_from_files.py --course " + course_code)
                return 1

            # 1. 文档分块（无 dry-run 限制，DB 操作可回滚）
            print("\n[1/4] 收集讲义文档并分块...")
            documents_dir = os.path.join(course_dir, 'documents')
            if not os.path.exists(documents_dir):
                print("  [WARN] 文档目录不存在: " + documents_dir)
                return 1

            doc_files = [f for f in os.listdir(documents_dir) if f.endswith('.md')]
            print("  找到 " + str(len(doc_files)) + " 个 Markdown 文档")

            # 解析蓝绿别名指向的集合（发布后别名存在，sync 通过别名操作）
            target_collection = None
            try:
                from services.qdrant_sync_service import BlueGreenCollectionManager
                from services.publish_service import connect_qdrant_with_retry
                _client = connect_qdrant_with_retry(max_retries=3)
                if _client is not None:
                    _bg = BlueGreenCollectionManager(_client)
                    _alias = _bg.alias_name(course_code)
                    for _a in _client.get_aliases().aliases:
                        if _a.alias_name == _alias:
                            target_collection = _a.collection_name
                            break
            except Exception:
                pass
            if target_collection:
                print("  目标集合(蓝绿别名): " + target_collection)
            else:
                print("  目标集合: qingli_docs (默认，别名未建立)")
            service = get_qdrant_sync_service(db, collection_name=target_collection)
            new_chunks = 0
            for doc_file in doc_files:
                doc_path = os.path.join(documents_dir, doc_file)
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                knowledge_node = db.query(KnowledgeNode).filter(
                    KnowledgeNode.subject_id == subject.id,
                    KnowledgeNode.name == os.path.splitext(doc_file)[0]
                ).first()

                source_doc, _ = service.register_source_document(
                    subject_id=subject.id,
                    title=doc_file,
                    content=content,
                    author=subject.name,
                    version='1.0',
                    section=doc_file,
                    license_type='unknown',
                    review_status='approved' if subject.publish_status == 'published' else 'pending',
                    reviewed_by='system',
                )
                chunks = service.sync_document_to_chunks(
                    source_doc=source_doc,
                    content=content,
                    knowledge_node_id=knowledge_node.id if knowledge_node else None,
                )
                new_chunks += len(chunks)
            db.commit()
            print("  新增切片: " + str(new_chunks))

            # 2. 增量同步 Qdrant（使用新的 sync_course_vectors）
            print("\n[2/4] 调用 sync_course_vectors...")
            if skip_embedding:
                print("  [SKIP] 跳过 Embedding (--skip-embedding)")
                # 直接做一致性检查
                consistency = service.consistency_check()
                report = {
                    'new_vectors': 0,
                    'updated_vectors': 0,
                    'unchanged': consistency['db_embedded_count'],
                    'to_delete': consistency['orphan_vector_count'],
                    'db_chunk_count': consistency['db_chunk_count'],
                    'qdrant_vector_count': consistency['qdrant_vector_count'],
                    'orphan_vector_count': consistency['orphan_vector_count'],
                    'missing_vector_count': consistency['missing_vector_count'],
                }
            else:
                report = service.sync_course_vectors(
                    course_code=course_code,
                    dry_run=dry_run,
                    prune=prune,
                    batch_size=100,
                )

            # 3. 输出同步报告
            print("\n[3/4] 同步报告")
            print("-" * 70)
            print("课程代码:           " + course_code)
            print("新增向量数:         " + str(report.get('new_vectors', 0)))
            print("更新向量数:         " + str(report.get('updated_vectors', 0)))
            print("未变化向量数:       " + str(report.get('unchanged', 0)))
            print("待删除向量数:       " + str(report.get('to_delete', 0)))
            print("数据库切片数:       " + str(report.get('db_chunk_count', 0)))
            print("Qdrant 向量数:      " + str(report.get('qdrant_vector_count', 0)))
            print("孤立向量数:         " + str(report.get('orphan_vector_count', 0)))
            print("缺失向量数:         " + str(report.get('missing_vector_count', 0)))
            if 'error' in report:
                print("错误: " + report['error'])

            # 4. 一致性状态（课程级：该课程切片数 == 别名集合中该课程向量数）
            print("\n[4/4] 一致性状态")
            course_consistent = (
                report.get('orphan_vector_count', 0) == 0 and
                report.get('missing_vector_count', 0) == 0 and
                report.get('db_chunk_count', 0) == report.get('qdrant_vector_count', 0)
            )
            print("  课程级一致性: " + ("PASS" if course_consistent else "FAIL"))
            print("  数据库切片数: " + str(report.get('db_chunk_count', 0)))
            print("  Qdrant 向量数: " + str(report.get('qdrant_vector_count', 0)))
            print("=" * 70)

            if 'error' in report:
                return 1
            return 0 if course_consistent or skip_embedding else 1
        finally:
            db.close()
    except Exception as e:
        print("[ERROR] 同步失败: " + str(e))
        import traceback
        traceback.print_exc()
        return 1


# ============== 子命令: review ==============

def cmd_review(args) -> int:
    """内容审核工作流

    用法:
      review list <course_code>                     列出待审核内容
      review approve <course_code> --item <id>       通过审核
      review reject  <course_code> --item <id> --reason <reason>  退回
      review status <course_code>                   查看审核进度
    """
    action = getattr(args, 'action', None)
    course_code = getattr(args, 'course_code', None)

    if action is None:
        print("[ERROR] 必须指定审核动作: list / approve / reject / status")
        return 1

    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code) if course_code else None
    if action != 'list_all' and (not course_dir or not os.path.exists(os.path.join(course_dir, 'course.json'))):
        print("[ERROR] 课程不存在: " + str(course_code))
        return 1

    if action == 'list':
        return _review_list(course_code, course_dir)
    elif action == 'approve':
        return _review_approve(course_code, course_dir, args)
    elif action == 'reject':
        return _review_reject(course_code, course_dir, args)
    elif action == 'status':
        return _review_status(course_code, course_dir)
    else:
        print("[ERROR] 未知审核动作: " + str(action))
        return 1


def _review_list(course_code, course_dir):
    """列出待审核内容"""
    print("=" * 70)
    print("待审核内容: " + course_code)
    print("=" * 70)

    items = []
    # 题库
    qb_file = os.path.join(course_dir, 'question_bank.json')
    if os.path.exists(qb_file):
        with open(qb_file, 'r', encoding='utf-8') as f:
            qb = json.load(f)
        for q in qb.get('questions', []):
            items.append({
                'type': 'question',
                'id': q.get('question_id') or q.get('id', ''),
                'title': (q.get('question', '') or '')[:40],
                'status': q.get('review_status', 'pending'),
                'reviewer': q.get('reviewed_by', ''),
            })

    # 错误模式
    ep_file = os.path.join(course_dir, 'error_patterns.json')
    if os.path.exists(ep_file):
        with open(ep_file, 'r', encoding='utf-8') as f:
            ep = json.load(f)
        for p in ep.get('error_patterns', ep.get('patterns', [])):
            items.append({
                'type': 'error_pattern',
                'id': p.get('error_id') or p.get('pattern_id') or p.get('id', ''),
                'title': p.get('error_name') or p.get('description', '')[:40],
                'status': p.get('review_status', 'pending'),
                'reviewer': p.get('reviewed_by', ''),
            })

    # 按状态分类
    pending = [i for i in items if i['status'] in ('pending', '', None)]
    approved = [i for i in items if i['status'] == 'approved']
    rejected = [i for i in items if i['status'] == 'rejected']

    print("\n[待审核] (" + str(len(pending)) + " 项)")
    for i in pending:
        print("  [" + i['type'] + "] " + i['id'] + " - " + i['title'])

    print("\n[已通过] (" + str(len(approved)) + " 项)")
    if approved and len(approved) <= 5:
        for i in approved:
            print("  [" + i['type'] + "] " + i['id'] + " - " + i['title'] + " (审核人: " + i['reviewer'] + ")")
    elif approved:
        for i in approved[:3]:
            print("  [" + i['type'] + "] " + i['id'] + " - " + i['title'] + " (审核人: " + i['reviewer'] + ")")
        print("  ... 共 " + str(len(approved)) + " 项")

    print("\n[已退回] (" + str(len(rejected)) + " 项)")
    for i in rejected:
        print("  [" + i['type'] + "] " + i['id'] + " - " + i['title'])

    print("\n总计: " + str(len(items)) + " 项, 通过率: " +
          ("%.1f%%" % (len(approved) / max(len(items), 1) * 100)))
    return 0


def _review_approve(course_code, course_dir, args):
    """通过审核"""
    item_id = getattr(args, 'item', None)
    reviewer = getattr(args, 'reviewer', None) or 'anonymous'
    item_type = getattr(args, 'type', None)

    if not item_id:
        print("[ERROR] 必须指定 --item <item_id>")
        return 1

    updated = _update_review_status(
        course_dir, item_id, item_type,
        new_status='approved',
        reviewer=reviewer,
        comment=getattr(args, 'comment', None) or '审核通过',
    )

    if updated == 0:
        print("[ERROR] 未找到项目: " + item_id + " (类型: " + str(item_type or 'any') + ")")
        return 1

    print("[OK] 已通过: " + item_id + " (审核人: " + reviewer + ")")
    print("     更新文件: " + str(updated) + " 个")
    return 0


def _review_reject(course_code, course_dir, args):
    """退回审核"""
    item_id = getattr(args, 'item', None)
    reviewer = getattr(args, 'reviewer', None) or 'anonymous'
    item_type = getattr(args, 'type', None)
    reason = getattr(args, 'reason', None)

    if not item_id:
        print("[ERROR] 必须指定 --item <item_id>")
        return 1
    if not reason:
        print("[ERROR] 必须指定 --reason <退回原因>")
        return 1

    updated = _update_review_status(
        course_dir, item_id, item_type,
        new_status='rejected',
        reviewer=reviewer,
        comment=reason,
    )

    if updated == 0:
        print("[ERROR] 未找到项目: " + item_id)
        return 1

    print("[OK] 已退回: " + item_id + " (审核人: " + reviewer + ")")
    print("     原因: " + reason)
    print("     更新文件: " + str(updated) + " 个")
    return 0


def _update_review_status(course_dir, item_id, item_type,
                           new_status, reviewer, comment):
    """更新指定项目的 review_status，返回更新文件数"""
    from datetime import datetime
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    updated = 0

    # 题库
    if item_type in (None, 'question'):
        qb_file = os.path.join(course_dir, 'question_bank.json')
        if os.path.exists(qb_file):
            with open(qb_file, 'r', encoding='utf-8') as f:
                qb = json.load(f)
            changed = False
            for q in qb.get('questions', []):
                qid = q.get('question_id') or q.get('id', '')
                if qid == item_id:
                    q['review_status'] = new_status
                    q['reviewed_by'] = reviewer
                    q['reviewed_at'] = now
                    q['review_comment'] = comment
                    changed = True
            if changed:
                with open(qb_file, 'w', encoding='utf-8') as f:
                    json.dump(qb, f, ensure_ascii=False, indent=2)
                updated += 1

    # 错误模式
    if item_type in (None, 'error_pattern'):
        ep_file = os.path.join(course_dir, 'error_patterns.json')
        if os.path.exists(ep_file):
            with open(ep_file, 'r', encoding='utf-8') as f:
                ep = json.load(f)
            changed = False
            patterns = ep.get('error_patterns', ep.get('patterns', []))
            for p in patterns:
                pid = p.get('error_id') or p.get('pattern_id') or p.get('id', '')
                if pid == item_id:
                    p['review_status'] = new_status
                    p['reviewed_by'] = reviewer
                    p['reviewed_at'] = now
                    p['review_comment'] = comment
                    changed = True
            if changed:
                with open(ep_file, 'w', encoding='utf-8') as f:
                    json.dump(ep, f, ensure_ascii=False, indent=2)
                updated += 1

    return updated


def _review_status(course_code, course_dir):
    """查看审核进度"""
    print("=" * 70)
    print("审核进度: " + course_code)
    print("=" * 70)

    # 读取 review_records.json
    rr_file = os.path.join(course_dir, 'review_records.json')
    if os.path.exists(rr_file):
        with open(rr_file, 'r', encoding='utf-8') as f:
            rr = json.load(f)
        summary = rr.get('review_summary', {})
        print("\n审核记录文件: review_records.json")
        print("  讲义总数: " + str(summary.get('total_documents', 0)))
        print("  题目总数: " + str(summary.get('total_questions', 0)))
        print("  错误模式总数: " + str(summary.get('total_error_patterns', 0)))
        print("  已通过讲义: " + str(summary.get('approved_documents', 0)))
        print("  已通过题目: " + str(summary.get('approved_questions', 0)))
        print("  已通过错误模式: " + str(summary.get('approved_error_patterns', 0)))
        print("  完成率: " + ("%.1f%%" % (summary.get('review_completion_rate', 0) * 100)))
        print("  最后审核: " + str(summary.get('last_review_date', '-')))
    else:
        print("\n[WARN] 未找到 review_records.json")

    # 实际文件中的审核状态
    print("\n实际文件状态:")
    qb_file = os.path.join(course_dir, 'question_bank.json')
    if os.path.exists(qb_file):
        with open(qb_file, 'r', encoding='utf-8') as f:
            qb = json.load(f)
        qs = qb.get('questions', [])
        approved = sum(1 for q in qs if q.get('review_status') == 'approved')
        print("  题库: " + str(approved) + "/" + str(len(qs)) + " 已通过")

    ep_file = os.path.join(course_dir, 'error_patterns.json')
    if os.path.exists(ep_file):
        with open(ep_file, 'r', encoding='utf-8') as f:
            ep = json.load(f)
        ps = ep.get('error_patterns', ep.get('patterns', []))
        approved = sum(1 for p in ps if p.get('review_status') == 'approved')
        print("  错误模式: " + str(approved) + "/" + str(len(ps)) + " 已通过")

    return 0


# ============== 子命令: report ==============

def cmd_report(args) -> int:
    """生成完整知识库报告（支持 --format json|markdown）

    用法:
      report                          生成报告并写入 reports/
      report --format json            仅输出 JSON
      report --format markdown        仅输出 Markdown
      report --course <code>          仅生成指定课程
    """
    fmt = getattr(args, 'format', 'markdown') or 'markdown'
    course_filter = getattr(args, 'course', None)

    if fmt not in ('json', 'markdown'):
        print("[ERROR] 非法格式: " + fmt + " (允许: json, markdown)")
        return 1

    # 收集报告数据
    report_data = _collect_report_data(course_filter)

    # 写入文件
    reports_dir = os.path.join(os.path.dirname(BACKEND_DIR), 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    json_path = os.path.join(reports_dir, 'knowledge_report.json')
    md_path = os.path.join(reports_dir, 'knowledge_report.md')

    # 总是写 JSON 文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print("[OK] JSON 报告: " + json_path)

    # 生成 Markdown
    md_content = _render_report_markdown(report_data)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print("[OK] Markdown 报告: " + md_path)

    # 控制台输出
    if fmt == 'json':
        print(json.dumps(report_data, ensure_ascii=False, indent=2))
    else:
        print(md_content)

    return 0


def _collect_report_data(course_filter: Optional[str]) -> dict:
    """收集报告数据"""
    courses = list_courses()
    if course_filter:
        courses = [c for c in courses if c == course_filter]

    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_courses': len(courses),
        'courses': [],
        'summary': {
            'total_knowledge_points': 0,
            'total_leaf_points': 0,
            'total_questions': 0,
            'total_documents': 0,
            'avg_lecture_coverage': 0.0,
            'avg_question_coverage': 0.0,
            'avg_source_coverage': 0.0,
            'avg_review_pass_rate': 0.0,
            'avg_dependency_completeness': 0.0,
        },
        'qdrant': {
            'db_chunk_count': 0,
            'qdrant_vector_count': 0,
            'orphan_vector_count': 0,
            'missing_vector_count': 0,
            'is_consistent': True,
        },
    }

    try:
        from database import SessionLocal
        from services.qdrant_sync_service import get_qdrant_sync_service
        db = SessionLocal()
        try:
            service = get_qdrant_sync_service(db)
            consistency = service.consistency_check()
            report['qdrant'] = {
                'db_chunk_count': consistency['db_chunk_count'],
                'qdrant_vector_count': consistency['qdrant_vector_count'],
                'orphan_vector_count': consistency['orphan_vector_count'],
                'missing_vector_count': consistency['missing_vector_count'],
                'is_consistent': consistency['is_consistent'],
            }
        finally:
            db.close()
    except Exception as e:
        report['qdrant']['error'] = str(e)

    total_lecture_cov = 0
    total_question_cov = 0
    total_source_cov = 0
    total_review_pass = 0
    total_dep_complete = 0

    for course in courses:
        course_data = _collect_course_report(course)
        report['courses'].append(course_data)
        report['summary']['total_knowledge_points'] += course_data.get('knowledge_point_count', 0)
        report['summary']['total_leaf_points'] += course_data.get('leaf_point_count', 0)
        report['summary']['total_questions'] += course_data.get('question_count', 0)
        report['summary']['total_documents'] += course_data.get('document_count', 0)
        total_lecture_cov += course_data.get('lecture_coverage', 0)
        total_question_cov += course_data.get('question_coverage', 0)
        total_source_cov += course_data.get('source_coverage', 0)
        total_review_pass += course_data.get('review_pass_rate', 0)
        total_dep_complete += course_data.get('dependency_completeness', 0)

    if courses:
        n = len(courses)
        report['summary']['avg_lecture_coverage'] = round(min(total_lecture_cov / n, 100.0), 2)
        report['summary']['avg_question_coverage'] = round(min(total_question_cov / n, 100.0), 2)
        report['summary']['avg_source_coverage'] = round(min(total_source_cov / n, 100.0), 2)
        report['summary']['avg_review_pass_rate'] = round(min(total_review_pass / n, 100.0), 2)
        report['summary']['avg_dependency_completeness'] = round(min(total_dep_complete / n, 100.0), 2)

    return report


def _collect_course_report(course: str) -> dict:
    """收集单课程报告"""
    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course)
    course_file = os.path.join(course_dir, 'course.json')

    data = {
        'course_code': course,
        'publish_status': 'unknown',
        'schema_version': '',
        'knowledge_point_count': 0,
        'leaf_point_count': 0,
        'lecture_coverage': 0.0,
        'question_coverage': 0.0,
        'source_coverage': 0.0,
        'review_pass_rate': 0.0,
        'dependency_completeness': 0.0,
        'db_chunk_count': 0,
        'qdrant_vector_count': 0,
        'orphan_vector_count': 0,
        'last_published_at': None,
    }

    if os.path.exists(course_file):
        with open(course_file, 'r', encoding='utf-8') as f:
            cd = json.load(f)
        data['publish_status'] = cd.get('publish_status', 'draft')
        data['schema_version'] = cd.get('schema_version', '')
        data['last_published_at'] = cd.get('last_updated')

    # 知识点统计
    tree_file = os.path.join(course_dir, 'knowledge_tree.json')
    if os.path.exists(tree_file):
        with open(tree_file, 'r', encoding='utf-8') as f:
            tree = json.load(f)
        leaf_count = 0
        total_count = 0

        def count(nodes):
            nonlocal leaf_count, total_count
            for n in nodes:
                total_count += 1
                if not n.get('children'):
                    leaf_count += 1
                else:
                    count(n.get('children', []))
        count(tree.get('roots', []))

        data['knowledge_point_count'] = total_count
        data['leaf_point_count'] = leaf_count

        # 讲义覆盖率
        docs_dir = os.path.join(course_dir, 'documents')
        doc_count = 0
        if os.path.exists(docs_dir):
            doc_count = len([f for f in os.listdir(docs_dir) if f.endswith('.md')])
        if leaf_count > 0:
            data['lecture_coverage'] = round(min(doc_count / leaf_count * 100, 100.0), 2)

    # 题库覆盖率与题目来源统计
    qb_file = os.path.join(course_dir, 'question_bank.json')
    if os.path.exists(qb_file):
        with open(qb_file, 'r', encoding='utf-8') as f:
            qb = json.load(f)
        questions = qb.get('questions', [])
        data['question_count'] = len(questions)
        if questions:
            with_kp = sum(1 for q in questions if q.get('knowledge_point_id'))
            data['question_coverage'] = round(min(with_kp / len(questions) * 100, 100.0), 2)

        # 题目来源统计
        q_total = len(questions)
        q_with_source = sum(1 for q in questions if q.get('source_ids'))
        q_missing_source = q_total - q_with_source
        data['question_source_stats'] = {
            'total': q_total,
            'with_source': q_with_source,
            'missing_source': q_missing_source,
            'coverage': round(min(q_with_source / max(q_total, 1) * 100, 100.0), 2),
        }
        # 题目审核统计
        q_approved = sum(1 for q in questions if q.get('review_status') == 'approved')
        data['question_review_stats'] = {
            'total': q_total,
            'approved': q_approved,
            'pending': q_total - q_approved,
            'pass_rate': round(min(q_approved / max(q_total, 1) * 100, 100.0), 2),
        }

    # 错误模式来源统计
    ep_file = os.path.join(course_dir, 'error_patterns.json')
    if os.path.exists(ep_file):
        with open(ep_file, 'r', encoding='utf-8') as f:
            ep = json.load(f)
        patterns = ep.get('error_patterns', ep.get('patterns', []))
        ep_total = len(patterns)
        ep_with_source = sum(1 for p in patterns if p.get('source_ids'))
        ep_missing_source = ep_total - ep_with_source
        data['error_pattern_source_stats'] = {
            'total': ep_total,
            'with_source': ep_with_source,
            'missing_source': ep_missing_source,
            'coverage': round(min(ep_with_source / max(ep_total, 1) * 100, 100.0), 2),
        }
        # 错误模式审核统计
        ep_approved = sum(1 for p in patterns if p.get('review_status') == 'approved')
        data['error_pattern_review_stats'] = {
            'total': ep_total,
            'approved': ep_approved,
            'pending': ep_total - ep_approved,
            'pass_rate': round(min(ep_approved / max(ep_total, 1) * 100, 100.0), 2),
        }

        # 整体来源追溯率（题库+错误模式综合）
        if 'question_count' in data and data['question_count'] > 0:
            total_items = data['question_count'] + ep_total
            total_with_source = (
                data['question_source_stats']['with_source'] + ep_with_source
            )
            data['source_coverage'] = round(
                min(total_with_source / max(total_items, 1) * 100, 100.0), 2)
        else:
            data['source_coverage'] = round(
                min(ep_with_source / max(ep_total, 1) * 100, 100.0), 2)

        # 整体审核通过率
        if 'question_count' in data and data['question_count'] > 0:
            total_items = data['question_count'] + ep_total
            total_approved = (
                data['question_review_stats']['approved'] + ep_approved
            )
            data['review_pass_rate'] = round(
                min(total_approved / max(total_items, 1) * 100, 100.0), 2)
        else:
            data['review_pass_rate'] = round(
                min(ep_approved / max(ep_total, 1) * 100, 100.0), 2)

    # 讲义来源统计（检查 documents 目录中每个 md 是否在 sources.json 中关联）
    sources_file = os.path.join(course_dir, 'sources.json')
    docs_dir = os.path.join(course_dir, 'documents')
    if os.path.exists(docs_dir):
        docs = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
        data['document_source_stats'] = {
            'total': len(docs),
            'with_source': len(docs) if os.path.exists(sources_file) else 0,
            'missing_source': 0 if os.path.exists(sources_file) else len(docs),
            'coverage': 100.0 if os.path.exists(sources_file) else 0.0,
        }

    # 依赖完整率
    deps_file = os.path.join(course_dir, 'dependencies.json')
    if os.path.exists(deps_file) and os.path.exists(tree_file):
        with open(deps_file, 'r', encoding='utf-8') as f:
            deps = json.load(f)
        all_deps = deps.get('dependencies', [])
        if all_deps:
            # 收集所有知识点 id
            all_ids = set()
            with open(tree_file, 'r', encoding='utf-8') as f:
                tree = json.load(f)
            def collect_ids(nodes):
                for n in nodes:
                    nid = n.get('id')
                    if nid:
                        all_ids.add(nid)
                    collect_ids(n.get('children', []))
            collect_ids(tree.get('roots', []))

            valid = sum(1 for d in all_deps
                        if (d.get('source_id') or d.get('source')) in all_ids
                        and (d.get('target_id') or d.get('target')) in all_ids)
            data['dependency_completeness'] = round(min(valid / len(all_deps) * 100, 100.0), 2)

    return data


def _render_report_markdown(report: dict) -> str:
    """渲染 Markdown 报告"""
    lines = []
    lines.append("# 青藜伴读 知识库报告")
    lines.append("")
    lines.append("生成时间: " + report.get('generated_at', ''))
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("| --- | --- |")
    lines.append("| 课程总数 | " + str(report.get('total_courses', 0)) + " |")
    lines.append("| 知识点数 | " + str(report['summary'].get('total_knowledge_points', 0)) + " |")
    lines.append("| 叶子知识点数 | " + str(report['summary'].get('total_leaf_points', 0)) + " |")
    lines.append("| 题目总数 | " + str(report['summary'].get('total_questions', 0)) + " |")
    lines.append("| 文档总数 | " + str(report['summary'].get('total_documents', 0)) + " |")
    lines.append("| 平均讲义覆盖率 | " + str(report['summary'].get('avg_lecture_coverage', 0)) + "% |")
    lines.append("| 平均题目覆盖率 | " + str(report['summary'].get('avg_question_coverage', 0)) + "% |")
    lines.append("| 平均来源追溯率 | " + str(report['summary'].get('avg_source_coverage', 0)) + "% |")
    lines.append("| 平均审核通过率 | " + str(report['summary'].get('avg_review_pass_rate', 0)) + "% |")
    lines.append("| 平均依赖完整率 | " + str(report['summary'].get('avg_dependency_completeness', 0)) + "% |")
    lines.append("")
    lines.append("## Qdrant 一致性")
    lines.append("")
    qd = report.get('qdrant', {})
    lines.append("| 指标 | 值 |")
    lines.append("| --- | --- |")
    lines.append("| 数据库切片数 | " + str(qd.get('db_chunk_count', 0)) + " |")
    lines.append("| Qdrant 向量数 | " + str(qd.get('qdrant_vector_count', 0)) + " |")
    lines.append("| 孤立向量数 | " + str(qd.get('orphan_vector_count', 0)) + " |")
    lines.append("| 缺失向量数 | " + str(qd.get('missing_vector_count', 0)) + " |")
    lines.append("| 一致性 | " + ("PASS" if qd.get('is_consistent') else "FAIL") + " |")
    lines.append("")
    lines.append("## 各课程详情")
    lines.append("")
    lines.append("| 课程 | 状态 | Schema | 知识点 | 叶子 | 讲义覆盖 | 题目覆盖 | 来源追溯 | 审核通过 | 依赖完整 | 最后发布 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for c in report.get('courses', []):
        lines.append("| " + c.get('course_code', '') +
                    " | " + c.get('publish_status', '') +
                    " | " + str(c.get('schema_version', '')) +
                    " | " + str(c.get('knowledge_point_count', 0)) +
                    " | " + str(c.get('leaf_point_count', 0)) +
                    " | " + str(c.get('lecture_coverage', 0)) + "%" +
                    " | " + str(c.get('question_coverage', 0)) + "%" +
                    " | " + str(c.get('source_coverage', 0)) + "%" +
                    " | " + str(c.get('review_pass_rate', 0)) + "%" +
                    " | " + str(c.get('dependency_completeness', 0)) + "%" +
                    " | " + str(c.get('last_published_at', '')) + " |")
    lines.append("")
    lines.append("## 来源缺失明细")
    lines.append("")
    lines.append("| 课程 | 题目总数 | 题目缺来源 | 题目来源率 | 错误模式总数 | 错误模式缺来源 | 错误模式来源率 | 讲义总数 | 讲义缺来源 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for c in report.get('courses', []):
        q_stats = c.get('question_source_stats', {'total': 0, 'missing_source': 0, 'coverage': 0})
        ep_stats = c.get('error_pattern_source_stats', {'total': 0, 'missing_source': 0, 'coverage': 0})
        d_stats = c.get('document_source_stats', {'total': 0, 'missing_source': 0, 'coverage': 0})
        lines.append("| " + c.get('course_code', '') +
                    " | " + str(q_stats.get('total', 0)) +
                    " | " + str(q_stats.get('missing_source', 0)) +
                    " | " + str(q_stats.get('coverage', 0)) + "%" +
                    " | " + str(ep_stats.get('total', 0)) +
                    " | " + str(ep_stats.get('missing_source', 0)) +
                    " | " + str(ep_stats.get('coverage', 0)) + "%" +
                    " | " + str(d_stats.get('total', 0)) +
                    " | " + str(d_stats.get('missing_source', 0)) + " |")
    lines.append("")
    lines.append("## 审核进度明细")
    lines.append("")
    lines.append("| 课程 | 题目总数 | 题目已审 | 题目审核率 | 错误模式总数 | 错误模式已审 | 错误模式审核率 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for c in report.get('courses', []):
        q_rv = c.get('question_review_stats', {'total': 0, 'approved': 0, 'pass_rate': 0})
        ep_rv = c.get('error_pattern_review_stats', {'total': 0, 'approved': 0, 'pass_rate': 0})
        lines.append("| " + c.get('course_code', '') +
                    " | " + str(q_rv.get('total', 0)) +
                    " | " + str(q_rv.get('approved', 0)) +
                    " | " + str(q_rv.get('pass_rate', 0)) + "%" +
                    " | " + str(ep_rv.get('total', 0)) +
                    " | " + str(ep_rv.get('approved', 0)) +
                    " | " + str(ep_rv.get('pass_rate', 0)) + "% |")
    lines.append("")
    return '\n'.join(lines)


# ============== 子命令: rebuild ==============

def cmd_rebuild(args) -> int:
    """从 JSON 源文件一键重建指定课程的数据库（可复现）

    用法:
      rebuild <course_code>            清空并重建该课程的知识点、讲义、习题
      rebuild <course_code> --dry-run  仅统计，不写入数据库

    重建依据（单一数据源）：
      knowledge_base/<course_code>/knowledge_tree.json
      knowledge_base/<course_code>/course.json
      knowledge_base/<course_code>/question_bank.json
      knowledge_base/<course_code>/documents/*.md
    """
    course_code_arg = args.course_code
    dry_run = getattr(args, 'dry_run', False)

    # 在 Windows GBK 终端下安全打印 emoji
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 70)
    print("从 JSON 重建课程知识库: " + course_code_arg)
    print("=" * 70)

    try:
        from services.path_utils import DATABASE_PATH
        from database import SessionLocal, Base, engine
        from models.database_models import Subject, KnowledgeNode
    except ImportError as e:
        print("[ERROR] 无法加载数据库模块: " + str(e))
        return 2

    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code_arg)
    if not os.path.isdir(course_dir):
        print("[ERROR] 课程目录不存在: " + course_dir)
        return 2

    tree_path = os.path.join(course_dir, 'knowledge_tree.json')
    course_path = os.path.join(course_dir, 'course.json')
    qb_path = os.path.join(course_dir, 'question_bank.json')
    docs_dir = os.path.join(course_dir, 'documents')

    for p in [tree_path, course_path, qb_path]:
        if not os.path.isfile(p):
            print("[ERROR] 缺少必需文件: " + p)
            return 2

    with open(tree_path, encoding='utf-8') as f:
        tree = json.load(f)
    with open(course_path, encoding='utf-8') as f:
        course_data = json.load(f)
    with open(qb_path, encoding='utf-8') as f:
        qb_data = json.load(f)

    roots = tree.get('roots', [])
    if not roots:
        print("[ERROR] knowledge_tree.json 的 roots 为空")
        return 1

    # 统计
    stats = {'chapters': 0, 'nodes': 0, 'leaves': 0, 'with_lecture': 0, 'with_exercises': 0}

    def walk(node, depth=0):
        stats['nodes'] += 1
        if depth == 0:
            stats['chapters'] += 1
        children = node.get('children', [])
        if not children:
            stats['leaves'] += 1
        for c in children:
            walk(c, depth + 1)

    for r in roots:
        walk(r)

    md_files = []
    if os.path.isdir(docs_dir):
        md_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
    stats['documents'] = len(md_files)

    qb_questions = qb_data.get('questions', [])
    stats['questions'] = len(qb_questions)

    print("[INFO] 章节数: " + str(stats['chapters']))
    print("[INFO] 总节点数: " + str(stats['nodes']))
    print("[INFO] 叶子节点数: " + str(stats['leaves']))
    print("[INFO] Markdown 文档: " + str(stats['documents']))
    print("[INFO] 题库题目: " + str(stats['questions']))

    if dry_run:
        print("[DRY-RUN] 未写入数据库")
        return 0

    # 确保表已存在
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        course_name = course_data.get('course_name', course_data.get('name', course_code_arg))
        # 清空旧数据
        subject = db.query(Subject).filter(Subject.course_code == course_code_arg).first()
        if not subject:
            subject = db.query(Subject).filter(Subject.name == course_name).first()
        if subject:
            db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id).delete()
            # 更新描述等字段
            subject.name = course_name
            subject.course_code = course_code_arg
            subject.description = course_data.get('description', '')
            subject.icon = 'BOOK'
            subject.education_level = 'university'
            subject.full_score = 100
        else:
            subject = Subject(
                name=course_name,
                course_code=course_code_arg,
                description=course_data.get('description', ''),
                icon='BOOK',
                education_level='university',
                full_score=100
            )
            db.add(subject)
            db.commit()
            db.refresh(subject)

        # 题目按知识点ID分组
        questions_by_kp = {}
        for q in qb_questions:
            kp_id = q.get('knowledge_point_id', '')
            questions_by_kp.setdefault(kp_id, []).append(q)

        def normalize_name(name):
            return name.replace('/', '').replace('\\', '').replace(' ', '').replace('-', '')

        def find_doc(node_name):
            normalized = normalize_name(node_name)
            if not normalized or not os.path.isdir(docs_dir):
                return None
            for doc_file in os.listdir(docs_dir):
                if not doc_file.endswith('.md'):
                    continue
                doc_stem = os.path.splitext(doc_file)[0]
                norm_doc = normalize_name(doc_stem)
                if normalized in norm_doc or norm_doc in normalized:
                    try:
                        with open(os.path.join(docs_dir, doc_file), encoding='utf-8') as f:
                            return f.read()
                    except Exception:
                        continue
            return None

        def process_node(node, parent_id=None):
            node_name = node.get('name', node.get('label', ''))
            node_code = node.get('node_code') or node.get('id') or ('node_' + str(hash(node_name)))
            kn = KnowledgeNode(
                subject_id=subject.id,
                parent_id=parent_id,
                node_code=node_code,
                name=node_name,
                description=node.get('description', ''),
                difficulty=node.get('difficulty', 0.5),
                mastery=node.get('mastery', 0.0),
                education_level='university',
                grade=''
            )
            db.add(kn)
            db.commit()
            db.refresh(kn)

            # 讲义：优先匹配 Markdown 文档
            content = find_doc(node_name)
            if content and len(content) > 50:
                kn.lecture_text = content
                stats['with_lecture'] += 1
            elif node.get('lecture_text') and 'error' not in node.get('lecture_text', '').lower():
                kn.lecture_text = node.get('lecture_text')
                stats['with_lecture'] += 1

            # 习题
            kp_id = node.get('id', '')
            if kp_id in questions_by_kp:
                exercises = []
                for q in questions_by_kp[kp_id]:
                    options = [opt.get('text', '') for opt in q.get('options', [])]
                    exercises.append({
                        'question': q.get('question', ''),
                        'options': options,
                        'answer': q.get('answer', ''),
                        'explanation': q.get('analysis', ''),
                        'difficulty': q.get('difficulty', 0.5)
                    })
                if exercises:
                    kn.exercises_json = json.dumps(exercises, ensure_ascii=False)
                    stats['with_exercises'] += 1

            db.commit()
            for child in node.get('children', []):
                process_node(child, parent_id=kn.id)

        for chapter in roots:
            process_node(chapter)

        db.commit()
        print("")
        print("[OK] 重建完成")
        print("     章节: " + str(stats['chapters']))
        print("     总节点: " + str(stats['nodes']))
        print("     叶子节点: " + str(stats['leaves']))
        print("     讲义填充: " + str(stats['with_lecture']))
        print("     习题填充: " + str(stats['with_exercises']))
        print("     数据库: " + str(DATABASE_PATH))
        return 0
    except Exception as e:
        db.rollback()
        print("[ERROR] 重建失败: " + str(e))
        return 2
    finally:
        db.close()


# ============== 子命令: gen-flashcards ==============

def cmd_gen_flashcards(args) -> int:
    """批量生成闪卡（仅给没有闪卡的叶子节点生成）

    用法:
      gen-flashcards <course_code>              给所有缺闪卡的叶子节点生成
      gen-flashcards <course_code> --dry-run    仅统计，不调用 LLM
      gen-flashcards <course_code> --limit 5    只生成前 5 个节点（测试用）
    """
    course_code_arg = args.course_code
    dry_run = getattr(args, 'dry_run', False)
    limit = getattr(args, 'limit', 0) or 0

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 70)
    print("批量生成闪卡: " + course_code_arg)
    print("=" * 70)

    try:
        from services.path_utils import DATABASE_PATH
        from database import SessionLocal
        from models.database_models import Subject, KnowledgeNode
    except ImportError as e:
        print("[ERROR] 无法加载数据库模块: " + str(e))
        return 2

    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.course_code == course_code_arg).first()
        if not subject:
            print("[ERROR] 课程不存在: " + course_code_arg)
            return 2

        # 找出所有缺闪卡的叶子节点
        leaves = db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id == subject.id,
            KnowledgeNode.parent_id.isnot(None)
        ).all()
        missing = [n for n in leaves if not n.flash_cards_json]
        print("[INFO] 叶子节点总数: " + str(len(leaves)))
        print("[INFO] 已有闪卡: " + str(len(leaves) - len(missing)))
        print("[INFO] 缺失闪卡: " + str(len(missing)))

        if limit > 0:
            missing = missing[:limit]
            print("[INFO] --limit 限制: 仅处理前 " + str(len(missing)) + " 个")

        if dry_run:
            print("[DRY-RUN] 未调用 LLM")
            return 0

        if not missing:
            print("[OK] 所有节点都有闪卡，无需生成")
            return 0

        # 延迟导入，避免影响其他子命令
        from api.db_routes import _build_flash_prompt
        from utils.llm_client import invoke_llm
        import json as _json

        success = 0
        failed = 0
        for i, node in enumerate(missing, 1):
            print("[" + str(i) + "/" + str(len(missing)) + "] 生成: " + node.name, end=" ... ", flush=True)
            try:
                edu_level = node.education_level or 'university'
                level_label = '大学' if edu_level != 'high_school' else '高中'
                flash_prompt = _build_flash_prompt(subject.name, level_label, node.name)
                raw = invoke_llm(flash_prompt, system_message='你是闪卡专家，只返回纯JSON数组，不要任何解释或代码块标记。')
                raw = (raw or '').strip()
                if raw.startswith('```'):
                    raw = raw.strip('`')
                    if 'json' in raw[:20].lower():
                        raw = raw[raw.find('['):]
                start = raw.find('[')
                if start >= 0:
                    end = raw.rfind(']')
                    if end > start:
                        raw = raw[start:end + 1]
                flash_cards = _json.loads(raw) if start >= 0 else []
                if flash_cards:
                    node.flash_cards_json = _json.dumps(flash_cards, ensure_ascii=False)
                    db.commit()
                    success += 1
                    print("OK (" + str(len(flash_cards)) + " 张)")
                else:
                    failed += 1
                    print("FAILED (空)")
            except Exception as e:
                failed += 1
                db.rollback()
                print("ERROR: " + str(e)[:80])

        print("")
        print("[OK] 完成: 成功 " + str(success) + ", 失败 " + str(failed))
        return 0 if success > 0 else 2
    finally:
        db.close()


# ============== 子命令: init-db ==============

def cmd_init_db(args) -> int:
    """初始化数据库（建表，不导入数据）

    用法:
      init-db              创建数据库与所有表
      init-db --reset      删除并重建数据库（危险！会丢失数据）
    """
    print("=" * 70)
    print("初始化数据库")
    print("=" * 70)

    try:
        from services.path_utils import DATABASE_PATH, BACKEND_DIR
        from database import Base, engine
        from sqlalchemy import inspect
    except ImportError as e:
        print("[ERROR] 无法加载数据库模块: " + str(e))
        return 2

    reset = getattr(args, 'reset', False)

    if reset:
        if os.path.exists(str(DATABASE_PATH)):
            print("[WARN] 删除现有数据库: " + str(DATABASE_PATH))
            os.remove(str(DATABASE_PATH))

    # 创建表
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print("[ERROR] 建表失败: " + str(e))
        return 2

    # 验证表
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("[OK] 数据库已创建: " + str(DATABASE_PATH))
    print("     表数量: " + str(len(tables)))
    if tables:
        print("     表: " + ", ".join(sorted(tables)))

    print("\n下一步:")
    print("  1. 执行数据迁移/导入: python backend/manage_knowledge.py migrate-db")
    print("  2. 发布课程: python backend/manage_knowledge.py publish <course_code>")
    return 0


# ============== 子命令: migrate-db ==============

def cmd_migrate_db(args) -> int:
    """数据库迁移占位（后续接入 Alembic）

    当前实现：检查表结构是否齐全，并补建缺失表。
    """
    print("=" * 70)
    print("数据库迁移检查")
    print("=" * 70)

    try:
        from services.path_utils import DATABASE_PATH
        from database import Base, engine
        from sqlalchemy import inspect
    except ImportError as e:
        print("[ERROR] 无法加载数据库模块: " + str(e))
        return 2

    if not os.path.exists(str(DATABASE_PATH)):
        print("[ERROR] 数据库尚未初始化")
        print("        请先执行: python backend/manage_knowledge.py init-db")
        return 2

    # 当前实现：补建缺失表（未来替换为 alembic upgrade head）
    try:
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("[OK] 迁移完成")
        print("     表数量: " + str(len(tables)))
        # 未来版本检查
        print("[INFO] 当前迁移版本: v1 (create_all)")
        print("[TODO] 未来将接入 Alembic 进行版本化迁移")
        return 0
    except Exception as e:
        print("[ERROR] 迁移失败: " + str(e))
        return 2


# ============== 子命令: doctor ==============

def cmd_doctor(args) -> int:
    """环境健康检查

    检查项:
      1. Python 版本
      2. 关键依赖
      3. Git 钩子配置
      4. 知识库目录
      5. 数据库文件
      6. Qdrant 连接
      7. 关键 Python 模块导入
    """
    print("=" * 70)
    print("青藜伴读 环境健康检查")
    print("=" * 70)
    print()

    all_pass = True

    # 1. Python 版本
    print("[1/7] Python 版本检查")
    pv = sys.version_info
    py_ok = pv >= (3, 8)
    print("  当前: " + str(pv.major) + "." + str(pv.minor) + "." + str(pv.micro))
    print("  要求: >= 3.8")
    print("  状态: " + ("OK" if py_ok else "FAIL"))
    if not py_ok:
        all_pass = False
    print()

    # 2. 关键依赖
    print("[2/7] 关键依赖检查")
    deps = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('qdrant_client', 'Qdrant Client'),
    ]
    for mod_name, display in deps:
        try:
            __import__(mod_name)
            print("  [OK] " + display)
        except ImportError:
            print("  [FAIL] " + display + " (pip install " + mod_name.replace('_', '-') + ")")
            all_pass = False
    print()

    # 3. Git 钩子配置
    print("[3/7] Git 钩子配置检查")
    try:
        import subprocess
        repo_root = os.path.dirname(BACKEND_DIR)
        result = subprocess.run(
            ['git', 'config', 'core.hooksPath'],
            cwd=repo_root,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
        )
        hooks_path = result.stdout.strip() if result.returncode == 0 else ''
        if hooks_path == '.githooks':
            print("  [OK] core.hooksPath = .githooks")
            # 检查钩子文件存在
            pre_commit = os.path.join(repo_root, '.githooks', 'pre-commit')
            pre_push = os.path.join(repo_root, '.githooks', 'pre-push')
            if os.path.exists(pre_commit):
                print("  [OK] .githooks/pre-commit 存在")
            else:
                print("  [FAIL] .githooks/pre-commit 不存在")
                all_pass = False
            if os.path.exists(pre_push):
                print("  [OK] .githooks/pre-push 存在")
            else:
                print("  [FAIL] .githooks/pre-push 不存在")
                all_pass = False
        else:
            print("  [FAIL] core.hooksPath = " + (hooks_path or '(未设置)') + " (期望 .githooks)")
            print("  修复: python backend/scripts/install_precommit.py")
            all_pass = False
    except Exception as e:
        print("  [FAIL] " + str(e))
        all_pass = False
    print()

    # 4. 知识库目录
    print("[4/7] 知识库目录检查")
    if os.path.exists(KNOWLEDGE_BASE_DIR):
        courses = list_courses()
        print("  [OK] 知识库目录存在")
        print("  课程数: " + str(len(courses)))
        for c in courses:
            course_file = os.path.join(KNOWLEDGE_BASE_DIR, c, 'course.json')
            if os.path.exists(course_file):
                with open(course_file, 'r', encoding='utf-8') as f:
                    cd = json.load(f)
                print("    - " + c + " [" + cd.get('publish_status', 'unknown') + "]")
            else:
                print("    - " + c + " [MISSING course.json]")
                all_pass = False
    else:
        print("  [FAIL] 知识库目录不存在: " + KNOWLEDGE_BASE_DIR)
        all_pass = False
    print()

    # 5. 数据库文件
    print("[5/7] 数据库文件检查")
    db_path = os.path.join(BACKEND_DIR, 'database', 'magicstudy.db')
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print("  [OK] " + db_path + " (" + str(size) + " bytes)")
    else:
        print("  [WARN] 数据库文件不存在 (将自动创建)")
    print()

    # 6. Qdrant 连接
    print("[6/7] Qdrant 连接检查")
    try:
        from database import SessionLocal
        from services.qdrant_sync_service import get_qdrant_sync_service
        db = SessionLocal()
        try:
            service = get_qdrant_sync_service(db)
            if service.qdrant_client is not None:
                print("  [OK] Qdrant 客户端已配置")
                # 尝试获取集合信息
                try:
                    info = service.qdrant_client.get_collection('magicstudy_docs')
                    print("  [OK] 集合 magicstudy_docs 存在")
                except Exception:
                    print("  [WARN] 集合 magicstudy_docs 不存在 (将在首次同步时创建)")
            else:
                print("  [WARN] Qdrant 客户端未配置 (降级为无向量模式)")
        finally:
            db.close()
    except Exception as e:
        print("  [WARN] " + str(e))
    print()

    # 7. 模块导入
    print("[7/7] 关键模块导入检查")
    modules = [
        ('services.validation_service', 'ValidationService'),
        ('services.publish_service', 'PublishService'),
        ('services.qdrant_sync_service', 'QdrantSyncService'),
        ('services.path_utils', 'path_utils'),
    ]
    for mod_path, display in modules:
        try:
            __import__(mod_path)
            print("  [OK] " + display)
        except ImportError as e:
            print("  [FAIL] " + display + ": " + str(e))
            all_pass = False
    print()

    # 汇总
    print("=" * 70)
    if all_pass:
        print("[PASS] 环境检查全部通过")
        return 0
    else:
        print("[FAIL] 环境检查存在问题")
        return 1
    print("=" * 70)


# ============== 子命令: status ==============

def cmd_status(args) -> int:
    """快速查看所有课程状态"""
    courses = list_courses()
    if not courses:
        print("[ERROR] 未找到任何课程")
        return 1

    print("=" * 70)
    print("青藜伴读 课程状态")
    print("=" * 70)
    print("-" * 70)
    print("课程代码".ljust(25) + " 状态".ljust(12) + " Schema".ljust(10) + " 最后更新")
    print("-" * 70)

    status_count = {}
    for course in courses:
        course_file = os.path.join(KNOWLEDGE_BASE_DIR, course, 'course.json')
        with open(course_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        status = data.get('publish_status', 'unknown')
        schema = data.get('schema_version', '')
        updated = data.get('last_updated', '')
        status_count[status] = status_count.get(status, 0) + 1
        print(
            course.ljust(25) + " " +
            status.ljust(12) + " " +
            schema.ljust(10) + " " +
            updated
        )

    print("-" * 70)
    print("状态分布:")
    for status, count in sorted(status_count.items()):
        print("  " + status + ": " + str(count))
    print("=" * 70)
    return 0


# ============== 子命令: diff ==============

def cmd_diff(args) -> int:
    """显示课程的待提交变更（对比 JSON 文件与数据库）"""
    course_code = args.course_code
    course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course_code)

    if not os.path.exists(course_dir):
        print("[ERROR] 课程不存在: " + course_code)
        return 1

    print("=" * 70)
    print("课程 " + course_code + " 差异对比")
    print("=" * 70)

    # 1. JSON 文件统计
    print("\n[1] JSON 文件统计")
    json_files = ['course.json', 'knowledge_tree.json', 'dependencies.json',
                   'question_bank.json', 'error_patterns.json', 'resources.json']
    for fn in json_files:
        path = os.path.join(course_dir, fn)
        if os.path.exists(path):
            size = os.path.getsize(path)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict):
                        count = sum(len(v) for v in data.values() if isinstance(v, list))
                    else:
                        count = len(data) if hasattr(data, '__len__') else 0
                    print("  " + fn.ljust(25) + " " + str(count).rjust(5) + " 项  " + str(size) + " bytes")
                except json.JSONDecodeError as e:
                    print("  " + fn.ljust(25) + " [JSON 解析错误]: " + str(e))
        else:
            print("  " + fn.ljust(25) + " [MISSING]")

    # 2. 文档数
    docs_dir = os.path.join(course_dir, 'documents')
    if os.path.exists(docs_dir):
        docs = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
        print("\n[2] 文档数: " + str(len(docs)))

    # 3. 数据库对比
    print("\n[3] 数据库对比")
    try:
        from database import SessionLocal
        from models.database_models import Subject, KnowledgeNode, SourceDocument, DocumentChunk
        db = SessionLocal()
        try:
            subject = db.query(Subject).filter(Subject.course_code == course_code).first()
            if not subject:
                print("  数据库中未找到课程: " + course_code)
                print("  请先运行: python backend/import_knowledge_from_files.py --course " + course_code)
                return 0

            kn_count = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id).count()
            sd_count = db.query(SourceDocument).filter(SourceDocument.subject_id == subject.id).count()

            # 课程下所有切片
            dc_count = db.query(DocumentChunk).join(
                SourceDocument, DocumentChunk.source_doc_id == SourceDocument.id
            ).filter(SourceDocument.subject_id == subject.id).count()

            print("  数据库 publish_status: " + (subject.publish_status or 'NULL'))
            print("  JSON    publish_status: " + self_read_json_status(course_code))
            print("  知识点 (DB): " + str(kn_count))
            print("  来源文档 (DB): " + str(sd_count))
            print("  切片数 (DB): " + str(dc_count))
        finally:
            db.close()
    except Exception as e:
        print("  [ERROR] " + str(e))

    print("\n" + "=" * 70)
    return 0


def self_read_json_status(course_code: str) -> str:
    """读取 JSON 中的 publish_status"""
    course_file = os.path.join(KNOWLEDGE_BASE_DIR, course_code, 'course.json')
    if not os.path.exists(course_file):
        return 'MISSING'
    with open(course_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('publish_status', 'unknown')


# ============== 主程序 ==============

def main():
    parser = argparse.ArgumentParser(
        description='MagicStudy 知识库一键管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # doctor
    subparsers.add_parser('doctor', help='环境健康检查')

    # init-db
    p_init = subparsers.add_parser('init-db', help='初始化数据库')
    p_init.add_argument('--reset', action='store_true', help='删除并重建数据库')

    # migrate-db
    subparsers.add_parser('migrate-db', help='数据库迁移检查')

    # rebuild
    p_rebuild = subparsers.add_parser('rebuild', help='从 JSON 源文件一键重建课程知识库（可复现）')
    p_rebuild.add_argument('course_code', help='课程代码')
    p_rebuild.add_argument('--dry-run', action='store_true', help='仅统计，不写入数据库')

    # gen-flashcards (批量生成闪卡)
    p_gfc = subparsers.add_parser('gen-flashcards', help='批量给缺闪卡的叶子节点生成 AI 闪卡')
    p_gfc.add_argument('course_code', help='课程代码')
    p_gfc.add_argument('--dry-run', action='store_true', help='仅统计，不调用 LLM')
    p_gfc.add_argument('--limit', type=int, default=0, help='只处理前 N 个节点（测试用，0=全部）')

    # validate (单课程)
    p_validate = subparsers.add_parser('validate', help='校验单个课程')
    p_validate.add_argument('course_code', help='课程代码')
    p_validate.add_argument('--policy', default='dev',
                            choices=['dev', 'release'],
                            help='校验策略: dev (默认) 或 release')
    
    # validate-all
    p_validate_all = subparsers.add_parser('validate-all', help='校验所有课程')
    p_validate_all.add_argument('--policy', default='dev',
                                 choices=['dev', 'release'],
                                 help='校验策略: dev (默认，允许带警告通过) 或 release (严格)')
    
    # status
    subparsers.add_parser('status', help='查看所有课程状态')
    
    # diff
    p_diff = subparsers.add_parser('diff', help='显示课程差异')
    p_diff.add_argument('course_code', help='课程代码')
    
    # publish
    p_publish = subparsers.add_parser('publish', help='发布课程（10 步蓝绿流程）')
    p_publish.add_argument('course_code', help='课程代码')
    p_publish.add_argument('--status', help='指定状态 (非 published 简单切换)')
    p_publish.add_argument('--dry-run', action='store_true', help='模拟发布，不修改状态')
    p_publish.add_argument('--inject-failure', dest='inject_failure',
                           help='故障注入点 (仅 MAGICSTUDY_TEST_MODE=1 时允许): '
                                'after_database_backup/after_database_write/'
                                'after_staging_collection_created/after_vectors_uploaded/'
                                'before_alias_swap/after_alias_swap/before_cleanup')
    
    # unpublish
    p_unpublish = subparsers.add_parser('unpublish', help='撤回发布')
    p_unpublish.add_argument('course_code', help='课程代码')
    p_unpublish.add_argument('--to', default='review',
                              help='目标状态 (默认 review)')
    
    # sync-vectors
    p_sync = subparsers.add_parser('sync-vectors', help='同步 Qdrant 向量索引')
    p_sync.add_argument('course_code', help='课程代码')
    p_sync.add_argument('--dry-run', action='store_true', help='模拟同步，不写入')
    p_sync.add_argument('--prune', action='store_true', help='清理孤立向量')
    p_sync.add_argument('--skip-embedding', action='store_true', help='跳过 Embedding')

    # review
    p_review = subparsers.add_parser('review', help='内容审核工作流')
    review_sub = p_review.add_subparsers(dest='action')
    p_review_list = review_sub.add_parser('list', help='列出待审核内容')
    p_review_list.add_argument('course_code', help='课程代码')
    p_review_approve = review_sub.add_parser('approve', help='通过审核')
    p_review_approve.add_argument('course_code', help='课程代码')
    p_review_approve.add_argument('--item', required=True, help='项目 ID')
    p_review_approve.add_argument('--type', choices=['question', 'error_pattern'],
                                  help='项目类型')
    p_review_approve.add_argument('--reviewer', default='anonymous', help='审核人')
    p_review_approve.add_argument('--comment', help='审核意见')
    p_review_reject = review_sub.add_parser('reject', help='退回审核')
    p_review_reject.add_argument('course_code', help='课程代码')
    p_review_reject.add_argument('--item', required=True, help='项目 ID')
    p_review_reject.add_argument('--type', choices=['question', 'error_pattern'],
                                  help='项目类型')
    p_review_reject.add_argument('--reviewer', default='anonymous', help='审核人')
    p_review_reject.add_argument('--reason', required=True, help='退回原因')
    p_review_status = review_sub.add_parser('status', help='查看审核进度')
    p_review_status.add_argument('course_code', help='课程代码')

    # report
    p_report = subparsers.add_parser('report', help='生成知识库报告')
    p_report.add_argument('--format', default='markdown',
                           choices=['json', 'markdown'],
                           help='输出格式 (默认 markdown)')
    p_report.add_argument('--course', help='仅生成指定课程')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    if args.command == 'doctor':
        return cmd_doctor(args)
    elif args.command == 'init-db':
        return cmd_init_db(args)
    elif args.command == 'migrate-db':
        return cmd_migrate_db(args)
    elif args.command == 'rebuild':
        return cmd_rebuild(args)
    elif args.command == 'gen-flashcards':
        return cmd_gen_flashcards(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'validate-all':
        return cmd_validate_all(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'diff':
        return cmd_diff(args)
    elif args.command == 'publish':
        return cmd_publish(args)
    elif args.command == 'unpublish':
        return cmd_unpublish(args)
    elif args.command == 'sync-vectors':
        return cmd_sync_vectors(args)
    elif args.command == 'review':
        return cmd_review(args)
    elif args.command == 'report':
        return cmd_report(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
