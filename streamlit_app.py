import streamlit as st
from a7do.mind import A7DOMind

# -------------------------------------------------
# App setup
# -------------------------------------------------
st.set_page_config(
    page_title="A7DO Cognitive Interface",
    layout="wide",
)

st.title("🧠 A7DO Cognitive Interface")

# -------------------------------------------------
# Initialise mind
# -------------------------------------------------
if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind: A7DOMind = st.session_state.mind

# -------------------------------------------------
# Sidebar — Identity & World State
# -------------------------------------------------
with st.sidebar:
    st.header("🧍 Identity")

    speaker = mind.language.speaker() or getattr(mind.identity, "creator", "Unknown")
    st.markdown(f"**Speaker:** {speaker}")
    st.markdown("**Agent:** A7DO")

    st.divider()

    st.header("🌍 World State")

    st.markdown(f"**People / Pets / Agent:** {len(mind.bridge.entities)}")
    st.markdown(f"**Objects:** {len(mind.objects.objects)}")
    st.markdown(f"**Events:** {len(mind.events.events)}")

    st.divider()

    if st.checkbox("Show Raw Entities"):
        for ent in mind.bridge.entities.values():
            st.markdown(
                f"- **{ent.name}** "
                f"({ent.kind}, conf={ent.confidence:.2f}, origin={ent.origin})"
            )

    if st.checkbox("Show Objects"):
        for obj in mind.objects.objects.values():
            st.markdown(
                f"- **{obj.label}**"
                f"{' (' + obj.colour + ')' if obj.colour else ''} | "
                f"state={obj.state} | "
                f"owner={obj.owner_entity_id} | "
                f"attached={obj.attached_to}"
            )

# -------------------------------------------------
# Main chat interface
# -------------------------------------------------
st.subheader("💬 Interaction")

user_text = st.text_input("Say something to A7DO:")

if user_text:
    result = mind.process(user_text)
    st.session_state.last_result = result

# -------------------------------------------------
# Response
# -------------------------------------------------
if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown("### 🗨️ A7DO")
    st.markdown(res.get("answer", "—"))

# -------------------------------------------------
# Event timeline
# -------------------------------------------------
st.divider()
st.subheader("🕒 Event Timeline")

if mind.events.events:
    for i, ev in enumerate(reversed(mind.events.events), start=1):
        with st.expander(f"Event {len(mind.events.events) - i + 1}"):
            st.markdown(f"**Description:** {ev.description}")
            st.markdown(f"**Place:** {ev.place or '—'}")
            st.markdown(f"**Time:** {ev.timestamp:.2f}")

            if ev.participants:
                st.markdown("**Participants:**")
                for pid in ev.participants:
                    ent = mind.bridge.entities.get(pid)
                    if ent:
                        st.markdown(f"- {ent.name} ({ent.kind})")

            if ev.smells:
                st.markdown(f"**Smells:** {', '.join(ev.smells)}")
            if ev.sounds:
                st.markdown(f"**Sounds:** {', '.join(ev.sounds)}")
else:
    st.info("No events recorded yet.")

# -------------------------------------------------
# Relationships
# -------------------------------------------------
st.divider()
st.subheader("🔗 Relationships")

if mind.relationships.relations:
    for rel in mind.relationships.relations:
        a = mind.bridge.entities.get(rel.subject_id)
        b = mind.bridge.entities.get(rel.object_id)
        if a and b:
            st.markdown(
                f"- **{a.name}** → *{rel.rel_type}* → **{b.name}**"
            )
else:
    st.info("No relationships recorded.")

# -------------------------------------------------
# Objects recall
# -------------------------------------------------
st.divider()
st.subheader("🧸 Objects")

if mind.objects.objects:
    for obj in mind.objects.objects.values():
        owner = mind.bridge.entities.get(obj.owner_entity_id)
        attached = mind.bridge.entities.get(obj.attached_to)

        st.markdown(
            f"- **{obj.label}**"
            f"{' (' + obj.colour + ')' if obj.colour else ''} | "
            f"state={obj.state} | "
            f"owner={owner.name if owner else '—'} | "
            f"attached={attached.name if attached else '—'}"
        )
else:
    st.info("No objects yet.")