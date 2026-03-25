"""右側結果儀表板"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from engine.monte_carlo import compute_percentiles, calculate_summary_metrics
from .theme import COLORS, SVG_ICONS


def _quarter_to_year_labels(n_steps: int) -> list:
    return [t / 4 for t in range(n_steps)]


def _chart_defaults() -> dict:
    return dict(
        template='plotly_white',
        font=dict(family='Inter, Noto Sans TC, sans-serif', size=13),
        title_font=dict(size=15, color=COLORS['text_primary']),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )


def plot_fan_chart(mc_results: dict, metric: str, title: str,
                   x_label: str = "營運年數（年）",
                   y_label: str = "",
                   thresholds: list = None,
                   threshold_labels: list = None,
                   is_percentage: bool = False,
                   is_billion: bool = False) -> go.Figure:
    """繪製扇形圖（蒙地卡羅百分位帶）"""
    pcts = compute_percentiles(mc_results, metric)
    n_steps = len(pcts['p50'])
    x = _quarter_to_year_labels(n_steps)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=list(pcts['p95']) + list(pcts['p5'][::-1]),
        fill='toself',
        fillcolor='rgba(37, 99, 235, 0.08)',
        line=dict(color='rgba(255,255,255,0)'),
        name='90%可能範圍',
        showlegend=True,
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=list(pcts['p75']) + list(pcts['p25'][::-1]),
        fill='toself',
        fillcolor='rgba(37, 99, 235, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='50%可能範圍',
        showlegend=True,
        hoverinfo='skip',
    ))

    hover_fmt = '第 %{x:.1f} 年<br>最可能值: %{y'
    if is_percentage:
        hover_fmt += ':.1%'
    elif is_billion:
        hover_fmt += ':.1f} 億台幣'
    else:
        hover_fmt += ':.1f'
    hover_fmt += '<extra></extra>'

    fig.add_trace(go.Scatter(
        x=x, y=list(pcts['p50']),
        mode='lines',
        line=dict(color=COLORS['primary'], width=2.5),
        name='最可能走勢',
        hovertemplate=hover_fmt,
    ))

    if thresholds and threshold_labels:
        colors = [COLORS['danger'], COLORS['warning'], COLORS['success'], COLORS['primary']]
        for i, (threshold, label) in enumerate(zip(thresholds, threshold_labels)):
            fig.add_hline(
                y=threshold, line_dash="dash",
                line_color=colors[i % len(colors)],
                annotation_text=label, annotation_position="right",
            )

    tickformat = '.0%' if is_percentage else ('.1f' if is_billion else '')

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        yaxis=dict(tickformat=tickformat),
        height=400,
        margin=dict(l=70, r=20, t=50, b=50),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        **_chart_defaults(),
    )
    return fig


def plot_single_run(results: dict) -> go.Figure:
    """繪製單次模擬結果（4 子圖），每張都有清楚 XY 軸"""
    n_steps = len(results['occupancy_rate'])
    x = _quarter_to_year_labels(n_steps)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['入住率', '資金池', '品牌信任', '品牌活力指數'],
        vertical_spacing=0.18,
        horizontal_spacing=0.12,
    )

    # 入住率
    fig.add_trace(go.Scatter(
        x=x, y=list(results['occupancy_rate']),
        mode='lines', name='入住率',
        line=dict(color=COLORS['primary']),
        hovertemplate='第 %{x:.1f} 年<br>入住率: %{y:.1%}<extra></extra>',
    ), row=1, col=1)
    fig.add_hline(y=0.85, line_dash='dash', line_color=COLORS['success'],
                  annotation_text='健康（85%）', row=1, col=1)
    fig.add_hline(y=0.75, line_dash='dash', line_color=COLORS['danger'],
                  annotation_text='存亡線（75%）', row=1, col=1)

    # 資金池
    fund_billions = results['fund_pool_total'] / 1e8
    fig.add_trace(go.Scatter(
        x=x, y=list(fund_billions),
        mode='lines', name='資金池',
        line=dict(color='#ED7D31'),
        hovertemplate='第 %{x:.1f} 年<br>資金池: %{y:.1f} 億台幣<extra></extra>',
    ), row=1, col=2)

    # 品牌信任
    fig.add_trace(go.Scatter(
        x=x, y=list(results['brand_trust']),
        mode='lines', name='品牌信任',
        line=dict(color=COLORS['success']),
        hovertemplate='第 %{x:.1f} 年<br>品牌信任: %{y:.0f}/100<extra></extra>',
    ), row=2, col=1)
    fig.add_hline(y=60, line_dash='dash', line_color=COLORS['success'],
                  annotation_text='健康（60）', row=2, col=1)
    fig.add_hline(y=40, line_dash='dash', line_color=COLORS['warning'],
                  annotation_text='警戒（40）', row=2, col=1)

    # 品牌活力
    fig.add_trace(go.Scatter(
        x=x, y=list(results['brand_vitality']),
        mode='lines', name='品牌活力',
        line=dict(color='#FFC000'),
        hovertemplate='第 %{x:.1f} 年<br>品牌活力: %{y:.0f}/100<extra></extra>',
    ), row=2, col=2)
    fig.add_hline(y=50, line_dash='dash', line_color=COLORS['warning'],
                  annotation_text='警戒（50）', row=2, col=2)

    # XY 軸標示
    fig.update_xaxes(title_text="營運年數（年）", row=1, col=1)
    fig.update_xaxes(title_text="營運年數（年）", row=1, col=2)
    fig.update_xaxes(title_text="營運年數（年）", row=2, col=1)
    fig.update_xaxes(title_text="營運年數（年）", row=2, col=2)
    fig.update_yaxes(title_text="入住率（%）", tickformat='.0%', row=1, col=1)
    fig.update_yaxes(title_text="總資金（億台幣）", row=1, col=2)
    fig.update_yaxes(title_text="信任分數（0-100）", row=2, col=1)
    fig.update_yaxes(title_text="活力指數（0-100）", row=2, col=2)

    fig.update_layout(
        title='',
        height=700,
        showlegend=False,
        margin=dict(l=60, r=20, t=50, b=60),
        **_chart_defaults(),
    )
    return fig


def plot_tornado_chart(sensitivity: list) -> go.Figure:
    """繪製龍捲風圖（敏感度分析）"""
    labels = [s['label'] for s in sensitivity]
    corr_occ = [s['corr_occupancy'] for s in sensitivity]
    corr_fund = [s['corr_fund'] for s in sensitivity]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=corr_occ, orientation='h',
        name='對入住率的影響', marker_color=COLORS['primary'],
        hovertemplate='%{y}<br>對入住率影響力: %{x:.2f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        y=labels, x=corr_fund, orientation='h',
        name='對資金池的影響', marker_color='#ED7D31',
        hovertemplate='%{y}<br>對資金池影響力: %{x:.2f}<extra></extra>',
    ))

    fig.update_layout(
        title='敏感度分析：調哪個參數影響最大？',
        xaxis_title='影響力（正 = 提升，負 = 降低）',
        yaxis_title='參數',
        barmode='group',
        height=400,
        margin=dict(l=120, r=20, t=50, b=50),
        **_chart_defaults(),
    )
    return fig


def _status_marker(value, green_threshold, yellow_threshold, higher_is_better=True) -> str:
    """回傳狀態文字標記"""
    if higher_is_better:
        if value >= green_threshold:
            return '[安全]'
        elif value >= yellow_threshold:
            return '[注意]'
        return '[危險]'
    else:
        if value <= green_threshold:
            return '[安全]'
        elif value <= yellow_threshold:
            return '[注意]'
        return '[危險]'


def render_dashboard(single_results: dict, mc_results: dict = None,
                     sensitivity: list = None):
    """渲染主儀表板"""

    # === 關鍵指標摘要 ===
    if mc_results is not None:
        st.markdown(
            f'<div class="dash-card-header">{SVG_ICONS["chart"]} 關鍵指標摘要</div>',
            unsafe_allow_html=True,
        )
        with st.expander("這四個數字代表什麼？"):
            st.markdown(
                "這是模擬上千次後得到的**最重要的四個結論**：\n\n"
                "1. **資金池耗盡機率** — 社區「倒閉」的可能性。超過 20% 就很危險。\n\n"
                "2. **首期達 85% 入住率** — 要多久才能住到健康水準。超過 5 年前期會很辛苦。\n\n"
                "3. **品牌老化觸發時間** — 多少年後社區開始「變老」、對新住戶失去吸引力。\n\n"
                "4. **無新血存活期** — 完全沒新住戶時，社區的錢還能撐多久。"
            )

        metrics = calculate_summary_metrics(mc_results)
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            prob = metrics['depletion_prob']
            marker = _status_marker(prob, 0.05, 0.20, higher_is_better=False)
            st.metric(
                f"{marker} 25年資金池耗盡機率",
                f"{prob:.1%}",
                help="模擬上千次後，有多少比例的情境會導致社區的錢花光。超過 20% 就代表這個方案太冒險了。"
            )
        with m2:
            years = metrics['median_fill_years']
            marker = _status_marker(years, 5, 10, higher_is_better=False)
            st.metric(
                f"{marker} 首期達85%入住率",
                f"{years:.1f} 年",
                help="第一期住滿 85% 需要多久。超過 5 年代表需要更多資金撐過去。"
            )
        with m3:
            aging = metrics['median_aging_trigger']
            marker = _status_marker(aging, 15, 10, higher_is_better=True)
            st.metric(
                f"{marker} 品牌老化觸發時間",
                f"{aging:.0f} 年",
                help="多久後社區開始「變老」。低於 15 年代表後面幾期可能找不到人住。"
            )
        with m4:
            survival = metrics['no_new_blood_survival']
            marker = _status_marker(survival, 48, 24, higher_is_better=True)
            st.metric(
                f"{marker} 無新血存活期",
                f"{survival:.0f} 個月",
                help="完全沒新住戶時，社區的錢還能撐幾個月。低於 24 個月安全邊際嚴重不足。"
            )

    # === 圖表分頁（SVG 圖標取代 emoji） ===
    tab1, tab2, tab3 = st.tabs([
        "單次模擬",
        "蒙地卡羅分布",
        "敏感度分析",
    ])

    with tab1:
        with st.expander("怎麼看這些圖？"):
            st.markdown(
                "這是**固定參數**跑一次的結果，呈現未來 25 年的走勢：\n\n"
                "- **入住率**：住了多少比例。85% 以上健康，75% 以下危險。\n\n"
                "- **資金池**：所有的錢加起來。往上走 = 在賺錢。\n\n"
                "- **品牌信任**：外界信心（0-100）。影響新住戶來不來。\n\n"
                "- **品牌活力**：社區年輕程度（0-100）。住戶越老越低。\n\n"
                "虛線 = 安全線。線掉到虛線以下要注意。\n\n"
                "**把滑鼠移到線上**可以看到精確數字。"
            )
        fig = plot_single_run(single_results)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if mc_results is not None:
            with st.expander("什麼是扇形圖？"):
                st.markdown(
                    "跑了上千次模擬，每次假設不同情境：\n\n"
                    "- **藍色線** = 最可能的走勢\n"
                    "- **深藍帶** = 50% 機率落在這個範圍\n"
                    "- **淺藍帶** = 90% 機率落在這個範圍\n\n"
                    "帶子越窄 = 越確定。帶子越寬 = 不確定性越大。"
                )

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_fan_chart(
                    mc_results, 'occupancy_rate',
                    '入住率軌跡（25年）',
                    y_label='入住率（%）',
                    thresholds=[0.90, 0.85, 0.80, 0.75],
                    threshold_labels=['優秀', '健康', '警戒', '存亡線'],
                    is_percentage=True,
                ), use_container_width=True)
            with col2:
                st.plotly_chart(plot_fan_chart(
                    mc_results, 'fund_pool_total',
                    '資金池水位（25年）',
                    y_label='總資金（億台幣）',
                    is_billion=True,
                ), use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(plot_fan_chart(
                    mc_results, 'brand_vitality',
                    '品牌活力指數（25年）',
                    y_label='活力指數（0-100）',
                    thresholds=[50, 30],
                    threshold_labels=['警戒', '危險'],
                ), use_container_width=True)
            with col4:
                st.plotly_chart(plot_fan_chart(
                    mc_results, 'brand_trust',
                    '品牌信任（25年）',
                    y_label='信任分數（0-100）',
                    thresholds=[60, 40],
                    threshold_labels=['健康', '警戒'],
                ), use_container_width=True)
        else:
            st.info("點擊上方「開始蒙地卡羅模擬」按鈕，就能看到上千種情境的分布範圍")

    with tab3:
        if sensitivity:
            with st.expander("怎麼看這張圖？"):
                st.markdown(
                    "這張圖告訴你**調哪個參數對結果影響最大**：\n\n"
                    "- 條越長 = 影響越大（優先關注）\n"
                    "- 往右 = 參數變大時結果變好\n"
                    "- 往左 = 參數變大時結果變差"
                )
            st.plotly_chart(plot_tornado_chart(sensitivity), use_container_width=True)
        else:
            st.info("點擊上方「開始蒙地卡羅模擬」按鈕，就能看到哪個因素影響最大")
