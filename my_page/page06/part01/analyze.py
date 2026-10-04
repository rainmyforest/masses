"""page06/part01 · 体质分析界面（2026-09-25 V3：自 part01_wuyun.py 移入）。

界面分区（表单设计最佳实践：分模块、隐藏不相关信息、及时反馈）：
  ① 基础信息：称呼/性别/分析视角/白话解说/深度模型
  ② 出生信息：阳历=date_input+time_input；阴历=数字表单+闰月（公历日历隐藏）
  ③ 排盘口径：出生地（城市/自定义经度）+ 时口径三选
  ④ 来访诉求（expander 选填）
工程化（C 项）：排盘与 LLM 结果双层缓存（同输入不重复计费）、
st.status 两段式进度、异常捕获 + 一键重试、结果 HTML 下载（part01/mdhtml.py）。
"""
from datetime import date, datetime, time

import pandas as pd
import streamlit as st

import my_model.open_ai.deepseek as dm
from my_page.page06.part01 import engine, mdhtml, prompt, solartime, yunqi

_DEFAULT_D = date(1990, 1, 1)
_DEFAULT_T = time(10, 0)


@st.cache_data(show_spinner=False)
def _cached_chart(*args):
    """排盘缓存（args 为 primitives 元组，key 自动生成）。"""
    return engine.chart(*args)


@st.cache_data(show_spinner=False)
def _cached_llm(role, content, models):
    """LLM 结果缓存：相同 prompt 不重复调用（不重复计费）。"""
    return dm.deepseek(role, content, models=models)


def _form_basic():
    """① 基础信息区。"""
    with st.container(border=True):
        st.markdown("##### ① 基础信息")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("称呼（选填，用于报告称呼）", key="p01_name",
                                 placeholder="如：李先生")
            sex = st.selectbox("性别", ["男", "女"], key="p01_sex")
        with c2:
            mode = st.selectbox("分析视角", prompt.MODES, key="p01_mode")
            vernacular = st.checkbox("白话解说（无专业术语）", key="p01_plain")
            deepthink = st.checkbox("是否使用智能分析pro？", key="p01_deep")
    return name, sex, mode, vernacular, deepthink


def _form_birth():
    """② 出生信息区：阳历=日历控件；阴历=数字表单（公历输入隐藏）。"""
    with st.container(border=True):
        st.markdown("##### ② 出生信息")
        calendar = st.selectbox("输入历法", ["阳历", "阴历"], key="p01_cal")
        time_rough = st.checkbox("出生时间不确定（时柱仅供参考）",
                                 key="p01_rough")

        if calendar == "阳历":
            # 默认值走 session_state 预置，避免与换算回调形成"双指定"
            for _k, _v in (("p01_date", _DEFAULT_D), ("p01_time", _DEFAULT_T)):
                if _k not in st.session_state:
                    st.session_state[_k] = _v
            dcol, tcol = st.columns(2)
            with dcol:
                d = st.date_input(
                    "出生日期（公历）", min_value=date(1900, 1, 1),
                    max_value=date(2100, 12, 31), key="p01_date")
            with tcol:
                t = st.time_input("出生时间（北京时间，精确到分）",
                                  key="p01_time")
            if isinstance(d, (list, tuple)):        # 拖选区间时取起点
                d = d[0]
            st.caption(solartime.shichen_label(t.hour))
            return {"calendar": calendar, "time_rough": time_rough,
                    "y": d.year, "m": d.month, "d": d.day, "leap": False,
                    "hour": t.hour, "minute": t.minute}

        # 阴历：数字表单直连排盘（公历日历不渲染——隐藏无关输入）
        ly, lm, ld = st.columns(3)
        with ly:
            yy = st.number_input("阴历年", min_value=1900, max_value=2100,
                                 value=1990, step=1, key="p01_ly")
        with lm:
            mm = st.number_input("阴历月", min_value=1, max_value=12,
                                 value=1, step=1, key="p01_lm")
        with ld:
            dd = st.number_input("阴历日", min_value=1, max_value=30,
                                 value=1, step=1, key="p01_ld")
        leap = st.checkbox("该月为闰月", key="p01_lleap")
        t = st.time_input("出生时间（北京时间，精确到分）", key="p01_time")
        # 实时换算回显（换算失败即提示，不等到排盘）
        try:
            s = engine.birth_solar(int(yy), int(mm), int(dd), 12,
                                   calendar="阴历", leap=leap)
            st.caption(f"对应公历 {s.getYear()}-{s.getMonth():02d}-{s.getDay():02d}"
                       f" ｜ {solartime.shichen_label(t.hour)}")
        except ValueError as e:
            st.error(str(e))
        return {"calendar": calendar, "time_rough": time_rough,
                "y": int(yy), "m": int(mm), "d": int(dd), "leap": leap,
                "hour": t.hour, "minute": t.minute}


