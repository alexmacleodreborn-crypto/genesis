import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="Mind Inspector", layout="wide")
st.title("🔍 A7DO — Mind Inspector")

mind: A7DOMind = st.session_state.get("mind")
if not mind:
    st.warning("Mind not initialised yet.")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entities")
    ents = list(getattr(mind.bridge, "entities", {}).values())
    if ents:
        for e in ents:
            st.write(f"- **{e.name}** ({e.kind})")
    else:
        st.write("_None_")

    st.subheader("Confirmed Relationships")
    rels = []
    try:
        rels = mind.relationships.all()
    except Exception:
        rels = []
    if rels:
        for r in rels:
            subj = mind.bridge.entities.get(r.subject_id)
            obj = mind.bridge.entities.get(r.object_id)
            if subj and obj:
                st.write(f"- **{subj.name}** → *{r.rel_type}* → **{obj.name}**")
    else:
        st.write("_None_")

with col2:
    st.subheader("Linguistic Guard (Stage 1)")
    guard = getattr(mind.language, "last_guard", {}) or {}
    accepted = guard.get("accepted", [])
    rejected = guard.get("rejected", [])

    st.write("**Accepted candidates:**")
    if accepted:
        st.write(", ".join(accepted))
    else:
        st.write("_None_")

    st.write("**Rejected tokens:**")
    if rejected:
        for r in rejected:
            st.write(f"- `{r['token']}` — {r['reason']}")
    else:
        st.write("_None_")

    st.subheader("Pending Hypotheses")
    pending = []
    try:
        pending = mind.pending_relationships.list_pending()
    except Exception:
        pending = []
    if pending:
        for p in pending:
            subj = mind.bridge.entities.get(p.subject_id)
            obj = mind.bridge.entities.get(p.object_id)
            if subj and obj:
                st.write(f"- **{obj.name}** might be **{subj.name}**’s dog ({p.confidence:.2f})")
    else:
        st.write("_None_")

    st.subheader("Dormant Hypotheses")
    dormant = []
    try:
        dormant = mind.pending_relationships.list_dormant()
    except Exception:
        dormant = []
    if dormant:
        for p in dormant:
            subj = mind.bridge.entities.get(p.subject_id)
            obj = mind.bridge.entities.get(p.object_id)
            if subj and obj:
                st.write(f"- **{obj.name}** ↔ **{subj.name}** (faded)")
    else:
        st.write("_None_")