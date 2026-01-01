import streamlit as st
from a7do.mind import A7DOMind
from a7do.graph import build_brain_dot

st.set_page_config(page_title="A7DO Cognitive Interface", layout="wide")

# ---------- init ----------
if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()
if "chat" not in st.session_state:
    st.session_state.chat = []

mind: A7DOMind = st.session_state.mind

# ---------- header ----------
st.markdown("# 🧠 A7DO Cognitive Interface")
st.caption("Entities · Objects · Relationships · Events · Experiences · Recall")

# ---------- sidebar ----------
with st.sidebar:
    st.subheader("Identity")
    st.markdown(mind.identity.panel_markdown())

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
    st.write("• ball")
    st.write("• Where is the red ball?")
    st.write("• We are at the park and there is a swing")

# ---------- tabs ----------
tab_chat, tab_world, tab_experiences, tab_graph = st.tabs(
    ["💬 Chat", "🌍 World", "📓 Experiences", "🧬 Brain Graph"]
)

# ==========================
# CHAT TAB
# ==========================
with tab_chat:
    st.subheader("Chat")
    user_text = st.text_input("Say something to A7DO:")

    if user_text:
        result = mind.process(user_text)
        st.session_state.chat.append(("You", user_text))
        st.session_state.chat.append(("A7DO", result.get("answer", "—")))

    # render chat
    for who, msg in st.session_state.chat[-30:]:
        if who == "You":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**A7DO:** {msg}")

# ==========================
# WORLD TAB
# ==========================
with tab_world:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Entities")
        for e in mind.bridge.entities.values():
            st.write(f"• {e.name} ({e.kind})  conf={e.confidence:.2f}  origin={e.origin}")

        st.subheader("Relationships")
        if not mind.relationships.relations:
            st.info("No relationships yet.")
        for r in mind.relationships.relations:
            a = mind.bridge.entities.get(r.subject_id)
            b = mind.bridge.entities.get(r.object_id)
            if a and b:
                st.write(f"• {a.name} → {r.rel_type} → {b.name}  ({r.note})")

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
        if not mind.events.events:
            st.info("No events yet.")
        for ev in reversed(mind.events.events[-20:]):
            st.write(f"• [{ev.place or '—'}] {ev.description}")
            if ev.smells:
                st.caption(f"smells: {', '.join(ev.smells)}")
            if ev.sounds:
                st.caption(f"sounds: {', '.join(ev.sounds)}")

# ==========================
# EXPERIENCES TAB
# ==========================
with tab_experiences:
    st.subheader("Structured Experiences")
    if not mind.experiences.experiences:
        st.info("No experiences yet. Trigger one by mentioning place + new object (e.g., park + swing).")

    for ex in reversed(list(mind.experiences.experiences.values())[-30:]):
        with st.expander(f"{ex.object_label} @ {ex.place}"):
            st.write(f"Interaction: {ex.interaction or '—'}")
            st.write(f"Looked like: {ex.visual or '—'}")
            st.write(f"Felt: {ex.emotion or '—'}")
            st.write(f"Did: {ex.action or '—'}")
            st.write(f"Liked: {ex.preference or '—'}")

# ==========================
# GRAPH TAB
# ==========================
with tab_graph:
    st.subheader("Brain-like Graph (World Model)")
    dot = build_brain_dot(mind)
    st.graphviz_chart(dot, use_container_width=True)
    with st.expander("DOT source (debug)"):
        st.code(dot)