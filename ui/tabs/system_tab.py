import streamlit as st

def render():
    # 中見出し (INFO)
    st.markdown('<div class="pixel-header">INFO</div>', unsafe_allow_html=True)
    
    st.markdown(
        f'<div style="font-size: 0.95rem; line-height: 1.8; color: var(--text-color); margin-bottom: 20px;">'
        f'• APP: POTLOG<br>'
        f'• VERSION: 1.0.0<br>'
        f'• STACK: Streamlit / Supabase / Gemini API<br>'
        f'• STATUS: ACTIVE'
        f'</div>',
        unsafe_allow_html=True
    )