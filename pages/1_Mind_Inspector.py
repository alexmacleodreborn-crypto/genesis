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

    st.subheader("Objects (records)")
    if hasattr(mind, "objects") and getattr(mind.objects, "objects", None):
        for oid, rec in mind.objects.objects.items():
            st.write(
                f"- **{rec.label}** (entity={rec.entity_id}) "
                f"attrs={rec.attributes or {}}"
            )
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
    st.write(", ".join(accepted) if accepted else "_None_")

    st.write("**Rejected tokens:**")
    if rejected:
        for r in rejected:
            st.write(f"- `{r['token']}` — {r['reason']}")
    else:
        st.write("_None_")

    st.subheader("Pending Relationship Hypotheses")
    pending_rel = []
    try:
        pending_rel = mind.pending_relationships.list_pending()
    except Exception:
        pending_rel = []
    if pending_rel:
        for p in pending_rel:
            subj = mind.bridge.entities.get(p.subject_id)
            obj = mind.bridge.entities.get(p.object_id)
            if subj and obj:
                st.write(f"- **{obj.name}** might be **{subj.name}**’s dog ({p.confidence:.2f})")
    else:
        st.write("_None_")

    st.subheader("Pending Object Disambiguations")
    if hasattr(mind, "objects") and getattr(mind.objects, "pending", None):
        pend = list(mind.objects.pending.values())
        if pend:
            for p in pend:
                st.write(f"- ({p.stage}) {p.prompt}")
        else:
            st.write("_None_")
    else:
        st.write("_None_")