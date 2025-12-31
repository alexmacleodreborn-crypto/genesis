import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(
    page_title="A7DO – Mind Inspector",
    layout="wide"
)

st.title("🔍 A7DO Mind Inspector")

# -------------------------------------------------
# Session
# -------------------------------------------------

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind: A7DOMind = st.session_state.mind

# -------------------------------------------------
# Helper: get memory frames safely
# -------------------------------------------------

def get_event_frames(memory, limit=50):
    """
    Defensive accessor for event/memory frames.
    Supports multiple memory implementations.
    """
    # Case 1: legacy .frames
    if hasattr(memory, "frames"):
        try:
            frames = memory.frames
            return frames[-limit:] if frames else []
        except Exception:
            pass

    # Case 2: common containers
    for attr in ("items", "entries", "events"):
        if hasattr(memory, attr):
            try:
                frames = getattr(memory, attr)
                return frames[-limit:] if frames else []
            except Exception:
                pass

    # Case 3: method-based access
    if hasattr(memory, "recent") and callable(memory.recent):
        try:
            return memory.recent(n=limit) or []
        except Exception:
            pass

    # Case 4: iterable memory
    try:
        frames = list(memory)
        return frames[-limit:]
    except Exception:
        pass

    return []

# -------------------------------------------------
# Event / Memory stream
# -------------------------------------------------

st.subheader("📜 Event / Memory Stream")

event_memory = mind.events  # alias to memory
frames = get_event_frames(event_memory)

if not frames:
    st.info("No events recorded yet.")
else:
    for i, frame in enumerate(reversed(frames), start=1):
        with st.expander(f"Event {len(frames) - i + 1}", expanded=False):
            if isinstance(frame, dict):
                st.json(frame)
            else:
                # Best-effort display
                st.write(frame)

# -------------------------------------------------
# Pending Entities
# -------------------------------------------------

st.subheader("🧩 Pending Entities")

pending = getattr(mind.bridge, "pending", {})
if not pending:
    st.caption("No pending entities.")
else:
    for p in pending.values():
        st.write(
            f"• **{p.name}** "
            f"(guess={p.kind_guess}, confidence={p.confidence:.2f}, seen={p.count})"
        )

# -------------------------------------------------
# Entity Graph
# -------------------------------------------------

st.subheader("🗂️ Entity Graph")

entities = getattr(mind.bridge, "entities", {})
if not entities:
    st.caption("No promoted entities yet.")
else:
    for e in entities.values():
        st.markdown(
            f"""
**{e.name}**  
Type: `{e.kind}`  
Owner: `{e.owner_name or "—"}`  
Aliases: {", ".join(e.aliases) if e.aliases else "—"}
"""
        )

# -------------------------------------------------
# System Signal
# -------------------------------------------------

st.subheader("📡 System Signal")

signal = getattr(mind, "_last_signal", None)
if signal:
    st.json(signal)
else:
    st.caption("No system signals emitted yet.")