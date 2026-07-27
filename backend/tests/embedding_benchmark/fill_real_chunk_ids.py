#!/usr/bin/env python3
"""Fill questions.json with real Qdrant point IDs.

The script reads every point payload from a live Qdrant collection, matches
questions to source documents and keywords, and writes actual Qdrant point IDs
into relevant_chunk_ids. It never fabricates chunk IDs.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from qdrant_client import QdrantClient
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pip install qdrant-client") from exc

DOC_KEYS = (
    "document_name",
    "document",
    "filename",
    "file_name",
    "source_file",
    "source",
    "title",
    "document_title",
)
TEXT_KEYS = ("text", "content", "page_content", "chunk_text", "body")
CHUNK_META_KEYS = ("chunk_id", "chunk_index", "page", "page_number", "section", "chapter")
TOKEN_RE = re.compile(r"[A-Za-z0-9_.:/+-]+|[\u4e00-\u9fff]+")


@dataclass(frozen=True)
class PointRecord:
    point_id: str
    payload: dict[str, Any]
    document: str
    text: str


def normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("\\", "/")
    text = re.sub(r"\s+", "", text)
    return text


def tokenize(text: str) -> list[str]:
    raw = TOKEN_RE.findall(str(text).lower())
    tokens: list[str] = []
    for token in raw:
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            tokens.extend(token[i : i + 2] for i in range(max(1, len(token) - 1)))
            tokens.append(token)
        else:
            tokens.append(token)
    return [t for t in tokens if t]


def payload_value(payload: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        for key in keys:
            value = metadata.get(key)
            if value not in (None, ""):
                return str(value)
    return ""


def iter_points(client: QdrantClient, collection: str, batch_size: int = 256) -> list[PointRecord]:
    records: list[PointRecord] = []
    offset: Any = None
    while True:
        points, next_offset = client.scroll(
            collection_name=collection,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = dict(point.payload or {})
            records.append(
                PointRecord(
                    point_id=str(point.id),
                    payload=payload,
                    document=payload_value(payload, DOC_KEYS),
                    text=payload_value(payload, TEXT_KEYS),
                )
            )
        if next_offset is None:
            break
        offset = next_offset
    return records


def document_score(expected: str, actual: str) -> float:
    e = normalize(expected)
    a = normalize(actual)
    if not e or not a:
        return 0.0
    e_base = e.rsplit("/", 1)[-1]
    a_base = a.rsplit("/", 1)[-1]
    if e == a or e_base == a_base:
        return 12.0
    if e_base in a_base or a_base in e_base:
        return 8.0
    e_stem = e_base.rsplit(".", 1)[0]
    a_stem = a_base.rsplit(".", 1)[0]
    if e_stem and (e_stem in a_stem or a_stem in e_stem):
        return 5.0
    return 0.0


def keyword_score(keywords: list[str], text: str, payload: dict[str, Any]) -> tuple[float, list[str]]:
    haystack = normalize(text + " " + json.dumps(payload, ensure_ascii=False, default=str))
    matched = [kw for kw in keywords if normalize(kw) and normalize(kw) in haystack]
    exact = sum(2.5 for _ in matched)
    q_tokens = Counter(tokenize(" ".join(keywords)))
    h_tokens = set(tokenize(haystack))
    token_hits = sum(weight for token, weight in q_tokens.items() if token in h_tokens)
    return exact + min(4.0, token_hits * 0.25), matched


def question_score(question: str, text: str) -> float:
    q_tokens = set(tokenize(question))
    t_tokens = set(tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens) / math.sqrt(len(q_tokens))
    return min(4.0, overlap)


def choose_collection(client: QdrantClient, questions: list[dict[str, Any]]) -> str:
    names = [item.name for item in client.get_collections().collections]
    if not names:
        raise RuntimeError("Qdrant contains no collections")

    best: tuple[float, str] | None = None

    for name in names:
        sample, _ = client.scroll(name, limit=200, with_payload=True, with_vectors=False)
        if not sample:
            continue

        # ---- 质量分：有真实文本payload的chunk占比 ----
        total = len(sample)
        has_text = sum(
            1 for p in sample
            if normalize(payload_value(dict(p.payload or {}), TEXT_KEYS))
        )
        text_ratio = has_text / max(total, 1)
        if text_ratio == 0:
            # 全是空payload，直接跳过
            continue

        score = text_ratio * 50.0  # 质量是最重要的指标

        # ---- 文档名匹配 ----
        docs = {normalize(payload_value(dict(p.payload or {}), DOC_KEYS)) for p in sample}
        expected_docs = {normalize(q.get("relevant_document")) for q in questions}
        score += sum(3.0 for expected in expected_docs for actual in docs
                     if expected and actual and (expected in actual or actual in expected))

        # ---- 内容关键词匹配 ----
        content_text = " ".join(
            normalize(payload_value(dict(p.payload or {}), TEXT_KEYS))
            for p in sample[:30]
        )
        keywords = set()
        for q in questions:
            keywords.update(q.get("relevant_keywords", []))
        score += sum(0.3 for kw in keywords if normalize(kw) in content_text)

        candidate = (score, name)
        if best is None or candidate > best:
            best = candidate

    if best is None:
        raise RuntimeError(
            "Could not identify the knowledge-base collection. "
            f"Available collections: {', '.join(names)}. Pass --collection explicitly."
        )
    print(f"  Auto-selected '{best[1]}' (score={best[0]:.1f})", file=sys.stderr)
    return best[1]


def point_metadata(record: PointRecord, score: float, matched_keywords: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "point_id": record.point_id,
        "document": record.document,
        "score": round(score, 4),
        "matched_keywords": matched_keywords,
    }
    for key in CHUNK_META_KEYS:
        value = record.payload.get(key)
        if value is None and isinstance(record.payload.get("metadata"), dict):
            value = record.payload["metadata"].get(key)
        if value is not None:
            result[key] = value
    return result


def resolve_question(question: dict[str, Any], points: list[PointRecord], top_k: int, min_score: float) -> tuple[list[str], list[dict[str, Any]]]:
    expected_doc = str(question.get("relevant_document", ""))
    keywords = [str(x) for x in question.get("relevant_keywords", []) if str(x).strip()]
    q_text = str(question.get("question", ""))
    ranked: list[tuple[float, PointRecord, list[str]]] = []
    for record in points:
        doc_s = document_score(expected_doc, record.document)
        kw_s, matched = keyword_score(keywords, record.text, record.payload)
        q_s = question_score(q_text, record.text)
        score = doc_s + kw_s + q_s
        # 不再硬性跳过文档名不匹配的chunk——当知识库未按章节拆文件时，
        # 文档名可能完全不同，此时仍依赖关键词+问题文本的语义匹配
        if score >= min_score:
            ranked.append((score, record, matched))
    ranked.sort(key=lambda item: (-item[0], item[1].point_id))
    selected = ranked[:top_k]
    return [item[1].point_id for item in selected], [point_metadata(item[1], item[0], item[2]) for item in selected]


def validate_resolved(questions: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    placeholder = re.compile(r"^(chunk_?0*\d+|todo|placeholder|__.*__)$", re.I)
    for q in questions:
        qid = q.get("question_id", "<unknown>")
        ids = q.get("relevant_chunk_ids")
        resolution = q.get("chunk_resolution", {})
        if not isinstance(ids, list) or not ids:
            # 空列表 = 知识库中找不到对应内容，允许（标记为unresolved）
            if resolution.get("status") == "unresolved":
                continue
            errors.append(f"{qid}: no relevant_chunk_ids resolved and not marked unresolved")
            continue
        for value in ids:
            if not isinstance(value, (str, int)) or not str(value).strip():
                errors.append(f"{qid}: invalid point ID {value!r}")
            elif placeholder.match(str(value).strip()):
                errors.append(f"{qid}: placeholder-like ID remains: {value}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None,
                        help="questions.json路径，默认为当前模块同级的questions.json")
    parser.add_argument("--output", help="Defaults to overwriting --input")
    parser.add_argument("--url", default="http://localhost:6333")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--collection", default=None,
                        help="Qdrant collection名。默认尝试读取 rag/config.py 中的 qdrant_collection，否则自动检测")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=5.0)
    parser.add_argument("--strict", action="store_true", help="Fail without writing if any question cannot be resolved")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        input_path = Path(__file__).parent / "questions.json"
    output_path = Path(args.output) if args.output else input_path
    questions = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(questions, list):
        raise SystemExit("questions.json root must be a JSON array")

    client = QdrantClient(url=args.url, api_key=args.api_key)
    if args.collection:
        collection = args.collection
    else:
        # 优先使用项目配置中的 collection，保证与 benchmark.py 一致
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
            from rag.config import settings
            configured = settings.qdrant_collection
            # 检查该 collection 是否存在且有数据
            cols = [c.name for c in client.get_collections().collections]
            if configured in cols:
                stats = client.get_collection(configured)
                if stats.points_count and stats.points_count > 0:
                    collection = configured
                    print(f"  Using configured collection '{collection}' from rag/config.py", file=sys.stderr)
                else:
                    print(f"  Configured collection '{configured}' is empty, auto-detecting...", file=sys.stderr)
                    collection = choose_collection(client, questions)
            else:
                print(f"  Configured collection '{configured}' not found, auto-detecting...", file=sys.stderr)
                collection = choose_collection(client, questions)
        except Exception:
            collection = choose_collection(client, questions)
    print(f"Using collection: {collection}", file=sys.stderr)
    points = iter_points(client, collection)
    print(f"Loaded {len(points)} points", file=sys.stderr)

    unresolved: list[str] = []
    for question in questions:
        ids, metadata = resolve_question(question, points, args.top_k, args.min_score)
        question["relevant_chunk_ids"] = ids
        question["resolved_chunk_metadata"] = metadata
        question["chunk_resolution"] = {
            "collection": collection,
            "identifier_type": "qdrant_point_id",
            "status": "resolved" if ids else "unresolved",
        }
        if not ids:
            unresolved.append(str(question.get("question_id", "<unknown>")))

    errors = validate_resolved(questions)
    if args.strict and errors:
        print("Resolution failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resolved_count = sum(1 for q in questions if q.get("chunk_resolution", {}).get("status") == "resolved")
    unresolved_count = sum(1 for q in questions if q.get("chunk_resolution", {}).get("status") == "unresolved")
    print(f"Wrote {output_path}", file=sys.stderr)
    print(f"Resolved: {resolved_count} questions, Unresolved (KB has no matching content): {unresolved_count} questions", file=sys.stderr)
    if unresolved:
        print(f"Unresolved: {', '.join(unresolved)}", file=sys.stderr)
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
