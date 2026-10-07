"""page06/part01 · S6 联调收口测试（2026-10-07）：独立版真实入口
fortune.py 的全链路 AppTest（LLM 打桩 + mdhtml 边界捕获）+ 缓存命中验证。

范围（S6 验收任务书）：
1. 全链路：已交运 / 未交运 / 时辰不确定 + 阴阳男女顺逆排 4 命例，
   断言页面表格（大运总表 / 流年明细）、prompt 大运流年事实注入、
   附录 A-E 组装无异常（捕获真实送入下载按钮的报告 HTML 检查
   开合默认、当前★高亮、换运年标注、口径说明与免责）；
2. 缓存命中：同输入重复运行，排盘 / 大运 / LLM 三层缓存均命中，
   不重复计算（引擎与 LLM 调用计数为证）。

打桩说明：AppTest 的 download_button 元素不暴露下载数据（proto 走
deferred file），故在 mdhtml.build_report_html 边界旁路捕获（返回值
原样透传，页面下载按钮收到的仍是真实 HTML，行为零改动）。
原 4 项依赖主平台 pages/06_*.py 的存量 e2e（及旧副本
test_part01_core.py）已于 2026-10-07 清理，本文件为唯一页面级联调入口。

断言基线（2026-10-07 用户版行为，同步记录）：
- 命盘综合表/五运六气改 st.table（折叠 expander 内），不计入
  at.dataframe → 大运总表/流年明细索引为 [0]/[1]（原 [1]/[2]）；
- 大区块 expander 标题加粗（如 "**大运流年**"）；
- 防爬闸门改为「默认示例值 1990-01-01 10:00 未修改禁提交」（第 6 节）。

运行：cd fortune-app && python -m pytest my_page/page06/part01/test_s6_integration.py -q
"""
import sys
from datetime import date, time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]      # fortune-app/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import my_model.open_ai.deepseek as dm                       # noqa: E402
from my_page.page06.part01 import (                          # noqa: E402
    analyze, dayun, engine, mdhtml, solartime)
from streamlit.testing.v1 import AppTest, AppTestError     # noqa: E402

APP = ROOT / "fortune.py"

_LLM_STUB = ("**一、出生运气禀赋解读**（S6 测试桩）……\n\n"
             "### 三、大运流年与体质走向\n体质环境倾向提示。")

_APX_TITLES = ("附录 A · 命盘综合表", "附录 B · 出生当年五运六气",
               "附录 C · 大运总表", "附录 D · 当前大运流年表",
               "附录 E · 排盘口径说明")


def _clear_caches():
    analyze._cached_chart.clear()
    analyze._cached_dayun.clear()
    analyze._cached_llm.clear()


@pytest.fixture(autouse=True)
def _fresh_caches():
    """每用例前后清三层缓存：避免跨用例同输入缓存命中吞掉打桩/计数。"""
    _clear_caches()
    yield
    _clear_caches()


@pytest.fixture
def llm_spy(monkeypatch):
    """LLM 打桩：记录调用次数与真实送出的 prompt，返回固定桩文本。"""
    box = {"n": 0, "role": "", "content": "", "models": None}

    def _fake(role="x", content="y", models=0):
        box["n"] += 1
        box["role"], box["content"], box["models"] = role, content, models
        return _LLM_STUB

    monkeypatch.setattr(dm, "deepseek", _fake)
    return box


@pytest.fixture
def html_capture(monkeypatch):
    """捕获真实送入下载按钮的报告 HTML（mdhtml 边界旁路，原值透传）。"""
    box = {}
    _orig = mdhtml.build_report_html

    def _wrap(title, meta, result_md, appendices=None):
        html_text = _orig(title, meta, result_md, appendices)
        box.update(html=html_text, meta=list(meta), title=title,
                   result_md=result_md, appendices=appendices)
        return html_text

    monkeypatch.setattr(mdhtml, "build_report_html", _wrap)
    return box


def _run_app(y, m, d, hh, mm, sex="男", rough=False, tmode=None):
    """走独立版真实入口 fortune.py。默认选北京时间口径（与单元锚点
    一致、不做经度校正）；tmode=None 时保留页面默认（平太阳时·邢台），
    用于覆盖默认口径路径。"""
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    if tmode is not None:
        at.selectbox(key="p01_tmode").set_value(tmode)
    if sex == "女":
        at.selectbox(key="p01_sex").set_value("女")
    if rough:
        at.checkbox(key="p01_rough").check()
    at.date_input(key="p01_date").set_value(date(y, m, d))
    at.time_input(key="p01_time").set_value(time(hh, mm))
    at.run()
    at.button(key="p01_go").click()
    at.run()
    return at


