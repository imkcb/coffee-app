import os
import requests
import json

def generate_recipe(prompt_text):
    """
    新形式のAPIキー（AQ.Ab8...）に対応した直接HTTP通信によるレシピ生成処理
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    # APIエンドポイントのURL（クエリパラメータで安全にキーを渡す）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
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

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            return None, f"API Error ({response.status_code}): {response.text}"
            
        res_json = response.json()
        candidates = res_json.get("candidates", [])
        if not candidates:
            return None, "AIからの応答が空でした。"
            
        text_content = candidates[0]["content"]["parts"][0]["text"]
        recipe_data = json.loads(text_content)
        return recipe_data, None

    except Exception as e:
        return None, f"通信エラー: {str(e)}"