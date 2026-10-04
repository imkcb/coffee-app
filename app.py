import streamlit as st
import db
import ai
import prompts

# 1. データの初期取得
beans_data = db.get_beans()
equipment_data = db.get_equipment()
drip_logs_data = db.get_drip_logs()

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

# 3. アプリタイトルと4タブ構成の定義
st.title("BARIS⚡太郎くん")
tab1, tab2, tab3, tab4 = st.tabs(["☕ ドリップ", "🫘 豆管理", "🛠️ 器具管理", "📈 履歴"])

# ==========================================
# タブ1: ドリップ画面
# ==========================================
with tab1:
    st.header("1. 条件選択")
    
    # --- ステップ1: 抽出タイプ ---
    selected_coffee_type = st.radio(
        "① 抽出タイプ",
        ["ホット", "アイス"],
        index=0 if st.session_state["coffee_type"] == "ホット" else 1,
        horizontal=True,
        key="drip_coffee_type"
    )
    
    # --- ステップ2: 購入店で絞り込み ---
    shops = sorted(list(set([b.get("shop") for b in beans_data if b.get("shop")])))
    shop_options = ["すべて"] + shops
    
    selected_shop = st.radio(
        "② 購入店を選択",
        shop_options,
        horizontal=True,
        key="drip_shop_choice"
    )
    
    # 店舗に基づいて豆リストをフィルタリング
    if selected_shop != "すべて":
        filtered_beans = [b for b in beans_data if b.get("shop") == selected_shop]
    else:
        filtered_beans = beans_data
        
    filtered_bean_names = [b.get("name") for b in filtered_beans if b.get("name")]
    if not filtered_bean_names:
        filtered_bean_names = bean_names
        
    # --- ステップ3: 豆を選択 ---
    bean_choice = st.radio(
        "③ 豆を選択",
        filtered_bean_names,
        key="drip_bean_choice"
    )
    
    # --- ステップ4: 味の方向性 ---
    flavor_profile = st.radio(
        "④ 味の方向性",
        ["すっきり・フルーティー", "バランス重視", "しっかり・コク旨"],
        horizontal=True,
        key="drip_flavor_profile"
    )
    
    # --- ステップ5: 詳細調整 ---
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
            roast_date_input = st.date_input("焙煎日（任意）", value=None, key="drip_roast_date")

    chosen_bean = next((b for b in beans_data if b.get("name") == bean_choice), {"name": bean_choice})
    chosen_bean_id = chosen_bean.get("id") if isinstance(chosen_bean, dict) else None
    
    # 直近の抽出評価を自動検索
    past_feedback_text = "過去の評価なし"
    if chosen_bean_id and drip_logs_data:
        past_logs = [l for l in drip_logs_data if l.get("bean_id") == chosen_bean_id]
        if past_logs:
            latest_log = past_logs[0]
            log_data = latest_log.get("data") or {}
            rating = log_data.get("rating")
            raw_issues = log_data.get("taste_issues") or log_data.get("taste_issue") or []
            issues_list = [raw_issues] if isinstance(raw_issues, str) else raw_issues
            raw_goals = log_data.get("target_goals") or log_data.get("target_goal") or []
            goals_list = [raw_goals] if isinstance(raw_goals, str) else raw_goals
            comment = log_data.get("comment", "")
            
            if rating or issues_list or goals_list:
                past_feedback_text = (
                    f"満足度: ★{rating or '未評価'}/5 | "
                    f"気になった点: [{ '、'.join(issues_list) or '特になし' }] | "
                    f"改善希望: [{ '、'.join(goals_list) or 'なし' }] | "
                    f"コメント: {comment or 'なし'}"
                )

    if past_feedback_text != "過去の評価なし":
        st.info(f"💡 **この豆の前回のフィードバック**\n{past_feedback_text}\n（今回のAI提案に自動反映されます）")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 最適なレシピを提案してもらう", key="unique_recipe_button", use_container_width=True):
        with st.spinner("天才焙煎士（Gemini）が最適なドリッパーと粉量、レシピを考案しています..."):
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
            else:
                st.warning("⚠️ 全てのAIモデルサーバーが混雑しています。1分ほど置いてから再度お試しください。")
                with st.expander("🔍 エラー詳細"):
                    st.write(error_msg)

    if "current_recipe" in st.session_state and st.session_state["current_recipe"]:
        recipe_data = st.session_state["current_recipe"]
        params = st.session_state["current_drip_params"]
        
        st.divider()
        st.success(f"レシピが完成しました！（{params.get('coffee_type', 'ホット')} / {params.get('water_per_cup', 300)}ml×{params.get('cup_count', 1)}杯）")
        
        st.subheader("✨ 使用器具指示")
        st.write(f"- **ドリッパー**: {recipe_data.get('selected_dripper', '指定なし')}")
        st.write(f"- **フィルター**: {recipe_data.get('selected_filter', '指定なし')}")
        st.write(f"- **ミル・グラインダー**: {recipe_data.get('selected_grinder', '指定なし')}")
        
        st.divider()
        st.write(f"**おすすめ粉量**: {recipe_data.get('recommended_powder_weight')} g")
        st.write(f"**お湯の温度**: {recipe_data.get('water_temp')} ℃")
        st.write(f"**蒸らし時間**: {recipe_data.get('bloom_time')} 秒")
        st.write(f"**ミルのグラインド設定**: {recipe_data.get('grind_setting')}")
        
        st.markdown("### 📊 抽出ステップ手順")
        steps = recipe_data.get('recipe_steps', [])
        if steps:
            table_md = "| STEP | 時間 | 注ぎ量 | 累計湯量 | 流量 | 注ぎ方 | 目的 |\n"
            table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for s in steps:
                step_num = s.get('step_number') if isinstance(s, dict) else s.step_number
                time_t = s.get('time_target') if isinstance(s, dict) else s.time_target
                step_w = s.get('step_water') if isinstance(s, dict) else s.step_water
                total_w = s.get('total_water') if isinstance(s, dict) else s.total_water
                flow = s.get('flow_rate') if isinstance(s, dict) else s.flow_rate
                method = s.get('pouring_method') if isinstance(s, dict) else s.pouring_method
                purp = s.get('purpose') if isinstance(s, dict) else s.purpose
                
                table_md += f"| {step_num} | {time_t} | {step_w}ml | {total_w}ml | {flow} | {method} | {purp} |\n"
            
            st.markdown(table_md)
            
        st.info(f"💡 ワンポイント: {recipe_data.get('tasting_notes')}")
        
        st.divider()
        st.subheader("📝 今回の抽出評価・フィードバック（任意）")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            drip_rating = st.slider("総合満足度", min_value=1, max_value=5, value=3, key="drip_input_rating")
            drip_issues = st.multiselect("味の気になった点（複数選択可）", prompts.TASTE_ISSUES_OPTIONS, default=["問題なし（バランス良好）"], key="drip_input_issues")
        with f_col2:
            drip_goals = st.multiselect("次回どうしたいか（複数選択可）", prompts.TARGET_GOALS_OPTIONS, default=["現状維持"], key="drip_input_goals")
            drip_comment = st.text_input("自由コメント（任意）", placeholder="例: 後味に少し渋みが残る", key="drip_input_comment")
        
        if st.button("💾 このレシピと評価を保存する", key="btn_save_recipe_with_eval", use_container_width=True):
            try:
                db.insert_drip_log({
                    "bean_id": params.get("bean_id"),
                    "flavor_profile": params.get("flavor_profile"),
                    "cup_count": params.get("cup_count"),
                    "roasted_date": params.get("roast_date") if params.get("roast_date") != "未指定" else None,
                    "grind_setting": recipe_data.get("grind_setting"),
                    "data": {
                        "bean_name": params.get("bean_name"), "recipe": recipe_data,
                        "rating": drip_rating, "taste_issues": drip_issues,
                        "target_goals": drip_goals, "comment": drip_comment,
                        "coffee_type": params.get("coffee_type"), "water_per_cup": params.get("water_per_cup")
                    }
                })
                st.success("レシピと評価を正常に保存しました！")
                del st.session_state["current_recipe"]
                del st.session_state["current_drip_params"]
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
                            db.delete_bean(b_id)
                            st.rerun()
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
                        db.update_bean(b_id, {
                            "name": u_name, "shop": u_shop, "roast_level": u_roast,
                            "origin": u_origin, "flavor_notes": u_flavor, "farm": u_farm,
                            "elevation": u_elevation, "process": u_process, "variety": u_variety
                        })
                        st.session_state[edit_key] = False
                        st.rerun()
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
            db.insert_equipment({"category": eq_category, "name": eq_name, "brand": eq_brand, "is_active": True})
            st.rerun()
                    
    st.divider()
    st.subheader("登録済みの器具一覧")
    if equipment_data:
        for eq in equipment_data:
            eq_id = eq.get("id")
            is_act = eq.get("is_active", True)
            if is_act is None: is_act = True

            col_info, col_toggle, col_del = st.columns([3, 1.5, 1])
            with col_info:
                status_str = "🟢 利用可能" if is_act else "🔴 欠品中（AI対象外）"
                st.markdown(f"・ **[{eq.get('category')}] {eq.get('name')}** （{status_str}）")
            with col_toggle:
                new_status = st.toggle("AI提案に含める", value=is_act, key=f"toggle_eq_{eq_id}")
                if new_status != is_act:
                    db.update_equipment(eq_id, {"is_active": new_status})
                    st.rerun()
            with col_del:
                if st.button("🗑️ 削除", key=f"del_eq_{eq_id}"):
                    db.delete_equipment(eq_id)
                    st.rerun()
    else:
        st.info("登録されている器具はまだありません。")

