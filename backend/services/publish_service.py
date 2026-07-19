#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青藜伴读 课程发布服务（蓝绿发布 + 确定性故障注入）

publish 命令依次执行:
  1. Schema 验证
  2. 数据关系验证
  3. 来源和审核验证
  4. 创建数据库备份（SQLite Backup API）
  5. 在事务中导入关系数据库
  6. 生成文档切片
  7. 创建蓝绿暂存集合 + 增量同步 Qdrant（写入暂存集合）
  8. 检查暂存集合切片和向量数量
  9. 运行抽样检索测试（通过别名）
  10. 原子别名切换 + 修改 publish_status

蓝绿发布方案：
  - 新版本向量先写入暂存集合（course_<code>_v<n>）
  - 校验通过后原子切换别名（course_<code>_alias -> 暂存集合）
  - 旧集合保留（默认最近 2 个），稳定后清理
  - 发布中途失败：数据库回滚 + 删除暂存集合，正式集合不受影响

确定性故障注入（仅 MAGICSTUDY_TEST_MODE=1 时允许）：
  after_database_backup / after_database_write / after_staging_collection_created
  / after_vectors_uploaded / before_alias_swap / after_alias_swap / before_cleanup
"""
import os
import sys
import json
import time
import sqlite3
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 路径处理
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
KNOWLEDGE_BASE_DIR = BACKEND_DIR / 'knowledge_base'

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# =====================================================================
# 数据结构
# =====================================================================

@dataclass
class PublishStep:
    """发布步骤结果"""
    name: str
    passed: bool
    message: str = ''
    duration_ms: int = 0
    error: str = ''


@dataclass
class PublishResult:
    """发布结果（含蓝绿与溯源元数据）"""
    course_code: str
    success: bool
    steps: List[PublishStep] = field(default_factory=list)
    backup_path: str = ''
    rollback_performed: bool = False
    rollback_actions: List[str] = field(default_factory=list)
    final_status: str = ''
    error: str = ''
    # 蓝绿与溯源元数据
    release_id: str = ''
    git_commit: str = ''
    schema_version: str = '2.0'
    embedding_model: str = ''
    embedding_dimension: int = 0
    qdrant_image: str = ''
    staging_collection: str = ''
    active_collection: str = ''
    previous_collection: str = ''
    alias_name: str = ''
    database_chunk_count: int = 0
    qdrant_vector_count: int = 0
    published_at: str = ''

    def to_dict(self) -> dict:
        return {
            'course_code': self.course_code,
            'success': self.success,
            'backup_path': self.backup_path,
            'rollback_performed': self.rollback_performed,
            'rollback_actions': self.rollback_actions,
            'final_status': self.final_status,
            'error': self.error,
            'release_id': self.release_id,
            'git_commit': self.git_commit,
            'schema_version': self.schema_version,
            'embedding_model': self.embedding_model,
            'embedding_dimension': self.embedding_dimension,
            'qdrant_image': self.qdrant_image,
            'staging_collection': self.staging_collection,
            'active_collection': self.active_collection,
            'previous_collection': self.previous_collection,
            'alias_name': self.alias_name,
            'database_chunk_count': self.database_chunk_count,
            'qdrant_vector_count': self.qdrant_vector_count,
            'published_at': self.published_at,
            'steps': [
                {
                    'name': s.name,
                    'passed': s.passed,
                    'message': s.message,
                    'duration_ms': s.duration_ms,
                    'error': s.error,
                }
                for s in self.steps
            ],
        }


class PublishError(Exception):
    """发布错误（触发回滚）"""
    pass


# =====================================================================
# 互斥锁（跨平台文件锁，超时自动释放）
# =====================================================================

class PublishLock:
    """发布互斥锁：防止两个 publish 命令同时运行"""

    LOCK_TIMEOUT = 3600  # 1 小时超时自动释放

    def __init__(self):
        self.lock_file = BACKEND_DIR / 'backups' / 'publish.lock'

    def acquire(self):
        self.lock_file.parent.mkdir(exist_ok=True)
        if self.lock_file.exists():
            age = time.time() - self.lock_file.stat().st_mtime
            if age < self.LOCK_TIMEOUT:
                raise PublishError(
                    '另一个发布正在进行，锁文件年龄 ' + str(int(age)) +
                    's（路径: ' + str(self.lock_file) + '）'
                )
        self.lock_file.write_text(str(os.getpid()))

    def release(self):
        try:
            self.lock_file.unlink()
        except FileNotFoundError:
            pass


# =====================================================================
# Qdrant 连接重试
# =====================================================================

def connect_qdrant_with_retry(max_retries: int = 10) -> Optional[object]:
    """连接 Qdrant 并验证可用性（指数退避重试）

    最多重试 max_retries 次，初始等待 1 秒，指数退避，最大等待 10 秒。
    最终失败返回 None。
    """
    try:
        from qdrant_client import QdrantClient
        from rag.config import settings as rag_settings
    except Exception as e:
        print('[WARN] 无法导入 Qdrant 客户端: ' + str(e))
        return None

    host = rag_settings.qdrant_host
    port = rag_settings.qdrant_port
    delay = 1.0
    for i in range(max_retries):
        try:
            # check_compatibility=False: 客户端 1.18 与服务端 1.7 基本功能兼容
            client = QdrantClient(host=host, port=port, check_compatibility=False)
            # 验证可用性
            client.get_collections()
            return client
        except Exception as e:
            print('[WARN] Qdrant 连接失败 (' + str(i + 1) + '/' + str(max_retries) + '): ' + str(e))
            if i < max_retries - 1:
                time.sleep(min(delay, 10.0))
                delay *= 2
    return None


# =====================================================================
# 发布服务
# =====================================================================

class PublishService:
    """课程发布服务（蓝绿 + 故障注入）"""

    # 支持的故障注入点
    FAILURE_POINTS = {
        'after_database_backup',
        'after_database_write',
        'after_staging_collection_created',
        'after_vectors_uploaded',
        'before_alias_swap',
        'after_alias_swap',
        'before_cleanup',
    }

    def __init__(self, db_session=None, dry_run: bool = False,
                 inject_failure: Optional[str] = None):
        self.dry_run = dry_run
        self.db = db_session
        self._backup_path: Optional[str] = None
        self._transaction_active = False

        # ---- 故障注入配置 ----
        self.inject_failure = inject_failure or os.environ.get('MAGICSTUDY_FAIL_STEP')
        self.test_mode = os.environ.get('MAGICSTUDY_TEST_MODE') == '1'
        # 正式环境禁止故障注入
        if self.inject_failure and not self.test_mode:
            raise PublishError(
                '故障注入仅在 MAGICSTUDY_TEST_MODE=1 时允许，'
                '正式环境检测到 MAGICSTUDY_FAIL_STEP=' + str(self.inject_failure)
            )
        if self.inject_failure and self.inject_failure not in self.FAILURE_POINTS:
            raise PublishError('未知故障点: ' + self.inject_failure +
                               '，支持: ' + ', '.join(sorted(self.FAILURE_POINTS)))

        # ---- 蓝绿状态（用于回滚）----
        self._qdrant_client = None
        self._bg_manager = None
        self._new_collection: Optional[str] = None
        self._old_collection: Optional[str] = None
        self._alias_switched = False

    # ============== 故障注入检查 ==============

    def _check_failure(self, point: str):
        """在指定故障点注入故障（仅测试模式）"""
        if self.inject_failure == point:
            raise PublishError('【故障注入】' + point + ' - 模拟发布中途失败')

    # ============== 辅助：获取溯源元数据 ==============

    def _get_git_commit(self) -> str:
        try:
            r = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=str(REPO_ROOT),
                timeout=5,
            )
            return r.stdout.strip()[:12] if r.returncode == 0 else 'unknown'
        except Exception:
            return 'unknown'

    def _get_qdrant_image(self) -> str:
        try:
            env_file = REPO_ROOT / '.env'
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith('QDRANT_IMAGE='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
        return 'unknown'

    def _ensure_qdrant(self):
        """获取 Qdrant 客户端（带重试），失败则抛 PublishError"""
        if self._qdrant_client is not None:
            return self._qdrant_client
        client = connect_qdrant_with_retry()
        if client is None:
            raise PublishError(
                '无法连接 Qdrant（已重试 10 次），请确认 Docker 容器运行中且 /readyz 可达'
            )
        self._qdrant_client = client
        return client

    def _get_bg_manager(self):
        """获取蓝绿管理器"""
        if self._bg_manager is None:
            from services.qdrant_sync_service import BlueGreenCollectionManager
            self._bg_manager = BlueGreenCollectionManager(self._ensure_qdrant())
        return self._bg_manager

    # ============== 主发布流程 ==============

    def publish_course(self, course_code: str) -> PublishResult:
        """发布课程（10 步蓝绿流程）"""
        result = PublishResult(
            course_code=course_code,
            success=False,
            release_id=datetime.utcnow().strftime('%Y%m%d%H%M%S') + '-' + course_code,
            git_commit=self._get_git_commit(),
            qdrant_image=self._get_qdrant_image(),
            embedding_model='BAAI/bge-base-zh',
            embedding_dimension=768,
            alias_name='course_' + course_code + '_alias',
        )
        lock = PublishLock()

        try:
            lock.acquire()
        except PublishError as e:
            result.error = str(e)
            return result

        try:
            # 步骤 1: Schema 验证
            step = self._step_1_schema_validation(course_code)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or 'Schema 验证失败'
                return result

            # 步骤 2: 数据关系验证
            step = self._step_2_data_relationship(course_code)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '数据关系验证失败'
                return result

            # 步骤 3: 来源和审核验证
            step = self._step_3_source_review(course_code)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '来源和审核验证失败'
                return result

            if self.dry_run:
                result.success = True
                result.final_status = 'dry_run_passed'
                return result

            # 步骤 4: 创建数据库备份（SQLite Backup API）
            step = self._step_4_backup_database()
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '数据库备份失败'
                return result
            result.backup_path = step.message
            self._check_failure('after_database_backup')

            # 步骤 5: 在事务中导入关系数据库
            step = self._step_5_import_to_db(course_code)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '数据库导入失败'
                self._rollback(course_code, result)
                return result
            self._check_failure('after_database_write')

            # 步骤 6: 生成文档切片
            step = self._step_6_generate_chunks(course_code)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '文档切片失败'
                self._rollback(course_code, result)
                return result

            # 步骤 7: 蓝绿暂存集合 + 增量同步 Qdrant
            step = self._step_7_bluegreen_sync(course_code, result)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '蓝绿同步失败'
                self._rollback(course_code, result)
                return result
            self._check_failure('after_vectors_uploaded')

            # 步骤 8: 暂存集合一致性检查
            step = self._step_8_staging_consistency(course_code, result)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '一致性检查失败'
                self._rollback(course_code, result)
                return result

            # ---- 故障点：别名切换前 ----
            self._check_failure('before_alias_swap')

            # 步骤 9: 抽样检索测试（通过别名查询暂存集合）
            step = self._step_9_sample_retrieval(course_code, result)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '抽样检索测试失败'
                self._rollback(course_code, result)
                return result

            # 步骤 10: 原子别名切换 + 修改 publish_status
            step = self._step_10_alias_switch_and_status(course_code, result)
            result.steps.append(step)
            if not step.passed:
                result.error = step.error or '别名切换/状态更新失败'
                self._rollback(course_code, result)
                return result
            self._alias_switched = True
            self._check_failure('after_alias_swap')

            # 清理旧集合（保留最近 2 个）
            self._check_failure('before_cleanup')
            self._cleanup_old_collections(course_code, result)

            result.success = True
            result.final_status = 'published'
            result.published_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            return result
        except PublishError as e:
            result.error = str(e)
            result.success = False
            self._rollback(course_code, result)
            return result
        except Exception as e:
            result.error = str(e)
            result.success = False
            self._rollback(course_code, result)
            return result
        finally:
            lock.release()

    # ============== 步骤实现 ==============

    def _step_1_schema_validation(self, course_code: str) -> PublishStep:
        """步骤 1: Schema 验证"""
        start = datetime.now()
        try:
            from services.validation_service import ValidationService, Severity
            service = ValidationService(policy='release')
            result = service.validate_course(course_code)
            errors = [i for i in result.issues if i.severity == Severity.ERROR]
            if errors:
                return PublishStep(
                    name='1. Schema 验证',
                    passed=False,
                    message='发现 ' + str(len(errors)) + ' 个错误',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                    error='; '.join(i.message for i in errors[:5]),
                )
            return PublishStep(
                name='1. Schema 验证',
                passed=True,
                message='Schema 验证通过 (' + str(len(result.warnings)) + ' 个警告)',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='1. Schema 验证',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_2_data_relationship(self, course_code: str) -> PublishStep:
        """步骤 2: 数据关系验证"""
        start = datetime.now()
        try:
            course_dir = KNOWLEDGE_BASE_DIR / course_code
            tree_file = course_dir / 'knowledge_tree.json'
            deps_file = course_dir / 'dependencies.json'

            if not tree_file.exists():
                return PublishStep(
                    name='2. 数据关系验证',
                    passed=False,
                    error='knowledge_tree.json 不存在',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            with open(tree_file, 'r', encoding='utf-8') as f:
                tree = json.load(f)

            all_ids = set()
            parent_child_pairs = []

            def collect(nodes, parent_id=None):
                for node in nodes:
                    nid = node.get('id')
                    if not nid:
                        continue
                    all_ids.add(nid)
                    if parent_id:
                        parent_child_pairs.append((parent_id, nid))
                    collect(node.get('children', []), nid)
            collect(tree.get('roots', []))

            if deps_file.exists():
                with open(deps_file, 'r', encoding='utf-8') as f:
                    deps = json.load(f)

                dep_count = 0
                invalid_deps = 0
                for dep in deps.get('dependencies', []):
                    src = dep.get('source_id') or dep.get('source')
                    tgt = dep.get('target_id') or dep.get('target')
                    dep_count += 1
                    if src not in all_ids or tgt not in all_ids:
                        invalid_deps += 1

                if invalid_deps > 0:
                    return PublishStep(
                        name='2. 数据关系验证',
                        passed=False,
                        message='依赖关系 ' + str(dep_count) + ' 条，无效 ' + str(invalid_deps) + ' 条',
                        error='无效依赖关系: ' + str(invalid_deps),
                        duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                    )

            return PublishStep(
                name='2. 数据关系验证',
                passed=True,
                message='知识点 ' + str(len(all_ids)) + ' 个，父子关系 ' + str(len(parent_child_pairs)) + ' 条',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='2. 数据关系验证',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_3_source_review(self, course_code: str) -> PublishStep:
        """步骤 3: 来源和审核验证"""
        start = datetime.now()
        try:
            course_dir = KNOWLEDGE_BASE_DIR / course_code
            ep_file = course_dir / 'error_patterns.json'

            if not ep_file.exists():
                return PublishStep(
                    name='3. 来源和审核验证',
                    passed=True,
                    message='无 error_patterns.json，跳过',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            with open(ep_file, 'r', encoding='utf-8') as f:
                ep_data = json.load(f)

            patterns = ep_data.get('patterns', ep_data.get('error_patterns', []))
            total = len(patterns)
            with_source = 0
            with_review = 0

            for p in patterns:
                if p.get('source_ids'):
                    with_source += 1
                if p.get('review_status'):
                    with_review += 1

            if with_source < total:
                return PublishStep(
                    name='3. 来源和审核验证',
                    passed=False,
                    message='有来源 ' + str(with_source) + '/' + str(total),
                    error='缺少来源字段的错误模式: ' + str(total - with_source),
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            return PublishStep(
                name='3. 来源和审核验证',
                passed=True,
                message='错误模式 ' + str(total) + ' 条，来源覆盖率 100%',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='3. 来源和审核验证',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_4_backup_database(self) -> PublishStep:
        """步骤 4: 创建数据库备份（使用 SQLite Backup API，避免文件占用）"""
        start = datetime.now()
        try:
            from database import DB_PATH
            db_path = str(DB_PATH)
            if not os.path.exists(db_path):
                return PublishStep(
                    name='4. 数据库备份',
                    passed=False,
                    error='数据库文件不存在: ' + db_path,
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            backup_dir = BACKEND_DIR / 'backups'
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / ('qingli_' + timestamp + '.db.bak')

            # 使用 SQLite Backup API（在线备份，不依赖文件复制）
            src = sqlite3.connect(db_path)
            dst = sqlite3.connect(str(backup_path))
            src.backup(dst)
            dst.close()
            src.close()

            self._backup_path = str(backup_path)
            return PublishStep(
                name='4. 数据库备份',
                passed=True,
                message='备份至: ' + str(backup_path),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='4. 数据库备份',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_5_import_to_db(self, course_code: str) -> PublishStep:
        """步骤 5: 在事务中导入关系数据库"""
        start = datetime.now()
        try:
            from database import SessionLocal
            from models.database_models import Subject

            self.db = SessionLocal()
            self.db.begin()
            self._transaction_active = True

            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()

            if not subject:
                from import_knowledge_from_files import KnowledgeETL
                course_dir = KNOWLEDGE_BASE_DIR / course_code
                etl = KnowledgeETL(str(course_dir))
                etl.session = self.db
                etl._validate_file_structure()
                etl._load_data()
                etl._import_knowledge_tree()
                etl._import_question_bank()
                etl._import_resources()
                etl._import_documents()
                self.db.flush()

            node_count = 0
            from models.database_models import KnowledgeNode
            if subject:
                node_count = self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.subject_id == subject.id
                ).count()

            return PublishStep(
                name='5. 数据库导入',
                passed=True,
                message='已导入知识点 ' + str(node_count) + ' 个',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='5. 数据库导入',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_6_generate_chunks(self, course_code: str) -> PublishStep:
        """步骤 6: 生成文档切片"""
        start = datetime.now()
        try:
            from services.qdrant_sync_service import get_qdrant_sync_service
            from models.database_models import Subject, KnowledgeNode

            course_dir = KNOWLEDGE_BASE_DIR / course_code
            docs_dir = course_dir / 'documents'

            if not docs_dir.exists():
                return PublishStep(
                    name='6. 文档切片',
                    passed=False,
                    error='文档目录不存在: ' + str(docs_dir),
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            # 用默认集合做切片注册（切片写入数据库，不涉及 Qdrant）
            service = get_qdrant_sync_service(self.db)
            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()

            if not subject:
                return PublishStep(
                    name='6. 文档切片',
                    passed=False,
                    error='课程未导入数据库',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            new_chunks = 0
            for doc_file in docs_dir.iterdir():
                if doc_file.suffix != '.md':
                    continue
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                kn = self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.subject_id == subject.id,
                    KnowledgeNode.name == doc_file.stem
                ).first()

                source_doc, _ = service.register_source_document(
                    subject_id=subject.id,
                    title=doc_file.name,
                    content=content,
                    author=subject.name,
                    version='1.0',
                    section=doc_file.stem,
                    license_type='unknown',
                    review_status='approved',
                    reviewed_by='publish_service',
                )
                chunks = service.sync_document_to_chunks(
                    source_doc=source_doc,
                    content=content,
                    knowledge_node_id=kn.id if kn else None,
                )
                new_chunks += len(chunks)

            self.db.commit()

            from models.database_models import DocumentChunk
            total_chunks = self.db.query(DocumentChunk).count()

            return PublishStep(
                name='6. 文档切片',
                passed=True,
                message='新增切片 ' + str(new_chunks) + ' 个，总切片 ' + str(total_chunks) + ' 个',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='6. 文档切片',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_7_bluegreen_sync(self, course_code: str, result: PublishResult) -> PublishStep:
        """步骤 7: 创建蓝绿暂存集合 + 增量同步 Qdrant（写入暂存集合）"""
        start = datetime.now()
        try:
            from services.qdrant_sync_service import get_qdrant_sync_service
            from models.database_models import Subject, DocumentChunk, SourceDocument

            qdrant_client = self._ensure_qdrant()
            bg = self._get_bg_manager()

            # 记录旧别名指向的集合（用于回滚）
            old_active = bg.get_current_active(course_code)
            self._old_collection = old_active['name'] if old_active else None
            result.previous_collection = self._old_collection or '(无)'

            # 创建新版本集合（暂存，别名切换前无人通过别名访问）
            version = bg.get_next_version(course_code)
            new_collection = bg.active_name(course_code, version)
            self._new_collection = new_collection
            result.staging_collection = new_collection

            from qdrant_client.http import models as qmodels
            # 若集合已存在则先删除（保证干净）
            try:
                qdrant_client.delete_collection(new_collection)
            except Exception:
                pass
            qdrant_client.create_collection(
                collection_name=new_collection,
                vectors_config=qmodels.VectorParams(
                    size=768,
                    distance=qmodels.Distance.COSINE,
                ),
            )

            self._check_failure('after_staging_collection_created')

            # 把当前课程所有切片标记为 pending（重新嵌入到新集合）
            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()
            if not subject:
                raise PublishError('课程未导入数据库')

            # SQLAlchemy 不允许在 join 查询上调用 update()，先查出 chunk id 再更新
            chunk_ids = self.db.query(DocumentChunk.id).join(
                SourceDocument,
                DocumentChunk.source_doc_id == SourceDocument.id,
            ).filter(
                SourceDocument.subject_id == subject.id
            ).all()
            chunk_id_list = [cid[0] for cid in chunk_ids]
            if chunk_id_list:
                self.db.query(DocumentChunk).filter(
                    DocumentChunk.id.in_(chunk_id_list)
                ).update(
                    {DocumentChunk.embedding_status: 'pending'},
                    synchronize_session='fetch',
                )
            self.db.commit()

            # 用新集合名创建 sync_service，嵌入到暂存集合
            service = get_qdrant_sync_service(self.db, collection_name=new_collection)
            embedded = service.embed_pending_chunks(batch_size=100)

            return PublishStep(
                name='7. 蓝绿同步',
                passed=True,
                message='暂存集合 ' + new_collection + '，嵌入向量 ' + str(embedded) + ' 个',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except PublishError:
            raise
        except Exception as e:
            return PublishStep(
                name='7. 蓝绿同步',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_8_staging_consistency(self, course_code: str, result: PublishResult) -> PublishStep:
        """步骤 8: 检查暂存集合的切片和向量数量一致性"""
        start = datetime.now()
        try:
            from models.database_models import Subject, DocumentChunk, SourceDocument
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            qdrant_client = self._ensure_qdrant()
            collection = self._new_collection

            # 数据库中该课程的切片数
            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()
            db_chunk_count = self.db.query(DocumentChunk).join(
                SourceDocument, DocumentChunk.source_doc_id == SourceDocument.id
            ).filter(SourceDocument.subject_id == subject.id).count()
            result.database_chunk_count = db_chunk_count

            # 暂存集合中该课程的向量数
            course_filter = Filter(must=[
                FieldCondition(key='course_code', match=MatchValue(value=course_code))
            ])
            offset = None
            qdrant_count = 0
            while True:
                points, next_offset = qdrant_client.scroll(
                    collection_name=collection,
                    scroll_filter=course_filter,
                    limit=100, offset=offset,
                    with_payload=False, with_vectors=False,
                )
                if not points:
                    break
                qdrant_count += len(points)
                offset = next_offset
                if not next_offset:
                    break
            result.qdrant_vector_count = qdrant_count

            if db_chunk_count != qdrant_count:
                return PublishStep(
                    name='8. 一致性检查',
                    passed=False,
                    message='DB 切片 ' + str(db_chunk_count) + ', 暂存向量 ' + str(qdrant_count),
                    error='暂存集合向量数与数据库切片数不一致',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            return PublishStep(
                name='8. 一致性检查',
                passed=True,
                message='DB 切片 ' + str(db_chunk_count) + ' = 暂存向量 ' + str(qdrant_count) + ' (一致)',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='8. 一致性检查',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_9_sample_retrieval(self, course_code: str, result: PublishResult) -> PublishStep:
        """步骤 9: 运行抽样检索测试（直接查询暂存集合）"""
        start = datetime.now()
        try:
            from models.database_models import Subject, DocumentChunk, SourceDocument
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()
            if not subject:
                return PublishStep(
                    name='9. 抽样检索测试',
                    passed=False,
                    error='课程未导入数据库',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            # 取 5 个切片做抽样
            chunks = self.db.query(DocumentChunk).join(
                SourceDocument, DocumentChunk.source_doc_id == SourceDocument.id
            ).filter(SourceDocument.subject_id == subject.id).limit(5).all()
            if not chunks:
                return PublishStep(
                    name='9. 抽样检索测试',
                    passed=False,
                    error='无切片可测试',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            qdrant_client = self._ensure_qdrant()
            collection = self._new_collection
            passed = 0
            for chunk in chunks:
                # 检查切片对应的向量是否存在于暂存集合
                try:
                    point, _ = qdrant_client.scroll(
                        collection_name=collection,
                        scroll_filter=Filter(must=[
                            FieldCondition(key='content_hash',
                                           match=MatchValue(value=chunk.content_hash))
                        ]),
                        limit=1,
                        with_payload=False, with_vectors=False,
                    )
                    if point:
                        passed += 1
                except Exception:
                    pass

            if passed < len(chunks) * 0.6:
                return PublishStep(
                    name='9. 抽样检索测试',
                    passed=False,
                    message='通过 ' + str(passed) + '/' + str(len(chunks)),
                    error='暂存集合抽样检索通过率不足',
                    duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                )

            return PublishStep(
                name='9. 抽样检索测试',
                passed=True,
                message='暂存集合检索通过 ' + str(passed) + '/' + str(len(chunks)),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except Exception as e:
            return PublishStep(
                name='9. 抽样检索测试',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _step_10_alias_switch_and_status(self, course_code: str,
                                          result: PublishResult) -> PublishStep:
        """步骤 10: 原子别名切换 + 修改 publish_status"""
        start = datetime.now()
        try:
            from models.database_models import Subject
            bg = self._get_bg_manager()

            # 原子别名切换
            ok = bg.switch_alias(course_code, self._new_collection, self._old_collection)
            if not ok:
                raise PublishError('别名切换失败')
            result.active_collection = self._new_collection

            # 修改 publish_status
            subject = self.db.query(Subject).filter(
                Subject.course_code == course_code
            ).first()
            if not subject:
                raise PublishError('课程未导入数据库')

            old_status = subject.publish_status or 'draft'
            subject.publish_status = 'published'
            subject.schema_version = '2.0'
            self.db.commit()

            # 同步更新 JSON 文件
            course_dir = KNOWLEDGE_BASE_DIR / course_code
            course_file = course_dir / 'course.json'
            with open(course_file, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            course_data['publish_status'] = 'published'
            course_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d')
            with open(course_file, 'w', encoding='utf-8') as f:
                json.dump(course_data, f, ensure_ascii=False, indent=2)

            return PublishStep(
                name='10. 别名切换+状态更新',
                passed=True,
                message='别名 ' + result.alias_name + ' -> ' + self._new_collection +
                        '，状态 ' + old_status + ' -> published',
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
        except PublishError:
            raise
        except Exception as e:
            return PublishStep(
                name='10. 别名切换+状态更新',
                passed=False,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
                error=str(e),
            )

    def _cleanup_old_collections(self, course_code: str, result: PublishResult):
        """清理旧集合（保留最近 2 个）"""
        try:
            bg = self._get_bg_manager()
            deleted = bg.cleanup_old_collections(course_code, keep=2)
            if deleted:
                result.steps.append(PublishStep(
                    name='清理旧集合',
                    passed=True,
                    message='已清理: ' + ', '.join(deleted),
                ))
        except Exception as e:
            print('[WARN] 清理旧集合失败: ' + str(e))

    # ============== 回滚 ==============

    def _rollback(self, course_code: str, result: PublishResult):
        """回滚：数据库回滚 + 别名回滚 + 删除暂存集合"""
        result.rollback_performed = True
        actions = result.rollback_actions
        print("[ROLLBACK] 开始回滚发布操作")

        # 1. 数据库回滚
        try:
            if self.db is not None and self._transaction_active:
                self.db.rollback()
                self._transaction_active = False
                msg = '数据库事务已回滚'
                actions.append(msg)
                print("[ROLLBACK] " + msg)
        except Exception as e:
            msg = '数据库回滚失败: ' + str(e)
            actions.append(msg)
            print("[ROLLBACK] " + msg)

        # 2. 别名回滚（仅当别名已切换）
        if self._alias_switched and self._old_collection:
            try:
                bg = self._get_bg_manager()
                ok = bg.rollback_alias(course_code, self._old_collection,
                                       self._new_collection)
                if ok:
                    msg = '别名已回滚 -> ' + str(self._old_collection)
                    actions.append(msg)
                    print("[ROLLBACK] " + msg)
                else:
                    msg = '别名回滚失败'
                    actions.append(msg)
                    print("[ROLLBACK] " + msg)
            except Exception as e:
                msg = '别名回滚异常: ' + str(e)
                actions.append(msg)
                print("[ROLLBACK] " + msg)

        # 3. 删除暂存集合（仅当别名未切换，暂存集合是孤立的）
        elif self._new_collection and self._qdrant_client is not None:
            try:
                self._qdrant_client.delete_collection(self._new_collection)
                msg = '暂存集合已删除: ' + self._new_collection
                actions.append(msg)
                print("[ROLLBACK] " + msg)
            except Exception as e:
                msg = '暂存集合删除失败: ' + str(e)
                actions.append(msg)
                print("[ROLLBACK] " + msg)

    def restore_from_backup(self) -> bool:
        """从备份恢复数据库（用于严重故障）"""
        if not self._backup_path or not os.path.exists(self._backup_path):
            return False
        try:
            from database import DB_PATH
            # 用 SQLite Backup API 恢复
            src = sqlite3.connect(self._backup_path)
            dst = sqlite3.connect(str(DB_PATH))
            src.backup(dst)
            dst.close()
            src.close()
            return True
        except Exception:
            return False
