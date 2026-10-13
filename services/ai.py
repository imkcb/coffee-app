import os
import json
import requests
import streamlit as st

# --- 1. 固定パラメータ (システムプロンプト & 最新世界トレンドルール) ---
SYSTEM_PROMPT = """
あなたは世界最高峰のスペシャルティコーヒーバリスタです。
最新の海外競技会トレンド（WBC / WBrC）に基づき、科学的かつ再現性の高いドリップレシピを生成してください。

【重要：言語指定】
生成するJSON内のすべての文字列（レシピ名、解説、目的、注水方法、流速、挽き目など）は、必ず自然な「日本語」で出力してください。

【1. 最新海外トレンド抽出原則】
- Bloom (蒸らし): 粉量の2.5〜3.0倍のお湯を使い、やや高めの位置から注いで粉全体に均一なアジテーション（撹拌）を与える。
- Extraction Dynamics (抽出展開):
  ・前半（1〜2投目）: フレーバーと明瞭な酸味を高濃度で抽出するため、適度な流速で注ぐ。
  ・後半（3投目以降）: 微粉の目詰まりと過抽出（渋み・雑味）を防ぐため、低い位置から静かに注ぐ。
- Ratio & Temperature:
  ・HOT: 基本粉湯比率は 1:15〜1:16.5。浅煎りは高湯温(90-94℃)、深煎りは低湯温(82-86℃)。
  ・ICE: 抽出液を濃縮するため 1:9〜1:10 で抽出させ、残りを氷で急冷・希釈する。

【2. FEEDBACK履歴（過去の抽出評価トレンド）に基づく可変アジャストルール】
提示された FEEDBACK HISTORY（最大5件の時系列評価）を読み解き、特に直近の改善トレンドおよび継続的な課題を考慮してレシピを最適化してください：
- FEELING（課題）への対応:
  ・「渋み・雑味」: 湯温を1〜2℃下げる、挽き目を1刻み粗くする、または後半の注水を抑える。
  ・「水っぽさ」: 粉湯比率を高濃度にし（お湯を減らす）、蒸らし時間または前半のアジテーションを強める。
  ・「重さ・濁り」: 挽き目を粗くし、注水回数を減らして流速を上げる。
- NEXT（目標）への対応:
  ・「コク・ボディ」: 湯温を1℃上げ、中盤の注水を細かく分ける。
  ・「酸味・キレ」: 湯温を維持しつつ前半の注水比率を増やす。
  ・「雑味オフ」: 後半の注水を中央一点の静かな注水に変更する。
※複数件の履歴がある場合、最新の評価を最も重視しつつ、過去に解決された課題が再発しないようバランスを取ること。

【3. 絶対制約事項】
- 使用機材（ドリッパー、ミル、フィルター）は、必ず提供された `available_gears`（ON状態の機材）の中から最も相性の良いものを1点ずつ選定すること。
- レシピステップ（recipe_steps）の `time` 表示は、そのステップが完了する目標経過時間（例: "0:45", "1:30", "2:30"）を記載すること。
- 出力は必ず日本語で行うこと。
"""

# JSON出力構造の標準定義
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recipe_title": {"type": "STRING"},
        "notes": {"type": "STRING"},
        "dripper": {"type": "STRING"},
        "filter": {"type": "STRING"},
        "grinder": {"type": "STRING"},
        "coffee_amount": {"type": "STRING"},
        "grind_setting": {"type": "STRING"},
        "water_temp": {"type": "STRING"},
        "bloom_time": {"type": "STRING"},
        "ice_amount": {"type": "STRING"},
        "recipe_steps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "step_number": {"type": "INTEGER"},
                    "purpose": {"type": "STRING"},
                    "time": {"type": "STRING"},
                    "pour_amount": {"type": "STRING"},
                    "total_amount": {"type": "STRING"},
                    "pouring_method": {"type": "STRING"},
                    "flow_rate": {"type": "STRING"}
                },
                "required": ["step_number", "purpose", "time", "pour_amount", "total_amount", "pouring_method", "flow_rate"]
            }
        }
    },
    "required": ["recipe_title", "notes", "dripper", "filter", "grinder", "coffee_amount", "grind_setting", "water_temp", "bloom_time", "recipe_steps"]
}

