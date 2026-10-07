"""DeepSeek API 调用（2026-10-07 P1-1：key 改为 secrets/环境变量读取）。

key 读取优先级：环境变量 DEEPSEEK_API_KEY → st.secrets（.streamlit/
secrets.toml 扁平键 DEEPSEEK_API_KEY，secrets 不进源码库）。
未配置时抛 RuntimeError（含配置指引），由 analyze.py 的 LLM 失败
兜底分支（st.error + 重试）承接——排盘/大运等本地计算不受影响。
"""
import os

from openai import OpenAI
import httpx

_BASE_URL = "https://api.deepseek.com"

_KEY_TIP = (
    "未配置 DeepSeek API key：请在项目根 .streamlit/secrets.toml 写入\n"
    '  DEEPSEEK_API_KEY = "sk-xxxx"\n'
    "或设置环境变量 DEEPSEEK_API_KEY 后重启应用。"
    "（secrets.toml 含真实 key，勿提交/同步；示例见"
    " .streamlit/secrets.toml.example）"
)


def api_key_or_none():
    """读取 API key：环境变量优先，其次 st.secrets；未配置返回 None。"""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    try:                       # Streamlit 运行环境才有 secrets（缺失/不可用则跳过）
        import streamlit as st
        key = str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
        if key:
            return key
    except Exception:
        pass
    return None


def allow_pro_or_default():
    """是否允许使用 Pro 模型：环境变量优先，其次 st.secrets；未配置默认 True。

    读取优先级：环境变量 DEEPSEEK_ALLOW_PRO → st.secrets["DEEPSEEK_ALLOW_PRO"]。
    字符串取值 "1"/"true"/"yes"/"on"（大小写不敏感）视为允许，其余视为不允许；
    secrets.toml 中 true/false 会被解析为 bool，直接使用。
    """
    val = os.environ.get("DEEPSEEK_ALLOW_PRO", "").strip().lower()
    if val:
        return val in ("1", "true", "yes", "on")
    try:
        import streamlit as st
        raw = st.secrets.get("DEEPSEEK_ALLOW_PRO", True)
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    except Exception:
        pass
    return True


def deepseek(role="You are a helpful assistant", content="Hello", models=0):
    key = api_key_or_none()
    if not key:
        raise RuntimeError(_KEY_TIP)
    client = OpenAI(api_key=key, base_url=_BASE_URL)
    allow_pro = allow_pro_or_default()
    if models == 0 or not allow_pro:
        # 模型 id 以 GET https://api.deepseek.com/models 返回为准：
        # deepseek-flash = DeepSeek-V4.1-Flash（旧名 deepseek-v4-flash
        # 已不存在，传错会报 model not found，表现为"key 配了仍调用失败"）
        # 若配置 DEEPSEEK_ALLOW_PRO=false，即使用户勾选 pro 也强制走 flash。
        model = "deepseek-flash"
    else:
        model = "deepseek-v4-pro"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": content},
            ],
            stream=False
        )
        return response.choices[0].message.content
    except httpx.HTTPStatusError as exc:
        # 打印服务器返回的原始内容
        print(f"HTTP Error: {exc.response.status_code}")
        print(f"Response content: {exc.response.text}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
