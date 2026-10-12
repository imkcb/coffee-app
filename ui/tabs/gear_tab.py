import streamlit as st
import streamlit.components.v1 as components
from services import db

def render():
    GEAR_TYPES = ["DRIPPER", "GRINDER", "FILTER", "KETTLE", "SERVER", "SCALE", "OTHER"]

    # --- 1. LIST Section (TYPE別グループ表示) ---
    st.markdown('<div class="pixel-header">LIST</div>', unsafe_allow_html=True)
    
    gears = db.get_gears() or []
    if not gears:
        st.info("No gear registered.")
    else:
        # TYPEごとに器具をグループ化
        grouped_gears = {}
        for gear in gears:
            g_type = gear.get("type") or "OTHER"
            if g_type not in GEAR_TYPES:
                g_type_key = "OTHER"
            else:
                g_type_key = g_type
            
            if g_type_key not in grouped_gears:
                grouped_gears[g_type_key] = []
            grouped_gears[g_type_key].append(gear)

        # GEAR_TYPES の順序に従って見出し付きで表示（データが存在するTYPEのみ）
        for g_type in GEAR_TYPES:
            if g_type in grouped_gears and grouped_gears[g_type]:
                st.markdown(f'<div class="sub-header">{g_type}</div>', unsafe_allow_html=True)
                
                for gear in grouped_gears[g_type]:
                    gear_id = gear.get("id")
                    g_name = gear.get("name") or "Unknown Gear"
                    g_brand = gear.get("brand") or "-"
                    
                    is_active = gear.get("is_active", True)
                    if is_active is None:
                        is_active = True
                    status_label = "ON" if is_active else "OFF"

                    header_text = f"{g_name}  |  {g_brand}  |  [{status_label}]"
                    
                    with st.expander(header_text):
                        toggle_key = f"toggle_active_{gear_id}"
                        new_active = st.toggle("ACTIVE", value=is_active, key=toggle_key)
                        
                        if new_active != is_active:
                            db.update_gear(gear_id, {"is_active": new_active})
                            st.rerun()

                        st.markdown("<br>", unsafe_allow_html=True)

                        st.markdown(
                            f'<div style="font-size: 0.9rem; line-height: 1.6; color: var(--subtext-color); margin-bottom: 12px;">'
                            f'• Name: {g_name}<br>'
                            f'• Type: {g_type}<br>'
                            f'• Brand: {g_brand}<br>'
                            f'• Active: {status_label}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        col_edit, col_del = st.columns(2)
                        edit_key = f"edit_active_gear_{gear_id}"
                        del_confirm_key = f"del_confirm_gear_{gear_id}"

                        with col_edit:
                            if st.button("EDIT", key=f"btn_edit_gear_{gear_id}", use_container_width=True):
                                st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                        with col_del:
                            if st.button("DELETE", key=f"btn_del_gear_{gear_id}", use_container_width=True):
                                st.session_state[del_confirm_key] = True

                        # EDIT フォーム + 自動スムーズスクロール
                        if st.session_state.get(edit_key, False):
                            st.markdown("<hr>", unsafe_allow_html=True)
                            st.markdown(f'<div id="edit-anchor-gear-{gear_id}"></div>', unsafe_allow_html=True)
                            components.html(
                                f"""
                                <script>
                                    const anchor = window.parent.document.getElementById('edit-anchor-gear-{gear_id}');
                                    if (anchor) {{
                                        anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    }}
                                </script>
                                """,
                                height=0,
                            )
                            st.markdown('<div class="sub-header">EDIT GEAR</div>', unsafe_allow_html=True)
                            with st.form(f"edit_gear_form_{gear_id}"):
                                e_name = st.text_input("NAME *", value=g_name)
                                
                                type_idx = GEAR_TYPES.index(g_type) if g_type in GEAR_TYPES else 0
                                e_type = st.selectbox("TYPE", GEAR_TYPES, index=type_idx)
                                
                                e_brand = st.text_input("BRAND", value=g_brand if g_brand != "-" else "")

                                save_btn = st.form_submit_button("UPDATE", type="primary", use_container_width=True)
                                if save_btn:
                                    update_data = {
                                        "name": e_name,
                                        "type": e_type,
                                        "brand": e_brand
                                    }
                                    if db.update_gear(gear_id, update_data):
                                        st.success("Updated successfully.")
                                        st.session_state[edit_key] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to update.")

                        # DELETE 再確認表示 + 自動スムーズスクロール
                        if st.session_state.get(del_confirm_key, False):
                            st.markdown("<hr>", unsafe_allow_html=True)
                            st.markdown(f'<div id="del-anchor-gear-{gear_id}"></div>', unsafe_allow_html=True)
                            components.html(
                                f"""
                                <script>
                                    const anchor = window.parent.document.getElementById('del-anchor-gear-{gear_id}');
                                    if (anchor) {{
                                        anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    }}
                                </script>
                                """,
                                height=0,
                            )
                            st.warning("Are you sure you want to delete this gear?")
                            col_c1, col_c2 = st.columns(2)
                            with col_c1:
                                if st.button("CONFIRM DELETE", key=f"confirm_del_gear_{gear_id}", type="primary", use_container_width=True):
                                    if db.delete_gear(gear_id):
                                        st.success("Deleted successfully.")
                                        st.session_state.pop(del_confirm_key, None)
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete.")
                            with col_c2:
                                if st.button("CANCEL", key=f"cancel_del_gear_{gear_id}", use_container_width=True):
                                    st.session_state[del_confirm_key] = False
                                    st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 2. ADD GEAR Section ---
    st.markdown('<div class="pixel-header">ADD GEAR</div>', unsafe_allow_html=True)
    
    with st.form("add_gear_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("NAME *")
            gear_type = st.selectbox("TYPE", GEAR_TYPES, index=0)
        with col2:
            brand = st.text_input("BRAND")

        submit_btn = st.form_submit_button("ADD GEAR", type="primary", use_container_width=True)

        if submit_btn:
            if not name:
                st.error("Name is required.")
            else:
                data = {
                    "name": name,
                    "type": gear_type,
                    "brand": brand,
                    "is_active": True
                }
                if db.add_gear(data):
                    st.success("Gear added successfully.")
                    st.rerun()
                else:
                    st.error("Failed to add gear.")