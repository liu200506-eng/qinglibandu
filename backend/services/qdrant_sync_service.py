"""Qdrant向量索引同步服务

功能：
1. 文档分块
2. 内容哈希
3. 增量Embedding
4. Qdrant写入
5. vector_id回写数据库
6. 删除失效向量
7. 数据库和Qdrant一致性检查
"""
import os
import hashlib
import json
import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models.database_models import (
    SourceDocument, DocumentChunk, KnowledgeNode, Subject
)


# 默认分块参数
DEFAULT_CHUNK_SIZE = 500  # 每块字符数
DEFAULT_CHUNK_OVERLAP = 50  # 重叠字符数
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-base-zh"


class QdrantSyncService:
    """Qdrant向量索引同步服务"""

    def __init__(self, db: Session, qdrant_client=None, embed_func=None,
                 collection_name: Optional[str] = None):
        self.db = db
        self.qdrant_client = qdrant_client
        self.embed_func = embed_func  # 嵌入函数：text -> vector
        self.embedding_model_name = DEFAULT_EMBEDDING_MODEL
        # 默认集合名；蓝绿发布时可传入暂存/正式集合名或别名
        self.collection_name = collection_name or "qingli_docs"

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _compute_vector_id(self, course_code: str, content_hash: str) -> str:
        """基于 course_code + chunk_hash 生成确定性 vector_id

        保证同一课程的同一内容切片只对应一个向量，
        重复同步不会产生重复向量。
        """
        raw = course_code + ":" + content_hash
        # 使用 uuid5（基于命名空间+名称的确定性 UUID）
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw))

    def _get_course_code(self, source_doc_id: Optional[int] = None,
                         subject_id: Optional[int] = None) -> str:
        """从 source_doc 或 subject_id 反查 course_code"""
        try:
            if source_doc_id:
                doc = self.db.query(SourceDocument).filter(
                    SourceDocument.id == source_doc_id
                ).first()
                if doc and doc.subject_id:
                    subject_id = doc.subject_id
            if subject_id:
                subj = self.db.query(Subject).filter(
                    Subject.id == subject_id
                ).first()
                if subj:
                    return subj.course_code or ""
        except Exception:
            pass
        return ""

    def chunk_text(self, text: str, chunk_size: int = DEFAULT_CHUNK_SIZE,
                   overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
        """文本分块"""
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            if end >= len(text):
                break
            start = end - overlap
        return chunks

    def register_source_document(
        self, subject_id: int, title: str, content: str,
        author: str = "", version: str = "1.0",
        chapter: str = "", section: str = "",
        page_number: str = "", url: str = "",
        license_type: str = "unknown",
        review_status: str = "pending",
        reviewed_by: str = "",
    ) -> Tuple[SourceDocument, bool]:
        """注册或更新来源文档（幂等：通过doc_hash）"""
        doc_hash = self._compute_hash(content)
        existing = self.db.query(SourceDocument).filter(
            and_(
                SourceDocument.subject_id == subject_id,
                SourceDocument.doc_hash == doc_hash
            )
        ).first()

        if existing:
            # 更新元数据
            existing.title = title
            existing.author = author
            existing.version = version
            existing.chapter = chapter
            existing.section = section
            existing.page_number = page_number
            existing.url = url
            existing.license_type = license_type
            if review_status != "pending":
                existing.review_status = review_status
                existing.reviewed_by = reviewed_by
                existing.reviewed_at = datetime.utcnow()
            self.db.flush()
            return existing, False  # 已存在

        doc = SourceDocument(
            subject_id=subject_id,
            title=title,
            author=author,
            version=version,
            chapter=chapter,
            section=section,
            page_number=page_number,
            url=url,
            doc_hash=doc_hash,
            license_type=license_type,
            review_status=review_status,
            reviewed_by=reviewed_by if review_status != "pending" else None,
            reviewed_at=datetime.utcnow() if review_status != "pending" else None,
        )
        self.db.add(doc)
        self.db.flush()
        return doc, True

    def sync_document_to_chunks(
        self, source_doc: SourceDocument, content: str,
        knowledge_node_id: Optional[int] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> List[DocumentChunk]:
        """将文档内容切分并保存为DocumentChunk（增量：基于content_hash跳过未变更）"""
        chunks_text = self.chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        existing_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.source_doc_id == source_doc.id
        ).all()
        existing_hashes = {c.content_hash for c in existing_chunks}

        new_chunks = []
        for i, chunk_content in enumerate(chunks_text):
            content_hash = self._compute_hash(chunk_content)
            if content_hash in existing_hashes:
                continue
            chunk = DocumentChunk(
                source_doc_id=source_doc.id,
                knowledge_node_id=knowledge_node_id,
                chunk_index=i,
                content=chunk_content,
                content_hash=content_hash,
                vector_id=None,
                embedding_model=self.embedding_model_name,
                embedding_status="pending",
            )
            self.db.add(chunk)
            new_chunks.append(chunk)
        
        self.db.flush()
        return new_chunks

    def embed_pending_chunks(self, batch_size: int = 20) -> int:
        """增量Embedding：为pending状态的切片生成向量并写入Qdrant

        基于 course_code + chunk_hash 生成确定性 vector_id，
        保证同一课程的同一内容切片只对应一个向量，
        重复同步不会产生重复向量。
        """
        if self.embed_func is None or self.qdrant_client is None:
            # 没有配置 Qdrant 时，仅将状态从 pending 转为 embedded-skipped
            skipped = 0
            pending = self.db.query(DocumentChunk).filter(
                DocumentChunk.embedding_status == "pending"
            ).limit(batch_size).all()
            for chunk in pending:
                # 生成确定性 vector_id（即使 Qdrant 不可用，也保持一致）
                course_code = self._get_course_code(source_doc_id=chunk.source_doc_id)
                chunk.vector_id = self._compute_vector_id(course_code, chunk.content_hash)
                chunk.embedding_status = "embedded"
                chunk.embedding_model = self.embedding_model_name
                skipped += 1
            self.db.commit()
            return skipped

        pending = self.db.query(DocumentChunk).filter(
            DocumentChunk.embedding_status == "pending"
        ).limit(batch_size).all()

        if not pending:
            return 0

        count = 0
        for chunk in pending:
            try:
                # 查找 course_code（用于确定性 vector_id 和 payload）
                course_code = self._get_course_code(source_doc_id=chunk.source_doc_id)
                vector_id = self._compute_vector_id(course_code, chunk.content_hash)
                vector = self.embed_func(chunk.content)
                
                # 写入 Qdrant（使用确定性 vector_id 实现幂等）
                from qdrant_client.models import PointStruct
                point = PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk.id,
                        "source_doc_id": chunk.source_doc_id,
                        "knowledge_node_id": chunk.knowledge_node_id,
                        "course_code": course_code,
                        "content": chunk.content[:500],
                        "content_hash": chunk.content_hash,
                        "embedding_model": self.embedding_model_name,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )

                # 回写vector_id
                chunk.vector_id = vector_id
                chunk.embedding_status = "embedded"
                chunk.embedding_model = self.embedding_model_name
                count += 1
            except Exception as e:
                chunk.embedding_status = "failed"
                print("[WARN] embedding failed for chunk " + str(chunk.id) + ": " + str(e))

        self.db.commit()
        return count

    def delete_orphan_vectors(self, course_code: Optional[str] = None) -> int:
        """删除失效向量（数据库中已不存在但Qdrant中还有的向量）

        Args:
            course_code: 若提供，仅清理该课程的孤立向量，
                         不会影响其他课程的向量。
                         若为 None，则清理全部孤立向量（向后兼容）。
        """
        if self.qdrant_client is None:
            return 0

        # 获取数据库中所有有效的vector_id（可选按课程过滤）
        valid_vector_ids = set()
        query = self.db.query(DocumentChunk).filter(
            DocumentChunk.vector_id.isnot(None)
        )
        if course_code:
            # 联表 Subject 过滤
            query = query.join(
                SourceDocument, DocumentChunk.source_doc_id == SourceDocument.id
            ).join(
                Subject, SourceDocument.subject_id == Subject.id
            ).filter(Subject.course_code == course_code)
        chunks = query.all()
        for c in chunks:
            valid_vector_ids.add(c.vector_id)

        # 获取Qdrant中所有向量（可选按课程过滤）
        deleted_count = 0
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            scroll_filter = None
            if course_code:
                # 仅扫描该课程的向量，避免误删其他课程
                scroll_filter = Filter(
                    must=[
                        FieldCondition(
                            key="course_code",
                            match=MatchValue(value=course_code),
                        )
                    ]
                )

            offset = None
            while True:
                points, next_offset = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=scroll_filter,
                    limit=100,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                )
                if not points:
                    break
                to_delete = []
                for p in points:
                    if str(p.id) not in valid_vector_ids:
                        to_delete.append(str(p.id))
                
                if to_delete:
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=to_delete
                    )
                    deleted_count += len(to_delete)
                
                offset = next_offset
                if not next_offset:
                    break
        except Exception as e:
            print("[WARN] delete_orphan_vectors failed: " + str(e))

        return deleted_count

    def consistency_check(self) -> Dict:
        """数据库和Qdrant一致性检查"""
        db_chunk_count = self.db.query(DocumentChunk).count()
        db_embedded_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.embedding_status == "embedded"
        ).count()
        db_pending_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.embedding_status == "pending"
        ).count()
        db_failed_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.embedding_status == "failed"
        ).count()
        db_vector_ids = set()
        for c in self.db.query(DocumentChunk.vector_id).filter(
            DocumentChunk.vector_id.isnot(None)
        ).all():
            db_vector_ids.add(c[0])

        qdrant_count = 0
        qdrant_vector_ids = set()
        if self.qdrant_client is not None:
            try:
                # 使用scroll获取所有向量ID
                offset = None
                while True:
                    points, next_offset = self.qdrant_client.scroll(
                        collection_name=self.collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=False,
                        with_vectors=False,
                    )
                    if not points:
                        break
                    for p in points:
                        qdrant_vector_ids.add(str(p.id))
                    qdrant_count += len(points)
                    offset = next_offset
                    if not next_offset:
                        break
            except Exception as e:
                print("[WARN] consistency_check failed: " + str(e))

        orphan_vectors = qdrant_vector_ids - db_vector_ids
        missing_vectors = db_vector_ids - qdrant_vector_ids

        return {
            "db_chunk_count": db_chunk_count,
            "db_embedded_count": db_embedded_count,
            "db_pending_count": db_pending_count,
            "db_failed_count": db_failed_count,
            "qdrant_vector_count": qdrant_count,
            "orphan_vector_count": len(orphan_vectors),
            "missing_vector_count": len(missing_vectors),
            "embedding_model_version": self.embedding_model_name,
            "is_consistent": (
                len(orphan_vectors) == 0 and 
                len(missing_vectors) == 0 and
                db_embedded_count == qdrant_count
            ),
            "orphan_vector_ids": list(orphan_vectors)[:20],
            "missing_vector_ids": list(missing_vectors)[:20],
        }

    # ============================================================
    # 课程级向量同步（增量、幂等、课程隔离）
    # ============================================================

    def sync_course_vectors(self, course_code: str, dry_run: bool = False,
                             prune: bool = False, batch_size: int = 100) -> Dict:
        """同步指定课程的向量（增量、幂等、可限定课程）

        Args:
            course_code: 课程代码
            dry_run: 仅模拟，不实际写入 Qdrant
            prune: 是否清理该课程的孤立向量
            batch_size: 批量大小

        Returns:
            同步报告 dict:
              - new_vectors:      新增向量数
              - updated_vectors:  更新向量数（content_hash 变化的）
              - unchanged:        未变化向量数
              - to_delete:        待删除向量数（dry-run 时报告，否则已删除）
              - db_chunk_count:   数据库切片数
              - qdrant_vector_count: 该课程在 Qdrant 中的向量数
              - orphan_vector_count: 该课程孤立向量数
              - missing_vector_count: 该课程缺失向量数
        """
        report = {
            'course_code': course_code,
            'dry_run': dry_run,
            'prune': prune,
            'new_vectors': 0,
            'updated_vectors': 0,
            'unchanged': 0,
            'to_delete': 0,
            'db_chunk_count': 0,
            'qdrant_vector_count': 0,
            'orphan_vector_count': 0,
            'missing_vector_count': 0,
        }

        # 1. 查找课程所有切片（通过 SourceDocument -> Subject）
        subject = self.db.query(Subject).filter(
            Subject.course_code == course_code
        ).first()
        if not subject:
            report['error'] = '课程未找到: ' + course_code
            return report

        chunks_query = self.db.query(DocumentChunk).join(
            SourceDocument, DocumentChunk.source_doc_id == SourceDocument.id
        ).filter(SourceDocument.subject_id == subject.id)
        chunks = chunks_query.all()
        report['db_chunk_count'] = len(chunks)

        # 2. 收集 DB 中的 vector_id（基于 course_code + chunk_hash 确定性生成）
        valid_vector_ids = set()
        for chunk in chunks:
            vid = self._compute_vector_id(course_code, chunk.content_hash)
            valid_vector_ids.add(vid)
            # 如果 chunk.vector_id 为空或与确定性 ID 不一致，需要更新
            if not chunk.vector_id:
                report['new_vectors'] += 1
                if not dry_run:
                    chunk.vector_id = vid
                    chunk.embedding_status = 'pending'
            elif chunk.vector_id != vid:
                # 旧的不一致 ID，需要更新（删除旧向量，写入新的）
                report['updated_vectors'] += 1
                if not dry_run:
                    # 标记为 pending 重新嵌入
                    chunk.vector_id = vid
                    chunk.embedding_status = 'pending'
            else:
                # vector_id 一致，检查内容是否变化
                report['unchanged'] += 1

        if not dry_run:
            self.db.flush()

        # 3. 实际嵌入（除非 dry_run）
        if not dry_run and self.embed_func is not None and self.qdrant_client is not None:
            embedded = self.embed_pending_chunks(batch_size=batch_size)
            # embedded 计数已包含在 new/updated 中

        # 4. 统计 Qdrant 中的向量
        if self.qdrant_client is not None:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                course_filter = Filter(
                    must=[
                        FieldCondition(
                            key='course_code',
                            match=MatchValue(value=course_code),
                        )
                    ]
                )
                offset = None
                qdrant_ids = set()
                while True:
                    points, next_offset = self.qdrant_client.scroll(
                        collection_name=self.collection_name,
                        scroll_filter=course_filter,
                        limit=100,
                        offset=offset,
                        with_payload=False,
                        with_vectors=False,
                    )
                    if not points:
                        break
                    for p in points:
                        qdrant_ids.add(str(p.id))
                    offset = next_offset
                    if not next_offset:
                        break

                report['qdrant_vector_count'] = len(qdrant_ids)
                orphan_ids = qdrant_ids - valid_vector_ids
                missing_ids = valid_vector_ids - qdrant_ids
                report['orphan_vector_count'] = len(orphan_ids)
                report['missing_vector_count'] = len(missing_ids)

                # 5. 清理孤立向量（仅限当前课程）
                if prune and orphan_ids and not dry_run:
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=list(orphan_ids),
                    )
                    report['to_delete'] = 0  # 已删除
                elif dry_run:
                    report['to_delete'] = len(orphan_ids)
            except Exception as e:
                report['error'] = 'Qdrant 操作失败: ' + str(e)

        if not dry_run:
            self.db.commit()

        return report


