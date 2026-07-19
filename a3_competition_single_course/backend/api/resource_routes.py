from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
import io
import base64
from engines import ProfileEngine, KnowledgeGraphEngine, resource_generator
from graph.resource_pipeline import resource_pipeline
from graph.state import MagicStudyState

router = APIRouter(prefix="/resources", tags=["resources"])

profile_engine = ProfileEngine()
kg_engine = KnowledgeGraphEngine()


@router.post("/generate")
async def generate_resources(student_id: str, knowledge_points: list[str], resource_type: str = Body("lecture")):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    topic = ", ".join(knowledge_points)
    content = ""
    
    for kp in knowledge_points:
        node = kg_engine.search_knowledge("computer_network", kp)
        if node:
            content += str(node)
    
    if resource_type in ["ppt", "mindmap", "code", "reading", "video"]:
        return generate_specific_resource(resource_type, topic, content)

    initial_state: MagicStudyState = {
        "profile": profile,
        "weak_points": knowledge_points,
        "diagnosis": {"summary": f"针对知识点: {', '.join(knowledge_points)}"}
    }

    result = resource_pipeline.invoke(initial_state)
    pack = result.get("resource_pack")

    return {
        "status": "success",
        "resource_pack": {
            "pack_id": pack.pack_id,
            "lecture_text": pack.lecture_text,
            "exercises": pack.exercises,
            "mind_map": pack.mind_map,
            "flash_cards": pack.flash_cards,
            "quality_score": pack.quality_score
        }
    }


@router.post("/generate/specific")
async def generate_specific_resource(
    resource_type: str = Body(...),
    topic: str = Body(...),
    content: str = Body("")
):
    if resource_type == "ppt":
        result = resource_generator.generate_ppt(topic, content)
        if result.get("data") and result.get("format") != "json":
            return StreamingResponse(
                io.BytesIO(base64.b64decode(result["data"])),
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
            )
        return result
    
    elif resource_type == "mindmap":
        return resource_generator.generate_mindmap(topic, content)
    
    elif resource_type == "code":
        return resource_generator.generate_code(topic, content)
    
    elif resource_type == "reading":
        return resource_generator.generate_reading(topic, content)
    
    elif resource_type == "video":
        return resource_generator.generate_video(topic, content)
    
    else:
        return {"status": "error", "message": f"不支持的资源类型: {resource_type}"}


@router.get("/types")
async def get_resource_types():
    return {
        "types": [
            {"id": "ppt", "name": "PPT讲义", "description": "生成可下载的PPT文件"},
            {"id": "mindmap", "name": "思维导图", "description": "生成Mermaid格式思维导图"},
            {"id": "code", "name": "代码实战", "description": "生成可运行代码+测试用例"},
            {"id": "reading", "name": "拓展阅读", "description": "RAG检索+LLM摘要"},
            {"id": "video", "name": "视频脚本", "description": "分镜脚本+TTS语音合成"},
            {"id": "lecture", "name": "知识点讲义", "description": "文本讲义+习题"},
        ]
    }


@router.get("/knowledge-tree/{subject}")
async def get_knowledge_tree(subject: str = "math"):
    tree = kg_engine.get_knowledge_tree(subject)
    return {"status": "success", "tree": tree}


@router.get("/knowledge/{subject}/{node_id}")
async def get_knowledge_node(subject: str, node_id: str):
    node = kg_engine.get_node_info(subject, node_id)
    if not node:
        return {"status": "error", "message": "Node not found"}
    return {"status": "success", "node": node}


@router.get("/search/{subject}")
async def search_knowledge(subject: str, query: str):
    results = kg_engine.search_knowledge(subject, query)
    return {"status": "success", "results": results}