import sys
import os
import streamlit as st

# Streamlit CloudのSecretsをプログラム側の環境変数へ反映
for k in ["SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY"]:
    if k in st.secrets:
        os.environ[k] = st.secrets[k]

import db
import ai
import prompts

# 1. ページ基本設定
st.set_page_config(
    page_title="Potlog",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# テーマ状態の初期化 (DARK, LIGHT, SYSTEM)
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "DARK"

theme_mode = st.session_state["theme_mode"]

# テーマ別ベースCSS変数定義
if theme_mode == "LIGHT":
    bg_color = "#F5F5F7"
    text_color = "#111111"
    sub_text_color = "#666666"
    card_bg = "#FFFFFF"
    border_color = "#E5E5E5"
    input_bg = "#FFFFFF"
    tab_unselected = "#666666"
    btn_bg = "#E8E8ED"
    btn_border = "#D1D1D6"
    btn_text = "#111111"
else:  # DARK または SYSTEM
    bg_color = "#000000"
    text_color = "#E0E0E0"
    sub_text_color = "#888888"
    card_bg = "#0D0D0D"
    border_color = "#262626"
    input_bg = "#171717"
    tab_unselected = "#737373"
    btn_bg = "#171717"
    btn_border = "#404040"
    btn_text = "#FFFFFF"

# 2. GLOBAL & TAB-ACCENT CSS
elektron_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&display=swap');

/* ベースフォント & 背景 */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}}

/* ヘッダー背景 */
[data-testid="stHeader"] {{
    background-color: {bg_color} !important;
}}

/* 8bitフォントはメインタイトルとH1~H3のみ */
h1, h2, h3, .potlog-title-text {{
    font-family: 'Silkscreen', monospace !important;
    color: {text_color} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

h4, h5, h6 {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 600 !important;
    color: {text_color} !important;
    letter-spacing: 0.5px;
}}

/* POTLOG タイトル */
.potlog-title-text {{
    font-size: 2.2rem;
    font-weight: 700;
    color: {text_color};
    margin-bottom: 20px;
}}

/* タブバー共通設定 */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 8px;
    background-color: {bg_color};
    border-bottom: 1px solid {border_color};
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 0px !important;
    background-color: transparent !important;
    color: {tab_unselected} !important;
    padding: 8px 12px !important;
}}

/* 各タブ選択時のネオンカラーアクセント */
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(1)[aria-selected="true"] {{
    color: #00FF66 !important; /* DRIP: 蛍光黄緑 */
    border-bottom: 2px solid #00FF66 !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(2)[aria-selected="true"] {{
    color: #FF007F !important; /* BEANS: 蛍光ピンク */
    border-bottom: 2px solid #FF007F !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(3)[aria-selected="true"] {{
    color: #FFEE00 !important; /* GEAR: 蛍光黄色 */
    border-bottom: 2px solid #FFEE00 !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(4)[aria-selected="true"] {{
    color: #00E5FF !important; /* LOGS: 蛍光ブルー */
    border-bottom: 2px solid #00E5FF !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(5)[aria-selected="true"] {{
    color: #B026FF !important; /* SYSTEM: 蛍光パープル */
    border-bottom: 2px solid #B026FF !important;
}}

/* ボタン基本構造 */
div.stButton > button {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border: 1px solid {btn_border} !important;
    border-radius: 4px !important;
    background-color: {btn_bg} !important;
    color: {btn_text} !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease;
}}

/* DRIP (蛍光黄緑 #00FF66) */
.tab-drip div.stButton > button[kind="primary"] {{
    background-color: #00FF66 !important;
    border-color: #00FF66 !important;
    color: #000000 !important;
}}
.tab-drip div[data-testid="stMetricValue"] {{
    color: #00FF66 !important;
}}

/* BEANS (蛍光ピンク #FF007F) */
.tab-beans div.stButton > button[kind="primary"] {{
    background-color: #FF007F !important;
    border-color: #FF007F !important;
    color: #FFFFFF !important;
}}
.tab-beans div[data-testid="stMetricValue"] {{
    color: #FF007F !important;
}}

/* GEAR (蛍光黄色 #FFEE00) */
.tab-gear div.stButton > button[kind="primary"] {{
    background-color: #FFEE00 !important;
    border-color: #FFEE00 !important;
    color: #000000 !important;
}}
.tab-gear div[data-testid="stMetricValue"] {{
    color: #FFEE00 !important;
}}

/* LOGS (蛍光ブルー #00E5FF) */
.tab-logs div.stButton > button[kind="primary"] {{
    background-color: #00E5FF !important;
    border-color: #00E5FF !important;
    color: #000000 !important;
}}
.tab-logs div[data-testid="stMetricValue"] {{
    color: #00E5FF !important;
}}

/* SYSTEM (蛍光パープル #B026FF) */
.tab-system div.stButton > button[kind="primary"] {{
    background-color: #B026FF !important;
    border-color: #B026FF !important;
    color: #FFFFFF !important;
}}
.tab-system div[data-testid="stMetricValue"] {{
    color: #B026FF !important;
}}

/* メトリック・カード表示 */
div[data-testid="stMetric"] {{
    border: 1px solid {border_color} !important;
    background-color: {card_bg} !important;
    padding: 12px !important;
    border-radius: 4px !important;
}}

div[data-testid="stMetricLabel"] {{
    color: {sub_text_color} !important;
    font-size: 0.75rem !important;
}}

/* 入力フォーム類 */
input, select, textarea, div[data-baseweb="select"] {{
    background-color: {input_bg} !important;
    color: {text_color} !important;
    border: 1px solid {border_color} !important;
    border-radius: 4px !important;
}}

/* 区切り線 */
hr {{
    border-color: {border_color} !important;
    margin: 24px 0 !important;
}}
</style>
"""

st.markdown(elektron_css, unsafe_allow_html=True)

# アプリタイトル
st.markdown('<div class="potlog-title-text">POTLOG</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["DRIP", "BEANS", "GEAR", "LOGS", "SYSTEM"])

from views import drip_view, beans_view, equip_view, history_view, system_view

with tab1:
    st.markdown('<div class="tab-drip">', unsafe_allow_html=True)
    drip_view.render()
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="tab-beans">', unsafe_allow_html=True)
    beans_view.render()
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="tab-gear">', unsafe_allow_html=True)
    equip_view.render()
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="tab-logs">', unsafe_allow_html=True)
    history_view.render()
    st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="tab-system">', unsafe_allow_html=True)
    system_view.render()
    st.markdown('</div>', unsafe_allow_html=True)