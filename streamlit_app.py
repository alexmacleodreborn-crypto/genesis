import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(layout="wide")
st.title("🧠 A7DO")

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind = st.session_state.mind

text = st.text_input("Say something")

if text:
    result = mind.process(text)
    st.write(result["answer"])

st.divider()
st.subheader("Entities")
for e in mind.bridge.entities.values():
    st.write(e)

st.divider()
st.subheader("Objects")
for o in mind.objects.objects.values():
    st.write(o)

st.divider()
st.subheader("Relationships")
for r in mind.relationships.relations:
    st.write(r)

st.divider()
st.subheader("Events")
for e in mind.events.events:
    st.write(e)