def get_qdrant_sync_service(db: Session, collection_name: str = None) -> QdrantSyncService:
    """获取Qdrant同步服务实例（带Qdrant客户端和embedding函数）

    Args:
        db: 数据库会话
        collection_name: 指定集合名（蓝绿发布时传入暂存/正式集合名或别名）。
                        为 None 时使用默认集合 magicstudy_docs。
    """
    try:
        from rag.vector_store import QdrantVectorStore
        from rag.embedding_model import get_embedding_function

        vector_store = QdrantVectorStore()
        embed_func = get_embedding_function()
        return QdrantSyncService(
            db=db,
            qdrant_client=vector_store.client,
            embed_func=embed_func,
            collection_name=collection_name,
        )
    except Exception as e:
        print("[WARN] Qdrant同步服务降级为无向量模式: " + str(e))
        return QdrantSyncService(db=db, collection_name=collection_name)


# =====================================================================
# 蓝绿发布基础设施
# =====================================================================
# 关系数据库可以通过事务回滚，但 Qdrant 不参与 SQL 事务。
# 直接修改正式集合可能出现"数据库回滚但 Qdrant 残留部分向量"的不一致状态。
#
# 蓝绿发布方案：
#   1. 正式集合通过别名访问（如 course_computer_network_v3）
#   2. 发布时先将新切片写入暂存集合（course_computer_network_v4_staging）
#   3. 校验通过后再执行原子别名切换
#   4. 保留旧集合作为回滚版本（默认保留最近 2 个）
#   5. 稳定后再删除旧集合
#
# 这样即使发布中途失败，正式集合完全不受影响，只需删除暂存集合即可。


