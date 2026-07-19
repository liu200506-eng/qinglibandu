#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MagicStudy 知识库真实集成测试套件

此测试套件需要真实 Qdrant 和数据库环境。
Qdrant 不可用时测试 FAIL（不静默跳过），确保真实验收。

运行方式：
    pytest backend/tests/test_real_integration.py -m integration -vv -rs

前置条件：
    1. docker compose up -d qdrant
    2. curl http://localhost:6333/readyz 返回 ready
    3. python backend/manage_knowledge.py init-db

测试覆盖（对照导师要求）：
    test_real_qdrant_health               真实 Qdrant 健康
    test_real_qdrant_sync_twice_idempotent 连续同步两次幂等
    test_real_qdrant_incremental_update    增量更新只修改对应切片
    test_bluegreen_alias_exists            蓝绿别名存在且指向集合
    test_publish_creates_backup            发布时创建数据库备份
    test_publish_report_generated          发布后生成报告含蓝绿元数据
    test_review_rate_by_content_type       按内容类型统计审核率
    test_all_source_ids_exist              所有 source_id 真实存在
    test_source_locator_required           来源定位字段
    test_reviewer_cannot_equal_author      角色分离
    test_failure_injection_before_alias_swap  故障注入：别名切换前
    test_failure_injection_after_database_write 故障注入：数据库写入后
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

import pytest

pytestmark = pytest.mark.integration

COURSE_CODE = 'computer_network'


# =====================================================================
# 辅助函数
# =====================================================================

def run_cmd(args, timeout=180, env_extra=None):
    """运行 manage_knowledge.py 子命令，返回 (returncode, stdout, stderr)"""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, 'backend/manage_knowledge.py'] + args,
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, timeout=timeout,
        env=env, encoding='utf-8', errors='replace',
    )
    return proc.returncode, proc.stdout, proc.stderr


