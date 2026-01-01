import streamlit as st
from a7do.mind import A7DOMind
from a7do.graph import build_brain_dot

st.set_page_config(page_title="A7DO Cognitive Interface", layout="wide")

# -------------------------------------------------
# Safe initialisation (handles hot reload issues)
# -------------------------------------------------
def get_mind():
    if "mind" not in st.session_state:
        st.session_state.mind = A7DOMind()
        return st.session_state.mind

    mind = st.session_state.mind

    # If architecture changed mid-session, re-init safely
    if not hasattr(mind, "identity"):
        st.session_state.mind = A7DOMind()
        return st.session_state.mind

    return mind


mind: A7DOMind = get_mind()

if "chat" not in st.session_state:
    st.session_state.chat = []

# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown("# 🧠 A7DO Cognitive Interface")
st.caption("Entities · Objects · Relationships · Events · Experiences · Recall")

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.subheader("Identity")

    if hasattr(mind, "identity") and hasattr(mind.identity, "panel_markdown"):
        st.markdown(mind.identity.panel_markdown())
    else:
        st.warning("Identity layer not initialised")

    st.divider()
    st.subheader("System State")

    st.metric("Entities", len(mind.bridge.entities))
    st.metric("Objects", len(mind.objects.objects))
    st.metric("Relationships", len(mind.relationships.relations))
    st.metric("Events", len(mind.events.events))
    st.metric("Experiences", len(mind.experiences.experiences))

    st.divider()
    st.subheader("Quick prompts")
    st.write("• My name is Alex Macleod")
    st.write("• Xena is my dog")
    st.write("• We are at the park with the red ball")
    st.write("• Where is the red ball?")
    st.write("• We are at the park and there is a swing")

# -------------------------------------------------
# Tabs
# -------------------------------------------------
tab_chat, tab_world, tab_experiences, tab_graph = st.tabs(
    ["💬 Chat", "🌍 World", "📓 Experiences", "🧬 Brain Graph"]
)

# -------------------------------------------------
# CHAT TAB
# -------------------------------------------------
with tab_chat:
    st.subheader("Chat")

    user_text = st.text_input("Say something to A7DO:")

    if user_text:
        result = mind.process(user_text)
        st.session_state.chat.append(("You", user_text))
        st.session_state.chat.append(("A7DO", result.get("answer", "—")))

    for who, msg in st.session_state.chat[-40:]:
        if who == "You":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**A7DO:** {msg}")

# -------------------------------------------------
# WORLD TAB
# -------------------------------------------------
with tab_world:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Entities")
        if not mind.bridge.entities:
            st.info("No entities yet.")
        for e in mind.bridge.entities.values():
            st.write(f"• {e.name} ({e.kind}) conf={e.confidence:.2f} origin={e.origin}")

        st.subheader("Relationships")
        if not mind.relationships.relations:
            st.info("No relationships yet.")
        for r in mind.relationships.relations:
            a = mind.bridge.entities.get(r.subject_id)
            b = mind.bridge.entities.get(r.object_id)
            if a and b:
                st.write(f"• {a.name} → {r.rel_type} → {b.name} ({r.note})")

    with c2:
        st.subheader("Objects")
        if not mind.objects.objects:
            st.info("No objects yet.")
        for o in mind.objects.objects.values():
            owner = mind.bridge.entities.get(o.owner_entity_id)
            attached = mind.bridge.entities.get(o.attached_to)
            st.write(
                f"• {(o.colour + ' ') if o.colour else ''}{o.label} | "
                f"state={o.state} | "
                f"owner={owner.name if owner else '—'} | "
                f"attached={attached.name if attached else '—'} | "
                f"last_place={o.location or 'unknown'}"
            )

        st.subheader("Events (latest 20)")
        for ev in reversed(mind.events.events[-20:]):
            st.write(f"• [{ev.place or '—'}] {ev.description}")
            if ev.smells:
                st.caption(f"smells: {', '.join(ev.smells)}")
            if ev.sounds:
                st.caption(f"sounds: {', '.join(ev.sounds)}")

# -------------------------------------------------
# EXPERIENCES TAB
# -------------------------------------------------
with tab_experiences:
    st.subheader("Structured Experiences")

    if not mind.experiences.experiences:
        st.info("No experiences yet.")
    else:
        for ex in reversed(list(mind.experiences.experiences.values())[-30:]):
            with st.expander(f"{ex.object_label} @ {ex.place}"):
                st.write(f"Interaction: {ex.interaction or '—'}")
                st.write(f"Visual: {ex.visual or '—'}")
                st.write(f"Emotion: {ex.emotion or '—'}")
                st.write(f"Action: {ex.action or '—'}")
                st.write(f"Preference: {ex.preference or '—'}")

# -------------------------------------------------
# BRAIN GRAPH TAB
# -------------------------------------------------
with tab_graph:
    st.subheader("Brain-like World Graph")

    dot = build_brain_dot(mind)
    st.graphviz_chart(dot, use_container_width=True)

    with st.expander("DOT source"):
        st.code(dot)