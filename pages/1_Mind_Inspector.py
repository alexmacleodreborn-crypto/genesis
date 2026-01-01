import streamlit as st

st.set_page_config(page_title="A7DO Mind Inspector", layout="wide")

st.title("🧠 A7DO — Mind Inspector")

mind = st.session_state.get("mind")
schedule = st.session_state.get("schedule")

if not mind or not schedule:
    st.info("Mind or Schedule not initialised yet.")
    st.stop()


# -------------------------------------------------
# Schedule / Consciousness State
# -------------------------------------------------
st.subheader("🕰️ Consciousness State")

status = schedule.status()

if not status["started"]:
    st.warning("Mind is dormant — waiting for schedule start.")
elif status["asleep"]:
    st.info("Mind is asleep (reflection / consolidation).")
elif status["completed"]:
    st.success("Day completed — ready to advance.")
else:
    st.success("Mind is awake and processing scheduled events.")

cols = st.columns(4)
cols[0].metric("Day", status["day"])
cols[1].metric("Awake Used", status["awake_used"])
cols[2].metric("Awake Remaining", status["awake_remaining"])
cols[3].metric("Events Queued", status["events_count"])

st.divider()


# -------------------------------------------------
# Identity
# -------------------------------------------------
st.subheader("🧍 Identity")

st.markdown(mind.identity.panel_markdown())


# -------------------------------------------------
# Entities
# -------------------------------------------------
st.subheader("👥 Entities")

if not mind.bridge.entities:
    st.info("No entities yet.")
else:
    for e in mind.bridge.entities.values():
        st.write(
            f"- **{e.name}** "
            f"(kind={e.kind}, confidence={e.confidence:.2f}, origin={e.origin})"
        )


# -------------------------------------------------
# Relationships
# -------------------------------------------------
st.subheader("🔗 Relationships")

if not mind.relationships.relations:
    st.info("No relationships.")
else:
    for r in mind.relationships.relations:
        a = mind.bridge.entities.get(r.subject_id)
        b = mind.bridge.entities.get(r.object_id)
        if a and b:
            st.write(f"- {a.name} → **{r.rel_type}** → {b.name} ({r.note})")


# -------------------------------------------------
# Objects
# -------------------------------------------------
st.subheader("🧸 Objects")

if not mind.objects.objects:
    st.info("No objects.")
else:
    for o in mind.objects.objects.values():
        owner = mind.bridge.entities.get(o.owner_entity_id)
        attached = mind.bridge.entities.get(o.attached_to)
        st.write(
            f"- {(o.colour + ' ') if o.colour else ''}{o.label} | "
            f"state={o.state} | "
            f"owner={owner.name if owner else '—'} | "
            f"attached={attached.name if attached else '—'} | "
            f"location={o.location or 'unknown'}"
        )


# -------------------------------------------------
# External Day Events (Reflection Source)
# -------------------------------------------------
st.subheader("📜 External Day Events (Reflection Source)")

if not mind.day_external_events:
    st.info("No external events recorded today.")
else:
    for i, ev in enumerate(mind.day_external_events[-20:], start=1):
        st.write(f"**{i}.** {ev}")


# -------------------------------------------------
# Sleep / Reflection Status
# -------------------------------------------------
st.subheader("🌙 Last Sleep Report")

if not mind.last_sleep_report:
    st.info("No sleep cycle has run yet.")
else:
    st.json(mind.last_sleep_report)