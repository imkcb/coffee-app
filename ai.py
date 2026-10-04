import os
import requests
import json

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    # 高速かつ安定しているエンドポイントを直接指定
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                text_content = candidates[0]["content"]["parts"][0]["text"]
                recipe_data = json.loads(text_content)
                return recipe_data, None
        return None, f"API Error ({response.status_code}): {response.text}"
    except Exception as e:
        return None, f"通信エラー: {str(e)}"