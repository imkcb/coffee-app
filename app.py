import os
import datetime
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

# ドラフト（未評価仮保存）と確定済み履歴の分離
draft_logs = []
confirmed_logs = []

if drip_logs_data:
    for log in drip_logs_data:
        data_p = log.get("data") or {}
        if data_p.get("is_draft") is True:
            draft_logs.append(log)
        else:
            confirmed_logs.append(log)

# 確定履歴を日付の新しい順（降順）に並び替え
if confirmed_logs:
    confirmed_logs = sorted(confirmed_logs, key=lambda x: str(x.get("created_at", "")), reverse=True)

bean_names = [b.get("name") for b in beans_data if b.get("name")] if beans_data else [
    "エチオピア イルガチェフェ", "グアテマラ アンティグア", "ブラジル サントス"
]

# 2. セッション状態の初期化
if "default_cup_count" not in st.session_state:
    st.session_state["default_cup_count"] = 1
if "coffee_type" not in st.session_state:
    st.session_state["coffee_type"] = "ホット"
if "water_per_cup" not in st.session_state:
    st.session_state["water_per_cup"] = 300

# リロード時のドラフト復元処理
if "current_recipe" not in st.session_state and draft_logs:
    latest_draft = draft_logs[-1]
    draft_data = latest_draft.get("data") or {}
    if draft_data.get("recipe"):
        st.session_state["current_recipe"] = draft_data.get("recipe")
        st.session_state["current_drip_params"] = {
            "bean_name": draft_data.get("bean_name"),
            "bean_id": latest_draft.get("bean_id"),
            "flavor_profile": latest_draft.get("flavor_profile"),
            "cup_count": latest_draft.get("cup_count", 1),
            "roast_date": latest_draft.get("roasted_date") or "未指定",
            "coffee_type": draft_data.get("coffee_type", "ホット"),
            "water_per_cup": draft_data.get("water_per_cup", 300)
        }
        st.session_state["draft_log_id"] = latest_draft.get("id")

# 3. アプリタイトルと4タブ構成の定義
st.title("BARIS⚡太郎くん")
tab1, tab2, tab3, tab4 = st.tabs(["☕ ドリップ", "🫘 豆管理", "🛠️ 器具管理", "📈 履歴"])

