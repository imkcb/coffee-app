import os
import streamlit as st

# Streamlit CloudのSecretsをプログラム側の環境変数へ反映
for k in ["SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY"]:
    if k in st.secrets:
        os.environ[k] = st.secrets[k]

import db
import ai
import prompts

# 1. データの初期取得
beans_data = db.get_beans()
equipment_data = db.get_equipment()
drip_logs_data = db.get_drip_logs()

bean_names = [b.get("name") for b in beans_data if b.get("name")] or [
    "エチオピア イルガチェフェ", "グアテマラ アンティグア", "ブラジル サントス"
]

# 2. セッション状態の初期化
if "default_cup_count" not in st.session_state:
    st.session_state["default_cup_count"] = 1
if "coffee_type" not in st.session_state:
    st.session_state["coffee_type"] = "ホット"
if "water_per_cup" not in st.session_state:
    st.session_state["water_per_cup"] = 300

# 3. アプリタイトルと4タブ構成の定義
st.title("BARIS⚡️太郎くん")
tab1, tab2, tab3, tab4 = st.tabs(["ドリップ", "豆管理", "器具管理", "履歴"])

# タブ1: ドリップ画面
with tab1:
    st.header("1. 条件選択")
    coffee_type = st.radio("抽出タイプ", ["ホット", "アイス"], key="coffee_type_radio")
    col1, col2 = st.columns(2)
    with col1:
        cup_count = st.number_input("杯数", min_value=1, max_value=5, value=st.session_state["default_cup_count"])
    with col2:
        water_per_cup = st.number_input("1杯あたりの湯量(ml)", min_value=100, max_value=500, value=st.session_state["water_per_cup"], step=10)
    selected_bean = st.selectbox("使用するコーヒー豆", bean_names)

# タブ2: 豆管理画面
with tab2:
    st.header("豆管理")
    st.subheader("豆の新規登録")
    with st.form("add_bean_form"):
        name = st.text_input("豆の名前（必須）")
        farm = st.text_input("農園")
        shop = st.text_input("購入店")
        elevation = st.text_input("標高")
        roast = st.selectbox("焙煎度", ["浅煎り", "中浅煎り", "中煎り", "中深煎り", "深煎り"])
        process = st.text_input("精製方法（プロセス）")
        origin = st.text_input("産地")
        variety = st.text_input("品種")
        flavor = st.text_input("フレーバーノート")
        submit_bean = st.form_submit_button("豆を登録する")
        if submit_bean:
            if name:
                db.add_bean({
                    "name": name, "farm": farm, "shop": shop, "elevation": elevation,
                    "roast": roast, "process": process, "origin": origin,
                    "variety": variety, "flavor": flavor
                })
                st.success(f"「{name}」を登録しました！")
                st.rerun()
            else:
                st.error("豆の名前を入力してください。")

    st.divider()
    st.subheader("登録済みの豆一覧")
    if beans_data:
        for b in beans_data:
            with st.expander(f"{b.get('name', '名称未設定')}"):
                st.write(f"**焙煎度:** {b.get('roast', '-')}")
                st.write(f"**産地/農園:** {b.get('origin', '-')}/ {b.get('farm', '-')}")
                st.write(f"**フレーバー:** {b.get('flavor', '-')}")
    else:
        st.info("登録されている豆はまだありません。")

# タブ3: 器具管理画面
with tab3:
    st.header("器具管理")
    st.subheader("器具の新規登録")
    with st.form("add_equipment_form"):
        eq_category = st.selectbox("カテゴリ", ["ミル（グラインダー）", "ドリッパー", "フィルター", "サーバー", "ケトル", "その他"])
        eq_name = st.text_input("器具名（必須）")
        submit_eq = st.form_submit_button("器具を登録する")
        if submit_eq:
            if eq_name:
                db.add_equipment({"category": eq_category, "name": eq_name})
                st.success(f"「{eq_name}」を登録しました！")
                st.rerun()
            else:
                st.error("器具名を入力してください。")

    st.divider()
    st.subheader("登録済みの器具一覧")
    if equipment_data:
        for eq in equipment_data:
            st.write(f"・ **[{eq.get('category', 'その他')}]** {eq.get('name', '-')}")
    else:
        st.info("登録されている器具はまだありません。")

# タブ4: 履歴画面
with tab4:
    st.header("抽出履歴")
    if drip_logs_data:
        for log in drip_logs_data:
            with st.expander(f"{log.get('created_at', '')[:10]} - {log.get('bean_name', '不明な豆')}"):
                st.write(f"**評価:** {log.get('rating', '-')}")
                st.write(f"**感想:** {log.get('comment', '-')}")
    else:
        st.info("まだ抽出履歴はありません。")