"""
Embedding模型选型实验 - 主评测脚本

控制变量（保证对比有效）：
- 同一份questions.json
- 同一Qdrant文档库（同一批chunk切分）
- 同一Top-K（默认10）
- 同一Distance（Cosine）
- 关闭Reranker（纯Embedding检索）
- 不进入大模型回答阶段

每个候选模型使用独立的Qdrant collection（避免维度冲突）。
BGE-M3为1024维，其他3个候选为768维。

运行方式：
    cd backend
    python -m tests.embedding_benchmark.benchmark --models bge-base-zh m3e-base text2vec
    python -m tests.embedding_benchmark.benchmark --models bge-base-zh m3e-base text2vec bge-m3 --repeat 3
"""
import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
import requests
from pathlib import Path
from typing import Dict, List

# 设置HF镜像加速下载
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 确保导入backend模块
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

from rag.config import settings
from .metrics import evaluate_single, aggregate, save_report


# ====================================================================
# 候选模型注册表（维度用于自动创建对应Qdrant collection）
# ====================================================================
CANDIDATE_MODELS = {
    "bge-base-zh": {
        "model_name": "BAAI/bge-base-zh-v1.5",
        "dim": 768,
        "description": "智源中文基础向量模型v1.5（项目当前使用）",
    },
    "m3e-base": {
        "model_name": "moka-ai/m3e-base",
        "dim": 768,
        "description": "Moka AI中文向量模型",
    },
    "text2vec": {
        "model_name": "shibing624/text2vec-base-chinese",
        "dim": 768,
        "description": "text2vec中文基础模型",
    },
    "bge-m3": {
        "model_name": "BAAI/bge-m3",
        "dim": 1024,
        "description": "智源多语言多功能大模型（机器资源允许时加入）",
    },
}


def load_questions() -> List[Dict]:
    """加载测试问题集。"""
    qpath = Path(__file__).parent / "questions.json"
    with open(qpath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_qdrant_client() -> QdrantClient:
    """根据settings获取Qdrant客户端。"""
    if settings.qdrant_mode == "local":
        return QdrantClient(path=settings.qdrant_local_path)
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        check_compatibility=False,
    )


