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
    if _usable(settings.SPARK_API_KEY) and _usable(settings.SPARK_APP_ID) and _usable(settings.SPARK_API_SECRET):
        return {"configured": True, "provider": "spark", "model": settings.SPARK_MODEL_NAME}
    if _usable(settings.DEEPSEEK_API_KEY):
        return {"configured": True, "provider": "deepseek", "model": settings.DEEPSEEK_MODEL_NAME}
    if _usable(settings.OPENAI_API_KEY):
        return {"configured": True, "provider": "openai-compatible", "model": settings.MODEL_NAME}
    return {"configured": False, "provider": None, "model": None}


class UnconfiguredLLM:
    """Keep the API server bootable while returning an actionable error on use."""

    message = (
        "未配置可用的大模型密钥。请在 backend/.env 中配置 "
        "DEEPSEEK_API_KEY、OPENAI_API_KEY，或完整的讯飞星火三项密钥。"
    )

    def invoke(self, *_args, **_kwargs):
        raise RuntimeError(self.message)

    def stream(self, *_args, **_kwargs):
        raise RuntimeError(self.message)


def get_llm():
    # 优先使用讯飞星火大模型（OpenAI兼容接口）
    if _usable(settings.SPARK_API_KEY) and _usable(settings.SPARK_APP_ID) and _usable(settings.SPARK_API_SECRET):
        logger.info(f"使用讯飞星火大模型: {settings.SPARK_MODEL_NAME}")
        return ChatOpenAI(
            model=settings.SPARK_MODEL_NAME,
            api_key=f"{settings.SPARK_APP_ID}:{settings.SPARK_API_KEY}:{settings.SPARK_API_SECRET}",
            base_url=settings.SPARK_API_BASE,
            temperature=0.7
        )
    # 其次使用DeepSeek配置
    if _usable(settings.DEEPSEEK_API_KEY):
        logger.info(f"使用DeepSeek模型: {settings.DEEPSEEK_MODEL_NAME}")
        return ChatOpenAI(
            model=settings.DEEPSEEK_MODEL_NAME,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
            temperature=0.7
        )
    if not _usable(settings.OPENAI_API_KEY):
        logger.warning(UnconfiguredLLM.message)
        return UnconfiguredLLM()

    # 回退到OpenAI兼容配置
    logger.info(f"使用OpenAI模型: {settings.MODEL_NAME}")
    return ChatOpenAI(
        model=settings.MODEL_NAME,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
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
