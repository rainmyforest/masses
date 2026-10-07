"""page06/part01 · 大运流年推算（2026-10-07 大运流年功能 S1，方案 2.2/2.3）。

口径（与排盘同源：由与 chart() 相同的 EightChar 对象派生，立春界年柱、
节气界月柱、太阳时校正后的出生时刻全部自动继承）：
- 起运流派 sect=1（默认，Q1）：传统"3 天折 1 年"折算；sect=2 按分钟精确折算
- 顺逆排：阳男阴女顺排、阴男阳女逆排（年柱天干阴阳 × 性别，与 lunar-python
  isForward 实现一致，回归测试 4 命例锚定）
- 大运固定 10 步（index 0~9）：index 0 为"出生→起运前"段（干支为空、
  仍带流年），index 1 起每步 10 年；"大运"列表跳过 index 0（Q7：起运前
  段由展示层据"起运"信息渲染为"—（出生至起运）"行）
- 流年干支以立春为界：公历年 y 的流年 = y 年立春起的干支年（公历
  1 月 1 日～立春前出生者，出生后首段实际属上一干支年，正常口径）
- 年龄为虚岁（lunar-python 口径：公历年 − 出生公历年 + 1）
- 十神以天干论（LunarUtil.SHI_SHEN[日干+运干]，Q5）；纳音查表
  LunarUtil.NAYIN[干支]；"五行" = 干五行 + 支本气五行（如丙子 → 火水）
- "当前"判定：now（可锚定，供回归测试）落入 [起年, 止年] 的大运步 /
  年份等于 now.year 的流年；换运年 = 各大运步起年

纯函数（无 st.*/LLM 依赖）；缓存由 analyze.py 侧包 @st.cache_data。
"""
from datetime import datetime

from lunar_python.util import LunarUtil

# _BRANCH_STEMS 为 engine 模块私有表，同包内复用（支本气单源维护）
from my_page.page06.part01.engine import STEM_WUXING, _BRANCH_STEMS

_YANG_STEMS = set("甲丙戊庚壬")
_SECT_LABEL = {1: "3天折1年（传统）", 2: "按分钟精确折算"}


def _normalize_gender(gender):
    """gender：1 男 / 0 女（容错 '男'/'女'，其余抛 ValueError）。"""
    if gender in (1, "男", True):
        return 1
    if gender in (0, "女", False):
        return 0
    raise ValueError(f"gender 应为 1（男）/0（女），收到：{gender!r}")


def _annotations(gz, day_gan):
    """干支 →（十神, 纳音, 五行）。十神以天干论；五行 = 干 + 支本气。"""
    return (LunarUtil.SHI_SHEN[day_gan + gz[0]],            # 十神：日干+运干
            LunarUtil.NAYIN[gz],                             # 纳音：干支查表
            STEM_WUXING[gz[0]] + STEM_WUXING[_BRANCH_STEMS[gz[1]][0]])


def _yun_span(yun):
    """起运距出生时长（Yun 折算值 → "出生后 3 年 2 个月"文本）。"""
    parts = []
    if yun.getStartYear():
        parts.append(f"{yun.getStartYear()} 年")
    if yun.getStartMonth():
        parts.append(f"{yun.getStartMonth()} 个月")
    if yun.getStartDay():
        parts.append(f"{yun.getStartDay()} 天")
    return ("出生后 " + " ".join(parts)) if parts else "出生后即交运"


def _liunian_row(ly, day_gan, now_year, huan_years):
    """流年 → 行 dict（年/虚岁/干支/十神/纳音/五行/当前/备注）。"""
    gz = ly.getGanZhi()
    shi_shen, nayin, wuxing = _annotations(gz, day_gan)
    cur = ly.getYear() == now_year
    note = ("当前年 ★" if cur
            else "换运年" if ly.getYear() in huan_years else "")
    return {"年": ly.getYear(), "虚岁": ly.getAge(), "干支": gz,
            "十神": shi_shen, "纳音": nayin, "五行": wuxing,
            "当前": cur, "备注": note}


def _step_item(dy, seq, day_gan, now_year):
    """大运步 → 行 dict（方案 2.3 契约 + 备注 列）。"""
    gz = dy.getGanZhi()
    shi_shen, nayin, wuxing = _annotations(gz, day_gan)
    cur = dy.getStartYear() <= now_year <= dy.getEndYear()
    return {
        "序": seq, "干支": gz, "十神": shi_shen,
        "纳音": nayin, "五行": wuxing,
        "起年": dy.getStartYear(), "止年": dy.getEndYear(),
        "起岁": dy.getStartAge(), "止岁": dy.getEndAge(),
        "流年数": len(dy.getLiuNian()),
        "当前": cur,
        "备注": "当前 ★" if cur else f"换运年 {dy.getStartYear()}",
    }


