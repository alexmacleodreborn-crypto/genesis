"""
Streamlit Front-End for A7DO

This file is the main entry point for interacting with the A7DO cognitive system.
It provides:
- Chat interface
- Character panel (identity, emotion, development)
- Memory summary
- Recent memory viewer
- Internal state snapshot

All cognitive logic lives in the a7do/ package.
"""

import streamlit as st

# Import the mind + memory systems
from a7do.mind import A7DOMind
from a7do.memory import MemorySystem


# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------

@st.cache_resource
def init_system():
    """
    Create the Mind and Memory systems once per session.
    """
    mind = A7DOMind()
    memory = MemorySystem()
    mind.attach_memory(memory)
    return mind, memory


mind, memory = init_system()


# -----------------------------------------------------------------------------
# Page Layout
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="A7DO Cognitive System",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 A7DO Cognitive System")
st.write("A modular artificial mind with identity, emotion, memory, development, and internal reasoning.")


# -----------------------------------------------------------------------------
# Sidebar: Character Panel
# -----------------------------------------------------------------------------

st.sidebar.header("Character Panel")
panel_text = mind.build_character_panel()
st.sidebar.markdown(panel_text)

st.sidebar.header("Memory Summary")
st.sidebar.markdown(memory.build_memory_summary())


# -----------------------------------------------------------------------------
# Main Chat Interface
# -----------------------------------------------------------------------------

st.subheader("Chat with A7DO")

user_input = st.text_input("Your message:", "")

if st.button("Send"):
    if user_input.strip():
        result = mind.process_question(user_input)

        st.markdown("### A7DO's Response")
        st.write(result["answer"])

        # Internal state snapshot
        with st.expander("Internal State Snapshot"):
            st.json(mind.export_state())

    else:
        st.warning("Please enter a message before sending.")


# -----------------------------------------------------------------------------
# Memory Viewer
# -----------------------------------------------------------------------------

st.subheader("Recent Memories")

recent = memory.export_recent(30)
for m in recent:
    st.markdown(
        f"**[{m['step_index']}] {m['kind']}** — {m['content']}  \n"
        f"*Tags:* {', '.join(m['tags'])}  \n"
        f"*Emotion:* {m['emotion_valence']} ({m['emotion_label']})"
    )
    st.markdown("---")
