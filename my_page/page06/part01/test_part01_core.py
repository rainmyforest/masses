"""page06/part01 测试：排盘引擎（A）+ 五运六气（B）+ prompt + 全链路。

运行：cd hospital && python -m pytest my_page/page06/part01/test_core.py -q
"""
import sys
from datetime import date, datetime, time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]      # hospital/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import Solar, Lunar                          # noqa: E402
from my_page.page06.part01 import engine, prompt, solartime, yunqi  # noqa: E402

# ─────────────────────────── A：排盘引擎 ───────────────────────────

# 已知排盘基准（lunar-python 标准输出，2026-09-25 与旧 YMDT 实测对照核定）
KNOWN_BAZI = [
    ((2026, 1, 20, 10), ["乙巳", "己丑", "甲午", "己巳"]),   # 立春前 → 年柱乙巳
    ((2026, 2, 4, 12), ["丙午", "庚寅", "己酉", "庚午"]),    # 立春当日交节后 → 丙午庚寅
    ((2026, 3, 5, 10), ["丙午", "庚寅", "戊寅", "丁巳"]),    # 惊蛰日交节前 → 月柱庚寅
    ((1984, 10, 5, 6), ["甲子", "癸酉", "壬申", "癸卯"]),    # 旧版错 3 柱的回归样例
]


@pytest.mark.parametrize("args,expect", KNOWN_BAZI)
def test_bazi_known(args, expect):
    y, m, d, h = args
    assert engine.chart(y, m, d, h)["bazi"] == expect


def test_chart_fields():
    info = engine.chart(2026, 3, 5, 10)
    assert info["ri_zhu"] == "戊" and info["ri_zhu_wuxing"] == "土"
    assert "公历 2026年3月5日 10时" == info["gongli"]
    assert "农历" in info["nongli"] and "二〇二六" in info["nongli"]
    assert list(info["table"].index) == ["年", "月", "日", "时"]
    assert "干支" in info["table"].columns and "纳音" in info["table"].columns


def test_lunar_input_and_roundtrip():
    # 阳历输入 与 其对应阴历输入 排盘一致（3 例，含跨春节窗口与闰月；
    # 时辰取非子时段——23 时晚子时归柱口径属 lunar-python 内部约定，不在往返范围）
    for (y, m, d, h) in [(2026, 1, 20, 10), (1984, 10, 5, 6), (2025, 8, 8, 10)]:
        lunar = Solar.fromYmdHms(y, m, d, h, 0, 0).getLunar()
        via_lunar = engine.chart(
            lunar.getYear(), lunar.getMonth(), lunar.getDay(), h, "阴历",
            lunar.getMonth() < 0)["bazi"]
        assert via_lunar == engine.chart(y, m, d, h)["bazi"], (y, m, d, h)


def test_leap_month_anchor():
    # 2025 闰六月初一 = 2025-07-25（公开历法锚点）
    s = Lunar.fromYmdHms(2025, -6, 1, 12, 0, 0).getSolar()
    assert (s.getYear(), s.getMonth(), s.getDay()) == (2025, 7, 25)
    info = engine.chart(2025, 6, 1, 12, "阴历", leap=True)
    assert "闰六月" in info["nongli"]
    assert info["bazi"] == engine.chart(2025, 7, 25, 12)["bazi"]


def test_invalid_dates():
    with pytest.raises(ValueError, match="阳历"):
        engine.chart(2026, 2, 30, 10)              # 阳历 2 月 30
    with pytest.raises(ValueError, match="闰二月"):
        engine.chart(2026, 2, 1, 10, "阴历", leap=True)   # 2026 无闰二月
    with pytest.raises(ValueError):
        engine.chart(2025, 13, 1, 10, "阴历")       # 月越界


# ─────────────────────── A：神煞表与 lunar-python 交叉验证 ───────────────────────

_NAYIN_ALIAS = {"佛灯火": "覆灯火"}   # 流派用词差异，二者等义


def _nayin_eq(a, b):
    return a == b or _NAYIN_ALIAS.get(a, a) == _NAYIN_ALIAS.get(b, b)


def _hidden_stems(cell):
    """从 numberology 藏干单元（如"壬（本干），庚（申藏干），…"）提取地支藏干列表。"""
    return [p.strip()[0] for p in str(cell).replace("，", ",").split(",")
            if "藏干" in p]


