import os
import requests
import json

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    # 1. APIキーで利用可能なモデル一覧を自動検出する
    usable_models = []
    for api_version in ["v1beta", "v1"]:
        list_url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={api_key}"
        try:
            res = requests.get(list_url, timeout=10)
            if res.status_code == 200:
                models_data = res.json().get("models", [])
                for m in models_data:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        model_name = m.get("name", "").replace("models/", "")
                        if model_name and (api_version, model_name) not in usable_models:
                            usable_models.append((api_version, model_name))
        except Exception:
            pass

    # 2. 自動検出できなかった場合のバックアップ候補
    if not usable_models:
        usable_models = [
            ("v1beta", "gemini-2.0-flash"),
            ("v1beta", "gemini-1.5-flash"),
            ("v1", "gemini-1.5-flash"),
            ("v1", "gemini-1.0-pro")
        ]

    # 3. 利用可能なモデルで順次レシピ生成を実行
    last_error = ""
    for api_version, model in usable_models:
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
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
                last_error = f"[{api_version}/{model}] Error ({response.status_code}): {response.text}"
        except Exception as e:
            last_error = f"[{api_version}/{model}] Exception: {str(e)}"

    return None, f"すべての自動検出モデルでエラーが発生しました: {last_error}"