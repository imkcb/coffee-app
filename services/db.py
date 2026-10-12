import os
import streamlit as st
from supabase import create_client, Client

# .env ファイルが存在する場合の自動読み込み対応
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key_name):
    # 1. OS環境変数 / .env からの取得
    val = os.getenv(key_name)
    if val:
        return val
    # 2. Streamlit secrets からの取得
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return None

supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    st.error("SUPABASE_URL または SUPABASE_KEY が取得できませんでした。.streamlit/secrets.toml または .env ファイルをご確認ください。")
    st.stop()

supabase: Client = create_client(supabase_url, supabase_key)

# --- Beans CRUD ---
def get_beans():
    try:
        response = supabase.table("beans").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching beans: {e}")
        return []

def add_bean(data):
    try:
        response = supabase.table("beans").insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding bean: {e}")
        return None

def update_bean(bean_id, data):
    try:
        response = supabase.table("beans").update(data).eq("id", bean_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating bean: {e}")
        return None

def delete_bean(bean_id):
    try:
        response = supabase.table("beans").delete().eq("id", bean_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error deleting bean: {e}")
        return None

# --- Equipment (Gear) CRUD ---
def get_equipment():
    try:
        response = supabase.table("equipment").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching equipment: {e}")
        return []

def add_equipment(data):
    try:
        response = supabase.table("equipment").insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding equipment: {e}")
        return None

def update_equipment(eq_id, data):
    try:
        response = supabase.table("equipment").update(data).eq("id", eq_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating equipment: {e}")
        return None

def delete_equipment(eq_id):
    try:
        response = supabase.table("equipment").delete().eq("id", eq_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error deleting equipment: {e}")
        return None

# gear_tab.py 用のエイリアス定義
get_gears = get_equipment
add_gear = add_equipment
update_gear = update_equipment
delete_gear = delete_equipment

# --- Drip Logs CRUD ---
def get_drip_logs():
    try:
        response = supabase.table("drip_logs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching drip logs: {e}")
        return []

def add_drip_log(data):
    try:
        response = supabase.table("drip_logs").insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding drip log: {e}")
        return None

def delete_drip_log(log_id):
    try:
        response = supabase.table("drip_logs").delete().eq("id", log_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error deleting drip log: {e}")
        return None
    
def update_drip_log(log_id, data):
    try:
        response = supabase.table("drip_logs").update(data).eq("id", log_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating drip log: {e}")
        return None
