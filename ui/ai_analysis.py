"""Claude Sonnet 4.6 AI 智能解讀"""

import os
from pathlib import Path
import streamlit as st
import numpy as np
from .theme import SVG_ICONS
from engine.monte_carlo import compute_percentiles, calculate_summary_metrics


def _load_api_key() -> str:
    """從 Streamlit secrets、環境變數或 .env 檔讀取 API key"""
    # 1. Streamlit Cloud secrets（部署時用）
    try:
        key = st.secrets.get('ANTHROPIC_API_KEY', '')
        if key:
            return key
    except Exception:
        pass
    # 2. 環境變數
    key = os.environ.get('ANTHROPIC_API_KEY', '')
    if key:
        return key
    # 3. .env 檔（本機開發用）
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        for line in env_path.read_text().strip().splitlines():
            line = line.strip()
            if line.startswith('ANTHROPIC_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"')
                os.environ['ANTHROPIC_API_KEY'] = key
                return key
    return ''


def _format_simulation_context(single_results: dict, mc_results: dict,
                                sensitivity: list, params, rules_status: list) -> str:
    """把模擬結果整理成結構化 prompt"""
    metrics = calculate_summary_metrics(mc_results)
    occ_pcts = compute_percentiles(mc_results, 'occupancy_rate')
    fund_pcts = compute_percentiles(mc_results, 'fund_pool_total')

    # 參數設定
    param_text = f"""## 目前的參數設定
| 參數 | 設定值 |
|------|--------|
| 首期規模 | {params.phase_configs[0].units} 戶 |
| 押金 | {params.deposit_amount/10000:.0f} 萬台幣 |
| 月費 | {params.monthly_fee/10000:.0f} 萬台幣/月 |
| 保險綁定強度 | {params.insurance_factor:.1f}（1.0=無, 3.0=泰康級）|
| 信託機制等級 | {params.trust_mechanism_level}（0=無保護, 3=北卡等級）|
| 獨立信託 | {'是' if params.trust_independent else '否'} |
| 醫療整合深度 | {params.medical_integration}（1=基本, 3=醫學中心級）|
| 溫泉設施 | {'有' if params.has_onsen else '無'} |
| 專業營運夥伴 | {'有' if params.has_professional_operator else '無'} |
| 體驗行銷投入 | {params.experience_level}/3 |
| 去標籤化程度 | {params.debranding_level}/3 |
| 園區配套完整度 | {params.community_self_sufficiency}/3 |
| 文化接受度初始值 | {params.initial_cultural_acceptance*100:.0f}% |
| 選址 | {'蘇澳' if params.location == 'suao' else '都市近郊'} |"""

    # 關鍵指標
    metrics_text = f"""## 關鍵指標（蒙地卡羅模擬結果）
| 指標 | 數值 | 安全標準 |
|------|------|---------|
| 25年資金池耗盡機率 | {metrics['depletion_prob']:.1%} | <5%安全, 5-20%注意, >20%危險 |
| 首期達85%入住率 | {metrics['median_fill_years']:.1f} 年 | <5年安全, 5-10年注意, >10年危險 |
| 品牌老化觸發時間 | {metrics['median_aging_trigger']:.0f} 年 | >15年安全, 10-15年注意, <10年危險 |
| 無新血存活期 | {metrics['no_new_blood_survival']:.0f} 個月 | >48月安全, 24-48月注意, <24月危險 |"""

    # 時間軌跡百分位
    years = [5, 10, 15, 20, 25]
    steps = [y * 4 - 1 for y in years]
    trajectory_text = "## 入住率軌跡（蒙地卡羅百分位）\n| 年份 | P5（最差5%）| P25 | P50（最可能）| P75 | P95（最好5%）|\n|------|-----------|-----|------------|-----|------------|\n"
    for y, s in zip(years, steps):
        trajectory_text += f"| 第{y}年 | {occ_pcts['p5'][s]:.0%} | {occ_pcts['p25'][s]:.0%} | {occ_pcts['p50'][s]:.0%} | {occ_pcts['p75'][s]:.0%} | {occ_pcts['p95'][s]:.0%} |\n"

    fund_text = "## 資金池軌跡（億台幣）\n| 年份 | P5 | P25 | P50 | P75 | P95 |\n|------|-----|-----|-----|-----|-----|\n"
    for y, s in zip(years, steps):
        fund_text += f"| 第{y}年 | {fund_pcts['p5'][s]/1e8:.0f} | {fund_pcts['p25'][s]/1e8:.0f} | {fund_pcts['p50'][s]/1e8:.0f} | {fund_pcts['p75'][s]/1e8:.0f} | {fund_pcts['p95'][s]/1e8:.0f} |\n"

    # 敏感度
    sens_text = "## 敏感度排名（影響力最大的因素）\n| 排名 | 參數 | 對入住率影響 | 對資金池影響 |\n|------|------|------------|------------|\n"
    for i, s in enumerate(sensitivity[:5]):
        sens_text += f"| {i+1} | {s['label']} | {s['corr_occupancy']:.2f} | {s['corr_fund']:.2f} |\n"

    # 規則
    triggered = [r for r in rules_status if r['status'] == 'triggered']
    warnings = [r for r in rules_status if r['status'] == 'warning']
    rules_text = "## 風險規則觸發狀態\n"
    if triggered:
        rules_text += "**已觸發（紅燈）：**\n"
        for r in triggered:
            rules_text += f"- {r['id']} {r['name']}（嚴重度 {r['severity']}/10）: {r['description']}\n"
    if warnings:
        rules_text += "**接近觸發（黃燈）：**\n"
        for r in warnings:
            rules_text += f"- {r['id']} {r['name']}（嚴重度 {r['severity']}/10）: {r['description']}\n"
    if not triggered and not warnings:
        rules_text += "所有規則在安全範圍內（全部綠燈）\n"

    # 單次模擬最終值
    final_text = f"""## 單次模擬最終狀態（第25年）
- 入住率: {single_results['occupancy_rate'][-1]:.1%}
- 資金池: {single_results['fund_pool_total'][-1]/1e8:.0f} 億台幣
- 品牌信任: {single_results['brand_trust'][-1]:.0f}/100
- 品牌活力: {single_results['brand_vitality'][-1]:.0f}/100
- 營運能力: {single_results['operational_capability'][-1]:.0f}/100"""

    return f"{param_text}\n\n{metrics_text}\n\n{trajectory_text}\n{fund_text}\n{sens_text}\n{rules_text}\n{final_text}"


