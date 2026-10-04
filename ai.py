import os
import requests
import json

def generate_recipe(prompt_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY が設定されていません。"

    # 1. APIキーで現在利用可能なモデル一覧を自動検索
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
                            # 処理の早いflashモデルを優先配置
                            if "flash" in m_name:
                                usable_models.insert(0, (api_version, m_name))
                            else:
                                usable_models.append((api_version, m_name))
        except Exception:
            pass

    # 自動取得に失敗した場合のバックアップ
    if not usable_models:
        usable_models = [
            ("v1beta", "gemini-1.5-flash"),
            ("v1", "gemini-1.5-flash")
        ]

    # 2. 検出された有効なモデルでレシピ生成を実行
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
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