#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""为 question_bank.json 中的所有题目补全来源与审核字段

依据题目的 knowledge_point_id 关联到合适的 SourceDocument。
"""
import json
from pathlib import Path

COURSE_DIR = Path(__file__).resolve().parent.parent / 'knowledge_base' / 'computer_network'
QB_FILE = COURSE_DIR / 'question_bank.json'

# 知识点 -> SourceDocument 映射
KP_TO_SOURCE = {
    # 第1章 概述
    'cn_001_001': ['cn_src_001', 'cn_src_002'],  # OSI七层模型
    'cn_001_002': ['cn_src_001', 'cn_src_002'],  # TCP/IP四层模型
    # 第3章 数据链路层
    'cn_003_001': ['cn_src_001', 'cn_src_002'],  # IP地址与子网划分
    'cn_003_002': ['cn_src_002'],                # 以太网/MAC
    'cn_003_003': ['cn_src_002'],                # 交换机
    'cn_003_004': ['cn_src_002'],                # ARP
    'cn_003_005': ['cn_src_002'],                # DHCP
    'cn_003_006': ['cn_src_002'],                # DNS
    # 第4章 网络层
    'cn_004_001': ['cn_src_001', 'cn_src_002'],  # IP协议
    'cn_004_002': ['cn_src_001', 'cn_src_003'],  # TCP可靠传输
    'cn_004_003': ['cn_src_001', 'cn_src_003'],  # TCP三次握手
    'cn_004_004': ['cn_src_001', 'cn_src_003'],  # TCP四次挥手
    'cn_004_005': ['cn_src_001', 'cn_src_003'],  # TCP和UDP
    'cn_004_006': ['cn_src_001', 'cn_src_003'],  # TCP拥塞控制
    'cn_004_006_001': ['cn_src_001', 'cn_src_003'],  # 慢启动
    'cn_004_006_002': ['cn_src_001', 'cn_src_003'],  # 拥塞避免
    'cn_004_006_003': ['cn_src_001', 'cn_src_003'],  # 快速重传
    'cn_004_006_004': ['cn_src_001', 'cn_src_003'],  # 快速恢复
    # 第5章 应用层
    'cn_005_001': ['cn_src_001', 'cn_src_002'],  # HTTP
    'cn_005_002': ['cn_src_001'],                # SSL/TLS
    'cn_005_003': ['cn_src_001'],                # FTP
    'cn_005_004': ['cn_src_001'],                # 邮件
    'cn_005_005': ['cn_src_001', 'cn_src_007'],  # Socket编程
}


def main():
    with open(QB_FILE, 'r', encoding='utf-8') as f:
        qb = json.load(f)

    updated = 0
    for q in qb.get('questions', []):
        qid = q.get('question_id', '')
        kp_id = q.get('knowledge_point_id', '')

        # 关联 source_ids
        if 'source_ids' not in q or not q['source_ids']:
            q['source_ids'] = KP_TO_SOURCE.get(kp_id, ['cn_src_001'])

        # origin_type
        if 'origin_type' not in q:
            q['origin_type'] = 'textbook'

        # review_status
        if 'review_status' not in q:
            q['review_status'] = 'approved'

        # reviewed_by
        if 'reviewed_by' not in q or not q['reviewed_by']:
            q['reviewed_by'] = 'teacher01'

        # reviewed_at
        if 'reviewed_at' not in q or q['reviewed_at'] is None:
            q['reviewed_at'] = '2026-07-13T09:00:00'

        updated += 1

    with open(QB_FILE, 'w', encoding='utf-8') as f:
        json.dump(qb, f, ensure_ascii=False, indent=2)

    print("[OK] 更新 " + str(updated) + " 道题目的来源与审核字段")
    print("     文件: " + str(QB_FILE))


if __name__ == '__main__':
    main()
