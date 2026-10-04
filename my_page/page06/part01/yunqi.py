"""page06/part01 · 五运六气推算（2026-09-25 B 项）。

口径（页面 caption 同步复述，属运气学与八字的不同分界，均为传统口径）：
- 运气年以【大寒】交司分界：出生在大寒前 → 归上一年运气周期（终之气）
- 八字年柱以【立春】分界（见 engine.py）——两者不同属正常口径差异
- 六步主气固定起于大寒；客气按年支定司天（三之气=司天、终之气=在泉）

数据依据：《黄帝内经·素问》天元纪大论/六微旨大论等七篇大论的通行推算法。
"""
from datetime import datetime

from lunar_python import Solar

# ── 岁运（中运）：年干定五行，阳干太过、阴干不及 ──
SUI_YUN = {
    "甲": ("土运", "太过"), "己": ("土运", "不及"),
    "乙": ("金运", "不及"), "庚": ("金运", "太过"),
    "丙": ("水运", "太过"), "辛": ("水运", "不及"),
    "丁": ("木运", "不及"), "壬": ("木运", "太过"),
    "戊": ("火运", "太过"), "癸": ("火运", "不及"),
}

# ── 司天（年支 → 上半年主客气）/ 在泉（表里配对）──
SI_TIAN = {
    "子": "少阴君火", "午": "少阴君火", "丑": "太阴湿土", "未": "太阴湿土",
    "寅": "少阳相火", "申": "少阳相火", "卯": "阳明燥金", "酉": "阳明燥金",
    "辰": "太阳寒水", "戌": "太阳寒水", "巳": "厥阴风木", "亥": "厥阴风木",
}
ZAI_QUAN = {  # 司天在上、在泉在下，固定表里配对
    "少阴君火": "阳明燥金", "阳明燥金": "少阴君火",
    "太阴湿土": "太阳寒水", "太阳寒水": "太阴湿土",
    "少阳相火": "厥阴风木", "厥阴风木": "少阳相火",
}

# ── 六步主气（大寒起，固定不变）/ 客气阴阳序（一阴→二阴→三阴→一阳→二阳→三阳）──
ZHU_QI = ("厥阴风木", "少阴君火", "少阳相火", "太阴湿土", "阳明燥金", "太阳寒水")
KE_ORDER = ("厥阴风木", "少阴君火", "太阴湿土", "少阳相火", "阳明燥金", "太阳寒水")
STEP_NAMES = ("初之气", "二之气", "三之气", "四之气", "五之气", "终之气")

# 六步起点节气（大寒→春分→小满→大暑→秋分→小雪，各起一步）
BOUNDARY_STEP = {"大寒": 0, "春分": 1, "小满": 2, "大暑": 3, "秋分": 4, "小雪": 5}

# 六气 → 五行（判客主加临的生克用）
QI_WUXING = {"厥阴风木": "木", "少阴君火": "火", "少阳相火": "火",
             "太阴湿土": "土", "阳明燥金": "金", "太阳寒水": "水"}
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _rel_label(ke, zhu):
    """客主加临：客气对主气的生克关系。"""
    k, z = QI_WUXING[ke], QI_WUXING[zhu]
    if k == z:
        return "客主同气"
    if _SHENG[k] == z:
        return "客生主"
    if _KE[k] == z:
        return "客克主"
    if _SHENG[z] == k:
        return "主生客"
    return "主克客"


def _jieqi_boundaries(year):
    """收集锚点年 year-1 与 year 两年节气表中的六步边界（datetime, 名）。

    实测锚点年 Y 的节气表含大寒(Y-01)至小雪(Y-11)，两表合扫即可
    覆盖任意出生日所在六步（含跨年终之气）。
    """
    out = set()
    for y in (year - 1, year):
        table = Solar.fromYmdHms(y, 7, 1, 12, 0, 0).getLunar().getJieQiTable()
        for name, s in table.items():
            if name in BOUNDARY_STEP:
                out.add((datetime(s.getYear(), s.getMonth(), s.getDay(),
                                  s.getHour(), s.getMinute(), s.getSecond()), name))
    return sorted(out)


def _six_step(solar):
    """定位出生时刻所属六步（返回步序 0-5 与当年大寒时刻）。"""
    bd = datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                  solar.getHour(), 0, 0)
    bounds = _jieqi_boundaries(solar.getYear())
    step = None
    for dt, name in bounds:
        if bd >= dt:
            step = BOUNDARY_STEP[name]
    # 当年大寒（一月，来自本年节气表）——运气年判定专用；
    # 注意不能用"最后一个 ≤ 出生日的大寒"，否则年初出生会误取上一年大寒
    dahans = [dt for dt, name in bounds
              if name == "大寒" and dt.year == solar.getYear()]
    dahan = dahans[0] if dahans else None
    return (step if step is not None else 5), dahan


def yunqi_facts(solar):
    """由出生 Solar 推五运六气事实（确定层，不做吉凶解读）。"""
    step, dahan = _six_step(solar)
    bd = datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), 0, 0)
    # 运气年：大寒前出生 → 归上一年干支（大寒交司；以立春界干支标注该年）
    qi_year = solar.getYear()
    if dahan is None or bd < dahan:
        qi_year -= 1
    gz = Solar.fromYmdHms(qi_year, 7, 1, 12, 0, 0).getLunar() \
        .getYearInGanZhiByLiChun()
    gan, zhi = gz[0], gz[1]

    sui_yun, guo = SUI_YUN[gan]
    si_tian = SI_TIAN[zhi]
    zai_quan = ZAI_QUAN[si_tian]
    # 客气六步：司天定三之气，按阴阳序环排
    base = KE_ORDER.index(si_tian)
    ke_qi = [KE_ORDER[(base - 2 + i) % 6] for i in range(6)]
    zhu_qi = ZHU_QI[step]

    lunar = solar.getLunar()
    return {
        "岁运干支": gz,
        "岁运": f"{sui_yun}{'太过' if guo == '太过' else '不及'}",
        "司天": si_tian,
        "在泉": zai_quan,
        "出生六步": STEP_NAMES[step],
        "主气": zhu_qi,
        "客气": ke_qi[step],
        "客主加临": _rel_label(ke_qi[step], zhu_qi),
        "月令": f"农历{lunar.getMonthInChinese()}月",
    }


def today_context():
    """当前时令（今日干支 + 当前六步主客气），供 prompt 顺时养生建议。"""
    now = datetime.now()
    solar = Solar.fromYmdHms(now.year, now.month, now.day,
                             now.hour, now.minute, 0)
    from my_page.page06.part01 import engine
    facts = yunqi_facts(solar)
    facts["今日干支"] = " ".join(engine.today_bazi())
    return facts
