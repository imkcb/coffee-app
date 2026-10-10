TASTE_ISSUES_OPTIONS = [
    "問題なし（バランス良好）",
    "前半の酸味が強すぎる・すっぱい",
    "後半の苦味・えぐみが重い",
    "全体的に薄い・水っぽい（抽出不足）",
    "過抽出で後味に強い渋みが残る",
    "フレーバーが立ちにくい・ボヤけている",
    "お湯の落ちきりが遅い（目詰まり）",
    "お湯の落ちきりが速すぎる"
]

TARGET_GOALS_OPTIONS = [
    "現状維持",
    "酸味を抑えて甘みを引き出したい",
    "フレーバー（華やかさ）をより際立たせたい",
    "ボディ感（コク）を補強したい",
    "渋みを減らしてクリーンな後味にしたい",
    "挽き目・湯温・注ぎスピードの再調整"
]

def build_drip_prompt(chosen_bean, roast_date_str, flavor_profile, cup_count, equipment_data, past_feedback_text, coffee_type="ホット", water_per_cup=300):
    total_target_volume = water_per_cup * cup_count
    
    if coffee_type == "アイス":
        ice_gram = int(total_target_volume * 0.4)
        water_ml = int(total_target_volume * 0.6)
        type_instruction = f"""
【アイスコーヒー（急冷式）の重要指示】
- 完成目標量は {total_target_volume}ml（{water_per_cup}ml × {cup_count}杯）です。
- 急冷式のため、注ぐお湯の総量は目標量の約60%（約{water_ml}ml）にし、残りの約40%（約{ice_gram}g）はサーバーにあらかじめセットする「氷」として計算してください。
- 抽出ステップ（recipe_steps）の最終累計湯量は、お湯の総量（約{water_ml}ml）で終わるように設定してください。
- `ice_amount` フィールドには「氷 {ice_gram}g（サーバーに事前投入）」と記載してください。
"""
    else:
        type_instruction = f"""
【ホットコーヒーの指示】
- 注ぐお湯の総量は {total_target_volume}ml（{water_per_cup}ml × {cup_count}杯）ぴったりにしてください。
- `ice_amount` フィールドには「なし」と記載してください。
"""

    prompt = f"""
あなたは世界最高峰のバリスタです。以下の条件に基づき、最高のドリップレシピを作成してください。

{type_instruction}

【豆情報】
{chosen_bean}

【焙煎日】
{roast_date_str}

【希望する味の方向性】
{flavor_profile}

【使用可能な器具一覧】
{equipment_data}

【前回の抽出フィードバック】
{past_feedback_text}
"""
    return prompt