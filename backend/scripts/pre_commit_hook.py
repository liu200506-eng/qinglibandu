#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青藜伴读 pre-commit 快速校验钩子

只检查暂存区中被修改的知识库文件，不运行：
  - Qdrant 同步
  - Embedding 计算
  - 网络链接访问
  - validate-all（完整校验）

退出码:
  0 = 通过
  1 = 校验失败
  2 = 环境错误（如 Python 模块缺失）

完整校验请运行:
  python backend/manage_knowledge.py validate-all
"""
import os
import sys
import json
import re
import unicodedata
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


# ============== 路径处理 ==============

# 仓库根目录（基于当前脚本位置计算，不依赖 cwd）
SCRIPT_DIR = Path(__file__).resolve().parent  # backend/scripts/
BACKEND_DIR = SCRIPT_DIR.parent               # backend/
REPO_ROOT = BACKEND_DIR.parent                # 仓库根目录
KNOWLEDGE_BASE_DIR = BACKEND_DIR / 'knowledge_base'

# 将 backend 加入 sys.path，便于导入项目模块
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============== Windows 非法文件名检查 ==============

WINDOWS_INVALID_CHARS = set('\\/:*?"<>|')
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}
MAX_PATH_LENGTH = 200  # Windows 限制约为 260，留余量


def color(text: str, code: str) -> str:
    codes = {'red': '31', 'green': '32', 'yellow': '33', 'blue': '34', 'gray': '90'}
    return "\033[" + codes.get(code, '0') + "m" + text + "\033[0m"


def ok(text: str) -> str: return color(text, 'green')
def fail(text: str) -> str: return color(text, 'red')
def warn(text: str) -> str: return color(text, 'yellow')
def info(text: str) -> str: return color(text, 'blue')


# ============== 获取暂存区文件 ==============

def get_staged_files() -> List[str]:
    """获取本次 git commit 暂存区中所有修改的文件（相对于仓库根目录）"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def filter_relevant_files(files: List[str]) -> Tuple[List[str], List[str]]:
    """筛选出知识库中的 JSON 和 Markdown 文件"""
    json_files = []
    md_files = []
    kb_marker = os.path.join('backend', 'knowledge_base') + os.sep
    kb_marker_unix = 'backend/knowledge_base/'
    
    for f in files:
        # 转换为绝对路径
        abs_path = REPO_ROOT / f
        if not abs_path.exists():
            continue
        # 只校验知识库目录内的文件
        f_normalized = f.replace('\\', '/')
        if 'backend/knowledge_base/' not in f_normalized:
            continue
        if f.endswith('.json'):
            json_files.append(str(abs_path))
        elif f.endswith('.md'):
            md_files.append(str(abs_path))
    return json_files, md_files


# ============== 检查 1: Windows 非法文件名 ==============

