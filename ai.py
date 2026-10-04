import os
import requests
import json

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    # 2026年現在アクティブな最新モデル候補（タイムアウトを絞り高速切り替え）
    model_candidates = [
        ("v1beta", "gemini-2.5-flash"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1", "gemini-2.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest")
    ]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    last_error = ""
    for api_version, model in model_candidates:
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
        try:
            # タイムアウトを5秒に設定し、応答のないモデルは即座に次へ切替
            response = requests.post(url, headers=headers, json=payload, timeout=5)
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