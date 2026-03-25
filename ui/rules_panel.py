"""底部規則觸發面板"""

import streamlit as st
from engine.rules import evaluate_rules
from .theme import COLORS, SVG_ICONS, get_status_icon


# 每條規則的白話文解說
RULE_EXPLANATIONS = {
    "R01": (
        "**押金擠兌螺旋**\n\n"
        "住戶退住要拿回押金，但如果入住率不到 80% 又沒有獨立信託，"
        "新住戶的押金不夠退給老住戶，就像銀行擠兌一樣 — 一旦開始就停不下來。\n\n"
        "**怎麼避免？** 設獨立信託（等級 2 以上）+ 保持入住率 80% 以上。"
    ),
    "R02": (
        "**增長飛輪**（好事）\n\n"
        "入住率高 → 住戶口碑好 → 品牌信任高 → 更多人想來住 → 入住率更高。"
        "加上保險綁定的推力，形成正向循環。\n\n"
        "**怎麼啟動？** 入住率 > 85% + 品牌信任 > 60 + 有保險綁定。"
    ),
    "R03": (
        "**品牌老化時間炸彈**\n\n"
        "住戶越住越老，外面的人看到整個社區都是 80 歲以上，"
        "年輕的 60 歲退休族就不想來了 — 覺得「那是老人院」。\n\n"
        "**怎麼避免？** 持續吸引年輕住戶入住，保持社區的年齡多樣性。"
    ),
    "R04": (
        "**信任資本飛輪**（好事）\n\n"
        "押金有獨立信託保護 → 住戶安心 → 口碑好 → 品牌信任高 → 更多人來。"
        "信託機制的成本會被品牌效益回收。\n\n"
        "**怎麼啟動？** 信託等級 >= 2 + 品牌信任 > 50。"
    ),
    "R05": (
        "**賣光沒住滿的空城陷阱**\n\n"
        "所有戶都賣出去了（簽約率高），但很多人沒實際搬進來住。"
        "社區空蕩蕩的，營運收入不夠，服務品質下降。\n\n"
        "**怎麼避免？** 關注「實際入住率」而非「簽約率」。"
    ),
    "R06": (
        "**規模 x 缺陷放大**\n\n"
        "社區小的時候有些問題可以應付，但超過 1000 戶後，"
        "如果信託不夠安全、保險沒綁定、入住率不夠高，"
        "任何一個小問題都會被放大成大危機。\n\n"
        "**怎麼避免？** 規模擴大前先補齊基礎建設（信託、保險、入住率）。"
    ),
    "R07": (
        "**醫療 x 品牌張力**\n\n"
        "一方面想「去標籤化」讓社區不像養老院，另一方面醫療整合又不足。"
        "結果兩邊都做不好 — 不像度假村也不像醫療社區。\n\n"
        "**怎麼避免？** 去標籤化程度要和醫療整合深度匹配。"
    ),
    "R08": (
        "**蘇澳距離摩擦**\n\n"
        "蘇澳離台北遠，如果園區配套又不完整、沒有體驗行銷，"
        "客人一聽到「蘇澳」就打退堂鼓，不願意跑那麼遠去看。\n\n"
        "**怎麼避免？** 加強體驗行銷（讓客人先來住住看）+ 園區配套要夠完整。"
    ),
    "R09": (
        "**營運能力缺口**\n\n"
        "住戶已經很多了，但營運團隊能力跟不上。"
        "服務品質下降 → 住戶不滿 → 口碑變差 → 品牌信任下降。\n\n"
        "**怎麼避免？** 引進專業營運夥伴，或在規模擴大前先提升團隊能力。"
    ),
    "R10": (
        "**保險飛輪台灣適配**\n\n"
        "規模已經超過 500 戶，但還沒有保險綁定通路。"
        "只靠傳統行銷很難支撐這麼大的規模所需要的新住戶量。\n\n"
        "**怎麼避免？** 在規模擴大前先談好保險合作。"
    ),
}


def _severity_bar_html(severity: int) -> str:
    """生成嚴重度指示條 HTML"""
    filled = ''.join(f'<span class="filled"></span>' for _ in range(severity))
    empty = ''.join(f'<span class="empty"></span>' for _ in range(10 - severity))
    return f'<div class="severity-bar">{filled}{empty}</div>'


def render_rules_panel(state, params):
    """渲染規則觸發狀態面板"""

    st.markdown(
        f'<div class="dash-card-header">{SVG_ICONS["sensitivity"]} 風險規則監控</div>',
        unsafe_allow_html=True,
    )

    with st.expander("什麼是「規則」？怎麼看紅黃綠燈？"):
        st.markdown(
            "模擬器內建了 **10 條規則**，每條都在監控一種特定的「風險」或「機會」。\n\n"
            "- **綠燈** = 安全，這個風險目前不存在\n\n"
            "- **黃燈** = 接近觸發，再惡化一點就會出問題\n\n"
            "- **紅燈** = 已經觸發，代表這個問題正在發生\n\n"
            "**嚴重度 1-10**：10 分是最嚴重的風險。\n\n"
            "**點擊每條規則的「了解更多」**可以看到白話解說和應對建議。"
        )

    rules = evaluate_rules(state, params)

    # 分成兩行，每行 5 個
    cols = st.columns(5)
    for i, rule in enumerate(rules):
        with cols[i % 5]:
            status = rule['status']
            status_icon = get_status_icon(status)

            st.markdown(
                f"""<div class="rule-card {status}">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                        {status_icon}
                        <strong>{rule['id']}</strong>
                    </div>
                    <div style="font-size:0.85em; color:{COLORS['text_primary']};">{rule['name']}</div>
                    <div style="font-size:0.75em; color:{COLORS['text_secondary']}; margin-top:4px;">
                        嚴重度 {rule['severity']}/10
                    </div>
                    {_severity_bar_html(rule['severity'])}
                </div>""",
                unsafe_allow_html=True,
            )

            # 白話解說（可展開）
            rule_id = rule['id']
            if rule_id in RULE_EXPLANATIONS:
                with st.popover("了解更多"):
                    st.markdown(RULE_EXPLANATIONS[rule_id])

    # 觸發規則的詳細說明
    triggered = [r for r in rules if r['status'] == 'triggered']
    warnings = [r for r in rules if r['status'] == 'warning']

    if triggered:
        st.error(
            f"**已觸發 {len(triggered)} 條規則**（需要立即注意）：\n\n" +
            "\n\n".join(f"- **{r['id']} {r['name']}** — {r['description']}" for r in triggered)
        )

    if warnings:
        st.warning(
            f"**{len(warnings)} 條規則接近觸發**（建議調整參數改善）：\n\n" +
            "\n\n".join(f"- **{r['id']} {r['name']}** — {r['description']}" for r in warnings)
        )

    if not triggered and not warnings:
        st.success("所有規則在安全範圍內 — 目前的參數組合沒有觸發任何已知風險。")
