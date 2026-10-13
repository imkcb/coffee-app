import os
import json
from google import genai
from google.genai import types

# --- 1. 固定パラメータ (システムプロンプト & 最新世界トレンドルール) ---
SYSTEM_PROMPT = """
あなたは世界最高峰のスペシャルティコーヒーバリスタです。
最新の海外競技会トレンド（WBC / WBrC）に基づき、科学的かつ再現性の高いドリップレシピを生成してください。

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

【4. 出力フォーマット (JSON)】
必ず以下のJSON構造のみで出力してください。余計なテキストは含めないでください。

{
  "recipe_title": "文字列 (例: MODERN HIGH-EXTRACTION DRIP)",
  "notes": "文字列 (抽出コンセプトや過去フィードバックの反映点を簡潔に説明)",
  "dripper": "文字列 (選定されたドリッパー名)",
  "filter": "文字列 (選定されたフィルター名)",
  "grinder": "文字列 (選定されたグラインダー名)",
  "coffee_amount": "文字列 (例: 18g)",
  "grind_setting": "文字列 (例: Comandante 22 clicks / Medium-Fine)",
  "water_temp": "文字列 (例: 92°C)",
  "bloom_time": "文字列 (例: 45s)",
  "ice_amount": "文字列 (ICE時のみ使用。例: 120g / HOT時は None)",
  "recipe_steps": [
    {
      "step_number": 1,
      "purpose": "文字列 (例: Bloom & High Agitation)",
      "time": "文字列 (例: 0:45)",
      "pour_amount": "文字列 (例: 50ml)",
      "total_amount": "文字列 (例: 50ml)",
      "pouring_method": "文字列 (例: High pour center to edge)",
      "flow_rate": "文字列 (例: Medium-Fast)"
    }
  ]
}
"""


def generate_recipe_with_gemini(
    target_bean: dict,
    coffee_type: str,
    water_ml: int,
    flavor_profile: str,
    roast_date_str: str,
    available_gears: list,
    recent_feedbacks: list = None
) -> dict:
    """
    固定パラメータ(WBCトレンド)と可変パラメータ(機材、SETUP、直近最大5件のFEEDBACK履歴)を結合してレシピを生成
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)

    target_model = "gemini-2.5-flash"
    try:
        models = client.models.list()
        available_names = [m.name for m in models]
        for name in available_names:
            if "gemini-2.5-flash" in name:
                target_model = name
                break
            elif "gemini-1.5-flash" in name:
                target_model = name
    except Exception:
        pass

    # --- 2. 器具情報のフォーマット ---
    gears_info = []
    for g in available_gears:
        gears_info.append(f"- [{g.get('type')}] {g.get('name')} (Brand: {g.get('brand', '-')})")
    gears_str = "\n".join(gears_info) if gears_info else "特になし（標準機材で構成してください）"

    # --- 3. SET UP 情報 ---
    setup_str = f"""
- 豆名: {target_bean.get('name', 'Custom Bean')}
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

    # --- 4. FEEDBACK 履歴（最大5件）を軽量フォーマット化 ---
    if recent_feedbacks:
        fb_lines = []
        for idx, fb in enumerate(recent_feedbacks, 1):
            data_obj = fb.get("data", {})
            created_at = fb.get("created_at", "")[:10] if fb.get("created_at") else f"Log #{idx}"
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

    user_prompt = f"""
以下の条件・データを掛け合わせ、最高の一杯となるハンドドリップレシピを生成してください。

【2. 所有器具情報 (available_gears)】
{gears_str}

【3. SET UP 情報】
{setup_str}

【4. 直近の FEEDBACK 履歴 (最新最大5件の時系列評価)】
{feedback_str}
"""

    response = client.models.generate_content(
        model=target_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)