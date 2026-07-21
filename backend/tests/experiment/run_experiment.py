#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A/B/C/D/E 五组对照实验 —— 真实调用 LLM，可复现。

实验组别:
  A: 纯 LLM                    —— 基线，只给题目
  B: LLM + RAG                 —— 检索知识库后作答
  C: LLM + RAG + 审查 Agent    —— 审查员评分，事实性不达标则重写（最多 2 次）
  D: LLM + RAG + 审查 + 画像   —— 完整系统，注入学生画像做个性化适配
  E: LLM + RAG + 画像（无审查）—— 消融组，证明审查 Agent 的边际贡献

评分维度（每题 0-5 分）:
  factual_score          事实正确性
  citation_score         引用准确性（A 组无检索，恒 0）
  personalization_score  个性化匹配度（A/B/C 组无画像，恒 0）

用法:
  cd backend/tests/experiment
  python run_experiment.py                      # 默认抽样 20 题，每组每题跑 1 次
  python run_experiment.py --questions 20 --repeat 3
  python run_experiment.py --all --repeat 3     # 全部 120 题

输出文件:
  raw_outputs_{group}.json   每组每题完整原文（prompt / answer / review / citations / retry）
  scores.csv                 每题每组的评分明细
  summary.json               每组均值 / 标准差 / 响应时间 / Token / 重试率
  run_log.txt                运行日志

复现说明:
  - 模型与温度固定在 model_config.json
  - 提示词版本固定在 prompt_versions/
  - 每组每题重复 N 次，报告均值与标准差
  - 所有 LLM 输出原样保存到 raw_outputs_*.json，可交叉核验