# ─────────── 1. 已交运男命：页面 / prompt / 附录全量断言 ───────────


def test_s6_e2e_full_1990_male(llm_spy, html_capture):
    """1990-01-15 10:30 男（阴男逆排，2026 已交运第 4 步癸酉）：
    页面三表 + 交运 caption + prompt 注入 + 附录 A-E 全量走查。"""
    at = _run_app(1990, 1, 15, 10, 30, "男", tmode=solartime.BEIJING)
    assert not at.exception, [e.value for e in at.exception]

    # ── 页面：排盘与大运流年区块 ──
    assert [s.value for s in at.success] == ["四柱：己巳 丁丑 庚辰 辛巳"]
    assert any("大运流年" in m.value for m in at.markdown)
    cap = " ｜ ".join(c.value for c in at.caption)
    assert ("起运：出生后 3 年 2 个月交运（1993年3月15日 10:30），"
            "起运虚岁 4｜阴男逆排") in cap
    assert "当前第 4 步大运 癸酉（伤官｜剑锋金），34-43 虚岁（2023-2032）" in cap
    assert any(b.key == "p01_dl" for b in at.get("download_button"))

    # 命盘综合表/五运六气改 st.table（折叠 expander 内，用户版 2026-10-07）：
    # 不计入 at.dataframe，且区块标题加粗
    assert len(at.get("table")) == 2
    labels = [e.label for e in at.expander]
    assert "**命盘综合表**" in labels and "**出生当年五运六气**" in labels
    assert "**大运流年**" in labels and "**当前大运 · 十年流年明细**" in labels

    # 大运总表（表 C）：起运前段 + 9 干支步；当前★ / 换运年标注
    d1 = at.dataframe[0].value
    assert list(d1.columns) == ["序", "起止虚岁", "起止公历", "大运干支",
                               "天干十神", "纳音", "五行", "备注"]
    assert len(d1) == 10
    assert d1.iloc[0]["序"] == "—"
    assert d1.iloc[0]["大运干支"] == "—（出生至起运）"
    assert d1.iloc[0]["备注"] == "起运前"
    gz = dict(zip(d1["序"], d1["大运干支"]))
    note = dict(zip(d1["序"], d1["备注"]))
    assert gz["1"] == "丙子" and gz["4"] == "癸酉"
    assert note["1"] == "换运年 1993"
    assert note["4"] == "当前 ★"
    assert note["5"] == "换运年 2033"
    assert (d1["备注"] == "换运年 1993").sum() == 1

    # 当前大运十年流年（表 D，expander 内）：2023-2032，当前年★
    d2 = at.dataframe[1].value
    assert list(d2.columns) == ["公历年", "虚岁", "流年干支", "天干十神",
                               "纳音", "备注"]
    assert list(d2["公历年"]) == list(range(2023, 2033))
    ln = d2.set_index("公历年")
    assert ln.loc[2026, "流年干支"] == "丙午"
    assert ln.loc[2026, "天干十神"] == "七杀"
    assert ln.loc[2026, "备注"] == "当前年 ★"
    assert ln.loc[2023, "备注"] == "换运年"

    # ── prompt：大运流年事实 / 日主强弱 / 红线强化（送 LLM 的真实内容）──
    c = llm_spy["content"]
    assert llm_spy["models"] == 0                      # 深度模型默认关
    assert "**大运流年事实**" in c and "以立春分界" in c
    assert "起运：出生后 3 年 2 个月交运（1993年3月15日 10:30）" in c
    assert "阴男逆排（3天折1年（传统））" in c
    assert "当前大运：癸酉（伤官/剑锋金），34-43 虚岁（2023-2032），第 4 步" in c
    assert "未来大运：壬申（食神/剑锋金），44-53 虚岁（2033-2042）" in c
    assert "2026 丙午（七杀，当前年）" in c
    assert "日主强弱粗判" in c
    assert "七个部分" in c
    assert "### 三、大运流年与体质走向" in c
    assert "换运年（2033）前后体质节奏的变化提示" in c
    assert "禁止吉凶祸福、事业财运、婚恋子女等命运断言" in c
    assert any("S6 测试桩" in m.value for m in at.markdown)   # 桩正文渲染

    # ── 附录 HTML（真实送入下载按钮的内容）──
    html = html_capture["html"]
    for t in _APX_TITLES:
        assert t in html, t
    assert html.count("<details open>") == 0          # C/D 改为默认收起
    assert html.count("<details>") == 5               # A-E 全部默认收起
    assert "<strong>当前 ★</strong>" in html          # C 当前步高亮
    assert "<strong>当前年 ★</strong>" in html        # D 当前年高亮
    assert "换运年 2033" in html
    assert "换运年 = 大运交接之年" in html
    for kw in ("虚岁", "立春", "大寒", "3天折1年", "出生至起运"):
        assert kw in html, kw                          # E 口径要素
    assert "性别：男" in html and "1990年1月15日" in html
    assert "四柱：己巳 丁丑 庚辰 辛巳（日主 庚）" in html
    assert "排盘口径：北京时间" in html
    assert "不构成医疗诊断，不预测吉凶" in html         # 页脚免责
    assert "不预测吉凶祸福；健康问题请线下就医" in html  # 附录 E 免责
    apx = html_capture["appendices"]
    assert [a["title"] for a in apx] == list(_APX_TITLES)
    assert [a["open"] for a in apx] == [False, False, False, False, False]


