import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

def get_beans():
    if not supabase: return []
    try:
        res = supabase.table("beans").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def insert_bean(data: dict):
    return supabase.table("beans").insert(data).execute()

def update_bean(bean_id: int, data: dict):
    return supabase.table("beans").update(data).eq("id", bean_id).execute()

def delete_bean(bean_id: int):
    return supabase.table("beans").delete().eq("id", bean_id).execute()

def get_equipment():
    if not supabase: return []
    try:
        res = supabase.table("equipment").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def insert_equipment(data: dict):
    # デフォルトで is_active = True をセット
    if "is_active" not in data:
        data["is_active"] = True
    return supabase.table("equipment").insert(data).execute()

def update_equipment(eq_id: int, data: dict):
    return supabase.table("equipment").update(data).eq("id", eq_id).execute()

def delete_equipment(eq_id: int):
    return supabase.table("equipment").delete().eq("id", eq_id).execute()

def get_drip_logs():
    if not supabase: return []
    try:
        res = supabase.table("drip_logs").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def insert_drip_log(data: dict):
    return supabase.table("drip_logs").insert(data).execute()

def update_drip_log(log_id: int, data: dict):
    return supabase.table("drip_logs").update(data).eq("id", log_id).execute()

def delete_drip_log(log_id: int):
    return supabase.table("drip_logs").delete().eq("id", log_id).execute()