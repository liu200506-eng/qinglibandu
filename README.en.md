# MagicStudy - AI-Powered Learning Companion

<div align="center">

![MagicStudy](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=A%20modern%20AI%20education%20platform%20logo%20with%20book%20and%20light%20bulb%20icon%2C%20blue%20and%20gold%20gradient%2C%20clean%20minimalist%20design&image_size=square)

**AI Intelligent Learning Decision and Coaching System**

An AI-powered learning assistant for high school and university students, forming a complete personalized learning loop through learning state modeling, strategy decision-making, intelligent tutoring, and feedback mechanisms.

</div>

---

## 📖 Project Overview

**MagicStudy** is an AI-powered intelligent learning assistance system designed to provide personalized, intelligent learning experiences for students. The system name derives from the ancient Chinese idiom "Qing Li Zhao Du" (青藜照读), symbolizing academic diligence with lamp-light, representing companionship for students on their knowledge-seeking journey.

### ✨ Core Values

- **Personalized Learning**: Customized learning paths based on learning state modeling
- **Intelligent Decision**: Multi-Agent collaborative decision engine for personalized strategy recommendations
- **Knowledge Enhancement**: RAG knowledge base supporting multi-modal document parsing and retrieval-augmented Q&A
- **Full-Cycle Coverage**: Complete learning loop from knowledge learning, practice consolidation to exam assessment
- **Multi-modal Resources**: AI-generated PPT, mind maps, code practice, extended reading, video scripts + TTS voice
- **Streamed Output**: Real-time progress feedback for batch knowledge base filling

---

## 🎯 Core Features

### 🧠 AI Decision Engine

- **Multi-Agent Collaboration**: LangGraph-based multi-Agent decision workflow
- **Execution Trace Visualization**: Real-time display of Agent nodes, input/output summaries, tool calls, retrieval sources, execution time, and review status
- **Adaptive Strategy**: Dynamically adjust recommendation strategies based on learning state
- **Mode Switching**: Direct explanation, Socratic questioning, and other tutoring modes

### 📊 Dynamic Learning Profile

- **4-Dimensional Interpretable Profile**: Mastery (question accuracy, knowledge point coverage), learning speed (answer time, task completion time), error stability (repeated errors), learning persistence (frequency, intervals, completion rate)
- **Visualization**: Knowledge radar chart, learning growth curve, weekly heatmap
- **Real-time Tracking**: Record learning trajectories and analyze learning habits
- **Intelligent Evaluation**: Automatically evaluate learning outcomes and generate improvement suggestions

### 📚 Knowledge System

- **Core Demonstration Course**: Computer Networks
- **Course Extensibility**: Architecture supports expansion to other subjects
- **Three-level Hierarchy**: Chapter → Section → Knowledge Point structure
- **Personalized Knowledge Notes**: AI-generated detailed explanations
- **Graded Questions**: Progressive difficulty exercise system

### 💬 Intelligent Tutoring

- **Dual-mode Q&A**: Direct explanation / Socratic guided questioning
- **Error Diagnosis**: Analyze error causes and provide targeted reinforcement training
- **Learning Planning**: Intelligent generation of study plans and task timelines
- **Voice Interaction**: ASR voice input and TTS voice broadcast

### 📁 RAG Knowledge Base

- **Multi-modal Parsing**: PDF, Word, image (OCR), text formats
- **Dual-path Retrieval**: BM25 keyword + dense vector similarity search
- **Rerank Optimization**: bge-reranker-base Chinese reranking model
- **Incremental Update**: File hash-based detection for efficient sync
- **Vector Storage**: Qdrant service architecture
- **Anti-Hallucination**: Document name and chapter positioning display; explicit refusal below similarity threshold; reviewer agent verification

### 🎤 Voice Features

- **Text-to-Speech (TTS)**: Edge TTS (default, free), general TTS service (backup, requires API)
- **Speech-to-Text (ASR)**: Web Speech API (default, browser built-in), general ASR service (backup)
- **Chinese-English Mixed**: Support for mixed language recognition and synthesis

### 🔒 Knowledge Base Governance & Secure Publishing

- **Hierarchical Validation Strategy**: Different validation standards based on course status (draft/demo_only/review/published/archived)
  - `draft`: Relaxed validation, allows missing fields
  - `demo_only`: Basic validation, allows some warnings
  - `review`: Strict validation, warnings acceptable
  - `published`: Mandatory blocking - ERROR for <100% source coverage, <100% review pass rate, insufficient knowledge coverage
  - `archived`: Only basic structure validation
- **Source Traceability**: Questions, error patterns, and notes must link to source_ids verified in sources.json
- **Human Review Workflow**: `review` subcommand with list/approve/reject operations; author/reviewer/publisher role separation
- **Blue-Green Deployment**: Atomic publishing via Qdrant alias mechanism; staging collection creation, atomic alias switching, rollback, and cleanup
- **Failure Injection Testing**: before_alias_swap and after_database_write injection points to verify rollback
- **Automated Testing**: 45 tests all passed (15 integration + 18 toolchain + 12 business)

### 📝 Exam System

- **Paper Generation**: AI auto-generated mock exams
- **Online Testing**: Multiple choice, true/false, fill-in-the-blank, essay questions
- **Auto Grading**: Objective questions auto-graded, subjective questions AI-assisted
- **Score Analysis**: Detailed answer analysis and knowledge mastery

### 📚 Error Notebook

