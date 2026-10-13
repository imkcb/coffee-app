import os
from supabase import create_client, Client

# --- 1. Supabase クライアント初期化 (安全対策付き) ---
raw_url = os.environ.get("SUPABASE_URL", "")
# 前後の空白除去 ＆ 末尾スラッシュ(/)を強制排除してPGRST125エラーを防止
supabase_url = raw_url.strip().rstrip("/")
supabase_key = os.environ.get("SUPABASE_KEY", "").strip()

if not supabase_url or not supabase_key:
    supabase = None
else:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Supabase Client Initialization Error: {e}")
        supabase = None


# --- 2. BEANS (コーヒー豆) 操作 ---
def get_beans():
    if not supabase:
        return []
    try:
        res = supabase.table("beans").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching beans: {e}")
        return []

def add_bean(bean_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("beans").insert(bean_data).execute()
        return res.data
    except Exception as e:
        print(f"Error adding bean: {e}")
        return None

def update_bean(bean_id: str, bean_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("beans").update(bean_data).eq("id", bean_id).execute()
        return res.data
    except Exception as e:
        print(f"Error updating bean: {e}")
        return None

def delete_bean(bean_id: str):
    if not supabase:
        return False
    try:
        supabase.table("beans").delete().eq("id", bean_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting bean: {e}")
        return False


# --- 3. GEARS (抽出器具) 操作 ---
def get_gears():
    if not supabase:
        return []
    try:
        res = supabase.table("gears").select("*").order("type").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching gears: {e}")
        return []

def add_gear(gear_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("gears").insert(gear_data).execute()
        return res.data
    except Exception as e:
        print(f"Error adding gear: {e}")
        return None

def update_gear(gear_id: str, gear_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("gears").update(gear_data).eq("id", gear_id).execute()
        return res.data
    except Exception as e:
        print(f"Error updating gear: {e}")
        return None

def delete_gear(gear_id: str):
    if not supabase:
        return False
    try:
        supabase.table("gears").delete().eq("id", gear_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting gear: {e}")
        return False


# --- 4. DRIP LOGS (抽出記録・FEEDBACK) 操作 ---
def get_drip_logs():
    if not supabase:
        return []
    try:
        res = supabase.table("drip_logs").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching drip logs: {e}")
        return []

def add_drip_log(log_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("drip_logs").insert(log_data).execute()
        return res.data
    except Exception as e:
        print(f"Error adding drip log: {e}")
        return None

def delete_drip_log(log_id: str):
    if not supabase:
        return False
    try:
        supabase.table("drip_logs").delete().eq("id", log_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting drip log: {e}")
        return False