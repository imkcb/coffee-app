import streamlit as st
import os

def render():
    st.markdown("### SYSTEM")

    st.markdown("#### THEME")
    current_theme = st.session_state.get("theme_mode", "DARK")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("DARK", use_container_width=True, type="primary" if current_theme == "DARK" else "secondary"):
            st.session_state["theme_mode"] = "DARK"
            st.rerun()
    with col2:
        if st.button("LIGHT", use_container_width=True, type="primary" if current_theme == "LIGHT" else "secondary"):
            st.session_state["theme_mode"] = "LIGHT"
            st.rerun()
    with col3:
        if st.button("SYSTEM", use_container_width=True, type="primary" if current_theme == "SYSTEM" else "secondary"):
            st.session_state["theme_mode"] = "SYSTEM"
            st.rerun()

    st.divider()
    st.markdown("#### INFO")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("APP VERSION", "v2.1.0")
        st.metric("ENGINE", "GEMINI API")
    with c2:
        supabase_status = "CONNECTED" if os.getenv("SUPABASE_URL") else "NOT CONFIGURED"
        st.metric("DATABASE", supabase_status)
        st.metric("ENVIRONMENT", "PRODUCTION")