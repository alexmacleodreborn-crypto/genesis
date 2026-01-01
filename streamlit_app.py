import streamlit as st
from a7do.schedule_engine import Schedule
from a7do.mind import A7DOMind
from a7do.teacher_planner import generate_day_schedule

st.set_page_config(page_title="A7DO", layout="centered")

if "world" not in st.session_state:
    st.info("Define the world first in World Profile.")
    st.stop()

if "schedule" not in st.session_state:
    st.session_state.schedule = Schedule()

schedule = st.session_state.schedule

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind(schedule)

mind = st.session_state.mind
world = st.session_state.world

st.title("🧠 A7DO")

st.caption(f"Day {schedule.day} — Place: {schedule.place or 'unset'}")

if schedule.state == "waiting":
    st.info("A7DO is waiting.")
    if st.button("Wake A7DO"):
        events = generate_day_schedule(world, schedule.day)
        schedule.load_day(schedule.day, "home", events)
        schedule.wake()
        mind.wake()
        st.rerun()

elif schedule.state == "awake":
    st.success("A7DO is awake.")
    ev = schedule.next_event()
    if ev:
        mind.process_event(ev)
        st.write(f"A7DO experiences: **{ev}**")
    else:
        schedule.sleep()
        report = mind.sleep()
        st.json(report)
        schedule.complete()
        st.rerun()

elif schedule.state == "complete":
    st.info("Day complete.")
    if st.button("Next Day"):
        schedule.load_day(schedule.day + 1, schedule.place, [])
        st.rerun()

st.divider()
st.subheader("Observer View")
st.write("Last:", mind.last)
st.write("Lexicon:", mind.lexicon.snapshot())