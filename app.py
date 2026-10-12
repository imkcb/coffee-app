import streamlit as st
from ui import theme
from ui.tabs import drip_tab, beans_tab, gear_tab, logs_tab, system_tab

st.set_page_config(page_title="POTLOG", page_icon="☕", layout="centered")

# CSS テーマ適用
theme.apply_theme()

# 最上部大見出し (POTLOG : 専用クラスでビットフォント化)
st.markdown('<div class="app-title">POTLOG</div>', unsafe_allow_html=True)

# 5タブ構成
tab_drip, tab_beans, tab_gear, tab_logs, tab_system = st.tabs(["DRIP", "BEANS", "GEAR", "LOGS", "SYSTEM"])

with tab_drip:
    drip_tab.render()
with tab_beans:
    beans_tab.render()
with tab_gear:
    gear_tab.render()
with tab_logs:
    logs_tab.render()
with tab_system:
    system_tab.render()