def check_windows_filename(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 Windows 非法文件名（保留字、非法字符、结尾空格等）"""
    errors = []
    for f in files:
        basename = os.path.basename(f)
        name_without_ext = os.path.splitext(basename)[0]
        
        # 检查非法字符
        invalid_in_name = set(basename) & WINDOWS_INVALID_CHARS
        if invalid_in_name:
            errors.append("文件名含非法字符 " + "".join(invalid_in_name) + ": " + f)
        
        # 检查 Windows 保留名
        if name_without_ext.upper() in WINDOWS_RESERVED_NAMES:
            errors.append("文件名是 Windows 保留名: " + f)
        
        # 检查结尾空格或英文句点
        if basename != basename.rstrip(' .'):
            errors.append("文件名以空格或句点结尾: " + f)
        
        # 检查文件名长度
        if len(basename) > MAX_PATH_LENGTH:
            errors.append("文件名过长 (>" + str(MAX_PATH_LENGTH) + "字符): " + f)
        
        # 检查路径长度
        if len(f) > 260:
            errors.append("路径过长 (>260字符): " + f)
        
        # 检查斜杠导致的意外目录（路径中不应包含 // 或 \\ 重复）
        if '//' in f.replace('\\', '/') or '\\\\' in f:
            errors.append("路径中含重复斜杠: " + f)
        
        # 检查 Unicode 规范化重名（NFC vs NFD）
        try:
            normalized = unicodedata.normalize('NFC', basename)
            if normalized != basename:
                errors.append("文件名未做 Unicode 规范化（建议 NFC）: " + f)
        except Exception:
            pass
    
    return (len(errors) == 0, errors)


# ============== 检查 2: JSON 格式合法性 ==============

def check_json_format(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 JSON 文件格式"""
    errors = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read()
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append("JSON 解析失败: " + f + " - " + str(e))
        except Exception as e:
            errors.append("读取文件失败: " + f + " - " + str(e))
    return (len(errors) == 0, errors)


# ============== 检查 3: course.json 必需字段 ==============

def check_course_json_fields(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 course.json 必需字段"""
    errors = []
    required_fields = ['schema_version', 'course_code', 'course_name', 'publish_status']
    valid_status = ['draft', 'review', 'published', 'demo_only', 'archived']
    
    for f in files:
        if not f.endswith('course.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            for field in required_fields:
                if field not in data:
                    errors.append("course.json 缺少必需字段: " + field + " - " + f)
            status = data.get('publish_status')
            if status and status not in valid_status:
                errors.append("course.json 非法 publish_status: " + status + " - " + f)
            if data.get('schema_version') and not str(data.get('schema_version')).startswith('2.'):
                errors.append("course.json schema_version 不是 2.x: " + str(data.get('schema_version')) + " - " + f)
        except Exception as e:
            errors.append("读取 course.json 失败: " + f + " - " + str(e))
    return (len(errors) == 0, errors)


# ============== 检查 4: knowledge_tree.json 字段和重复 node_code ==============

def check_knowledge_tree(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 knowledge_tree.json 字段和重复 node_code"""
    errors = []
    
    for f in files:
        if not f.endswith('knowledge_tree.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            
            if 'schema_version' not in data:
                errors.append("knowledge_tree.json 缺少 schema_version - " + f)
            if 'course_code' not in data:
                errors.append("knowledge_tree.json 缺少 course_code - " + f)
            
            all_nodes = {}
            node_ids = set()
            
            def collect_nodes(nodes, parent_path=""):
                for node in nodes:
                    node_id = node.get('id')
                    node_code = node.get('node_code')
                    name = node.get('name', '')
                    path = parent_path + "/" + name
                    
                    if not node_id:
                        errors.append("知识点缺少 id 字段 - " + f + " (" + path + ")")
                    if not node_code:
                        errors.append("知识点缺少 node_code 字段 - " + f + " (" + name + ")")
                    if not name:
                        errors.append("知识点缺少 name 字段 - " + f + " (id=" + str(node_id) + ")")
                    
                    difficulty = node.get('difficulty', 0.5)
                    if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 1:
                        errors.append("难度非法 " + str(difficulty) + " - " + f + " (" + name + ")")
                    
                    threshold = node.get('mastery_threshold', 0.6)
                    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                        errors.append("掌握阈值非法 " + str(threshold) + " - " + f + " (" + name + ")")
                    
                    if node_id:
                        if node_id in node_ids:
                            errors.append("知识点 ID 重复: " + str(node_id) + " - " + f)
                        node_ids.add(node_id)
                    
                    if node_code:
                        if node_code in all_nodes:
                            errors.append(
                                "node_code 重复: " + node_code + 
                                " (节点1: " + all_nodes[node_code] + 
                                ", 节点2: " + name + ") - " + f
                            )
                        else:
                            all_nodes[node_code] = name
                    
                    children = node.get('children', [])
                    if children:
                        collect_nodes(children, path)
            
            collect_nodes(data.get('roots', []))
        except Exception as e:
            errors.append("读取 knowledge_tree.json 失败: " + f + " - " + str(e))
    
    return (len(errors) == 0, errors)


# ============== 检查 5: 依赖关系和循环依赖 ==============

def check_dependencies(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 dependencies.json 的合法性、先修节点存在性、循环依赖"""
    errors = []
    
    for f in files:
        if not f.endswith('dependencies.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            
            course_dir = os.path.dirname(f)
            tree_file = os.path.join(course_dir, 'knowledge_tree.json')
            if not os.path.exists(tree_file):
                errors.append("缺少 knowledge_tree.json - " + course_dir)
                continue
            
            with open(tree_file, 'r', encoding='utf-8') as fp:
                tree_data = json.load(fp)
            
            all_node_ids = set()
            def collect_ids(nodes):
                for node in nodes:
                    nid = node.get('id')
                    if nid:
                        all_node_ids.add(nid)
                    collect_ids(node.get('children', []))
            collect_ids(tree_data.get('roots', []))
            
            dep_graph = {}
            
            deps = data.get('dependencies', [])
            for dep in deps:
                src = dep.get('source_id') or dep.get('source')
                tgt = dep.get('target_id') or dep.get('target')
                
                if not src or not tgt:
                    errors.append("依赖关系缺少 source/target - " + f + " - " + json.dumps(dep, ensure_ascii=False))
                    continue
                
                if src not in all_node_ids:
                    errors.append("依赖关系 source 不存在: " + str(src) + " - " + f)
                if tgt not in all_node_ids:
                    errors.append("依赖关系 target 不存在: " + str(tgt) + " - " + f)
                
                if src not in dep_graph:
                    dep_graph[src] = []
                dep_graph[src].append(tgt)
            
            # 循环依赖检测（DFS）
            WHITE, GRAY, BLACK = 0, 1, 2
            color_map = {nid: WHITE for nid in all_node_ids}
            
            def dfs(node, path):
                if color_map.get(node) == GRAY:
                    cycle = path[path.index(node):] + [node] if node in path else path + [node]
                    errors.append("检测到循环依赖: " + " -> ".join(cycle) + " - " + f)
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
            
        except Exception as e:
            errors.append("读取 dependencies.json 失败: " + f + " - " + str(e))
    
    return (len(errors) == 0, errors)


# ============== 检查 6: 题库答案和难度 ==============

def check_question_bank(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 question_bank.json 的答案和难度"""
    errors = []
    
    for f in files:
        if not f.endswith('question_bank.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            
            course_dir = os.path.dirname(f)
            tree_file = os.path.join(course_dir, 'knowledge_tree.json')
            if not os.path.exists(tree_file):
                continue
            
            with open(tree_file, 'r', encoding='utf-8') as fp:
                tree_data = json.load(fp)
            
            all_node_ids = set()
            def collect_ids(nodes):
                for node in nodes:
                    nid = node.get('id')
                    if nid:
                        all_node_ids.add(nid)
                    collect_ids(node.get('children', []))
            collect_ids(tree_data.get('roots', []))
            
            questions = data.get('questions', [])
            for q in questions:
                qid = q.get('question_id') or q.get('id', 'unknown')
                
                answer = q.get('answer')
                if not answer:
                    errors.append("题目答案为空: " + str(qid) + " - " + f)
                
                difficulty = q.get('difficulty', 0.5)
                if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 1:
                    errors.append("题目难度非法 " + str(difficulty) + ": " + str(qid) + " - " + f)
                
                kp_id = q.get('knowledge_point_id') or q.get('knowledge_node_id')
                kp_name = q.get('knowledge_point_name') or q.get('knowledge_node_name')
                if not kp_id and not kp_name:
                    errors.append("题目未绑定知识点: " + str(qid) + " - " + f)
                elif kp_id and kp_id not in all_node_ids:
                    errors.append("题目绑定知识点不存在: " + str(kp_id) + " - " + f + " (题目 " + str(qid) + ")")
            
        except Exception as e:
            errors.append("读取 question_bank.json 失败: " + f + " - " + str(e))
    
    return (len(errors) == 0, errors)


# ============== 检查 7: 资源链接格式 ==============

def check_resources(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 resources.json 资源链接格式（不检查可达性）"""
    errors = []
    url_pattern = re.compile(r'^https?://')
    
    for f in files:
        if not f.endswith('resources.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            
            course_dir = os.path.dirname(f)
            tree_file = os.path.join(course_dir, 'knowledge_tree.json')
            if not os.path.exists(tree_file):
                continue
            
            with open(tree_file, 'r', encoding='utf-8') as fp:
                tree_data = json.load(fp)
            
            all_node_ids = set()
            def collect_ids(nodes):
                for node in nodes:
                    nid = node.get('id')
                    if nid:
                        all_node_ids.add(nid)
                    collect_ids(node.get('children', []))
            collect_ids(tree_data.get('roots', []))
            
            resources = data.get('resources', [])
            for r in resources:
                rid = r.get('resource_id') or r.get('id', 'unknown')
                url = r.get('url', '')
                if url and not url_pattern.match(url):
                    errors.append("资源 URL 格式不合法: " + url + " - " + f + " (资源 " + str(rid) + ")")
                
                kp_id = r.get('knowledge_point_id') or r.get('knowledge_node_id')
                if kp_id and kp_id not in all_node_ids:
                    errors.append("资源绑定知识点不存在: " + str(kp_id) + " - " + f + " (资源 " + str(rid) + ")")
        except Exception as e:
            errors.append("读取 resources.json 失败: " + f + " - " + str(e))
    
    return (len(errors) == 0, errors)


# ============== 检查 8: error_patterns.json 来源字段 ==============

def check_error_patterns(files: List[str]) -> Tuple[bool, List[str]]:
    """检查 error_patterns.json 的来源字段（review 状态课程才严格检查）"""
    errors = []
    
    valid_origin_types = {
        'textbook', 'official_document', 'open_course',
        'teacher_defined', 'team_defined'
    }
    
    for f in files:
        if not f.endswith('error_patterns.json'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            
            course_dir = os.path.dirname(f)
            course_file = os.path.join(course_dir, 'course.json')
            
            publish_status = 'draft'
            if os.path.exists(course_file):
                with open(course_file, 'r', encoding='utf-8') as fp:
                    course_data = json.load(fp)
                publish_status = course_data.get('publish_status', 'draft')
            
            # draft 状态只做基础检查
            if publish_status == 'draft' or publish_status == 'archived':
                continue
            
            patterns = data.get('patterns', data.get('error_patterns', []))
            for p in patterns:
                pid = p.get('pattern_id') or p.get('id', 'unknown')
                
                # review 和 published 状态必须检查来源字段
                if publish_status in ('review', 'published'):
                    if 'origin_type' not in p:
                        errors.append("error_pattern 缺少 origin_type - " + f + " (" + str(pid) + ")")
                    elif p['origin_type'] not in valid_origin_types:
                        errors.append(
                            "error_pattern 非法 origin_type: " + str(p['origin_type']) +
                            " (合法值: " + ", ".join(sorted(valid_origin_types)) + ") - " + f +
                            " (" + str(pid) + ")"
                        )
                    
                    if 'source_ids' not in p or not p['source_ids']:
                        errors.append("error_pattern 缺少 source_ids - " + f + " (" + str(pid) + ")")
                    
                    if 'review_status' not in p:
                        errors.append("error_pattern 缺少 review_status - " + f + " (" + str(pid) + ")")
        except Exception as e:
            errors.append("读取 error_patterns.json 失败: " + f + " - " + str(e))
    
    return (len(errors) == 0, errors)


# ============== 主校验流程 ==============

def main() -> int:
    # 环境检查
    if not KNOWLEDGE_BASE_DIR.exists():
        print(ok("[SKIP] 知识库目录不存在，跳过校验"))
        return 0
    
    print(info("=" * 60))
    print(info("青藜伴读 pre-commit 快速校验"))
    print(info("=" * 60))
    
    staged = get_staged_files()
    if not staged:
        print(ok("[SKIP] 没有暂存的文件"))
        return 0
    
    print("暂存文件数: " + str(len(staged)))
    
    json_files, md_files = filter_relevant_files(staged)
    
    if not json_files and not md_files:
        print(ok("[SKIP] 没有知识库相关的 JSON/Markdown 文件变更"))
        return 0
    
    print("待校验 JSON 文件: " + str(len(json_files)))
    print("待校验 Markdown 文件: " + str(len(md_files)))
    print()
    
    all_files = json_files + md_files
    all_pass = True
    all_errors = []
    
    checks = [
        ("Windows 非法文件名", check_windows_filename, all_files),
        ("JSON 格式合法性", check_json_format, json_files),
        ("course.json 必需字段", check_course_json_fields, json_files),
        ("knowledge_tree.json 字段和重复 node_code", check_knowledge_tree, json_files),
        ("依赖关系和循环依赖", check_dependencies, json_files),
        ("题目答案和难度", check_question_bank, json_files),
        ("资源链接格式", check_resources, json_files),
        ("error_patterns 来源字段", check_error_patterns, json_files),
    ]
    
    for idx, (name, check_func, target_files) in enumerate(checks, 1):
        if not target_files:
            # 跳过空目标
            if name == "course.json 必需字段" and not any(f.endswith('course.json') for f in json_files):
                continue
            if name == "knowledge_tree.json 字段和重复 node_code" and not any(f.endswith('knowledge_tree.json') for f in json_files):
                continue
            if name == "依赖关系和循环依赖" and not any(f.endswith('dependencies.json') for f in json_files):
                continue
            if name == "题目答案和难度" and not any(f.endswith('question_bank.json') for f in json_files):
                continue
            if name == "资源链接格式" and not any(f.endswith('resources.json') for f in json_files):
                continue
            if name == "error_patterns 来源字段" and not any(f.endswith('error_patterns.json') for f in json_files):
                continue
        
        print(info("[" + str(idx) + "] " + name + "..."))
        passed, errors = check_func(target_files)
        if passed:
            print(ok("  [PASS]"))
        else:
            print(fail("  [FAIL]"))
            for e in errors:
                print("    - " + e)
            all_errors.extend(errors)
            all_pass = False
    
    print()
    print("=" * 60)
    if all_pass:
        print(ok("[PASS] 所有校验通过，允许提交"))
        print("=" * 60)
        return 0
    else:
        print(fail("[FAIL] 校验失败，共 " + str(len(all_errors)) + " 个错误"))
        print(fail("请修复上述错误后重新提交"))
        print()
        print("跳过校验（紧急情况）: git commit --no-verify")
        print("完整校验（慢）: python backend/manage_knowledge.py validate-all")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as e:
        print(fail("[ERROR] 钩子执行异常: " + str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(2)
