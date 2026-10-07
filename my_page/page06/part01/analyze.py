"""page06/part01 · 体质分析界面（2026-09-25 V3：自 part01_wuyun.py 移入；
2026-10-07 S4：接线大运流年——dayun_facts 缓存调用、五运六气之后新增
大运流年展示（交运 caption + 大运总表 + 当前大运十年流年明细 expander）、
prompt 注入 dayun/strength、附录 A-E 数据组装传 mdhtml 导出）。

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
from my_page.page06.part01 import dayun, engine, mdhtml, prompt, solartime, yunqi

_DEFAULT_D = date(1990, 1, 1)
_DEFAULT_T = time(10, 0)


@st.cache_data(show_spinner=False)
def _cached_chart(*args):
    """排盘缓存（args 为 primitives 元组，key 自动生成）。"""
    return engine.chart(*args)


@st.cache_data(show_spinner=False)
def _cached_dayun(y, m, d, h, mi, gender, now_year):
    """大运流年缓存（primitives 入参与 _cached_chart 同款；口径同源——
    由同一校正后时刻重建 Solar 派生 EightChar 大运）。
    now_year 入键：跨年自动失效重算"当前★/当前年★"标记，
    避免长期驻留进程跨年后的口径过期；dayun_facts 内仅用 now.year，
    传年初锚定即与 datetime.now() 同年结果一致（确定性缓存值）。"""
    solar = engine.birth_solar(y, m, d, h, mi, "阳历", False)
    return dayun.dayun_facts(solar, gender, now=datetime(now_year, 1, 1))


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

        # 默认值走 session_state 预置，避免与换算回调形成"双指定"
        # （两种历法共用 p01_time，预置放在分支外确保默认判定口径一致）
        for _k, _v in (("p01_date", _DEFAULT_D), ("p01_time", _DEFAULT_T)):
            if _k not in st.session_state:
                st.session_state[_k] = _v

        if calendar == "阳历":
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
            # 出生日期与时间都仍是默认示例值 → 视为未填写，禁止提交
            is_default = (d == _DEFAULT_D and t == _DEFAULT_T)
            if is_default:
                st.warning("出生日期与时间仍是默认示例值（1990-01-01 10:00），"
                           "请先选择真实的出生日期和时间。")
            return {"calendar": calendar, "time_rough": time_rough,
                    "y": d.year, "m": d.month, "d": d.day, "leap": False,
                    "hour": t.hour, "minute": t.minute,
                    "is_default": is_default}

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
        # 阴历年/月/日/闰月与时间都仍是默认值 → 视为未填写，禁止提交
        is_default = (int(yy) == _DEFAULT_D.year and int(mm) == _DEFAULT_D.month
                      and int(dd) == _DEFAULT_D.day and not leap
                      and t == _DEFAULT_T)
        if is_default:
            st.warning("出生日期与时间仍是默认示例值（1990年正月初一 10:00），"
                       "请先选择真实的出生日期和时间。")
        return {"calendar": calendar, "time_rough": time_rough,
                "y": int(yy), "m": int(mm), "d": int(dd), "leap": leap,
                "hour": t.hour, "minute": t.minute,
                "is_default": is_default}


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


# 大运总表（表 C）/ 当前大运流年（表 D）展示列契约（方案 2.4：
# 两表字段完全一致地进页面与 HTML 附录）
_DAYUN_COLS = ("序", "起止虚岁", "起止公历", "大运干支", "天干十神", "纳音",
               "五行", "备注")
_LIUNIAN_COLS = ("公历年", "虚岁", "流年干支", "天干十神", "纳音", "备注")


def _dayun_display_rows(dy, birth_year):
    """大运总表行（表 C）：起运前段"—（出生至起运）"行 + 全部干支步。

    Q7：起运前段（虚岁 1 起、无大运干支）由展示层据"起运"信息渲染；
    起运虚岁为 1（出生即交运）时该段为空、不渲染。
    "序"列统一 str（含起运前"—"），避免 st.dataframe Arrow 混型序列化报错。"""
    rows = []
    if dy["大运"] and dy["大运"][0]["起岁"] > 1:
        first = dy["大运"][0]
        rows.append({"序": "—", "起止虚岁": f"1-{first['起岁'] - 1}",
                     "起止公历": f"{birth_year}-{first['起年'] - 1}",
                     "大运干支": "—（出生至起运）", "天干十神": "—",
                     "纳音": "—", "五行": "—", "备注": "起运前"})
    rows.extend({"序": str(s["序"]), "起止虚岁": f"{s['起岁']}-{s['止岁']}",
                 "起止公历": f"{s['起年']}-{s['止年']}", "大运干支": s["干支"],
                 "天干十神": s["十神"], "纳音": s["纳音"], "五行": s["五行"],
                 "备注": s["备注"]} for s in dy["大运"])
    return rows


def _liunian_display_rows(rows):
    """当前大运流年行（表 D 列契约）。"""
    return [{"公历年": r["年"], "虚岁": r["虚岁"], "流年干支": r["干支"],
             "天干十神": r["十神"], "纳音": r["纳音"], "备注": r["备注"]}
            for r in rows]


def _md_table(rows, cols):
    """展示行 → 附录 markdown 表（"备注"含 ★ 的行加粗：<strong>+★，
    方案 4.2；页面 st.dataframe 单元格不渲染 markdown，附录侧由本函数补足）。"""
    if not rows:
        return "（无数据）"
    marked = []
    for r in rows:
        r = dict(r)
        if "★" in str(r.get("备注", "")):    # B 表无备注列，get 兜底
            r["备注"] = f"**{r['备注']}**"
        marked.append(r)
    return pd.DataFrame(marked, columns=list(cols)).to_markdown(index=False)


def _paipan_brief(tmode, tip):
    """排盘口径简述（P3-2 文案去重）：tmode 短名 + tip 括号内校正明细。

    tmode 为模式全称（如"北京时间（东经120°标准时，不校正）"），tip 为
    "短名（具体校正）"（如"北京时间（未校正）"），直接拼接会两次出现
    模式名——取 tmode 首个"（"前短名与 tip 括号内明细重组，三种口径
    （北京/平太阳/真太阳）均无重复且校正数值保留。"""
    short = tmode.split("（", 1)[0]
    detail = tip[tip.index("（") + 1:tip.rindex("）")] if "（" in tip else tip
    return f"{short}（{detail}）"


def _appendix_e_md(dy, tmode, tip, time_rough):
    """附录 E · 排盘口径说明（虚岁/起运流派/立春分界/免责等）。"""
    qy = dy["起运"]
    lines = [
        "- 年龄均为**虚岁**（公历年 − 出生公历年 + 1，非周岁）。",
        f"- 起运：{qy['出生后']}交运（{qy['交运时刻']}），起运虚岁 "
        f"{qy['起运虚岁']}；顺逆排按「{qy['排法']}」，折算流派为"
        f"「{qy['流派']}」。",
        "- 分界口径：八字年柱与流年干支均以**立春**交接时刻分界；"
        "五运六气运气年以**大寒**交司分界，两者干支不同属正常口径差异。",
        f"- 排盘时刻：{_paipan_brief(tmode, tip)}；大运流年由同一排盘派生，"
        "口径同源。",
        "- 大运共 10 步（约至 90 岁）；第 1 步之前为「出生至起运」段"
        "（无大运干支，表中以 — 表示）。",
    ]
    if time_rough:
        lines.append("- 出生时间不确定：时柱与起运交运日期仅供参考"
                     "（误差可达数月）。")
    lines += [
        "- 打印提示：如需打印完整附录，请先在浏览器中点击各节标题展开后"
        "再打印（收起节不随打印输出）。",
        "- 免责：本附录与报告正文均为体质倾向提示，不构成医疗诊断、"
        "不预测吉凶祸福；健康问题请线下就医。",
    ]
    return "\n".join(lines)


def _build_appendices(dy, info, facts, rows_dayun, rows_ln, tmode, tip,
                      time_rough):
    """附录 A-E 数据组装（方案 4.3 契约 → mdhtml.appendices 入参）：
    A 命盘综合表 / B 出生当年五运六气 / C 大运总表 / D 当前大运流年表 /
    E 排盘口径说明，五节一律默认收起（2026-10-07 应需求调整）。"""
    qy = dy["起运"]
    if rows_ln:
        d_md = _md_table(rows_ln, _LIUNIAN_COLS)
    else:                                   # 未交运（儿童命例）
        first = dy["大运"][0]
        d_md = (f"尚未交运：{first['起年']} 年（虚岁 {first['起岁']}）起进入"
                f"第一步大运 {first['干支']}（{first['十神']}），"
                "届时起算十年流年。")
    return [
        {"title": "附录 A · 命盘综合表", "open": False,
         "md": info["table"].to_markdown()},
        {"title": "附录 B · 出生当年五运六气", "open": False,
         "md": _md_table([{"项目": k, "内容": str(v)}
                          for k, v in facts.items()], ("项目", "内容"))
         + "\n\n注：运气年以大寒交司分界（出生在大寒前归上一年运气周期）；"
           "八字年柱以立春分界；六步主气起于大寒、客气按年支司天定位。"},
        {"title": "附录 C · 大运总表", "open": False,
         "md": _md_table(rows_dayun, _DAYUN_COLS)
         + f"\n\n注：{qy['出生后']}交运（{qy['交运时刻']}），{qy['排法']}"
           f"（流派：{qy['流派']}）；年龄为虚岁；换运年 = 大运交接之年。"},
        {"title": "附录 D · 当前大运流年表", "open": False, "md": d_md},
        {"title": "附录 E · 排盘口径说明", "open": False,
         "md": _appendix_e_md(dy, tmode, tip, time_rough)},
    ]


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

    go = st.button("开始分析", type="primary", key="p01_go",
                   disabled=birth["is_default"],
                   help="出生日期和时间仍是默认示例值时不可提交，"
                        "请先在②出生信息中选择真实值。")

    # ── 排盘（含太阳时校正）+ 结果展示 ──
    if not go:
        return
    if birth["is_default"]:
        # 双保险：按钮已 disabled，此处拦截异常/脚本方式触发的提交
        st.warning("请先将出生日期和时间改为真实值，再开始分析。")
        st.stop()

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
    with st.expander("**命盘综合表**"):
        st.table(info["table"])

    with st.expander("**出生当年五运六气**"):
        st.table(pd.DataFrame({"项目": list(facts.keys()),
                           "内容": [str(v) for v in facts.values()]}))
        st.caption("口径说明：运气年以大寒交司分界（出生在大寒前归上一年运气周期）；"
                "八字年柱以立春分界；六步主气起于大寒、客气按年支司天定位。")

    # ── 大运流年（S4：交运 caption + 大运总表 + 当前大运十年明细）──
    dy = _cached_dayun(adj.year, adj.month, adj.day, adj.hour, adj.minute,
                       sex, datetime.now().year)
    rows_dayun = _dayun_display_rows(dy, info["solar"].getYear())
    rows_ln = _liunian_display_rows(dy["当前大运流年"])
    qy = dy["起运"]
    with st.expander("**大运流年**"):
        st.caption(f"起运：{qy['出生后']}交运（{qy['交运时刻']}），起运虚岁 "
               f"{qy['起运虚岁']}｜{qy['排法']}｜起运流派：{qy['流派']}｜"
               "年龄均为虚岁")
        st.dataframe(pd.DataFrame(rows_dayun, columns=list(_DAYUN_COLS)),
                     hide_index=True, width="stretch")
    if rows_ln:
        cur = dy["当前大运"]
        with st.expander("**当前大运 · 十年流年明细**", expanded=False):
            st.dataframe(pd.DataFrame(rows_ln, columns=list(_LIUNIAN_COLS)),
                         hide_index=True, width="stretch")
            st.caption(f"当前第 {cur['序']} 步大运 {cur['干支']}"
                       f"（{cur['十神']}｜{cur['纳音']}），{cur['起岁']}-"
                       f"{cur['止岁']} 虚岁（{cur['起年']}-{cur['止年']}）；"
                       "★ = 当前所在，换运年 = 大运交接之年。")
    else:                                   # 未交运（儿童命例）
        first = dy["大运"][0]
        st.caption(f"尚未交运：{first['起年']} 年（虚岁 {first['起岁']}）起进入"
                   f"第一步大运 {first['干支']}（{first['十神']}）。")
    if birth["time_rough"]:                 # 起运随时辰漂移（方案 R2）
        st.caption("出生时间不确定，起运与交运日期仅供参考（误差可达数月）。")

    # ── LLM 解读层（缓存 + 异常重试 + 进度）──
    today = yunqi.today_context()
    q = question.strip() or prompt.default_question(mode)
    role, content = prompt.build_prompt(
        mode, info, facts, today, q, sex,
        vernacular=vernacular, name=name, time_rough=birth["time_rough"],
        dayun=dy, strength=engine.day_master_strength(info["bazi"]))

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

    # ── HTML 下载（附录 A-E，S4 组装 → S5 渲染）──
    meta_lines = [
        f"称呼：{name.strip()}" if name.strip() else f"性别：{sex}",
        f"出生：{info['gongli']}（{info['nongli']}）",
        f"四柱：{' '.join(info['bazi'])}（日主 {info['ri_zhu']}）",
        f"排盘口径：{_paipan_brief(tmode, tip)}",
    ]
    html_text = mdhtml.build_report_html(
        "五运六气体质分析报告", [m for m in meta_lines if m], result,
        appendices=_build_appendices(dy, info, facts, rows_dayun, rows_ln,
                                     tmode, tip, birth["time_rough"]))
    fname = datetime.now().strftime("体质分析_%Y%m%d_%H%M.html")
    st.download_button(
        "⬇️ 下载本报告（HTML）", data=html_text,
        file_name=fname, mime="text/html", key="p01_dl")
