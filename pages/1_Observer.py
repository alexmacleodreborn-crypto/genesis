import streamlit as st

st.set_page_config(page_title="Observer", layout="wide")
st.title("👁️ Observer — Learning Trace")

mind = st.session_state.get("mind")
schedule = st.session_state.get("schedule")
world = st.session_state.get("world")

if not mind or not schedule or not world:
    st.info("Go to the main A7DO page and World Profile first.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
status = schedule.status()
c1.metric("Day", status["day"])
c2.metric("State", status["state"])
c3.metric("Room", status["room"])
c4.metric("Events Remaining", status["events_remaining"])

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Current World Lock")
    st.write(f"Parents present: **{world.has_parents()}**")
    st.write(f"Home generated: **{world.home_generated}**")
    st.write(f"Locomotion: **{status['locomotion']}**")
    st.write(f"Position (x,y): **{status['pos_xy']}**")

    st.subheader("Lexicon (exposure counts)")
    st.json(mind.lexicon.snapshot())

with right:
    st.subheader("Latest Coherence Check")
    st.json(mind.last_coherence or {"note": "no coherence run yet"})

    st.subheader("Latest Sleep Report")
    st.json(mind.last_sleep_report or {"note": "no sleep yet"})

st.divider()
st.subheader("Learning Trace (what was shown → how structure formed)")

trace = mind.trace[-60:]
if not trace:
    st.info("No trace yet. Wake A7DO and step events.")
else:
    for t in trace[::-1]:
        phase = t.get("phase")
        if phase == "experience":
            st.markdown(f"### EXPERIENCE @ {t.get('room')}")
            st.code(t.get("prompt", "—"))
            st.json(t.get("event", {}))
            st.json({"coherence": t.get("coherence", {})})
        elif phase == "movement":
            st.markdown("### MOVEMENT (inferred from place change)")
            st.write(f"From **{t.get('from')}** → **{t.get('to')}**")
        elif phase == "blocked":
            st.markdown("### BLOCKED (decoherence protection)")
            st.code(t.get("event", "—"))
            st.json(t.get("coherence", {}))
        elif phase == "sleep":
            st.markdown("### SLEEP (replay stats)")
            st.json(t.get("report", {}))
        else:
            st.markdown(f"### {phase.upper()}")
            st.json(t)