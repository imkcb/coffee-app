import streamlit as st
import db

def render():
    st.markdown('<div class="beans-tab-marker"></div>', unsafe_allow_html=True)
    st.markdown("### BEANS")

    st.markdown("#### ADD BEAN")
    with st.form("add_bean_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            bean_name = st.text_input("BEAN NAME")
            shop_name = st.text_input("ROASTERY / SHOP")
        with col2:
            roast_level = st.selectbox("ROAST LEVEL", ["LIGHT", "MEDIUM-LIGHT", "MEDIUM", "MEDIUM-DARK", "DARK"])
            origin = st.text_input("ORIGIN", placeholder="例: Ethiopia")

        notes = st.text_input("NOTES", placeholder="例: ナチュラル製法、華やかな香り（任意）")
        
        submitted = st.form_submit_button("REGISTER BEAN", type="primary", use_container_width=True)
        if submitted:
            if bean_name:
                try:
                    payload = {
                        "name": bean_name,
                        "shop": shop_name if shop_name else "Unknown",
                        "roast_level": roast_level,
                        "origin": origin,
                        "notes": notes
                    }
                    db.insert_bean(payload)
                    st.success("BEAN REGISTERED!")
                    st.rerun()
                except Exception as e:
                    st.error(f"ERROR: {e}")
            else:
                st.warning("PLEASE INPUT BEAN NAME")

    st.divider()

    st.markdown("#### BEAN LIST")
    beans_data = db.get_beans()
    if beans_data:
        sorted_beans = sorted(beans_data, key=lambda x: str(x.get("name", "")).lower())
        for bean in sorted_beans:
            b_name = bean.get("name", "-")
            b_shop = bean.get("shop", "Unknown")
            b_roast = bean.get("roast_level", "-")
            b_notes = bean.get("notes", "")

            st.markdown(
                f"""
                <div style="border: 1px solid #333333; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
                    <div style="font-weight: bold; font-size: 1.0rem;">{b_name}</div>
                    <div style="font-size: 0.85rem; opacity: 0.8; margin-top: 4px;">
                        ROASTERY: {b_shop} ｜ ROAST: {b_roast}
                    </div>
                    {f'<div style="font-size: 0.8rem; opacity: 0.6; margin-top: 2px;">{b_notes}</div>' if b_notes else ''}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("NO BEANS REGISTERED YET.")