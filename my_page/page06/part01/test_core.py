"""page06/part01 测试：排盘引擎（A）+ 五运六气（B）+ prompt
+ 大运流年/日主强弱（C）+ key 管理（D）+ HTML 导出 + 太阳时。

独立版（fortune-app）本地单测：不依赖主平台页面（原 4 项 e2e 已随
test_part01_core.py 一并清理，页面级联调见 test_s6_integration.py）。
运行：cd fortune-app && python -m pytest my_page/page06/part01/test_core.py -q
"""
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]      # fortune-app/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import Solar, Lunar                          # noqa: E402
from my_page.page06.part01 import (                             # noqa: E402
    dayun, engine, prompt, solartime, yunqi)

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


# ───────────── C：大运流年 + 日主强弱（2026-10-07 大运流年功能 S1-S3） ─────────────

_NOW = datetime(2026, 10, 7, 12, 0)      # now 锚定（可复现，不随真实日期漂移）

# 顺/逆排 4 命例（年柱干支阴阳 × 性别，方案 2.1 实测锚定）
_DAYUN_CASES = [
    # (y, m, d, h, mi), gender, 排法, 大运前 3 步干支, 起运虚岁
    ((1990, 1, 15, 10, 30), 1, "阴男逆排", ["丙子", "乙亥", "甲戌"], 4),
    ((1990, 1, 15, 10, 30), 0, "阴女顺排", ["戊寅", "己卯", "庚辰"], 7),
    ((1984, 10, 5, 6, 0), 1, "阳男顺排", ["甲戌", "乙亥", "丙子"], 2),
    ((1984, 10, 5, 6, 0), 0, "阳女逆排", ["壬申", "辛未", "庚午"], 10),
]


@pytest.mark.parametrize("args,gender,pai,seq,start_age", _DAYUN_CASES)
def test_dayun_direction(args, gender, pai, seq, start_age):
    y, m, d, h, mi = args
    f = dayun.dayun_facts(Solar.fromYmdHms(y, m, d, h, mi, 0), gender, now=_NOW)
    assert f["起运"]["排法"] == pai
    assert f["起运"]["起运虚岁"] == start_age
    assert [s["干支"] for s in f["大运"][:3]] == seq
    assert len(f["大运"]) == 9                    # 10 步含起运前段，干支步 9
    assert [s["序"] for s in f["大运"]] == list(range(1, 10))


def test_dayun_1990_male_anchor():
    """方案 2.1/3.1 标准命例全量锚定（己巳丁丑庚辰辛巳，男，now=2026）。"""
    f = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0),
                          1, now=_NOW)
    q = f["起运"]
    assert q["交运时刻"] == "1993年3月15日 10:30"
    assert q["出生后"] == "出生后 3 年 2 个月"
    assert q["流派"] == "3天折1年（传统）"
    cur = f["当前大运"]
    assert cur["干支"] == "癸酉" and cur["序"] == 4
    assert (cur["起年"], cur["止年"], cur["起岁"], cur["止岁"]) == \
        (2023, 2032, 34, 43)
    assert cur["十神"] == "伤官"                    # 庚日主见癸
    assert cur["纳音"] == "剑锋金" and cur["五行"] == "水金"
    assert cur["当前"] and cur["备注"] == "当前 ★"
    assert [s["干支"] for s in f["未来大运"]] == ["壬申", "辛未"]
    fut = {s["干支"]: s for s in f["未来大运"]}
    assert fut["壬申"]["十神"] == "食神" and fut["壬申"]["纳音"] == "剑锋金"
    assert fut["辛未"]["纳音"] == "路旁土" and fut["辛未"]["五行"] == "金土"
    assert f["大运"][4]["备注"] == "换运年 2033"    # 序 5 壬申起年
    # 当前大运流年：当前步管辖 10 流年；虚岁口径 = 公历年差 + 1
    assert len(f["当前大运流年"]) == 10
    assert [r["年"] for r in f["当前大运流年"]] == list(range(2023, 2033))
    assert [r["虚岁"] for r in f["当前大运流年"]] == list(range(34, 44))
    # 近期流年（当前年 ±3）：2023-2029，2026 为当前年
    near = {r["年"]: r for r in f["近期流年"]}
    assert sorted(near) == list(range(2023, 2030))
    assert near[2026]["当前"] and near[2026]["备注"] == "当前年 ★"
    assert near[2026]["干支"] == "丙午" and near[2026]["十神"] == "七杀"
    assert near[2026]["虚岁"] == 37               # 2026 − 1990 + 1
    assert near[2023]["备注"] == "换运年"          # 癸酉步起年


