import streamlit as st
from a7do.profiles import WorldProfiles
from a7do.schedule_engine import Schedule
from a7do.mind import A7DOMind
from a7do.teacher_planner import generate_two_day_schedule
from a7do.homeplot import generate_default_home

st.set_page_config(page_title="A7DO", layout="wide")

# --- state init
if "world" not in st.session_state:
    st.session_state.world = WorldProfiles()

world = st.session_state.world

if "schedule" not in st.session_state:
    st.session_state.schedule = Schedule()

schedule = st.session_state.schedule

# homeplot can be generated from World Profile page; fallback to session if exists
homeplot = st.session_state.get("homeplot")
if world.home_generated and not homeplot:
    # reconstruct from seed if needed
    homeplot = generate_default_home(int(world.home_seed))
    st.session_state.homeplot = homeplot

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind(schedule=schedule, world=world)

mind = st.session_state.mind

st.title("🧠 A7DO — Cognitive Core")

# --- central display
if not world.home_generated:
    st.warning("WAITING — BIRTHING: HomePlot not generated yet. Create it in World Profile.")
elif not world.has_parents():
    st.warning("WAITING — BIRTHING: Mum + Dad must be added in World Profile to unlock learning.")
else:
    st.success("READY: World scaffold + parents present. Schedule can be generated.")

st.divider()

# --- status bar
status = schedule.status()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Day", status["day"])
c2.metric("State", status["state"])
c3.metric("Room", status["room"])
c4.metric("Events Remaining", status["events_remaining"])
c5.metric("Locomotion", status["locomotion"])

st.divider()

# --- controls
left, right = st.columns([1, 1])

with left:
    st.subheader("Schedule Control")

    if st.button("🤖 Generate 2-Day Schedule", disabled=(not world.home_generated or not world.has_parents())):
        plan = generate_two_day_schedule(world, st.session_state.homeplot, seed=11)
        st.session_state.plan = plan
        st.success("Two-day schedule created (Day 0 + Day 1).")

    plan = st.session_state.get("plan")

    if plan:
        st.write("Planned Days:", list(plan.keys()))
        st.write(f"Day 0 events: {len(plan[0])} | Day 1 events: {len(plan[1])}")

    st.divider()

    if st.button("🌅 Wake A7DO (load current day)", disabled=(not plan or schedule.state not in ("waiting","complete"))):
        day = schedule.day
        events = plan.get(day, [])
        schedule.load_day(day=day, homeplot=st.session_state.homeplot, start_room="hall", events=events)
        schedule.wake()
        mind.wake()
        st.rerun()

    if st.button("⏭️ Step 1 Event", disabled=(schedule.state != "awake")):
        ev = schedule.next_event()
        if ev is None:
            schedule.sleep()
            rep = mind.sleep()
            schedule.complete()
            st.success("Day ended → Sleep replay complete.")
        else:
            mind.ingest_event(ev)
        st.rerun()

    if st.button("▶️ Run Day", disabled=(schedule.state != "awake")):
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
    st.subheader("Current Event Queue")
    if schedule.events:
        for i, ev in enumerate(schedule.events, 1):
            st.write(f"**{i}.** room=`{ev.room}` agent=`{ev.agent}` action=`{ev.action}` obj=`{ev.obj}` to_room=`{ev.to_room}`")
    else:
        st.info("No queued events. Generate schedule, then Wake A7DO.")

    st.divider()
    st.subheader("Now (Observer summary)")
    st.write("Last:", mind.last)
    st.write("Position (x,y):", schedule.spatial.pos_xy)
    st.write("Room:", schedule.current_room)

st.divider()
st.subheader("Quick Lexicon View (exposure counts)")
st.json(mind.lexicon.snapshot())