# ==========================================
# タブ1: ドリップ画面
# ==========================================
with tab1:
    st.header("1. 条件選択")
    
    selected_coffee_type = st.radio(
        "① 抽出タイプ",
        ["ホット", "アイス"],
        index=0 if st.session_state["coffee_type"] == "ホット" else 1,
        horizontal=True,
        key="drip_coffee_type"
    )
    
    shops = sorted(list(set([b.get("shop") for b in beans_data if b.get("shop")])))
    shop_options = ["すべて"] + shops
    
    selected_shop = st.radio(
        "② 購入店を選択",
        shop_options,
        horizontal=True,
        key="drip_shop_choice"
    )
    
    if selected_shop != "すべて":
        filtered_beans = [b for b in beans_data if b.get("shop") == selected_shop]
    else:
        filtered_beans = beans_data
        
    filtered_bean_names = [b.get("name") for b in filtered_beans if b.get("name")]
    if not filtered_bean_names:
        filtered_bean_names = bean_names
        
    bean_choice = st.radio(
        "③ 豆を選択",
        filtered_bean_names,
        key="drip_bean_choice"
    )
    
    flavor_profile = st.radio(
        "④ 味の方向性",
        ["すっきり・フルーティー", "バランス重視", "しっかり・コク旨"],
        horizontal=True,
        key="drip_flavor_profile"
    )
    
    with st.expander("⚙️ 細かい設定（量・杯数・焙煎日）", expanded=True):
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            selected_water_per_cup = st.number_input(
                "1杯あたりの量 (ml)", min_value=150, max_value=500,
                value=st.session_state["water_per_cup"], step=10
            )
            cup_count = st.slider(
                "抽出する杯数", min_value=1, max_value=4,
                value=st.session_state["default_cup_count"]
            )
        with col_sub2:
            today_date = datetime.date.today()
            roast_date_input = st.date_input(
                "焙煎日（任意）",
                value=None,
                max_value=today_date,
                key="drip_roast_date"
            )

    chosen_bean = next((b for b in beans_data if b.get("name") == bean_choice), {"name": bean_choice})
    chosen_bean_id = chosen_bean.get("id") if isinstance(chosen_bean, dict) else None
    
    past_feedback_text = "過去の評価なし"
    if chosen_bean_id and confirmed_logs:
        past_logs = [l for l in confirmed_logs if l.get("bean_id") == chosen_bean_id]
        if past_logs:
            latest_log = past_logs[0]
            log_data = latest_log.get("data") or {}
            rating = log_data.get("rating")
            acid = log_data.get("acid_level", "適正")
            bitter = log_data.get("bitter_level", "適正")
            act_time = log_data.get("actual_time", "")
            raw_issues = log_data.get("taste_issues") or log_data.get("taste_issue") or []
            issues_list = [raw_issues] if isinstance(raw_issues, str) else raw_issues
            raw_goals = log_data.get("target_goals") or log_data.get("target_goal") or []
            goals_list = [raw_goals] if isinstance(raw_goals, str) else raw_goals
            comment = log_data.get("comment", "")
            
            feedback_parts = [f"満足度: ★{rating or '未評価'}/5"]
            if acid != "適正": feedback_parts.append(f"酸味: {acid}")
            if bitter != "適正": feedback_parts.append(f"苦味・ボディ: {bitter}")
            if act_time: feedback_parts.append(f"実際の抽出完了時間: {act_time}")
            if issues_list: feedback_parts.append(f"気になった点: [{ '、'.join(issues_list) }]")
            if goals_list: feedback_parts.append(f"改善希望: [{ '、'.join(goals_list) }]")
            if comment: feedback_parts.append(f"コメント: {comment}")

            past_feedback_text = " | ".join(feedback_parts)

    if past_feedback_text != "過去の評価なし":
        st.info(f"💡 **この豆の前回のフィードバック**\n{past_feedback_text}\n（今回のAI提案に自動反映されます）")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 最適なレシピを提案してもらう", key="unique_recipe_button", use_container_width=True):
        with st.spinner("BARIS⚡太郎くんが最適なドリッパーと粉量、レシピを考案しています..."):
            roast_date_str = roast_date_input.strftime("%Y-%m-%d") if roast_date_input else "未指定"
            active_equipment = [eq for eq in equipment_data if eq.get("is_active", True) is not False]
            
            prompt = prompts.build_drip_prompt(
                chosen_bean=chosen_bean,
                roast_date_str=roast_date_str,
                flavor_profile=flavor_profile,
                cup_count=cup_count,
                equipment_data=active_equipment,
                past_feedback_text=past_feedback_text,
                coffee_type=selected_coffee_type,
                water_per_cup=selected_water_per_cup
            )
            
            recipe_data, error_msg = ai.generate_recipe(prompt)
            if recipe_data:
                st.session_state["current_recipe"] = recipe_data
                st.session_state["current_drip_params"] = {
                    "bean_name": bean_choice, "bean_id": chosen_bean_id,
                    "flavor_profile": flavor_profile, "cup_count": cup_count, "roast_date": roast_date_str,
                    "coffee_type": selected_coffee_type, "water_per_cup": selected_water_per_cup
                }
                
                # ドラフト（DRAFT）として1件のみ上書き保存
                draft_payload = {
                    "bean_id": chosen_bean_id,
                    "flavor_profile": flavor_profile,
                    "cup_count": cup_count,
                    "roasted_date": roast_date_str if roast_date_str != "未指定" else None,
                    "grind_setting": recipe_data.get('grind_setting', '-'),
                    "data": {
                        "is_draft": True,
                        "bean_name": bean_choice, "recipe": recipe_data,
                        "coffee_type": selected_coffee_type, "water_per_cup": selected_water_per_cup
                    }
                }
                
                try:
                    existing_draft_id = st.session_state.get("draft_log_id") or (draft_logs[-1].get("id") if draft_logs else None)
                    if existing_draft_id:
                        db.update_drip_log(existing_draft_id, draft_payload)
                    else:
                        new_res = db.insert_drip_log(draft_payload)
                        if new_res and isinstance(new_res, list) and len(new_res) > 0:
                            st.session_state["draft_log_id"] = new_res[0].get("id")
                except Exception as e:
                    print(f"Draft save error: {e}")
            else:
                st.warning("⚠️ 全てのAIモデルサーバーが混雑しています。1分ほど置いてから再度お試しください。")
                with st.expander("🔍 エラー詳細"):
                    st.write(error_msg)

    # 現在表示すべきレシピが存在する場合
    if "current_recipe" in st.session_state and st.session_state["current_recipe"]:
        recipe = st.session_state["current_recipe"]
        params = st.session_state["current_drip_params"]

        st.divider()
        st.success(f"レシピが完成しました！（{params.get('coffee_type', 'ホット')} / {params.get('water_per_cup', 300)}ml×{params.get('cup_count', 1)}杯）")
        
        st.markdown(f"### 📖 {recipe.get('recipe_title', '-')}")

        st.subheader("✨ 使用器具指示")
        st.write(f"- **ドリッパー**: {recipe.get('dripper', '-')}")
        st.write(f"- **フィルター**: {recipe.get('filter', '-')}")
        st.write(f"- **ミル・グラインダー**: {recipe.get('grinder', '-')}")
        
        st.divider()
        st.write(f"**おすすめ粉量**: {recipe.get('coffee_amount', '-')}")
        st.write(f"**お湯の温度**: {recipe.get('water_temp', '-')}")
        
        ice_val = recipe.get('ice_amount', 'なし')
        if ice_val and ice_val != 'なし' and ice_val != '-':
            st.write(f"**準備する氷（サーバー内）**: 🧊 {ice_val}")

        st.write(f"**ミルのグラインド設定**: {recipe.get('grind_setting', '-')}")
        st.write(f"**蒸らし時間**: {recipe.get('bloom_time', '-')}")

        st.markdown("### 📊 抽出ステップ手順")
        steps = recipe.get('recipe_steps', [])
        if steps and isinstance(steps, list):
            table_md = "| STEP | 時間 | 注ぎ量 | 累計湯量 | 流量 | 注ぎ方 | 目的 |\n"
            table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for s in steps:
                if isinstance(s, dict):
                    table_md += f"| {s.get('step_number', '-')} | {s.get('time', '-')} | {s.get('pour_amount', '-')} | {s.get('total_amount', '-')} | {s.get('flow_rate', '-')} | {s.get('pouring_method', '-')} | {s.get('purpose', '-')} |\n"
            st.markdown(table_md)

        st.info(f"💡 ワンポイント: {recipe.get('notes', '-')}")

        with st.expander("🔍 生成された生のデータ（JSON）を確認"):
            st.json(recipe)

        st.divider()
        st.subheader("📝 今回の抽出評価・フィードバック")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            drip_rating = st.slider("総合満足度", min_value=1, max_value=5, value=3, key="drip_input_rating")
            acid_level = st.select_slider("酸味の印象", options=["弱すぎる", "やや弱め", "適正", "やや強め", "強すぎる"], value="適正", key="drip_input_acid")
            bitter_level = st.select_slider("苦味・ボディの印象", options=["軽すぎる", "やや軽め", "適正", "やや重め", "重すぎる"], value="適正", key="drip_input_bitter")
            drip_issues = st.multiselect("味の気になった点（複数選択可）", prompts.TASTE_ISSUES_OPTIONS, default=["問題なし（バランス良好）"], key="drip_input_issues")
        with f_col2:
            actual_time = st.text_input("実際の落ちきり完了時間（任意）", placeholder="例: 2:45", key="drip_input_actual_time")
            drip_goals = st.multiselect("次回どうしたいか（複数選択可）", prompts.TARGET_GOALS_OPTIONS, default=["現状維持"], key="drip_input_goals")
            drip_comment = st.text_input("自由コメント（任意）", placeholder="例: 後半の落ちが遅く渋みが少し出た", key="drip_input_comment")
        
        if st.button("💾 この評価で確定・保存する", key="btn_save_recipe_with_eval", use_container_width=True):
            try:
                final_payload = {
                    "bean_id": params.get("bean_id"),
                    "flavor_profile": params.get("flavor_profile"),
                    "cup_count": params.get("cup_count"),
                    "roasted_date": params.get("roast_date") if params.get("roast_date") != "未指定" else None,
                    "grind_setting": recipe.get('grind_setting', '-'),
                    "data": {
                        "is_draft": False,  # ドラフト解除（確定ログ化）
                        "bean_name": params.get("bean_name"), "recipe": recipe,
                        "rating": drip_rating, "acid_level": acid_level, "bitter_level": bitter_level,
                        "actual_time": actual_time, "taste_issues": drip_issues,
                        "target_goals": drip_goals, "comment": drip_comment,
                        "coffee_type": params.get("coffee_type"), "water_per_cup": params.get("water_per_cup")
                    }
                }
                
                draft_id = st.session_state.get("draft_log_id") or (draft_logs[-1].get("id") if draft_logs else None)
                if draft_id:
                    db.update_drip_log(draft_id, final_payload)
                else:
                    db.insert_drip_log(final_payload)
                    
                st.success("レシピ評価を確定保存しました！")
                del st.session_state["current_recipe"]
                del st.session_state["current_drip_params"]
                if "draft_log_id" in st.session_state:
                    del st.session_state["draft_log_id"]
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")

