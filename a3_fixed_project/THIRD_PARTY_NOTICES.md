# Third-Party Notices

## 项目来源说明

### MagicStudy 原始项目

| 项目 | 说明 |
|------|------|
| **原始项目名称** | MagicStudy - AI智能学习助手 |
| **原始开发者** | MagicStudy开源社区 |
| **获取方式** | Git子模块引入，后转为直接放入主仓库 |
| **许可证** | MIT License |

### 参赛团队新增模块

以下模块由参赛团队独立开发，不属于原始MagicStudy项目：

| 模块 | 路径 | 说明 |
|------|------|------|
| **分级校验服务** | `backend/services/validation_service.py` | 根据课程状态（draft/demo_only/review/published/archived）应用不同校验标准 |
| **发布服务** | `backend/services/publish_service.py` | 发布流程管理，支持故障回滚 |
| **Qdrant同步服务** | `backend/services/qdrant_sync_service.py` | 蓝绿发布基础设施，支持原子别名切换 |
| **审核服务** | `backend/services/review_service.py` | 内容审核工作流，支持list/approve/reject操作 |
| **7维学习画像引擎** | `backend/engines/profile_engine.py` | 扩展至7维度画像（知识掌握度、先修知识缺口、错误模式、学习效率、学习持续性、学习目标与约束、资源交互偏好） |
| **反事实画像演示** | `backend/demo/counterfactual_demo.py` | 同一知识点针对不同学生画像的教学决策差异展示 |
| **TCP慢启动微课生成** | `backend/demo/tcp_slow_start_video.py` | matplotlib动画+TTS+字幕+ffmpeg合成MP4 |
| **真实集成测试** | `backend/tests/test_real_integration.py` | 15项集成测试，涵盖Qdrant同步、发布流程、故障注入 |
| **工具链测试** | `backend/tests/test_knowledge_toolchain.py` | 21项工具链测试 |
| **知识库治理** | `backend/manage_knowledge.py` | 命令行管理工具（validate/init-db/publish/sync-vectors/review） |
| **来源文档** | `backend/knowledge_base/computer_network/sources.json` | 35个来源文档清单 |
| **审核记录** | `backend/knowledge_base/computer_network/review_records.json` | 62条审核记录（35文档+19题+8错误模式） |

## 第三方依赖

### Python依赖

| 依赖 | 版本 | 许可证 |
|------|------|--------|
| FastAPI | 0.110+ | MIT |
| SQLAlchemy | 2.x | MIT |
| Pydantic | 2.x | MIT |
| LangGraph | 0.1+ | MIT |
| LangChain | 0.1+ | MIT |
| SentenceTransformers | 3.x | Apache 2.0 |
| Qdrant Client | 1.8+ | Apache 2.0 |
| python-dotenv | - | BSD-3-Clause |
| matplotlib | - | PSF |
| scikit-learn | - | BSD-3-Clause |
| pytest | - | MIT |

### 前端依赖

| 依赖 | 版本 | 许可证 |
|------|------|--------|
| Vue | 3.x | MIT |
| TypeScript | 5.x | Apache 2.0 |
| Vite | 6.x | MIT |
| Element Plus | 2.x | MIT |
| Pinia | 2.x | MIT |

### AI模型

| 模型 | 来源 | 许可证 |
|------|------|--------|
| BAAI/bge-base-zh-v1.5 | ModelScope/HuggingFace | MIT |
| BAAI/bge-reranker-base | ModelScope/HuggingFace | MIT |
| Edge TTS | Microsoft | 免费商用 |
| PaddleOCR | Baidu | Apache 2.0 |

## 代码比例说明

| 类别 | 占比 | 说明 |
|------|------|------|
| 原始MagicStudy代码 | ~30% | 基础框架、前端页面、部分API |
| 参赛团队新增代码 | ~50% | 知识库治理、安全发布、画像扩展、测试套件 |
| 第三方依赖 | ~20% | Python包、前端库、AI模型 |

## 许可证合规

本项目整体采用 **MIT License**，所有第三方依赖均符合开源许可证要求，可用于商业和非商业用途。
