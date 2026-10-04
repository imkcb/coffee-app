import os
import requests
import json

# APIが返却すべきJSON構造を厳格に固定するスキーマ定義
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recipe_title": {"type": "STRING", "description": "レシピのタイトル"},
        "dripper": {"type": "STRING", "description": "使用するドリッパー名"},
        "filter": {"type": "STRING", "description": "使用するフィルター名"},
        "grinder": {"type": "STRING", "description": "使用するミル・グラインダー名"},
        "coffee_amount": {"type": "STRING", "description": "推奨粉量（例: 19g）"},
        "water_temp": {"type": "STRING", "description": "お湯の温度（例: 94℃）"},
        "ice_amount": {"type": "STRING", "description": "アイス抽出時にサーバーへ事前に用意する氷の量（例: 120g、ホットの場合は なし）"},
        "grind_setting": {"type": "STRING", "description": "ミルのグラインド設定"},
        "bloom_time": {"type": "STRING", "description": "蒸らし時間（例: 0:00 - 0:40）"},
        "recipe_steps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "step_number": {"type": "INTEGER", "description": "ステップ番号"},
                    "time": {"type": "STRING", "description": "時間（例: 0:00 - 0:40）"},
                    "pour_amount": {"type": "STRING", "description": "注ぎ量（例: 47ml）"},
                    "total_amount": {"type": "STRING", "description": "累計湯量（例: 47ml）"},
                    "flow_rate": {"type": "STRING", "description": "湯量・流量指示"},
                    "pouring_method": {"type": "STRING", "description": "注ぎ方"},
                    "purpose": {"type": "STRING", "description": "目的"}
                },
                "required": ["step_number", "time", "pour_amount", "total_amount", "flow_rate", "pouring_method", "purpose"]
            }
        },
        "notes": {"type": "STRING", "description": "ワンポイント解説（急冷式の場合は氷で解凍して指定総量になる旨を記載）"}
    },
    "required": ["recipe_title", "dripper", "filter", "grinder", "coffee_amount", "water_temp", "ice_amount", "grind_setting", "bloom_time", "recipe_steps", "notes"]
}

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

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
                    return recipe_data, None
            else:
                last_error = f"[{model}] ({response.status_code}): {response.text}"
        except Exception as e:
            last_error = f"[{model}] {str(e)}"

    return None, f"モデル接続エラー: {last_error}"