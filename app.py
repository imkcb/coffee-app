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

# 2. ELEKTRON-INSPIRED MONOCHROME CSS (表示崩れ防止・シンプル化)
elektron_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&display=swap');

/* 全体背景 & ベースフォント */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: #000000 !important;
    color: #E0E0E0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* ヘッダー背景 */
[data-testid="stHeader"] {
    background-color: #000000 !important;
}

/* 8bitフォントはアプリタイトルと大・中見出し（H1~H3）のみに限定 */
h1, h2, h3, .potlog-title-text {
    font-family: 'Silkscreen', monospace !important;
    color: #FFFFFF !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

h4, h5, h6 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.5px;
}

/* Potlog タイトル（枠囲み・サブタイトルなし） */
.potlog-title-text {
    font-size: 2.2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 20px;
}

/* タブデザイン */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #000000;
    border-bottom: 1px solid #262626;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 0px !important;
    background-color: transparent !important;
    color: #737373 !important;
    padding: 8px 16px !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    color: #FFFFFF !important;
    border-bottom: 2px solid #FF9900 !important;
    background-color: transparent !important;
}

/* ボタン */
div.stButton > button {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border: 1px solid #404040 !important;
    border-radius: 4px !important;
    background-color: #171717 !important;
    color: #FFFFFF !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease;
}

div.stButton > button:hover {
    background-color: #262626 !important;
    border-color: #A3A3A3 !important;
    color: #FFFFFF !important;
}

/* プライマリボタン */
div.stButton > button[kind="primary"] {
    background-color: #FF9900 !important;
    border-color: #FF9900 !important;
    color: #000000 !important;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #FFAD33 !important;
    border-color: #FFAD33 !important;
    color: #000000 !important;
}

/* メトリック表示 */
div[data-testid="stMetric"] {
    border: 1px solid #262626 !important;
    background-color: #0D0D0D !important;
    padding: 12px !important;
    border-radius: 4px !important;
}

div[data-testid="stMetricLabel"] {
    color: #A3A3A3 !important;
    font-size: 0.75rem !important;
}

div[data-testid="stMetricValue"] {
    color: #FF9900 !important;
    font-weight: 700 !important;
}

/* 入力フォーム類 */
input, select, textarea, div[data-baseweb="select"] {
    background-color: #171717 !important;
    color: #FFFFFF !important;
    border: 1px solid #333333 !important;
    border-radius: 4px !important;
}

/* 区切り線 */
hr {
    border-color: #262626 !important;
    margin: 24px 0 !important;
}
</style>
"""

st.markdown(elektron_css, unsafe_allow_html=True)

# シンプルなタイトル描画（枠囲み・サブタイトル排除）
st.markdown('<div class="potlog-title-text">POTLOG</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["DRIP", "BEANS", "GEAR", "LOGS"])

from views import drip_view, beans_view, equip_view, history_view

with tab1:
    drip_view.render()

with tab2:
    beans_view.render()

with tab3:
    equip_view.render()

with tab4:
    history_view.render()