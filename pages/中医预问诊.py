import streamlit as st
import pandas as pd
from datetime import datetime
import io
import xlsxwriter

# 设置页面配置
st.set_page_config(
    page_title="中医症状自评报告",
    page_icon="🌿",
    layout="wide"
)

# 初始化session state
if 'report_submitted' not in st.session_state:
    st.session_state.report_submitted = False
if 'report_data' not in st.session_state:
    st.session_state.report_data = {}

# 应用标题
st.title("🌿 中医症状描述自评报告")
st.markdown("""
<div style="background-color:#f0f8ff; padding:20px; border-radius:10px; margin-bottom:20px;">
<h3 style="color:#2c7873; text-align:center;">中医辨证参考工具</h3>
<p style="text-align:center;">本系统旨在帮助您系统地整理和描述身体的不适感受，为中医辨证提供参考。</p>
<p style="text-align:center; font-size:0.9em; color:#666;">请根据最近一周（或您认为相关的时间段）的实际情况填写</p>
</div>
""", unsafe_allow_html=True)

# 创建表单
with st.form("tcm_assessment_form"):
    st.header("📋 基本信息")

    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input("姓名*", placeholder="请输入您的姓名")
    with col2:
        gender = st.selectbox("性别*", ["请选择", "男", "女", "其他"])
    with col3:
        age = st.number_input("年龄*", min_value=0, max_value=120, value=30, step=1)

    report_date = st.date_input("报告日期*", value=datetime.now().date())

    st.markdown("---")
    st.header("🌡️ 第一部分：核心症状与全身状态")

    st.subheader("1. 最主要的不适（请描述1-3项）")

    discomforts = []
    for i in range(1, 4):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            discomfort = st.text_input(f"不适{i}描述", placeholder=f"如：头痛、胃胀等", key=f"discomfort_{i}")
        with col2:
            location = st.text_input(f"部位{i}", placeholder="具体部位", key=f"location_{i}")
        with col3:
            severity = st.selectbox(f"程度{i}", ["", "轻", "中", "重"], key=f"severity_{i}")

        if discomfort:
            discomforts.append(
                f"{discomfort}（部位：{location if location else '未指定'}，程度：{severity if severity else '未指定'}）")

    st.subheader("2. 全身整体感觉")

    col1, col2 = st.columns(2)

    with col1:
        energy_level = st.selectbox(
            "精力体力*",
            ["", "充沛", "一般", "容易疲劳，休息后能缓解", "容易疲劳，休息后不能缓解"]
        )

        sweat_pattern = st.selectbox(
            "出汗情况",
            ["", "无汗", "容易出汗，稍动即出", "夜间睡着后出汗（盗汗）",
             "仅头部/胸口出汗", "汗出后怕风", "正常"]
        )

    with col2:
        temperature_preference = st.selectbox(
            "怕冷/怕热*",
            ["", "特别怕冷，手脚凉", "特别怕热，喜凉", "既怕冷又怕热", "无明显异常"]
        )

        body_temperature = st.selectbox(
            "整体寒热感觉",
            ["", "自我感觉身体发热（体温可高可不高）", "自我感觉身体/体内发冷",
             "忽冷忽热", "无明显寒热"]
        )

    st.markdown("---")
    st.header("👁️ 第二部分：中医四诊信息")

    st.subheader("一、望诊（自我观察）")

    tab1, tab2, tab3 = st.tabs(["精神面貌与面色", "舌象观察", "其他"])

    with tab1:
        spirit_state = st.selectbox(
            "精神面貌",
            ["", "有神，目光明亮", "少神，精神不振", "烦躁不安", "淡漠"]
        )

        complexion = st.selectbox(
            "面色",
            ["", "红润", "苍白", "萎黄（黄而无光）", "潮红（如化妆）",
             "晦暗（发暗发黑）", "青紫"]
        )

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            tongue_color = st.selectbox(
                "舌质颜色",
                ["", "淡红", "淡白", "红", "绛红（深红）", "有瘀点/瘀斑"]
            )

            tongue_body = st.selectbox(
                "舌体形态",
                ["", "胖大，有齿痕", "瘦小", "正常"]
            )

        with col2:
            tongue_coating_color = st.selectbox(
                "舌苔颜色",
                ["", "薄白", "白厚", "黄", "灰黑"]
            )

            tongue_coating_texture = st.selectbox(
                "舌苔质地",
                ["", "薄", "厚", "腻（如涂油）", "干燥", "湿润/滑"]
            )

        tongue_other = st.multiselect(
            "舌象其他特征",
            ["舌下络脉青紫怒张", "无明显异常"]
        )

    with tab3:
        breath_smell = st.selectbox(
            "口气",
            ["", "无异常", "有口臭", "有酸腐味"]
        )

        secretion_smell = st.selectbox(
            "分泌物气味",
            ["", "无异常", "有异味"]
        )

    st.subheader("二、问诊（详细感受）")

    # 创建多个选项卡来组织问诊内容
    q_tabs = st.tabs(["头面五官", "饮食与二便", "睡眠与情绪", "女性专属"])

    with q_tabs[0]:
        st.markdown("**头面五官症状**")

        head_symptoms = st.multiselect(
            "头部症状",
            ["头晕", "头重如裹（感觉裹着布）", "头痛", "无异常"]
        )

        head_pain_location = st.text_input("头痛部位（如有）", placeholder="如：前额、两侧、后脑等")

        facial_symptoms = st.multiselect(
            "眼耳口鼻症状",
            ["眼睛干涩", "耳鸣（声如蝉鸣/如潮水）", "口干", "口苦",
             "口淡无味", "喜饮水", "不欲饮水"]
        )

        drink_preference = st.selectbox(
            "饮水偏好",
            ["", "喜温饮", "喜凉饮", "无特别偏好"]
        )

        throat_symptoms = st.multiselect(
            "咽喉症状",
            ["咽干", "咽痛", "有异物感（梅核气）", "无异常"]
        )

    with q_tabs[1]:
        st.markdown("**饮食与消化**")

        appetite = st.selectbox(
            "食欲",
            ["", "好", "一般", "差，不想吃", "易饿，吃得多（消谷善饥）"]
        )

        after_meal = st.multiselect(
            "饭后感觉",
            ["舒适", "腹胀", "胃脘胀痛", "反酸烧心"]
        )

        food_preference = st.multiselect(
            "口味偏好",
            ["喜热食", "喜冷食", "喜辛辣", "喜甜食", "喜油腻", "无特别偏好"]
        )

        st.markdown("**二便情况**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**大便**")
            bowel_frequency = st.selectbox(
                "大便频率",
                ["", "每日一次", "每日多次", "多日一次", "不定时"]
            )

            bowel_consistency = st.selectbox(
                "大便性状",
                ["", "成形，软硬适中", "稀溏/不成形", "干结如羊粪",
                 "先干后稀", "黏腻，粘马桶"]
            )

            bowel_sensation = st.multiselect(
                "排便感觉",
                ["排便顺畅", "排便费力", "肛门灼热", "里急后重（有便意但排不尽）"]
            )

        with col2:
            st.markdown("**小便**")
            urine_color = st.selectbox(
                "小便颜色",
                ["", "清长", "淡黄", "深黄/黄赤", "浑浊"]
            )

            urine_pattern = st.multiselect(
                "小便频率/感觉",
                ["次数多，量多", "次数多，量少", "尿急、尿痛",
                 "排尿无力/余沥不尽", "正常"]
            )

    with q_tabs[2]:
        st.markdown("**睡眠情况**")

        sleep_problems = st.multiselect(
            "睡眠问题",
            ["入睡困难", "多梦易醒", "早醒", "嗜睡，睡不醒", "睡眠尚可"]
        )

        dream_frequency = st.selectbox(
            "梦境情况",
            ["", "多梦", "少梦", "噩梦", "记不清"]
        )

        st.markdown("**情绪与心理**")

        emotional_state = st.multiselect(
            "情绪状态",
            ["情绪平稳", "容易烦躁、发怒", "情绪低落、抑郁",
             "思虑过多", "容易紧张、焦虑", "精神萎靡，对什么都提不起兴趣"]
        )

        st.markdown("**疼痛与不适**")

        pain_locations = st.multiselect(
            "不适部位",
            ["胸部", "胁肋部", "胃脘部", "腹部", "腰部", "四肢关节", "其他", "无明显疼痛"]
        )

        other_pain_location = st.text_input("其他部位（如有）")

        pain_character = st.multiselect(
            "疼痛性质",
            ["胀痛", "刺痛（固定不移）", "隐痛（绵绵不休）",
             "冷痛（得热缓解）", "灼痛", "酸痛", "重着感（沉重感）"]
        )

        pressure_response = st.radio(
            "按压反应",
            ["", "喜按喜揉", "拒按，按压更痛", "无明显偏好"]
        )

    with q_tabs[3]:
        if gender == "女":
            st.markdown("**女性专属（月经情况）**")

            menstrual_cycle = st.selectbox(
                "月经周期",
                ["", "规律", "提前", "推后", "先后不定", "已绝经"]
            )

            if menstrual_cycle in ["提前", "推后"]:
                days = st.number_input("约多少天", min_value=1, max_value=30, value=7)

            menstrual_flow = st.selectbox(
                "经量",
                ["", "正常", "过多", "过少", "时多时少"]
            )

            menstrual_color = st.selectbox(
                "颜色/质地",
                ["", "鲜红", "淡红", "暗红/紫黑", "有血块"]
            )

            menstrual_symptoms = st.multiselect(
                "经期感觉",
                ["小腹坠胀", "小腹冷痛", "经前乳房胀痛", "无特殊不适"]
            )

            leucorrhea = st.selectbox(
                "白带情况",
                ["", "量少", "量多", "色白清稀", "色黄粘稠", "有异味", "无异常"]
            )
        else:
            st.info("此部分仅适用于女性用户")

    st.markdown("---")
    st.header("📊 第三部分：体质与环境因素")

    st.subheader("1. 体质倾向自评（可多选）")

    constitution_types = st.multiselect(
        "请选择您认为符合的体质倾向",
        [
            "气虚型：易疲劳，气短，懒言，易感冒。",
            "阳虚型：畏寒怕冷，四肢不温，喜热饮。",
            "阴虚型：手足心热，口干咽燥，喜冷饮，失眠多梦。",
            "痰湿型：身体沉重，面部油多，喉中有痰，大便粘腻。",
            "湿热型：面垢油光，口苦口干，大便粘滞或燥结，小便短黄。",
            "血瘀型：面色晦暗或有斑点，身体某处固定刺痛，舌有瘀点。",
            "气郁型：情绪抑郁或烦躁，胸闷，喜欢叹气。",
            "特禀型：易过敏（鼻炎、荨麻疹等），对季节变化适应差。",
            "平和型：精力充沛，适应力强，患病少。"
        ]
    )

    st.subheader("2. 近期生活环境与习惯")

    col1, col2 = st.columns(2)

    with col1:
        stress_level = st.select_slider(
            "压力水平",
            options=["低", "中低", "中等", "中高", "高"]
        )

        sleep_pattern = st.selectbox(
            "作息规律性",
            ["", "规律", "常熬夜"]
        )

        if sleep_pattern == "常熬夜":
            bedtime = st.slider("通常几点睡", 20, 30, 24)

    with col2:
        exercise_frequency = st.selectbox(
            "运动频率",
            ["", "经常（每周3次以上）", "偶尔（每周1-2次）", "很少（每月1-2次）", "几乎不运动"]
        )

        diet_preferences = st.multiselect(
            "饮食偏好",
            ["辛辣", "生冷（如冷饮、沙拉）", "油腻甜食", "清淡", "均衡", "偏咸", "偏甜"]
        )

    st.markdown("---")
    st.header("📝 第四部分：总结与诉求")

    possible_causes = st.text_area(
        "您认为导致当前症状的可能原因有哪些？",
        placeholder="如：近期劳累、情绪波动、饮食不节、外感风寒、久病等",
        height=80
    )

    improvement_goals = st.text_area(
        "您希望通过调理，主要改善哪些方面？",
        placeholder="请具体描述您希望通过中医调理达到的效果",
        height=80
    )

    additional_notes = st.text_area(
        "其他补充说明（可选）",
        placeholder="请补充任何其他相关信息",
        height=60
    )

    # 提交按钮
    submitted = st.form_submit_button("📤 提交自评报告", use_container_width=True)