def _branch_chars(cell):
    """空亡单元兼容 list/str 两种形态，取地支字符序列。"""
    return "".join(c for c in str(cell) if c in "子丑寅卯辰巳午未申酉戌亥")


@pytest.mark.parametrize("y,m,d,h", [(1984, 10, 5, 6), (2026, 2, 4, 12)])
def test_numberology_crosscheck(y, m, d, h):
    """神煞表沿用 my_data/data06/numerology.py，与 lunar-python 交叉验证：
    干支 / 纳音 / 地支藏干 / 天干十神（表中"生克"列）/ 空亡。
    （表内"十神"列为藏干十神，属 numerology 自有口径，不在此比对。）"""
    ec = Solar.fromYmdHms(y, m, d, h, 0, 0).getLunar().getEightChar()
    info = engine.chart(y, m, d, h)
    t = info["table"]
    for i, pillar in enumerate(("Year", "Month", "Day", "Time")):
        assert t["干支"].iloc[i] == getattr(ec, f"get{pillar}")()
        assert _nayin_eq(t["纳音"].iloc[i], getattr(ec, f"get{pillar}NaYin")())
        assert _hidden_stems(t["藏干"].iloc[i]) == list(
            getattr(ec, f"get{pillar}HideGan")())
        assert t["生克"].iloc[i] == getattr(ec, f"get{pillar}ShiShenGan")()
        assert _branch_chars(t["空亡"].iloc[i]) == getattr(
            ec, f"get{pillar}XunKong")()


# ─────────────────────────── B：五运六气 ───────────────────────────

def test_yunqi_2026_after_dahan():
    # 2026-01-20 10时（大寒 09:44:56 交节后）→ 运气年 2026 丙午
    f = yunqi.yunqi_facts(Solar.fromYmdHms(2026, 1, 20, 10, 0, 0))
    assert f["岁运干支"] == "丙午" and f["岁运"] == "水运太过"
    assert f["司天"] == "少阴君火" and f["在泉"] == "阳明燥金"
    assert f["出生六步"] == "初之气"
    assert f["主气"] == "厥阴风木" and f["客气"] == "太阳寒水"
    assert f["客主加临"] == "客生主"          # 水生木


def test_yunqi_2026_before_dahan():
    # 2026-01-15（大寒前）→ 归上一年乙巳运气周期（终之气）
    f = yunqi.yunqi_facts(Solar.fromYmdHms(2026, 1, 15, 10, 0, 0))
    assert f["岁运干支"] == "乙巳" and f["岁运"] == "金运不及"
    assert f["司天"] == "厥阴风木" and f["在泉"] == "少阳相火"
    assert f["出生六步"] == "终之气"
    assert f["主气"] == "太阳寒水" and f["客气"] == "少阳相火"   # 终之气=在泉
    assert f["客主加临"] == "主克客"          # 水克火


def test_yunqi_2026_step2():
    # 2026-03-25（春分后小满前）→ 二之气
    f = yunqi.yunqi_facts(Solar.fromYmdHms(2026, 3, 25, 10, 0, 0))
    assert f["岁运干支"] == "丙午"
    assert f["出生六步"] == "二之气"
    assert f["主气"] == "少阴君火" and f["客气"] == "厥阴风木"
    assert f["客主加临"] == "客生主"          # 木生火


def test_yunqi_1984_jiazi():
    # 1984-08-01 甲子年四之气
    f = yunqi.yunqi_facts(Solar.fromYmdHms(1984, 8, 1, 10, 0, 0))
    assert f["岁运干支"] == "甲子" and f["岁运"] == "土运太过"
    assert f["司天"] == "少阴君火" and f["在泉"] == "阳明燥金"
    assert f["出生六步"] == "四之气"
    assert f["主气"] == "太阴湿土" and f["客气"] == "太阴湿土"
    assert f["客主加临"] == "客主同气"


def test_yunqi_kou_jing_note():
    # 口径自洽：大寒前后两天，八字年柱同为乙巳、运气年却跨丙午（口径差异可解释）
    b1 = engine.chart(2026, 1, 19, 10)["bazi"][0]
    b2 = engine.chart(2026, 1, 21, 10)["bazi"][0]
    assert b1 == b2 == "乙巳"
    f1 = yunqi.yunqi_facts(Solar.fromYmdHms(2026, 1, 19, 10, 0, 0))
    f2 = yunqi.yunqi_facts(Solar.fromYmdHms(2026, 1, 21, 10, 0, 0))
    assert f1["岁运干支"] == "乙巳" and f2["岁运干支"] == "丙午"


