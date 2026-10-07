import pandas as pd
# 完整的纳音表
na_yin_table = {
    '甲子': '海中金', '乙丑': '海中金', '丙寅': '炉中火', '丁卯': '炉中火', '戊辰': '大林木', '己巳': '大林木',
    '庚午': '路旁土', '辛未': '路旁土', '壬申': '剑锋金', '癸酉': '剑锋金', '甲戌': '山头火', '乙亥': '山头火',
    '丙子': '涧下水', '丁丑': '涧下水', '戊寅': '城头土', '己卯': '城头土', '庚辰': '白蜡金', '辛巳': '白蜡金',
    '壬午': '杨柳木', '癸未': '杨柳木', '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹雳火', '己丑': '霹雳火', '庚寅': '松柏木', '辛卯': '松柏木', '壬辰': '长流水', '癸巳': '长流水',
    '甲午': '沙中金', '乙未': '沙中金', '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金', '甲辰': '佛灯火', '乙巳': '佛灯火',
    '丙午': '天河水', '丁未': '天河水', '戊申': '大驿土', '己酉': '大驿土', '庚戌': '钗钏金', '辛亥': '钗钏金',
    '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水', '丙辰': '沙中土', '丁巳': '沙中土',
    '戊午': '天上火', '己未': '天上火', '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水'
}
# 完整的藏干表
zang_gan_table = {
    '子': '癸', '丑': '己癸辛', '寅': '甲丙戊', '卯': '乙', '辰': '戊乙癸', '巳': '丙庚戊',
    '午': '丁己', '未': '己丁乙', '申': '庚壬戊', '酉': '辛', '戌': '戊辛丁', '亥': '壬甲'
}
# 日主相关信息
# 定义十神关系
shi_shen_relations = {
    '生我': {
        '同性': '正印', '异性': '偏印'
    },
    '我生': {
        '同性': '食神', '异性': '伤官'
    },
    '克我': {
        '同性': '正官', '异性': '七杀'
    },
    '我克': {
        '同性': '偏财', '异性': '正财'
    },
    '同我': {
        '同性': '比肩', '异性': '劫财'
    }
}
# 定义五行阴阳属性
yin_yang = {
    '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳', '己': '阴',
    '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴'
}
# 完整的十二长生表
sheng_chang_table = {
    '甲': {'亥': '长生', '子': '沐浴', '丑': '冠带', '寅': '临官', '卯': '帝旺', '辰': '衰', '巳': '病', '午': '死', '未': '墓', '申': '绝', '酉': '胎', '戌': '养'},
    '乙': {'午': '长生', '未': '沐浴', '申': '冠带', '酉': '临官', '戌': '帝旺', '亥': '衰', '子': '病', '丑': '死', '寅': '墓', '卯': '绝', '辰': '胎', '巳': '养'},
    '丙': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '丁': {'酉': '长生', '戌': '沐浴', '亥': '冠带', '子': '临官', '丑': '帝旺', '寅': '衰', '卯': '病', '辰': '死', '巳': '墓', '午': '绝', '未': '胎', '申': '养'},
    '戊': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '己': {'酉': '长生', '戌': '沐浴', '亥': '冠带', '子': '临官', '丑': '帝旺', '寅': '衰', '卯': '病', '辰': '死', '巳': '墓', '午': '绝', '未': '胎', '申': '养'},
    '庚': {'巳': '长生', '午': '沐浴', '未': '冠带', '申': '临官', '酉': '帝旺', '戌': '衰', '亥': '病', '子': '死', '丑': '墓', '寅': '绝', '卯': '胎', '辰': '养'},
    '辛': {'子': '长生', '丑': '沐浴', '寅': '冠带', '卯': '临官', '辰': '帝旺', '巳': '衰', '午': '病', '未': '死', '申': '墓', '酉': '绝', '戌': '胎', '亥': '养'},
    '壬': {'申': '长生', '酉': '沐浴', '戌': '冠带', '亥': '临官', '子': '帝旺', '丑': '衰', '寅': '病', '卯': '死', '辰': '墓', '巳': '绝', '午': '胎', '未': '养'},
    '癸': {'卯': '长生', '辰': '沐浴', '巳': '冠带', '午': '临官', '未': '帝旺', '申': '衰', '酉': '病', '戌': '死', '亥': '墓', '子': '绝', '丑': '胎', '寅': '养'}
}
# 完整的空亡表
kong_wang_table = {
    '甲子': ['戌', '亥'], '甲戌': ['申', '酉'], '甲申': ['午', '未'], '甲午': ['辰', '巳'],
    '甲辰': ['寅', '卯'], '甲寅': ['子', '丑'],
    '乙丑': ['戌', '亥'], '乙亥': ['申', '酉'], '乙酉': ['午', '未'], '乙未': ['辰', '巳'],
    '乙巳': ['寅', '卯'], '乙卯': ['子', '丑'],
    '丙寅': ['戌', '亥'], '丙子': ['申', '酉'], '丙戌': ['午', '未'], '丙申': ['辰', '巳'],
    '丙午': ['寅', '卯'], '丙辰': ['子', '丑'],
    '丁卯': ['戌', '亥'], '丁丑': ['申', '酉'], '丁亥': ['午', '未'], '丁酉': ['辰', '巳'],
    '丁未': ['寅', '卯'], '丁巳': ['子', '丑'],
    '戊辰': ['戌', '亥'], '戊寅': ['申', '酉'], '戊子': ['午', '未'], '戊戌': ['辰', '巳'],
    '戊申': ['寅', '卯'], '戊午': ['子', '丑'],
    '己巳': ['戌', '亥'], '己卯': ['申', '酉'], '己丑': ['午', '未'], '己亥': ['辰', '巳'],
    '己酉': ['寅', '卯'], '己未': ['子', '丑'],
    '庚午': ['戌', '亥'], '庚辰': ['申', '酉'], '庚寅': ['午', '未'], '庚子': ['辰', '巳'],
    '庚戌': ['寅', '卯'], '庚申': ['子', '丑'],
    '辛未': ['戌', '亥'], '辛巳': ['申', '酉'], '辛卯': ['午', '未'], '辛丑': ['辰', '巳'],
    '辛亥': ['寅', '卯'], '辛酉': ['子', '丑'],
    '壬申': ['戌', '亥'], '壬午': ['申', '酉'], '壬辰': ['午', '未'], '壬寅': ['辰', '巳'],
    '壬子': ['寅', '卯'], '壬戌': ['子', '丑'],
    '癸酉': ['戌', '亥'], '癸未': ['申', '酉'], '癸巳': ['午', '未'], '癸卯': ['辰', '巳'],
    '癸丑': ['寅', '卯'], '癸亥': ['子', '丑']
}
# 假设这是你定义的天干五行和阴阳属性的字典
TIAN_GAN = {
    '甲': ('阳', '木'), '乙': ('阴', '木'),
    '丙': ('阳', '火'), '丁': ('阴', '火'),
    '戊': ('阳', '土'), '己': ('阴', '土'),
    '庚': ('阳', '金'), '辛': ('阴', '金'),
    '壬': ('阳', '水'), '癸': ('阴', '水')
}

