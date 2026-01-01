import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO – Mind Inspector", layout="wide")

# -------------------------------
# Load mind from session
# -------------------------------
if "mind" not in st.session_state:
    st.error("Mind not initialised. Go back to the main page first.")
    st.stop()

mind: A7DOMind = st.session_state.mind

st.title("🧠 A7DO Mind Inspector")
st.caption("Live inspection of internal cognitive layers")

# -------------------------------
# High-level state
# -------------------------------
st.subheader("System State")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Entities", len(mind.bridge.entities))
c2.metric("Objects", len(mind.objects.objects))
c3.metric("Relationships", len(mind.relationships.relations))
c4.metric("Events", len(mind.events.events))
c5.metric("Experiences", len(mind.experiences.experiences))

# -------------------------------
# Awaiting state (VERY important)
# -------------------------------
st.subheader("Awaiting / Cognitive Hold State")
if mind.awaiting:
    st.warning("Mind is awaiting input")
    st.json(mind.awaiting)
else:
    st.success("No pending cognitive state")

st.divider()

# -------------------------------
# ENTITIES
# -------------------------------
st.subheader("Entities")
if not mind.bridge.entities:
    st.info("No entities yet.")
else:
    for e in mind.bridge.entities.values():
        with st.expander(f"{e.name} ({e.kind})"):
            st.write(f"**Entity ID:** {e.entity_id}")
            st.write(f"**Confidence:** {e.confidence}")
            st.write(f"**Origin:** {e.origin}")
            st.write(f"**Created:** {e.created_at}")

# -------------------------------
# OBJECTS
# -------------------------------
st.subheader("Objects")
if not mind.objects.objects:
    st.info("No objects yet.")
else:
    for o in mind.objects.objects.values():
        with st.expander(f"{(o.colour + ' ') if o.colour else ''}{o.label}"):
            st.write(f"**Object ID:** {o.object_id}")
            st.write(f"**State:** {o.state}")
            st.write(f"**Owner:** {mind.bridge.entities[o.owner_entity_id].name if o.owner_entity_id and o.owner_entity_id in mind.bridge.entities else '—'}")
            st.write(f"**Attached To:** {mind.bridge.entities[o.attached_to].name if o.attached_to and o.attached_to in mind.bridge.entities else '—'}")
            st.write(f"**Last Location:** {o.location or 'unknown'}")
            st.write(f"**Created:** {o.created_at}")
            st.write(f"**Last Seen:** {o.last_seen}")

# -------------------------------
# RELATIONSHIPS
# -------------------------------
st.subheader("Relationships")
if not mind.relationships.relations:
    st.info("No relationships yet.")
else:
    for r in mind.relationships.relations:
        a = mind.bridge.entities.get(r.subject_id)
        b = mind.bridge.entities.get(r.object_id)
        if not a or not b:
            continue
        st.write(f"• **{a.name}** → *{r.rel_type}* → **{b.name}**  ({r.note})")

# -------------------------------
# EVENTS
# -------------------------------
st.subheader("Events (latest 30)")
if not mind.events.events:
    st.info("No events yet.")
else:
    for ev in reversed(mind.events.events[-30:]):
        with st.expander(f"[{ev.place or '—'}] {ev.description[:60]}"):
            st.write(f"**Description:** {ev.description}")
            st.write(f"**Participants:** {', '.join(mind.bridge.entities[eid].name for eid in ev.participants if eid in mind.bridge.entities)}")
            st.write(f"**Timestamp:** {ev.timestamp}")
            if ev.smells:
                st.write(f"**Smells:** {', '.join(ev.smells)}")
            if ev.sounds:
                st.write(f"**Sounds:** {', '.join(ev.sounds)}")

# -------------------------------
# EXPERIENCES
# -------------------------------
st.subheader("Experiences")
if not mind.experiences.experiences:
    st.info("No experiences yet.")
else:
    for ex in mind.experiences.experiences.values():
        with st.expander(f"{ex.object_label} @ {ex.place}"):
            st.write(f"**Experience ID:** {ex.experience_id}")
            st.write(f"**Interaction:** {ex.interaction or '—'}")
            st.write(f"**Visual:** {ex.visual or '—'}")
            st.write(f"**Emotion:** {ex.emotion or '—'}")
            st.write(f"**Action:** {ex.action or '—'}")
            st.write(f"**Preference:** {ex.preference or '—'}")
            st.write(f"**Created:** {ex.created_at}")