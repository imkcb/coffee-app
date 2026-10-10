import streamlit as st
import db

def render():
    beans_data = db.get_beans()

    st.header("🫘 豆管理")
    st.subheader("豆の新規登録")
    col1, col2 = st.columns(2)
    with col1:
        bean_name = st.text_input("豆の名前（必須）", key="input_bean_name")
        shop_name = st.text_input("購入店", key="input_shop_name")
        roast_lvl = st.selectbox("焙煎度", ["浅煎り", "中浅煎り", "中煎り", "中深煎り", "深煎り"], key="input_roast_lvl")
        origin_name = st.text_input("産地", key="input_origin_name")
        flavor_notes = st.text_input("フレーバーノート", key="input_flavor_notes")
    with col2:
        farm_name = st.text_input("農園", key="input_farm_name")
        elevation_val = st.text_input("標高", key="input_elevation_val")
        process_type = st.text_input("精製方法 (プロセス)", key="input_process_type")
        variety_name = st.text_input("品種", key="input_variety_name")

    if st.button("🫘 豆を登録する", key="btn_add_bean"):
        if not bean_name:
            st.error("豆の名前を入力してください。")
        else:
            try:
                db.insert_bean({
                    "name": bean_name, "shop": shop_name, "roast_level": roast_lvl,
                    "origin": origin_name, "flavor_notes": flavor_notes, "farm": farm_name,
                    "elevation": elevation_val, "process": process_type, "variety": variety_name
                })
                st.success(f"「{bean_name}」を保存しました！")
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")

    st.divider()
    st.subheader("登録済みの豆一覧")
    if beans_data:
        for b in beans_data:
            b_id = b.get("id")
            with st.expander(f"🫘 **{b.get('name')}** （{b.get('roast_level', '未設定')}）"):
                edit_key = f"edit_bean_mode_{b_id}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False

                if not st.session_state[edit_key]:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**購入店**: {b.get('shop') or '未設定'}")
                        st.write(f"**産地**: {b.get('origin') or '未設定'}")
                        st.write(f"**フレーバー**: {b.get('flavor_notes') or '未設定'}")
                    with c2:
                        st.write(f"**精製方法**: {b.get('process') or '未設定'}")
                        st.write(f"**品種**: {b.get('variety') or '未設定'}")
                    st.divider()
                    col_btn1, col_btn2 = st.columns([1, 1])
                    with col_btn1:
                        if st.button("✏️ 編集", key=f"btn_edit_mode_bean_{b_id}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🗑️ 削除", key=f"del_bean_{b_id}"):
                            try:
                                db.delete_bean(b_id)
                                st.success("削除しました。")
                                st.rerun()
                            except Exception as e:
                                st.error(f"削除エラー: {e}")
                else:
                    st.markdown("#### ✏️ 豆情報の編集")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        u_name = st.text_input("豆の名前", value=b.get("name") or "", key=f"u_bname_{b_id}")
                        u_shop = st.text_input("購入店", value=b.get("shop") or "", key=f"u_bshop_{b_id}")
                        roast_opts = ["浅煎り", "中浅煎り", "中煎り", "中深煎り", "深煎り"]
                        u_roast = st.selectbox("焙煎度", roast_opts, index=roast_opts.index(b.get("roast_level")) if b.get("roast_level") in roast_opts else 0, key=f"u_broast_{b_id}")
                        u_origin = st.text_input("産地", value=b.get("origin") or "", key=f"u_borigin_{b_id}")
                        u_flavor = st.text_input("フレーバーノート", value=b.get("flavor_notes") or "", key=f"u_bflavor_{b_id}")
                    with ec2:
                        u_farm = st.text_input("農園", value=b.get("farm") or "", key=f"u_bfarm_{b_id}")
                        u_elevation = st.text_input("標高", value=b.get("elevation") or "", key=f"u_belev_{b_id}")
                        u_process = st.text_input("精製方法", value=b.get("process") or "", key=f"u_bproc_{b_id}")
                        u_variety = st.text_input("品種", value=b.get("variety") or "", key=f"u_bvar_{b_id}")

                    if st.button("💾 更新を保存", key=f"btn_save_u_bean_{b_id}"):
                        try:
                            db.update_bean(b_id, {
                                "name": u_name, "shop": u_shop, "roast_level": u_roast,
                                "origin": u_origin, "flavor_notes": u_flavor, "farm": u_farm,
                                "elevation": u_elevation, "process": u_process, "variety": u_variety
                            })
                            st.session_state[edit_key] = False
                            st.success("更新しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新エラー: {e}")
    else:
        st.info("登録されている豆はまだありません。")