# 假设这是你定义的五行生克关系的字典
SHENG_KE = {
    '木': {'生': '火', '克': '土'},
    '火': {'生': '土', '克': '金'},
    '土': {'生': '金', '克': '水'},
    '金': {'生': '水', '克': '木'},
    '水': {'生': '木', '克': '火'}
}

# 十神名称对照表（保持原结构）
SHI_SHEN_NAMES = {
    ('同我', '同阴同阳'): '比肩',
    ('同我', '阴阳不同'): '劫财',
    ('我生', '同阴同阳'): '食神',
    ('我生', '阴阳不同'): '伤官',
    ('我克', '同阴同阳'): '偏财',
    ('我克', '阴阳不同'): '正财',
    ('生我', '同阴同阳'): '偏印',
    ('生我', '阴阳不同'): '正印',
    ('克我', '同阴同阳'): '七杀',
    ('克我', '阴阳不同'): '正官'
}

# 定义天干、地支及其五行属性
heavenly_stems = {
    '甲': '阳木', '乙': '阴木', '丙': '阳火', '丁': '阴火',
    '戊': '阳土', '己': '阴土', '庚': '阳金', '辛': '阴金',
    '壬': '阳水', '癸': '阴水'
}

earthly_branches = {
    '子': ('阳水', {'癸': '阴水'}),
    '丑': ('阴土', {'己': '阴土', '辛': '阴金', '癸': '阴水'}),
    '寅': ('阳木', {'甲': '阳木', '丙': '阳火', '戊': '阳土'}),
    '卯': ('阴木', {'乙': '阴木'}),
    '辰': ('阳土', {'戊': '阳土', '乙': '阴木', '癸': '阴水'}),
    '巳': ('阳火', {'丙': '阳火', '戊': '阳土', '庚': '阳金'}),
    '午': ('阳火', {'丁': '阴火', '己': '阴土'}),
    '未': ('阴土', {'己': '阴土', '丁': '阴火', '乙': '阴木'}),
    '申': ('阳金', {'庚': '阳金', '壬': '阳水', '戊': '阳土'}),
    '酉': ('阴金', {'辛': '阴金'}),
    '戌': ('阳土', {'戊': '阳土', '辛': '阴金', '丁': '阴火'}),
    '亥': ('阴水', {'壬': '阳水', '甲': '阳木'})
}

