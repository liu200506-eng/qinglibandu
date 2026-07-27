# Embedding模型选型实验报告

> 状态：**待填充**。请先运行 `fill_real_chunk_ids.py` 回填真实 Qdrant point ID，再运行 `benchmark.py` 获取真实数据。

快速流程：
```bash
cd backend
# 步骤1: 回填真实point ID（需Qdrant运行中）
python -m tests.embedding_benchmark.fill_real_chunk_ids --url http://localhost:6333 --strict

# 步骤2: 运行3个模型的评测
python -m tests.embedding_benchmark.benchmark --models bge-base-zh m3e-base text2vec --repeat 3
```

## 1. 实验目的

横向对比不同中文 Embedding 模型在本项目知识库下的检索效果与本地部署成本，为模型选型提供真实数据支撑，避免凭直觉或社区口碑做选择。

## 2. 实验环境

| 项目 | 值 |
|---|---|
| CPU | 待填 |
| GPU | 待填 |
| 内存 | 待填 |
| Python | 待填（由脚本自动写入 `_meta.python`） |
| Qdrant 版本 | 待填 |
| Qdrant 模式 | 待填（`local` / `server`） |
| 实验时间 | 待填（由脚本自动写入 `_meta.timestamp`） |

## 3. 数据集

| 项目 | 值 |
|---|---|
| 源文档数量 | 待填 |
| 文本块（chunk）总数 | 待填（由脚本写入 `chunk_count`） |
| 测试问题数量 | 40 道（eq001—eq040） |
| 标注方式 | 先用 `fill_real_chunk_ids.py` 从运行中的 Qdrant 自动匹配真实 point ID，再人工复核；未回填时退化到 `relevant_keywords` 软匹配 |
| 问题覆盖类型 | 精确关键词 / 同义改写 / 专业术语 / 跨段落 / 容易混淆 |

## 4. 固定参数（控制变量）

| 参数 | 值 |
|---|---|
| Chunk Size | `settings.chunk_size`（默认 1024） |
| Chunk Overlap | `settings.chunk_overlap`（默认 128） |
| Top-K | 10 |
| Distance | Cosine |
| Reranker | **关闭**（仅评测 Embedding 检索能力） |
| 大模型回答 | **不进入**（避免 RAGAS/Prompt 干扰） |
| BM25 | **不参与**（仅向量检索） |

## 5. 候选模型

| 简称 | 完整名称 | 维度 | 说明 |
|---|---|---|---|
| bge-base-zh | BAAI/bge-base-zh-v1.5 | 768 | 当前基线 |
| m3e-base | moka-ai/m3e-base | 768 | Moka AI 中文向量 |
| text2vec | shibing624/text2vec-base-chinese | 768 | text2vec 中文基础 |
| bge-m3 | BAAI/bge-m3 | 1024 | 多语言大模型（可选） |

## 6. 实验结果

> 待 `results.json` 生成后填入下表。

| 模型 | 维度 | Hit@1 | Hit@3 | Recall@5 | MRR | 编码耗时/ms | 检索耗时/ms | 模型加载峰值内存/MB |
|---|---|---|---|---|---|---|---|---|
| bge-base-zh-v1.5 | 768 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |
| m3e-base | 768 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |
| text2vec-base-chinese | 768 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |
| bge-m3 | 1024 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |

## 7. 选型结论

待填。请基于真实结果撰写，例如：

> 在 N 道测试问题上，bge-base-zh-v1.5 的 Hit@3 达到 XX%，MRR 为 X.XX，平均编码耗时 XX ms。综合检索效果与本地部署资源占用，选用 BAAI/bge-base-zh-v1.5 作为项目默认 Embedding 模型。
