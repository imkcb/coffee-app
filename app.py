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

# --- テーマ別カラーパレット定義 ---
if theme_mode == "LIGHT":
    bg_color = "#F5F5F7"
    text_color = "#111111"
    sub_text_color = "#555555"
    card_bg = "#EBEBEF"
    border_color = "#CCCCCC"
    input_bg = "#FFFFFF"
    tab_unselected = "#666666"
    btn_bg = "#E0E0E5"
    btn_border = "#B8B8C0"
    btn_text = "#111111"
    
    # LIGHTモード用 高コントラストアクセント
    c_drip = "#008A43"    # Deep Emerald Green
    c_drip_txt = "#FFFFFF"
    c_beans = "#C70063"   # Deep Magenta
    c_beans_txt = "#FFFFFF"
    c_gear = "#A67C00"    # Deep Gold
    c_gear_txt = "#FFFFFF"
    c_logs = "#0077B6"    # Deep Cyan/Blue
    c_logs_txt = "#FFFFFF"
    c_system = "#7A00CC"  # Deep Violet
    c_system_txt = "#FFFFFF"
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
    
    # DARKモード用 蛍光アクセント
    c_drip = "#00FF66"    # 蛍光黄緑 (Neon Green)
    c_drip_txt = "#000000"
    c_beans = "#FF007F"   # 蛍光ピンク
    c_beans_txt = "#FFFFFF"
    c_gear = "#FFEE00"    # 蛍光イエロー
    c_gear_txt = "#000000"
    c_logs = "#00E5FF"    # 蛍光ブルー
    c_logs_txt = "#000000"
    c_system = "#B026FF"  # 蛍光パープル
    c_system_txt = "#FFFFFF"

# 2. GLOBAL & TAB-PANEL CSS
elektron_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&display=swap');

/* 全体背景 & ベーステキスト */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}}