# ─────────── 2. 阴阳男女 × 顺逆排 4 命例（页面 + prompt + 附录）──


_S6_CASES = [
    # (y,m,d,h,mi), sex, 排法, 前3步干支, 起运虚岁, 当前大运, 当前序
    ((1990, 1, 15, 10, 30), "男", "阴男逆排",
     ["丙子", "乙亥", "甲戌"], 4, "癸酉", 4),
    ((1990, 1, 15, 10, 30), "女", "阴女顺排",
     ["戊寅", "己卯", "庚辰"], 7, "辛巳", 4),
    ((1984, 10, 5, 6, 0), "男", "阳男顺排",
     ["甲戌", "乙亥", "丙子"], 2, "戊寅", 5),
    ((1984, 10, 5, 6, 0), "女", "阳女逆排",
     ["壬申", "辛未", "庚午"], 10, "己巳", 4),
]


@pytest.mark.parametrize("args,sex,pai,seq3,start_age,cur_gz,cur_seq", _S6_CASES)
def test_s6_e2e_direction_matrix(args, sex, pai, seq3, start_age, cur_gz,
                                 cur_seq, llm_spy, html_capture):
    """阴阳男女顺逆排典型命例：页面排法/干支序列、prompt 注入与
    附录 C 干支逐例核对（2026 年均已交运）。"""
    y, m, d, h, mi = args
    at = _run_app(y, m, d, h, mi, sex=sex, tmode=solartime.BEIJING)
    assert not at.exception, [e.value for e in at.exception]

    cap = " ｜ ".join(c.value for c in at.caption)
    assert pai in cap and f"起运虚岁 {start_age}" in cap
    assert f"当前第 {cur_seq} 步大运 {cur_gz}" in cap

    d1 = at.dataframe[0].value                     # 命盘综合表改 st.table 后为 [0]
    gz = dict(zip(d1["序"], d1["大运干支"]))
    for i, g in enumerate(seq3):
        assert gz[str(i + 1)] == g, (pai, i + 1, g)
    note = dict(zip(d1["序"], d1["备注"]))
    assert note[str(cur_seq)] == "当前 ★"

    d2 = at.dataframe[1].value                     # 已交运 → 有流年明细
    assert (d2["备注"] == "当前年 ★").sum() == 1

    c = llm_spy["content"]
    assert f"{pai}（3天折1年（传统））" in c
    assert f"- 当前大运：{cur_gz}（" in c
    assert "未来大运：" in c and "近期流年（当前年前后 3 年）" in c

    html = html_capture["html"]
    for t in _APX_TITLES:
        assert t in html, t
    for g in seq3:
        assert g in html, g
    assert "<strong>当前 ★</strong>" in html
    assert "<strong>当前年 ★</strong>" in html


# ─────────── 3. 未交运（儿童命例）───────────


def test_s6_e2e_before_start_2024(llm_spy, html_capture):
    """2024-06-15 男（2031 起运，未交运）：无流年明细表、caption 与
    prompt 渲染"尚未交运"、附录 D 以文字说明替代、无当前★标注。"""
    at = _run_app(2024, 6, 15, 10, 0, sex="男", tmode=solartime.BEIJING)
    assert not at.exception, [e.value for e in at.exception]

    assert len(at.dataframe) == 1                   # 仅大运总表（无流年明细）
    assert len(at.get("table")) == 2                # 命盘综合表 + 五运六气照常
    assert "**当前大运 · 十年流年明细**" not in [e.label for e in at.expander]
    cap = " ｜ ".join(c.value for c in at.caption)
    assert "尚未交运：2031 年（虚岁 8）起进入第一步大运 辛未（劫财）" in cap

    c = llm_spy["content"]
    assert "尚未交运，2031 年起进入第一步大运 辛未" in c

    html = html_capture["html"]
    for t in _APX_TITLES:
        assert t in html, t
    assert "尚未交运：2031 年（虚岁 8）起进入第一步大运 辛未（劫财）" in html
    assert "<strong>当前 ★</strong>" not in html
    assert "<strong>当前年 ★</strong>" not in html


