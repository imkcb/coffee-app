RECIPE_PROMPT_TEMPLATE = """
以下の抽出条件に基づき、ハンドドリップコーヒーの最適な抽出レシピを生成してください。
返却は必ず以下のJSONフォーマットのキー名を寸分違わず使用し、純粋なJSONのみを出力してください。

【抽出条件】
- 対象の豆: {bean_name} ({bean_roast})
- 抽出タイプ: {coffee_type}
- 目標出来上がり量: {water_ml} ml
- 目指す味わい: {flavor_profile}
- 焙煎日: {roast_date_str}
- 使用可能ドリッパー: {available_drippers}
- 使用可能フィルター: {available_filters}
- 使用可能グラインダー: {available_grinders}
- 過去の抽出ログ参考:
{past_logs_summary}

【計算ルール】
- coffee_typeが「ICED」の場合、お湯と氷の割合を 60:40 とし、お湯の量={iced_water_ml}ml、氷の量={iced_ice_g}g と計算してください。
- STEP 1の手順説明(description)には、抽出を開始する前にあらかじめサーバー内に氷{iced_ice_g}gをセットしておく旨を明記してください。
- 使用可能器具（ドリッパー、フィルター、グラインダー）の中から、今回の豆と味わいに最も適した組み合わせを選び、gears_usedオブジェクトに含めてください。

【絶対遵守のJSON出力フォーマット例】
{{
  "recipe_title": "エチオピア ハンベラ バランスホットドリップ",
  "summary": "華やかな香りとクリーンな味わいを引き出すレシピです。",
  "coffee_g": 13,
  "water_temp": 90,
  "total_water_ml": {water_ml},
  "total_time": "2分30秒",
  "gears_used": {{
    "dripper": "ORIGAMI Dripper Air S",
    "filter": "アバカペーパーフィルター",
    "grind_size": "中細挽き",
    "grinder": "Comandante C40"
  }},
  "steps": [
    {{
      "step": 1,
      "title": "蒸らし",
      "water_amount": "40ml",
      "time": "0:00 - 0:45",
      "description": "全体に均一にお湯を注ぎ、45秒間蒸らします。"
    }},
    {{
      "step": 2,
      "title": "1回目注水",
      "water_amount": "80ml",
      "time": "0:45 - 1:15",
      "description": "中心から円を描くように優しく注ぎます。"
    }}
  ],
  "notes": "注湯は壁面に直接当てず粉の土手を中心に優しく撹拌するように注いでください。"
}}
"""