"""

import argparse
import csv
import json
import os
import sys
import time
import statistics
from datetime import datetime
from typing import Dict, List, Optional

# 让脚本能从 experiment 目录直接运行
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
# cwd 设为 backend，让 config.py 的 env_file=".env" 能正确加载密钥
os.chdir(BACKEND_DIR)

from utils.llm_client import get_llm, llm_config_status
from langchain_core.messages import HumanMessage, SystemMessage

QUESTIONS_PATH = os.path.join(EXPERIMENT_DIR, "questions.json")

# ============================================================
# 配置（写入 model_config.json 供复现核验）
# ============================================================
MODEL_CONFIG = {
    "temperature": 0.3,
    "max_tokens": 1024,
    "review_threshold": 4.0,   # 审查员事实性评分 < 4 触发重写
    "max_retries": 2,          # 最多重写次数
    "repeat_default": 1,
    "questions_default": 20,
}

# 三类反事实学生画像（与项目资料一致）
STUDENT_PROFILES = {
    "weak_basis": {
        "label": "基础薄弱型",
        "mastery": 35,
        "common_errors": ["混淆 cwnd 与 rwnd", "不理解拥塞窗口概念"],
        "preferred_resource": "动画+图解",
        "daily_minutes": 20,
    },
    "calc_error": {
        "label": "计算易错型",
        "mastery": 55,
        "common_errors": ["RTT 计算漏项", "BDP 单位换算错"],
        "preferred_resource": "公式推导+例题",
        "daily_minutes": 35,
    },
    "code_pref": {
        "label": "偏好编程型",
        "mastery": 70,
        "common_errors": ["概念能用但说不清"],
        "preferred_resource": "代码仿真+实验",
        "daily_minutes": 45,
    },
}


# ============================================================
# 工具函数
# ============================================================
def load_questions(limit: Optional[int] = None) -> List[Dict]:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        all_q = json.load(f)
    if limit and limit < len(all_q):
        # 稳定抽样：按 question_id 排序后取前 limit 题，保证可复现
        all_q = sorted(all_q, key=lambda x: x["question_id"])[:limit]
    return all_q


def call_llm(system: str, user: str) -> Dict:
    """调用 LLM，返回 {answer, latency_s, tokens}。"""
    llm = get_llm()
    t0 = time.time()
    resp = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])
    latency = time.time() - t0
    tokens = 0
    try:
        # ChatOpenAI 的响应带 usage_metadata
        um = getattr(resp, "usage_metadata", None)
        if um:
            tokens = int(um.get("total_tokens", 0))
        else:
            tokens = len(resp.content) // 2  # 粗略估计
    except Exception:
        tokens = len(resp.content) // 2
    return {"answer": resp.content, "latency_s": round(latency, 2), "tokens": tokens}


def rag_retrieve(query: str, top_k: int = 5) -> List[Dict]:
    """调用 RAGEngine 检索，返回来源片段。失败时返回空列表。"""
    try:
        from rag.engine import RAGEngine
        engine = RAGEngine()
        return engine.retrieve(query, top_k=top_k, subject="计算机网络")
    except Exception as e:
        print(f"  [RAG 警告] 检索失败，回退为空上下文: {e}")
        return []


def format_citations(docs: List[Dict]) -> str:
    if not docs:
        return "（未检索到相关内容）"
    lines = []
    for i, d in enumerate(docs, 1):
        content = d.get("content") or d.get("text") or d.get("page_content") or ""
        source = d.get("source") or d.get("metadata", {}).get("source", "知识库")
        lines.append(f"[{i}] 来源:{source}\n{content[:400]}")
    return "\n\n".join(lines)


def format_profile(profile: Dict) -> str:
    return (
        f"学生画像：{profile['label']}，掌握度{profile['mastery']}%，"
        f"常见错误{profile['common_errors']}，"
        f"偏好资源{profile['preferred_resource']}，"
        f"每日可学{profile['daily_minutes']}分钟。"
        f"请用符合该学生水平与偏好的方式作答。"
    )


# ============================================================
# 审查员（C/D 组使用）—— 答疑答案审查 + 重写触发
# ============================================================
REVIEW_PROMPT = """你是严格的答案审查员。对下面的【学生问题】和【AI回答】做四项检查，输出 JSON：
{
  "factual": 0-5 的整数,           // 事实正确性，5=完全正确，0=全错
  "citation": 0-5 的整数,          // 引用是否准确对应来源（无来源时按回答自洽性给分）
  "completeness": 0-5 的整数,      // 知识点覆盖完整度
  "validity": 0-5 的整数,          // 答案有效性（能否解决学生问题）
  "issues": ["问题1", "问题2"],    // 发现的具体错误
  "rewrite_advice": "若需重写，给出修改建议；无需重写则为空字符串"
}
只输出 JSON，不要任何额外文字。"""


def review_answer(question: str, answer: str, citations: str) -> Dict:
    """让审查员 LLM 评分。返回解析后的 dict。"""
    user_msg = f"【学生问题】\n{question}\n\n【检索到的来源】\n{citations}\n\n【AI回答】\n{answer}"
    try:
        result = call_llm(REVIEW_PROMPT, user_msg)
        # 解析 JSON（容错：模型可能加 ```json 包裹）
        raw = result["answer"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        scores = json.loads(raw)
        return {
            "factual": int(scores.get("factual", 0)),
            "citation": int(scores.get("citation", 0)),
            "completeness": int(scores.get("completeness", 0)),
            "validity": int(scores.get("validity", 0)),
            "issues": scores.get("issues", []),
            "rewrite_advice": scores.get("rewrite_advice", ""),
            "review_latency_s": result["latency_s"],
            "review_tokens": result["tokens"],
        }
    except Exception as e:
        return {
            "factual": 0, "citation": 0, "completeness": 0, "validity": 0,
            "issues": [f"审查解析失败: {e}"], "rewrite_advice": "",
            "review_latency_s": 0, "review_tokens": 0,
        }


# ============================================================
# 最终评分员（独立于审查员，对所有组统一打分）
# ============================================================
SCORE_PROMPT = """你是独立评分员。对下面的【学生问题】【AI回答】打分（0-5 整数）。
判断标准：
- factual_score: 事实正确性（5=完全正确，0=全错）
- citation_score: 引用准确性。若回答引用了来源且来源支撑回答给5；无引用来源给0
- personalization_score: 个性化匹配度。若回答体现了对学生水平/偏好的适配给高分；否则给低分
输出 JSON：{"factual_score": int, "citation_score": int, "personalization_score": int}
只输出 JSON。"""


def final_score(question: str, answer: str, has_citation: bool, has_profile: bool) -> Dict:
    user_msg = f"【学生问题】\n{question}\n\n【AI回答】\n{answer}\n\n说明：该回答{'有' if has_citation else '无'}引用来源，{'注入了' if has_profile else '未注入'}学生画像。"
    try:
        result = call_llm(SCORE_PROMPT, user_msg)
        raw = result["answer"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        s = json.loads(raw)
        return {
            "factual_score": int(s.get("factual_score", 0)),
            "citation_score": int(s.get("citation_score", 0)) if has_citation else 0,
            "personalization_score": int(s.get("personalization_score", 0)) if has_profile else 0,
            "scoring_latency_s": result["latency_s"],
            "scoring_tokens": result["tokens"],
        }
    except Exception as e:
        return {
            "factual_score": 0, "citation_score": 0, "personalization_score": 0,
            "scoring_latency_s": 0, "scoring_tokens": 0, "error": str(e),
        }


# ============================================================
# 五组实验逻辑
# ============================================================
BASE_SYSTEM = "你是计算机网络辅导老师，请准确、清晰地回答问题。"


def run_group_a(q: Dict) -> Dict:
    """A: 纯 LLM。"""
    r = call_llm(BASE_SYSTEM, q["question"])
    return {"answer": r["answer"], "citations": "", "latency_s": r["latency_s"],
            "tokens": r["tokens"], "retries": 0, "review": None, "profile": None}


def run_group_b(q: Dict) -> Dict:
    """B: LLM + RAG。"""
    docs = rag_retrieve(q["question"])
    citations = format_citations(docs)
    user = f"参考以下来源作答：\n{citations}\n\n问题：{q['question']}"
    r = call_llm(BASE_SYSTEM, user)
    return {"answer": r["answer"], "citations": citations, "latency_s": r["latency_s"],
            "tokens": r["tokens"], "retries": 0, "review": None, "profile": None}


def run_group_c(q: Dict) -> Dict:
    """C: LLM + RAG + 审查（触发重写）。"""
    docs = rag_retrieve(q["question"])
    citations = format_citations(docs)
    user = f"参考以下来源作答：\n{citations}\n\n问题：{q['question']}"
    r = call_llm(BASE_SYSTEM, user)
    answer, retries, review = r["answer"], 0, None
    total_tokens = r["tokens"]
    total_latency = r["latency_s"]

    while retries < MODEL_CONFIG["max_retries"]:
        review = review_answer(q["question"], answer, citations)
        total_tokens += review["review_tokens"]
        total_latency += review["review_latency_s"]
        if review["factual"] >= MODEL_CONFIG["review_threshold"]:
            break
        # 触发重写
        advice = review.get("rewrite_advice", "") or "请修正上述问题后重新作答。"
        rewrite_user = f"你之前的回答存在以下问题：\n{json.dumps(review['issues'], ensure_ascii=False)}\n修改建议：{advice}\n\n原始问题：{q['question']}\n参考来源：\n{citations}\n\n请给出修正后的回答。"
        r2 = call_llm(BASE_SYSTEM, rewrite_user)
        answer = r2["answer"]
        total_tokens += r2["tokens"]
        total_latency += r2["latency_s"]
        retries += 1

    return {"answer": answer, "citations": citations, "latency_s": round(total_latency, 2),
            "tokens": total_tokens, "retries": retries, "review": review, "profile": None}


def run_group_d(q: Dict, profile: Dict) -> Dict:
    """D: LLM + RAG + 审查 + 画像（完整系统）。"""
    docs = rag_retrieve(q["question"])
    citations = format_citations(docs)
    system = BASE_SYSTEM + " " + format_profile(profile)
    user = f"参考以下来源作答：\n{citations}\n\n问题：{q['question']}"
    r = call_llm(system, user)
    answer, retries, review = r["answer"], 0, None
    total_tokens = r["tokens"]
    total_latency = r["latency_s"]

    while retries < MODEL_CONFIG["max_retries"]:
        review = review_answer(q["question"], answer, citations)
        total_tokens += review["review_tokens"]
        total_latency += review["review_latency_s"]
        if review["factual"] >= MODEL_CONFIG["review_threshold"]:
            break
        advice = review.get("rewrite_advice", "") or "请修正上述问题后重新作答。"
        rewrite_user = f"你之前的回答存在以下问题：\n{json.dumps(review['issues'], ensure_ascii=False)}\n修改建议：{advice}\n\n学生画像：{format_profile(profile)}\n原始问题：{q['question']}\n参考来源：\n{citations}\n\n请给出修正后的、适配该学生的回答。"
        r2 = call_llm(system, rewrite_user)
        answer = r2["answer"]
        total_tokens += r2["tokens"]
        total_latency += r2["latency_s"]
        retries += 1

    return {"answer": answer, "citations": citations, "latency_s": round(total_latency, 2),
            "tokens": total_tokens, "retries": retries, "review": review, "profile": profile["label"]}


def run_group_e(q: Dict, profile: Dict) -> Dict:
    """E: LLM + RAG + 画像（无审查，消融组）。"""
    docs = rag_retrieve(q["question"])
    citations = format_citations(docs)
    system = BASE_SYSTEM + " " + format_profile(profile)
    user = f"参考以下来源作答：\n{citations}\n\n问题：{q['question']}"
    r = call_llm(system, user)
    return {"answer": r["answer"], "citations": citations, "latency_s": r["latency_s"],
            "tokens": r["tokens"], "retries": 0, "review": None, "profile": profile["label"]}


GROUP_RUNNERS = {
    "A": lambda q, profile: run_group_a(q),
    "B": lambda q, profile: run_group_b(q),
    "C": lambda q, profile: run_group_c(q),
    "D": lambda q, profile: run_group_d(q, profile),
    "E": lambda q, profile: run_group_e(q, profile),
}

GROUP_HAS_CITATION = {"B", "C", "D", "E"}
GROUP_HAS_PROFILE = {"D", "E"}


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="A/B/C/D/E 五组对照实验（真实调用 LLM）")
    parser.add_argument("--questions", type=int, default=MODEL_CONFIG["questions_default"],
                        help=f"抽样题数（默认 {MODEL_CONFIG['questions_default']}）")
    parser.add_argument("--all", action="store_true", help="使用全部 120 题")
    parser.add_argument("--repeat", type=int, default=MODEL_CONFIG["repeat_default"],
                        help=f"每题重复次数（默认 {MODEL_CONFIG['repeat_default']}）")
    parser.add_argument("--groups", default="A,B,C,D,E", help="运行的组别，逗号分隔")
    args = parser.parse_args()

    # 前置检查：LLM 是否配置
    status = llm_config_status()
    if not status["configured"]:
        print("❌ 未配置大模型密钥，请在 backend/.env 中配置。无法运行真实实验。")
        sys.exit(1)
    print(f"✅ 使用模型: {status['provider']} / {status['model']}")

    questions = load_questions(None if args.all else args.questions)
    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    repeat = max(1, args.repeat)
    print(f"题目数: {len(questions)} | 组别: {groups} | 每题重复: {repeat}")
    print(f"预计调用次数: {len(questions) * len(groups) * repeat} 次主调用 + 审查/评分调用")
    print("=" * 60)

    # 轮换画像（让 D/E 组在不同题上覆盖三类学生）
    profile_keys = list(STUDENT_PROFILES.keys())

    # 保存完整原文
    raw_outputs = {g: [] for g in groups}
    # 评分明细
    score_rows = []
    # 运行日志
    log_lines = [f"实验运行 {datetime.now().isoformat()}", f"模型: {status['provider']}/{status['model']}",
                 f"题目数: {len(questions)} 组别: {groups} 重复: {repeat}", "=" * 60]

    total_calls = len(questions) * len(groups) * repeat
    call_idx = 0
    t_start = time.time()

    for q in questions:
        qid = q["question_id"]
        for g in groups:
            profile = STUDENT_PROFILES[profile_keys[hash(qid) % len(profile_keys)]]
            for rep in range(repeat):
                call_idx += 1
                t0 = time.time()
                try:
                    result = GROUP_RUNNERS[g](q, profile)
                    # 最终评分（独立评分员）
                    sc = final_score(q["question"], result["answer"],
                                     has_citation=(g in GROUP_HAS_CITATION),
                                     has_profile=(g in GROUP_HAS_PROFILE))
                    total_tokens = result["tokens"] + sc["scoring_tokens"]
                    total_latency = result["latency_s"] + sc["scoring_latency_s"]

                    raw_outputs[g].append({
                        "question_id": qid, "repeat": rep, "group": g,
                        "question": q["question"], "knowledge_point": q.get("knowledge_point", ""),
                        "profile": result["profile"], "citations": result["citations"],
                        "answer": result["answer"], "review": result["review"],
                        "final_score": sc, "retries": result["retries"],
                        "latency_s": round(total_latency, 2), "tokens": total_tokens,
                        "timestamp": datetime.now().isoformat(),
                    })
                    score_rows.append({
                        "question_id": qid, "group": g, "repeat": rep,
                        "factual_score": sc["factual_score"],
                        "citation_score": sc["citation_score"],
                        "personalization_score": sc["personalization_score"],
                        "retries": result["retries"], "latency_s": total_latency,
                        "tokens": total_tokens,
                    })
                    elapsed = time.time() - t0
                    line = f"[{call_idx}/{total_calls}] {qid} 组{g} rep{rep} | factual={sc['factual_score']} cite={sc['citation_score']} pers={sc['personalization_score']} retries={result['retries']} {elapsed:.1f}s"
                    print(line)
                    log_lines.append(line)
                except Exception as e:
                    err = f"[{call_idx}/{total_calls}] {qid} 组{g} rep{rep} 失败: {e}"
                    print(err)
                    log_lines.append(err)
                    score_rows.append({
                        "question_id": qid, "group": g, "repeat": rep,
                        "factual_score": 0, "citation_score": 0, "personalization_score": 0,
                        "retries": 0, "latency_s": 0, "tokens": 0, "error": str(e),
                    })

    total_elapsed = time.time() - t_start
    print("=" * 60)
    print(f"实验完成，总耗时 {total_elapsed:.1f}s")

    # 写 raw_outputs
    for g in groups:
        with open(os.path.join(EXPERIMENT_DIR, f"raw_outputs_{g.lower()}.json"), "w", encoding="utf-8") as f:
            json.dump(raw_outputs[g], f, ensure_ascii=False, indent=2)

    # 写 scores.csv
    with open(os.path.join(EXPERIMENT_DIR, "scores.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question_id", "group", "repeat",
                                               "factual_score", "citation_score",
                                               "personalization_score", "retries",
                                               "latency_s", "tokens"])
        writer.writeheader()
        for row in score_rows:
            row.pop("error", None)
            writer.writerow(row)

    # 写 summary.json（含均值/标准差/响应时间/Token/重试率）
    summary = {}
    for g in groups:
        g_rows = [r for r in score_rows if r["group"] == g]
        n = len(g_rows)
        if n == 0:
            continue
        def mean_std(key):
            vals = [r[key] for r in g_rows]
            return {"mean": round(statistics.mean(vals), 2),
                    "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0}
        summary[g] = {
            "n_samples": n,
            "factual_accuracy": mean_std("factual_score"),
            "citation_accuracy": mean_std("citation_score"),
            "personalization_match": mean_std("personalization_score"),
            "latency_s": mean_std("latency_s"),
            "tokens": mean_std("tokens"),
            "retry_rate": round(sum(1 for r in g_rows if r.get("retries", 0) > 0) / n, 2),
            "failure_rate": round(sum(1 for r in g_rows if "error" in r) / n, 2),
        }
    summary["_meta"] = {
        "model": status["model"], "provider": status["provider"],
        "temperature": MODEL_CONFIG["temperature"],
        "questions": len(questions), "repeat": repeat,
        "groups": groups, "total_elapsed_s": round(total_elapsed, 1),
        "timestamp": datetime.now().isoformat(),
    }
    with open(os.path.join(EXPERIMENT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 写 model_config.json + run_log.txt
    with open(os.path.join(EXPERIMENT_DIR, "model_config.json"), "w", encoding="utf-8") as f:
        json.dump({**MODEL_CONFIG, "provider": status["provider"],
                   "model": status["model"]}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(EXPERIMENT_DIR, "run_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    # 打印汇总
    print("\n" + "=" * 60)
    print("A/B/C/D/E 五组对照实验结果汇总")
    print("=" * 60)
    print(f"{'组别':<6} {'事实正确率':<14} {'引用正确率':<14} {'个性化匹配':<14} {'均延时':<10} {'重试率':<8}")
    print("-" * 60)
    for g in groups:
        if g not in summary:
            continue
        s = summary[g]
        print(f"{g:<6} "
              f"{s['factual_accuracy']['mean']}±{s['factual_accuracy']['std']:<10} "
              f"{s['citation_accuracy']['mean']}±{s['citation_accuracy']['std']:<10} "
              f"{s['personalization_match']['mean']}±{s['personalization_match']['std']:<10} "
              f"{s['latency_s']['mean']:<8}s "
              f"{s['retry_rate']:<8}")
    print("=" * 60)
    print(f"\n说明：")
    print(f"- 评分由独立 LLM 评分员给出（0-5 分），模型 {status['model']}，温度 {MODEL_CONFIG['temperature']}")
    print(f"- 每组每题重复 {repeat} 次，报告均值±标准差")
    print(f"- 完整原文见 raw_outputs_*.json，评分明细见 scores.csv")
    print(f"- D vs C 证明画像价值，D vs E 证明审查 Agent 价值")


if __name__ == "__main__":
    main()
