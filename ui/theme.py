"""專業視覺主題 — CSS 注入"""

import streamlit as st

COLORS = {
    'primary': '#2563EB',
    'primary_light': '#DBEAFE',
    'success': '#059669',
    'success_light': '#D1FAE5',
    'warning': '#D97706',
    'warning_light': '#FEF3C7',
    'danger': '#DC2626',
    'danger_light': '#FEE2E2',
    'accent_gold': '#B8860B',
    'bg_dark': '#0F172A',
    'bg_dark_mid': '#1E293B',
    'bg_light': '#F8FAFC',
    'bg_card': '#FFFFFF',
    'text_primary': '#0F172A',
    'text_secondary': '#64748B',
    'border': '#E2E8F0',
}

# SVG 圖標（取代 emoji）
SVG_ICONS = {
    'safe': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="8" fill="#059669"/><path d="M5.5 9.5L7.5 11.5L12.5 6.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'warning': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="8" fill="#D97706"/><path d="M9 6V10M9 12.5V12" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
    'danger': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="8" fill="#DC2626"/><path d="M6.5 6.5L11.5 11.5M11.5 6.5L6.5 11.5" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
    'chart': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="10" width="3" height="6" rx="1" fill="#2563EB"/><rect x="7.5" y="6" width="3" height="10" rx="1" fill="#2563EB" opacity="0.7"/><rect x="13" y="2" width="3" height="14" rx="1" fill="#2563EB" opacity="0.4"/></svg>',
    'monte_carlo': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="5" cy="7" r="1.5" fill="#2563EB"/><circle cx="9" cy="4" r="1.5" fill="#2563EB" opacity="0.7"/><circle cx="13" cy="9" r="1.5" fill="#2563EB" opacity="0.5"/><circle cx="7" cy="12" r="1.5" fill="#2563EB" opacity="0.6"/><circle cx="12" cy="14" r="1.5" fill="#2563EB" opacity="0.4"/><circle cx="4" cy="14" r="1.5" fill="#2563EB" opacity="0.3"/></svg>',
    'sensitivity': '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="#2563EB" stroke-width="2" fill="none"/><circle cx="9" cy="9" r="4" stroke="#2563EB" stroke-width="2" fill="none"/><circle cx="9" cy="9" r="1.5" fill="#DC2626"/></svg>',
    'home': '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 10L10 3L17 10" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 9V16H8V12H12V16H15V9" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'step1': '<svg width="32" height="32" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="14" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/><path d="M14 11H17V22H14.5" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'step2': '<svg width="32" height="32" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="14" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/><path d="M12 13C12 11.3 13.5 10 15.5 10C17.5 10 19 11.3 19 13C19 15 16 16 14 18H20" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'step3': '<svg width="32" height="32" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="14" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/><path d="M12 11H19L15 16C17 16 19 17 19 19.5C19 21.5 17.5 23 15.5 23C13.5 23 12 21.5 12 20" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'ai': '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="3" width="14" height="14" rx="3" stroke="#7C3AED" stroke-width="2"/><circle cx="8" cy="9" r="1.5" fill="#7C3AED"/><circle cx="12" cy="9" r="1.5" fill="#7C3AED"/><path d="M7 13C7 13 8.5 14.5 10 14.5C11.5 14.5 13 13 13 13" stroke="#7C3AED" stroke-width="1.5" stroke-linecap="round"/></svg>',
    'sliders': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><line x1="4" y1="6" x2="20" y2="6" stroke="#64748B" stroke-width="2" stroke-linecap="round"/><circle cx="9" cy="6" r="2.5" fill="#2563EB" stroke="white" stroke-width="1.5"/><line x1="4" y1="12" x2="20" y2="12" stroke="#64748B" stroke-width="2" stroke-linecap="round"/><circle cx="15" cy="12" r="2.5" fill="#2563EB" stroke="white" stroke-width="1.5"/><line x1="4" y1="18" x2="20" y2="18" stroke="#64748B" stroke-width="2" stroke-linecap="round"/><circle cx="7" cy="18" r="2.5" fill="#2563EB" stroke="white" stroke-width="1.5"/></svg>',
    'eye': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M2 12C2 12 5 5 12 5C19 5 22 12 22 12C22 12 19 19 12 19C5 19 2 12 2 12Z" stroke="#64748B" stroke-width="2"/><circle cx="12" cy="12" r="3" stroke="#2563EB" stroke-width="2"/></svg>',
    'play': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#64748B" stroke-width="2"/><path d="M10 8L16 12L10 16V8Z" fill="#059669"/></svg>',
}


def get_status_icon(status: str) -> str:
    """取得狀態圖標 HTML"""
    if status in ('safe', 'success', 'green'):
        return SVG_ICONS['safe']
    elif status in ('warning', 'yellow'):
        return SVG_ICONS['warning']
    elif status in ('danger', 'triggered', 'red'):
        return SVG_ICONS['danger']
    return ''