# ─────────── 4. 时辰不确定（默认平太阳时口径一并覆盖）───────────


def test_s6_e2e_time_rough_default_mean_time(llm_spy, html_capture):
    """时辰不确定（R2）+ 页面默认口径（平太阳时·邢台）：经度校正
    -22 分钟进入交运时刻（口径同源验证）、偏差提示与附录 E 说明。"""
    at = _run_app(1990, 1, 15, 10, 30, sex="男", rough=True)
    assert not at.exception, [e.value for e in at.exception]

    cap = " ｜ ".join(c.value for c in at.caption)
    assert "起运：出生后 3 年 2 个月交运（1993年3月15日 10:08），起运虚岁 4" in cap
    assert "出生时间不确定，起运与交运日期仅供参考（误差可达数月）" in cap

    c = llm_spy["content"]
    assert "时间不确定" in c and "仅供参考" in c
    assert "数天至数月偏差" in c

    html = html_capture["html"]
    assert "出生时间不确定：时柱与起运交运日期仅供参考" in html
    assert "<strong>当前 ★</strong>" in html        # 已交运照常高亮
    assert "平太阳时" in html                        # 默认口径入 meta/附录


# ─────────── 5. 缓存命中：同输入重复运行不重复计算 ───────────


def test_s6_e2e_cache_hit(monkeypatch, llm_spy, html_capture):
    """同输入二次点击生成：排盘 / 大运 / LLM 三层缓存全部命中，
    引擎与 LLM 调用计数不增长（不重复计算、不重复计费）。"""
    calls = {"chart": 0, "dayun": 0}
    _chart, _dy_facts = engine.chart, dayun.dayun_facts

    def chart_spy(*a, **kw):
        calls["chart"] += 1
        return _chart(*a, **kw)

    def dayun_spy(*a, **kw):
        calls["dayun"] += 1
        return _dy_facts(*a, **kw)

    monkeypatch.setattr(engine, "chart", chart_spy)
    monkeypatch.setattr(dayun, "dayun_facts", dayun_spy)

    at = _run_app(1990, 1, 15, 10, 30, sex="男", tmode=solartime.BEIJING)
    assert not at.exception
    assert calls == {"chart": 1, "dayun": 1}
    assert llm_spy["n"] == 1

    at.button(key="p01_go").click()                 # 同输入再次生成
    at.run()
    assert not at.exception
    assert calls == {"chart": 1, "dayun": 1}        # 缓存命中：零重算
    assert llm_spy["n"] == 1                        # LLM 不重复计费
    assert any("S6 测试桩" in m.value for m in at.markdown)
    assert html_capture["html"]                     # 附录组装照常完成
    assert html_capture["html"].count("<details open>") == 0  # C/D 默认收起


# ─────────── 6. 防爬闸门（默认示例值禁提交，用户版 2026-10-07）───────────


def test_s6_gate_default_birth_blocked(llm_spy):
    """默认示例值未修改（阳历/阴历两分支）：warning 指引 + 提交按钮
    禁用，排盘/LLM 均不触发（爬虫默认值直提被拦，不耗 token）。"""
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    # 阳历分支：默认 1990-01-01 10:00
    assert any("仍是默认示例值（1990-01-01 10:00）" in w.value
               for w in at.warning)
    with pytest.raises(AppTestError, match="disabled"):
        at.button(key="p01_go").click()
    assert llm_spy["n"] == 0                        # LLM 零调用
    assert len(at.success) == 0                     # 未进排盘路径
    # 阴历分支：默认 1990 年正月初一 10:00
    at.selectbox(key="p01_cal").set_value("阴历")
    at.run()
    assert any("仍是默认示例值（1990年正月初一 10:00）" in w.value
               for w in at.warning)
    with pytest.raises(AppTestError, match="disabled"):
        at.button(key="p01_go").click()
    assert llm_spy["n"] == 0


def test_s6_gate_modified_birth_ok(llm_spy, html_capture):
    """修改任一出生输入（仅改日期、时间仍默认）：闸门解除，
    全链路照常出结果（防爬不误伤真人）。"""
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    at.date_input(key="p01_date").set_value(date(1990, 1, 15))
    at.run()
    assert not [w for w in at.warning if "默认示例值" in w.value]
    at.button(key="p01_go").click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert [s.value for s in at.success] == ["四柱：己巳 丁丑 庚辰 辛巳"]
    assert llm_spy["n"] == 1
    assert html_capture["html"]
