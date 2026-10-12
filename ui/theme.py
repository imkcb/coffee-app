import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
    /* 1. 極太ピクセルフォント (Press Start 2P) & 日本語ドットフォント (DotGothic16) インポート */
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&family=Press+Start+2P&display=swap');

    :root {
        --bg-color: #0d0d0d;
        --card-bg: #1a1a1a;
        --accent-color: #00E65C;
        --text-color: #f0f0f0;
        --subtext-color: #a0a0a0;
        --border-color: #2a2a2a;
    }

    /* 2. POTLOG (最上部大見出し) : 極太ビットフォント・文字色 白 */
    .app-title {
        font-family: 'Press Start 2P', monospace !important;
        font-size: 2.0rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: 2px !important;
        margin-top: 10px !important;
        margin-bottom: 16px !important;
    }

    /* 3. 中見出し (SETUP, LIST, ADD BEAN 等) : 極太ビットフォント・文字色 白 */
    .pixel-header {
        font-family: 'Press Start 2P', monospace !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-top: 12px !important;
        margin-bottom: 8px !important;
        letter-spacing: 1px !important;
    }

    /* 4. セクション区切り線 (余白の統一・圧縮) */
    .section-divider {
        margin-top: 16px !important;
        margin-bottom: 8px !important;
        border: none !important;
        border-top: 1px solid var(--border-color) !important;
    }

    /* 5. DRIPタブ レシピタイトル : 日本語対応ドットフォント (DotGothic16)・ネオングリーン */
    .recipe-title {
        font-family: 'DotGothic16', 'Press Start 2P', monospace !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: var(--accent-color) !important;
        margin-top: 12px !important;
        margin-bottom: 16px !important;
        line-height: 1.5 !important;
    }

    /* 6. レシピ各ステップ (STEP 1等) : 通常フォント */
    .step-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: var(--accent-color) !important;
        margin-bottom: 6px !important;
    }

    /* 7. 小見出し (1. ROASTERY, FEELING 等) : 通常フォント */
    .sub-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 1.0rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin-top: 12px !important;
        margin-bottom: 6px !important;
    }

    /* 8. 全プライマリボタン (ネオングリーン背景 ＋ 黒文字 #121212 / 外光なし) */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"],
    div.stFormSubmitButton > button,
    button[data-testid="baseButton-primary"] {
        background-color: var(--accent-color) !important;
        color: #121212 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
    }

    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #00e65c !important;
        color: #121212 !important;
        box-shadow: none !important;
        transform: translateY(-1px);
    }

    /* 9. セカンダリボタン (RESET, EDIT, DELETE など / 外光なし) */
    div.stButton > button[kind="secondary"],
    div.stButton > button:not([kind="primary"]) {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button:not([kind="primary"]):hover {
        border-color: var(--accent-color) !important;
        color: var(--accent-color) !important;
        box-shadow: none !important;
        transform: translateY(-1px);
    }

    /* 10. st.pills (選択肢ボタン / 外光なし) */
    div[data-testid="stPills"] button {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        transition: all 0.2s ease-in-out !important;
        border-radius: 20px !important;
    }

    div[data-testid="stPills"] button[aria-selected="false"]:hover,
    div[data-testid="stPills"] button:not([aria-selected="true"]):hover {
        border-color: var(--accent-color) !important;
        color: var(--accent-color) !important;
        box-shadow: none !important;
        transform: translateY(-1px);
    }

    div[data-testid="stPills"] button[aria-selected="true"] {
        background-color: var(--accent-color) !important;
        color: #121212 !important;
        font-weight: 700 !important;
    }

    /* 11. Number Input (+ - ボタン) */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        font-weight: 300 !important;
        font-size: 14px !important;
        background-color: transparent !important;
        border: none !important;
        transition: color 0.15s ease, text-shadow 0.15s ease !important;
    }

    button[data-testid="stNumberInputStepDown"]:hover,
    button[data-testid="stNumberInputStepUp"]:hover {
        color: var(--accent-color) !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    button[data-testid="stNumberInputStepDown"]:active,
    button[data-testid="stNumberInputStepUp"]:active {
        color: var(--accent-color) !important;
        background-color: transparent !important;
        text-shadow: none !important;
    }

    button[data-testid="stNumberInputStepDown"]:focus,
    button[data-testid="stNumberInputStepUp"]:focus {
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* 12. メトリクスカード (SPEC) */
    .spec-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }

    .spec-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
    }

    .spec-label {
        font-size: 0.75rem;
        color: var(--subtext-color);
        font-weight: 600;
        margin-bottom: 4px;
    }

    .spec-value {
        font-size: 1.1rem;
        color: var(--text-color);
        font-weight: 700;
    }

    /* 13. STEPS カード */
    .step-card {
        background-color: var(--card-bg);
        border-left: 3px solid var(--accent-color);
        border-radius: 4px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }

    .step-purpose {
        font-size: 0.95rem;
        color: var(--text-color);
        margin-bottom: 6px;
        line-height: 1.4;
    }

    .step-time {
        font-size: 0.85rem;
        color: var(--subtext-color);
        margin-bottom: 6px;
    }

    .step-meta {
        font-size: 0.8rem;
        color: var(--subtext-color);
    }

    .step-meta-highlight {
        color: var(--text-color);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)