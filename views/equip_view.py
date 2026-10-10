import streamlit as st
import db

def render():
    st.markdown('<div class="gear-tab-marker"></div>', unsafe_allow_html=True)
    st.markdown("### GEAR")

    st.markdown("#### ADD GEAR")
    with st.form("add_gear_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            gear_type = st.selectbox("GEAR TYPE", ["DRIPPER", "FILTER", "GRINDER", "KETTLE", "OTHER"])
            gear_name = st.text_input("GEAR NAME", placeholder="例: HARIO V60 01")
        with col2:
            brand = st.text_input("BRAND / MAKER", placeholder="例: HARIO")
            notes = st.text_input("NOTES", placeholder="例: 樹脂製・1~2人用（任意）")

        submitted = st.form_submit_button("REGISTER GEAR", type="primary", use_container_width=True)
        if submitted:
            if gear_name:
                try:
                    payload = {
                        "type": gear_type,
                        "name": gear_name,
                        "brand": brand,
                        "notes": notes,
                        "is_active": True
                    }
                    db.insert_equipment(payload)
                    st.success("GEAR REGISTERED!")
                    st.rerun()
                except Exception as e:
                    st.error(f"ERROR: {e}")
            else:
                st.warning("PLEASE INPUT GEAR NAME")

    st.divider()

    st.markdown("#### GEAR LIST")
    equipment_data = db.get_equipment()
    if equipment_data:
        sorted_gear = sorted(equipment_data, key=lambda x: (str(x.get("type", "")), str(x.get("name", ""))))
        for gear in sorted_gear:
            g_name = gear.get("name", "-")
            g_type = gear.get("type", "-")
            g_brand = gear.get("brand", "")
            g_notes = gear.get("notes", "")

            st.markdown(
                f"""
                <div style="border: 1px solid #333333; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
                    <div style="font-weight: bold; font-size: 1.0rem;">[{g_type}] {g_name}</div>
                    <div style="font-size: 0.85rem; opacity: 0.8; margin-top: 4px;">
                        BRAND: {g_brand if g_brand else '-'}
                    </div>
                    {f'<div style="font-size: 0.8rem; opacity: 0.6; margin-top: 2px;">{g_notes}</div>' if g_notes else ''}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("NO GEAR REGISTERED YET.")