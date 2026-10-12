import datetime
import streamlit as st
import streamlit.components.v1 as components
from services import db

def render():
    logs = db.get_drip_logs() or []
    
    if not logs:
        st.info("No logs found.")
        return

    beans = db.get_beans() or []
    bean_map = {b.get("id"): b.get("name", "Unknown Bean") for b in beans}

    for log in logs:
        log_id = log.get("id")
        created_at_str = log.get("created_at", "")
        
        date_display = created_at_str[:10] if created_at_str else "-"

        bean_id = log.get("bean_id")
        bean_name = bean_map.get(bean_id, "Custom Bean")

        log_data = log.get("data") or {}
        recipe = log_data.get("recipe") or {}

        recipe_title = recipe.get("recipe_title", "RECIPE")
        rating_num = log_data.get("rating", 3)
        flavor_profile = log.get("flavor_profile") or "BALANCED"

        header_text = f"{date_display}  |  {recipe_title}  |  {bean_name}  |  ★{rating_num}  |  {flavor_profile}"

        with st.expander(header_text):
            acidity = log_data.get("acidity", "Optimal")
            bitterness = log_data.get("bitterness", log_data.get("bitterness_body", "Optimal"))
            body = log_data.get("body", log_data.get("bitterness_body", "Optimal"))
            issues_list = log_data.get("issues", [])
            improvements_list = log_data.get("improvements", [])
            memo = log_data.get("memo") or ""

            issues_str = ", ".join(issues_list) if issues_list else "なし"
            improvements_str = ", ".join(improvements_list) if improvements_list else "なし"

            st.markdown(
                f'<div style="font-size: 0.9rem; line-height: 1.6; color: var(--subtext-color); margin-bottom: 12px;">'
                f'• Rating: ★{rating_num}<br>'
                f'• Acidity: {acidity} | Bitterness: {bitterness} | Body: {body}<br>'
                f'• FEELING: {issues_str}<br>'
                f'• NEXT: {improvements_str}<br>'
                f'• Comment: {memo if memo else "-"}'
                f'</div>',
                unsafe_allow_html=True
            )

            if recipe:
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size: 0.95rem; font-weight: bold; margin-bottom: 6px;">BREWING RECIPE</div>'
                    f'<div style="font-size: 0.85rem; color: var(--subtext-color); line-height: 1.5;">'
                    f'• Bean: {recipe.get("coffee_amount", "-")} | Grind: {recipe.get("grind_setting", "-")} | Temp: {recipe.get("water_temp", "-")}<br>'
                    f'• Dripper: {recipe.get("dripper", "-")} | Filter: {recipe.get("filter", "-")} | Grinder: {recipe.get("grinder", "-")}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            col_edit, col_del = st.columns(2)
            edit_key = f"edit_active_log_{log_id}"
            del_confirm_key = f"del_confirm_log_{log_id}"

            with col_edit:
                if st.button("EDIT", key=f"btn_edit_log_{log_id}", use_container_width=True):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)

            with col_del:
                if st.button("DELETE", key=f"btn_del_log_{log_id}", use_container_width=True):
                    st.session_state[del_confirm_key] = True

            # EDIT フォーム + 自動スムーズスクロール
            if st.session_state.get(edit_key, False):
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(f'<div id="edit-anchor-log-{log_id}"></div>', unsafe_allow_html=True)
                components.html(
                    f"""
                    <script>
                        const anchor = window.parent.document.getElementById('edit-anchor-log-{log_id}');
                        if (anchor) {{
                            anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    </script>
                    """,
                    height=0,
                )
                st.markdown('<div class="sub-header">EDIT LOG</div>', unsafe_allow_html=True)
                with st.form(f"edit_log_form_{log_id}"):
                    e_rating = st.slider("Rating (1-5)", min_value=1, max_value=5, value=int(rating_num))
                    
                    slider_opts = ["Very Light", "Light", "Optimal", "Strong", "Very Strong"]
                    
                    e_acidity_idx = slider_opts.index(acidity) if acidity in slider_opts else 2
                    e_acidity = st.select_slider("Acidity", options=slider_opts, value=slider_opts[e_acidity_idx])
                    
                    e_bitterness_idx = slider_opts.index(bitterness) if bitterness in slider_opts else 2
                    e_bitterness = st.select_slider("Bitterness", options=slider_opts, value=slider_opts[e_bitterness_idx])
                    
                    e_body_idx = slider_opts.index(body) if body in slider_opts else 2
                    e_body = st.select_slider("Body", options=slider_opts, value=slider_opts[e_body_idx])

                    feeling_opts = ["良好", "渋み・雑味", "水っぽさ", "重さ・濁り", "余韻の弱さ"]
                    default_feelings = [f for f in issues_list if f in feeling_opts] or ["良好"]
                    e_issues = st.pills("FEELING", options=feeling_opts, default=default_feelings, selection_mode="multi")

                    next_opts = ["現状維持", "コク・ボディ", "香り・華やかさ", "甘み・まとまり", "酸味・キレ", "すっきり・軽やか", "雑味オフ"]
                    default_nexts = [n for n in improvements_list if n in next_opts] or ["現状維持"]
                    e_improvements = st.pills("NEXT", options=next_opts, default=default_nexts, selection_mode="multi")

                    e_memo = st.text_area("COMMENT (OPTIONAL)", value=memo, height=100)

                    save_btn = st.form_submit_button("UPDATE", type="primary", use_container_width=True)
                    if save_btn:
                        updated_data = dict(log_data)
                        updated_data["rating"] = e_rating
                        updated_data["acidity"] = e_acidity
                        updated_data["bitterness"] = e_bitterness
                        updated_data["body"] = e_body
                        updated_data["issues"] = list(e_issues) if e_issues else []
                        updated_data["improvements"] = list(e_improvements) if e_improvements else []
                        updated_data["memo"] = e_memo

                        update_payload = {"data": updated_data}
                        if hasattr(db, 'update_drip_log') and db.update_drip_log(log_id, update_payload):
                            st.success("Updated successfully.")
                            st.session_state[edit_key] = False
                            st.rerun()
                        else:
                            st.error("Failed to update log.")

            # DELETE 再確認表示 + 自動スムーズスクロール
            if st.session_state.get(del_confirm_key, False):
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(f'<div id="del-anchor-log-{log_id}"></div>', unsafe_allow_html=True)
                components.html(
                    f"""
                    <script>
                        const anchor = window.parent.document.getElementById('del-anchor-log-{log_id}');
                        if (anchor) {{
                            anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    </script>
                    """,
                    height=0,
                )
                st.warning("Are you sure you want to delete this log?")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("CONFIRM DELETE", key=f"confirm_del_log_{log_id}", type="primary", use_container_width=True):
                        if db.delete_drip_log(log_id):
                            st.success("Deleted successfully.")
                            st.session_state.pop(del_confirm_key, None)
                            st.rerun()
                        else:
                            st.error("Failed to delete.")
                with col_c2:
                    if st.button("CANCEL", key=f"cancel_del_log_{log_id}", use_container_width=True):
                        st.session_state[del_confirm_key] = False
                        st.rerun()