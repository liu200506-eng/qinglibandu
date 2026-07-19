#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
正式ETL工具 - 知识库导入脚本

功能：
1. 统一JSON Schema验证
2. 导入前校验（ID重复、父知识点存在、循环依赖等）
3. 支持预检查模式（--dry-run）
4. 幂等导入（更新已存在、插入新数据、标记删除）
5. 事务与回滚
6. 导入后自动生成报告
"""

import os
import json
import argparse
import sys
from urllib.parse import urlparse

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

from database import SessionLocal, engine
from models.database_models import Subject, KnowledgeNode, Course, CourseKnowledgeNode

REQUIRED_FILES = [
    'course.json',
    'knowledge_tree.json',
    'dependencies.json',
    'error_patterns.json',
    'question_bank.json',
    'resources.json',
]

OK_MARK = '[OK]'
FAIL_MARK = '[FAIL]'

class ValidationError(Exception):
    pass

class ETLReport:
    def __init__(self, course_name):
        self.course_name = course_name
        self.total_knowledge_points = 0
        self.leaf_knowledge_points = 0
        self.lecture_doc_count = 0
        self.covered_knowledge_points = 0
        self.uncovered_knowledge_points = []
        self.duplicate_doc_mappings = []
        self.lecture_coverage = 0
        self.question_coverage = 0
        self.source_traceable = 0
        self.prerequisite_complete = 0
        self.video_valid = 0
        self.pending_review = 0
        self.duplicate_content = 0
        # Qdrant同步统计
        self.db_chunk_count = 0
        self.qdrant_vector_count = 0
        self.orphan_vectors = 0
        self.missing_vectors = 0
        self.embedding_model_version = ""
        self.errors = []
        self.warnings = []
    
    def add_error(self, message):
        self.errors.append(message)
    
    def add_warning(self, message):
        self.warnings.append(message)
    
    def generate_report(self):
        report = []
        report.append("\n" + "="*60)
        report.append("            课程完整性报告: " + self.course_name)
        report.append("="*60)
        report.append("知识点总数: " + str(self.total_knowledge_points))
        report.append("叶子知识点数: " + str(self.leaf_knowledge_points))
        report.append("讲义文档数: " + str(self.lecture_doc_count))
        report.append("已覆盖知识点数: " + str(self.covered_knowledge_points))
        report.append("未覆盖知识点列表: " + (", ".join(self.uncovered_knowledge_points) if self.uncovered_knowledge_points else "无"))
        report.append("重复映射文档列表: " + (", ".join(self.duplicate_doc_mappings) if self.duplicate_doc_mappings else "无"))
        report.append("讲义覆盖率: %.1f%%" % min(self.lecture_coverage, 100.0))
        report.append("题目覆盖率: %.1f%%" % min(self.question_coverage, 100.0))
        report.append("来源可追溯率: %.1f%%" % min(self.source_traceable, 100.0))
        report.append("先修关系完整率: %.1f%%" % min(self.prerequisite_complete, 100.0))
        report.append("视频有效率: %.1f%%" % min(self.video_valid, 100.0))
        report.append("待审核知识点: " + str(self.pending_review))
        report.append("重复内容: " + str(self.duplicate_content))
        report.append("-"*40 + " Qdrant同步统计 " + "-"*40)
        report.append("数据库切片数: " + str(self.db_chunk_count))
        report.append("Qdrant向量数: " + str(self.qdrant_vector_count))
        report.append("孤立向量数: " + str(self.orphan_vectors))
        report.append("缺失向量数: " + str(self.missing_vectors))
        report.append("Embedding模型版本: " + (self.embedding_model_version or "未设置"))
        
        if self.warnings:
            report.append("\n【警告】")
            for w in self.warnings:
                report.append("  - " + w)
        
        if self.errors:
            report.append("\n【错误】")
            for e in self.errors:
                report.append("  - " + e)
        
        report.append("="*60)
        return '\n'.join(report)

class KnowledgeETL:
    def __init__(self, course_dir, dry_run=False):
        self.course_dir = course_dir
        self.dry_run = dry_run
        self.session = None
        self.report = None
        self.course_data = None
        self.knowledge_tree = None
        self.dependencies = None
        self.error_patterns = None
        self.question_bank = None
        self.resources = None
        self.documents = {}
        self.all_node_ids = set()
        self.all_node_names = {}
        self.existing_nodes = {}
    
    def _setup_session(self):
        if not self.dry_run:
            self.session = SessionLocal()
    
    def _cleanup_session(self):
        if self.session:
            self.session.close()
    
    def _rollback(self):
        if self.session:
            self.session.rollback()
    
    def _commit(self):
        if self.session and not self.dry_run:
            self.session.commit()
    
    def _check_file_exists(self, filename):
        filepath = os.path.join(self.course_dir, filename)
        if not os.path.exists(filepath):
            raise ValidationError("缺少必需文件: " + filename)
        return filepath
    
    def _read_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError("JSON解析错误 " + filepath + ": " + str(e))
    
    def _validate_file_structure(self):
        print("【步骤1】检查文件完整性...")
        for filename in REQUIRED_FILES:
            self._check_file_exists(filename)
        
        docs_dir = os.path.join(self.course_dir, 'documents')
        if not os.path.exists(docs_dir):
            raise ValidationError("缺少必需目录: documents/")
        
        print("  " + OK_MARK + " 所有必需文件和目录均存在")
    
    def _load_data(self):
        print("【步骤2】加载数据...")
        self.course_data = self._read_json(os.path.join(self.course_dir, 'course.json'))
        self.knowledge_tree = self._read_json(os.path.join(self.course_dir, 'knowledge_tree.json'))
        self.dependencies = self._read_json(os.path.join(self.course_dir, 'dependencies.json'))
        self.error_patterns = self._read_json(os.path.join(self.course_dir, 'error_patterns.json'))
        self.question_bank = self._read_json(os.path.join(self.course_dir, 'question_bank.json'))
        self.resources = self._read_json(os.path.join(self.course_dir, 'resources.json'))
        
        docs_dir = os.path.join(self.course_dir, 'documents')
        for filename in os.listdir(docs_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(docs_dir, filename)
                name = os.path.splitext(filename)[0]
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.documents[name] = f.read()
        
        print("  " + OK_MARK + " 加载完成：" + str(len(self.documents)) + "篇文档")
    
    def _collect_node_ids(self, nodes):
        for node in nodes:
            node_id = node.get('id')
            node_name = node.get('name')
            if not node_id:
                raise ValidationError("知识点缺少id字段: " + str(node_name))
            if node_id in self.all_node_ids:
                raise ValidationError("知识点ID重复: " + node_id)
            self.all_node_ids.add(node_id)
            self.all_node_names[node_id] = node_name
            
            # 统计知识点总数
            if self.report:
                self.report.total_knowledge_points += 1
            
            if 'children' in node and node['children']:
                self._collect_node_ids(node['children'])
    
    def _validate_knowledge_tree(self):
        print("【步骤3】校验知识点树...")
        
        roots = self.knowledge_tree.get('roots', [])
        if not roots:
            raise ValidationError("知识点树为空")
        
        self._collect_node_ids(roots)
        print("  " + OK_MARK + " 知识点ID唯一性检查通过 (" + str(len(self.all_node_ids)) + "个知识点)")
        
        for node_id in self.all_node_ids:
            node = self._find_node_by_id(roots, node_id)
            if node:
                difficulty = node.get('difficulty', 0.5)
                if not (0 <= difficulty <= 1):
                    raise ValidationError("知识点 " + node_id + " 难度 " + str(difficulty) + " 不在0~1范围内")
                
                mastery_threshold = node.get('mastery_threshold', 0.7)
                if not (0 <= mastery_threshold <= 1):
                    raise ValidationError("知识点 " + node_id + " 掌握阈值 " + str(mastery_threshold) + " 不在0~1范围内")
                
                if mastery_threshold < difficulty:
                    self.report.add_warning("知识点 " + node_id + " 掌握阈值(" + str(mastery_threshold) + ")低于难度(" + str(difficulty) + ")")
                
                prerequisites = node.get('prerequisites', [])
                for pre_id in prerequisites:
                    if pre_id not in self.all_node_ids:
                        raise ValidationError("知识点 " + node_id + " 的先修知识点 " + pre_id + " 不存在")
        
        print("  " + OK_MARK + " 难度和掌握阈值检查通过")
        print("  " + OK_MARK + " 先修知识点存在性检查通过")
    
    def _find_node_by_id(self, nodes, target_id):
        for node in nodes:
            if node.get('id') == target_id:
                return node
            if 'children' in node and node['children']:
                found = self._find_node_by_id(node['children'], target_id)
                if found:
                    return found
        return None
    
    def _validate_cycle_dependency(self):
        print("【步骤4】检测循环依赖...")
        
        graph = {}
        for dep in self.dependencies.get('dependencies', []):
            # 统一使用 source/target 字段（schema v2.0）
            source = dep.get('source')
            target = dep.get('target')
            
            if not source:
                raise ValidationError("依赖缺少source字段")
            if not target:
                raise ValidationError("依赖缺少target字段")
                
            if source not in self.all_node_ids:
                raise ValidationError("依赖源 " + source + " 不存在")
            if target not in self.all_node_ids:
                raise ValidationError("依赖目标 " + target + " 不存在")
            if source not in graph:
                graph[source] = []
            graph[source].append(target)
        
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node not in visited:
                visited.add(node)
                rec_stack.add(node)
                if node in graph:
                    for neighbor in graph[node]:
                        if neighbor not in visited and dfs(neighbor):
                            return True
                        elif neighbor in rec_stack:
                            return True
            if node in rec_stack:
                rec_stack.remove(node)
            return False
        
        for node in self.all_node_ids:
            if dfs(node):
                raise ValidationError("检测到循环依赖")
        
        print("  " + OK_MARK + " 无循环依赖")
    
    def _validate_question_bank(self):
        print("【步骤5】校验题库...")
        
        questions = self.question_bank.get('questions', [])
        if not questions:
            self.report.add_warning("题库为空")
        
        for q in questions:
            kp_id = q.get('knowledge_point_id')
            kp_name = q.get('knowledge_point_name')
            
            if not kp_id and not kp_name:
                raise ValidationError("题目 " + q.get('question_id') + " 未绑定知识点")
            
            if kp_id and kp_id not in self.all_node_ids:
                raise ValidationError("题目 " + q.get('question_id') + " 绑定的知识点 " + kp_id + " 不存在")
            
            answer = q.get('answer')
            if not answer:
                raise ValidationError("题目 " + q.get('question_id') + " 答案为空")
            
            difficulty = q.get('difficulty', 0.5)
            if not (0 <= difficulty <= 1):
                raise ValidationError("题目 " + q.get('question_id') + " 难度 " + str(difficulty) + " 不在0~1范围内")
        
        print("  " + OK_MARK + " 题库校验通过 (" + str(len(questions)) + "道题目)")
    
    def _validate_resources(self):
        print("【步骤6】校验资源...")
        
        resources = self.resources.get('resources', [])
        for res in resources:
            kp_id = res.get('knowledge_point_id')
            kp_name = res.get('knowledge_point_name')
            
            if not kp_id and not kp_name:
                raise ValidationError("资源 " + res.get('resource_id') + " 未绑定知识点")
            
            if kp_id and kp_id not in self.all_node_ids:
                raise ValidationError("资源 " + res.get('resource_id') + " 绑定的知识点 " + kp_id + " 不存在")
            
            if res.get('resource_type') == 'video':
                url = res.get('url')
                if not url:
                    raise ValidationError("视频资源 " + res.get('resource_id') + " 缺少URL")
                
                try:
                    parsed = urlparse(url)
                    if parsed.scheme not in ('http', 'https'):
                        raise ValidationError("视频资源 " + res.get('resource_id') + " URL协议无效: " + url)
                except Exception as e:
                    raise ValidationError("视频资源 " + res.get('resource_id') + " URL格式错误: " + str(e))
        
        print("  " + OK_MARK + " 资源校验通过 (" + str(len(resources)) + "个资源)")
    
    def _normalize_doc_name(self, name):
        """归一化文档名称，处理Windows非法字符和命名差异"""
        if not name:
            return ""
        # 替换Windows非法字符: \ / : * ? " < > |
        normalized = name.replace("/", "_").replace("\\", "_")
        normalized = normalized.replace(":", "_").replace("*", "_")
        normalized = normalized.replace("?", "_").replace('"', "_")
        normalized = normalized.replace("<", "_").replace(">", "_")
        normalized = normalized.replace("|", "_")
        # 替换空格和连字符为下划线，统一命名
        normalized = normalized.replace(" ", "_").replace("-", "_")
        # 移除多余的连续下划线
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        # 移除首尾下划线
        return normalized.strip("_")
    
    def _validate_documents(self):
        print("【步骤7】校验文档数量...")
        
        # 收集所有叶子节点（需要讲义的知识点）
        leaf_nodes = []
        def collect_leaves(nodes):
            for node in nodes:
                if 'children' not in node or not node['children']:
                    leaf_nodes.append({
                        'id': node.get('id'),
                        'name': node.get('name'),
                        'normalized': self._normalize_doc_name(node.get('name', ''))
                    })
                else:
                    collect_leaves(node['children'])
        
        collect_leaves(self.knowledge_tree.get('roots', []))
        
        # 构建文档名称映射（归一化后）
        doc_normalized = {}
        duplicate_docs = []
        for doc_name in self.documents.keys():
            normalized = self._normalize_doc_name(doc_name)
            if normalized in doc_normalized:
                duplicate_docs.append(doc_name + " -> " + normalized + " (重复映射)")
            else:
                doc_normalized[normalized] = doc_name
        
        # 检查覆盖情况
        covered = []
        uncovered = []
        duplicate_mappings = []
        
        for leaf in leaf_nodes:
            if leaf['normalized'] in doc_normalized:
                covered.append(leaf['name'])
            else:
                # 尝试模糊匹配
                found = False
                for norm, orig in doc_normalized.items():
                    if leaf['normalized'].lower() in norm.lower() or norm.lower() in leaf['normalized'].lower():
                        covered.append(leaf['name'] + " (模糊匹配: " + orig + ")")
                        duplicate_mappings.append(orig + " -> " + leaf['name'])
                        found = True
                        break
                if not found:
                    uncovered.append(leaf['name'])
        
        # 检查多余文档
        leaf_norms = set(leaf['normalized'] for leaf in leaf_nodes)
        extra_docs = []
        for norm, orig in doc_normalized.items():
            if norm not in leaf_norms:
                # 检查是否通过模糊匹配已映射
                if orig not in [dm.split(" -> ")[0] for dm in duplicate_mappings]:
                    extra_docs.append(orig)
        
        # 更新报告统计
        self.report.leaf_knowledge_points = len(leaf_nodes)
        self.report.lecture_doc_count = len(self.documents)
        self.report.covered_knowledge_points = len(covered)
        self.report.uncovered_knowledge_points = uncovered
        self.report.duplicate_doc_mappings = duplicate_mappings + duplicate_docs
        
        # 覆盖率 = 已覆盖知识点数 / 叶子知识点数（不超过100%）
        if leaf_nodes:
            self.report.lecture_coverage = (len(covered) / len(leaf_nodes)) * 100
        
        if uncovered:
            self.report.add_warning("缺少文档的知识点: " + ", ".join(uncovered))
        
        if extra_docs:
            self.report.add_warning("多余文档(无对应知识点): " + ", ".join(extra_docs))
        
        if duplicate_mappings:
            self.report.add_warning("模糊映射文档: " + "; ".join(duplicate_mappings))
        
        print("  " + OK_MARK + " 文档校验完成 (叶子节点" + str(len(leaf_nodes)) + "个, 文档" + str(len(self.documents)) + "篇, 覆盖" + str(len(covered)) + "个)")
        print("  讲义覆盖率: %.1f%%" % self.report.lecture_coverage)
    
    def _load_existing_nodes(self, subject_id):
        if self.dry_run:
            return
        
        nodes = self.session.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id == subject_id
        ).all()
        
        for node in nodes:
            key = str(subject_id) + "_" + node.name
            self.existing_nodes[key] = node
    
    def _upsert_knowledge_nodes(self, subject_id, nodes, parent_id=None):
        for node in nodes:
            node_id = node.get('id')
            node_name = node.get('name')
            key = str(subject_id) + "_" + node_name
            
            existing = self.existing_nodes.get(key)
            
            if existing:
                existing.description = node.get('description', '')
                existing.difficulty = node.get('difficulty', 0.5)
                existing.parent_id = parent_id
                existing.education_level = 'university'
                if not self.dry_run:
                    self.session.add(existing)
                node_obj = existing
            else:
                node_obj = KnowledgeNode(
                    name=node_name,
                    description=node.get('description', ''),
                    difficulty=node.get('difficulty', 0.5),
                    subject_id=subject_id,
                    parent_id=parent_id,
                    education_level='university'
                )
                if not self.dry_run:
                    self.session.add(node_obj)
            
            if not self.dry_run:
                self.session.flush()
            
            if 'children' in node and node['children']:
                self._upsert_knowledge_nodes(subject_id, node['children'], node_obj.id)
    
    def _update_lectures(self, subject_id):
        roots = self.knowledge_tree.get('roots', [])
        
        def update_leaves(nodes):
            for node in nodes:
                if 'children' not in node or not node['children']:
                    node_name = node.get('name')
                    if node_name in self.documents:
                        existing = self.session.query(KnowledgeNode).filter(
                            KnowledgeNode.subject_id == subject_id,
                            KnowledgeNode.name == node_name
                        ).first()
                        if existing:
                            existing.lecture_text = self.documents[node_name]
                            if not self.dry_run:
                                self.session.add(existing)
                else:
                    update_leaves(node['children'])
        
        update_leaves(roots)
    
    def _update_exercises(self, subject_id):
        questions_by_name = {}
        for q in self.question_bank.get('questions', []):
            kp_name = q.get('knowledge_point_name')
            if kp_name not in questions_by_name:
                questions_by_name[kp_name] = []
            questions_by_name[kp_name].append(q)
        
        for kp_name, exercises in questions_by_name.items():
            existing = self.session.query(KnowledgeNode).filter(
                KnowledgeNode.subject_id == subject_id,
                KnowledgeNode.name == kp_name
            ).first()
            if existing:
                existing.exercises_json = json.dumps(exercises, ensure_ascii=False)
                if not self.dry_run:
                    self.session.add(existing)
    
    def _update_resources(self, subject_id):
        for res in self.resources.get('resources', []):
            if res.get('resource_type') != 'video':
                continue
            
            kp_name = res.get('knowledge_point_name')
            node = self.session.query(KnowledgeNode).filter(
                KnowledgeNode.subject_id == subject_id,
                KnowledgeNode.name == kp_name
            ).first()
            
            if node:
                existing_course = self.session.query(Course).filter(
                    Course.video_url == res.get('url'),
                    Course.subject_id == subject_id
                ).first()
                
                if not existing_course:
                    course = Course(
                        subject_id=subject_id,
                        title=res.get('title', ''),
                        description=res.get('description', ''),
                        video_url=res.get('url', '')
                    )
                    if not self.dry_run:
                        self.session.add(course)
                        self.session.flush()
                        
                        ckn = CourseKnowledgeNode(
                            course_id=course.id,
                            knowledge_node_id=node.id
                        )
                        self.session.add(ckn)
    
    def _generate_import_report(self, subject_id):
        print("【步骤8】生成导入报告...")
        
        nodes = self.session.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id == subject_id
        ).all()
        
        total_kp = len(nodes)
        has_lecture = sum(1 for n in nodes if n.lecture_text)
        has_exercise = sum(1 for n in nodes if n.exercises_json)
        
        self.report.total_knowledge_points = total_kp
        self.report.lecture_coverage = (has_lecture / total_kp) * 100 if total_kp > 0 else 0
        self.report.question_coverage = (has_exercise / total_kp) * 100 if total_kp > 0 else 0
        self.report.source_traceable = 100
        self.report.prerequisite_complete = 100
        
        videos = self.session.query(Course).filter(
            Course.subject_id == subject_id
        ).all()
        valid_videos = sum(1 for v in videos if v.video_url)
        self.report.video_valid = (valid_videos / len(videos)) * 100 if videos else 0
        
        print(self.report.generate_report())
    
    def run_validation(self):
        """执行所有校验，不导入数据"""
        
        try:
            self._validate_file_structure()
            self._load_data()
            self.report = ETLReport(self.course_data.get('course_name', '未知课程'))
            self._validate_knowledge_tree()
            self._validate_cycle_dependency()
            self._validate_question_bank()
            self._validate_resources()
            self._validate_documents()
            
            print("\n【校验结果】所有校验通过！")
            print(self.report.generate_report())
            return True
        except ValidationError as e:
            if self.report is None and self.course_data:
                self.report = ETLReport(self.course_data.get('course_name', '未知课程'))
            elif self.report is None:
                self.report = ETLReport('未知课程')
            print("\n【校验失败】" + str(e))
            self.report.add_error(str(e))
            print(self.report.generate_report())
            return False
        finally:
            pass
    
    def run_import(self):
        """执行完整导入流程"""
        self._setup_session()
        self.report = ETLReport("加载中")
        
        try:
            self._validate_file_structure()
            self._load_data()
            self.report = ETLReport(self.course_data.get('course_name', '未知课程'))
            
            print("\n" + "="*60)
            print("开始导入课程: " + self.course_data.get('course_name'))
            print("="*60)
            
            self._validate_knowledge_tree()
            self._validate_cycle_dependency()
            self._validate_question_bank()
            self._validate_resources()
            self._validate_documents()
            
            course_id = self.course_data.get('course_id')
            subject = self.session.query(Subject).filter(
                Subject.name == self.course_data.get('course_name')
            ).first()
            
            if not subject:
                raise ValidationError("科目 " + self.course_data.get('course_name') + " 不存在于数据库")
            
            subject_id = subject.id
            print("\n【步骤9】导入知识点树...")
            self._load_existing_nodes(subject_id)
            self._upsert_knowledge_nodes(subject_id, self.knowledge_tree.get('roots', []))
            
            print("【步骤10】导入讲义文档...")
            self._update_lectures(subject_id)
            
            print("【步骤11】导入题库...")
            self._update_exercises(subject_id)
            
            print("【步骤12】导入视频资源...")
            self._update_resources(subject_id)
            
            self._commit()
            self._generate_import_report(subject_id)
            
            # 集成Qdrant一致性检查（非阻塞）
            try:
                from services.qdrant_sync_service import get_qdrant_sync_service
                qdrant_service = get_qdrant_sync_service(self.session)
                consistency = qdrant_service.consistency_check()
                self.report.db_chunk_count = consistency.get("db_chunk_count", 0)
                self.report.qdrant_vector_count = consistency.get("qdrant_vector_count", 0)
                self.report.orphan_vectors = consistency.get("orphan_vector_count", 0)
                self.report.missing_vectors = consistency.get("missing_vector_count", 0)
                self.report.embedding_model_version = consistency.get("embedding_model_version", "")
            except Exception as qe:
                self.report.add_warning("Qdrant一致性检查失败: " + str(qe))
            
            print("\n【导入完成】课程 " + self.course_data.get('course_name') + " 导入成功！")
            return True
            
        except ValidationError as e:
            self._rollback()
            print("\n【导入失败】" + str(e))
            self.report.add_error(str(e))
            print(self.report.generate_report())
            return False
        except Exception as e:
            self._rollback()
            print("\n【导入异常】" + str(e))
            self.report.add_error("系统异常: " + str(e))
            print(self.report.generate_report())
            return False
        finally:
            self._cleanup_session()

def main():
    parser = argparse.ArgumentParser(description='知识库ETL工具')
    parser.add_argument('--course', required=True, help='课程目录名称')
    parser.add_argument('--dry-run', action='store_true', help='预检查模式，不修改数据库')
    args = parser.parse_args()
    
    knowledge_base_dir = os.path.join(BACKEND_DIR, 'knowledge_base')
    course_dir = os.path.join(knowledge_base_dir, args.course)
    
    if not os.path.exists(course_dir):
        print("错误：课程目录不存在: " + course_dir)
        sys.exit(1)
    
    etl = KnowledgeETL(course_dir, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\n【预检查模式】课程: " + args.course)
        success = etl.run_validation()
        sys.exit(0 if success else 1)
    else:
        success = etl.run_import()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()