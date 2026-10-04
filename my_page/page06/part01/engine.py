"""page06/part01 · 排盘引擎（2026-09-25 A 项：lunar-python 替换自研 YMDT.py）。

口径（与页面 caption 一致）：
- 年柱：以立春交接时刻分界；月柱：以十二节（惊蛰/清明/…）交接时刻分界
- 日柱/时柱：天文历法推算（旧 YMDT 的"农历日喂公历公式"错误已消除）
- 阴历输入支持闰月（lunar-python 以负数月表示闰月）

旧 Time/YMDT.py 实测抽样 4 例错 3 例（日柱系统性错误 + 立春窗口年月柱错误），
本引擎以 lunar-python 为唯一排盘真源；神煞综合表沿用
my_data/data06/numerology.py（表数据与 lunar-python 交叉验证通过，见 test_core.py）。
"""
from datetime import datetime

from lunar_python import Solar, Lunar

from my_data.data06 import numerology as nlog

_PILLARS = ("年", "月", "日", "时")

_CN_MONTH = {1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
             7: "七", 8: "八", 9: "九", 10: "十", 11: "十一", 12: "十二"}

STEM_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
               "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def birth_solar(year, month, day, hour, minute=0, calendar="阳历", leap=False):
    """统一产出 lunar_python.Solar（公历对象）。

    阳历：校验真实日期（lunar-python 对 2 月 30 会静默归一，必须自行拦截）。
    阴历：闰月以负数月传入；不存在的闰月/日期由 lunar-python 抛错，统一转 ValueError。
    minute 不改变时柱地支（时辰按小时定），但配合太阳时校正可能跨时辰/跨日，
    故与 hour 一并透传给 lunar-python。
    """
    if calendar == "阳历":
        try:
            datetime(year, month, day)          # 真实日期校验（2月30/平年2月29等）
        except ValueError as e:
            raise ValueError(f"{year}年{month}月{day}日不是有效的阳历日期") from e
        return Solar.fromYmdHms(year, month, day, hour, minute, 0)
    # 阴历：闰月两种传法都兼容——(month=6, leap=True) 或 month=-6（lunar-python 风格）
    lunar_month = -month if (leap and month > 0) else month
    try:
        return Lunar.fromYmdHms(year, lunar_month, day, hour, minute, 0).getSolar()
    except Exception as e:                     # lunar-python 对非法阴历抛 Exception
        tip = (f"闰{_CN_MONTH.get(month, month)}月" if (leap or month < 0)
               else f"{month}月{day}日")
        raise ValueError(f"{year}年不存在{tip}，请核对阴历日期（或闰月勾选）") from e


# 藏干权重（支本气 0.6 / 中气 0.3 / 余气 0.1；天干另按 1.0 全重计，
# 通行"干支藏干加权"力量估计口径，供 LLM 解读五行分布用）
_BRANCH_STEMS = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}
_STEM_W = (0.6, 0.3, 0.1)


def wuxing_stats(bazi):
    """四柱五行力量分布（确定性事实层）：天干全重 + 藏干加权。

    返回 {五行: 权重和}（保留 1 位小数），供 prompt 注入——LLM 解读
    "五行分布"时有据可依，不靠模型自行数干支。
    """
    stats = {w: 0.0 for w in "木火土金水"}
    for gz in bazi:
        stats[STEM_WUXING[gz[0]]] += 1.0          # 天干
        for i, s in enumerate(_BRANCH_STEMS[gz[1]]):
            stats[STEM_WUXING[s]] += _STEM_W[min(i, 2)]
    return {w: round(v, 1) for w, v in stats.items()}


def chart(year, month, day, hour, calendar="阳历", leap=False, minute=0):
    """排盘主入口：四柱八字 + 神煞综合表 + 农/公历文本。"""
    solar = birth_solar(year, month, day, hour, minute, calendar, leap)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    bazi = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    table = nlog.numberology(bazi)
    table.index = list(_PILLARS)
    return {
        "solar": solar,
        "lunar": lunar,
        "bazi": bazi,
        "gongli": f"公历 {solar.getYear()}年{solar.getMonth()}月{solar.getDay()}日 {hour}时",
        "nongli": f"农历 {lunar.toString()}",
        "ri_zhu": ec.getDay()[0],
        "ri_zhu_wuxing": STEM_WUXING[ec.getDay()[0]],
        "wuxing": wuxing_stats(bazi),
        "table": table,
    }


def today_bazi():
    """今日干支（供"当前时令"上下文）。"""
    now = datetime.now()
    ec = Solar.fromYmdHms(now.year, now.month, now.day,
                          now.hour, now.minute, 0).getLunar().getEightChar()
    return [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
