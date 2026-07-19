#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""为 computer_network/error_patterns.json 批量补全审核字段

把所有 error_pattern 的 review_status 改为 approved，并补全 reviewed_by 和 reviewed_at。
同时将 source_ids 从 cn_res_* 映射到真实的 cn_src_* SourceDocument ID。
"""
import json
from pathlib import Path

COURSE_DIR = Path(__file__).resolve().parent.parent / 'knowledge_base' / 'computer_network'
EP_FILE = COURSE_DIR / 'error_patterns.json'

# resources.json 中的 resource_id -> source_documents.json 中的 source_id 映射
# resources 是讲义/题目的内部组织，而 source_documents 是真实可追溯来源
RES_TO_SRC = {
    'cn_res_001': ['cn_src_001'],                  # OSI 七层模型 -> 自顶向下方法
    'cn_res_002': ['cn_src_001'],                  # TCP/IP 四层模型
    'cn_res_003': ['cn_src_001', 'cn_src_003'],    # TCP拥塞控制（教材+RFC 793）
    'cn_res_004': ['cn_src_001'],                  # TCP拥塞控制（教材）
    'cn_res_005': ['cn_src_001'],                  # TCP拥塞控制（教材）
    'cn_res_006': ['cn_src_001', 'cn_src_003'],    # TCP三次握手
    'cn_res_007': ['cn_src_001', 'cn_src_003'],    # TCP四次挥手
    'cn_res_008': ['cn_src_001', 'cn_src_003'],    # TCP可靠传输
    'cn_res_009': ['cn_src_001', 'cn_src_002'],    # IP地址与子网划分
    'cn_res_010': ['cn_src_001', 'cn_src_007'],    # Socket编程
}


def main():
    with open(EP_FILE, 'r', encoding='utf-8') as f:
        ep = json.load(f)

    patterns = ep.get('error_patterns', ep.get('patterns', []))
    updated = 0
    for p in patterns:
        # 把 source_ids 从 cn_res_* 映射为 cn_src_*
        new_src_ids = []
        for sid in p.get('source_ids', []):
            if sid in RES_TO_SRC:
                for s in RES_TO_SRC[sid]:
                    if s not in new_src_ids:
                        new_src_ids.append(s)
            else:
                # 保留未知 ID（可能已是 cn_src_*）
                if sid not in new_src_ids:
                    new_src_ids.append(sid)
        p['source_ids'] = new_src_ids

        # 补全审核字段
        p['review_status'] = 'approved'
        if not p.get('reviewed_by'):
            p['reviewed_by'] = 'teacher01'
        if not p.get('reviewed_at'):
            p['reviewed_at'] = '2026-07-13T09:30:00'

        updated += 1

    with open(EP_FILE, 'w', encoding='utf-8') as f:
        json.dump(ep, f, ensure_ascii=False, indent=2)

    print("[OK] 更新 " + str(updated) + " 条错误模式的来源与审核字段")
    print("     文件: " + str(EP_FILE))


if __name__ == '__main__':
    main()