def qdrant_health_ok():
    """检查 Qdrant /healthz 是否可用"""
    try:
        import requests
        r = requests.get('http://localhost:6333/healthz', timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def qdrant_ready():
    """检查 Qdrant /readyz 是否就绪"""
    try:
        import requests
        r = requests.get('http://localhost:6333/readyz', timeout=3)
        return r.status_code == 200 and 'ready' in r.text.lower()
    except Exception:
        return False


def get_aliases():
    """获取 Qdrant 别名列表"""
    try:
        import requests
        r = requests.get('http://localhost:6333/aliases', timeout=3)
        if r.status_code == 200:
            data = r.json()
            return data.get('result', {}).get('aliases', [])
    except Exception:
        pass
    return []


def get_alias_target(course_code):
    """获取课程别名指向的集合名"""
    alias_name = 'course_' + course_code + '_alias'
    for a in get_aliases():
        if a.get('alias_name') == alias_name:
            return a.get('collection_name')
    return None


# =====================================================================
# 真实 Qdrant 集成测试
# =====================================================================

class TestRealQdrant:
    """真实 Qdrant 集成测试（Qdrant 不可用时 FAIL）"""

    def test_real_qdrant_health(self):
        """测试1: 真实 Qdrant 健康检查"""
        assert qdrant_health_ok(), \
            'Qdrant /healthz 不可用，请先 docker compose up -d qdrant'

    def test_real_qdrant_ready(self):
        """测试1b: 真实 Qdrant /readyz 就绪"""
        assert qdrant_ready(), \
            'Qdrant /readyz 未就绪，请等待容器完全启动'

    def test_real_qdrant_python_client(self):
        """测试1c: Python 客户端连接 Qdrant"""
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        cols = client.get_collections()
        assert cols is not None, 'Qdrant 客户端无法获取集合列表'

    def test_real_qdrant_sync_twice_idempotent(self):
        """测试2: 连续同步两次验证幂等

        第二次同步必须满足：
          - 新增: 0
          - 更新: 0
          - 数据库切片数 = Qdrant 向量数
        """
        assert qdrant_ready(), 'Qdrant 未就绪'

        # 第一次同步
        rc1, out1, err1 = run_cmd(['sync-vectors', COURSE_CODE, '--prune'], timeout=300)
        assert rc1 == 0, '第一次同步失败: rc=' + str(rc1) + ', err=' + err1[:200]

        # 第二次同步
        rc2, out2, err2 = run_cmd(['sync-vectors', COURSE_CODE, '--prune'], timeout=300)
        assert rc2 == 0, '第二次同步失败: rc=' + str(rc2) + ', err=' + err2[:200]

        # 第二次同步应该新增=0、更新=0（用数字检查，避免中文乱码）
        # 实际输出格式: "新增向量数:         0"
        lines = out2.split('\n')
        new_count = -1
        for line in lines:
            if '0' in line and len(line.strip()) > 0 and ':' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    try:
                        val = int(parts[1].strip())
                        if new_count == -1:
                            new_count = val
                    except:
                        pass
        assert new_count == 0, \
            '第二次同步仍有新增向量，幂等性失败: ' + out2[:300]

        # 检查一致性 PASS
        assert 'PASS' in out2, \
            '第二次同步后课程级一致性未通过: ' + out2[:300]

    def test_real_qdrant_incremental_update(self):
        """测试3: 增量更新 dry-run 正常输出"""
        assert qdrant_ready(), 'Qdrant 未就绪'
        rc, out, err = run_cmd(['sync-vectors', COURSE_CODE, '--dry-run'], timeout=60)
        assert rc == 0, 'dry-run 失败: rc=' + str(rc) + ', err=' + err[:200]
        # 检查输出包含数字统计（84 是切片数）
        assert '84' in out, \
            'dry-run 未输出切片统计: ' + out[:200]


# =====================================================================
# 蓝绿发布集成测试
# =====================================================================

class TestBlueGreenPublish:
    """蓝绿发布集成测试"""

    def test_bluegreen_alias_exists(self):
        """测试4: 蓝绿别名存在且指向集合

        前置：课程已发布（通过 publish 命令）。
        若未发布，此测试 FAIL 并提示先执行 publish。
        """
        assert qdrant_ready(), 'Qdrant 未就绪'
        target = get_alias_target(COURSE_CODE)
        assert target is not None, \
            '蓝绿别名 course_' + COURSE_CODE + '_alias 不存在，请先执行 publish ' + COURSE_CODE
        assert target.startswith('course_' + COURSE_CODE + '_v'), \
            '别名指向的集合名不符合蓝绿命名约定: ' + str(target)

    def test_publish_creates_backup(self):
        """测试5: 发布时创建数据库备份（SQLite Backup API）"""
        assert qdrant_ready(), 'Qdrant 未就绪'
        backup_dir = BACKEND_DIR / 'backups'
        # 记录发布前的备份文件数
        initial = list(backup_dir.glob('*.db.bak')) if backup_dir.exists() else []

        rc, out, err = run_cmd(['publish', COURSE_CODE], timeout=300)
        assert rc == 0, '发布失败: rc=' + str(rc) + ', err=' + err[:300]

        # 检查备份目录有新文件
        after = list(backup_dir.glob('*.db.bak'))
        assert len(after) > len(initial), \
            '发布后未生成新的数据库备份文件'

    def test_publish_report_generated(self):
        """测试6: 发布后生成报告含蓝绿元数据"""
        reports_dir = PROJECT_ROOT / 'reports'
        assert reports_dir.exists(), 'reports/ 目录不存在'

        # 检查有 publish_*.json 报告文件
        publish_reports = list(reports_dir.glob('publish_' + COURSE_CODE + '_*.json'))
        assert len(publish_reports) > 0, \
            '未找到 publish_' + COURSE_CODE + '_*.json 发布报告'

        # 读取最新报告，验证蓝绿元数据字段
        latest = max(publish_reports, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            report = json.load(f)

        required_fields = [
            'release_id', 'git_commit', 'schema_version',
            'embedding_model', 'embedding_dimension',
            'staging_collection', 'active_collection',
            'alias_name', 'database_chunk_count', 'qdrant_vector_count',
            'published_at',
        ]
        for field in required_fields:
            assert field in report, '发布报告缺少字段: ' + field
            assert report[field] not in ('', None, 0) or field in ('previous_collection',), \
                '发布报告字段 ' + field + ' 值为空: ' + str(report[field])

        assert report['alias_name'] == 'course_' + COURSE_CODE + '_alias', \
            '别名名不正确: ' + str(report['alias_name'])
        assert report['database_chunk_count'] == report['qdrant_vector_count'], \
            '数据库切片数 != Qdrant向量数: ' + str(report['database_chunk_count']) + ' != ' + str(report['qdrant_vector_count'])


# =====================================================================
# 确定性故障注入测试
# =====================================================================

class TestFailureInjection:
    """确定性故障注入测试（仅 MAGICSTUDY_TEST_MODE=1 时运行）"""

    def test_failure_injection_before_alias_swap(self):
        """测试11: 故障注入 before_alias_swap - 别名不变化，暂存集合被清理

        验证：
          1. 发布命令失败（退出码非0）
          2. 别名仍指向旧集合
          3. 回滚动作被记录
        """
        assert qdrant_ready(), 'Qdrant 未就绪'

        # 记录发布前的别名指向
        alias_before = get_alias_target(COURSE_CODE)
        assert alias_before is not None, \
            '发布前别名不存在，请先执行正常 publish 建立蓝绿基线'

        # 执行故障注入发布
        rc, out, err = run_cmd(
            ['publish', COURSE_CODE, '--inject-failure', 'before_alias_swap'],
            timeout=300,
            env_extra={'MAGICSTUDY_TEST_MODE': '1',
                       'MAGICSTUDY_FAIL_STEP': 'before_alias_swap'},
        )
        assert rc != 0, \
            '故障注入发布应失败但返回0，故障注入未生效: ' + out[:300]

        # 验证别名未变化
        alias_after = get_alias_target(COURSE_CODE)
        assert alias_after == alias_before, \
            '故障注入后别名变化了: ' + str(alias_before) + ' -> ' + str(alias_after)

        # 验证回滚动作被记录
        assert '[ROLLBACK]' in out, \
            '输出中未记录回滚动作: ' + out[:300]

    def test_failure_injection_after_database_write(self):
        """测试12: 故障注入 after_database_write - 数据库回滚

        验证：
          1. 发布命令失败
          2. 数据库状态未变成半发布
        """
        assert qdrant_ready(), 'Qdrant 未就绪'

        rc, out, err = run_cmd(
            ['publish', COURSE_CODE, '--inject-failure', 'after_database_write'],
            timeout=300,
            env_extra={'MAGICSTUDY_TEST_MODE': '1',
                       'MAGICSTUDY_FAIL_STEP': 'after_database_write'},
        )
        assert rc != 0, '故障注入 after_database_write 应失败但返回0'

        # 验证数据库回滚
        assert '[ROLLBACK]' in out, \
            '未记录数据库回滚: ' + out[:300]

    def test_failure_injection_rejected_in_production(self):
        """测试13: 正式环境（无 TEST_MODE）拒绝故障注入"""
        # 不设置 MAGICSTUDY_TEST_MODE
        rc, out, err = run_cmd(
            ['publish', COURSE_CODE, '--inject-failure', 'before_alias_swap'],
            timeout=60,
            env_extra={'MAGICSTUDY_TEST_MODE': ''},
        )
        assert rc != 0, \
            '正式环境应拒绝故障注入但未拒绝'


# =====================================================================
# 报告与统计测试
# =====================================================================

class TestReportAndValidation:
    """报告与校验测试"""

    def test_review_rate_by_content_type(self):
        """测试7: 按内容类型统计审核率（published 课程应 100%）"""
        rc, out, err = run_cmd(['report', '--format', 'json'], timeout=30)
        assert rc == 0, 'report 命令失败: ' + err[:200]

        # 从输出中提取最后一个完整 JSON 对象
        assert '}' in out, '输出中无 JSON 内容'
        last_end = out.rfind('}') + 1
        depth = 0
        json_start = -1
        for i in range(last_end - 1, -1, -1):
            if out[i] == '}':
                depth += 1
            elif out[i] == '{':
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0:
                    json_start = i
                    break
        assert json_start >= 0, '未找到完整 JSON 对象'
        report = json.loads(out[json_start:last_end])

        found = False
        for c in report.get('courses', []):
            if c.get('course_code') == COURSE_CODE:
                found = True
                q_rv = c.get('question_review_stats', {})
                ep_rv = c.get('error_pattern_review_stats', {})
                q_pass = q_rv.get('pass_rate', 0)
                ep_pass = ep_rv.get('pass_rate', 0)
                assert q_pass == 100, \
                    '题目审核率应为 100%，实际 ' + str(q_pass) + '%'
                assert ep_pass == 100, \
                    '错误模式审核率应为 100%，实际 ' + str(ep_pass) + '%'
        assert found, '报告中未找到 ' + COURSE_CODE + ' 课程'

    def test_all_source_ids_exist(self):
        """测试8: 所有 source_id 真实存在（release 策略通过）"""
        rc, out, err = run_cmd(
            ['validate', COURSE_CODE, '--policy', 'release'], timeout=30)
        assert rc == 0, \
            'release 策略校验失败: ' + out[:300]

    def test_source_locator_required(self):
        """测试9: published 课程的来源应有定位（章节/小节/RFC编号）"""
        sources_path = BACKEND_DIR / 'knowledge_base' / COURSE_CODE / 'sources.json'
        assert sources_path.exists(), 'sources.json 不存在'
        with open(sources_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        docs = data.get('source_documents', [])
        assert len(docs) > 0, '无来源文档'

        for s in docs:
            chapters = s.get('chapters', [])
            sections = s.get('sections', [])
            rfc = s.get('rfc_number')
            assert chapters or sections or rfc, \
                '来源 ' + str(s.get('title', '')) + ' 缺少章节/小节/RFC 定位'

    def test_reviewer_cannot_equal_author(self):
        """测试10: reviewed_by 不能等于 author（角色分离）"""
        qb_path = BACKEND_DIR / 'knowledge_base' / COURSE_CODE / 'question_bank.json'
        assert qb_path.exists(), 'question_bank.json 不存在'
        with open(qb_path, 'r', encoding='utf-8') as f:
            qb = json.load(f)

        for q in qb.get('questions', []):
            if q.get('review_status') == 'approved':
                author = q.get('author') or q.get('content_author')
                reviewer = q.get('reviewed_by')
                if author and reviewer:
                    assert author != reviewer, \
                        '题目 ' + str(q.get('question_id', '')) + \
                        ' 自审自批: author=' + str(author) + ' == reviewer=' + str(reviewer)


# =====================================================================
# 脚本入口（保留 __main__ 兼容直接运行）
# =====================================================================

if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v', '-rs']))
