"""fortune-app 入口：五运六气体质分析 · 免登录独立版（2026-10-05）。

自医疗数据平台 v2.5-final 的 my_page/page06/part01 原样提出：
- 界面/排盘/运气/Prompt/HTML导出：my_page/page06/part01/（零改动，便于同步）
- 神煞综合表：my_data/data06/numerology.py
- LLM 调用（DeepSeek）：my_model/open_ai/deepseek.py

启动：streamlit run fortune.py
与主项目同步：升级主项目 part01 后，整目录覆盖 my_page/page06/part01/ 即可。
"""
import streamlit as st

from my_page.page06.part01 import analyze

st.set_page_config(
    page_title="五运六气体质分析",
    page_icon="☯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

analyze.main()