def test_dayun_liuchun_boundary():
    """立春分界：年柱（→顺逆排）与流年干支（→立春界）双验证。"""
    # 2026-02-03（乙巳年）vs 2026-02-04 12时（立春交节后，丙午年）男命
    a = dayun.dayun_facts(Solar.fromYmdHms(2026, 2, 3, 12, 0, 0), 1, now=_NOW)
    b = dayun.dayun_facts(Solar.fromYmdHms(2026, 2, 4, 12, 0, 0), 1, now=_NOW)
    assert a["起运"]["排法"] == "阴男逆排" and a["大运"][0]["干支"] == "戊子"
    assert b["起运"]["排法"] == "阳男顺排" and b["大运"][0]["干支"] == "辛卯"
    for f in (a, b):                              # 2026 立春前出生，流年仍丙午
        near = {r["年"]: r["干支"] for r in f["近期流年"]}
        assert near[2026] == "丙午"
    # 流年干支与独立立春界锚点交叉验证（1990 男命，2023-2029 全覆盖）
    f90 = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0), 1, now=_NOW)
    near = {r["年"]: r["干支"] for r in f90["近期流年"]}
    for y in range(2023, 2030):
        anchor = Solar.fromYmdHms(y, 7, 1, 12, 0, 0).getLunar() \
            .getYearInGanZhiByLiChun()           # 7 月远离开年边界，锚点安全
        assert near[y] == anchor, y


def test_dayun_now_anchor_reproducible():
    """now 锚定可复现：同公历年一致；跨步边界当前标记正确迁移。"""
    s = Solar.fromYmdHms(1990, 1, 15, 10, 30, 0)
    f1 = dayun.dayun_facts(s, 1, now=datetime(2026, 10, 7, 12, 0))
    f2 = dayun.dayun_facts(s, 1, now=datetime(2026, 10, 7, 20, 0))
    assert f1 == f2                               # 同公历年 → 输出逐字段一致
    assert dayun.dayun_facts(s, 1, now=datetime(2032, 6, 1))["当前大运"][
        "干支"] == "癸酉"                          # 止年含 2032
    assert dayun.dayun_facts(s, 1, now=datetime(2033, 6, 1))["当前大运"][
        "干支"] == "壬申"                          # 2033 已换运


def test_dayun_before_start_child():
    """未交运（index 0 段）：当前大运 None、未来=前两步、起运前仍带流年。"""
    f = dayun.dayun_facts(Solar.fromYmdHms(2024, 6, 15, 10, 0, 0), 1, now=_NOW)
    assert f["当前大运"] is None and f["当前大运流年"] == []
    assert not any(s["当前"] for s in f["大运"])
    assert [s["干支"] for s in f["未来大运"]] == ["辛未", "壬申"]
    near = {r["年"]: r["干支"] for r in f["近期流年"]}
    assert near.get(2024) == "甲辰" and near.get(2026) == "丙午"
    assert 2023 not in near                        # 出生前年份不入流年


def test_dayun_sect2_and_gender_norm():
    """sect=2 精确折算（交运时刻不同、干支序列一致）；gender 容错。"""
    f1 = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0),
                           "男", now=_NOW)
    f2 = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0),
                           1, sect=2, now=_NOW)
    assert f1["起运"]["流派"] == "3天折1年（传统）"
    assert f2["起运"]["流派"] == "按分钟精确折算"
    assert f2["起运"]["交运时刻"] == "1993年3月17日 04:30"
    assert [s["干支"] for s in f2["大运"]] == [s["干支"] for s in f1["大运"]]
    with pytest.raises(ValueError, match="gender"):
        dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0),
                          "x", now=_NOW)


def test_dayun_limit_truncation():
    """limit 截断"大运"列表；当前判定与起运虚岁不受截断影响。"""
    f = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0), 1,
                          limit=3, now=_NOW)
    assert [s["序"] for s in f["大运"]] == [1, 2, 3]
    assert f["当前大运"]["干支"] == "癸酉" and f["当前大运"]["序"] == 4
    assert f["起运"]["起运虚岁"] == 4


