import datetime
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

import db
import ai
import prompts

def get_session_id():
    ctx = get_script_run_ctx()
    if ctx:
        return ctx.session_id
    return "default_session"

def render():
    user_session_id = get_session_id()

    beans_data = db.get_beans()
    equipment_data = db.get_equipment()
    drip_logs_data = db.get_drip_logs()

    my_draft_log = None
    confirmed_logs = []

    if drip_logs_data:
        for log in drip_logs_data:
            data_p = log.get("data") or {}
            if data_p.get("is_draft") is True:
                if data_p.get("session_id") == user_session_id:
                    my_draft_log = log
            else:
                confirmed_logs.append(log)

    if confirmed_logs:
        confirmed_logs = sorted(confirmed_logs, key=lambda x: str(x.get("created_at", "")), reverse=True)

    bean_names = [b.get("name") for b in beans_data if b.get("name")] if beans_data else [
        "エチオピア イルガチェフェ", "グアテマラ アンティグア", "ブラジル サントス"
    ]

    if "default_cup_count" not in st.session_state:
        st.session_state["default_cup_count"] = 1
    if "coffee_type" not in st.session_state:
        st.session_state["coffee_type"] = "ホット"
    if "water_per_cup" not in st.session_state:
        st.session_state["water_per_cup"] = 300

    if "current_recipe" not in st.session_state and my_draft_log:
        draft_data = my_draft_log.get("data") or {}
        if draft_data.get("recipe"):
            st.session_state["current_recipe"] = draft_data.get("recipe")
            st.session_state["current_drip_params"] = {
                "bean_name": draft_data.get("bean_name"),
                "bean_id": my_draft_log.get("bean_id"),
                "flavor_profile": my_draft_log.get("flavor_profile"),
                "cup_count": my_draft_log.get("cup_count", 1),
                "roast_date": my_draft_log.get("roasted_date") or "未指定",
                "coffee_type": draft_data.get("coffee_type", "ホット"),
                "water_per_cup": draft_data.get("water_per_cup", 300)
            }
            st.session_state["draft_log_id"] = my_draft_log.get("id")

    st.header("1. 条件選択")

    st.markdown("##### ① 抽出タイプを選択")
    selected_coffee_type = st.radio(
        "抽出タイプ",
        ["ホット", "アイス"],
        index=0 if st.session_state["coffee_type"] == "ホット" else 1,
        horizontal=True,
        key="drip_coffee_type",
        label_visibility="collapsed"
    )
    st.session_state["coffee_type"] = selected_coffee_type

    shops = sorted(list(set([b.get("shop") for b in beans_data if b.get("shop")])))
    shop_options = ["すべて"] + shops

    st.markdown("---")
    st.markdown("##### ② 購入店を選択")
    selected_shop = st.radio(
        "購入店",
        shop_options,
        horizontal=True,
        key="drip_shop_choice",
        label_visibility="collapsed"
    )

    if selected_shop != "すべて":
        filtered_beans = [b for b in beans_data if b.get("shop") == selected_shop]
    else:
        filtered_beans = beans_data

    filtered_bean_names = [b.get("name") for b in filtered_beans if b.get("name")]
    if not filtered_bean_names:
        filtered_bean_names = bean_names

    st.markdown("---")
    st.markdown("##### ③ 豆を選択")
    bean_choice = st.radio(
        "豆を選択",
        filtered_bean_names,
        key="drip_bean_choice",
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### ④ 味の方向性")
    flavor_profile = st.radio(
        "味の方向性",
        ["すっきり・フルーティー", "バランス重視", "しっかり・コク旨"],
        horizontal=True,
        key="drip_flavor_profile",
        label_visibility="collapsed"
    )

    st.markdown("---")
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

                draft_payload = {
                    "bean_id": chosen_bean_id,
                    "flavor_profile": flavor_profile,
                    "cup_count": cup_count,
                    "roasted_date": roast_date_str if roast_date_str != "未指定" else None,
                    "grind_setting": recipe_data.get('grind_setting', '-'),
                    "data": {
                        "is_draft": True,
                        "session_id": user_session_id,
                        "bean_name": bean_choice, "recipe": recipe_data,
                        "coffee_type": selected_coffee_type, "water_per_cup": selected_water_per_cup
                    }
                }

                try:
                    existing_draft_id = st.session_state.get("draft_log_id") or (my_draft_log.get("id") if my_draft_log else None)
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

    if "current_recipe" in st.session_state and st.session_state["current_recipe"]:
        recipe = st.session_state["current_recipe"]
        params = st.session_state["current_drip_params"]

        st.divider()
        st.success(f"レシピが完成しました！（{params.get('coffee_type', 'ホット')} / {params.get('water_per_cup', 300)}ml×{params.get('cup_count', 1)}杯）")
        st.markdown(f"### 📖 {recipe.get('recipe_title', '-')}")

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.metric("おすすめ粉量", recipe.get('coffee_amount', '-'))
            st.metric("お湯の温度", recipe.get('water_temp', '-'))
        with c_p2:
            st.metric("ミル挽き目", recipe.get('grind_setting', '-'))
            ice_val = recipe.get('ice_amount', 'なし')
            if ice_val and ice_val != 'なし' and ice_val != '-':
                st.metric("事前投入の氷", f"🧊 {ice_val}")
            else:
                st.metric("蒸らし時間", recipe.get('bloom_time', '-'))

        with st.expander("✨ 使用指定器具の詳細を見る", expanded=False):
            st.write(f"- **ドリッパー**: {recipe.get('dripper', '-')}")
            st.write(f"- **フィルター**: {recipe.get('filter', '-')}")
            st.write(f"- **ミル・グラインダー**: {recipe.get('grinder', '-')}")

        st.markdown("### 📊 抽出ステップ手順")
        steps = recipe.get('recipe_steps', [])
        if steps and isinstance(steps, list):
            for s in steps:
                if isinstance(s, dict):
                    st.markdown(
                        f"""
                        <div style="background-color: #1e222a; padding: 12px 16px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 12px;">
                            <div style="font-size: 1.1em; font-weight: bold; color: #ffffff; display: flex; justify-content: space-between;">
                                <span>STEP {s.get('step_number', '-')}: {s.get('purpose', '-')}</span>
                                <span style="color: #ffbd45;">⏱️ {s.get('time', '-')}</span>
                            </div>
                            <div style="margin-top: 8px; font-size: 0.95em; color: #d0d4dc;">
                                💧 <b>注ぎ量:</b> {s.get('pour_amount', '-')} ｜ 🏁 <b>累計:</b> <span style="font-weight: bold; color: #40c4ff;">{s.get('total_amount', '-')}</span>
                            </div>
                            <div style="margin-top: 6px; font-size: 0.9em; color: #a0a8b6;">
                                🌀 <b>注ぎ方:</b> {s.get('pouring_method', '-')}（{s.get('flow_rate', '-')}）
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.info(f"💡 **ワンポイント解説**: {recipe.get('notes', '-')}")

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
                        "is_draft": False,
                        "session_id": user_session_id,
                        "bean_name": params.get("bean_name"), "recipe": recipe,
                        "rating": drip_rating, "acid_level": acid_level, "bitter_level": bitter_level,
                        "actual_time": actual_time, "taste_issues": drip_issues,
                        "target_goals": drip_goals, "comment": drip_comment,
                        "coffee_type": params.get("coffee_type"), "water_per_cup": params.get("water_per_cup")
                    }
                }

                draft_id = st.session_state.get("draft_log_id") or (my_draft_log.get("id") if my_draft_log else None)
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