import os
import streamlit as st
from supabase import create_client, Client

# --- 1. 安全な環境変数取得関数 ---
def _get_secret(key: str) -> str:
    """os.environ と st.secrets の両方から環境変数を取得"""
    # 1. os.environ から取得
    val = os.environ.get(key)
    if val:
        return val.strip()
    # 2. st.secrets から取得
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return ""

# --- 2. Supabase クライアント初期化 ---
raw_url = _get_secret("SUPABASE_URL")
# URLの整形 (末尾スラッシュや /rest/v1 などの誤入力を自動補正)
supabase_url = raw_url.rstrip("/")
if supabase_url.endswith("/rest/v1"):
    supabase_url = supabase_url[:-8].rstrip("/")

supabase_key = _get_secret("SUPABASE_KEY")

supabase: Client = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Supabase Client Initialization Error: {e}")
        supabase = None


# --- 3. BEANS (コーヒー豆) 操作 ---
def get_beans():
    if not supabase:
        st.error("DB Connection Error: SUPABASE_URL または SUPABASE_KEY が取得できていません。")
        return []
    try:
        res = supabase.table("beans").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching beans: {e}")
        return []

def add_bean(bean_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("beans").insert(bean_data).execute()
        return res.data
    except Exception as e:
        st.error(f"Error adding bean: {e}")
        return None

def update_bean(bean_id: str, bean_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("beans").update(bean_data).eq("id", bean_id).execute()
        return res.data
    except Exception as e:
        st.error(f"Error updating bean: {e}")
        return None

def delete_bean(bean_id: str):
    if not supabase:
        return False
    try:
        supabase.table("beans").delete().eq("id", bean_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting bean: {e}")
        return False


# --- 4. GEARS (抽出器具) 操作 ---
def get_gears():
    if not supabase:
        return []
    try:
        res = supabase.table("gears").select("*").order("type").execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching gears: {e}")
        return []

def add_gear(gear_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("gears").insert(gear_data).execute()
        return res.data
    except Exception as e:
        st.error(f"Error adding gear: {e}")
        return None

def update_gear(gear_id: str, gear_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("gears").update(gear_data).eq("id", gear_id).execute()
        return res.data
    except Exception as e:
        st.error(f"Error updating gear: {e}")
        return None

def delete_gear(gear_id: str):
    if not supabase:
        return False
    try:
        supabase.table("gears").delete().eq("id", gear_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting gear: {e}")
        return False


# --- 5. DRIP LOGS (抽出記録・FEEDBACK) 操作 ---
def get_drip_logs():
    if not supabase:
        return []
    try:
        res = supabase.table("drip_logs").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching drip logs: {e}")
        return []

def add_drip_log(log_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("drip_logs").insert(log_data).execute()
        return res.data
    except Exception as e:
        st.error(f"Error adding drip log: {e}")
        return None

def delete_drip_log(log_id: str):
    if not supabase:
        return False
    try:
        supabase.table("drip_logs").delete().eq("id", log_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting drip log: {e}")
        return False

def update_drip_log(log_id: str, log_data: dict):
    if not supabase:
        return None
    try:
        res = supabase.table("drip_logs").update(log_data).eq("id", log_id).execute()
        return res.data
    except Exception as e:
        print(f"Error updating drip log: {e}")
        return None