def _call_claude(context: str) -> dict:
    """呼叫 Claude Sonnet 4.6 進行分析"""
    api_key = _load_api_key()
    if not api_key:
        return {'error': '未設定 ANTHROPIC_API_KEY 環境變數。請在系統環境變數中設定後重新啟動。'}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """你是一位資深的養老社區開發顧問，正在為決策者分析模擬結果。

決策者不是工程師，所以你必須：
1. 用白話文解釋所有內容，避免專業術語
2. 給出具體、可操作的建議
3. 直接說好壞，不要模稜兩可

請嚴格按照以下格式回答（繁體中文）：

## 總體評估
用 3 句話摘要整體狀況。第一句話明確說「這個方案【安全/有風險/很危險】」。

## 關鍵發現
列出 3-5 個最重要的發現，每一條用一句白話文說明。

## 風險分析
分析最可能出錯的 2-3 件事，以及發生的可能性（高/中/低）和後果。

## 策略建議
給出 3-5 個具體行動建議，按優先順序排列。每條建議要說清楚「做什麼」和「為什麼」。

## 下一步測試
建議接下來應該調整哪些參數重新模擬，以及為什麼要這樣測。"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000,
            },
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"請分析以下養生造鎮專案的模擬結果，並給出白話文解讀和策略建議：\n\n{context}",
                }
            ],
        )

        # 解析回應
        analysis_text = ''
        thinking_text = ''
        for block in response.content:
            if block.type == 'thinking':
                thinking_text = block.thinking
            elif block.type == 'text':
                analysis_text = block.text

        return {
            'analysis': analysis_text,
            'thinking': thinking_text,
            'error': None,
        }

    except Exception as e:
        return {'error': f'API 呼叫失敗：{str(e)}'}


def render_ai_analysis(single_results: dict, mc_results: dict,
                        sensitivity: list, params, rules_status: list):
    """渲染 AI 智能解讀區塊"""

    st.markdown(
        f"""<div class="dash-card-header">
            {SVG_ICONS['ai']} AI 智能解讀
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption("讓 AI 顧問用白話文幫你分析模擬結果，並給出具體的方向建議")

    # 檢查 API Key
    api_key = _load_api_key()
    if not api_key:
        st.warning(
            "尚未設定分析金鑰。請聯絡管理員設定後重新啟動系統。"
        )
        return

    # 按鈕
    col1, col2 = st.columns([1, 4])
    with col1:
        run_ai = st.button("開始 AI 解讀", type="secondary",
                            help="將模擬結果傳給 AI 顧問進行分析，約需 15-30 秒")
    with col2:
        if st.session_state.get('ai_analysis'):
            if st.button("重新分析"):
                st.session_state.pop('ai_analysis', None)
                st.rerun()

    # 執行分析
    if run_ai:
        with st.spinner("AI 顧問正在分析你的模擬結果...（約需 15-30 秒）"):
            context = _format_simulation_context(
                single_results, mc_results, sensitivity, params, rules_status
            )
            result = _call_claude(context)
            st.session_state['ai_analysis'] = result

    # 顯示結果
    cached = st.session_state.get('ai_analysis')
    if cached:
        if cached.get('error'):
            st.error(f"分析失敗：{cached['error']}")
            st.info("請確認分析金鑰是否正確，或稍後重試。")
        else:
            # 顯示分析內容
            st.markdown(
                f'<div class="ai-card">{""}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(cached['analysis'])

            # 思考過程不顯示（AI 內部推理，非使用者介面內容）
