import streamlit as st
import streamlit.components.v1 as components
from services import db

def render():
    ROAST_OPTIONS = ["LIGHT", "MEDIUM LIGHT", "MEDIUM", "MEDIUM DARK", "DARK"]

    # --- 1. LIST Section (ROASTERY別グループ表示) ---
    st.markdown('<div class="pixel-header">LIST</div>', unsafe_allow_html=True)
    
    beans = db.get_beans() or []
    if not beans:
        st.info("No beans registered.")
    else:
        # ROASTERYごとに豆データをグループ化
        grouped_beans = {}
        for bean in beans:
            r_name = bean.get("roastery")
            r_key = r_name.strip() if r_name and r_name.strip() else "OTHER"
            if r_key not in grouped_beans:
                grouped_beans[r_key] = []
            grouped_beans[r_key].append(bean)

        # 焙煎所名をソート（OTHERは末尾に配置）
        roasteries = sorted([r for r in grouped_beans.keys() if r != "OTHER"])
        if "OTHER" in grouped_beans:
            roasteries.append("OTHER")

        # 各ROASTERYの見出しをつけて描画
        for roastery_name in roasteries:
            st.markdown(f'<div class="sub-header">{roastery_name}</div>', unsafe_allow_html=True)
            
            for bean in grouped_beans[roastery_name]:
                bean_id = bean.get("id")
                b_name = bean.get("name", "Unknown Bean")
                b_roastery = bean.get("roastery") or "-"
                b_origin = bean.get("origin") or "-"

                header_text = f"{b_name}  |  {b_origin}"
                
                with st.expander(header_text):
                    st.markdown(
                        f'<div style="font-size: 0.9rem; line-height: 1.6; color: var(--subtext-color); margin-bottom: 12px;">'
                        f'• Roastery: {b_roastery}<br>'
                        f'• Origin: {b_origin}<br>'
                        f'• Farm: {bean.get("farm") or "-"}<br>'
                        f'• Elevation: {bean.get("elevation") or "-"}<br>'
                        f'• Process: {bean.get("process") or "-"}<br>'
                        f'• Variety: {bean.get("variety") or "-"}<br>'
                        f'• Flavor Notes: {bean.get("flavor_notes") or "-"}<br>'
                        f'• Roast Level: {bean.get("roast_level") or "-"}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    col_edit, col_del = st.columns(2)
                    
                    edit_key = f"edit_active_{bean_id}"
                    del_confirm_key = f"del_confirm_{bean_id}"

                    with col_edit:
                        if st.button("EDIT", key=f"btn_edit_{bean_id}", use_container_width=True):
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                    with col_del:
                        if st.button("DELETE", key=f"btn_del_{bean_id}", use_container_width=True):
                            st.session_state[del_confirm_key] = True

                    # EDITフォーム + 自動スムーズスクロール
                    if st.session_state.get(edit_key, False):
                        st.markdown("<hr>", unsafe_allow_html=True)
                        st.markdown(f'<div id="edit-anchor-bean-{bean_id}"></div>', unsafe_allow_html=True)
                        components.html(
                            f"""
                            <script>
                                const anchor = window.parent.document.getElementById('edit-anchor-bean-{bean_id}');
                                if (anchor) {{
                                    anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                }}
                            </script>
                            """,
                            height=0,
                        )
                        st.markdown('<div class="sub-header">EDIT BEAN</div>', unsafe_allow_html=True)
                        with st.form(f"edit_bean_form_{bean_id}"):
                            e_name = st.text_input("NAME *", value=b_name)
                            e_roastery = st.text_input("ROASTERY", value=bean.get("roastery") or "")
                            e_origin = st.text_input("ORIGIN", value=bean.get("origin") or "")
                            e_farm = st.text_input("FARM", value=bean.get("farm") or "")
                            e_elevation = st.text_input("ELEVATION", value=bean.get("elevation") or "")
                            e_process = st.text_input("PROCESS", value=bean.get("process") or "")
                            e_variety = st.text_input("VARIETY", value=bean.get("variety") or "")
                            e_flavor_notes = st.text_input("FLAVOR NOTES", value=bean.get("flavor_notes") or "")
                            
                            curr_roast = bean.get("roast_level") or "MEDIUM"
                            roast_map = {
                                "浅煎り": "LIGHT",
                                "中浅煎り": "MEDIUM LIGHT",
                                "中煎り": "MEDIUM",
                                "中深煎り": "MEDIUM DARK",
                                "深煎り": "DARK"
                            }
                            curr_roast_en = roast_map.get(curr_roast, curr_roast)
                            roast_idx = ROAST_OPTIONS.index(curr_roast_en) if curr_roast_en in ROAST_OPTIONS else 2
                            e_roast_level = st.selectbox("ROAST LEVEL", ROAST_OPTIONS, index=roast_idx)

                            save_btn = st.form_submit_button("UPDATE", type="primary", use_container_width=True)
                            if save_btn:
                                update_data = {
                                    "name": e_name,
                                    "roastery": e_roastery,
                                    "origin": e_origin,
                                    "farm": e_farm,
                                    "elevation": e_elevation,
                                    "process": e_process,
                                    "variety": e_variety,
                                    "flavor_notes": e_flavor_notes,
                                    "roast_level": e_roast_level
                                }
                                if db.update_bean(bean_id, update_data):
                                    st.success("Updated successfully.")
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                else:
                                    st.error("Failed to update.")

                    # DELETE 再確認表示 + 自動スムーズスクロール
                    if st.session_state.get(del_confirm_key, False):
                        st.markdown("<hr>", unsafe_allow_html=True)
                        st.markdown(f'<div id="del-anchor-bean-{bean_id}"></div>', unsafe_allow_html=True)
                        components.html(
                            f"""
                            <script>
                                const anchor = window.parent.document.getElementById('del-anchor-bean-{bean_id}');
                                if (anchor) {{
                                    anchor.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                }}
                            </script>
                            """,
                            height=0,
                        )
                        st.warning("Are you sure you want to delete this bean?")
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            if st.button("CONFIRM DELETE", key=f"confirm_del_{bean_id}", type="primary", use_container_width=True):
                                if db.delete_bean(bean_id):
                                    st.success("Deleted successfully.")
                                    st.session_state.pop(del_confirm_key, None)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete.")
                        with col_c2:
                            if st.button("CANCEL", key=f"cancel_del_{bean_id}", use_container_width=True):
                                st.session_state[del_confirm_key] = False
                                st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 2. ADD BEAN Section ---
    st.markdown('<div class="pixel-header">ADD BEAN</div>', unsafe_allow_html=True)
    
    with st.form("add_bean_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("NAME *")
            roastery = st.text_input("ROASTERY")
            origin = st.text_input("ORIGIN")
            farm = st.text_input("FARM")
            elevation = st.text_input("ELEVATION")
        with col2:
            process = st.text_input("PROCESS")
            variety = st.text_input("VARIETY")
            flavor_notes = st.text_input("FLAVOR NOTES")
            roast_level = st.selectbox("ROAST LEVEL", ROAST_OPTIONS, index=2)

        submit_btn = st.form_submit_button("ADD BEAN", type="primary", use_container_width=True)

        if submit_btn:
            if not name:
                st.error("Name is required.")
            else:
                data = {
                    "name": name,
                    "roastery": roastery,
                    "origin": origin,
                    "farm": farm,
                    "elevation": elevation,
                    "process": process,
                    "variety": variety,
                    "flavor_notes": flavor_notes,
                    "roast_level": roast_level
                }
                if db.add_bean(data):
                    st.success("Bean added successfully.")
                    st.rerun()
                else:
                    st.error("Failed to add bean.")