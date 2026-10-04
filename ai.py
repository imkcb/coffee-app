import os
import requests
import json

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    # 試行するモデルの候補リスト
    model_candidates = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash"
    ]

    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    last_error = ""

    for model in model_candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    text_content = candidates[0]["content"]["parts"][0]["text"]
                    recipe_data = json.loads(text_content)
                    return recipe_data, None
            else:
                last_error = f"{model} Error ({response.status_code}): {response.text}"
        except Exception as e:
            last_error = f"{model} Exception: {str(e)}"

    return None, f"すべてのモデル試行でエラーが発生しました: {last_error}"