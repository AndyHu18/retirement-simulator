"""養生造鎮決策模擬器 — Streamlit 主介面"""

import streamlit as st
from engine.model import run_simulation
from engine.monte_carlo import run_monte_carlo, run_sensitivity_analysis
from engine.scenarios import STRESS_SCENARIOS
from engine.rules import evaluate_rules
from ui.controls import render_controls
from ui.dashboard import render_dashboard
from ui.rules_panel import render_rules_panel
from ui.theme import apply_theme, SVG_ICONS
from ui.guide import render_guide
from ui.ai_analysis import render_ai_analysis


st.set_page_config(
    page_title="養生造鎮決策模擬器",
    page_icon="🏘️",
    layout="wide",
)

# 套用專業視覺主題
apply_theme()

st.markdown(
    '<div class="main-header">'
    '<h1>華友聯蘇澳養生造鎮 — 決策模擬器</h1>'
    '<p>模擬未來 25 年的營運軌跡，找到最安全的決策組合</p>'
    '</div>',
    unsafe_allow_html=True,
)

# === 操作說明 ===
render_guide()

# === 左側控制面板 ===
with st.sidebar:
    controls = render_controls()

params = controls['params']
n_simulations = controls['n_simulations']
stress_scenario = controls['stress_scenario']

# 壓力測試覆蓋
stress_overrides = None
if controls['run_stress'] and stress_scenario:
    stress_overrides = STRESS_SCENARIOS[stress_scenario]['overrides']

# === 單次確定性模擬（即時） ===
single_results = run_simulation(params, n_steps=100, seed=42,
                                stress_overrides=stress_overrides)

# === 蒙地卡羅模擬（按鈕觸發） ===
mc_results = st.session_state.get('mc_results', None)
sensitivity = st.session_state.get('sensitivity', None)

st.divider()

col_btn1, col_btn2 = st.columns([1, 3])
with col_btn1:
    run_mc = st.button(
        f"開始蒙地卡羅模擬（{n_simulations}次）",
        type="primary",
        help="點擊後會跑上千次隨機模擬，讓你看到各種可能情境下的結果分布。"
            "跑完後「蒙地卡羅分布」和「敏感度分析」兩個分頁才會有內容。"
    )

if run_mc:
    with st.spinner(f"正在跑 {n_simulations} 次模擬，請稍候..."):
        progress = st.progress(0)

        def update_progress(current, total):
            progress.progress(current / total)

        mc_results = run_monte_carlo(
            params,
            n_simulations=n_simulations,
            n_steps=100,
            stress_overrides=stress_overrides,
            progress_callback=update_progress,
        )
        st.session_state['mc_results'] = mc_results

        # 敏感度分析（用較少次數）
        sensitivity = run_sensitivity_analysis(
            params, n_simulations=min(500, n_simulations),
        )
        st.session_state['sensitivity'] = sensitivity

        progress.empty()

# === 主儀表板 ===
render_dashboard(single_results, mc_results, sensitivity)

# === AI 智能解讀 ===
if mc_results is not None:
    st.divider()
    final_state = single_results.get('final_state')
    rules_status = evaluate_rules(final_state, params) if final_state else []
    render_ai_analysis(single_results, mc_results, sensitivity or [], params, rules_status)

# === 規則觸發面板 ===
st.divider()
final_state = single_results.get('final_state')
if final_state:
    render_rules_panel(final_state, params)

# === 壓力測試說明 ===
if controls['run_stress'] and stress_scenario:
    st.divider()
    sc = STRESS_SCENARIOS[stress_scenario]
    st.info(
        f"**壓力測試情境：{sc['name']}**\n\n"
        f"{sc['description']}\n\n"
        f"壓力測試 = 故意模擬壞事發生，看社區撐不撐得住。"
        f"如果壓力測試下結果還能接受，代表方案的安全邊際足夠。"
    )

# === 頁尾 ===
st.divider()
st.caption(
    "模擬器基於存量-流量模型 + 蒙地卡羅方法。"
    "所有數值為模擬結果，僅供決策參考，不構成投資建議。"
    "金額單位：新台幣。時間步長：每季度（3個月）。模擬期間：25年。"
)