- **Auto Collection**: Errors automatically collected
- **Categorization**: By knowledge point, error type
- **Reinforcement Training**: Targeted practice for errors
- **Statistical Analysis**: Error rate statistics and improvement suggestions

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MagicStudy AI Learning Companion             │
│                         Frontend Presentation Layer             │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Knowledge    │ Learning     │ Intelligent  │ RAG Knowledge     │
│ Practice     │ Profile      │ Tutoring     │ Base              │
├──────────────┴──────────────┴──────────────┴───────────────────┤
│                         Backend Service Layer                   │
│  FastAPI + LangGraph + SentenceTransformers                    │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Learning     │ AI Decision  │ RAG Engine   │ Voice Service     │
│ State Model  │ Engine       │              │ (TTS/ASR)        │
├──────────────┴──────────────┴──────────────┴───────────────────┤
│                         Data Storage Layer                      │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│   SQLite     │   Qdrant     │   LLM API    │   File Storage    │
│ (Business)   │ (Vector)     │ (LLM)        │ (Documents)       │
└──────────────┴──────────────┴──────────────┴───────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend

| Technology | Version | Description |
|------------|---------|-------------|
| Vue | 3.x | Progressive frontend framework |
| TypeScript | 5.x | Type-safe JavaScript |
| Vite | 6.x | Fast build tool |
| Pinia | 2.x | State management |
| Element Plus | 2.x | Enterprise UI components |
| Vue Router | 4.x | Routing |

### Backend

| Technology | Version | Description |
|------------|---------|-------------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.110+ | High-performance async framework |
| SQLAlchemy | 2.x | ORM framework |
| Pydantic | 2.x | Data validation |
| LangGraph | 0.1+ | AI Agent framework |
| LangChain | 0.1+ | LLM application framework |
| SentenceTransformers | 3.x | Embedding models |
| Qdrant | 1.7+ | Vector database |

### AI Models

| Model Type | Model Name | Description |
|------------|------------|-------------|
| Embedding | BAAI/bge-base-zh | Chinese semantic encoding, 768-dim |
| Rerank | BAAI/bge-reranker-base | Chinese reranking model |
| OCR | PaddleOCR | Text recognition |
| TTS | Edge TTS / General TTS | Text-to-speech |
| ASR | Web Speech / General ASR | Speech recognition |
| LLM | Competition-designated Standardized LLM Base | Connects to the competition's official standardized LLM interface for multi-agent dialogue, logical reasoning, and document parsing |

---

## 📁 Project Structure

```
A3/
├── frontend/              # Frontend project
│   ├── src/
│   │   ├── views/         # Page views
│   │   ├── components/    # Components
│   │   ├── stores/        # Pinia stores
│   │   ├── api/           # API interfaces
│   │   └── router/        # Router configuration
│   └── package.json
│
├── backend/               # Backend project
│   ├── main.py            # Entry file
│   ├── manage_knowledge.py # Knowledge base CLI tool
│   ├── api/               # API routes
│   ├── rag/               # RAG engine
│   ├── services/          # Core services
│   │   ├── validation_service.py    # Hierarchical validation
│   │   ├── publish_service.py       # Publishing with rollback
│   │   └── qdrant_sync_service.py   # Blue-green deployment
│   ├── engines/           # Core engines
│   ├── agents/            # Multi-Agent system
│   ├── tests/             # Test directory
│   │   ├── test_real_integration.py # Integration tests (15)
│   │   ├── test_knowledge_toolchain.py # Toolchain tests (18)
│   │   └── test_magicstudy.py       # Business tests (12)
│   └── knowledge_base/    # Knowledge base
│
├── reports/               # Reports directory
└── docker-compose.yml     # Docker Compose configuration
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
git clone https://gitee.com/ghosts-in-a-dying-state/a3.git
cd a3
docker-compose up -d
```

Services:
- Frontend: http://localhost:5175
- Backend: http://localhost:8001
- Qdrant Dashboard: http://localhost:6333/dashboard

### Manual Setup

```bash
# Start Qdrant
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.7.0

# Backend
cd backend
pip install -r requirements.txt
python run_seed.py
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

---

## 🧪 Experiment Comparison

Four controlled experiment groups:

| Group | Mode | Unique Difference |
|-------|------|-------------------|
| A | LLM | LLM-only answers |
| B | LLM + RAG | + Knowledge base retrieval |
| C | LLM + RAG + Review | + Fact verification agent |
| D | Full System | + Learning profile personalization |

**Results**:
- Fact accuracy: 70% → 80% → 90% → 90%
- Citation accuracy: - → 70% → 80% → 80%
- Personalization: 30% → 40% → 40% → 80%

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Response Time | 2.8-3.8 seconds |
| Vector Dimension | 768 (BGE-base) |
| Q&A Accuracy | ~90% |
| Tests Passed | 45/45 |

---

## 📝 Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.0.0 | 2026-07 | Initial version |
| v1.1.0 | 2026-07 | Added RAG knowledge base |
| v1.2.0 | 2026-07 | Added voice features |
| v1.3.0 | 2026-07 | Docker deployment |
| v1.4.0 | 2026-07 | Standardized LLM base integration, resource generation |
| v1.5.0 | 2026-07 | Knowledge governance, blue-green deployment, 45 tests |

---

## 📄 License

MIT License

---

## 📞 Contact

- **Project**: https://gitee.com/ghosts-in-a-dying-state/a3
- **Issues**: Submit to repository

---

**MagicStudy Team** 🌟

> "Illuminating your learning journey"