def apply_theme():
    """注入自訂 CSS 主題"""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

        /* === 全域字型 === */
        html, body, [class*="css"] {{
            font-family: 'Inter', 'Noto Sans TC', sans-serif;
        }}

        /* === 頂部標題區 === */
        .main-header {{
            background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_dark_mid']} 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }}
        .main-header h1 {{
            color: white !important;
            font-size: 1.75rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px;
            border-bottom: 3px solid {COLORS['accent_gold']};
            padding-bottom: 0.5rem;
            display: inline-block;
            margin: 0;
        }}
        .main-header p {{
            color: #94A3B8 !important;
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }}

        /* === 指標卡片 === */
        [data-testid="stMetric"] {{
            background: {COLORS['bg_card']};
            border-radius: 12px;
            padding: 1rem 1.25rem;
            box-shadow: 0 1px 8px rgba(0,0,0,0.06);
            border-left: 4px solid {COLORS['border']};
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 0.82rem !important;
            color: {COLORS['text_secondary']} !important;
            font-weight: 500 !important;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: {COLORS['text_primary']} !important;
        }}

        /* === Tab 膠囊式 === */
        [data-baseweb="tab-list"] {{
            gap: 8px;
            background: {COLORS['bg_light']};
            padding: 4px;
            border-radius: 10px;
        }}
        [data-baseweb="tab"] {{
            border-radius: 8px !important;
            padding: 8px 20px !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }}
        [data-baseweb="tab"][aria-selected="true"] {{
            background: {COLORS['primary']} !important;
            color: white !important;
        }}
        [data-baseweb="tab-highlight"] {{
            display: none;
        }}
        [data-baseweb="tab-border"] {{
            display: none;
        }}

        /* === 側邊欄 === */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FAFBFE 0%, #F0F2F8 100%);
        }}
        [data-testid="stSidebar"] h2 {{
            font-size: 1.1rem !important;
            color: {COLORS['text_primary']} !important;
            border-left: 4px solid {COLORS['primary']};
            padding-left: 12px;
        }}
        [data-testid="stSidebar"] h3 {{
            font-size: 0.95rem !important;
            color: {COLORS['text_secondary']} !important;
            margin-top: 1.2rem !important;
        }}

        /* === 展開區 === */
        [data-testid="stExpander"] {{
            border: 1px solid {COLORS['border']} !important;
            border-radius: 10px !important;
            background: {COLORS['bg_light']} !important;
        }}
        [data-testid="stExpander"] summary {{
            font-weight: 500 !important;
            color: {COLORS['text_primary']} !important;
        }}

        /* === 自訂卡片容器 === */
        .dash-card {{
            background: {COLORS['bg_card']};
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 1px 8px rgba(0,0,0,0.06);
            border: 1px solid {COLORS['border']};
            margin-bottom: 1rem;
        }}
        .dash-card-header {{
            font-size: 1rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* === 快速入門步驟卡片 === */
        .step-card {{
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 1px 6px rgba(0,0,0,0.04);
            min-height: 140px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .step-card-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-top: 4px;
        }}
        .step-card-desc {{
            font-size: 0.78rem;
            color: {COLORS['text_secondary']};
            line-height: 1.4;
        }}

        /* === 規則卡片 === */
        .rule-card {{
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
            min-height: 90px;
            border: 1px solid {COLORS['border']};
        }}
        .rule-card.safe {{ background: {COLORS['success_light']}; border-color: #A7F3D0; }}
        .rule-card.warning {{ background: {COLORS['warning_light']}; border-color: #FDE68A; }}
        .rule-card.triggered {{ background: {COLORS['danger_light']}; border-color: #FECACA; }}

        .severity-bar {{
            display: inline-flex;
            gap: 2px;
            margin-top: 4px;
        }}
        .severity-bar .filled {{
            width: 8px; height: 8px;
            border-radius: 2px;
            background: {COLORS['text_secondary']};
        }}
        .severity-bar .empty {{
            width: 8px; height: 8px;
            border-radius: 2px;
            background: {COLORS['border']};
        }}

        /* === AI 分析區 === */
        .ai-card {{
            background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
            border: 1px solid #C4B5FD;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        .ai-section {{
            background: white;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            border-left: 4px solid #7C3AED;
        }}
        .ai-section-title {{
            font-weight: 600;
            font-size: 0.95rem;
            color: #5B21B6;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* === 按鈕 === */
        [data-testid="stBaseButton-primary"] {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.5rem !important;
        }}

        /* === Divider === */
        [data-testid="stHorizontalBlock"] hr {{
            border-color: {COLORS['border']} !important;
        }}
    </style>
    """, unsafe_allow_html=True)