def dayun_facts(solar, gender=1, sect=1, limit=10, now=None):
    """大运流年事实（确定性事实层，供 prompt 注入与页面/附录表格）。

    :param solar: 出生 Solar（应为太阳时校正后的时刻，与 chart() 同源）
    :param gender: 1 男 / 0 女（容错 '男'/'女'）
    :param sect:   1 传统"3 天折 1 年"（默认）/ 2 按分钟精确折算
    :param limit:  "大运"列表步数上限（起运前段不计；当前/未来判定不受限）
    :param now:    锚定时刻（默认 datetime.now()），决定"当前"标记
    :return: 方案 2.3 契约 dict（全 primitives，可 JSON 序列化）：
        起运（交运时刻/起运虚岁/排法/流派/出生后）；
        大运（序/干支/十神/纳音/五行/起年/止年/起岁/止岁/流年数/当前/备注）；
        当前大运（单条，未交运为 None）；未来大运（其后 2 步，未交运时为前 2 步）；
        当前大运流年（当前步管辖 10 流年）；近期流年（当前年 ±3，起运前段亦覆盖）
    """
    now = now or datetime.now()
    gender = _normalize_gender(gender)

    ec = solar.getLunar().getEightChar()
    day_gan = ec.getDay()[0]
    year_gan = ec.getYear()[0]
    yun = ec.getYun(gender, sect)
    da_yun = yun.getDaYun()                       # 固定 10 步（index 0~9）

    yang = year_gan in _YANG_STEMS
    forward = yang == (gender == 1)               # 阳男阴女顺、阴男阳女逆
    pai = (f"{'阳' if yang else '阴'}{'男' if gender == 1 else '女'}"
           f"{'顺排' if forward else '逆排'}")

    start = yun.getStartSolar()

    steps = []
    for i, dy in enumerate(da_yun):
        if i == 0 or not dy.getGanZhi():          # 起运前段（Q7 不入列表）
            continue
        if len(steps) >= limit:
            break
        steps.append(_step_item(dy, len(steps) + 1, day_gan, now.year))

    # 当前大运步（全量扫描，不受 limit 截断影响）
    cur_dy, cur_seq = None, None
    for i, dy in enumerate(da_yun):
        if i == 0 or not dy.getGanZhi():
            continue
        if dy.getStartYear() <= now.year <= dy.getEndYear():
            cur_dy, cur_seq = dy, i               # 序 = da_yun 下标（0 段跳过）
            break
    cur_step = next((s for s in steps if s["当前"]), None)
    if cur_dy is not None and cur_step is None:   # limit 截断时仍给出当前步
        cur_step = _step_item(cur_dy, cur_seq, day_gan, now.year)

    # 未来 2 步：当前步之后；未交运（index 0 段）时为头两步
    after = cur_seq if cur_seq is not None else 0
    future = steps[after: after + 2]

    huan_years = {s["起年"] for s in steps}       # 换运年 = 各大运步起年
    liunian_by_year = {}
    for dy in da_yun:                             # 含 index 0 段（起运前流年）
        for ly in dy.getLiuNian():
            liunian_by_year[ly.getYear()] = _liunian_row(
                ly, day_gan, now.year, huan_years)

    return {
        "起运": {
            "交运时刻": (f"{start.getYear()}年{start.getMonth()}月"
                        f"{start.getDay()}日 "
                        f"{start.getHour():02d}:{start.getMinute():02d}"),
            "起运虚岁": steps[0]["起岁"] if steps else None,
            "排法": pai,
            "流派": _SECT_LABEL.get(sect, f"sect={sect}"),
            "出生后": _yun_span(yun),
        },
        "大运": steps,
        "当前大运": dict(cur_step) if cur_step else None,
        "未来大运": [dict(s) for s in future],
        "当前大运流年": ([_liunian_row(ly, day_gan, now.year, huan_years)
                          for ly in cur_dy.getLiuNian()] if cur_dy else []),
        "近期流年": [liunian_by_year[y] for y in
                     range(now.year - 3, now.year + 4) if y in liunian_by_year],
    }