# ==========================================
# タブ2: 豆管理画面
# ==========================================
with tab2:
    st.header("🫘 豆管理")
    st.subheader("豆の新規登録")
    col1, col2 = st.columns(2)
    with col1:
        bean_name = st.text_input("豆の名前（必須）", key="input_bean_name")
        shop_name = st.text_input("購入店", key="input_shop_name")
        roast_lvl = st.selectbox("焙煎度", ["浅煎り", "中浅煎り", "中煎り", "中深煎り", "深煎り"], key="input_roast_lvl")
        origin_name = st.text_input("産地", key="input_origin_name")
        flavor_notes = st.text_input("フレーバーノート", key="input_flavor_notes")
    with col2:
        farm_name = st.text_input("農園", key="input_farm_name")
        elevation_val = st.text_input("標高", key="input_elevation_val")
        process_type = st.text_input("精製方法 (プロセス)", key="input_process_type")
        variety_name = st.text_input("品種", key="input_variety_name")

    if st.button("🫘 豆を登録する", key="btn_add_bean"):
        if not bean_name:
            st.error("豆の名前を入力してください。")
        else:
            try:
                db.insert_bean({
                    "name": bean_name, "shop": shop_name, "roast_level": roast_lvl,
                    "origin": origin_name, "flavor_notes": flavor_notes, "farm": farm_name,
                    "elevation": elevation_val, "process": process_type, "variety": variety_name
                })
                st.success(f"「{bean_name}」を保存しました！")
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")
                    
    st.divider()
    st.subheader("登録済みの豆一覧")
    if beans_data:
        for b in beans_data:
            b_id = b.get("id")
            with st.expander(f"🫘 **{b.get('name')}** （{b.get('roast_level', '未設定')}）"):
                edit_key = f"edit_bean_mode_{b_id}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False

                if not st.session_state[edit_key]:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**購入店**: {b.get('shop') or '未設定'}")
                        st.write(f"**産地**: {b.get('origin') or '未設定'}")
                        st.write(f"**フレーバー**: {b.get('flavor_notes') or '未設定'}")
                    with c2:
                        st.write(f"**精製方法**: {b.get('process') or '未設定'}")
                        st.write(f"**品種**: {b.get('variety') or '未設定'}")
                    st.divider()
                    col_btn1, col_btn2 = st.columns([1, 1])
                    with col_btn1:
                        if st.button("✏️ 編集", key=f"btn_edit_mode_bean_{b_id}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🗑️ 削除", key=f"del_bean_{b_id}"):
                            try:
                                db.delete_bean(b_id)
                                st.success("削除しました。")
                                st.rerun()
                            except Exception as e:
                                st.error(f"削除エラー: {e}")
                else:
                    st.markdown("#### ✏️ 豆情報の編集")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        u_name = st.text_input("豆の名前", value=b.get("name") or "", key=f"u_bname_{b_id}")
                        u_shop = st.text_input("購入店", value=b.get("shop") or "", key=f"u_bshop_{b_id}")
                        roast_opts = ["浅煎り", "中浅煎り", "中煎り", "中深煎り", "深煎り"]
                        u_roast = st.selectbox("焙煎度", roast_opts, index=roast_opts.index(b.get("roast_level")) if b.get("roast_level") in roast_opts else 0, key=f"u_broast_{b_id}")
                        u_origin = st.text_input("産地", value=b.get("origin") or "", key=f"u_borigin_{b_id}")
                        u_flavor = st.text_input("フレーバーノート", value=b.get("flavor_notes") or "", key=f"u_bflavor_{b_id}")
                    with ec2:
                        u_farm = st.text_input("農園", value=b.get("farm") or "", key=f"u_bfarm_{b_id}")
                        u_elevation = st.text_input("標高", value=b.get("elevation") or "", key=f"u_belev_{b_id}")
                        u_process = st.text_input("精製方法", value=b.get("process") or "", key=f"u_bproc_{b_id}")
                        u_variety = st.text_input("品種", value=b.get("variety") or "", key=f"u_bvar_{b_id}")

                    if st.button("💾 更新を保存", key=f"btn_save_u_bean_{b_id}"):
                        try:
                            db.update_bean(b_id, {
                                "name": u_name, "shop": u_shop, "roast_level": u_roast,
                                "origin": u_origin, "flavor_notes": u_flavor, "farm": u_farm,
                                "elevation": u_elevation, "process": u_process, "variety": u_variety
                            })
                            st.session_state[edit_key] = False
                            st.success("更新しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新エラー: {e}")
    else:
        st.info("登録されている豆はまだありません。")