# 处理表单提交
if submitted:
    # 验证必填字段
    if not name or gender == "请选择" or not age:
        st.error("请填写基本信息中的必填项（姓名、性别、年龄）")
    elif not energy_level or not temperature_preference:
        st.error("请填写核心症状与全身状态中的必填项")
    else:
        # 收集所有数据到字典
        report_data = {
            "基本信息": {
                "姓名": name,
                "性别": gender,
                "年龄": age,
                "报告日期": report_date.strftime("%Y-%m-%d")
            },
            "核心症状": {
                "最主要的不适": ", ".join(discomforts) if discomforts else "未描述",
                "精力体力": energy_level,
                "怕冷/怕热": temperature_preference,
                "出汗情况": sweat_pattern,
                "整体寒热感觉": body_temperature
            },
            "望诊": {
                "精神面貌": spirit_state,
                "面色": complexion,
                "舌质颜色": tongue_color,
                "舌体形态": tongue_body,
                "舌苔颜色": tongue_coating_color,
                "舌苔质地": tongue_coating_texture,
                "舌象其他特征": ", ".join(tongue_other) if tongue_other else "无",
                "口气": breath_smell,
                "分泌物气味": secretion_smell
            },
            "问诊_头面五官": {
                "头部症状": ", ".join(head_symptoms) if head_symptoms else "无异常",
                "头痛部位": head_pain_location,
                "眼耳口鼻症状": ", ".join(facial_symptoms) if facial_symptoms else "无异常",
                "饮水偏好": drink_preference,
                "咽喉症状": ", ".join(throat_symptoms) if throat_symptoms else "无异常"
            },
            "问诊_饮食二便": {
                "食欲": appetite,
                "饭后感觉": ", ".join(after_meal) if after_meal else "舒适",
                "口味偏好": ", ".join(food_preference) if food_preference else "无特别偏好",
                "大便频率": bowel_frequency,
                "大便性状": bowel_consistency,
                "排便感觉": ", ".join(bowel_sensation) if bowel_sensation else "排便顺畅",
                "小便颜色": urine_color,
                "小便频率/感觉": ", ".join(urine_pattern) if urine_pattern else "正常"
            },
            "问诊_睡眠情绪": {
                "睡眠问题": ", ".join(sleep_problems) if sleep_problems else "睡眠尚可",
                "梦境情况": dream_frequency,
                "情绪状态": ", ".join(emotional_state) if emotional_state else "情绪平稳",
                "不适部位": ", ".join(pain_locations) if pain_locations else "无明显疼痛",
                "其他部位": other_pain_location,
                "疼痛性质": ", ".join(pain_character) if pain_character else "无",
                "按压反应": pressure_response
            },
            "问诊_女性专属": {
                "月经周期": menstrual_cycle if gender == "女" else "不适用",
                "经量": menstrual_flow if gender == "女" else "不适用",
                "经色质地": menstrual_color if gender == "女" else "不适用",
                "经期感觉": ", ".join(menstrual_symptoms) if gender == "女" and menstrual_symptoms else "不适用",
                "白带情况": leucorrhea if gender == "女" else "不适用"
            },
            "体质环境": {
                "体质倾向": ", ".join(constitution_types) if constitution_types else "未选择",
                "压力水平": stress_level,
                "作息规律": sleep_pattern,
                "就寝时间": f"{bedtime}点" if sleep_pattern == "常熬夜" else "不适用",
                "运动频率": exercise_frequency,
                "饮食偏好": ", ".join(diet_preferences) if diet_preferences else "均衡"
            },
            "总结诉求": {
                "可能原因": possible_causes,
                "改善目标": improvement_goals,
                "补充说明": additional_notes
            }
        }

        # 保存到session state
        st.session_state.report_submitted = True
        st.session_state.report_data = report_data

        st.success("✅ 自评报告提交成功！")

