import os
import json
import requests
import streamlit as st

# APIが返却すべきJSON構造を厳格に固定するスキーマ定義
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recipe_title": {"type": "STRING", "description": "レシピのタイトル（日本語）"},
        "dripper": {"type": "STRING", "description": "使用するドリッパー名（登録器具から選択）"},
        "filter": {"type": "STRING", "description": "使用するフィルター名（登録器具から選択）"},
        "grinder": {"type": "STRING", "description": "使用するミル・グラインダー名（登録器具から選択）"},
        "coffee_amount": {"type": "STRING", "description": "推奨粉量（例: 18.5g）"},
        "water_temp": {"type": "STRING", "description": "お湯の温度（例: 90°C）"},
        "ice_amount": {"type": "STRING", "description": "アイス抽出時にサーバーへ事前に用意する氷の量（例: 100g、ホットの場合は None または なし）"},
        "grind_setting": {"type": "STRING", "description": "ミルのグラインド設定（例: 23 Clicks (中細挽き)）"},
        "bloom_time": {"type": "STRING", "description": "蒸らし時間（例: 45 sec）"},
        "recipe_steps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "step_number": {"type": "INTEGER", "description": "ステップ番号"},
                    "time": {"type": "STRING", "description": "そのステップが完了するタイマーの累計目標時刻（例: STEP1の蒸らし完了なら 0:45）"},
                    "pour_amount": {"type": "STRING", "description": "注ぎ量（例: 50ml）"},
                    "total_amount": {"type": "STRING", "description": "累計湯量（例: 50ml）"},
                    "flow_rate": {"type": "STRING", "description": "湯量・流量指示（例: 約5ml/s）"},
                    "pouring_method": {"type": "STRING", "description": "注ぎ方（日本語）"},
                    "purpose": {"type": "STRING", "description": "目的（日本語）"}
                },
                "required": ["step_number", "time", "pour_amount", "total_amount", "flow_rate", "pouring_method", "purpose"]
            }
        },
        "notes": {"type": "STRING", "description": "ワンポイント解説（日本語）"}
    },
    "required": ["recipe_title", "dripper", "filter", "grinder", "coffee_amount", "water_temp", "ice_amount", "grind_setting", "bloom_time", "recipe_steps", "notes"]
}

def get_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    return api_key

def generate_recipe_with_gemini(target_bean, coffee_type, water_ml, flavor_profile, roast_date_str="NULL", available_gears=None):
    api_key = get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY が環境変数または .streamlit/secrets.toml に設定されていません。")

    # 所有器具リストの整形（コンテキスト完全保持）
    gears_text = "No specific equipment registered in DB. Use standard barista equipment."
    if available_gears:
        gear_lines = []
        for g in available_gears:
            name = g.get("name") or g.get("item_name") or g.get("title") or "Unknown"
            cat = g.get("category") or g.get("type") or "Equipment"
            gear_lines.append(f"- [{cat}] {name}")
        gears_text = "\n".join(gear_lines)

    # プロンプトの構成
    prompt_text = f"""
    You are a world-class professional barista.
    Generate an optimal, precise drip coffee brewing recipe based on the following specifications and available equipment.

    [Target Coffee Bean]
    - Name: {target_bean.get('name', 'Custom Bean')}
    - Roast Level: {target_bean.get('roast_level', 'Medium')}
    - Origin / Profile: {target_bean.get('origin', '')} {target_bean.get('flavor_profile', '')}
    - Roastery: {target_bean.get('roastery', 'N/A')}
    - Roast Date: {roast_date_str}

    [Brewing Parameters]
    - Type: {coffee_type}
    - Total Water Volume: {water_ml} ml
    - Desired Flavor Profile: {flavor_profile}

    [Available Equipment / Gear Registered in DB]
    {gears_text}

    [OUTPUT REQUIREMENTS & STRICT RULES]
    1. CRITICAL: You MUST select drippers, filters, and grinders STRICTLY from the provided [Available Equipment / Gear Registered in DB] list above whenever applicable. Do NOT suggest equipment that the user does not own.
    2. CRITICAL TIMING RULE: For `time` in each step of `recipe_steps`, output the CUMULATIVE TARGET COMPLETION TIME on the timer when that step finishes. (e.g., If Step 1 is blooming from 0:00 to 0:45, `time` MUST be "0:45", NOT "0:00"). Do NOT output start times.
    3. Explanatory and commentary text fields (`recipe_title`, `notes`, `purpose`, `pouring_method`, `flow_rate`) MUST be generated in Japanese (日本語).
    4. Technical specifications (gear names, numerical values, temperatures, times) should use standard English/numerical units.
    """

    # 動的モデル探査（指示固定ルール）
    usable_models = []
    for api_version in ["v1beta", "v1"]:
        list_url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={api_key}"
        try:
            res = requests.get(list_url, timeout=5)
            if res.status_code == 200:
                for m in res.json().get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        m_name = m.get("name", "").replace("models/", "")
                        if m_name:
                            if "flash" in m_name:
                                usable_models.insert(0, (api_version, m_name))
                            else:
                                usable_models.append((api_version, m_name))
        except Exception:
            pass

    if not usable_models:
        usable_models = [
            ("v1beta", "gemini-1.5-flash"),
            ("v1", "gemini-1.5-flash")
        ]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "response_schema": RESPONSE_SCHEMA
        }
    }

    last_error = ""
    for api_version, model in usable_models:
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    text_content = candidates[0]["content"]["parts"][0]["text"]
                    recipe_data = json.loads(text_content)
                    return recipe_data
            else:
                last_error = f"[{model}] ({response.status_code}): {response.text}"
        except Exception as e:
            last_error = f"[{model}] {str(e)}"

    raise RuntimeError(f"モデル接続エラー: {last_error}")