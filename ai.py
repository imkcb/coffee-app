import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from prompts import SYSTEM_INSTRUCTION

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=API_KEY) if API_KEY else None

class RecipeStep(BaseModel):
    step_number: int = Field(description="ステップ番号 (1, 2, 3...)")
    time_target: str = Field(description="開始・経過時間 (例: '0:00〜0:35')")
    step_water: int = Field(description="このステップで注ぐ湯量 (ml/g)")
    total_water: int = Field(description="このステップ終了時点の累計湯量 (ml/g)")
    flow_rate: str = Field(description="流量 (例: '細湯 (約3〜4g/s)', '中湯 (約6〜8g/s)', '太湯 (約10g/s〜)')")
    pouring_method: str = Field(description="注ぎ方 (例: '中心から外側へ円を描く', '中心部のみに一点注ぎ')")
    purpose: str = Field(description="ステップの目的 (例: 'ガス抜き・粉の湿潤', '酸味と甘みの抽出', '濃度調整')")

class CoffeeRecipe(BaseModel):
    selected_dripper: str = Field(description="推奨ドリッパー")
    selected_filter: str = Field(description="推奨ペーパーフィルター")
    selected_grinder: str = Field(description="使用ミル・グラインダー")
    recommended_powder_weight: float = Field(description="推奨粉量 (g)")
    water_temp: int = Field(description="湯温 (℃)")
    bloom_time: int = Field(description="蒸らし時間 (秒)")
    grind_setting: str = Field(description="グラインド設定")
    recipe_steps: list[RecipeStep] = Field(description="ステップごとの抽出表")
    tasting_notes: str = Field(description="ワンポイント解説")

def generate_recipe(prompt: str):
    """複数モデル順次切替による自動フォールバック制御付きレシピ生成"""
    if not ai_client:
        return None, "GEMINI_API_KEY が設定されていません。"

    candidate_models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
    ]

    last_error = None
    for model_name in candidate_models:
        for attempt in range(2):
            try:
                response = ai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=CoffeeRecipe,
                        temperature=0.1
                    )
                )
                return json.loads(response.text), None
            except Exception as e:
                last_error = str(e)
                time.sleep(1)

    return None, last_error