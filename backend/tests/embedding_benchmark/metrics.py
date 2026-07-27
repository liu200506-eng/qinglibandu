"""
Embedding模型选型实验 - 检索指标计算

不依赖RAGAS，专注于检索层指标：
- Hit@1：Top-1结果是否命中相关chunk
- Hit@3：Top-3中是否出现相关chunk
- Recall@5：Top-5召回了多少比例的相关chunk
- MRR：Mean Reciprocal Rank，正确结果排序越靠前分数越高

ground truth优先级：
1. relevant_chunk_ids（由fill_real_chunk_ids.py回填的真实Qdrant point ID）
2. resolved_chunk_metadata[].point_id（回填脚本输出的元数据）
3. relevant_keywords（退化到关键词软匹配，仅用于无真实ID时）
"""
from typing import List, Dict, Set
import json
from pathlib import Path


def _get_relevant_set(question: Dict) -> Set[str]:
    """提取问题的相关chunk_id集合，作为ground truth。"""
    # 如果标记为unresolved，直接返回空集
    resolution = question.get("chunk_resolution", {})
    if isinstance(resolution, dict) and resolution.get("status") == "unresolved":
        return set()

    # 优先级1: relevant_chunk_ids（由回填脚本写入的真实point ID）
    ids = set(question.get("relevant_chunk_ids", []))
    if ids:
        return ids

    # 优先级2: resolved_chunk_metadata中的point_id
    meta = question.get("resolved_chunk_metadata", [])
    if meta and isinstance(meta, list):
        meta_ids = set()
        for item in meta:
            if isinstance(item, dict) and item.get("point_id"):
                meta_ids.add(str(item["point_id"]))
        if meta_ids:
            return meta_ids

    # 优先级3: 退化到关键词匹配（软标签，仅用于无真实ID时的初步测试）
    keywords = question.get("relevant_keywords", [])
    if keywords:
        return set(keywords)

    return set()


def _hit_at_k(retrieved_ids: List[str], relevant_set: Set[str], k: int) -> int:
    """Top-K中只要出现一个相关项即记为命中。"""
    top_k = retrieved_ids[:k]
    return 1 if any(rid in relevant_set for rid in top_k) else 0


def _recall_at_k(retrieved_ids: List[str], relevant_set: Set[str], k: int) -> float:
    """Top-K召回了相关项的比例。"""
    if not relevant_set:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / len(relevant_set)


def _reciprocal_rank(retrieved_ids: List[str], relevant_set: Set[str]) -> float:
    """第一个相关结果的倒数排名。"""
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_set:
            return 1.0 / i
    return 0.0


def evaluate_single(question: Dict, retrieved_ids: List[str]) -> Dict:
    """对单条问题计算所有指标。"""
    relevant_set = _get_relevant_set(question)
    if not relevant_set:
        return {"skipped": True, "reason": "无标准答案（relevant_chunk_ids和relevant_keywords均为空）"}

    has_real_ids = bool(question.get("relevant_chunk_ids")) or bool(
        isinstance(question.get("resolved_chunk_metadata"), list)
        and any(item.get("point_id") for item in question.get("resolved_chunk_metadata", []) if isinstance(item, dict))
    )

    return {
        "question_id": question.get("question_id"),
        "hit_at_1": _hit_at_k(retrieved_ids, relevant_set, 1),
        "hit_at_3": _hit_at_k(retrieved_ids, relevant_set, 3),
        "recall_at_5": _recall_at_k(retrieved_ids, relevant_set, 5),
        "mrr": _reciprocal_rank(retrieved_ids, relevant_set),
        "relevant_count": len(relevant_set),
        "has_real_ids": has_real_ids,
    }


def aggregate(per_question_results: List[Dict]) -> Dict:
    """汇总所有问题的平均指标。分别统计有真实ID和全部（含软标签）的结果。"""
    valid = [r for r in per_question_results if not r.get("skipped")]
    if not valid:
        return {
            "valid_questions": 0,
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
        }

    # 分离真实ID题和软标签题
    real_id_results = [r for r in valid if r.get("has_real_ids")]
    soft_label_results = [r for r in valid if not r.get("has_real_ids")]

    def _calc(rs):
        if not rs:
            return None
        n = len(rs)
        return {
            "hit_at_1": sum(r["hit_at_1"] for r in rs) / n,
            "hit_at_3": sum(r["hit_at_3"] for r in rs) / n,
            "recall_at_5": sum(r["recall_at_5"] for r in rs) / n,
            "mrr": sum(r["mrr"] for r in rs) / n,
        }

    return {
        "valid_questions": len(valid),
        "real_id_questions": len(real_id_results),
        "soft_label_questions": len(soft_label_results),
        "hit_at_1": sum(r["hit_at_1"] for r in valid) / len(valid),
        "hit_at_3": sum(r["hit_at_3"] for r in valid) / len(valid),
        "recall_at_5": sum(r["recall_at_5"] for r in valid) / len(valid),
        "mrr": sum(r["mrr"] for r in valid) / len(valid),
        "real_id_metrics": _calc(real_id_results),
        "soft_label_metrics": _calc(soft_label_results),
    }


def save_report(per_model_results: Dict, output_path: str):
    """将所有模型的指标结果写入JSON文件。"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(per_model_results, f, ensure_ascii=False, indent=2)
    print(f"[metrics] 报告已保存: {output_path}")


if __name__ == "__main__":
    # 自检
    demo_question = {
        "question_id": "demo",
        "relevant_chunk_ids": ["c1", "c2"],
    }
    demo_retrieved = ["c3", "c1", "c4", "c2", "c5"]
    single = evaluate_single(demo_question, demo_retrieved)
    print("单题结果:", single)
    print("聚合结果:", aggregate([single]))
