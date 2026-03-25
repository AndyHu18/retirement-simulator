"""左側控制面板"""

import streamlit as st
from engine.parameters import SimParams, get_default_params
from engine.scenarios import STRESS_SCENARIOS


def _info_box(text: str):
    """顯示可展開的說明區塊"""
    st.markdown(
        f'<div style="background:#f0f2f6; border-radius:6px; padding:8px 10px; '
        f'margin:-8px 0 12px 0; font-size:0.82em; color:#444; line-height:1.5;">'
        f'{text}</div>',
        unsafe_allow_html=True,
    )


def render_controls() -> dict:
    """渲染左側控制面板，回傳使用者選擇的參數和設定"""
    st.header("決策控制桿")
    st.caption("每一項都是你可以調整的「決策」，調完右邊圖表會即時更新")

    # === 結構性決策 ===
    st.subheader("結構性決策")
    with st.expander("這是什麼？", expanded=False):
        st.markdown(
            "這些是**建案最一開始就要決定**、之後很難改的事情。"
            "例如第一期要蓋多少戶、要不要跟保險公司合作、押金怎麼保管等。"
            "這些選擇會大幅影響後面 25 年的所有數字。"
        )

    phase1_units = st.slider(
        "首期規模（戶）", 200, 2000, 500, 50,
        help="第一期要蓋幾戶。戶數越多，前期投資越大，但如果住滿了規模效益也越好。"
            "建議從 500 戶起步，觀察入住率後再決定第二期。"
    )

    has_insurance = st.checkbox(
        "保險綁定通路", value=False,
        help="是否跟壽險公司合作，讓買保單的人可以優先入住。"
            "像中國泰康之家就是靠保險綁定，2 年內住滿 99%。"
    )
    insurance_level = 1.0
    if has_insurance:
        insurance_level = st.slider(
            "保險綁定強度", 1.0, 3.0, 2.0, 0.1,
            help="1.0 = 只是轉介合作（保險業務員推薦），效果有限\n\n"
                "2.0 = 深度綁定（買特定保單就有入住資格），效果明顯\n\n"
                "3.0 = 泰康等級（保單和入住權完全綁定），新住戶來源可以翻 3 倍"
        )

    trust_options = [
        "0 - 無信託保護",
        "1 - 基本信託",
        "2 - 獨立信託+審批",
        "3 - 北卡等級（最高）",
    ]
    trust_choice = st.selectbox(
        "押金信託等級", trust_options,
        help="住戶交了幾千萬押金，這筆錢怎麼保管？\n\n"
            "等級 0：公司自己管（最危險，可能被挪用）\n\n"
            "等級 1：放在銀行信託，但公司還是能動用\n\n"
            "等級 2：獨立信託＋第三方審批才能動用（推薦）\n\n"
            "等級 3：美國北卡羅來納州等級，政府監管＋保證金，最安全"
    )
    trust_level = int(trust_choice[0])

    ccrc_ratio = st.slider(
        "介護棟佔比（%）", 0, 30, 15, 5,
        help="社區裡有多少比例是給「需要照護的長者」住的。\n\n"
            "0% = 純健康養生社區，身體不好的人只能搬走\n\n"
            "15% = 留一部分床位給需要照護的住戶（業界常見）\n\n"
            "30% = 接近護理之家比例，可以讓住戶在社區裡「老到底」"
    )

    medical_options = [
        "1 - 基本診所",
        "2 - 區域醫療合作",
        "3 - 醫學中心級（園區內二級醫院）",
    ]
    medical_choice = st.selectbox(
        "醫療整合深度", medical_options,
        help="園區的醫療資源有多強？這是長者選擇養老社區最在意的因素之一。\n\n"
            "等級 1：園區內設小診所，大病要外送\n\n"
            "等級 2：跟附近醫院簽合作約，有專車接送和優先看診\n\n"
            "等級 3：園區內蓋醫院，什麼病都能處理（投資最大但最有吸引力）"
    )
    medical_level = int(medical_choice[0])

    has_operator = st.checkbox(
        "專業營運夥伴", value=False,
        help="華友聯本身是建商，不是養老營運專家。\n\n"
            "勾選 = 找專業團隊（例如日本養老品牌）來負責日常經營\n\n"
            "不勾 = 自己培養團隊，前期會比較辛苦但省成本"
    )

    # === 財務參數 ===
    st.subheader("財務參數")
    with st.expander("這是什麼？", expanded=False):
        st.markdown(
            "住戶要付多少錢？社區還有什麼收入來源？"
            "這些直接決定社區的「口袋有多深」，能不能撐過入住率低的時期。"
        )

    deposit_twd = st.slider(
        "押金（萬台幣）", 1500, 4000, 2500, 100,
        help="每戶入住時要繳的保證金。\n\n"
            "1500 萬 = 門檻較低，吸引更多人，但社區現金較少\n\n"
            "2500 萬 = 中等水準\n\n"
            "4000 萬 = 高門檻，客群較窄但資金充裕\n\n"
            "退住時可退還約 90%。"
    )

    monthly_fee_twd = st.slider(
        "月費（萬台幣）", 5, 20, 10, 1,
        help="住戶每個月要繳的管理費，包含餐飲、清潔、基本服務等。\n\n"
            "5 萬 = 基本服務，利潤薄\n\n"
            "10 萬 = 包含較完整的服務和活動\n\n"
            "20 萬 = 頂級服務（五星飯店等級），只有高端客群能負擔"
    )

    has_onsen = st.checkbox(
        "冷泉/溫泉設施", value=True,
        help="蘇澳特色之一。有溫泉 = 更有吸引力，但營運成本會增加約 80%。"
            "要考慮這筆額外成本是否值得。"
    )

    other_revenue = st.slider(
        "其他收入流（萬台幣/月）", 0, 5000, 500, 100,
        help="除了月費以外的收入來源，例如：\n\n"
            "• 園區內餐廳、超商的租金\n\n"
            "• 健身房、游泳池的額外收費\n\n"
            "• 開放外部人士使用的溫泉門票\n\n"
            "• 短期試住體驗的收入\n\n"
            "多元收入可以降低對月費的依賴。"
    )

    # === 環境假設 ===
    st.subheader("環境假設")
    with st.expander("這是什麼？", expanded=False):
        st.markdown(
            "這些是**你控制不了**的外部因素，但你可以假設不同的情況。"
            "例如台灣社會對養老機構的接受度、你願意花多少力氣做體驗行銷等。"
        )

    initial_acceptance = st.slider(
        "文化接受度初始值（%）", 1, 20, 5, 1,
        help="目前台灣有多少比例的人願意住進養老社區。\n\n"
            "現實中台灣約 5% — 大部分人還是覺得「住養老院 = 被子女拋棄」。\n\n"
            "數字越高代表你假設社會觀念越開放。這個值會每年緩慢成長。"
    )

    experience_level = st.slider(
        "體驗行銷投入", 0, 3, 1,
        help="讓潛在客戶「先來住住看」的投入程度。\n\n"
            "0 = 完全不做，等客人自己來（最省錢但轉化率低）\n\n"
            "1 = 基本參觀日和說明會\n\n"
            "2 = 提供 1-3 天免費試住體驗\n\n"
            "3 = 泰康級，在各城市設體驗中心＋長期試住方案（最貴但效果最好）"
    )

    debranding = st.slider(
        "去標籤化程度", 1, 3, 2,
        help="社區給人的感覺像什麼？\n\n"
            "1 = 傳統養老院（長者可能抗拒）\n\n"
            "2 = 生活社區（強調「生活方式」而非「養老」）\n\n"
            "3 = 度假社區（完全沒有養老院的感覺，但可能和醫療形象矛盾）"
    )

    community_sufficiency = st.slider(
        "園區配套完整度", 0, 3, 1,
        help="園區本身有多「自給自足」？蘇澳離市區遠，配套不足會很不方便。\n\n"
            "0 = 純住宅，什麼都要出園區買\n\n"
            "1 = 有基本餐廳和小超市\n\n"
            "2 = 有完整商業區、藥局、銀行\n\n"
            "3 = 像一個小城市，幾乎不需要出門"
    )

    # === 模擬設定 ===
    st.subheader("模擬設定")
    with st.expander("這是什麼？", expanded=False):
        st.markdown(
            "**蒙地卡羅模擬**：因為未來有不確定性（經濟好壞、突發事件等），"
            "所以我們不只跑一次模擬，而是跑上千次，每次隨機產生不同的未來情境。"
            "這樣就能看到「最好的情況」到「最差的情況」的完整範圍。\n\n"
            "**壓力測試**：故意假設發生特定壞事（例如經濟衰退），看社區撐不撐得住。"
        )

    sim_options = [100, 500, 1000, 5000, 10000]
    n_simulations = st.selectbox(
        "蒙地卡羅次數", sim_options, index=2,
        help="跑幾次隨機模擬。\n\n"
            "100 次 = 快但不太準（約 1 秒）\n\n"
            "1000 次 = 夠用（約 12 秒）\n\n"
            "10000 次 = 最精確（約 2 分鐘）"
    )

    run_stress = st.checkbox(
        "跑壓力測試", value=False,
        help="模擬如果發生特定壞事（例如經濟衰退、信任危機），社區會怎樣。"
    )
    stress_scenario = None
    if run_stress:
        scenario_names = {k: v['name'] for k, v in STRESS_SCENARIOS.items()}
        stress_key = st.selectbox(
            "壓力情境",
            list(scenario_names.keys()),
            format_func=lambda x: f"{scenario_names[x]} — {STRESS_SCENARIOS[x]['description']}",
            help="選擇要模擬哪種壞事。「複合災難」是最嚴苛的測試，"
                "同時發生經濟衰退＋成本暴漲。"
        )
        stress_scenario = stress_key

    # === 組裝參數 ===
    params = get_default_params()
    params.phase_configs[0].units = phase1_units
    params.deposit_amount = deposit_twd * 10_000
    params.monthly_fee = monthly_fee_twd * 10_000
    params.insurance_factor = insurance_level
    params.trust_mechanism_level = trust_level
    params.trust_independent = trust_level >= 2
    params.ccrc_care_ratio = ccrc_ratio / 100
    params.medical_integration = medical_level
    params.has_onsen = has_onsen
    params.other_revenue_monthly = other_revenue * 10_000
    params.initial_cultural_acceptance = initial_acceptance / 100
    params.experience_level = experience_level
    params.debranding_level = debranding
    params.community_self_sufficiency = community_sufficiency
    params.has_professional_operator = has_operator
    if has_operator:
        params.initial_operational_capability = 55.0
        params.team_quality = 1.3

    return {
        'params': params,
        'n_simulations': n_simulations,
        'run_stress': run_stress,
        'stress_scenario': stress_scenario,
    }