# 新增：星运表（大运状态）
xing_yun_table = {
    '长生': '新生阶段，充满活力',
    '沐浴': '成长阶段，需要呵护',
    '冠带': '青年阶段，崭露头角',
    '临官': '壮年阶段，事业鼎盛',
    '帝旺': '巅峰阶段，能量最强',
    '衰': '开始衰退，力不从心',
    '病': '问题显现，需要调整',
    '死': '能量最低，陷入困境',
    '墓': '隐藏积累，等待时机',
    '绝': '完全断绝，重新开始',
    '胎': '孕育新生，准备阶段',
    '养': '滋养成长，平稳发展'
}

# 新增：自坐表（日干与日支关系）
zi_zuo_table = {
    '甲': {'子': '沐浴', '丑': '冠带', '寅': '临官', '卯': '帝旺', '辰': '衰', '巳': '病',
          '午': '死', '未': '墓', '申': '绝', '酉': '胎', '戌': '养', '亥': '长生'},
    '乙': {'子': '病', '丑': '衰', '寅': '帝旺', '卯': '临官', '辰': '冠带', '巳': '沐浴',
          '午': '长生', '未': '养', '申': '胎', '酉': '绝', '戌': '墓', '亥': '死'},
    '丙': {'子': '胎', '丑': '养', '寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官',
          '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝'},
    '丁': {'子': '绝', '丑': '墓', '寅': '死', '卯': '病', '辰': '衰', '巳': '帝旺',
          '午': '临官', '未': '冠带', '申': '沐浴', '酉': '长生', '戌': '养', '亥': '胎'},
    '戊': {'子': '胎', '丑': '养', '寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官',
          '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝'},
    '己': {'子': '绝', '丑': '墓', '寅': '死', '卯': '病', '辰': '衰', '巳': '帝旺',
          '午': '临官', '未': '冠带', '申': '沐浴', '酉': '长生', '戌': '养', '亥': '胎'},
    '庚': {'子': '死', '丑': '墓', '寅': '绝', '卯': '胎', '辰': '养', '巳': '长生',
          '午': '沐浴', '未': '冠带', '申': '临官', '酉': '帝旺', '戌': '衰', '亥': '病'},
    '辛': {'子': '长生', '丑': '养', '寅': '胎', '卯': '绝', '辰': '墓', '巳': '死',
          '午': '病', '未': '衰', '申': '帝旺', '酉': '临官', '戌': '冠带', '亥': '沐浴'},
    '壬': {'子': '帝旺', '丑': '衰', '寅': '病', '卯': '死', '辰': '墓', '巳': '绝',
          '午': '胎', '未': '养', '申': '长生', '酉': '沐浴', '戌': '冠带', '亥': '临官'},
    '癸': {'子': '临官', '丑': '冠带', '寅': '沐浴', '卯': '长生', '辰': '养', '巳': '胎',
          '午': '绝', '未': '墓', '申': '死', '酉': '病', '戌': '衰', '亥': '帝旺'}
}