def build_collection_for_model(client: QdrantClient, model_key: str, model_info: Dict,
                              source_collection: str, target_collection: str,
                              encoder) -> int:
    """
    将源collection的所有点（文本+元数据）用新模型重新编码，
    写入为该模型专属的新collection。
    返回写入的point数量。
    """
    # 1. 读取源collection全部点
    stats = client.get_collection(source_collection)
    total = stats.points_count or 0
    if total == 0:
        raise RuntimeError(f"源collection {source_collection} 为空，请先在主系统中索引文档")

    print(f"[build] 从 {source_collection} 读取 {total} 个chunk")
    all_points, _ = client.scroll(
        collection_name=source_collection,
        limit=total,
        with_payload=True,
        with_vectors=False,
    )

    # 2. 为新模型创建独立collection
    collections = [c.name for c in client.get_collections().collections]
    if target_collection in collections:
        client.delete_collection(target_collection)
    client.create_collection(
        collection_name=target_collection,
        vectors_config=VectorParams(size=model_info["dim"], distance=Distance.COSINE),
    )

    # 3. 批量编码并写入
    batch = 64
    texts = [p.payload.get("text", "") for p in all_points]
    metadatas = [p.payload or {} for p in all_points]

    written = 0
    for i in range(0, len(texts), batch):
        batch_texts = texts[i:i + batch]
        batch_meta = metadatas[i:i + batch]
        vectors = encoder.encode(batch_texts)
        points = []
        for j, (vec, meta) in enumerate(zip(vectors, batch_meta)):
            # 用源point的id作为锚点，便于跨模型对齐
            src_id = all_points[i + j].id
            points.append(PointStruct(id=str(src_id), vector=vec, payload=meta))
        client.upsert(collection_name=target_collection, points=points)
        written += len(points)
        if (i // batch) % 5 == 0:
            print(f"[build] 已写入 {written}/{total}")

    print(f"[build] 模型 {model_key} collection构建完成: {written} points")
    return written


def _rest_search(client: QdrantClient, collection: str, query_vec, top_k: int):
    """通过REST API搜索（兼容Qdrant 1.7.0，qdrant-client 1.18移除了search方法）。"""
    host = settings.qdrant_host
    port = settings.qdrant_port
    url = f"http://{host}:{port}/collections/{collection}/points/search"
    resp = requests.post(url, json={
        "vector": query_vec.tolist() if hasattr(query_vec, "tolist") else list(query_vec),
        "limit": top_k,
        "with_payload": True,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["result"]


def search_with_model(client: QdrantClient, collection: str, encoder, query: str,
                     top_k: int = 10) -> List[Dict]:
    """用指定模型编码query并检索对应collection。"""
    query_vec = encoder.encode(query)
    results = _rest_search(client, collection, query_vec, top_k)
    return [{"id": str(r["id"]), "score": float(r["score"]), "payload": r.get("payload", {})} for r in results]


def benchmark_one_model(model_key: str, questions: List[Dict], top_k: int = 10,
                        repeat: int = 1) -> Dict:
    """对单个模型执行完整评测。"""
    if model_key not in CANDIDATE_MODELS:
        raise ValueError(f"未知模型: {model_key}，可选: {list(CANDIDATE_MODELS.keys())}")

    info = CANDIDATE_MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"评测模型: {info['model_name']} (dim={info['dim']})")
    print(f"{'='*60}")

    # 1. 加载模型并记录内存
    tracemalloc.start()
    t0 = time.time()
    encoder = SentenceTransformer(info["model_name"])
    model_load_time = time.time() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    model_load_peak_mb = peak / (1024 * 1024)
    print(f"[load] 加载耗时 {model_load_time:.2f}s, 峰值内存 {model_load_peak_mb:.2f} MB")

    # 2. 构建该模型专属的Qdrant collection
    client = get_qdrant_client()
    target_collection = f"benchmark_{model_key.replace('-', '_')}"
    source_collection = settings.qdrant_collection
    chunk_count = build_collection_for_model(
        client, model_key, info, source_collection, target_collection, encoder
    )

    # 3. 预热：前3条问题编码一次
    warmup_qs = [q["question"] for q in questions[:3]]
    _ = encoder.encode(warmup_qs)

    # 4. 正式评测（可重复多次取平均）
    all_runs = []
    for run_idx in range(repeat):
        per_question = []
        encoding_latencies = []
        search_latencies = []

        for q in questions:
            query = q["question"]

            # 编码耗时
            t1 = time.time()
            query_vec = encoder.encode(query)
            encode_ms = (time.time() - t1) * 1000
            encoding_latencies.append(encode_ms)

            # 检索耗时（仅Qdrant search部分）
            t2 = time.time()
            results = _rest_search(client, target_collection, query_vec, top_k)
            search_ms = (time.time() - t2) * 1000
            search_latencies.append(search_ms)

            retrieved_ids = [str(r["id"]) for r in results]
            per_question.append(evaluate_single(q, retrieved_ids))

        agg = aggregate(per_question)
        agg_run = {
            "run": run_idx + 1,
            "per_question": per_question,
            "encoding_latency_ms_avg": sum(encoding_latencies) / len(encoding_latencies),
            "search_latency_ms_avg": sum(search_latencies) / len(search_latencies),
            **agg,
        }
        all_runs.append(agg_run)
        print(f"[run {run_idx+1}] Hit@1={agg['hit_at_1']:.3f} Hit@3={agg['hit_at_3']:.3f} "
              f"MRR={agg['mrr']:.3f} 编码={agg_run['encoding_latency_ms_avg']:.1f}ms "
              f"检索={agg_run['search_latency_ms_avg']:.1f}ms")

    # 5. 多轮平均
    avg = {
        "model_key": model_key,
        "model_name": info["model_name"],
        "dim": info["dim"],
        "description": info["description"],
        "chunk_count": chunk_count,
        "top_k": top_k,
        "repeat": repeat,
        "model_load_time_s": model_load_time,
        "model_load_peak_mb": model_load_peak_mb,
        "hit_at_1": sum(r["hit_at_1"] for r in all_runs) / repeat,
        "hit_at_3": sum(r["hit_at_3"] for r in all_runs) / repeat,
        "recall_at_5": sum(r["recall_at_5"] for r in all_runs) / repeat,
        "mrr": sum(r["mrr"] for r in all_runs) / repeat,
        "encoding_latency_ms": sum(r["encoding_latency_ms_avg"] for r in all_runs) / repeat,
        "search_latency_ms": sum(r["search_latency_ms_avg"] for r in all_runs) / repeat,
        "all_runs": all_runs,
    }

    # 6. 清理：可选删除临时collection
    # client.delete_collection(target_collection)

    # 7. 释放模型内存
    del encoder
    gc.collect()

    return avg


def main():
    parser = argparse.ArgumentParser(description="Embedding模型选型评测")
    parser.add_argument("--models", nargs="+", required=True,
                        choices=list(CANDIDATE_MODELS.keys()),
                        help="要评测的模型列表")
    parser.add_argument("--top_k", type=int, default=10, help="检索返回数量")
    parser.add_argument("--repeat", type=int, default=1, help="每模型重复运行次数")
    parser.add_argument("--output", type=str, default=None,
                        help="结果输出路径，默认为同级results.json")
    args = parser.parse_args()

    questions = load_questions()
    print(f"加载 {len(questions)} 道测试问题")

    # 检查ground truth质量
    resolved_status = [q.get("chunk_resolution", {}).get("status", "unknown") for q in questions]
    has_real_ids = sum(1 for q in questions if q.get("relevant_chunk_ids") or (
        isinstance(q.get("resolved_chunk_metadata"), list) and
        any(isinstance(item, dict) and item.get("point_id") for item in q.get("resolved_chunk_metadata", []))
    ))
    unresolved_count = sum(1 for s in resolved_status if s == "unresolved")
    has_soft_labels = sum(1 for q, s in zip(questions, resolved_status)
                         if s != "unresolved"
                         and not q.get("relevant_chunk_ids")
                         and not (isinstance(q.get("resolved_chunk_metadata"), list) and
                              any(isinstance(item, dict) and item.get("point_id") for item in q.get("resolved_chunk_metadata", [])))
                         and q.get("relevant_keywords"))

    print(f"  有真实ID: {has_real_ids} 道")
    if unresolved_count:
        print(f"  知识库无匹配内容(unresolved): {unresolved_count} 道（将被跳过，不参与指标计算）")
    if has_soft_labels:
        print(f"  仅有软标签(relevant_keywords): {has_soft_labels} 道")
    if has_soft_labels:
        print("\n  ⚠️  部分题目缺少真实Qdrant point ID。建议运行：")
        print("     python -m tests.embedding_benchmark.fill_real_chunk_ids --strict")
        print("     然后再运行本评测脚本，以获得可信的检索指标。\n")

    # 验证源collection存在
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        print(f"❌ 源collection '{settings.qdrant_collection}' 不存在！")
        print(f"   可用的collection: {collections}")
        print(f"   请先在主系统中索引文档，或修改 rag/config.py 中的 qdrant_collection 设置")
        sys.exit(1)
    stats = client.get_collection(settings.qdrant_collection)
    print(f"源collection '{settings.qdrant_collection}': {stats.points_count or 0} 个chunk")

    output_path = args.output or str(Path(__file__).parent / "results.json")

    all_results = {}
    for model_key in args.models:
        try:
            result = benchmark_one_model(model_key, questions, args.top_k, args.repeat)
            all_results[model_key] = result
        except Exception as e:
            print(f"[ERROR] 模型 {model_key} 评测失败: {e}")
            all_results[model_key] = {"error": str(e), "model_key": model_key}

    # 保存环境元信息
    import platform
    all_results["_meta"] = {
        "cpu": platform.processor(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "top_k": args.top_k,
        "repeat": args.repeat,
        "question_count": len(questions),
        "source_collection": settings.qdrant_collection,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "qdrant_mode": settings.qdrant_mode,
        "reranker": "DISABLED (Embedding-only benchmark)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_report(all_results, output_path)

    # 控制台打印汇总
    print("\n" + "=" * 70)
    print("汇总对比")
    print("=" * 70)
    print(f"{'Model':<35}{'Dim':<6}{'Hit@1':<8}{'Hit@3':<8}{'MRR':<8}{'Encode(ms)':<12}{'Search(ms)':<12}")
    for k, v in all_results.items():
        if k == "_meta" or "error" in v:
            continue
        print(f"{v['model_name']:<35}{v['dim']:<6}{v['hit_at_1']:<8.3f}"
              f"{v['hit_at_3']:<8.3f}{v['mrr']:<8.3f}"
              f"{v['encoding_latency_ms']:<12.1f}{v['search_latency_ms']:<12.1f}")


if __name__ == "__main__":
    main()