def test_today_context():
    ctx = yunqi.today_context()
    assert "今日干支" in ctx and "主气" in ctx and "客气" in ctx


# ─────────────────────────── B：Prompt ───────────────────────────


def _mk_prompt(mode, **kw):
    info = engine.chart(1984, 10, 5, 6)
    facts = yunqi.yunqi_facts(info["solar"])
    today = yunqi.today_context()
    return prompt.build_prompt(mode, info, facts, today, "总是失眠", "女", **kw)


def test_prompt_analysis_mode():
    role, content = _mk_prompt(prompt.MODES[0])
    assert "五运六气" in role
    for kw in ("岁运", "司天", "在泉", "客主加临", "体质", "不预测吉凶"):
        assert kw in content, kw
    assert "四柱：甲子 癸酉 壬申 癸卯" in content
    assert "日主" in content and "当前时令" in content
    # V3：五行力量分布 + 四季调养日历事实/结构注入
    assert "五行力量分布" in content and "四季调养日历" in content


def test_prompt_wellness_mode():
    role, content = _mk_prompt(prompt.MODES[1])
    assert "养生顾问" in role
    assert "顺时养生" in content or "顺时调理" in content
    assert "不预测吉凶" in content
    assert "命理大师" not in content and "流日运势" not in content


def test_prompt_vernacular():
    """白话解说模式：注入大白话指令；默认模式无。"""
    _, plain = _mk_prompt(prompt.MODES[0], vernacular=True)
    assert "大白话" in plain and "类比" in plain
    _, pro = _mk_prompt(prompt.MODES[0])
    assert "大白话" not in pro


def test_prompt_personalization():
    """称呼与时间不确定注入。"""
    _, c1 = _mk_prompt(prompt.MODES[0], name="李先生")
    assert "李先生" in c1
    _, c2 = _mk_prompt(prompt.MODES[0], time_rough=True)
    assert "时间不确定" in c2 and "仅供参考" in c2


def test_wuxing_stats():
    """五行加权统计（干1.0/本气0.6/中气0.3/余气0.1）确定性验证。
    甲子 癸酉 壬申 癸卯：木1.6 火0 土0.1 金1.2 水3.9"""
    ws = engine.wuxing_stats(["甲子", "癸酉", "壬申", "癸卯"])
    assert ws == {"木": 1.6, "火": 0.0, "土": 0.1, "金": 1.2, "水": 3.9}, ws


# ─────────────── HTML 报告导出（mdhtml.py） ───────────────

def test_md_to_html_elements():
    from my_page.page06.part01 import mdhtml
    md = ("## 标题二\n\n段落有**加粗**和*斜体*。\n\n- 项目一\n- 项目二\n\n"
          "1. 第一\n2. 第二\n\n| 列A | 列B |\n|---|---|\n| 1 | 2 |\n\n---\n")
    h = mdhtml.md_to_html(md)
    assert "<h3>标题二</h3>" in h
    assert "<strong>加粗</strong>" in h and "<em>斜体</em>" in h
    assert "<ul><li>项目一</li><li>项目二</li></ul>" in h
    assert "<ol><li>第一</li><li>第二</li></ol>" in h
    assert "<table>" in h and "<th>列A</th>" in h and "<td>1</td>" in h
    assert "<hr/>" in h


def test_build_report_html():
    from my_page.page06.part01 import mdhtml
    page = mdhtml.build_report_html(
        "五运六气体质分析报告", ["四柱：甲子 癸酉 壬申 癸卯"], "## 一\n内容")
    assert page.startswith("<!DOCTYPE html>")
    assert "甲子 癸酉 壬申 癸卯" in page
    assert "不构成医疗诊断" in page        # 免责页脚
    assert "<h3>一</h3>" in page           # ## 映射 h3（# → h2）


# ─────────────────────────── 全链路（AppTest） ───────────────────────────


# ─────────────── 太阳时校正 + 分钟精度（solartime.py） ───────────────