def _form_options():
    """③ 排盘口径区：出生地 + 太阳时。"""
    with st.container(border=True):
        st.markdown("##### ③ 排盘口径")
        c1, c2 = st.columns(2)
        with c1:
            city = st.selectbox("出生地（用于太阳时校正）",
                                list(solartime.CITY_LON), key="p01_city")
            custom = st.checkbox("自定义经度（东经度数）", key="p01_custom")
            if custom:
                longitude = st.number_input(
                    "东经经度", min_value=70.0, max_value=140.0,
                    value=float(solartime.CITY_LON[city]), step=0.01,
                    format="%.2f", key="p01_lon")
            else:
                longitude = float(solartime.CITY_LON[city])
        with c2:
            tmode = st.selectbox("排盘时口径", solartime.MODES, key="p01_tmode")
        if tmode != solartime.BEIJING:
            st.caption("校正说明：平太阳时=经度差×4分/度；真太阳时=平太阳时+均时差"
                       "（当日太阳实际位置）。命理排盘主流用平太阳时。")
    return longitude, tmode


def main():
    st.title("五运六气体质分析")
    st.caption("依据出生时间推算四柱与五运六气，分析先天体质偏性并给出顺时养生建议。"
               "本分析为体质倾向提示，不构成医疗诊断，不预测吉凶。")

    name, sex, mode, vernacular, deepthink = _form_basic()
    birth = _form_birth()
    longitude, tmode = _form_options()

    with st.expander("④ 来访诉求（选填，默认全面分析）"):
        question = st.text_area(
            "想重点了解的问题", height=80, key="p01_q",
            placeholder="如：最近总睡不好、容易心烦……（留空则全面分析）")

    go = st.button("开始分析", type="primary", key="p01_go")

    # ── 排盘（含太阳时校正）+ 结果展示 ──
    if not go:
        return

    with st.status("正在排盘…", expanded=True) as status:
        # 阴历输入：先换算成公历日期（闰月由 lunar-python 处理），
        # 再拼钟表时刻做太阳时校正——校正对象始终是"钟表时刻"，
        # 与输入历法无关
        if birth["calendar"] == "阴历":
            try:
                _s = engine.birth_solar(
                    birth["y"], birth["m"], birth["d"], 12,
                    calendar="阴历", leap=birth["leap"])
            except ValueError as e:
                st.error(str(e))
                st.stop()
            y_, m_, d_ = _s.getYear(), _s.getMonth(), _s.getDay()
        else:
            y_, m_, d_ = birth["y"], birth["m"], birth["d"]
        try:
            raw_dt = datetime(y_, m_, d_, birth["hour"], birth["minute"])
        except ValueError as e:
            st.error(f"出生日期无效：{e}")
            st.stop()
        adj, lon_min, eot = solartime.adjust(raw_dt, longitude, tmode)
        if tmode == solartime.BEIJING:
            tip = "北京时间（未校正）"
        elif tmode == solartime.MEAN:
            tip = f"地方平太阳时（经度校正 {lon_min:+.1f} 分）"
        else:
            tip = (f"真太阳时（经度校正 {lon_min:+.1f} 分、"
                   f"均时差 {eot:+.1f} 分）")
        status.update(label=f"排盘完成 · 排盘时刻 {adj:%Y-%m-%d %H:%M} · {tip}")

    try:
        info = _cached_chart(adj.year, adj.month, adj.day, adj.hour,
                            "阳历", False, adj.minute)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    facts = yunqi.yunqi_facts(info["solar"])

    st.success("四柱：" + " ".join(info["bazi"]))
    st.caption(f"{info['gongli']} ｜ {info['nongli']} ｜ "
               f"日主：{info['ri_zhu']}（五行属{info['ri_zhu_wuxing']}）")
    st.markdown("**命盘综合表**")
    st.dataframe(info["table"])

    st.markdown("**出生当年五运六气**")
    st.table(pd.DataFrame({"项目": list(facts.keys()),
                           "内容": [str(v) for v in facts.values()]}))
    st.caption("口径说明：运气年以大寒交司分界（出生在大寒前归上一年运气周期）；"
               "八字年柱以立春分界；六步主气起于大寒、客气按年支司天定位。")

    # ── LLM 解读层（缓存 + 异常重试 + 进度）──
    today = yunqi.today_context()
    q = question.strip() or prompt.default_question(mode)
    role, content = prompt.build_prompt(
        mode, info, facts, today, q, sex,
        vernacular=vernacular, name=name, time_rough=birth["time_rough"])

    with st.status("正在生成分析报告…（约1分钟）", expanded=False) as status:
        try:
            result = _cached_llm(role, content, 1 if deepthink else 0)
        except Exception as e:
            st.error(f"AI 分析调用失败：{e}")
            if st.button("重试", key="p01_retry"):
                st.rerun()
            st.stop()
        status.update(label="报告生成完成")

    st.markdown(result)

    # ── HTML 下载 ──
    meta_lines = [
        f"称呼：{name.strip()}" if name.strip() else f"性别：{sex}",
        f"出生：{info['gongli']}（{info['nongli']}）",
        f"四柱：{' '.join(info['bazi'])}（日主 {info['ri_zhu']}）",
        f"排盘口径：{tmode}（{tip}）",
    ]
    html_text = mdhtml.build_report_html(
        "五运六气体质分析报告", [m for m in meta_lines if m], result)
    fname = datetime.now().strftime("体质分析_%Y%m%d_%H%M.html")
    st.download_button(
        "⬇️ 下载本报告（HTML）", data=html_text,
        file_name=fname, mime="text/html", key="p01_dl")
