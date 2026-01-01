import streamlit as st

from a7do.mind import A7DOMind
from a7do.schedule import ScheduleEngine, ScheduledEvent
from a7do.graph import build_brain_dot

st.set_page_config(page_title="A7DO Cognitive Interface", layout="wide")

# -------------------------
# Session init
# -------------------------
if "mind" not in st.session_state or not hasattr(st.session_state.get("mind"), "identity"):
    st.session_state.mind = A7DOMind()

if "schedule" not in st.session_state:
    st.session_state.schedule = ScheduleEngine()

if "log" not in st.session_state:
    st.session_state.log = []

mind: A7DOMind = st.session_state.mind
sched: ScheduleEngine = st.session_state.schedule

# -------------------------
# Header
# -------------------------
st.markdown("# 🧠 A7DO — Scheduled Cognition")
st.caption("External Schedule → Builders → Events → Sleep → Reflection (Pattern 1 replay)")

# -------------------------
# Sidebar: Identity + Schedule State
# -------------------------
with st.sidebar:
    st.subheader("Identity")
    st.markdown(mind.identity.panel_markdown())

    st.divider()
    st.subheader("Schedule State")
    s = sched.status()
    st.metric("Day", s["day"])
    st.metric("Awake used", s["awake_used"])
    st.metric("Awake remaining", s["awake_remaining"])
    st.write(f"Started: **{s['started']}**  |  Asleep: **{s['asleep']}**  |  Completed: **{s['completed']}**")
    st.write(f"Events queued: **{s['events_count']}**  | Cursor: **{s['cursor']}**")

    if st.button("Reset schedule + mind day buffer"):
        sched.reset()
        mind.new_day_reset()
        st.session_state.log = []
        st.rerun()

# -------------------------
# Tabs
# -------------------------
tab_schedule, tab_world, tab_reflection, tab_graph = st.tabs(
    ["📆 Schedule Builders", "🌍 World State", "🌙 Sleep & Reflection", "🧬 Brain Graph"]
)

