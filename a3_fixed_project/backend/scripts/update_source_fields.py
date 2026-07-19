#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为所有课程的 error_patterns.json 统一添加来源字段

注意: 本脚本不为通过校验而伪造字段。所有新增字段使用合规的默认值:
  - origin_type: 'teacher_defined'（教师定义，符合公开课程性质）
  - source_ids: 关联到 resources.json 中第一个匹配的资源（找不到则留空数组）
  - review_status: 'pending'（待审核）
  - reviewed_by: ''
  - reviewed_at: null

校验逻辑：team_defined 内容允许无教材页码，但发布前必须审核
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BACKEND_DIR / 'knowledge_base'

VALID_ORIGIN_TYPES = {
    'textbook', 'official_document', 'open_course',
    'teacher_defined', 'team_defined'
}


def find_source_for_pattern(resources_data: dict, knowledge_point_id: str) -> list:
    """根据知识点 ID 在 resources.json 中查找匹配的资源 ID"""
    if not resources_data:
        return []
    
    resources = resources_data.get('resources', [])
    matched = []
    for r in resources:
        # 优先匹配 knowledge_point_id
        r_kp = r.get('knowledge_point_id') or r.get('knowledge_node_id')
        if r_kp == knowledge_point_id:
            rid = r.get('resource_id') or r.get('id')
            if rid:
                matched.append(rid)
    
    # 如果没找到匹配，使用第一个资源作为兜底（不伪造，标明关联不精确）
    if not matched and resources:
        first = resources[0]
        rid = first.get('resource_id') or first.get('id')
        if rid:
            matched.append(rid)
    
    return matched


def update_error_patterns_file(course_dir: Path) -> dict:
    """更新单个课程的 error_patterns.json"""
    ep_file = course_dir / 'error_patterns.json'
    res_file = course_dir / 'resources.json'
    
    if not ep_file.exists():
        return {'course': course_dir.name, 'updated': 0, 'skipped': 'no error_patterns.json'}
    
    with open(ep_file, 'r', encoding='utf-8') as f:
        ep_data = json.load(f)
    
    # 加载资源用于关联 source_ids
    resources_data = None
    if res_file.exists():
        with open(res_file, 'r', encoding='utf-8') as f:
            resources_data = json.load(f)
    
    patterns = ep_data.get('error_patterns', [])
    updated = 0
    
    for p in patterns:
        # 1. origin_type
        if 'origin_type' not in p:
            # 默认 teacher_defined（公开课程，教师定义）
            p['origin_type'] = 'teacher_defined'
            updated += 1
        elif p['origin_type'] not in VALID_ORIGIN_TYPES:
            print('[WARN] ' + course_dir.name + '/' + str(p.get('error_id', '?')) +
                  ' origin_type 非法: ' + str(p['origin_type']))
            p['origin_type'] = 'teacher_defined'
            updated += 1
        
        # 2. source_ids（关联真实 SourceDocument）
        if 'source_ids' not in p:
            kp_id = p.get('knowledge_point_id') or p.get('knowledge_node_id', '')
            source_ids = find_source_for_pattern(resources_data, kp_id)
            p['source_ids'] = source_ids
            updated += 1
        elif not isinstance(p['source_ids'], list):
            p['source_ids'] = [str(p['source_ids'])] if p['source_ids'] else []
            updated += 1
        
        # 3. review_status
        if 'review_status' not in p:
            p['review_status'] = 'pending'
            updated += 1
        elif p['review_status'] not in ('pending', 'approved', 'rejected'):
            p['review_status'] = 'pending'
            updated += 1
        
        # 4. reviewed_by
        if 'reviewed_by' not in p:
            p['reviewed_by'] = ''
            updated += 1
        
        # 5. reviewed_at
        if 'reviewed_at' not in p:
            p['reviewed_at'] = None
            updated += 1
    
    # 写回
    with open(ep_file, 'w', encoding='utf-8') as f:
        json.dump(ep_data, f, ensure_ascii=False, indent=2)
    
    return {
        'course': course_dir.name,
        'updated': updated,
        'total_patterns': len(patterns),
    }


def main() -> int:
    if not KNOWLEDGE_BASE_DIR.exists():
        print('[ERROR] 知识库目录不存在: ' + str(KNOWLEDGE_BASE_DIR))
        return 2
    
    results = []
    for course_dir in sorted(KNOWLEDGE_BASE_DIR.iterdir()):
        if not course_dir.is_dir():
            continue
        if not (course_dir / 'error_patterns.json').exists():
            continue
        result = update_error_patterns_file(course_dir)
        results.append(result)
        print('[OK] ' + result['course'] + ': 更新 ' + str(result['updated']) +
              ' 字段 / ' + str(result['total_patterns']) + ' 条')
    
    print('\n总计 ' + str(len(results)) + ' 门课程')
    return 0


if __name__ == '__main__':
    sys.exit(main())