def test_dayun_contract_serializable():
    """接口契约（方案 2.3）：结构完整 + 全 primitives（可 JSON 序列化）。"""
    import json
    f = dayun.dayun_facts(Solar.fromYmdHms(1990, 1, 15, 10, 30, 0), 1, now=_NOW)
    json.dumps(f, ensure_ascii=False)              # 不抛即通过
    assert set(f) == {"起运", "大运", "当前大运", "未来大运",
                      "当前大运流年", "近期流年"}
    step_keys = {"序", "干支", "十神", "纳音", "五行", "起年", "止年",
                 "起岁", "止岁", "流年数", "当前", "备注"}
    assert all(set(s) == step_keys for s in f["大运"])
    assert set(f["当前大运"]) == step_keys


def test_day_master_strength():
    """日主强弱三要素粗判（Q9）：得令/得地/得势锚定。"""
    # 甲子 癸酉 壬申 癸卯：壬水得令（酉月本气金生水）、得地（申藏壬水）、
    # 得势（水3.9+金1.2=5.1/6.8）→ 偏强，喜木（泄）土（制）
    st = engine.day_master_strength(["甲子", "癸酉", "壬申", "癸卯"])
    assert (st["得令"], st["得地"], st["得势"]) == (True, True, True)
    assert st["粗判"] == "偏强"
    assert st["喜用倾向"] == "木（食伤泄秀）、土（官杀制衡）"
    assert st["同党权重"] == "5.1/6.8（约 75%）"
    # 己巳 丁丑 庚辰 辛巳：庚金得令（丑月本气土生金）、失地（辰无金）、
    # 得势（金2.7+土2.4=5.1/8.0）→ 偏强，喜水（泄）火（制）
    st2 = engine.day_master_strength(["己巳", "丁丑", "庚辰", "辛巳"])
    assert (st2["得令"], st2["得地"], st2["得势"]) == (True, False, True)
    assert st2["粗判"] == "偏强"
    assert st2["喜用倾向"] == "水（食伤泄秀）、火（官杀制衡）"
    # 丁巳 丙午 甲申 庚午：甲木夏生，火旺泄气，三要素全失 → 偏弱
    st3 = engine.day_master_strength(["丁巳", "丙午", "甲申", "庚午"])
    assert (st3["得令"], st3["得地"], st3["得势"]) == (False, False, False)
    assert st3["粗判"] == "偏弱"
    assert st3["喜用倾向"] == "水（印绶生扶）、木（比劫帮扶）"
    # 丙寅 庚寅 甲午 庚午：甲木得令（寅月本气木）、失地（午无木）、
    # 失势（木2.2/7.8）→ 中和（单项）
    st4 = engine.day_master_strength(["丙寅", "庚寅", "甲午", "庚午"])
    assert (st4["得令"], st4["得地"], st4["得势"]) == (True, False, False)
    assert st4["粗判"] == "中和"
    assert st4["喜用倾向"] == "无明显喜忌，以五行流通为要"


def _mk_prompt_dy(mode, with_dayun=True, **kw):
    """大运流年版 prompt 组装（S3：dayun + strength 注入，now 锚定）。"""
    info = engine.chart(1990, 1, 15, 10, minute=30)
    facts = yunqi.yunqi_facts(info["solar"])
    today = yunqi.today_context()
    dy = dayun.dayun_facts(info["solar"], 1, now=_NOW) if with_dayun else None
    st = engine.day_master_strength(info["bazi"])
    return prompt.build_prompt(mode, info, facts, today, "最近睡不好", "男",
                               dayun=dy, strength=st, **kw)


def test_prompt_dayun_injection():
    """S3：大运流年事实段 + 日主强弱粗判注入 head（分析师模式）。"""
    _, c = _mk_prompt_dy(prompt.MODES[0])
    assert "大运流年事实" in c and "以立春分界" in c
    assert "起运：出生后 3 年 2 个月交运（1993年3月15日 10:30）" in c
    assert "阴男逆排（3天折1年（传统））" in c
    assert "当前大运：癸酉（伤官/剑锋金），34-43 虚岁（2023-2032），第 4 步" in c
    assert "未来大运：壬申（食神/剑锋金），44-53 虚岁（2033-2042）" in c
    assert "2023 癸卯（伤官）" in c and "2029 己酉（正印）" in c
    assert "2026 丙午（七杀，当前年）" in c
    assert "日主强弱粗判" in c and "粗判**偏强**" in c and "喜用倾向" in c


