import datetime
import re
import streamlit as st
import streamlit.components.v1 as components
from services import db, ai

def extract_ml(text):
    """'50ml' などの文字列から数値を抽出"""
    if not text:
        return 0
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else 0

def render():
    st.markdown('<div class="pixel-header">SETUP</div>', unsafe_allow_html=True)

    # --- 1. SETUP Form ---
    beans = db.get_beans() or []
    
    roasteries = sorted(list(set([b.get("roastery") for b in beans if b.get("roastery")])))
    roastery_options = ["ALL"] + roasteries + ["NONE"]

    # 1. ROASTERY
    st.markdown('<div class="sub-header">1. ROASTERY</div>', unsafe_allow_html=True)
    selected_roastery = st.selectbox(
        "ROASTERY", 
        roastery_options, 
        index=None, 
        placeholder="SELECT", 
        label_visibility="collapsed"
    )

    target_bean = None

    if selected_roastery == "NONE":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sub-header">2. BEAN (ROAST LEVEL)</div>', unsafe_allow_html=True)
        roast_level_override = st.pills(
            "BEAN (ROAST LEVEL)",
            ["LIGHT", "MEDIUM LIGHT", "MEDIUM", "MEDIUM DARK", "DARK"],
            default="MEDIUM",
            label_visibility="collapsed"
        )
        target_bean = {
            "id": None,
            "name": f"CUSTOM BEAN ({roast_level_override})",
            "roast_level": roast_level_override,
            "roastery": "NONE"
        }
    elif selected_roastery is not None:
        if selected_roastery == "ALL":
            filtered_beans = beans
        else:
            filtered_beans = [b for b in beans if b.get("roastery") == selected_roastery]

        bean_options = {b.get("name", "Unknown Bean"): b for b in filtered_beans}
        bean_names = list(bean_options.keys())

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sub-header">2. BEAN</div>', unsafe_allow_html=True)
        selected_bean_name = st.selectbox(
            "BEAN", 
            bean_names, 
            index=None, 
            placeholder="SELECT", 
            label_visibility="collapsed"
        )
        if selected_bean_name and selected_bean_name in bean_options:
            target_bean = bean_options[selected_bean_name]
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sub-header">2. BEAN</div>', unsafe_allow_html=True)
        st.selectbox("BEAN", [], index=None, placeholder="SELECT", disabled=True, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. TYPE
    st.markdown('<div class="sub-header">3. TYPE</div>', unsafe_allow_html=True)
    coffee_type = st.pills("TYPE", ["HOT", "ICE"], default="HOT", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. FLAVOR
    st.markdown('<div class="sub-header">4. FLAVOR</div>', unsafe_allow_html=True)
    flavor_profile = st.pills("FLAVOR", ["FRUITY & LIGHT", "BALANCED", "RICH & BOLD"], default="FRUITY & LIGHT", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. QUANTITY & ROAST DATE
    st.markdown('<div class="sub-header">5. QUANTITY</div>', unsafe_allow_html=True)
    col_w, col_r = st.columns(2)
    with col_w:
        water_ml = st.number_input("WATER (ml)", min_value=100, max_value=1000, value=300, step=10)
    with col_r:
        roast_date_val = st.date_input(
            "ROAST DATE (OPTIONAL)", 
            value=None, 
            max_value=datetime.date.today()
        )
        roast_date_str = roast_date_val.strftime("%Y-%m-%d") if roast_date_val else "NULL"

    st.markdown("<br>", unsafe_allow_html=True)

    # Action Buttons
    col_gen, col_rst = st.columns([3, 1])
    with col_gen:
        generate_btn = st.button("GENERATE RECIPE", type="primary", use_container_width=True)
    with col_rst:
        if st.button("RESET", use_container_width=True):
            st.session_state.pop("current_recipe", None)
            st.session_state.pop("current_bean", None)
            st.rerun()

    # --- 2. Recipe Generation Logic ---
    if generate_btn:
        if not selected_roastery or not target_bean:
            st.error("Please select both ROASTERY and BEAN.")
            return

        with st.spinner("Thinking..."):
            try:
                # 1. アクティブ器具リストの取得
                all_gears = db.get_gears() or []
                active_gears = [
                    g for g in all_gears 
                    if g.get("is_active") is True or g.get("is_active") is None
                ]

                # 2. 直近最大5件のFEEDBACK（評価ログ）を取得
                all_logs = db.get_drip_logs() or []
                target_bean_id = target_bean.get("id")
                recent_feedbacks = []
                
                if target_bean_id:
                    bean_logs = [l for l in all_logs if l.get("bean_id") == target_bean_id]
                    if bean_logs:
                        recent_feedbacks = bean_logs[:5]  # 最新5件を取得

                # 3. AIレシピ生成（固定ルール + 器具 + SETUP + FEEDBACK履歴5件）
                recipe = ai.generate_recipe_with_gemini(
                    target_bean=target_bean,
                    coffee_type=coffee_type or "HOT",
                    water_ml=water_ml,
                    flavor_profile=flavor_profile or "BALANCED",
                    roast_date_str=roast_date_str,
                    available_gears=active_gears,
                    recent_feedbacks=recent_feedbacks
                )
                st.session_state["current_recipe"] = recipe
                st.session_state["current_bean"] = target_bean
                st.session_state["should_scroll_to_recipe"] = True
            except Exception as e:
                st.error(f"Recipe Generation Error: {e}")
                return

    # --- 3. Recipe Display ---
    recipe = st.session_state.get("current_recipe")
    target_bean = st.session_state.get("current_bean", {})

    if recipe:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div id="recipe-top"></div>', unsafe_allow_html=True)

        if st.session_state.get("should_scroll_to_recipe", False):
            components.html(
                """
                <script>
                    const anchor = window.parent.document.getElementById('recipe-top');
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                </script>
                """,
                height=0,
            )
            st.session_state["should_scroll_to_recipe"] = False

        # 1. Recipe Title
        st.markdown(
            f'<div class="recipe-title">{recipe.get("recipe_title", "RECIPE")}</div>', 
            unsafe_allow_html=True
        )

        # 2. NOTES
        notes = recipe.get("notes")
        if notes:
            st.markdown('<div class="pixel-header">NOTES</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div style="font-size: 0.95rem; line-height: 1.6; color: var(--text-color); margin-bottom: 12px;">{notes}</div>', 
                unsafe_allow_html=True
            )

        # 3. GEAR
        st.markdown('<div class="pixel-header">GEAR</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size: 0.95rem; line-height: 1.6; color: var(--text-color); margin-bottom: 16px;">'
            f'• Dripper: {recipe.get("dripper", "-")}<br>'
            f'• Filter: {recipe.get("filter", "-")}<br>'
            f'• Grinder: {recipe.get("grinder", "-")}'
            f'</div>', 
            unsafe_allow_html=True
        )

        # 4. SPEC
        st.markdown('<div class="pixel-header">SPEC</div>', unsafe_allow_html=True)
        
        coffee_val = recipe.get('coffee_amount', '-')
        grind_val = recipe.get('grind_setting', '-')
        temp_val = recipe.get('water_temp', '-')
        bloom_val = recipe.get('bloom_time', '-')
        ice_val = recipe.get('ice_amount', '-')

        spec_cards_html = (
            f'<div class="spec-grid">'
            f'<div class="spec-card"><div class="spec-label">BEAN</div><div class="spec-value">{coffee_val}</div></div>'
            f'<div class="spec-card"><div class="spec-label">GRIND</div><div class="spec-value">{grind_val}</div></div>'
            f'<div class="spec-card"><div class="spec-label">TEMP</div><div class="spec-value">{temp_val}</div></div>'
            f'<div class="spec-card"><div class="spec-label">BLOOM</div><div class="spec-value">{bloom_val}</div></div>'
        )
        
        if coffee_type == "ICE" and ice_val and str(ice_val).lower() != "none":
            spec_cards_html += (
                f'<div class="spec-card" style="grid-column: span 2;">'
                f'<div class="spec-label">ICE</div><div class="spec-value">{ice_val}</div>'
                f'</div>'
            )
            
        spec_cards_html += '</div>'
        st.markdown(spec_cards_html, unsafe_allow_html=True)

        # 5. STEPS
        st.markdown('<div class="pixel-header">STEPS</div>', unsafe_allow_html=True)
        
        steps = recipe.get("recipe_steps", [])
        total_recipe_water = water_ml if water_ml > 0 else 300
        total_steps = len(steps)

        for idx, step in enumerate(steps):
            step_num = step.get("step_number", idx + 1)
            
            time_html = ""
            if idx > 0:
                prev_time = steps[idx - 1].get("time", "")
                if idx == total_steps - 1:
                    curr_time = step.get("time", "")
                    if prev_time and curr_time:
                        time_html = f'<div class="step-time">-{prev_time}-{curr_time}</div>'
                    elif prev_time:
                        time_html = f'<div class="step-time">-{prev_time}-</div>'
                else:
                    if prev_time:
                        time_html = f'<div class="step-time">-{prev_time}-</div>'

            pour_ml = extract_ml(step.get("pour_amount", ""))
            wait_ratio = round((pour_ml / total_recipe_water) * 100) if total_recipe_water > 0 else 0
            total_amt = step.get("total_amount", "")

            st.markdown(
                f'<div class="step-card">'
                f'<div class="step-header">STEP {step_num}</div>'
                f'<div class="step-purpose">{step.get("purpose", "")}</div>'
                f'{time_html}'
                f'<div class="step-meta">'
                f'<span class="step-meta-highlight">TOTAL: {total_amt}</span> | '
                f'<span class="step-meta-highlight">WAIT: {wait_ratio}%</span>'
                f'</div>'
                f'<div class="step-meta" style="margin-top: 4px;">'
                f'METHOD: {step.get("pouring_method", "")} ({step.get("flow_rate", "")})'
                f'</div></div>',
                unsafe_allow_html=True
            )

        # RAW DATA
        with st.expander("RAW DATA"):
            st.json(recipe)

        st.markdown("<br>", unsafe_allow_html=True)

        # FEEDBACK
        st.markdown('<div class="pixel-header">FEEDBACK</div>', unsafe_allow_html=True)
        
        with st.form("feedback_form"):
            rating = st.slider("Rating (1-5)", min_value=1, max_value=5, value=3)
            st.markdown("<br>", unsafe_allow_html=True)

            acidity = st.select_slider(
                "Acidity",
                options=["Very Light", "Light", "Optimal", "Strong", "Very Strong"],
                value="Optimal"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            bitterness = st.select_slider(
                "Bitterness",
                options=["Very Light", "Light", "Optimal", "Strong", "Very Strong"],
                value="Optimal"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            body = st.select_slider(
                "Body",
                options=["Very Light", "Light", "Optimal", "Strong", "Very Strong"],
                value="Optimal"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown('<div class="sub-header">FEELING</div>', unsafe_allow_html=True)
            issues = st.pills(
                "FEELING",
                options=["良好", "渋み・雑味", "水っぽさ", "重さ・濁り", "余韻の弱さ"],
                default=["良好"],
                selection_mode="multi",
                label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown('<div class="sub-header">NEXT</div>', unsafe_allow_html=True)
            improvements = st.pills(
                "NEXT",
                options=["現状維持", "コク・ボディ", "香り・華やかさ", "甘み・まとまり", "酸味・キレ", "すっきり・軽やか", "雑味オフ"],
                default=["現状維持"],
                selection_mode="multi",
                label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            memo = st.text_area(
                "COMMENT (OPTIONAL)", 
                placeholder="例: 後半の抽出速度がやや遅く、わずかに渋みを感じた。（任意）", 
                height=100
            )

            st.markdown("<br>", unsafe_allow_html=True)
            save_feedback_btn = st.form_submit_button("SAVE FEEDBACK", type="primary", use_container_width=True)

            if save_feedback_btn:
                log_payload = {
                    "bean_id": target_bean.get("id"),
                    "flavor_profile": flavor_profile,
                    "grind_setting": recipe.get("grind_setting", ""),
                    "data": {
                        "rating": rating,
                        "acidity": acidity,
                        "bitterness": bitterness,
                        "body": body,
                        "issues": list(issues) if issues else [],
                        "improvements": list(improvements) if improvements else [],
                        "memo": memo,
                        "coffee_type": coffee_type,
                        "recipe": recipe
                    }
                }
                if db.add_drip_log(log_payload):
                    st.success("Feedback log saved successfully. You can review it in LOGS tab.")
                else:
                    st.error("Failed to save feedback log.")