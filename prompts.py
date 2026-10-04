# SYSTEM INSTRUCTION（AIの役割を「パラメータチューナー」に限定）
SYSTEM_INSTRUCTION = (
    "あなたは世界標準のスペシャルティ抽出理論に基づき、コーヒー抽出パラメータを微調整する専門のチューナーです。"
    "提示された物理的な基本レシピ（ホット/急冷式アイスの固定計算値）を骨組みとし、"
    "豆の条件や過去のフィードバックに基づいて可変パラメータ（湯温・挽き目・粉量・蒸らし時間）のみを適切に微調整してください。"
    "各抽出ステップ（recipe_steps）は、指定された表形式（時間・注ぐ量・累計量・流量・注ぎ方・目的）に従い、言葉の表記揺れなく具体的に出力してください。"
    "使用する器具（ドリッパー、ペーパーフィルター、ミル等）は手持ちの器具リストの中から網羅的に指定してください。"
    "回答は常に日本語で行ってください。"
)

# 味の気になった点（選択肢）
TASTE_ISSUES_OPTIONS = [
    "問題なし（バランス良好）",
    "苦味・えぐみが強い（抽出が強すぎる）",
    "酸味が尖っている / 味が浅い（抽出が足りない）",
    "全体的に濃すぎる",
    "全体的に薄い / 水っぽい"
]

# 次回どうしたいか（選択肢）
TARGET_GOALS_OPTIONS = [
    "現状維持",
    "苦味を抑えたい",
    "酸味を抑えたい",
    "コク・甘みを強めたい",
    "すっきりさせたい"
]

def build_drip_prompt(
    chosen_bean: dict, 
    roast_date_str: str, 
    flavor_profile: str, 
    cup_count: int, 
    equipment_data: list, 
    past_feedback_text: str,
    coffee_type: str = "ホット",
    water_per_cup: int = 300
) -> str:
    """
    設定値（ホット/アイス、1杯あたりの抽出量）に基づく物理的固定値プロンプト生成
    """
    total_target_ml = water_per_cup * cup_count
    
    if coffee_type == "アイス":
        drip_water = int(total_target_ml * 0.6)
        ice_amount = total_target_ml - drip_water
        total_powder_base = round(total_target_ml / 15.8, 1)
        bloom_water_base = int(total_powder_base * 2.5)
        
        type_instruction = (
            f"【物理的ベースレシピ（急冷式アイスコーヒートレンド固定値）】\n"
            f"- 抽出タイプ: アイスコーヒー（急冷式）\n"
            f"- 杯数: {cup_count}杯\n"
            f"- 目標完成量: {total_target_ml}ml （1杯当たり{water_per_cup}ml）\n"
            f"- サーバー内にあらかじめセットする氷の量: 約{ice_amount}g\n"
            f"- ドリップに使用する総お湯量: {drip_water}ml\n"
            f"- 基準粉量: {total_powder_base}g\n"
            f"- 基準湯温: 94℃\n"
            f"- 基準蒸らし: 湯量{bloom_water_base}ml / 時間40秒\n"
            f"- 注ぎ構造: 蒸らし ＋ 2〜3回の分割注ぎ（短時間で濃く抽出）\n"
        )
    else:
        drip_water = total_target_ml
        total_powder_base = round(total_target_ml / 15.8, 1)
        bloom_water_base = int(total_powder_base * 3.15)
        
        type_instruction = (
            f"【物理的ベースレシピ（ホットコーヒー世界標準トレンド固定値）】\n"
            f"- 抽出タイプ: ホットコーヒー\n"
            f"- 杯数: {cup_count}杯\n"
            f"- 基準総湯量: {drip_water}ml （1杯当たり{water_per_cup}ml）\n"
            f"- 基準粉量: {total_powder_base}g （Brew Ratio 約1:15.8）\n"
            f"- 基準湯温: 92℃\n"
            f"- 基準蒸らし: 湯量{bloom_water_base}ml / 時間35秒\n"
            f"- 注ぎ構造: ブルーム（蒸らし）＋3回分割注ぎ（計4ステップ、目標抽出時間 2:30〜3:00）\n"
        )

    return (
        f"{type_instruction}"
        f"- 手持ちの器具一覧: {equipment_data}\n\n"
        f"【入力条件（可変要因）】\n"
        f"- 豆情報: {chosen_bean}\n"
        f"- 焙煎日: {roast_date_str}\n"
        f"- 希望する味の方向性: {flavor_profile}\n"
        f"- 前回の抽出フィードバック: {past_feedback_text}\n\n"
        f"【AIへの調整指示ルール】\n"
        f"上記の『物理的ベースレシピ』を厳格に維持した上で可変パラメータのみを補正してください。\n"
        f"1. 手持ち器具の中から「ドリッパー」「ペーパーフィルター」「ミル」をそれぞれ1つずつ選定して明記\n"
        f"2. 各抽出ステップ（recipe_steps）は以下の表記ルールを厳密に守って出力すること：\n"
        f"   - 流量の表記表現: 「細湯 (約3〜4g/s)」「中湯 (約6〜8g/s)」「太湯 (約10g/s〜)」「点滴」のいずれかを選択\n"
        f"   - 注ぎ方の表記表現: 「中心から外側へ円を描く」「中心部のみに一点注ぎ」「全体へ均一に回し注ぐ」のいずれかをベースに記述\n"
        f"   - 目的の表記表現: 「ガス抜き・粉の湿潤」「酸味とフレーバーの抽出」「甘みとボディ感の補強」「濃度調整・余分な渋みの抑制」等を明記"
    )