def test_prompt_dayun_sections():
    """S3：报告新增独立节三，原三~六节顺延为四~七节。"""
    _, c = _mk_prompt_dy(prompt.MODES[0])
    assert "七个部分" in c and "六个部分" not in c
    secs = ["一、出生运气禀赋解读", "二、日主与五行体质",
            "三、大运流年与体质走向", "四、体质特征与易感倾向",
            "五、顺时养生方案", "六、四季调养日历", "七、心理疏导与赋能"]
    for sec in secs:
        assert sec in c, sec
    for i in range(len(secs) - 1):                # 节序单调递增
        assert c.index(secs[i]) < c.index(secs[i + 1])
    assert "换运年（2033）前后体质节奏的变化提示" in c


def test_prompt_dayun_redline_and_wellness():
    """S3：红线强化句；顾问模式注入并并入第一节，原四部分结构保持。"""
    _, c = _mk_prompt_dy(prompt.MODES[0])
    assert "禁止吉凶祸福、事业财运、婚恋子女等命运断言" in c
    _, w = _mk_prompt_dy(prompt.MODES[1])
    assert "大运流年事实" in w and "当前大运" in w
    assert "阶段性体质背景" in w                # 并入第一节，不单独成节
    assert "三、行动清单" in w and "四、心理疏导与赋能" in w
    assert "婚恋子女等命运断言" in w                # 顾问模式红线同样强化


def test_prompt_dayun_time_rough():
    """S3：time_rough + dayun → 起运交运日期偏差局限性说明（R2）。"""
    _, c = _mk_prompt_dy(prompt.MODES[0], time_rough=True)
    assert "时间不确定" in c and "仅供参考" in c
    assert "数天至数月偏差" in c


def test_prompt_dayun_before_start():
    """未交运命例：prompt 渲染"尚未交运"行，不抛异常。"""
    info = engine.chart(2024, 6, 15, 10)
    facts = yunqi.yunqi_facts(info["solar"])
    today = yunqi.today_context()
    dy = dayun.dayun_facts(info["solar"], 1, now=_NOW)
    _, c = prompt.build_prompt(prompt.MODES[0], info, facts, today,
                               "孩子体质", "男", dayun=dy)
    assert "尚未交运，2031 年起进入第一步大运 辛未" in c


def test_prompt_without_dayun_backward_compat():
    """不传 dayun/strength（旧调用/主平台同步）→ V3 六节结构与原输出不变。"""
    _, c = _mk_prompt(prompt.MODES[0])
    assert "大运流年事实" not in c and "日主强弱粗判" not in c
    assert "六个部分" in c and "三、大运流年与体质走向" not in c
    for sec in ("三、体质特征与易感倾向", "四、顺时养生方案",
                "五、四季调养日历", "六、心理疏导与赋能"):
        assert sec in c, sec
    assert "七、心理疏导与赋能" not in c


# ───────────── D：DeepSeek key 管理（2026-10-07 P1-1） ─────────────

def test_deepseek_key_env_priority(monkeypatch):
    """key 读取：环境变量 DEEPSEEK_API_KEY 优先（不真实调用 API）。"""
    from my_model.open_ai import deepseek as ds
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-env-key")
    assert ds.api_key_or_none() == "sk-test-env-key"


def test_deepseek_key_missing_error(monkeypatch):
    """未配置 key → RuntimeError 带配置指引（analyze.py 兜底分支承接）。"""
    from my_model.open_ai import deepseek as ds
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    if ds.api_key_or_none():          # 运行环境已配置（如用户本地）→ 不适用
        pytest.skip("DEEPSEEK_API_KEY 已配置，跳过缺失场景")
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        ds.deepseek()


def test_deepseek_no_hardcoded_key():
    """源码无硬编码 key（P1-1 回归红线：key 不进源码）。"""
    src = Path(ROOT / "my_model/open_ai/deepseek.py").read_text(encoding="utf-8")
    assert "sk-d068fc" not in src
    assert 'api_key="' not in src.replace('api_key=key', '')


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