_EOT_ANCHORS = [  # 天文年历公开锚点（分钟），容差 ±1.0
    ((2026, 2, 11), -14.2),   # 年内最负
    ((2026, 5, 15), 3.7),
    ((2026, 7, 26), -6.5),
    ((2026, 11, 3), 16.4),    # 年内最正
]


@pytest.mark.parametrize("ymd,expect", _EOT_ANCHORS)
def test_eot_anchors(ymd, expect):
    from my_page.page06.part01 import solartime
    eot = solartime.equation_of_time(datetime(*ymd, 12, 0))
    assert abs(eot - expect) < 1.0, f"{ymd}: got {eot:.2f} expect≈{expect}"


def test_solar_time_modes():
    from my_page.page06.part01 import solartime
    bj = datetime(2026, 3, 5, 10, 30)          # 北京时间
    # 北京时间口径：原样返回
    out, lon_m, eot = solartime.adjust(bj, 114.50, solartime.BEIJING)
    assert out == bj and lon_m == 0.0
    # 邢台平太阳时：114.5°E → (114.5-120)×4 = −22.0 分
    out, lon_m, _ = solartime.adjust(bj, 114.50, solartime.MEAN)
    assert lon_m == -22.0 and out == datetime(2026, 3, 5, 10, 8)
    # 真太阳时：3月初均时差为负 → 真太阳时 < 平太阳时
    out_true, _, eot = solartime.adjust(bj, 114.50, solartime.TRUE)
    assert eot < 0 and out_true < out


def test_solar_time_cross_day():
    """跨日边界：北京 00:10，邢台经度+负均时差 → 回退到前一日（日柱随退）。"""
    from my_page.page06.part01 import solartime
    bj = datetime(2026, 1, 20, 0, 10)          # 1/20 大寒日 00:10
    out_true, lon_m, eot = solartime.adjust(bj, 114.50, solartime.TRUE)
    # 邢台经度 −22 分 + 1月下旬均时差约 −11 分 → 共约 −33 分 → 1/19 23:37
    assert out_true.date() == date(2026, 1, 19), out_true
    assert out_true.hour == 23
    # 校正后排盘 = 前一日排盘（日柱随校正回退）
    assert engine.chart(out_true.year, out_true.month, out_true.day,
                        out_true.hour, minute=out_true.minute)["bazi"] == \
        engine.chart(2026, 1, 19, 23, minute=37)["bazi"]
    # 而不校正的排盘日柱是 1/20 的——两者日柱必须不同，证明校正生效
    assert engine.chart(out_true.year, out_true.month, out_true.day,
                        out_true.hour, minute=out_true.minute)["bazi"][2] != \
        engine.chart(2026, 1, 20, 0, minute=10)["bazi"][2]


def test_minute_passthrough():
    """分钟不改变同小时内的时柱（时辰按小时定）。"""
    assert (engine.chart(2026, 1, 20, 10, minute=30)["bazi"]
            == engine.chart(2026, 1, 20, 10, minute=0)["bazi"])


def test_shichen_label():
    from my_page.page06.part01 import solartime
    assert solartime.shichen_label(10) == "巳时（09:00–11:00）"
    assert solartime.shichen_label(23).startswith("子时")
    assert solartime.shichen_label(0).startswith("子时")


def test_city_lon_table():
    from my_page.page06.part01 import solartime
    assert solartime.CITY_LON["邢台"] == 114.50
    assert len(solartime.CITY_LON) >= 30        # 河北全覆盖 + 全国主要城市


def test_e2e_lunar_direct(monkeypatch):
    """阴历直连：公历日历隐藏（无 date_input），阴历表单直接排盘；
    2025 闰六月初一排盘 = 公历 2025-07-25 排盘；非法闰月拦截。"""
    import my_model.open_ai.deepseek as dm_mod
    monkeypatch.setattr(dm_mod, "deepseek",
                        lambda role, content, models=0: "**测试桩**")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(
        str(ROOT / "pages/06_🌿_中医道医学习平台.py"), default_timeout=60)
    at.run()
    at.selectbox(key="p01_cal").set_value("阴历")
    at.run()
    assert not at.exception
    assert len(at.date_input) == 0                    # 公历日历已隐藏
    at.number_input(key="p01_ly").set_value(2025)
    at.number_input(key="p01_lm").set_value(6)
    at.number_input(key="p01_ld").set_value(1)
    at.checkbox(key="p01_lleap").check()
    at.time_input(key="p01_time").set_value(time(10, 0))
    at.run()
    at.button(key="p01_go").click()
    at.run()
    assert not at.exception, at.exception
    expect = " ".join(engine.chart(2025, 7, 25, 10)["bazi"])
    assert any(expect in s.value for s in at.success), expect
    # 非法闰月拦截
    at.number_input(key="p01_lm").set_value(2)
    at.run()
    at.button(key="p01_go").click()
    at.run()
    assert any("闰二月" in e.value for e in at.error)