def _get_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
    return api_key

def generate_recipe_with_gemini(
    target_bean: dict,
    coffee_type: str,
    water_ml: int,
    flavor_profile: str,
    roast_date_str: str,
    available_gears: list,
    recent_feedbacks: list = None
) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。")

    # --- REST APIによる動的モデル探査 ---
    usable_models = []
    for api_version in ["v1beta", "v1"]:
        list_url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={api_key}"
        try:
            res = requests.get(list_url, timeout=5)
            if res.status_code == 200:
                for m in res.json().get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_name = m.get("name", "").replace("models/", "")
                        if m_name:
                            if "flash" in m_name:
                                usable_models.insert(0, (api_version, m_name))
                            else:
                                usable_models.append((api_version, m_name))
        except Exception:
            pass

    if not usable_models:
        usable_models = [("v1beta", "gemini-1.5-flash"), ("v1", "gemini-1.5-flash")]

    # --- 器具情報整形 ---
    gears_info = []
    for g in available_gears:
        gears_info.append(f"- [{g.get('type')}] {g.get('name')} (ブランド: {g.get('brand', '-')})")
    gears_str = "\n".join(gears_info) if gears_info else "特になし（標準機材で構成してください）"

    # --- SETUP 情報 ---
    setup_str = f"""
- 豆名: {target_bean.get('name', 'カスタムビーン')}
- 焙煎所: {target_bean.get('roastery', '-')}
- 産地: {target_bean.get('origin', '-')}
- 焙煎度: {target_bean.get('roast_level', 'MEDIUM')}
- プロセス: {target_bean.get('process', '-')}
- フレーバーノート: {target_bean.get('flavor_notes', '-')}
- 抽出タイプ: {coffee_type}
- 総湯量: {water_ml}ml
- 目標フレーバー傾向: {flavor_profile}
- 焙煎日: {roast_date_str}
"""

    # --- FEEDBACK 履歴整形 ---
    if recent_feedbacks:
        fb_lines = []
        for idx, fb in enumerate(recent_feedbacks, 1):
            data_obj = fb.get("data", {})
            created_at = fb.get("created_at", "")[:10] if fb.get("created_at") else f"ログ #{idx}"
            issues = ", ".join(data_obj.get("issues", [])) or "なし"
            improvements = ", ".join(data_obj.get("improvements", [])) or "なし"
            memo = data_obj.get("memo", "")
            
            line = (
                f"[{idx}] {created_at} | ★{data_obj.get('rating', '-')}"
                f" | 酸味:{data_obj.get('acidity', '-')} 苦味:{data_obj.get('bitterness', '-')} ボディ:{data_obj.get('body', '-')}"
                f" | 課題:{issues} | 目標:{improvements}"
            )
            if memo:
                line += f" | 注記:{memo}"
            fb_lines.append(line)
        feedback_str = "\n".join(fb_lines)
    else:
        feedback_str = "過去のフィードバックデータなし（初抽出のためトレンド標準で作成）"

    prompt_text = f"""
{SYSTEM_PROMPT}

以下の条件・データを掛け合わせ、最高の一杯となるハンドドリップレシピを日本語で生成してください。

【2. 所有器具情報 (available_gears)】
{gears_str}

【3. SET UP 情報】
{setup_str}

【4. 直近の FEEDBACK 履歴 (最新最大5件の時系列評価)】
{feedback_str}
"""

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
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    text_content = candidates[0]["content"]["parts"][0]["text"]
                    return json.loads(text_content)
            else:
                last_error = f"[{model}] ({response.status_code}): {response.text}"
        except Exception as e:
            last_error = f"[{model}] {str(e)}"

    raise RuntimeError(f"API通信エラー: {last_error}")