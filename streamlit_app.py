import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO", layout="centered")

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind = st.session_state.mind

st.title("🧠 A7DO")
st.caption("Infant Learning Mode")

st.divider()

# -------------------------
# State
# -------------------------
if not mind.schedule.started:
    st.info("A7DO is waiting.")

    if st.button("🌅 Wake A7DO"):
        mind.schedule.start()
        mind.wake()
        st.rerun()

else:
    if mind.awake:
        st.success("A7DO is awake.")

        phrase = st.text_input(
            "Teach A7DO (simple phrases only)",
            placeholder="this is a dog"
        )

        if st.button("👁️ Show"):
            if phrase:
                response = mind.process_experience(phrase)
                st.write(response)
                st.rerun()

        if st.button("🌙 Sleep"):
            report = mind.sleep()
            mind.schedule.end()
            st.json(report)
            st.rerun()

    else:
        st.info("A7DO is sleeping.")