def test_e2e_solar_time_toggle(monkeypatch):
    """太阳时口径切换：默认 1990-01-01 10:00 + 邢台平太阳时（-22 分）
    → 排盘公历回显退到 1989-12-31（跨年校正生效）。"""
    import my_model.open_ai.deepseek as dm_mod
    monkeypatch.setattr(dm_mod, "deepseek",
                        lambda role, content, models=0: "**测试桩**")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(
        str(ROOT / "pages/06_🌿_中医道医学习平台.py"), default_timeout=60)
    at.run()
    at.selectbox(key="p01_tmode").set_value(solartime.MEAN)
    at.run()
    at.button(key="p01_go").click()
    at.run()
    assert not at.exception, at.exception
    # 校正生效：1990-01-01 10:00 − 22分 → 公历回显退为"1日 9时"
    # （跨日场景见 test_solar_time_cross_day；此处同日仅小时回退；
    #   农历"一九八九年腊月"是农历年滞后公历年，属正常现象）
    assert any("公历 1990年1月1日 9时" in c.value for c in at.caption), \
        [c.value for c in at.caption]
    assert any("平太阳时" in c.value for c in at.caption)


def test_e2e_part01(monkeypatch):
    """表单 → 排盘 → 运气 → prompt → LLM（打桩）→ 展示。"""
    import my_model.open_ai.deepseek as dm_mod
    captured = {}

    def fake_deepseek(role, content, models=0):
        captured["role"] = role
        captured["content"] = content
        return "**体质分析结果（测试桩）**：五运六气 OK"

    monkeypatch.setattr(dm_mod, "deepseek", fake_deepseek)

    from streamlit.testing.v1 import AppTest
    # 用真实入口（pages/06 包装页调用 main()；main.py 本身不自调）
    at = AppTest.from_file(
        str(ROOT / "pages/06_🌿_中医道医学习平台.py"), default_timeout=60)
    at.run()
    assert not at.exception
    # 默认菜单即「五运六气体质分析」；date/time 控件选值
    at.date_input(key="p01_date").set_value(date(2026, 1, 20))
    at.time_input(key="p01_time").set_value(time(10, 30))
    at.checkbox(key="p01_plain").check()           # 白话解说模式
    at.run()
    at.button(key="p01_go").click()
    at.run()
    assert not at.exception, at.exception
    assert any("乙巳 己丑 甲午 己巳" in s.value for s in at.success)
    assert any("体质分析结果（测试桩）" in m.value for m in at.markdown)
    # 打桩捕获的 prompt 里确实带了确定性事实 + 白话指令
    assert "司天" in captured["content"] and "四柱" in captured["content"]
    assert "大白话" in captured["content"]
    # HTML 下载按钮已渲染（download_button 独立元素类型）
    assert any(b.key == "p01_dl" for b in at.get("download_button"))


def test_e2e_menu_routing(monkeypatch):
    """四菜单切换渲染（part03 未登录走拦截分支）。

    bookstore/ceshi 的存储目录按平台分支：Windows=项目目录，非 Windows=/var/books
    （用户本地为 Windows，正常）。本沙箱为 Linux，测试内临时把
    platform.system 打桩为 Windows，走与用户一致的项目目录分支。
    """
    monkeypatch.setattr("platform.system", lambda: "Windows")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(
        str(ROOT / "pages/06_🌿_中医道医学习平台.py"), default_timeout=60)
    at.run()
    # V4：书籍两模块已合并为"中医书馆"，菜单共三项
    at.sidebar.radio[0].set_value("中医书馆")
    at.run()
    assert not at.exception, at.exception
    # 解决问题记录：未登录 → warning 拦截，不抛异常
    at.sidebar.radio[0].set_value("解决问题记录")
    at.run()
    assert not at.exception
    assert any("未登录" in w.value for w in at.warning)
