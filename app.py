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
    page_icon="🫖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. ELEKTRON 8-BIT MONOCHROME CSS
elektron_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DotGothic16&family=Silkscreen:wght@400;700&display=swap');

/* 全体背景 & フォント */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    font-family: 'DotGothic16', monospace, sans-serif !important;
}

/* ヘッダー非表示・背景固定 */
[data-testid="stHeader"] {
    background-color: #000000 !important;
}

/* 見出し (Silkscreen / DotGothic16 8bit) */
h1, h2, h3, h4, h5, h6, span, label, p {
    font-family: 'DotGothic16', monospace !important;
}

h1, h2, h3, h4 {
    font-family: 'Silkscreen', 'DotGothic16', monospace !important;
    color: #FFFFFF !important;
    text-transform: uppercase;
}

/* Potlog 8bitヘッダー */
.potlog-container {
    border: 2px solid #FFFFFF;
    background-color: #0A0A0A;
    padding: 18px;
    margin-bottom: 20px;
    box-shadow: 4px 4px 0px #333333;
}

.potlog-title-text {
    font-family: 'Silkscreen', monospace !important;
    font-size: 2.2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: 2px;
}

.potlog-sub-text {
    font-family: 'DotGothic16', monospace !important;
    font-size: 0.85rem;
    color: #888888;
    margin-top: 6px;
}

/* タブデザイン (Elektron OLEDスタイル) */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: #000000;
    border-bottom: 2px solid #333333;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Silkscreen', 'DotGothic16', monospace !important;
    border: 1px solid #444444 !important;
    border-radius: 0px !important;
    background-color: #111111 !important;
    color: #888888 !important;
    padding: 8px 12px !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    border: 1px solid #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #000000 !important;
    box-shadow: 2px 2px 0px #FF9900 !important;
}

/* ボタン (8bit 押し込み風) */
div.stButton > button {
    font-family: 'Silkscreen', 'DotGothic16', monospace !important;
    border: 2px solid #FFFFFF !important;
    border-radius: 0px !important;
    background-color: #0A0A0A !important;
    color: #FFFFFF !important;
    box-shadow: 3px 3px 0px #444444 !important;
}

div.stButton > button:hover {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    box-shadow: 3px 3px 0px #FF9900 !important;
}

/* メトリック・カード */
div[data-testid="stMetric"], [data-testid="stExpander"] {
    border: 1px solid #444444 !important;
    border-radius: 0px !important;
    background-color: #0A0A0A !important;
}

div[data-testid="stMetricValue"] {
    color: #FF9900 !important;
}
</style>
"""

st.markdown(elektron_css, unsafe_allow_html=True)

# 8bit ヘッダー描画
st.markdown(
    """
    <div class="potlog-container">
        <div class="potlog-title-text">🫖 POTLOG</div>
        <div class="potlog-sub-text">// ELEKTRONIC DRIP ENGINE v2.0</div>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4 = st.tabs(["☕ DRIP", "🫘 BEANS", "🛠️ GEAR", "📈 LOGS"])

from views import drip_view, beans_view, equip_view, history_view

with tab1:
    drip_view.render()

with tab2:
    beans_view.render()

with tab3:
    equip_view.render()

with tab4:
    history_view.render()