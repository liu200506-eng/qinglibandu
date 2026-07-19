#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
迁移脚本：为所有知识点树添加 node_code 字段
node_code = 知识点的 id 字段（作为稳定标识符）
"""

import os
import json

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_DIR = os.path.join(BACKEND_DIR, 'knowledge_base')

COURSES = [
    'computer_network',
    'computer_organization',
    'database_principles',
    'data_structure',
    'operating_system',
]

def add_node_code(nodes):
    """为知识点树节点添加 node_code 字段"""
    for node in nodes:
        node_id = node.get('id', '')
        # node_code 直接使用 id 作为稳定标识符
        node['node_code'] = node_id
        
        if 'children' in node and node['children']:
            add_node_code(node['children'])

def migrate_course(course_dir):
    """迁移单个课程的知识点树"""
    tree_file = os.path.join(course_dir, 'knowledge_tree.json')
    if not os.path.exists(tree_file):
        print("[SKIP] " + course_dir + " 无 knowledge_tree.json")
        return
    
    with open(tree_file, 'r', encoding='utf-8') as f:
        tree = json.load(f)
    
    # 添加 schema_version
    if 'schema_version' not in tree:
        tree['schema_version'] = '2.0'
    
    # 添加 course_code（如果不存在）
    if 'course_code' not in tree:
        tree['course_code'] = tree.get('course_id', '')
    
    # 为所有节点添加 node_code
    roots = tree.get('roots', [])
    add_node_code(roots)
    
    with open(tree_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    
    print("[OK] " + os.path.basename(course_dir) + " 迁移完成")

def main():
    print("开始迁移知识点树...")
    for course in COURSES:
        course_dir = os.path.join(KNOWLEDGE_BASE_DIR, course)
        if os.path.exists(course_dir):
            migrate_course(course_dir)
        else:
            print("[SKIP] " + course + " 目录不存在")
    print("\n迁移完成！")

if __name__ == '__main__':
    main()