# 显示报告结果
if st.session_state.report_submitted:
    st.markdown("---")
    st.header("📄 自评报告结果")

    # 创建报告摘要
    st.subheader("📋 报告摘要")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("姓名", st.session_state.report_data["基本信息"]["姓名"])
    with col2:
        st.metric("性别", st.session_state.report_data["基本信息"]["性别"])
    with col3:
        st.metric("年龄", st.session_state.report_data["基本信息"]["年龄"])

    # 显示主要症状
    st.subheader("🌡️ 主要症状摘要")

    main_symptoms = st.session_state.report_data["核心症状"]["最主要的不适"]
    if main_symptoms != "未描述":
        st.info(f"**最主要的不适：** {main_symptoms}")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**精力体力：** {st.session_state.report_data['核心症状']['精力体力']}")
        st.write(f"**怕冷/怕热：** {st.session_state.report_data['核心症状']['怕冷/怕热']}")

    with col2:
        st.write(f"**出汗情况：** {st.session_state.report_data['核心症状']['出汗情况']}")
        st.write(f"**整体寒热：** {st.session_state.report_data['核心症状']['整体寒热感觉']}")

    # 体质倾向
    constitution = st.session_state.report_data["体质环境"]["体质倾向"]
    if constitution != "未选择":
        st.subheader("🧬 体质倾向自评")
        st.write(constitution)

    # 显示DataFrame格式的报告
    st.subheader("📊 完整报告（DataFrame格式）")

    # 将嵌套字典转换为扁平格式用于DataFrame
    flat_data = {}
    for category, items in st.session_state.report_data.items():
        if isinstance(items, dict):
            for key, value in items.items():
                flat_data[f"{category}_{key}"] = value
        else:
            flat_data[category] = items

    # 创建DataFrame
    df = pd.DataFrame([flat_data])

    # 转置DataFrame以便更好地查看
    df_transposed = df.T.reset_index()
    df_transposed.columns = ["项目", "内容"]

    # 显示DataFrame
    st.dataframe(df_transposed, use_container_width=True, height=600)

    # 提供下载选项
    st.subheader("💾 导出报告")

    col1, col2 = st.columns(2)

    with col1:
        # 导出为CSV
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下载为CSV文件",
            data=csv,
            file_name=f"中医症状自评报告_{name}_{report_date}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        # 导出为Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='中医症状自评报告')

        st.download_button(
            label="下载为Excel文件",
            data=output.getvalue(),
            file_name=f"中医症状自评报告_{name}_{report_date}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )

    # 显示中医辨证提示
    st.subheader("🌿 中医辨证参考提示")

    st.markdown("""
    <div style="background-color:#f9f9f9; padding:15px; border-radius:10px; border-left:5px solid #2c7873;">
    <h4 style="color:#2c7873;">重要提示：</h4>
    <ol>
    <li>本自评报告仅为自我健康管理及就医时提供线索参考，<strong>不能替代专业中医师的"望闻问切"四诊合参</strong>。</li>
    <li>中医辨证复杂，症状常虚实夹杂、寒热交错，建议携带此报告咨询合格中医师，进行综合诊断和个性化调理。</li>
    <li>症状如有加重或出现急症，请及时就医。</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

# 侧边栏信息
with st.sidebar:
    st.image("image/1.jpg")
    st.title("中医自评指南")

    st.markdown("""
    ### 填写说明：

    1. **准确性**：请根据最近一周的真实感受填写
    2. **完整性**：带*号为必填项，其他尽量填写
    3. **客观性**：如实描述，避免主观臆断

    ### 注意事项：

    - 舌象观察请在自然光下进行
    - 症状描述尽量具体
    - 不确定的项目可选择"未描述"

    ### 中医辨证要点：

    - **八纲辨证**：阴阳、表里、寒热、虚实
    - **气血津液**：气滞、血瘀、痰湿等
    - **脏腑辨证**：心、肝、脾、肺、肾功能状态
    """)

    st.markdown("---")
    st.caption("本工具仅供参考，不替代专业医疗建议")

# 底部信息
st.markdown("---")
st.caption("© 2023 中医症状自评报告系统 | 仅供健康管理参考 | 如有急症请及时就医")