/* 8bitフォントはメインタイトルとH1~H3のみ */
h1, h2, h3, .potlog-title-text {{
    font-family: 'Silkscreen', monospace !important;
    color: {text_color} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

h4, h5, h6, label, p, span, div {{
    color: {text_color} !important;
}}

label, .stMarkdown p, [data-testid="stWidgetLabel"] p {{
    color: {text_color} !important;
    font-weight: 600 !important;
}}

/* POTLOG タイトル */
.potlog-title-text {{
    font-size: 2.2rem;
    font-weight: 700;
    color: {text_color} !important;
    margin-bottom: 20px;
}}

/* タブバー共通設定 */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 6px;
    background-color: {bg_color} !important;
    border-bottom: 1px solid {border_color} !important;
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

/* タブ選択時のアンダーライン表示 */
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(1)[aria-selected="true"] {{ color: {c_drip} !important; border-bottom: 2px solid {c_drip} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(2)[aria-selected="true"] {{ color: {c_beans} !important; border-bottom: 2px solid {c_beans} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(3)[aria-selected="true"] {{ color: {c_gear} !important; border-bottom: 2px solid {c_gear} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(4)[aria-selected="true"] {{ color: {c_logs} !important; border-bottom: 2px solid {c_logs} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] button:nth-child(5)[aria-selected="true"] {{ color: {c_system} !important; border-bottom: 2px solid {c_system} !important; }}

/* --- 初期（未選択）ボタン：無色（シックなダーク背景＋枠線） --- */
div.stButton > button,
button[data-testid="stBaseButton-secondary"] {{
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

div.stButton > button:hover,
button[data-testid="stBaseButton-secondary"]:hover {{
    border-color: {text_color} !important;
}}

/* --- デフォルトプライマリボタン（フォールバック：蛍光黄緑） --- */
button[data-testid="stBaseButton-primary"],
button[kind="primary"],
div.stButton > button[kind="primary"] {{
    background-color: {c_drip} !important;
    border-color: {c_drip} !important;
    color: {c_drip_txt} !important;
}}

button[data-testid="stBaseButton-primary"] *,
button[kind="primary"] * {{
    color: {c_drip_txt} !important;
    font-weight: bold !important;
}}

/* --- 各タブ（1〜5）ごとの選択時テーマカラー指定 --- */

/* 1. DRIP タブ（蛍光黄緑 #00FF66） */
[data-testid="stTabPanel"]:nth-of-type(1) button[data-testid="stBaseButton-primary"],
[data-testid="stTabPanel"]:nth-of-type(1) button[kind="primary"],
[data-testid="stTabPanel"]:nth-of-type(1) div.stButton > button[kind="primary"] {{
    background-color: {c_drip} !important;
    border-color: {c_drip} !important;
    color: {c_drip_txt} !important;
}}
[data-testid="stTabPanel"]:nth-of-type(1) button[data-testid="stBaseButton-primary"] *,
[data-testid="stTabPanel"]:nth-of-type(1) button[kind="primary"] * {{
    color: {c_drip_txt} !important;
    font-weight: bold !important;
}}

/* 2. BEANS タブ（蛍光ピンク #FF007F） */
[data-testid="stTabPanel"]:nth-of-type(2) button[data-testid="stBaseButton-primary"],
[data-testid="stTabPanel"]:nth-of-type(2) button[kind="primary"],
[data-testid="stTabPanel"]:nth-of-type(2) div.stButton > button[kind="primary"] {{
    background-color: {c_beans} !important;
    border-color: {c_beans} !important;
    color: {c_beans_txt} !important;
}}
[data-testid="stTabPanel"]:nth-of-type(2) button[data-testid="stBaseButton-primary"] *,
[data-testid="stTabPanel"]:nth-of-type(2) button[kind="primary"] * {{
    color: {c_beans_txt} !important;
    font-weight: bold !important;
}}

/* 3. GEAR タブ（蛍光イエロー #FFEE00） */
[data-testid="stTabPanel"]:nth-of-type(3) button[data-testid="stBaseButton-primary"],
[data-testid="stTabPanel"]:nth-of-type(3) button[kind="primary"],
[data-testid="stTabPanel"]:nth-of-type(3) div.stButton > button[kind="primary"] {{
    background-color: {c_gear} !important;
    border-color: {c_gear} !important;
    color: {c_gear_txt} !important;
}}
[data-testid="stTabPanel"]:nth-of-type(3) button[data-testid="stBaseButton-primary"] *,
[data-testid="stTabPanel"]:nth-of-type(3) button[kind="primary"] * {{
    color: {c_gear_txt} !important;
    font-weight: bold !important;
}}

/* 4. LOGS タブ（蛍光ブルー #00E5FF） */
[data-testid="stTabPanel"]:nth-of-type(4) button[data-testid="stBaseButton-primary"],
[data-testid="stTabPanel"]:nth-of-type(4) button[kind="primary"],
[data-testid="stTabPanel"]:nth-of-type(4) div.stButton > button[kind="primary"] {{
    background-color: {c_logs} !important;
    border-color: {c_logs} !important;
    color: {c_logs_txt} !important;
}}
[data-testid="stTabPanel"]:nth-of-type(4) button[data-testid="stBaseButton-primary"] *,
[data-testid="stTabPanel"]:nth-of-type(4) button[kind="primary"] * {{
    color: {c_logs_txt} !important;
    font-weight: bold !important;
}}

/* 5. SYSTEM タブ（蛍光パープル #B026FF） */
[data-testid="stTabPanel"]:nth-of-type(5) button[data-testid="stBaseButton-primary"],
[data-testid="stTabPanel"]:nth-of-type(5) button[kind="primary"],
[data-testid="stTabPanel"]:nth-of-type(5) div.stButton > button[kind="primary"] {{
    background-color: {c_system} !important;
    border-color: {c_system} !important;
    color: {c_system_txt} !important;
}}
[data-testid="stTabPanel"]:nth-of-type(5) button[data-testid="stBaseButton-primary"] *,
[data-testid="stTabPanel"]:nth-of-type(5) button[kind="primary"] * {{
    color: {c_system_txt} !important;
    font-weight: bold !important;
}}

/* スライダー＆マルチセレクトタグのテーマカラー適用 */
[data-testid="stTabPanel"]:nth-of-type(1) [data-baseweb="slider"] div[role="slider"] {{ background-color: {c_drip} !important; border-color: {c_drip} !important; }}
[data-testid="stTabPanel"]:nth-of-type(1) [data-baseweb="slider"] > div > div > div {{ background-color: {c_drip} !important; }}

[data-testid="stTabPanel"]:nth-of-type(1) span[data-baseweb="tag"] {{ background-color: {c_drip} !important; border-color: {c_drip} !important; }}
[data-testid="stTabPanel"]:nth-of-type(1) span[data-baseweb="tag"] span, 
[data-testid="stTabPanel"]:nth-of-type(1) span[data-baseweb="tag"] div, 
[data-testid="stTabPanel"]:nth-of-type(1) span[data-baseweb="tag"] svg {{ color: {c_drip_txt} !important; fill: {c_drip_txt} !important; font-weight: bold !important; }}

/* READY通知バナーの黒背景×蛍光黄緑枠化 */
div[data-testid="stNotification"] {{
    background-color: #0D0D0D !important;
    border: 1px solid {c_drip} !important;
    border-radius: 4px !important;
}}
div[data-testid="stNotification"] * {{
    color: {c_drip} !important;
}}

/* メトリック表示 */
div[data-testid="stMetric"] {{
    border: 1px solid {border_color} !important;
    background-color: {card_bg} !important;
    padding: 12px !important;
    border-radius: 4px !important;
}}

div[data-testid="stMetricLabel"] {{ color: {sub_text_color} !important; font-size: 0.75rem !important; }}
[data-testid="stTabPanel"]:nth-of-type(1) div[data-testid="stMetricValue"] {{ color: {c_drip} !important; }}
[data-testid="stTabPanel"]:nth-of-type(2) div[data-testid="stMetricValue"] {{ color: {c_beans} !important; }}
[data-testid="stTabPanel"]:nth-of-type(3) div[data-testid="stMetricValue"] {{ color: {c_gear} !important; }}
[data-testid="stTabPanel"]:nth-of-type(4) div[data-testid="stMetricValue"] {{ color: {c_logs} !important; }}
[data-testid="stTabPanel"]:nth-of-type(5) div[data-testid="stMetricValue"] {{ color: {c_system} !important; }}

/* 入力フォーム類 */
input, select, textarea, div[data-baseweb="select"] {{
    background-color: {input_bg} !important;
    color: {text_color} !important;
    border: 1px solid {border_color} !important;
    border-radius: 4px !important;
}}

hr {{ border-color: {border_color} !important; margin: 24px 0 !important; }}
</style>
"""

st.markdown(elektron_css, unsafe_allow_html=True)

# アプリタイトル
st.markdown('<div class="potlog-title-text">POTLOG</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["DRIP", "BEANS", "GEAR", "LOGS", "SYSTEM"])

from views import drip_view, beans_view, equip_view, history_view, system_view

with tab1:
    drip_view.render()

with tab2:
    beans_view.render()

with tab3:
    equip_view.render()

with tab4:
    history_view.render()

with tab5:
    system_view.render()