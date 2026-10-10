import os
import streamlit as st

# Streamlit CloudのSecretsをプログラム側の環境変数へ反映
for k in ["SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY"]:
    if k in st.secrets:
        os.environ[k] = st.secrets[k]

from views import drip_view, beans_view, equip_view, history_view

# アプリタイトルと4タブ構成の定義
st.title("BARIS⚡太郎くん")
tab1, tab2, tab3, tab4 = st.tabs(["☕ ドリップ", "🫘 豆管理", "🛠️ 器具管理", "📈 履歴"])

with tab1:
    drip_view.render()

with tab2:
    beans_view.render()

with tab3:
    equip_view.render()

with tab4:
    history_view.render()