"""左側控制面板 — v2 快速/進階模式"""

import copy
import streamlit as st
from engine.parameters import (
    SimParams, get_default_params,
    CAPITAL_STRUCTURE_PRESETS, DEPOSIT_MODEL_PRESETS,
    EXPERIENCE_PRESETS, MEDICAL_PRESETS, ONSEN_PRESETS,
    OPERATOR_PRESETS, MACRO_PRESETS, REGULATORY_PRESETS,
    AGING_COUNTERMEASURE_EFFECTS, REVENUE_STREAM_ESTIMATES,
)
from engine.scenarios import STRESS_SCENARIOS


def _apply_preset(params: SimParams, preset: dict):
    """把 preset 的值套用到 params"""
    for k, v in preset.items():
        if hasattr(params, k):
            setattr(params, k, v)


def render_controls() -> dict:
    """渲染左側控制面板，回傳使用者選擇的參數和設定"""
    st.header("決策控制桿")

    # === 模式切換 ===
    advanced = st.toggle("進階模式", value=False,
                          help="快速模式：5 個策略下拉即可開始。進階模式：可微調所有底層參數。")

    if not advanced:
        st.caption("5 個核心決策即可模擬。切到進階模式可看到所有底層參數。")
    else:
        st.caption("策略下拉會填入預設值，你可以在展開的面板中覆蓋任何數字。")

    params = get_default_params()

    # ================================================================
    # Group 1: 資本與財務策略
    # ================================================================
    st.subheader("資本與財務")

    # 1.1 資本結構
    capital_sel = st.selectbox("資本結構", list(CAPITAL_STRUCTURE_PRESETS.keys()),
        help="資金從哪裡來？決定了你「等得起多久」。\n\n"
             "自有資金：口袋淺但自主性高\n\n"
             "壽險資金：口袋深、耐心長（泰康模式）\n\n"
             "銀行貸款：利息高、壓力大\n\n"
             "混合：最常見的做法")
    cap_preset = CAPITAL_STRUCTURE_PRESETS[capital_sel]
    _apply_preset(params, cap_preset)

    if advanced:
        with st.expander(f"資本結構底層參數"):
            params.total_budget_twd = st.slider(
                "總投資預算（億台幣）", 300, 1500,
                int(cap_preset['total_budget_twd'] / 1e8), 50,
                help="整個專案可動用的資金總額") * 1e8
            params.annual_cost_of_capital = st.slider(
                "年化資金成本（%）", 1.0, 10.0,
                cap_preset['annual_cost_of_capital'] * 100, 0.5,
                help="每年要付的利息或資金報酬率") / 100
            params.payback_tolerance_years = st.slider(
                "回收期容忍度（年）", 5, 40,
                cap_preset['payback_tolerance_years'], 1,
                help="投資人能接受幾年內回本")

    # 1.2 押金模式
    deposit_sel = st.selectbox("押金退還模式", list(DEPOSIT_MODEL_PRESETS.keys()),
        help="住戶的押金怎麼退？這直接影響擠兌風險。\n\n"
             "全額可退：住戶安心，但退費壓力大\n\n"
             "漸進償卻：5年後退費歸零，大幅降低擠兌風險")
    dep_preset = DEPOSIT_MODEL_PRESETS[deposit_sel]
    _apply_preset(params, dep_preset)

    if advanced:
        with st.expander(f"押金模式底層參數"):
            params.refund_percentage = st.slider(
                "退還比例（%）", 0, 100,
                int(dep_preset['refund_percentage'] * 100), 5) / 100
            if dep_preset.get('amortization_years', 0) > 0:
                params.amortization_years = st.slider(
                    "償卻年限", 3, 10, dep_preset['amortization_years'], 1,
                    help="幾年後退費義務歸零")

    # 1.3 押金金額和月費
    deposit_twd = st.slider("押金（萬台幣）", 500, 4000,
        int(2500 * dep_preset.get('deposit_amount_multiplier', 1.0)), 100,
        help="每戶入住時繳的保證金")
    params.deposit_amount = deposit_twd * 10_000

    monthly_fee_twd = st.slider("月費（萬台幣）", 5, 20, 10, 1,
        help="每月管理費（含餐飲、清潔、基本服務）")
    params.monthly_fee = monthly_fee_twd * 10_000

    # 1.4 押金信託
    trust_options = [
        "0 - 無信託保護",
        "1 - 基本信託",
        "2 - 獨立信託+審批",
        "3 - 北卡等級（最高）",
    ]
    trust_choice = st.selectbox("押金信託等級", trust_options,
        help="住戶的幾千萬押金怎麼保管？等級越高住戶越安心。")
    trust_level = int(trust_choice[0])
    params.trust_mechanism_level = trust_level
    params.trust_independent = trust_level >= 2

    # ================================================================
    # Group 2: 需求引擎策略
    # ================================================================
    st.subheader("需求引擎")

    # 2.1 保險綁定
    has_insurance = st.checkbox("保險綁定通路", value=False,
        help="跟壽險公司合作，讓保戶優先入住（泰康模式）")
    if has_insurance:
        params.insurance_factor = st.slider("保險綁定強度", 1.0, 3.0, 2.0, 0.1,
            help="1.0=轉介  2.0=深度綁定  3.0=泰康級")
        if advanced:
            params.insurance_start_quarter = st.slider(
                "保險通路上線時間（第幾季）", 0, 20, 8, 1,
                help="保險合作需要時間準備，通常第2-3年才上線")
    else:
        params.insurance_factor = 1.0

    # 2.2 體驗行銷
    exp_sel = st.selectbox("體驗行銷策略", list(EXPERIENCE_PRESETS.keys()),
        help="讓潛在客戶「先來住住看」的投入程度")
    exp_preset = EXPERIENCE_PRESETS[exp_sel]
    _apply_preset(params, exp_preset)

    if advanced:
        with st.expander("體驗行銷底層參數"):
            params.conversion_boost = st.slider(
                "轉化率加成", 1.0, 2.0, exp_preset['conversion_boost'], 0.05,
                help="體驗行銷帶來的入住率提升")
            params.experience_monthly_cost = st.slider(
                "月成本（萬台幣）", 0, 5000,
                int(exp_preset['experience_monthly_cost'] / 10_000), 100) * 10_000

    # 2.3 H 會館客群
    if advanced:
        with st.expander("H會館客群導入"):
            params.h_hotel_funnel_active = st.checkbox("啟用H會館客群導入", value=True)
            if params.h_hotel_funnel_active:
                params.h_hotel_annual_contacts = st.slider(
                    "年度活動客群（人）", 2000, 15000, 6000, 500)
                params.h_hotel_inquiry_rate = st.slider(
                    "客群→諮詢轉化率（%）", 1, 10, 3, 1) / 100
                params.h_hotel_close_rate = st.slider(
                    "諮詢→入住轉化率（%）", 5, 25, 12, 1) / 100

    # 2.4 行銷預算
    if advanced:
        params.marketing_budget_monthly = st.slider(
            "月行銷預算（萬台幣）", 100, 5000, 500, 100,
            help="越高越能克服蘇澳的距離劣勢") * 10_000

    # ================================================================
    # Group 3: 產品與營運策略
    # ================================================================
    st.subheader("產品與營運")

    # 3.1 醫療整合
    med_sel = st.selectbox("醫療整合層級", list(MEDICAL_PRESETS.keys()),
        help="醫療是長者選養老社區最在意的事")
    med_preset = MEDICAL_PRESETS[med_sel]
    _apply_preset(params, med_preset)

    if advanced:
        with st.expander("醫療底層參數"):
            params.medical_occupancy_boost = st.slider(
                "入住率加成", 1.0, 1.5, med_preset['medical_occupancy_boost'], 0.05)
            params.medical_external_revenue = st.checkbox(
                "醫療設施對外營業", value=False,
                help="開放給非住戶使用（健檢/復健），可增加收入")

    # 3.2 CCRC 配比
    ccrc_ratio = st.slider("介護棟佔比（%）", 0, 30, 15, 5,
        help="社區裡留多少比例給需要照護的長者")
    params.ccrc_care_ratio = ccrc_ratio / 100

    # 3.3 溫泉規格
    onsen_sel = st.selectbox("冷泉/溫泉規格", list(ONSEN_PRESETS.keys()),
        help="蘇澳特色。有溫泉更有吸引力，但營運成本高。")
    ons_preset = ONSEN_PRESETS[onsen_sel]
    _apply_preset(params, ons_preset)

    if advanced:
        with st.expander("溫泉底層參數"):
            params.onsen_external_revenue = st.slider(
                "溫泉對外月收入（萬台幣）", 0, 2000,
                int(ons_preset.get('onsen_external_revenue', 0) / 10_000), 100) * 10_000

    # 3.4 營運策略
    op_sel = st.selectbox("營運策略", list(OPERATOR_PRESETS.keys()),
        help="誰來經營日常營運？建商轉型做養老有學習曲線。")
    op_preset = OPERATOR_PRESETS[op_sel]
    _apply_preset(params, op_preset)
    if op_preset.get('initial_operational_capability', 0) >= 50:
        params.has_professional_operator = True

    if advanced:
        with st.expander("營運底層參數"):
            params.staff_turnover_rate = st.slider(
                "年人員流失率（%）", 2, 30,
                int(op_preset['staff_turnover_rate'] * 100), 1) / 100
            params.learning_rate = st.slider(
                "團隊學習速率", 0.3, 2.0, op_preset['learning_rate'], 0.1)

    # 3.5 去標籤化
    params.debranding_level = st.slider("去養老標籤化程度", 1, 3, 2,
        help="1=保守（養生語言） 2=中度（生活方式） 3=激進（純生活品牌）")

    # ================================================================
    # Group 4: 開發節奏
    # ================================================================
    if advanced:
        st.subheader("開發節奏")

        with st.expander("各期規模分配"):
            default_units = [500, 700, 800, 1000, 1000, 1200, 1300, 1500]
            phase_units = []
            cols = st.columns(4)
            for i in range(8):
                with cols[i % 4]:
                    u = st.number_input(f"第{i+1}期（戶）", 100, 2500, default_units[i], 50)
                    phase_units.append(u)
            from engine.parameters import PhaseConfig
            params.phase_configs = [
                PhaseConfig(units=u, construction_cost=u * 5_000_000)
                for u in phase_units
            ]
            st.metric("總戶數", f"{sum(phase_units):,}")

        params.phase_activation_threshold = st.slider(
            "前期入住率達標線", 0.60, 0.95, 0.80, 0.05,
            help="前一期入住率達到此值才啟動下一期建設")
        params.min_days_cash_for_new_phase = st.slider(
            "最低現金儲備天數", 100, 500, 250, 50,
            help="應急儲備低於此天數時不啟動新期")

        # 品牌老化對抗
        with st.expander("品牌老化對抗策略"):
            aging_sels = st.multiselect("選擇對抗措施",
                list(AGING_COUNTERMEASURE_EFFECTS.keys()),
                help="可多選，效果疊加但上限70%")
            total_decay_red = 0
            total_age_red = 0
            total_aging_cost = 0
            total_aging_rev = 0
            for sel in aging_sels:
                eff = AGING_COUNTERMEASURE_EFFECTS[sel]
                total_decay_red += eff.get('brand_vitality_decay_reduction', 0)
                total_age_red += eff.get('new_resident_avg_age_reduction', 0)
                total_aging_cost += eff.get('additional_monthly_cost', 0)
                total_aging_rev += eff.get('additional_monthly_revenue', 0)
            params.brand_vitality_decay_reduction = min(0.70, total_decay_red)
            params.new_resident_avg_age_reduction = total_age_red
            params.aging_countermeasure_cost = total_aging_cost
            params.aging_countermeasure_revenue = total_aging_rev

        # 多元收入流
        with st.expander("多元收入流"):
            stream_sels = st.multiselect("選擇收入來源",
                list(REVENUE_STREAM_ESTIMATES.keys()),
                help="可多選。有些需要對應設施（如溫泉SPA需要溫泉）")
            total_stream_rev = 0
            total_stream_setup = 0
            stream_configs = []
            for sel in stream_sels:
                info = REVENUE_STREAM_ESTIMATES[sel]
                if info.get('requires_onsen') and not params.has_onsen:
                    st.warning(f"{sel} 需要溫泉設施，已跳過")
                    continue
                if info.get('requires_ccrc') and params.ccrc_care_ratio == 0:
                    st.warning(f"{sel} 需要介護設施，已跳過")
                    continue
                total_stream_rev += info['monthly_revenue']
                total_stream_setup += info['setup_cost']
                stream_configs.append({
                    **info,
                    'activation_quarter': info.get('ramp_up_quarters', 4),
                })
            params.total_stream_monthly_revenue = total_stream_rev
            params.revenue_stream_setup_cost = total_stream_setup
            params.other_revenue_monthly += total_stream_rev
            params._revenue_stream_configs = stream_configs

    else:
        # 快速模式：首期規模
        phase1_units = st.slider("首期規模（戶）", 200, 2000, 500, 50,
            help="第一期蓋幾戶。建議 500 戶起步。")
        params.phase_configs[0].units = phase1_units
        params.phase_configs[0].construction_cost = phase1_units * 5_000_000

    # ================================================================
    # Group 5: 外部環境假設
    # ================================================================
    st.subheader("外部環境")

    initial_acceptance = st.slider("文化接受度初始值（%）", 1, 20, 5, 1,
        help="目前台灣約5%的人願意住養老社區")
    params.initial_cultural_acceptance = initial_acceptance / 100

    if advanced:
        params.annual_acceptance_growth = st.slider(
            "文化接受度年增長率（百分點）", 0.5, 4.0, 2.0, 0.5,
            help="每年增加的百分點。台灣預估 1.5-2.5") / 100

        # 宏觀經濟
        macro_sel = st.selectbox("宏觀經濟假設", list(MACRO_PRESETS.keys()),
            help="經濟環境的波動程度")
        _apply_preset(params, MACRO_PRESETS[macro_sel])

        # 法規環境
        reg_sel = st.selectbox("法規環境演進", list(REGULATORY_PRESETS.keys()),
            help="台灣未來是否會出台CCRC專法？這影響信託的品牌價值。")
        _apply_preset(params, REGULATORY_PRESETS[reg_sel])

        # 競品
        params.competitor_entry = st.checkbox("模擬強力競品進入", value=False)
        if params.competitor_entry:
            params.competitor_year = st.slider("競品進入年份", 3, 20, 8)
            comp_strength = st.selectbox("競品強度", [
                "中度（分流10-15%需求）",
                "強勢（國泰/富邦級，分流25-35%）"
            ])
            if "強勢" in comp_strength:
                params.competitor_diversion_rate = 0.30
                params.competitor_brand_shock = 15
            else:
                params.competitor_diversion_rate = 0.12
                params.competitor_brand_shock = 5

        params.community_self_sufficiency = st.slider(
            "園區配套完整度", 0, 3, 1,
            help="園區自給自足程度。蘇澳離市區遠，配套很重要。")
    else:
        params.community_self_sufficiency = st.slider(
            "園區配套完整度", 0, 3, 1,
            help="0=純住宅  1=基本餐廳  2=完整商業  3=小城市")

    # ================================================================
    # 模擬設定
    # ================================================================
    st.subheader("模擬設定")

    sim_options = [100, 500, 1000, 5000, 10000]
    n_simulations = st.selectbox("蒙地卡羅次數", sim_options, index=2,
        help="100次=快但粗  1000次=夠用  10000次=精確")

    run_stress = st.checkbox("跑壓力測試", value=False,
        help="模擬特定壞事發生時社區撐不撐得住")
    stress_scenario = None
    if run_stress:
        scenario_names = {k: v['name'] for k, v in STRESS_SCENARIOS.items()}
        stress_key = st.selectbox("壓力情境",
            list(scenario_names.keys()),
            format_func=lambda x: f"{scenario_names[x]} — {STRESS_SCENARIOS[x]['description']}")
        stress_scenario = stress_key

    return {
        'params': params,
        'n_simulations': n_simulations,
        'run_stress': run_stress,
        'stress_scenario': stress_scenario,
    }