# ==========================================
# タブ3: 器具管理画面
# ==========================================
with tab3:
    st.header("🛠️ 器具管理")
    st.subheader("器具の新規登録")
    eq_category = st.selectbox("カテゴリ", ["ドリッパー", "ミル（グラインダー）", "フィルター", "サーバー", "その他"], key="input_eq_category")
    eq_name = st.text_input("器具の名前（必須）", key="input_eq_name")
    eq_brand = st.text_input("ブランド / メーカー", key="input_eq_brand")
    
    if st.button("☕ 器具を登録する", key="btn_add_equipment"):
        if eq_name:
            try:
                db.insert_equipment({"category": eq_category, "name": eq_name, "brand": eq_brand, "is_active": True})
                st.success(f"「{eq_name}」を登録しました！")
                st.rerun()
            except Exception as e:
                st.error(f"登録エラー: {e}")
                    
    st.divider()
    st.subheader("登録済みの器具一覧")
    if equipment_data:
        for eq in equipment_data:
            eq_id = eq.get("id")
            is_act = eq.get("is_active", True)
            if is_act is None: is_act = True

            edit_eq_key = f"edit_eq_mode_{eq_id}"
            if edit_eq_key not in st.session_state: st.session_state[edit_eq_key] = False

            if not st.session_state[edit_eq_key]:
                col_info, col_toggle, col_edit, col_del = st.columns([3, 1.5, 1, 1])
                with col_info:
                    status_str = "🟢 利用可能" if is_act else "🔴 欠品中（AI対象外）"
                    brand_str = f"（{eq.get('brand')}）" if eq.get('brand') else ""
                    st.markdown(f"・ **[{eq.get('category')}] {eq.get('name')}** {brand_str} - {status_str}")
                with col_toggle:
                    new_status = st.toggle("AI提案に含める", value=is_act, key=f"toggle_eq_{eq_id}")
                    if new_status != is_act:
                        db.update_equipment(eq_id, {"is_active": new_status})
                        st.rerun()
                with col_edit:
                    if st.button("✏️ 編集", key=f"btn_edit_mode_eq_{eq_id}"):
                        st.session_state[edit_eq_key] = True
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 削除", key=f"del_eq_{eq_id}"):
                        try:
                            db.delete_equipment(eq_id)
                            st.success("削除しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除エラー: {e}")
            else:
                st.markdown("#### ✏️ 器具情報の編集")
                eq_cat_opts = ["ドリッパー", "ミル（グラインダー）", "フィルター", "サーバー", "その他"]
                u_eq_cat = st.selectbox("カテゴリ", eq_cat_opts, index=eq_cat_opts.index(eq.get("category")) if eq.get("category") in eq_cat_opts else 0, key=f"u_eqcat_{eq_id}")
                u_eq_name = st.text_input("器具の名前", value=eq.get("name") or "", key=f"u_eqname_{eq_id}")
                u_eq_brand = st.text_input("ブランド / メーカー", value=eq.get("brand") or "", key=f"u_eqbrand_{eq_id}")

                col_u_save, col_u_cancel = st.columns([1, 1])
                with col_u_save:
                    if st.button("💾 更新を保存", key=f"btn_save_u_eq_{eq_id}"):
                        try:
                            db.update_equipment(eq_id, {
                                "category": u_eq_cat,
                                "name": u_eq_name,
                                "brand": u_eq_brand
                            })
                            st.session_state[edit_eq_key] = False
                            st.success("器具情報を更新しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新エラー: {e}")
                with col_u_cancel:
                    if st.button("キャンセル", key=f"btn_cancel_u_eq_{eq_id}"):
                        st.session_state[edit_eq_key] = False
                        st.rerun()
    else:
        st.info("登録されている器具はまだありません。")