def get_relationship(day_stem, other_stem):
    """优化的十神计算函数"""
    # 获取五行属性和阴阳
    day_wuxing = heavenly_stems[day_stem][1]
    other_wuxing = heavenly_stems[other_stem][1]
    day_yinyang = heavenly_stems[day_stem][0]
    other_yinyang = heavenly_stems[other_stem][0]
    # 五行生克关系映射（新增核心逻辑）
    shengke_map = {
        '木': {'生': '火', '克': '土'},
        '火': {'生': '土', '克': '金'},
        '土': {'生': '金', '克': '水'},
        '金': {'生': '水', '克': '木'},
        '水': {'生': '木', '克': '火'}
    }
    # 判断五行关系（逻辑优化）
    if day_wuxing == other_wuxing:
        relation_type = '同我'
    elif other_wuxing == shengke_map[day_wuxing]['生']:
        relation_type = '我生'
    elif other_wuxing == shengke_map[day_wuxing]['克']:
        relation_type = '我克'
    elif day_wuxing in shengke_map[other_wuxing]['克']:  # 被克
        relation_type = '克我'
    else:  # 被生
        relation_type = '生我'
    # 判断阴阳属性（优化判断逻辑）
    yinyang_same = (day_yinyang == other_yinyang)

    # 返回对应十神（使用字典查询）
    return SHI_SHEN_NAMES[
        (relation_type,
         '同阴同阳' if yinyang_same else '阴阳不同')
    ]

def calculate_ten_gods(bazi):
    """优化后的十神计算主函数"""
    day_stem = bazi[2][0]  # 日干
    results = []

    for i, pillar in enumerate(bazi):
        stem, branch = pillar[0], pillar[1]
        pillar_results = []

        # 处理天干
        stem_rel = get_relationship(day_stem, stem)
        pillar_results.append(stem_rel)

        # 处理地支藏干（增加主气标记）
        main_qi, hidden = earthly_branches[branch]
        for h_stem in hidden:
            h_rel = get_relationship(day_stem, h_stem)
            # 标记主气（示例：*表示主气）
            tag = '*' if h_stem == main_qi else ''
            pillar_results.append(f"{h_rel}{tag}")

        # 去重处理（保留原始顺序）
        seen = set()
        final_results = []
        for item in pillar_results:
            if item not in seen:
                seen.add(item)
                final_results.append(item)

        # print(f"第{i + 1}柱 {pillar}: {', '.join(final_results)}")
        results.append(final_results)
    new_results = [row[1:] for row in results]

    return new_results

def determine_shi_shen(bazi):
    """
    根据输入的八字确定每个天干对应的十神
    :param bazi: 一个包含四个元素的元组，每个元素是一个表示干支的字符串，如 ('丙子', '丁酉', '庚午', '丁亥')
    :return: 一个字典，键为年、月、日、时，值为对应的十神
    """
    # 提取日柱天干作为日主
    ri_zhu = bazi[2][0]
    ri_zhu_yin_yang, ri_zhu_wu_xing = TIAN_GAN[ri_zhu]

    result = {}
    columns = ['年', '月', '日', '时']
    for i, gan_zhi in enumerate(bazi):
        tian_gan = gan_zhi[0]
        tian_gan_yin_yang, tian_gan_wu_xing = TIAN_GAN[tian_gan]

        # 判断五行关系
        if tian_gan_wu_xing == ri_zhu_wu_xing:
            relation = '同我'
        elif SHENG_KE[ri_zhu_wu_xing]['生'] == tian_gan_wu_xing:
            relation = '我生'
        elif SHENG_KE[ri_zhu_wu_xing]['克'] == tian_gan_wu_xing:
            relation = '我克'
        elif SHENG_KE[tian_gan_wu_xing]['生'] == ri_zhu_wu_xing:
            relation = '生我'
        elif SHENG_KE[tian_gan_wu_xing]['克'] == ri_zhu_wu_xing:
            relation = '克我'

        # 判断阴阳关系
        if tian_gan_yin_yang == ri_zhu_yin_yang:
            yin_yang_relation = '同阴同阳'
        else:
            yin_yang_relation = '阴阳不同'

        # 确定十神
        shi_shen = SHI_SHEN_NAMES[(relation, yin_yang_relation)]
        result[columns[i]] = shi_shen
    result = list(result.values())
    result[2] = "日主"
    return result

def calculate_na_yin(bazi):
    """计算八字的纳音"""
    return [na_yin_table[ganzhi] for ganzhi in bazi]

def calculate_zang_gan(bazi):
    """计算八字的藏干"""
    zang_gan = []
    for ganzhi in bazi:
        gan = ganzhi[0]
        zhi = ganzhi[1]
        zang = zang_gan_table.get(zhi, '')
        zang_gan.append(f"{gan}（本干），{','.join([f'{z}（{zhi}藏干）' for z in zang])}" if zang else f"{gan}（本干）")
    return zang_gan

