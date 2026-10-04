import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

supabase: Client = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Supabase Client Init Error: {e}")

# ------------------------------------------
# 1. 豆 (beans) テーブル操作
# ------------------------------------------
def get_beans():
    if not supabase: return []
    try:
        response = supabase.table("beans").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching beans: {e}")
        return []

def insert_bean(bean_dict):
    if not supabase: return None
    try:
        response = supabase.table("beans").insert(bean_dict).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting bean: {e}")
        raise e

def update_bean(bean_id, update_dict):
    if not supabase: return None
    try:
        response = supabase.table("beans").update(update_dict).eq("id", bean_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating bean: {e}")
        raise e

def delete_bean(bean_id):
    if not supabase: return None
    try:
        response = supabase.table("beans").delete().eq("id", bean_id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting bean: {e}")
        raise e

# ------------------------------------------
# 2. 器具 (equipment) テーブル操作
# ------------------------------------------
def get_equipment():
    if not supabase: return []
    try:
        response = supabase.table("equipment").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching equipment: {e}")
        return []

def insert_equipment(eq_dict):
    if not supabase: return None
    try:
        response = supabase.table("equipment").insert(eq_dict).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting equipment: {e}")
        raise e

def update_equipment(eq_id, update_dict):
    if not supabase: return None
    try:
        response = supabase.table("equipment").update(update_dict).eq("id", eq_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating equipment: {e}")
        raise e

def delete_equipment(eq_id):
    if not supabase: return None
    try:
        response = supabase.table("equipment").delete().eq("id", eq_id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting equipment: {e}")
        raise e

# ------------------------------------------
# 3. 抽出ログ (drip_logs) テーブル操作
# ------------------------------------------
def get_drip_logs():
    if not supabase: return []
    try:
        response = supabase.table("drip_logs").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching drip_logs: {e}")
        return []

def insert_drip_log(log_dict):
    if not supabase: return None
    try:
        response = supabase.table("drip_logs").insert(log_dict).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting drip_log: {e}")
        raise e

def update_drip_log(log_id, update_dict):
    if not supabase: return None
    try:
        response = supabase.table("drip_logs").update(update_dict).eq("id", log_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating drip_log: {e}")
        raise e

def delete_drip_log(log_id):
    if not supabase: return None
    try:
        response = supabase.table("drip_logs").delete().eq("id", log_id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting drip_log: {e}")
        raise e