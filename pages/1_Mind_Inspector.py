import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("🧠 Mind Inspector")

# --------------------------------------------------
# Recover shared state
# --------------------------------------------------

mind = st.session_state.get("mind")
childhood = st.session_state.get("childhood")

if not mind:
    st.error("Mind not initialised yet.")
    st.stop()

# --------------------------------------------------
# Cognitive Timeline
# --------------------------------------------------

st.header("📜 Cognitive Timeline")
for e in mind.events:
    st.code(e)

# --------------------------------------------------
# Reasoning Signals (Z–Σ)
# --------------------------------------------------

st.header("🧭 Last Mind Path")
st.write(" → ".join(getattr(mind, "path", [])) or "No path recorded yet.")

st.header("✅ Last Coherence")
st.json(getattr(mind, "last_coherence", None) or {"info": "No coherence yet."})

st.header("📈 Reasoning Signals (Z–Σ)")
signals = getattr(mind, "last_signals", None)
if not signals:
    st.info("No reasoning signals recorded yet.")
else:
    st.json({"mode": signals.get("mode", "unknown")})
    # keep your plotting code here using signals["z"] and signals["sigma"]
    
signals = getattr(mind, "last_signals", None)

st.header("📈 Reasoning Signals (Z–Σ)")

if signals:
    z = signals["z"]
    sigma = signals["sigma"]
    mode = signals.get("mode", "unknown")

    fig, ax = plt.subplots(2, 1, figsize=(9, 5))

    ax[0].plot(z, label="Z (Inhibition)")
    ax[0].plot(sigma, label="Σ (Exploration)")
    ax[0].legend()
    ax[0].set_title(f"Constraint vs Exploration ({mode})")

    coherence = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
    ax[1].plot(coherence)
    ax[1].axhline(0.6, linestyle="--", color="yellow")
    ax[1].set_title("Coherence Gate (Safe to Speak)")

    st.pyplot(fig)
else:
    st.info("No reasoning signals recorded yet.")

# --------------------------------------------------
# Childhood Learning Inspector
# --------------------------------------------------

st.header("🧒 Childhood Learning")

if childhood:
    summary = childhood.summary()

    st.metric(
        "Active Learning Burst",
        "Yes" if summary["active"] else "No"
    )

    if summary["active"]:
        st.metric("Seconds Remaining", summary["seconds_remaining"])

    if summary["imprints"]:
        st.subheader("Recent Imprints")
        st.json(summary["imprints"])
    else:
        st.info("No childhood imprints yet.")
else:
    st.info("Childhood module not initialised.")