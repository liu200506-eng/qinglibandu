from engines import ProfileEngine, KnowledgeGraphEngine
from graph.resource_pipeline import resource_pipeline
from graph.state import MagicStudyState

profile_engine = ProfileEngine()
kg_engine = KnowledgeGraphEngine()


def generate_resources(student_id: str, knowledge_points: list[str]) -> dict:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {}

    initial_state: MagicStudyState = {
        "profile": profile,
        "weak_points": knowledge_points,
        "diagnosis": {"summary": f"针对知识点: {', '.join(knowledge_points)}"}
    }

    result = resource_pipeline.invoke(initial_state)
    return result.get("resource_pack", {})


def get_knowledge_tree(subject: str = "math") -> dict:
    return kg_engine.get_knowledge_tree(subject)


def get_knowledge_node(subject: str, node_id: str) -> dict | None:
    return kg_engine.get_node_info(subject, node_id)


def search_knowledge(subject: str, query: str) -> list[dict]:
    return kg_engine.search_knowledge(subject, query)