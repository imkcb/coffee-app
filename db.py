import os
from supabase import create_client

# 接続クライアントを動的に取得する関数
def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

# 豆データの取得処理
def get_beans():
    try:
        supabase = get_client()  # 呼び出し時にクライアントを作成
        res = supabase.table("beans").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching beans: {e}")
        return []

# 器具データの取得処理
def get_equipment():
    try:
        supabase = get_client()
        res = supabase.table("equipment").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching equipment: {e}")
        return []

# 抽出履歴の取得処理
def get_drip_logs():
    try:
        supabase = get_client()
        res = supabase.table("drip_logs").select("*").order("created_at", ascending=False).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching drip logs: {e}")
        return []