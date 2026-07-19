from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import json

router = APIRouter(prefix="/ragas", tags=["RAGAS评测"])

rag_engine: Optional[any] = None

try:
    from rag.engine import RAGEngine
    rag_engine_available = True
except Exception:
    rag_engine_available = False


@router.post("/evaluate", summary="RAGAS评测")
async def evaluate_ragas(
    test_cases: List[Dict],
):
    if not rag_engine_available:
        raise HTTPException(status_code=500, detail="RAG引擎依赖未安装")
    
    try:
        global rag_engine
        if rag_engine is None:
            rag_engine = RAGEngine()
        
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_relevancy,
            context_recall,
        )
        import pandas as pd
        
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        
        for tc in test_cases:
            query = tc.get("question", "")
            ground_truth = tc.get("ground_truth", "")
            
            results = rag_engine.retrieve(query, top_k=3)
            context_list = [r["text"] for r in results]
            
            questions.append(query)
            answers.append(json.dumps(results[:1], ensure_ascii=False))
            contexts.append(context_list)
            ground_truths.append([ground_truth])
        
        df = pd.DataFrame({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        
        result = evaluate(
            df,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_relevancy,
                context_recall,
            ],
        )
        
        return result.to_dict()
    
    except ImportError as e:
        if 'ragas' in str(e):
            return {
                "error": "ragas模块未安装",
                "message": "请运行 pip install ragas 安装评测框架",
                "test_cases_count": len(test_cases),
            }
        else:
            return {
                "error": "RAG引擎依赖未安装",
                "message": "请运行 pip install qdrant-client sentence-transformers rank-bm25 python-docx pdfplumber jieba",
                "test_cases_count": len(test_cases),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测失败: {str(e)}")


@router.get("/metrics", summary="获取可用评测指标")
async def get_available_metrics():
    try:
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_relevancy,
            context_recall,
            context_precision,
        )
        
        return {
            "metrics": [
                {
                    "name": "faithfulness",
                    "description": "答案忠实度：评估答案是否完全基于提供的上下文",
                },
                {
                    "name": "answer_relevancy",
                    "description": "答案相关性：评估答案与问题的相关性",
                },
                {
                    "name": "context_relevancy",
                    "description": "上下文相关性：评估检索到的上下文与问题的相关性",
                },
                {
                    "name": "context_recall",
                    "description": "上下文召回率：评估检索到的上下文是否包含所有必要信息",
                },
                {
                    "name": "context_precision",
                    "description": "上下文精确率：评估检索到的上下文中有多少是有用的",
                },
            ]
        }
    except ImportError:
        return {
            "error": "ragas模块未安装",
            "metrics": ["faithfulness", "answer_relevancy", "context_relevancy", "context_recall", "context_precision"],
        }
