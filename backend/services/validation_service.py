#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青藜伴读 分级校验服务

按课程 publish_status 执行不同标准:
  draft:          检查基础 JSON 和课程编码
  demo_only:      检查知识树、依赖关系和基础题库
  review:         检查讲义、题库、来源和审核字段
  published:      执行全部严格检查
  archived:       跳过发布检查

策略:
  dev:            开发策略，demo_only 课程允许"带警告通过"
  release:        发布策略，严格校验所有非 archived 课程
"""
import os
import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============== 路径处理（使用统一 path_utils） ==============

try:
    from services.path_utils import (
        BACKEND_DIR, REPO_ROOT, KNOWLEDGE_BASE_DIR,
        WINDOWS_INVALID_CHARS, WINDOWS_RESERVED_NAMES, MAX_PATH_LENGTH,
    )
except ImportError:
    # 直接计算（保证独立性）
    BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
    REPO_ROOT = BACKEND_DIR.parent
    KNOWLEDGE_BASE_DIR = BACKEND_DIR / 'knowledge_base'
    WINDOWS_INVALID_CHARS = set('\\/:*?"<>|')
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }
    MAX_PATH_LENGTH = 200


# ============== 常量 ==============

VALID_PUBLISH_STATUS = ['draft', 'review', 'published', 'demo_only', 'archived']

VALID_ORIGIN_TYPES = {
    'textbook', 'official_document', 'open_course',
    'teacher_defined', 'team_defined'
}


# ============== 数据类 ==============

class Severity(Enum):
    ERROR = 'error'      # 阻断
    WARNING = 'warning'  # 警告
    INFO = 'info'        # 提示


@dataclass
class ValidationIssue:
    """校验问题"""
    severity: Severity
    code: str            # 问题代码
    message: str         # 问题描述
    file: str = ''       # 涉及文件
    course: str = ''     # 涉及课程


@dataclass
class CourseValidationResult:
    """单课程校验结果"""
    course_code: str
    publish_status: str
    policy: str
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]
    
    @property
    def passed(self) -> bool:
        """是否通过（无 ERROR）"""
        return len(self.errors) == 0
    
    @property
    def passed_with_warnings(self) -> bool:
        """带警告通过"""
        return self.passed and len(self.warnings) > 0
    
    def to_dict(self) -> dict:
        return {
            'course_code': self.course_code,
            'publish_status': self.publish_status,
            'policy': self.policy,
            'passed': self.passed,
            'passed_with_warnings': self.passed_with_warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'issues': [
                {
                    'severity': i.severity.value,
                    'code': i.code,
                    'message': i.message,
                    'file': i.file,
                    'course': i.course,
                }
                for i in self.issues
            ],
        }


@dataclass
class ValidationReport:
    """完整校验报告"""
    policy: str
    results: List[CourseValidationResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)
    
    @property
    def total_errors(self) -> int:
        return sum(len(r.errors) for r in self.results)
    
    @property
    def total_warnings(self) -> int:
        return sum(len(r.warnings) for r in self.results)
    
    def to_dict(self) -> dict:
        return {
            'policy': self.policy,
            'passed': self.passed,
            'total_errors': self.total_errors,
            'total_warnings': self.total_warnings,
            'course_count': len(self.results),
            'results': [r.to_dict() for r in self.results],
        }


# ============== 校验服务 ==============

class ValidationService:
    """分级校验服务"""
    
    def __init__(self, policy: str = 'dev'):
        if policy not in ('dev', 'release'):
            raise ValueError("policy 必须是 dev 或 release")
        self.policy = policy
    
    # ---------- 公共入口 ----------
    
    def validate_all(self) -> ValidationReport:
        """校验所有课程"""
        report = ValidationReport(policy=self.policy)
        for course_code in self.list_courses():
            result = self.validate_course(course_code)
            report.results.append(result)
        return report
    
    def validate_course(self, course_code: str) -> CourseValidationResult:
        """校验单个课程"""
        course_dir = KNOWLEDGE_BASE_DIR / course_code
        if not course_dir.exists():
            result = CourseValidationResult(
                course_code=course_code,
                publish_status='unknown',
                policy=self.policy,
            )
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='COURSE_NOT_FOUND',
                message='课程目录不存在: ' + str(course_dir),
                course=course_code,
            ))
            return result
        
        # 读取 course.json
        course_data, course_issues = self._load_json(course_dir / 'course.json')
        publish_status = course_data.get('publish_status', 'draft') if course_data else 'draft'
        
        result = CourseValidationResult(
            course_code=course_code,
            publish_status=publish_status,
            policy=self.policy,
        )
        result.issues.extend(course_issues)
        
        # archived 课程跳过校验
        if publish_status == 'archived':
            result.issues.append(ValidationIssue(
                severity=Severity.INFO,
                code='ARCHIVED_SKIPPED',
                message='archived 课程跳过校验',
                course=course_code,
            ))
            return result
        
        # 按状态分级校验
        if publish_status == 'draft':
            self._validate_draft(course_dir, course_data, result)
        elif publish_status == 'demo_only':
            self._validate_demo_only(course_dir, course_data, result)
        elif publish_status == 'review':
            self._validate_review(course_dir, course_data, result)
        elif publish_status == 'published':
            self._validate_published(course_dir, course_data, result)
        
        # dev 策略下，demo_only 课程允许带警告通过
        if self.policy == 'dev' and publish_status == 'demo_only':
            for issue in result.issues[:]:
                if issue.severity == Severity.ERROR and issue.code in (
                    'MISSING_DOCUMENT', 'MISSING_SOURCE_FIELD'
                ):
                    issue.severity = Severity.WARNING
        
        return result
    
    # ---------- 分级校验实现 ----------
    
    def _validate_draft(self, course_dir: Path, course_data: dict, result: CourseValidationResult):
        """draft: 检查基础 JSON 和课程编码"""
        # 1. 必需文件存在
        required_files = ['course.json', 'knowledge_tree.json']
        for fn in required_files:
            if not (course_dir / fn).exists():
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='MISSING_FILE',
                    message='缺少必需文件: ' + fn,
                    file=str(course_dir / fn),
                    course=result.course_code,
                ))
        
        # 2. course.json 必需字段
        self._check_course_fields(course_dir, course_data, result, strict=False)
        
        # 3. knowledge_tree.json 基础字段
        tree_data, _ = self._load_json(course_dir / 'knowledge_tree.json')
        if tree_data:
            self._check_knowledge_tree_basic(tree_data, course_dir, result)
    
    def _validate_demo_only(self, course_dir: Path, course_data: dict, result: CourseValidationResult):
        """demo_only: 检查知识树、依赖关系和基础题库"""
        # 包含 draft 全部检查
        self._validate_draft(course_dir, course_data, result)
        
        tree_data, _ = self._load_json(course_dir / 'knowledge_tree.json')
        
        # 依赖关系检查
        deps_data, _ = self._load_json(course_dir / 'dependencies.json')
        if deps_data is None:
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='MISSING_FILE',
                message='缺少 dependencies.json',
                course=result.course_code,
            ))
        elif tree_data:
            self._check_dependencies(deps_data, tree_data, course_dir, result)
        
        # 基础题库检查
        qb_data, _ = self._load_json(course_dir / 'question_bank.json')
        if qb_data is None:
            result.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code='MISSING_FILE',
                message='缺少 question_bank.json',
                course=result.course_code,
            ))
        elif tree_data:
            self._check_question_bank(qb_data, tree_data, course_dir, result, strict=False)
    
    def _validate_review(self, course_dir: Path, course_data: dict, result: CourseValidationResult):
        """review: 检查讲义、题库、来源和审核字段

        review 状态允许 WARNING（缺失来源、未审核只警告，不阻断）。
        """
        # 包含 demo_only 全部检查
        self._validate_demo_only(course_dir, course_data, result)

        tree_data, _ = self._load_json(course_dir / 'knowledge_tree.json')

        # 1. 讲义覆盖率（缺失为 WARNING）
        self._check_documents_coverage(course_dir, tree_data, result, strict=False)

        # 2. 题库检查（review 状态允许 WARNING，不强制阻断）
        qb_data, _ = self._load_json(course_dir / 'question_bank.json')
        if qb_data and tree_data:
            self._check_question_bank(qb_data, tree_data, course_dir, result, strict=False)

        # 3. 错误模式来源字段（review 状态允许 WARNING）
        ep_data, _ = self._load_json(course_dir / 'error_patterns.json')
        if ep_data:
            self._check_error_patterns(ep_data, course_dir, result, strict=False)

        # 4. 资源链接
        res_data, _ = self._load_json(course_dir / 'resources.json')
        if res_data and tree_data:
            self._check_resources(res_data, tree_data, course_dir, result)
    
    def _validate_published(self, course_dir: Path, course_data: dict, result: CourseValidationResult):
        """published: 执行全部严格检查

        published 课程强制阻断规则（ERROR）：
          - 来源追溯率 < 100%
          - 审核通过率 < 100%
          - 知识点讲义覆盖率 < 100%
          - 数据库与向量不一致（由 publish 流程检查）
          - 抽样检索失败（由 publish 流程检查）
        """
        # 包含 review 全部检查（strict=True 已在内部生效）
        self._validate_review(course_dir, course_data, result)

        # 1. course.json 严格字段
        self._check_course_fields(course_dir, course_data, result, strict=True)

        # 2. 文件名严格检查
        self._check_filenames(course_dir, result)

        # 3. 所有知识点必须有讲义（讲义覆盖率 100%）
        tree_data, _ = self._load_json(course_dir / 'knowledge_tree.json')
        if tree_data:
            self._check_all_leaves_have_docs(course_dir, tree_data, result)

        # 4. published 课程：来源追溯率与审核通过率必须为 100%
        self._check_published_source_coverage(course_dir, result)
        self._check_published_review_status(course_dir, result)

    def _check_published_source_coverage(self, course_dir: Path,
                                          result: CourseValidationResult):
        """published 课程：检查来源追溯率（题目、错误模式、讲义均需 100% 关联来源）

        严格校验规则：
          1. 每个内容必须有 source_ids 字段且非空
          2. 每个 source_id 必须在 sources.json 的 source_documents 中真实存在
          3. source_id 不能引用失效的来源（review_status=rejected/deleted）
          4. 不能机械关联同一个来源到所有内容（同源率 > 50% 触发 WARNING）
        """
        # 加载来源文档清单，构建 source_id → source 索引
        sources_data, _ = self._load_json(course_dir / 'sources.json')
        source_index = {}
        if sources_data:
            for s in sources_data.get('source_documents', []):
                sid = s.get('source_id')
                if sid:
                    source_index[sid] = s

        # 题库
        qb_data, _ = self._load_json(course_dir / 'question_bank.json')
        all_q_source_ids = []
        if qb_data:
            for q in qb_data.get('questions', []):
                qid = q.get('question_id') or q.get('id', 'unknown')
                sids = q.get('source_ids')
                if not sids:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_MISSING_SOURCE',
                        message='published 课程题目缺少 source_ids: ' + str(qid),
                        file=str(course_dir / 'question_bank.json'),
                        course=result.course_code,
                    ))
                    continue
                # 检查每个 source_id 真实存在
                for sid in sids:
                    if sid not in source_index:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='PUBLISHED_INVALID_SOURCE_ID',
                            message='published 课程题目 source_id 不存在: ' + str(sid) +
                                    ' (题目: ' + str(qid) + ')',
                            file=str(course_dir / 'question_bank.json'),
                            course=result.course_code,
                        ))
                    else:
                        # 检查来源本身是否失效
                        src_status = source_index[sid].get('review_status')
                        if src_status in ('rejected', 'deleted', 'deprecated'):
                            result.issues.append(ValidationIssue(
                                severity=Severity.ERROR,
                                code='PUBLISHED_SOURCE_DEPRECATED',
                                message='published 课程题目引用了失效来源: ' + str(sid) +
                                        ' (状态: ' + str(src_status) + ', 题目: ' + str(qid) + ')',
                                file=str(course_dir / 'question_bank.json'),
                                course=result.course_code,
                            ))
                all_q_source_ids.extend(sids)

        # 错误模式
        ep_data, _ = self._load_json(course_dir / 'error_patterns.json')
        all_ep_source_ids = []
        if ep_data:
            patterns = ep_data.get('patterns', ep_data.get('error_patterns', []))
            for p in patterns:
                pid = p.get('pattern_id') or p.get('error_id') or p.get('id', 'unknown')
                sids = p.get('source_ids')
                if not sids:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_MISSING_SOURCE',
                        message='published 课程错误模式缺少 source_ids: ' + str(pid),
                        file=str(course_dir / 'error_patterns.json'),
                        course=result.course_code,
                    ))
                    continue
                for sid in sids:
                    if sid not in source_index:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='PUBLISHED_INVALID_SOURCE_ID',
                            message='published 课程错误模式 source_id 不存在: ' + str(sid) +
                                    ' (错误模式: ' + str(pid) + ')',
                            file=str(course_dir / 'error_patterns.json'),
                            course=result.course_code,
                        ))
                    else:
                        src_status = source_index[sid].get('review_status')
                        if src_status in ('rejected', 'deleted', 'deprecated'):
                            result.issues.append(ValidationIssue(
                                severity=Severity.ERROR,
                                code='PUBLISHED_SOURCE_DEPRECATED',
                                message='published 课程错误模式引用失效来源: ' + str(sid) +
                                        ' (错误模式: ' + str(pid) + ')',
                                file=str(course_dir / 'error_patterns.json'),
                                course=result.course_code,
                            ))
                all_ep_source_ids.extend(sids)

        # 检查机械关联同一来源（同源率 > 50% 触发 WARNING）
        # 仅当内容项多于 5 项时检查
        q_count = len(qb_data.get('questions', [])) if qb_data else 0
        ep_count = len(patterns) if ep_data else 0
        total_items = q_count + ep_count
        if total_items > 5:
            all_sids = all_q_source_ids + all_ep_source_ids
            if all_sids:
                from collections import Counter
                most_common_sid, most_common_count = Counter(all_sids).most_common(1)[0]
                same_source_rate = most_common_count / total_items
                if same_source_rate > 0.5 and len(set(all_sids)) < 3:
                    result.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        code='PUBLISHED_SOURCE_MONOTONIC',
                        message='published 课程内容来源过于集中: ' + str(most_common_sid) +
                                ' 关联 ' + str(round(same_source_rate * 100, 1)) + '% 的内容',
                        file=str(course_dir / 'sources.json'),
                        course=result.course_code,
                    ))

    def _check_published_review_status(self, course_dir: Path,
                                          result: CourseValidationResult):
        """published 课程：检查审核通过率（题目、错误模式均需 review_status=approved）

        严格校验规则：
          1. review_status 必须 = approved
          2. reviewed_by 不能为空
          3. reviewed_by 不能与 author 相同（角色分离原则）
             - author 默认为 'author' 或 'content_author' 字段
             - 评审者不能自己批准自己的内容
        """
        # 题库
        qb_data, _ = self._load_json(course_dir / 'question_bank.json')
        if qb_data:
            for q in qb_data.get('questions', []):
                qid = q.get('question_id') or q.get('id', 'unknown')
                status = q.get('review_status')
                if status != 'approved':
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_NOT_REVIEWED',
                        message='published 课程题目未通过审核: ' + str(qid) +
                                ' (当前: ' + str(status) + ')',
                        file=str(course_dir / 'question_bank.json'),
                        course=result.course_code,
                    ))
                    continue
                # 角色分离：reviewed_by 不能与 author 相同
                reviewed_by = q.get('reviewed_by')
                if not reviewed_by:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_NO_REVIEWER',
                        message='published 课程题目已审核但缺少 reviewed_by: ' + str(qid),
                        file=str(course_dir / 'question_bank.json'),
                        course=result.course_code,
                    ))
                else:
                    author = q.get('author') or q.get('content_author')
                    if author and reviewed_by == author:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='PUBLISHED_SELF_REVIEW',
                            message='published 课程题目自审自批（author == reviewed_by): ' +
                                    str(qid) + ' (' + str(reviewed_by) + ')',
                            file=str(course_dir / 'question_bank.json'),
                            course=result.course_code,
                        ))
        # 错误模式
        ep_data, _ = self._load_json(course_dir / 'error_patterns.json')
        if ep_data:
            patterns = ep_data.get('patterns', ep_data.get('error_patterns', []))
            for p in patterns:
                pid = p.get('pattern_id') or p.get('error_id') or p.get('id', 'unknown')
                status = p.get('review_status')
                if status != 'approved':
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_NOT_REVIEWED',
                        message='published 课程错误模式未通过审核: ' + str(pid) +
                                ' (当前: ' + str(status) + ')',
                        file=str(course_dir / 'error_patterns.json'),
                        course=result.course_code,
                    ))
                    continue
                reviewed_by = p.get('reviewed_by')
                if not reviewed_by:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='PUBLISHED_NO_REVIEWER',
                        message='published 课程错误模式已审核但缺少 reviewed_by: ' + str(pid),
                        file=str(course_dir / 'error_patterns.json'),
                        course=result.course_code,
                    ))
                else:
                    author = p.get('author') or p.get('content_author')
                    if author and reviewed_by == author:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='PUBLISHED_SELF_REVIEW',
                            message='published 课程错误模式自审自批（author == reviewed_by): ' +
                                    str(pid) + ' (' + str(reviewed_by) + ')',
                            file=str(course_dir / 'error_patterns.json'),
                            course=result.course_code,
                        ))
    
    # ---------- 检查实现 ----------
    
    def _load_json(self, path: Path) -> Tuple[Optional[dict], List[ValidationIssue]]:
        """加载 JSON 文件"""
        issues = []
        if not path.exists():
            return None, issues
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, issues
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='JSON_PARSE_ERROR',
                message='JSON 解析失败: ' + str(e),
                file=str(path),
            ))
            return None, issues
        except Exception as e:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='FILE_READ_ERROR',
                message='读取文件失败: ' + str(e),
                file=str(path),
            ))
            return None, issues
    
    def _check_course_fields(self, course_dir: Path, course_data: Optional[dict],
                              result: CourseValidationResult, strict: bool):
        """检查 course.json 必需字段"""
        if course_data is None:
            return
        
        required = ['schema_version', 'course_code', 'course_name', 'publish_status']
        if strict:
            required += ['version', 'last_updated']
        
        for field_name in required:
            if field_name not in course_data:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='MISSING_COURSE_FIELD',
                    message='course.json 缺少必需字段: ' + field_name,
                    file=str(course_dir / 'course.json'),
                    course=result.course_code,
                ))
        
        status = course_data.get('publish_status')
        if status and status not in VALID_PUBLISH_STATUS:
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='INVALID_PUBLISH_STATUS',
                message='非法 publish_status: ' + status,
                file=str(course_dir / 'course.json'),
                course=result.course_code,
            ))
        
        sv = course_data.get('schema_version')
        if sv and not str(sv).startswith('2.'):
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='INVALID_SCHEMA_VERSION',
                message='schema_version 不是 2.x: ' + str(sv),
                file=str(course_dir / 'course.json'),
                course=result.course_code,
            ))
    
    def _check_knowledge_tree_basic(self, tree_data: dict, course_dir: Path,
                                      result: CourseValidationResult):
        """检查 knowledge_tree.json 基础字段"""
        if 'schema_version' not in tree_data:
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='MISSING_TREE_FIELD',
                message='knowledge_tree.json 缺少 schema_version',
                file=str(course_dir / 'knowledge_tree.json'),
                course=result.course_code,
            ))
        if 'course_code' not in tree_data:
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code='MISSING_TREE_FIELD',
                message='knowledge_tree.json 缺少 course_code',
                file=str(course_dir / 'knowledge_tree.json'),
                course=result.course_code,
            ))
        
        # 检查节点 id 和 node_code 唯一性
        node_ids = set()
        node_codes = {}
        
        def collect(nodes):
            for node in nodes:
                nid = node.get('id')
                ncode = node.get('node_code')
                name = node.get('name', '')
                
                if not nid:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='MISSING_NODE_ID',
                        message='知识点缺少 id 字段: ' + name,
                        file=str(course_dir / 'knowledge_tree.json'),
                        course=result.course_code,
                    ))
                else:
                    if nid in node_ids:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='DUPLICATE_NODE_ID',
                            message='知识点 ID 重复: ' + str(nid),
                            file=str(course_dir / 'knowledge_tree.json'),
                            course=result.course_code,
                        ))
                    node_ids.add(nid)
                
                if not ncode:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='MISSING_NODE_CODE',
                        message='知识点缺少 node_code 字段: ' + name,
                        file=str(course_dir / 'knowledge_tree.json'),
                        course=result.course_code,
                    ))
                else:
                    if ncode in node_codes:
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='DUPLICATE_NODE_CODE',
                            message='node_code 重复: ' + ncode +
                                    ' (节点1: ' + node_codes[ncode] +
                                    ', 节点2: ' + name + ')',
                            file=str(course_dir / 'knowledge_tree.json'),
                            course=result.course_code,
                        ))
                    else:
                        node_codes[ncode] = name
                
                # 难度合法性
                difficulty = node.get('difficulty', 0.5)
                if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 1:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='INVALID_DIFFICULTY',
                        message='难度非法 ' + str(difficulty) + ': ' + name,
                        file=str(course_dir / 'knowledge_tree.json'),
                        course=result.course_code,
                    ))
                
                # 递归子节点
                collect(node.get('children', []))
        
        collect(tree_data.get('roots', []))
    
    def _check_dependencies(self, deps_data: dict, tree_data: dict,
                              course_dir: Path, result: CourseValidationResult):
        """检查依赖关系和循环依赖"""
        # 收集所有知识点 id
        all_node_ids = set()
        def collect_ids(nodes):
            for node in nodes:
                nid = node.get('id')
                if nid:
                    all_node_ids.add(nid)
                collect_ids(node.get('children', []))
        collect_ids(tree_data.get('roots', []))
        
        dep_graph = {}
        deps = deps_data.get('dependencies', [])
        for dep in deps:
            src = dep.get('source_id') or dep.get('source')
            tgt = dep.get('target_id') or dep.get('target')
            
            if not src or not tgt:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='INVALID_DEPENDENCY',
                    message='依赖关系缺少 source/target: ' + json.dumps(dep, ensure_ascii=False),
                    file=str(course_dir / 'dependencies.json'),
                    course=result.course_code,
                ))
                continue
            
            if src not in all_node_ids:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='DEPENDENCY_SOURCE_NOT_FOUND',
                    message='依赖关系 source 不存在: ' + str(src),
                    file=str(course_dir / 'dependencies.json'),
                    course=result.course_code,
                ))
            if tgt not in all_node_ids:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='DEPENDENCY_TARGET_NOT_FOUND',
                    message='依赖关系 target 不存在: ' + str(tgt),
                    file=str(course_dir / 'dependencies.json'),
                    course=result.course_code,
                ))
            
            if src not in dep_graph:
                dep_graph[src] = []
            dep_graph[src].append(tgt)
        
        # 循环依赖检测（DFS）
        WHITE, GRAY, BLACK = 0, 1, 2
        color_map = {nid: WHITE for nid in all_node_ids}
        
        def dfs(node, path):
            if color_map.get(node) == GRAY:
                cycle = path[path.index(node):] + [node] if node in path else path + [node]
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='CIRCULAR_DEPENDENCY',
                    message='检测到循环依赖: ' + ' -> '.join(cycle),
                    file=str(course_dir / 'dependencies.json'),
                    course=result.course_code,
                ))
                return True
            if color_map.get(node) == BLACK:
                return False
            color_map[node] = GRAY
            for neighbor in dep_graph.get(node, []):
                if dfs(neighbor, path + [node]):
                    return True
            color_map[node] = BLACK
            return False
        
        for nid in all_node_ids:
            if color_map.get(nid) == WHITE:
                if dfs(nid, []):
                    break
    
    def _check_question_bank(self, qb_data: dict, tree_data: dict,
                                course_dir: Path, result: CourseValidationResult,
                                strict: bool):
        """检查题库"""
        all_node_ids = set()
        def collect_ids(nodes):
            for node in nodes:
                nid = node.get('id')
                if nid:
                    all_node_ids.add(nid)
                collect_ids(node.get('children', []))
        collect_ids(tree_data.get('roots', []))
        
        questions = qb_data.get('questions', [])
        for q in questions:
            qid = q.get('question_id') or q.get('id', 'unknown')
            
            # 答案不能为空
            answer = q.get('answer')
            if not answer:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='EMPTY_ANSWER',
                    message='题目答案为空: ' + str(qid),
                    file=str(course_dir / 'question_bank.json'),
                    course=result.course_code,
                ))
            
            # 难度合法性
            difficulty = q.get('difficulty', 0.5)
            if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 1:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='INVALID_DIFFICULTY',
                    message='题目难度非法 ' + str(difficulty) + ': ' + str(qid),
                    file=str(course_dir / 'question_bank.json'),
                    course=result.course_code,
                ))
            
            # 必须绑定知识点
            kp_id = q.get('knowledge_point_id') or q.get('knowledge_node_id')
            kp_name = q.get('knowledge_point_name') or q.get('knowledge_node_name')
            if not kp_id and not kp_name:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='QUESTION_NOT_BOUND',
                    message='题目未绑定知识点: ' + str(qid),
                    file=str(course_dir / 'question_bank.json'),
                    course=result.course_code,
                ))
            elif kp_id and kp_id not in all_node_ids:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='QUESTION_KNOWLEDGE_NOT_FOUND',
                    message='题目绑定知识点不存在: ' + str(kp_id) + ' (题目 ' + str(qid) + ')',
                    file=str(course_dir / 'question_bank.json'),
                    course=result.course_code,
                ))
            
            # 严格模式：检查来源
            if strict:
                if 'source_ids' not in q or not q['source_ids']:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='MISSING_SOURCE_FIELD',
                        message='题目缺少 source_ids: ' + str(qid),
                        file=str(course_dir / 'question_bank.json'),
                        course=result.course_code,
                    ))
    
    def _check_error_patterns(self, ep_data: dict, course_dir: Path,
                                 result: CourseValidationResult, strict: bool):
        """检查错误模式"""
        patterns = ep_data.get('patterns', ep_data.get('error_patterns', []))
        for p in patterns:
            pid = p.get('pattern_id') or p.get('id', 'unknown')
            
            if 'origin_type' not in p:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR if strict else Severity.WARNING,
                    code='MISSING_ORIGIN_TYPE',
                    message='error_pattern 缺少 origin_type: ' + str(pid),
                    file=str(course_dir / 'error_patterns.json'),
                    course=result.course_code,
                ))
            elif p['origin_type'] not in VALID_ORIGIN_TYPES:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='INVALID_ORIGIN_TYPE',
                    message='非法 origin_type: ' + str(p['origin_type']) +
                            ' (合法: ' + ', '.join(sorted(VALID_ORIGIN_TYPES)) + ')',
                    file=str(course_dir / 'error_patterns.json'),
                    course=result.course_code,
                ))
            
            if 'source_ids' not in p or not p['source_ids']:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR if strict else Severity.WARNING,
                    code='MISSING_SOURCE_FIELD',
                    message='error_pattern 缺少 source_ids: ' + str(pid),
                    file=str(course_dir / 'error_patterns.json'),
                    course=result.course_code,
                ))
            
            if 'review_status' not in p:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR if strict else Severity.WARNING,
                    code='MISSING_REVIEW_STATUS',
                    message='error_pattern 缺少 review_status: ' + str(pid),
                    file=str(course_dir / 'error_patterns.json'),
                    course=result.course_code,
                ))
    
    def _check_resources(self, res_data: dict, tree_data: dict,
                          course_dir: Path, result: CourseValidationResult):
        """检查资源"""
        url_pattern = re.compile(r'^https?://')
        
        all_node_ids = set()
        def collect_ids(nodes):
            for node in nodes:
                nid = node.get('id')
                if nid:
                    all_node_ids.add(nid)
                collect_ids(node.get('children', []))
        collect_ids(tree_data.get('roots', []))
        
        resources = res_data.get('resources', [])
        for r in resources:
            rid = r.get('resource_id') or r.get('id', 'unknown')
            url = r.get('url', '')
            if url and not url_pattern.match(url):
                result.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code='INVALID_URL',
                    message='资源 URL 格式不合法: ' + url + ' (' + str(rid) + ')',
                    file=str(course_dir / 'resources.json'),
                    course=result.course_code,
                ))
            
            kp_id = r.get('knowledge_point_id') or r.get('knowledge_node_id')
            if kp_id and kp_id not in all_node_ids:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code='RESOURCE_KNOWLEDGE_NOT_FOUND',
                    message='资源绑定知识点不存在: ' + str(kp_id) + ' (' + str(rid) + ')',
                    file=str(course_dir / 'resources.json'),
                    course=result.course_code,
                ))
    
    def _check_documents_coverage(self, course_dir: Path, tree_data: Optional[dict],
                                    result: CourseValidationResult, strict: bool):
        """检查讲义覆盖率"""
        if not tree_data:
            return
        
        # 统计叶子节点
        leaf_count = 0
        def count_leaves(nodes):
            nonlocal leaf_count
            for node in nodes:
                if not node.get('children'):
                    leaf_count += 1
                else:
                    count_leaves(node.get('children', []))
        count_leaves(tree_data.get('roots', []))
        
        # 统计文档
        docs_dir = course_dir / 'documents'
        doc_count = 0
        if docs_dir.exists():
            doc_count = len([f for f in docs_dir.iterdir() if f.suffix == '.md'])
        
        if leaf_count == 0:
            return
        
        coverage = min(doc_count / leaf_count * 100, 100.0) if leaf_count > 0 else 0
        
        if doc_count < leaf_count:
            severity = Severity.ERROR if strict else Severity.WARNING
            result.issues.append(ValidationIssue(
                severity=severity,
                code='MISSING_DOCUMENT',
                message='讲义覆盖不足: 文档 ' + str(doc_count) + '/' + str(leaf_count) +
                        ' (覆盖率 ' + ('%.1f%%' % coverage) + ')',
                file=str(docs_dir),
                course=result.course_code,
            ))
    
    def _check_all_leaves_have_docs(self, course_dir: Path, tree_data: dict,
                                      result: CourseValidationResult):
        """检查所有叶子节点都有讲义

        匹配策略（按顺序尝试）:
          1. 严格匹配：知识点名 == 文件名（不含扩展名）
          2. 规范化匹配：替换 Windows 非法字符 / : * ? " < > | 为 _
          3. 子串匹配：知识点名是文件名的子串，或反之
        """
        import re as _re
        docs_dir = course_dir / 'documents'
        existing_docs = []  # 保留原始名
        if docs_dir.exists():
            for f in docs_dir.iterdir():
                if f.suffix == '.md':
                    existing_docs.append(f.stem)
        
        def _normalize(name: str) -> str:
            """规范化名称：替换非法字符"""
            # 替换 Windows 非法字符为 _
            normalized = _re.sub(r'[\\/:*?"<>|]', '_', name)
            # 也尝试替换为 -
            return normalized
        
        def _normalize_hyphen(name: str) -> str:
            """用连字符替换"""
            return _re.sub(r'[\\/:*?"<>|]', '-', name)
        
        def _try_match(kp_name: str) -> bool:
            """尝试匹配文档"""
            if kp_name in existing_docs:
                return True
            norm_under = _normalize(kp_name)
            norm_hyphen = _normalize_hyphen(kp_name)
            for doc in existing_docs:
                doc_norm = _normalize(doc)
                doc_norm_h = _normalize_hyphen(doc)
                if norm_under == doc_norm or norm_hyphen == doc_norm_h:
                    return True
                # 子串匹配（去除常见前缀后缀）
                # 去除 "详解" 后缀
                for suffix in ['详解', '（详解）', '(详解)']:
                    if doc.endswith(suffix) and doc[:-len(suffix)] == kp_name:
                        return True
                    if doc.endswith(suffix) and doc[:-len(suffix)] == norm_under:
                        return True
                # 去除常见前缀
                for prefix in ['TCP', 'UDP', 'IP', 'SSL']:
                    if kp_name.startswith(prefix) and kp_name[len(prefix):] in doc:
                        return True
            return False
        
        def check_leaves(nodes):
            for node in nodes:
                if not node.get('children'):
                    name = node.get('name', '')
                    if not _try_match(name):
                        result.issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            code='MISSING_DOCUMENT',
                            message='知识点缺少讲义: ' + name,
                            file=str(docs_dir / (name + '.md')),
                            course=result.course_code,
                        ))
                else:
                    check_leaves(node.get('children', []))
        check_leaves(tree_data.get('roots', []))
    
    def _check_filenames(self, course_dir: Path, result: CourseValidationResult):
        """检查目录下所有文件名安全性"""
        for path in course_dir.rglob('*'):
            if path.is_file():
                basename = path.name
                name_without_ext = path.stem
                
                # 检查非法字符
                invalid_in_name = set(basename) & WINDOWS_INVALID_CHARS
                if invalid_in_name:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='INVALID_FILENAME',
                        message='文件名含非法字符 ' + "".join(invalid_in_name) + ': ' + basename,
                        file=str(path),
                        course=result.course_code,
                    ))
                
                # 检查 Windows 保留名
                if name_without_ext.upper() in WINDOWS_RESERVED_NAMES:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='RESERVED_FILENAME',
                        message='文件名是 Windows 保留名: ' + basename,
                        file=str(path),
                        course=result.course_code,
                    ))
                
                # 检查结尾空格或英文句点
                if basename != basename.rstrip(' .'):
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='INVALID_FILENAME_ENDING',
                        message='文件名以空格或句点结尾: ' + basename,
                        file=str(path),
                        course=result.course_code,
                    ))
                
                # 检查文件名长度
                if len(basename) > MAX_PATH_LENGTH:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code='FILENAME_TOO_LONG',
                        message='文件名过长 (>' + str(MAX_PATH_LENGTH) + '字符): ' + basename,
                        file=str(path),
                        course=result.course_code,
                    ))
                
                # Unicode 规范化重名检查
                try:
                    normalized = unicodedata.normalize('NFC', basename)
                    if normalized != basename:
                        result.issues.append(ValidationIssue(
                            severity=Severity.WARNING,
                            code='FILENAME_NOT_NORMALIZED',
                            message='文件名未做 Unicode 规范化（建议 NFC）: ' + basename,
                            file=str(path),
                            course=result.course_code,
                        ))
                except Exception:
                    pass
    
    # ---------- 工具方法 ----------
    
    def list_courses(self) -> List[str]:
        """列出所有课程目录"""
        if not KNOWLEDGE_BASE_DIR.exists():
            return []
        courses = []
        for item in sorted(KNOWLEDGE_BASE_DIR.iterdir()):
            if item.is_dir() and (item / 'course.json').exists():
                courses.append(item.name)
        return courses
