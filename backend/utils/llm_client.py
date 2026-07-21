from langchain_openai import ChatOpenAI
from config import settings
from langchain_core.messages import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


def _usable(value: str) -> bool:
    """Reject empty values and untouched example placeholders."""
    value = (value or "").strip()
    return bool(value) and not value.lower().startswith("your_")


def llm_config_status() -> dict:
    if _usable(settings.LLM_API_KEY):
        return {"configured": True, "provider": "competition-llm", "model": settings.LLM_MODEL_NAME}
    return {"configured": False, "provider": None, "model": None}


class UnconfiguredLLM:
    """Keep the API server bootable while returning an actionable error on use."""

    message = (
        "未配置可用的大模型密钥。请在 backend/.env 中配置 "
        "LLM_API_KEY（赛事指定标准化大模型底座）。"
    )

    def invoke(self, *_args, **_kwargs):
        raise RuntimeError(self.message)

    def stream(self, *_args, **_kwargs):
        raise RuntimeError(self.message)


def get_llm():
    """获取赛事指定标准化大模型底座实例。"""
    if not _usable(settings.LLM_API_KEY):
        logger.warning(UnconfiguredLLM.message)
        return UnconfiguredLLM()

    logger.info(f"使用赛事指定标准化大模型底座: {settings.LLM_MODEL_NAME}")
    return ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE if _usable(settings.LLM_API_BASE) else None,
        temperature=0.7
    )


def invoke_llm(prompt: str, system_message: str = "") -> str:
    try:
        llm = get_llm()
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        raise


def stream_llm(prompt: str, system_message: str = ""):
    try:
        llm = get_llm()
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error(f"LLM流式调用失败: {e}")
        yield f"[Error] {e}"
