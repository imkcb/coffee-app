import streamlit as st
import db

def render():
    st.markdown('<div class="logs-tab-marker"></div>', unsafe_allow_html=True)
    st.markdown("### LOGS")

    drip_logs = db.get_drip_logs()
    confirmed_logs = []

    if drip_logs:
        for log in drip_logs:
            data_p = log.get("data") or {}
            if data_p.get("is_draft") is not True:
                confirmed_logs.append(log)

    if confirmed_logs:
        confirmed_logs = sorted(confirmed_logs, key=lambda x: str(x.get("created_at", "")), reverse=True)
        
        st.markdown(f"#### TOTAL SESSIONS ({len(confirmed_logs)})")

        for log in confirmed_logs:
            created_at = str(log.get("created_at", ""))[:10]
            data = log.get("data") or {}
            bean_name = data.get("bean_name", "Unknown Bean")
            rating = data.get("rating", "-")
            coffee_type = data.get("coffee_type", "HOT")
            water_amount = data.get("water_per_cup", 300)
            comment = data.get("comment", "")

            with st.expander(f"[{created_at}] {bean_name} (Rating: {rating}/5)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**TYPE**: {coffee_type}")
                    st.write(f"**WATER**: {water_amount} ml")
                    st.write(f"**ACIDITY**: {data.get('acid_level', '-')}")
                with c2:
                    st.write(f"**BODY**: {data.get('bitter_level', '-')}")
                    st.write(f"**TIME**: {data.get('actual_time', '-') if data.get('actual_time') else '-'}")
                    st.write(f"**RATING**: {rating} / 5")

                if comment:
                    st.info(f"**NOTE**: {comment}")

                recipe = data.get("recipe") or {}
                if recipe:
                    st.markdown("**RECIPE SUMMARY**")
                    st.write(f"- COFFEE: {recipe.get('coffee_amount', '-')}")
                    st.write(f"- TEMP: {recipe.get('water_temp', '-')}")
                    st.write(f"- GRIND: {recipe.get('grind_setting', '-')}")
    else:
        st.info("NO LOGS SAVED YET.")