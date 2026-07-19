# Release Notes - v1.0.3-contest-final

## 📋 版本信息

- **版本号**: v1.0.3-contest-final
- **Commit Hash**: `0239a6a`
- **发布日期**: 2026-07-17
- **项目状态**: 参赛封版状态

## 🎯 项目简介

青藜伴读（MagicStudy）是一款面向高校课程学习场景的AI智能学习决策与陪练系统，基于动态学习画像、多智能体协同、RAG知识库和多模态资源生成，构建个性化学习决策与陪练系统。

**核心竞争力**：动态学习画像 → 多智能体决策 → RAG证据检索 → 审查核验 → 个性化学习资源 → 练习反馈

## ✨ 本次更新内容

### 新增特性
- 三种学生画像类型（基础薄弱型、易混淆型、偏好实践型）
- SVG格式思维导图生成
- 完整学习闭环流程文档
- 实验评分标准量化体系

### 修复问题
- 修正实验结论（C/D组事实正确率均为90%）
- 删除未经证明的性能指标
- 清理历史提交中的HTML文件
- 降低宣传性词语表述

## 🔧 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 后端运行环境 |
| Node.js | 18+ | 前端运行环境 |
| Docker | 20+ | 运行Qdrant向量数据库 |
| Git | 2+ | 版本控制 |

## 🚀 启动方式

### Docker Compose一键部署（推荐）

```bash
git clone https://gitee.com/ghosts-in-a-dying-state/a3.git
cd a3
docker-compose up -d
```

服务地址：
- 前端：http://localhost:5175
- 后端：http://localhost:8001
- Qdrant管理界面：http://localhost:6333/dashboard

### 手动启动

```bash
# 1. 启动Qdrant
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.7.0

# 2. 后端
cd backend
pip install -r requirements.txt
python run_seed.py
python main.py

# 3. 前端
cd frontend
npm install
npm run dev
```

## 🔑 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 学生 | student1 | magicstudy |
| 学生 | student2 | magicstudy |
| 管理员 | admin | magicstudy |

## ⚙️ 环境变量配置

复制 `backend/.env.example` 为 `backend/.env`，配置以下关键参数：

```env
# LLM配置（必填）
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# 讯飞TTS/ASR（可选）
XFYUN_TTS_APP_ID=your_app_id
XFYUN_TTS_API_KEY=your_api_key
XFYUN_TTS_API_SECRET=your_api_secret
```

## 📊 实验结果摘要

### A/B/C/D四组对照实验

| 组别 | 模式 | 事实正确率 | 引用正确率 | 个性化匹配度 |
|------|------|------------|------------|--------------|
| A组 | LLM | 70% | 0% | 30% |
| B组 | LLM + RAG | 80% | 70% | 40% |
| C组 | LLM + RAG + 审查 | 90% | 80% | 40% |
| D组 | 完整系统 | 90% | 80% | 80% |

### 实验结论
- 审查机制主要改善事实可靠性
- 学习画像主要改善个性化适配效果

## 📁 项目结构

```
A3/
├── backend/           # 后端服务
│   ├── api/          # API路由
│   ├── agents/       # 多智能体
│   ├── engines/      # 核心引擎（画像、资源生成）
│   ├── graph/        # LangGraph工作流
│   ├── knowledge_base/computer_network/  # 知识库
│   └── tests/experiment/  # 实验数据
├── frontend/         # 前端应用
│   └── src/          # 源代码
├── docker-compose.yml
└── README.md
```

## ⚠️ 已知限制

1. 需要配置LLM API密钥才能正常运行
2. 当前仅完成计算机网络课程的深度示范
3. 实验数据基于20道题小样本验证
4. 首次运行需要下载预训练模型

## 📝 测试命令

```bash
# 运行后端测试
cd backend
python -m pytest tests/ -v

# 运行实验脚本
python backend/tests/experiment/run_experiment.py
```

## 📌 关键文件说明

| 文件 | 说明 |
|------|------|
| `backend/tests/experiment/questions.json` | 20道测试题目 |
| `backend/tests/experiment/scoring_rubric.json` | 评分标准 |
| `backend/tests/experiment/scores.csv` | 评分结果 |
| `backend/tests/experiment/summary.json` | 实验汇总数据 |
| `backend/knowledge_base/computer_network/` | 计算机网络知识库 |

## 📞 联系方式

- 项目地址：https://gitee.com/ghosts-in-a-dying-state/a3
- 技术文档：README.md
- 演示视频：待上传

---

*本项目为软件杯A3赛道参赛作品*