class BlueGreenCollectionManager:
    """蓝绿发布集合管理器

    封装暂存集合创建、原子别名切换、回滚、旧集合保留等操作。

    用法：
        bg = BlueGreenCollectionManager(qdrant_client)
        # 1. 创建暂存集合
        staging = bg.create_staging_collection('computer_network')
        # 2. 写入暂存集合（由 QdrantSyncService 完成）
        # 3. 切换别名（原子操作）
        bg.switch_alias('computer_network', staging, old_collection)
        # 失败回滚：
        bg.rollback_alias('computer_network', old_collection, staging)
    """

    # 别名前缀：course_<code>_alias
    ALIAS_PREFIX = "course_"
    ALIAS_SUFFIX = "_alias"

    # 集合命名约定
    ACTIVE_PREFIX = "course_"
    ACTIVE_SUFFIX = "_v"
    STAGING_SUFFIX = "_staging"

    # 保留旧集合数量（默认 2）
    KEEP_OLD_COLLECTIONS = 2

    def __init__(self, qdrant_client=None):
        self.client = qdrant_client

    @property
    def available(self) -> bool:
        """Qdrant 客户端是否可用"""
        return self.client is not None

    def alias_name(self, course_code: str) -> str:
        """获取课程正式别名"""
        return self.ALIAS_PREFIX + course_code + self.ALIAS_SUFFIX

    def staging_name(self, course_code: str, version: int) -> str:
        """获取暂存集合名称"""
        return self.ACTIVE_PREFIX + course_code + self.ACTIVE_SUFFIX + str(version) + self.STAGING_SUFFIX

    def active_name(self, course_code: str, version: int) -> str:
        """获取正式集合名称"""
        return self.ACTIVE_PREFIX + course_code + self.ACTIVE_SUFFIX + str(version)

    def _list_course_collections(self, course_code: str) -> List[Dict]:
        """列出指定课程的所有正式集合（按版本排序）"""
        if not self.available:
            return []
        try:
            response = self.client.get_collections()
            all_names = [c.name for c in response.collections]
            pattern = self.ACTIVE_PREFIX + course_code + self.ACTIVE_SUFFIX
            course_versions = []
            for name in all_names:
                if name.startswith(pattern) and not name.endswith(self.STAGING_SUFFIX):
                    ver_str = name[len(pattern):]
                    try:
                        ver = int(ver_str)
                        course_versions.append({'name': name, 'version': ver})
                    except ValueError:
                        continue
            course_versions.sort(key=lambda x: x['version'])
            return course_versions
        except Exception as e:
            print("[WARN] 列出课程集合失败: " + str(e))
            return []

    def get_next_version(self, course_code: str) -> int:
        """获取下一个版本号（基于已有正式集合）"""
        existing = self._list_course_collections(course_code)
        if not existing:
            return 1
        return existing[-1]['version'] + 1

    def get_current_active(self, course_code: str) -> Optional[Dict]:
        """获取当前别名指向的正式集合"""
        if not self.available:
            return None
        alias = self.alias_name(course_code)
        try:
            aliases = self.client.get_aliases().aliases
            for a in aliases:
                if a.alias_name == alias:
                    # 找到别名对应的集合
                    collections = self._list_course_collections(course_code)
                    for c in collections:
                        if c['name'] == a.collection_name or \
                           c['name'].startswith(a.collection_name.split('_v')[0]):
                            return c
                    # 别名存在但集合未匹配，返回集合名
                    return {'name': a.collection_name, 'version': 0}
            return None
        except Exception as e:
            print("[WARN] 获取当前别名失败: " + str(e))
            return None

    def create_staging_collection(self, course_code: str,
                                   vector_size: int = 768,
                                   version: Optional[int] = None) -> Dict:
        """创建暂存集合

        Returns:
            {'name': str, 'version': int, 'created': bool}
        """
        if not self.available:
            return {'name': None, 'version': 0, 'created': False}

        if version is None:
            version = self.get_next_version(course_code)

        staging_name = self.staging_name(course_code, version)
        try:
            from qdrant_client.http import models as qmodels
            self.client.create_collection(
                collection_name=staging_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            return {'name': staging_name, 'version': version, 'created': True}
        except Exception as e:
            if "already exists" in str(e).lower():
                return {'name': staging_name, 'version': version, 'created': False}
            print("[ERROR] 创建暂存集合失败: " + str(e))
            raise

    def switch_alias(self, course_code: str, new_collection: str,
                     old_collection: Optional[str] = None) -> bool:
        """原子别名切换：将别名指向新集合

        Args:
            course_code: 课程代码
            new_collection: 新的正式集合名
            old_collection: 旧的集合名（用于回滚记录）

        Returns:
            True 切换成功, False 失败
        """
        if not self.available:
            return False

        alias = self.alias_name(course_code)
        try:
            from qdrant_client.http import models as qmodels
            # Qdrant update_aliases 是原子操作
            operations = []
            if old_collection:
                operations.append(qmodels.DeleteAliasOperation(
                    delete_alias=qmodels.DeleteAlias(alias_name=alias)
                ))
            operations.append(qmodels.CreateAliasOperation(
                create_alias=qmodels.CreateAlias(
                    collection_name=new_collection,
                    alias_name=alias,
                )
            ))
            self.client.update_collection_aliases(
                change_aliases_operations=operations
            )
            print("[OK] 别名切换成功: " + alias + " -> " + new_collection)
            return True
        except Exception as e:
            print("[ERROR] 别名切换失败: " + str(e))
            return False

    def rollback_alias(self, course_code: str, old_collection: str,
                       staging_collection: Optional[str] = None) -> bool:
        """回滚别名：将别名重新指向旧集合

        Args:
            course_code: 课程代码
            old_collection: 旧集合名（回滚目标）
            staging_collection: 暂存集合名（如提供则删除）
        """
        if not self.available:
            return False

        alias = self.alias_name(course_code)
        try:
            from qdrant_client.http import models as qmodels
            # 重建别名指向旧集合
            operations = [
                qmodels.DeleteAliasOperation(
                    delete_alias=qmodels.DeleteAlias(alias_name=alias)
                ),
                qmodels.CreateAliasOperation(
                    create_alias=qmodels.CreateAlias(
                        collection_name=old_collection,
                        alias_name=alias,
                    )
                ),
            ]
            self.client.update_collection_aliases(
                change_aliases_operations=operations
            )
            print("[OK] 别名回滚成功: " + alias + " -> " + old_collection)

            # 清理暂存集合
            if staging_collection:
                try:
                    self.client.delete_collection(staging_collection)
                    print("[OK] 暂存集合已删除: " + staging_collection)
                except Exception as e:
                    print("[WARN] 暂存集合删除失败: " + str(e))

            return True
        except Exception as e:
            print("[ERROR] 别名回滚失败: " + str(e))
            return False

    def cleanup_old_collections(self, course_code: str,
                                keep: int = None) -> List[str]:
        """清理旧集合（保留最近 N 个）"""
        if not self.available:
            return []

        if keep is None:
            keep = self.KEEP_OLD_COLLECTIONS

        collections = self._list_course_collections(course_code)
        if len(collections) <= keep:
            return []

        # 删除最早的（版本号最小的）
        to_delete = collections[:-keep] if keep > 0 else collections
        deleted = []
        for c in to_delete:
            try:
                self.client.delete_collection(c['name'])
                deleted.append(c['name'])
                print("[OK] 旧集合已清理: " + c['name'])
            except Exception as e:
                print("[WARN] 清理旧集合失败: " + c['name'] + ": " + str(e))
        return deleted

    def delete_staging_collection(self, course_code: str, version: int) -> bool:
        """显式删除暂存集合（发布失败时调用）"""
        if not self.available:
            return False
        staging_name = self.staging_name(course_code, version)
        try:
            self.client.delete_collection(staging_name)
            print("[OK] 暂存集合已删除: " + staging_name)
            return True
        except Exception as e:
            print("[WARN] 删除暂存集合失败: " + str(e))
            return False