# ==========================================
# タブ4: 履歴画面
# ==========================================
with tab4:
    st.header("📈 抽出履歴と再編集")
    if confirmed_logs:
        for log in confirmed_logs:
            log_id = log.get("id")
            created_at = str(log.get("created_at", ""))[:10]
            data_payload = log.get("data") or {}
            bean_name = data_payload.get("bean_name") or log.get("bean_name") or "不明な豆"
            recipe = data_payload.get("recipe") or {}
            
            curr_rating = data_payload.get("rating", 3)
            curr_acid = data_payload.get("acid_level", "適正")
            curr_bitter = data_payload.get("bitter_level", "適正")
            curr_actual_time = data_payload.get("actual_time", "")
            raw_issues = data_payload.get("taste_issues") or data_payload.get("taste_issue") or ["問題なし（バランス良好）"]
            curr_issues = [raw_issues] if isinstance(raw_issues, str) else raw_issues
            raw_goals = data_payload.get("target_goals") or data_payload.get("target_goal") or ["現状維持"]
            curr_goals = [raw_goals] if isinstance(raw_goals, str) else raw_goals
            curr_comment = data_payload.get("comment", "")
            
            safe_issues = [x for x in curr_issues if x in prompts.TASTE_ISSUES_OPTIONS]
            safe_goals = [x for x in curr_goals if x in prompts.TARGET_GOALS_OPTIONS]

            acid_opts = ["弱すぎる", "やや弱め", "適正", "やや強め", "強すぎる"]
            bitter_opts = ["軽すぎる", "やや軽め", "適正", "やや重め", "重すぎる"]

            log_type = data_payload.get("coffee_type", "ホット")
            log_water = data_payload.get("water_per_cup", 300)

            with st.expander(f"📅 {created_at} 🫘 {bean_name} [{log_type}/{log_water}ml] (★{curr_rating})"):
                st.write(f"**推奨ドリッパー**: {recipe.get('dripper', '-')} | **粉量**: {recipe.get('coffee_amount', '-')} | **湯温**: {recipe.get('water_temp', '-')}")
                
                steps = recipe.get('recipe_steps', [])
                if steps and isinstance(steps, list):
                    st.markdown("**抽出ステップ**:")
                    table_md = "| STEP | 時間 | 注ぎ量 | 累計湯量 | 流量 | 注ぎ方 | 目的 |\n"
                    table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                    for s in steps:
                        if isinstance(s, dict):
                            table_md += f"| {s.get('step_number', '-')} | {s.get('time', '-')} | {s.get('pour_amount', '-')} | {s.get('total_amount', '-')} | {s.get('flow_rate', '-')} | {s.get('pouring_method', '-')} | {s.get('purpose', '-')} |\n"
                    st.markdown(table_md)
                
                st.divider()
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    new_rating = st.slider("総合満足度", min_value=1, max_value=5, value=curr_rating, key=f"hist_rate_{log_id}")
                    new_acid = st.select_slider("酸味の印象", options=acid_opts, value=curr_acid if curr_acid in acid_opts else "適正", key=f"hist_acid_{log_id}")
                    new_bitter = st.select_slider("苦味・ボディの印象", options=bitter_opts, value=curr_bitter if curr_bitter in bitter_opts else "適正", key=f"hist_bitter_{log_id}")
                    new_issues = st.multiselect("味の気になった点", prompts.TASTE_ISSUES_OPTIONS, default=safe_issues, key=f"hist_issue_{log_id}")
                with f_col2:
                    new_actual_time = st.text_input("実際の落ちきり完了時間", value=curr_actual_time, key=f"hist_actual_time_{log_id}")
                    new_goals = st.multiselect("次回どうしたいか", prompts.TARGET_GOALS_OPTIONS, default=safe_goals, key=f"hist_goal_{log_id}")
                    new_comment = st.text_input("自由コメント", value=curr_comment, key=f"hist_comment_{log_id}")
                
                if st.button("⭐ 評価を更新する", key=f"btn_hist_rate_{log_id}"):
                    try:
                        updated_payload = data_payload
                        updated_payload["rating"] = new_rating
                        updated_payload["acid_level"] = new_acid
                        updated_payload["bitter_level"] = new_bitter
                        updated_payload["actual_time"] = new_actual_time
                        updated_payload["taste_issues"] = new_issues
                        updated_payload["target_goals"] = new_goals
                        updated_payload["comment"] = new_comment
                        db.update_drip_log(log_id, {"data": updated_payload})
                        st.success("評価を更新しました。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")

                if st.button("🗑 この履歴を削除", key=f"del_log_{log_id}"):
                    try:
                        db.delete_drip_log(log_id)
                        st.success("削除しました。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {e}")
    else:
        st.info("保存された抽出履歴はまだありません。")