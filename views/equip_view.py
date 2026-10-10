import streamlit as st
import db

def render():
    equipment_data = db.get_equipment()

    st.header("🛠️ 器具管理")
    st.subheader("器具の新規登録")
    eq_category = st.selectbox("カテゴリ", ["ドリッパー", "ミル（グラインダー）", "フィルター", "サーバー", "その他"], key="input_eq_category")
    eq_name = st.text_input("器具の名前（必須）", key="input_eq_name")
    eq_brand = st.text_input("ブランド / メーカー", key="input_eq_brand")

    if st.button("☕ 器具を登録する", key="btn_add_equipment"):
        if eq_name:
            try:
                db.insert_equipment({"category": eq_category, "name": eq_name, "brand": eq_brand, "is_active": True})
                st.success(f"「{eq_name}」を登録しました！")
                st.rerun()
            except Exception as e:
                st.error(f"登録エラー: {e}")

    st.divider()
    st.subheader("登録済みの器具一覧")
    if equipment_data:
        for eq in equipment_data:
            eq_id = eq.get("id")
            is_act = eq.get("is_active", True)
            if is_act is None: is_act = True

            edit_eq_key = f"edit_eq_mode_{eq_id}"
            if edit_eq_key not in st.session_state: st.session_state[edit_eq_key] = False

            if not st.session_state[edit_eq_key]:
                col_info, col_toggle, col_edit, col_del = st.columns([3, 1.5, 1, 1])
                with col_info:
                    status_str = "🟢 利用可能" if is_act else "🔴 欠品中（AI対象外）"
                    brand_str = f"（{eq.get('brand')}）" if eq.get('brand') else ""
                    st.markdown(f"・ **[{eq.get('category')}] {eq.get('name')}** {brand_str} - {status_str}")
                with col_toggle:
                    new_status = st.toggle("AI提案に含める", value=is_act, key=f"toggle_eq_{eq_id}")
                    if new_status != is_act:
                        db.update_equipment(eq_id, {"is_active": new_status})
                        st.rerun()
                with col_edit:
                    if st.button("✏️ 編集", key=f"btn_edit_mode_eq_{eq_id}"):
                        st.session_state[edit_eq_key] = True
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 削除", key=f"del_eq_{eq_id}"):
                        try:
                            db.delete_equipment(eq_id)
                            st.success("削除しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除エラー: {e}")
            else:
                st.markdown("#### ✏️ 器具情報の編集")
                eq_cat_opts = ["ドリッパー", "ミル（グラインダー）", "フィルター", "サーバー", "その他"]
                u_eq_cat = st.selectbox("カテゴリ", eq_cat_opts, index=eq_cat_opts.index(eq.get("category")) if eq.get("category") in eq_cat_opts else 0, key=f"u_eqcat_{eq_id}")
                u_eq_name = st.text_input("器具の名前", value=eq.get("name") or "", key=f"u_eqname_{eq_id}")
                u_eq_brand = st.text_input("ブランド / メーカー", value=eq.get("brand") or "", key=f"u_eqbrand_{eq_id}")

                col_u_save, col_u_cancel = st.columns([1, 1])
                with col_u_save:
                    if st.button("💾 更新を保存", key=f"btn_save_u_eq_{eq_id}"):
                        try:
                            db.update_equipment(eq_id, {
                                "category": u_eq_cat,
                                "name": u_eq_name,
                                "brand": u_eq_brand
                            })
                            st.session_state[edit_eq_key] = False
                            st.success("器具情報を更新しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新エラー: {e}")
                with col_u_cancel:
                    if st.button("キャンセル", key=f"btn_cancel_u_eq_{eq_id}"):
                        st.session_state[edit_eq_key] = False
                        st.rerun()
    else:
        st.info("登録されている器具はまだありません。")