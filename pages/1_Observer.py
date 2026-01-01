import streamlit as st

st.set_page_config(page_title="Observer", layout="centered")

mind = st.session_state.get("mind")

st.title("👁️ Observer")

if not mind:
    st.info("A7DO not initialised.")
    st.stop()

st.subheader("Last Action")
st.write(mind.last or "—")

st.subheader("Recent Experiences")
for p in mind.experiences.recent(10):
    st.write("•", p)

st.subheader("Known Words")
st.json(mind.lexicon.known_words())