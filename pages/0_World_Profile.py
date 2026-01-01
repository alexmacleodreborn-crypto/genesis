import streamlit as st
from a7do.world_profile import WorldProfile

if "world" not in st.session_state:
    st.session_state.world = WorldProfile()

world = st.session_state.world

st.title("🌍 World Profile (Observer)")

with st.form("add_place"):
    p = st.text_input("Add place")
    if st.form_submit_button("Add place") and p:
        world.add_place(p)

with st.form("add_person"):
    n = st.text_input("Add person")
    r = st.text_input("Role (optional)")
    if st.form_submit_button("Add person") and n:
        world.add_person(n, r)

with st.form("add_pet"):
    n = st.text_input("Pet name")
    s = st.text_input("Species")
    if st.form_submit_button("Add pet") and n:
        world.add_pet(n, s)

with st.form("add_object"):
    o = st.text_input("Object")
    if st.form_submit_button("Add object") and o:
        world.add_object(o)

st.subheader("World Snapshot")
st.json(world.snapshot())