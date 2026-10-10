import streamlit as st
import db
import prompts

def render():
    drip_logs_data = db.get_drip_logs()
    confirmed_logs = []

    if drip_logs_data:
        for log in drip_logs_data:
            data_p = log.get("data") or {}
            if data_p.get("is_draft") is not True:
                confirmed_logs.append(log)

    if confirmed_logs:
        confirmed_logs = sorted(confirmed_logs, key=lambda x: str(x.get("created_at", "")), reverse=True)

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
                    for s in steps:
                        if isinstance(s, dict):
                            st.markdown(f"- **STEP {s.get('step_number', '-')} ({s.get('time', '-')})**: {s.get('pour_amount', '-')}（累計 {s.get('total_amount', '-')}） / {s.get('pouring_method', '-')}")

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