# ============================================================
# TAB 1: SCHEDULE BUILDERS
# ============================================================
with tab_schedule:
    st.subheader("Build today’s schedule (external truth)")
    st.caption("Add at least 1 event, then press Start Schedule. Each event costs 1 awake-hour (max 6). Sleep is forced.")

    colA, colB = st.columns([1, 1])

    with colA:
        st.markdown("### Add an event")
        builder = st.selectbox(
            "Builder",
            ["user_input", "relationship", "object", "sensory", "language", "shapes", "routine"],
        )

        payload = {}

        if builder == "user_input":
            payload["name"] = st.text_input("Name (optional)", value="")
            payload["text"] = st.text_area("User input text (day anchor)", value="hello")

        elif builder == "relationship":
            payload["subject"] = st.text_input("Subject (blank = speaker)", value="")
            payload["relation"] = st.text_input("Relation (pet/friend/uncle/owns/etc.)", value="friend")
            payload["object"] = st.text_input("Object (entity name)", value="Craig")
            payload["object_kind"] = st.selectbox("Object kind", ["person", "pet", "agent"], index=0)
            payload["note"] = st.text_input("Note", value="scheduled")

        elif builder == "object":
            payload["label"] = st.text_input("Object label (ball/swing/etc.)", value="ball")
            payload["colour"] = st.text_input("Colour (optional)", value="red")
            payload["owner"] = st.text_input("Owner (blank = speaker)", value="")
            payload["attached_to"] = st.text_input("Attached to (pet/person name optional)", value="")
            payload["state"] = st.selectbox("State", ["present", "gone"], index=0)
            payload["place"] = st.text_input("Place (optional)", value="park")

        elif builder == "sensory":
            payload["place"] = st.text_input("Place", value="park")
            payload["smells"] = st.text_input("Smells (comma-separated)", value="fresh grass").split(",")
            payload["sounds"] = st.text_input("Sounds (comma-separated)", value="birds").split(",")
            payload["emotion"] = st.text_input("Emotion (optional)", value="calm")
            payload["note"] = st.text_input("Note", value="sensory snapshot")

        elif builder == "language":
            payload["concept"] = st.text_input("Concept (pronoun/tense/etc.)", value="pronoun")
            payload["token"] = st.text_input("Token", value="I")
            payload["meaning"] = st.text_input("Meaning", value="speaker refers to self")
            payload["examples"] = st.text_area("Examples (optional)", value="I am Alex.\nMy dog is Xena.")

        elif builder == "shapes":
            payload["shape"] = st.text_input("Shape", value="circle")
            payload["properties"] = st.text_area("Properties (optional)", value="round, no corners")
            payload["example"] = st.text_input("Example", value="ball")

        elif builder == "routine":
            payload["slot"] = st.selectbox("Slot", ["morning", "afternoon", "evening"], index=0)
            payload["activity"] = st.text_input("Activity", value="go to the park")
            payload["participants"] = [x.strip() for x in st.text_input("Participants (comma-separated)", value="Alex, Xena").split(",")]
            payload["place"] = st.text_input("Place (optional)", value="park")

        if st.button("Add event to today"):
            try:
                sched.day.add_event(ScheduledEvent(builder=builder, payload=payload))
                st.success("Event added.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with colB:
        st.markdown("### Today’s event queue")
        if not sched.day.events:
            st.info("No events yet. Add at least 1 event.")
        else:
            for i, ev in enumerate(sched.day.events):
                st.write(f"**{i+1}.** `{ev.builder}` — {ev.payload}")

        st.divider()

        start_ok = sched.day.has_minimum_to_start() and (not sched.day.started)
        if st.button("▶️ Start Schedule", disabled=not start_ok):
            try:
                sched.day.start()
                # auto Wake (not counted as an awake-hour event)
                st.session_state.log.append(("SYSTEM", f"Day {sched.day.day_index} — WAKE"))
                st.success("Schedule started. A7DO is awake.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        run_disabled = (not sched.day.started) or sched.day.asleep or sched.day.completed
        if st.button("➡️ Run next event (1 hour)", disabled=run_disabled):
            ev = sched.day.consume_next()
            if ev is None:
                # force sleep boundary
                sched.day.mark_sleep()
                st.session_state.log.append(("SYSTEM", "Forced SLEEP (awake hours boundary or events ended)."))
                st.rerun()
            else:
                with st.spinner("A7DO processing scheduled event..."):
                    result = mind.ingest_scheduled_event(ev.builder, ev.payload)
                st.session_state.log.append((ev.builder, result.get("answer", "—")))

                # check forced sleep
                if sched.day.should_force_sleep():
                    sched.day.mark_sleep()
                    st.session_state.log.append(("SYSTEM", "Entering SLEEP (end of awake window)."))

                st.rerun()

        if st.button("🌙 Run Sleep (Reflection Pattern 1)", disabled=(not sched.day.asleep or sched.day.completed)):
            # run sleep
            report = mind.sleep()
            st.session_state.log.append(("SLEEP", "Reflection Pattern 1 complete."))
            sched.day.mark_complete()
            st.rerun()

        if st.button("➡️ Advance Day", disabled=(not sched.day.completed)):
            sched.new_day()
            mind.new_day_reset()
            st.session_state.log.append(("SYSTEM", f"Advanced to Day {sched.day.day_index} (awaiting schedule)."))
            st.rerun()

        st.divider()
        st.markdown("### Run Log")
        for who, msg in st.session_state.log[-40:]:
            st.write(f"**{who}:** {msg}")

# ============================================================
# TAB 2: WORLD STATE
# ============================================================
with tab_world:
    st.subheader("Entities")
    for e in mind.bridge.entities.values():
        st.write(f"• {e.name} ({e.kind}) conf={e.confidence:.2f} origin={e.origin}")

    st.subheader("Relationships")
    if not mind.relationships.relations:
        st.info("No relationships.")
    else:
        for r in mind.relationships.relations:
            a = mind.bridge.entities.get(r.subject_id)
            b = mind.bridge.entities.get(r.object_id)
            if a and b:
                st.write(f"• {a.name} → {r.rel_type} → {b.name} ({r.note})")

    st.subheader("Objects")
    if not mind.objects.objects:
        st.info("No objects.")
    else:
        for o in mind.objects.objects.values():
            owner = mind.bridge.entities.get(o.owner_entity_id)
            attached = mind.bridge.entities.get(o.attached_to)
            st.write(
                f"• {(o.colour + ' ') if o.colour else ''}{o.label} | state={o.state} | "
                f"owner={owner.name if owner else '—'} | attached={attached.name if attached else '—'} | "
                f"last_place={o.location or 'unknown'}"
            )

    st.subheader("External Day Events (truth replay buffer)")
    if not mind.day_external_events:
        st.info("None yet today.")
    else:
        for ev in mind.day_external_events[-30:]:
            st.write(ev)

# ============================================================
# TAB 3: SLEEP & REFLECTION
# ============================================================
with tab_reflection:
    st.subheader("Sleep Report (Pattern 1 replay)")
    if not mind.last_sleep_report:
        st.info("No sleep run yet.")
    else:
        st.json(mind.last_sleep_report)

    st.subheader("Reflection clusters (visual reoccurrence)")
    clusters = mind.sleep_engine.reflection.last_clusters
    if not clusters:
        st.info("No clusters yet (run sleep).")
    else:
        for c in clusters:
            with st.expander(f"{c.label} (strength={c.strength:.2f})"):
                for n in c.nodes:
                    st.write(f"- {n}")

# ============================================================
# TAB 4: BRAIN GRAPH
# ============================================================
with tab_graph:
    st.subheader("World Graph")
    dot = build_brain_dot(mind)
    st.graphviz_chart(dot, use_container_width=True)
    with st.expander("DOT source"):
        st.code(dot)