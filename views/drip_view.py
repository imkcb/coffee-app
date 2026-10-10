import re
import datetime
import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

import db
import ai
import prompts

def get_session_id():
    ctx = get_script_run_ctx()
    if ctx:
        return ctx.session_id
    return "default_session"

# スクロールヘルパー関数
def auto_scroll_to(element_id):
    js_code = f"""
    <script>
        setTimeout(function() {{
            var element = window.parent.document.getElementById('{element_id}');
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}, 200);
    </script>
    """
    components.html(js_code, height=0)

# 蒸らし時間を「xx sec」のみに整形
def format_bloom_time(raw_bloom):
    if not raw_bloom or raw_bloom == '-':
        return "-"
    raw_str = str(raw_bloom).strip()
    match_range = re.search(r'0:00\s*[-~〜]\s*0:(\d{1,2})', raw_str)
    if match_range:
        return f"{int(match_range.group(1))} sec"
    match_sec = re.search(r'(\d+)', raw_str)
    if match_sec:
        return f"{int(match_sec.group(1))} sec"
    return raw_str

# ステップ時間を「-0:45」のように終了時間のみの形式に整形
def format_step_time(raw_time):
    if not raw_time or raw_time == '-':
        return "-"
    raw_str = str(raw_time).strip()
    match = re.search(r'(?:[-~〜]|\s+to\s+)?(\d{1,2}:\d{2})$', raw_str)
    if match:
        return f"-{match.group(1)}"
    match_single = re.search(r'(\d{1,2}:\d{2})', raw_str)
    if match_single:
        return f"-{match_single.group(1)}"
    match_sec = re.search(r'(\d+)', raw_str)
    if match_sec:
        sec = int(match_sec.group(1))
        m = sec // 60
        s = sec % 60
        return f"-{m}:{s:02d}"
    return f"-{raw_str}"

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
        "Brazil Santos", "Ethiopia Yirgacheffe", "Guatemala Antigua"
    ]

    # セッション状態の初期化
    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 1
    if "sel_type" not in st.session_state:
        st.session_state["sel_type"] = "HOT"
    if "sel_shop" not in st.session_state:
        st.session_state["sel_shop"] = "ALL"
    if "sel_bean" not in st.session_state:
        st.session_state["sel_bean"] = bean_names[0] if bean_names else ""
    if "sel_roast_level" not in st.session_state:
        st.session_state["sel_roast_level"] = "MEDIUM"
    if "sel_flavor" not in st.session_state:
        st.session_state["sel_flavor"] = "BALANCED"

    if "default_cup_count" not in st.session_state:
        st.session_state["default_cup_count"] = 1
    if "water_per_cup" not in st.session_state:
        st.session_state["water_per_cup"] = 300

    # ドラフト復元
    if "current_recipe" not in st.session_state and my_draft_log:
        draft_data = my_draft_log.get("data") or {}
        if draft_data.get("recipe"):
            st.session_state["current_recipe"] = draft_data.get("recipe")
            st.session_state["current_drip_params"] = {
                "bean_name": draft_data.get("bean_name"),
                "bean_id": my_draft_log.get("bean_id"),
                "flavor_profile": my_draft_log.get("flavor_profile"),
                "cup_count": my_draft_log.get("cup_count", 1),
                "roast_date": my_draft_log.get("roasted_date") or "UNSPECIFIED",
                "coffee_type": draft_data.get("coffee_type", "HOT"),
                "water_per_cup": draft_data.get("water_per_cup", 300)
            }
            st.session_state["draft_log_id"] = my_draft_log.get("id")

    st.markdown("### SETUP")

    # --- STEP 1: DRIP TYPE ---
    st.markdown('<div id="step-1" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
    st.markdown("#### 1. TYPE")
    type_col1, type_col2 = st.columns(2)
    with type_col1:
        if st.button("HOT", use_container_width=True, type="primary" if st.session_state["sel_type"] == "HOT" and st.session_state["wizard_step"] > 1 else "secondary"):
            st.session_state["sel_type"] = "HOT"
            if st.session_state["wizard_step"] == 1:
                st.session_state["wizard_step"] = 2
            st.session_state["scroll_target"] = "step-2"
            st.rerun()
    with type_col2:
        if st.button("ICED", use_container_width=True, type="primary" if st.session_state["sel_type"] == "ICED" and st.session_state["wizard_step"] > 1 else "secondary"):
            st.session_state["sel_type"] = "ICED"
            if st.session_state["wizard_step"] == 1:
                st.session_state["wizard_step"] = 2
            st.session_state["scroll_target"] = "step-2"
            st.rerun()

    # --- STEP 2: ROASTERY / SHOP ---
    if st.session_state["wizard_step"] >= 2:
        st.markdown("---")
        st.markdown('<div id="step-2" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.markdown("#### 2. ROASTERY")
        shops = sorted(list(set([b.get("shop") for b in beans_data if b.get("shop")])))
        shop_options = ["ALL", "NONE"] + shops

        shop_cols = st.columns(min(len(shop_options), 4))
        for idx, shop_item in enumerate(shop_options):
            col_target = shop_cols[idx % len(shop_cols)]
            with col_target:
                is_selected = (st.session_state["sel_shop"] == shop_item) and (st.session_state["wizard_step"] > 2)
                if st.button(shop_item, key=f"btn_shop_{shop_item}", use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state["sel_shop"] = shop_item
                    if st.session_state["wizard_step"] == 2:
                        st.session_state["wizard_step"] = 3
                    st.session_state["scroll_target"] = "step-3"
                    st.rerun()

    # --- STEP 3: BEAN or ROAST LEVEL ---
    if st.session_state["wizard_step"] >= 3:
        st.markdown("---")
        st.markdown('<div id="step-3" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)

        if st.session_state["sel_shop"] == "NONE":
            st.markdown("#### 3. ROAST LEVEL")
            roast_levels = ["LIGHT", "MEDIUM", "DARK"]
            r_cols = st.columns(3)
            for idx, r_lvl in enumerate(roast_levels):
                with r_cols[idx]:
                    is_selected = (st.session_state["sel_roast_level"] == r_lvl) and (st.session_state["wizard_step"] > 3)
                    if st.button(r_lvl, key=f"btn_roast_{r_lvl}", use_container_width=True, type="primary" if is_selected else "secondary"):
                        st.session_state["sel_roast_level"] = r_lvl
                        st.session_state["sel_bean"] = f"Custom Bean ({r_lvl})"
                        if st.session_state["wizard_step"] == 3:
                            st.session_state["wizard_step"] = 4
                        st.session_state["scroll_target"] = "step-4"
                        st.rerun()
        else:
            st.markdown("#### 3. BEAN")
            if st.session_state["sel_shop"] != "ALL":
                filtered_beans = [b for b in beans_data if b.get("shop") == st.session_state["sel_shop"]]
            else:
                filtered_beans = beans_data

            filtered_bean_names = [b.get("name") for b in filtered_beans if b.get("name")]
            if not filtered_bean_names:
                filtered_bean_names = bean_names

            # アルファベット順にソート
            filtered_bean_names = sorted(filtered_bean_names, key=lambda x: str(x).lower())

            bean_cols = st.columns(1 if len(filtered_bean_names) == 1 else 2)
            for idx, b_name in enumerate(filtered_bean_names):
                col_target = bean_cols[idx % len(bean_cols)]
                with col_target:
                    is_selected = (st.session_state["sel_bean"] == b_name) and (st.session_state["wizard_step"] > 3)
                    if st.button(b_name, key=f"btn_bean_{b_name}", use_container_width=True, type="primary" if is_selected else "secondary"):
                        st.session_state["sel_bean"] = b_name
                        if st.session_state["wizard_step"] == 3:
                            st.session_state["wizard_step"] = 4
                        st.session_state["scroll_target"] = "step-4"
                        st.rerun()

    # --- STEP 4: FLAVOR PROFILE ---
    if st.session_state["wizard_step"] >= 4:
        st.markdown("---")
        st.markdown('<div id="step-4" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.markdown("#### 4. FLAVOR")
        flavors = ["FRUITY & LIGHT", "BALANCED", "RICH & BOLD"]
        flv_cols = st.columns(3)
        for idx, flv in enumerate(flavors):
            with flv_cols[idx]:
                is_selected = (st.session_state["sel_flavor"] == flv) and (st.session_state["wizard_step"] > 4)
                if st.button(flv, key=f"btn_flv_{flv}", use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state["sel_flavor"] = flv
                    if st.session_state["wizard_step"] == 4:
                        st.session_state["wizard_step"] = 5
                    st.session_state["scroll_target"] = "step-5"
                    st.rerun()

    # --- STEP 5: FINE TUNING ---
    if st.session_state["wizard_step"] >= 5:
        st.markdown("---")
        st.markdown('<div id="step-5" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.markdown("#### 5. QUANTITY")
        with st.expander("SETTINGS", expanded=True):
            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                selected_water_per_cup = st.number_input(
                    "WATER / CUP (ml)", min_value=150, max_value=500,
                    value=st.session_state["water_per_cup"], step=10
                )
                cup_count = st.slider(
                    "CUPS", min_value=1, max_value=4,
                    value=st.session_state["default_cup_count"]
                )
            with col_sub2:
                today_date = datetime.date.today()
                roast_date_input = st.date_input(
                    "ROAST DATE",
                    value=None,
                    max_value=today_date,
                    key="drip_roast_date"
                )

        if st.session_state["sel_shop"] == "NONE":
            chosen_bean = {
                "name": f"Custom Bean ({st.session_state.get('sel_roast_level', 'MEDIUM')})",
                "roast_level": st.session_state.get('sel_roast_level', 'MEDIUM'),
                "notes": "Custom bean without roastery designation"
            }
            chosen_bean_id = None
        else:
            chosen_bean = next((b for b in beans_data if b.get("name") == st.session_state["sel_bean"]), {"name": st.session_state["sel_bean"]})
            chosen_bean_id = chosen_bean.get("id") if isinstance(chosen_bean, dict) else None

        # 過去フィードバック
        past_feedback_text = "No prior feedback"
        if chosen_bean_id and confirmed_logs:
            past_logs = [l for l in confirmed_logs if l.get("bean_id") == chosen_bean_id]
            if past_logs:
                latest_log = past_logs[0]
                log_data = latest_log.get("data") or {}
                rating = log_data.get("rating")
                acid = log_data.get("acid_level", "OPTIMAL")
                bitter = log_data.get("bitter_level", "OPTIMAL")
                act_time = log_data.get("actual_time", "")
                raw_issues = log_data.get("taste_issues") or log_data.get("taste_issue") or []
                issues_list = [raw_issues] if isinstance(raw_issues, str) else raw_issues
                raw_goals = log_data.get("target_goals") or log_data.get("target_goal") or []
                goals_list = [raw_goals] if isinstance(raw_goals, str) else raw_goals
                comment = log_data.get("comment", "")

                feedback_parts = [f"Rating: {rating or '-'}/5"]
                if acid != "適正" and acid != "OPTIMAL": feedback_parts.append(f"Acid: {acid}")
                if bitter != "適正" and bitter != "OPTIMAL": feedback_parts.append(f"Body: {bitter}")
                if act_time: feedback_parts.append(f"Time: {act_time}")
                if issues_list: feedback_parts.append(f"Issues: [{ ', '.join(issues_list) }]")
                if goals_list: feedback_parts.append(f"Goals: [{ ', '.join(goals_list) }]")
                if comment: feedback_parts.append(f"Note: {comment}")

                past_feedback_text = " | ".join(feedback_parts)

        if past_feedback_text != "No prior feedback":
            st.info(f"LAST MEMORY\n{past_feedback_text}")

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("GENERATE", key="unique_recipe_button", use_container_width=True, type="primary"):
                with st.spinner("COMPUTING..."):
                    roast_date_str = roast_date_input.strftime("%Y-%m-%d") if roast_date_input else "UNSPECIFIED"
                    active_equipment = [eq for eq in equipment_data if eq.get("is_active", True) is not False]

                    prompt = prompts.build_drip_prompt(
                        chosen_bean=chosen_bean,
                        roast_date_str=roast_date_str,
                        flavor_profile=st.session_state["sel_flavor"],
                        cup_count=cup_count,
                        equipment_data=active_equipment,
                        past_feedback_text=past_feedback_text,
                        coffee_type=st.session_state["sel_type"],
                        water_per_cup=selected_water_per_cup
                    )

                    recipe_data, error_msg = ai.generate_recipe(prompt)
                    if recipe_data:
                        st.session_state["current_recipe"] = recipe_data
                        st.session_state["current_drip_params"] = {
                            "bean_name": chosen_bean.get("name"), "bean_id": chosen_bean_id,
                            "flavor_profile": st.session_state["sel_flavor"], "cup_count": cup_count, "roast_date": roast_date_str,
                            "coffee_type": st.session_state["sel_type"], "water_per_cup": selected_water_per_cup
                        }

                        draft_payload = {
                            "bean_id": chosen_bean_id,
                            "flavor_profile": st.session_state["sel_flavor"],
                            "cup_count": cup_count,
                            "roasted_date": roast_date_str if roast_date_str != "UNSPECIFIED" else None,
                            "grind_setting": recipe_data.get('grind_setting', '-'),
                            "data": {
                                "is_draft": True,
                                "session_id": user_session_id,
                                "bean_name": chosen_bean.get("name"), "recipe": recipe_data,
                                "coffee_type": st.session_state["sel_type"], "water_per_cup": selected_water_per_cup
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
                        st.session_state["scroll_target"] = "recipe-view"
                        st.rerun()
                    else:
                        st.warning("SERVERS BUSY. RETRY LATER.")
                        with st.expander("ERROR DETAILS"):
                            st.write(error_msg)

        with col_btn2:
            if st.button("RESET", use_container_width=True):
                st.session_state["wizard_step"] = 1
                st.session_state["scroll_target"] = "step-1"
                st.rerun()

    # --- RECIPE DISPLAY ---
    if "current_recipe" in st.session_state and st.session_state["current_recipe"]:
        recipe = st.session_state["current_recipe"]
        params = st.session_state["current_drip_params"]

        st.divider()
        st.markdown('<div id="recipe-view" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.success(f"READY // [{params.get('coffee_type', 'HOT')}] {params.get('water_per_cup', 300)}ml x {params.get('cup_count', 1)}")
        st.markdown(f"### {recipe.get('recipe_title', '-')}")

        formatted_bloom = format_bloom_time(recipe.get('bloom_time'))

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.metric("COFFEE", recipe.get('coffee_amount', '-'))
            st.metric("TEMP", recipe.get('water_temp', '-'))
            st.metric("DRIPPER", recipe.get('dripper', '-'))
            st.metric("GRINDER", recipe.get('grinder', '-'))
        with c_p2:
            st.metric("GRIND", recipe.get('grind_setting', '-'))
            st.metric("BLOOM", formatted_bloom)
            st.metric("FILTER", recipe.get('filter', '-'))

        ice_val = recipe.get('ice_amount', 'なし')
        if ice_val and ice_val != 'なし' and ice_val != '-':
            st.info(f"PRE-ICE: {ice_val}")

        st.markdown("### STEPS")
        steps = recipe.get('recipe_steps', [])
        if steps and isinstance(steps, list):
            for s in steps:
                if isinstance(s, dict):
                    step_time = format_step_time(s.get('time', '-'))
                    st.markdown(
                        f"""
                        <div style="background-color: #0D0D0D; padding: 12px 16px; border: 1px solid #262626; border-left: 3px solid #FF9900; margin-bottom: 12px; border-radius: 4px;">
                            <div style="font-size: 1.0em; font-weight: bold; color: #FFFFFF;">
                                STEP {s.get('step_number', '-')}: {s.get('purpose', '-')}
                            </div>
                            <div style="font-size: 0.9em; font-weight: bold; color: #FF9900; margin-top: 2px;">
                                {step_time}
                            </div>
                            <div style="margin-top: 8px; font-size: 0.9em; color: #CCCCCC;">
                                <b>POUR:</b> {s.get('pour_amount', '-')} ｜ <b>TOTAL:</b> <span style="font-weight: bold; color: #FFFFFF;">{s.get('total_amount', '-')}</span>
                            </div>
                            <div style="margin-top: 4px; font-size: 0.85em; color: #888888;">
                                <b>METHOD:</b> {s.get('pouring_method', '-')}（{s.get('flow_rate', '-')}）
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.info(f"NOTES: {recipe.get('notes', '-')}")

        with st.expander("RAW DATA"):
            st.json(recipe)

        st.divider()
        st.subheader("EVALUATION")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            drip_rating = st.slider("RATING (1-5)", min_value=1, max_value=5, value=3, key="drip_input_rating")
            acid_level = st.select_slider("ACIDITY", options=["TOO WEAK", "WEAK", "OPTIMAL", "STRONG", "TOO STRONG"], value="OPTIMAL", key="drip_input_acid")
            bitter_level = st.select_slider("BODY / BITTERNESS", options=["TOO LIGHT", "LIGHT", "OPTIMAL", "HEAVY", "TOO HEAVY"], value="OPTIMAL", key="drip_input_bitter")
            drip_issues = st.multiselect("TASTE ISSUES", prompts.TASTE_ISSUES_OPTIONS, default=["問題なし（バランス良好）"], key="drip_input_issues")
        with f_col2:
            actual_time = st.text_input("TOTAL TIME (e.g. 2:45)", placeholder="e.g. 2:45", key="drip_input_actual_time")
            drip_goals = st.multiselect("NEXT GOALS", prompts.TARGET_GOALS_OPTIONS, default=["現状維持"], key="drip_input_goals")
            drip_comment = st.text_input("NOTES / COMMENT", placeholder="e.g. Slight astringency in finish", key="drip_input_comment")

        if st.button("SAVE EVALUATION", key="btn_save_recipe_with_eval", use_container_width=True, type="primary"):
            try:
                final_payload = {
                    "bean_id": params.get("bean_id"),
                    "flavor_profile": params.get("flavor_profile"),
                    "cup_count": params.get("cup_count"),
                    "roasted_date": params.get("roast_date") if params.get("roast_date") != "UNSPECIFIED" else None,
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

                st.success("LOG SAVED!")
                del st.session_state["current_recipe"]
                del st.session_state["current_drip_params"]
                if "draft_log_id" in st.session_state:
                    del st.session_state["draft_log_id"]
                st.session_state["wizard_step"] = 1
                st.session_state["scroll_target"] = "step-1"
                st.rerun()
            except Exception as e:
                st.error(f"SAVE ERROR: {e}")

    # スクロール対象の実行
    if "scroll_target" in st.session_state and st.session_state["scroll_target"]:
        auto_scroll_to(st.session_state["scroll_target"])
        st.session_state["scroll_target"] = None