def get_shi_shen_relation(gan, ri_zhu):
    """根据天干和日主计算十神关系"""
    if gan == ri_zhu:
        return '日主'
    diff = (ord(gan) - ord(ri_zhu)) % 10
    if diff == 0:
        relation = '同我'
    elif diff == 5:
        relation = '生我'
    elif diff == 10 - 5:
        relation = '我生'
    elif diff == 3:
        relation = '克我'
    else:
        relation = '我克'
    return shi_shen_relations[relation][f"{'同性' if yin_yang[gan] == yin_yang[ri_zhu] else '异性'}"]

def calculate_shi_shen(bazi, ri_zhu):
    """计算八字的十神"""
    shi_shen = []
    for ganzhi in bazi:
        gan = ganzhi[0]
        zhi = ganzhi[1]
        zang = zang_gan_table.get(zhi, '')
        gan_relation = get_shi_shen_relation(gan, ri_zhu)
        zang_relations = [get_shi_shen_relation(z, ri_zhu) for z in zang] if zang else []
        shi_shen.append(f"{gan}：{gan_relation}，{','.join([f'{z}:{rel}' for z, rel in zip(zang, zang_relations)])}" if zang_relations else f"{gan}：{gan_relation}")
    return shi_shen
def calculate_sheng_chang(bazi, ri_zhu):
    """计算八字的长生状态"""
    return [sheng_chang_table[ri_zhu][ganzhi[1]] for ganzhi in bazi if ganzhi[1] in sheng_chang_table[ri_zhu]]

def calculate_kongwang(bazi):
    """计算八字的空亡（两支连写为短字符串，如"戌亥"；
    旧实现 str(list) 产出"['戌', '亥']"，表格里占宽且不可读）。"""
    return ["".join(kong_wang_table[stem_branch])
            for stem_branch in bazi if stem_branch in kong_wang_table]


def calculate_xing_yun(bazi, ri_zhu):
    """计算星运（仅状态名，如"长生"；旧实现追加的大段释义
    "长生 - 新生阶段，充满活力"在表格每行重复，把列撑到折叠）。"""
    xing_yun = []
    for ganzhi in bazi:
        zhi = ganzhi[1]
        if zhi in sheng_chang_table[ri_zhu]:
            xing_yun.append(sheng_chang_table[ri_zhu][zhi])
        else:
            xing_yun.append("")
    return xing_yun


def calculate_zi_zuo(bazi):
    """计算自坐（日干与日支关系，仅状态名；释义见 xing_yun_table）。"""
    zi_zuo = []
    for ganzhi in bazi:
        zhi = ganzhi[1]  # 当前柱的地支
        gan = ganzhi[0]  # 当前柱的天干
        if zhi in zi_zuo_table[gan]:
            zi_zuo.append(zi_zuo_table[gan][zhi])
        else:
            zi_zuo.append("")
    return zi_zuo



def numberology(bazi):
    """主函数，计算八字的各项信息"""
    # 计算生克
    ss = determine_shi_shen(bazi)
    # 计算纳音
    na_yin = calculate_na_yin(bazi)
    # 计算藏干
    zang_gan = calculate_zang_gan(bazi)
    # 计算日主
    ri_zhu = bazi[2][0]
    # 计算十神
    shi_shen = calculate_ten_gods(bazi)
    # 计算长生
    sheng_chang = calculate_sheng_chang(bazi, ri_zhu)
    # 计算空亡
    kong_wang = calculate_kongwang(bazi)
    # 计算星运
    xing_yun = calculate_xing_yun(bazi, ri_zhu)
    # 计算自坐
    zi_zuo = calculate_zi_zuo(bazi)

    # 输出结果（全部为短字符串列：藏干十神原为 list，直接进 st.dataframe
    # 会被 Arrow/Glide 渲染成挤在一起的对象单元格，这里统一顿号连接；
    # "*"为藏干主气标记，表格无图例故去除，主气信息在"藏干"列首位）
    result = pd.DataFrame({
        '生克': ss,
        '干支': bazi,
        '纳音': na_yin,
        '藏干': zang_gan,
        '十神': ["、".join(x).replace("*", "") for x in shi_shen],
        '长生': sheng_chang,
        '空亡': kong_wang,
        '星运': xing_yun,
        '自坐': zi_zuo
    })
    return result


# # 示例八字
# bazi = ['丙子', '丁酉', '庚午', '丁亥']
# result = numberology(bazi)
# print(result)