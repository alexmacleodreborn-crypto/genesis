import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a7do.homeplot import generate_default_home
from a7do.mind import A7DOMind
from a7do.profiles import WorldProfiles
from a7do.schedule_engine import Schedule
from a7do.teacher_planner import generate_two_day_schedule

st.set_page_config(page_title="A7DO Dashboard", layout="wide")


# --- state init
if "world" not in st.session_state:
    st.session_state.world = WorldProfiles()
world = st.session_state.world

if "schedule" not in st.session_state:
    st.session_state.schedule = Schedule()
schedule = st.session_state.schedule

homeplot = st.session_state.get("homeplot")
if world.home_generated and not homeplot:
    homeplot = generate_default_home(int(world.home_seed))
    st.session_state.homeplot = homeplot

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind(schedule=schedule, world=world)
mind = st.session_state.mind


st.title("🧠 A7DO Streamlit Dashboard")
st.caption("Control day simulation + inspect learning metrics in one place.")

# --- readiness
if not world.home_generated:
    st.warning("WAITING: Generate HomePlot in World Profile page.")
elif not world.has_parents():
    st.warning("WAITING: Add both Mum and Dad in World Profile page.")
else:
    st.success("READY: Home + parents configured.")

status = schedule.status()
plan = st.session_state.get("plan")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Day", status["day"])
m2.metric("State", status["state"])
m3.metric("Room", status["room"])
m4.metric("Queue", status["events_remaining"])
m5.metric("Locomotion", status["locomotion"])

st.divider()

left, right = st.columns([1, 1])
with left:
    st.subheader("Simulation Controls")

    if st.button("🤖 Generate 2-Day Schedule", disabled=(not world.home_generated or not world.has_parents())):
        generated_plan = generate_two_day_schedule(world, st.session_state.homeplot, seed=11)
        st.session_state.plan = generated_plan
        st.success("Generated day plan (0 and 1).")

    plan = st.session_state.get("plan")
    if plan:
        st.write(f"Planned days: {sorted(plan.keys())}")
        st.write(f"Day 0 events: {len(plan.get(0, []))} | Day 1 events: {len(plan.get(1, []))}")

    if st.button("🌅 Wake A7DO", disabled=(not plan or schedule.state not in ("waiting", "complete"))):
        day = schedule.day
        events = plan.get(day, [])
        schedule.load_day(
            day=day,
            place=st.session_state.get("homeplot"),
            homeplot=st.session_state.get("homeplot"),
            start_room="hall",
            events=events,
        )
        schedule.wake()
        mind.wake()
        st.rerun()

    if st.button("⏭️ Step Event", disabled=(schedule.state != "awake")):
        ev = schedule.next_event()
        if ev is None:
            schedule.sleep()
            mind.sleep()
            schedule.complete()
            st.success("Day complete + replay stored.")
        else:
            mind.ingest_event(ev)
        st.rerun()

    if st.button("▶️ Run Full Day", disabled=(schedule.state != "awake")):
        while schedule.state == "awake":
            ev = schedule.next_event()
            if ev is None:
                schedule.sleep()
                mind.sleep()
                schedule.complete()
                break
            mind.ingest_event(ev)
        st.rerun()

    if st.button("➡️ Next Day", disabled=(schedule.state != "complete")):
        schedule.day += 1
        schedule.state = "waiting"
        schedule.events = []
        st.rerun()

with right:
    st.subheader("Upcoming Events")
    if schedule.events:
        queue_df = pd.DataFrame(
            [
                {
                    "room": e.room,
                    "agent": e.agent,
                    "action": e.action,
                    "object": e.obj,
                    "to_room": e.to_room,
                }
                for e in schedule.events
            ]
        )
        st.dataframe(queue_df, use_container_width=True)
    else:
        st.info("No queued events.")

    st.subheader("Current Snapshot")
    st.json(
        {
            "last": mind.last,
            "position": schedule.spatial.pos_xy,
            "room": schedule.current_room,
            "trace_events": len(mind.trace),
            "experience_count": len(mind.experiences),
        }
    )

st.divider()
st.subheader("Learning Dashboard")

trace = mind.trace
experience_rows = [t for t in trace if t.get("phase") == "experience"]

if experience_rows:
    events_df = pd.DataFrame(
        [
            {
                "room": row["event"].get("room"),
                "agent": row["event"].get("agent"),
                "action": row["event"].get("action"),
                "object": row["event"].get("object"),
                "coherence": row.get("coherence", {}).get("score", 0),
            }
            for row in experience_rows
        ]
    )

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Events by room**")
        room_counts = events_df["room"].value_counts().rename_axis("room").reset_index(name="count")
        st.bar_chart(room_counts.set_index("room"))

    with d2:
        st.markdown("**Coherence trend**")
        coherence_df = events_df[["coherence"]].reset_index(names="event_idx")
        st.line_chart(coherence_df.set_index("event_idx"))

    st.markdown("**Recent experienced events**")
    st.dataframe(events_df.tail(12), use_container_width=True)
else:
    st.info("No experiences yet. Wake and run at least one event.")

st.subheader("Lexicon Exposure")
st.json(mind.lexicon.snapshot())