# ==========================================
# タブ4: 履歴画面
# ==========================================
with tab4:
    st.header("📈 抽出履歴と再編集")
    if drip_logs_data:
        for log in drip_logs_data:
            log_id = log.get("id")
            created_at = log.get("created_at", "")[:10]
            data_payload = log.get("data") or {}
            bean_name = data_payload.get("bean_name", "不明な豆")
            recipe = data_payload.get("recipe") or {}
            
            curr_rating = data_payload.get("rating", 3)
            raw_issues = data_payload.get("taste_issues") or data_payload.get("taste_issue") or ["問題なし（バランス良好）"]
            curr_issues = [raw_issues] if isinstance(raw_issues, str) else raw_issues
            raw_goals = data_payload.get("target_goals") or data_payload.get("target_goal") or ["現状維持"]
            curr_goals = [raw_goals] if isinstance(raw_goals, str) else raw_goals
            curr_comment = data_payload.get("comment", "")
            
            log_type = data_payload.get("coffee_type", "ホット")
            log_water = data_payload.get("water_per_cup", 300)
            
            with st.expander(f"📅 {created_at} - 🫘 {bean_name} [{log_type}/{log_water}ml] (★{curr_rating})"):
                st.write(f"**推奨ドリッパー**: {recipe.get('selected_dripper', '未設定')} | **粉量**: {recipe.get('recommended_powder_weight', '-')} g | **湯温**: {recipe.get('water_temp', '-')} ℃")
                
                # 履歴でもステップを表形式で表示
                steps = recipe.get("recipe_steps", [])
                if steps:
                    st.markdown("**抽出ステップ**:")
                    table_md = "| STEP | 時間 | 注ぎ量 | 累計湯量 | 流量 | 注ぎ方 | 目的 |\n"
                    table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                    for s in steps:
                        if isinstance(s, dict):
                            table_md += f"| {s.get('step_number','')} | {s.get('time_target','')} | {s.get('step_water','')}ml | {s.get('total_water','')}ml | {s.get('flow_rate','')} | {s.get('pouring_method','')} | {s.get('purpose','')} |\n"
                        else:
                            table_md += f"| {s} |\n"
                    st.markdown(table_md)
                
                st.divider()
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    new_rating = st.slider("総合満足度", min_value=1, max_value=5, value=curr_rating, key=f"hist_rate_{log_id}")
                    new_issues = st.multiselect("味の気になった点", prompts.TASTE_ISSUES_OPTIONS, default=curr_issues, key=f"hist_issue_{log_id}")
                with f_col2:
                    new_goals = st.multiselect("次回どうしたいか", prompts.TARGET_GOALS_OPTIONS, default=curr_goals, key=f"hist_goal_{log_id}")
                    new_comment = st.text_input("自由コメント", value=curr_comment, key=f"hist_comment_{log_id}")
                
                if st.button("⭐ 評価を更新する", key=f"btn_hist_rate_{log_id}"):
                    updated_payload = data_payload
                    updated_payload["rating"] = new_rating
                    updated_payload["taste_issues"] = new_issues
                    updated_payload["target_goals"] = new_goals
                    updated_payload["comment"] = new_comment
                    db.update_drip_log(log_id, {"data": updated_payload})
                    st.success("評価を更新しました。")
                    st.rerun()

                if st.button("🗑️️ この履歴を削除", key=f"del_log_{log_id}"):
                    db.delete_drip_log(log_id)
                    st.rerun()
    else:
        st.info("保存された抽出履歴はまだありません。")