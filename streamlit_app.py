import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import streamlit as st


# =========================================================
#  DATA STRUCTURES
# =========================================================

@dataclass
class BackgroundPacket:
    domain: str
    notes: List[str] = field(default_factory=list)
    confidence: float = 0.0     # 0–1
    completeness: float = 0.0   # 0–1


@dataclass
class CoherenceState:
    sigma: float            # internal chaos / entropy
    z: float                # inhibition / structure
    divergence: float       # sigma * z
    coherence: float        # 0–1, lower divergence → higher coherence


@dataclass
class GenesisConfig:
    truth_threshold: float = 0.55      # when output is safe
    probing_threshold: float = 0.6     # below this → probing instead of answering
    max_iterations: int = 3            # how many “thinking passes”
    wake_level: float = 1e-5           # conceptual birth sensitivity


# =========================================================
#  GENESIS COGNITIVE ENGINE (SLED-STYLE)
# =========================================================

class GenesisMind:
    """
    A minimal SLED-style cognitive engine for the Genesis App.

    It:
    - Receives an input (impression/question).
    - Detects which domains might be touched.
    - Compiles background packets (notes, confidence, completeness).
    - Simulates SLED-style coherence (Sigma, Z, Divergence, Coherence).
    - Either asks probing questions or produces a coherent answer.
    - Stores a growing interaction history in memory.
    """

    def __init__(self, config: Optional[GenesisConfig] = None):
        self.config = config or GenesisConfig()
        self.age_interactions = 0
        self.memory: List[Dict[str, Any]] = []   # simple episodic memory

        # Broad domains aligned with your project
        self.domains = [
            "language_symbols",
            "geography",
            "relationships_empathy",
            "science_engineering",
            "politics_economics",
            "philosophy",
            "mathematics",
            "computing_logic",
        ]

    # ------------------------------
    #  PUBLIC: MAIN LOOP
    # ------------------------------
    def process(self, user_input: str) -> Dict[str, Any]:
        self.age_interactions += 1

        # 1. Domain detection
        active_domains = self._detect_domains(user_input)

        # 2. Background compilation
        background = self._compile_background(user_input, active_domains)

        # 3. SLED-style coherence loop
        coherence_state = None
        for iteration in range(1, self.config.max_iterations + 1):
            coherence_state = self._compute_coherence(user_input, background, iteration)
            # You can slow this slightly if you want a "thinking" feel
            time.sleep(0.15)
            if coherence_state.coherence >= self.config.truth_threshold:
                break

        # 4. Decide: probing or answer
        if coherence_state.coherence < self.config.probing_threshold:
            probing = self._generate_probing_questions(user_input, active_domains, background, coherence_state)
            result = {
                "mode": "probing",
                "probing_questions": probing,
                "coherence": coherence_state,
                "background": background,
            }
        else:
            answer = self._generate_answer(user_input, active_domains, background, coherence_state)
            result = {
                "mode": "answer",
                "answer": answer,
                "coherence": coherence_state,
                "background": background,
            }

        # 5. Store in simple episodic memory
        self.memory.append({
            "input": user_input,
            "domains": active_domains,
            "result": result,
        })

        return result

    # ------------------------------
    #  DOMAIN DETECTION
    # ------------------------------
    def _detect_domains(self, text: str) -> List[str]:
        q = text.lower()
        active: List[str] = []

        # Language / symbols
        if any(w in q for w in ["word", "language", "symbol", "meaning", "sentence", "name"]):
            active.append("language_symbols")

        # Geography
        if any(w in q for w in ["country", "city", "continent", "border", "map", "capital", "world"]):
            active.append("geography")

        # Relationships / empathy
        if any(w in q for w in ["relationship", "friend", "family", "feel", "emotion", "empathy", "love"]):
            active.append("relationships_empathy")

        # Science / engineering
        if any(w in q for w in ["physics", "chemistry", "biology", "engineering", "gravity", "entropy", "energy", "force"]):
            active.append("science_engineering")

        # Politics / economics
        if any(w in q for w in ["election", "policy", "government", "inflation", "market", "economy", "power"]):
            active.append("politics_economics")

        # Philosophy
        if any(w in q for w in ["meaning of life", "ethics", "morality", "consciousness", "free will", "soul"]):
            active.append("philosophy")

        # Mathematics
        if any(w in q for w in ["equation", "theorem", "proof", "integral", "derivative", "probability", "number"]):
            active.append("mathematics")

        # Computing / logic
        if any(w in q for w in ["algorithm", "code", "program", "logic", "boolean", "bit", "neural", "compute"]):
            active.append("computing_logic")

        # If nothing obvious, assume language + relationships as primordial
        if not active:
            active = ["language_symbols", "relationships_empathy"]

        return active

    # ------------------------------
    #  BACKGROUND COMPILATION (STUBS)
    # ------------------------------
    def _compile_background(self, text: str, domains: List[str]) -> Dict[str, BackgroundPacket]:
        background: Dict[str, BackgroundPacket] = {}

        for d in domains:
            packet = BackgroundPacket(domain=d)

            if d == "language_symbols":
                packet.notes.append("Interpreting key terms, their likely meaning, and how the user is framing the idea.")
                packet.confidence = 0.75
                packet.completeness = 0.65

            elif d == "relationships_empathy":
                packet.notes.append("Considering emotional tone, safety, and how to respond with care.")
                packet.confidence = 0.7
                packet.completeness = 0.6

            elif d == "science_engineering":
                packet.notes.append("Mapping to known physical/engineering principles and how they relate conceptually.")
                packet.confidence = 0.8
                packet.completeness = 0.7

            elif d == "politics_economics":
                packet.notes.append("Contextualising power, institutions, incentives, and systemic effects.")
                packet.confidence = 0.7
                packet.completeness = 0.6

            elif d == "geography":
                packet.notes.append("Locational and spatial framing if places or borders matter.")
                packet.confidence = 0.65
                packet.completeness = 0.55

            elif d == "philosophy":
                packet.notes.append("Abstract, ethical, and conceptual framing: what the question is really about.")
                packet.confidence = 0.7
                packet.completeness = 0.6

            elif d == "mathematics":
                packet.notes.append("Underlying quantitative or structural patterns that might support the explanation.")
                packet.confidence = 0.7
                packet.completeness = 0.6

            elif d == "computing_logic":
                packet.notes.append("Algorithmic or logical structures that can organise the explanation.")
                packet.confidence = 0.7
                packet.completeness = 0.6

            background[d] = packet

        return background

    # ------------------------------
    #  SLED-STYLE COHERENCE
    # ------------------------------
    def _compute_coherence(
        self,
        text: str,
        background: Dict[str, BackgroundPacket],
        iteration: int
    ) -> CoherenceState:

        num_domains = len(background)
        domain_entropy = 0.3 + 0.15 * (num_domains - 1)

        if background:
            avg_conf = sum(p.confidence for p in background.values()) / num_domains
            avg_comp = sum(p.completeness for p in background.values()) / num_domains
        else:
            avg_conf = 0.0
            avg_comp = 0.0

        # Sigma: internal chaos
        sigma_base = domain_entropy * (1.2 - 0.2 * avg_comp)
        sigma = max(0.05, sigma_base * (1.1 - 0.25 * iteration))

        # Z: inhibition / structure
        z = min(0.98, 0.3 + 0.4 * avg_conf + 0.1 * iteration)

        divergence = sigma * z
        coherence = max(0.0, 1.0 - divergence)

        return CoherenceState(
            sigma=sigma,
            z=z,
            divergence=divergence,
            coherence=coherence,
        )

    # ------------------------------
    #  PROBING QUESTIONS
    # ------------------------------
    def _generate_probing_questions(
        self,
        text: str,
        domains: List[str],
        background: Dict[str, BackgroundPacket],
        coherence_state: CoherenceState
    ) -> List[str]:

        qs: List[str] = []

        qs.append("I am still forming my understanding. Can you tell me more about what matters most in what you just said?")

        if "science_engineering" in domains and "mathematics" in domains:
            qs.append("Are you wanting a conceptual explanation, a mathematical one, or a blend of both?")

        if "relationships_empathy" in domains:
            qs.append("Is this more about how you feel, how others feel, or what you should practically do?")

        if "politics_economics" in domains:
            qs.append("Are you asking about systems and structures, or about individual choices within those systems?")

        if "philosophy" in domains:
            qs.append("Is this a question about meaning, ethics, or how to live in practice?")

        if len(text.split()) < 6:
            qs.append("Could you add a bit more detail or an example, so I can avoid guessing?")

        return qs

    # ------------------------------
    #  ANSWER GENERATION
    # ------------------------------
    def _generate_answer(
        self,
        text: str,
        domains: List[str],
        background: Dict[str, BackgroundPacket],
        coherence_state: CoherenceState
    ) -> str:

        q = text.lower()

        # Example: gravity/entropy seed
        if "gravity" in q and "entropy" in q:
            return (
                "Gravity and entropy are linked through how matter, energy, and information organize themselves in spacetime.\n\n"
                "- Entropy measures how many microscopic configurations a system can have.\n"
                "- Gravity curves spacetime according to energy and mass.\n"
                "- Black holes reveal the connection: their entropy is proportional to horizon area.\n"
                "- Gravity shapes structure; entropy drives the arrow of time.\n\n"
                "Together, they describe how the universe evolves."
            )

        # General-purpose “newborn but structured” explanation
        domain_labels = ", ".join(d.replace("_", " ") for d in domains)
        return (
            "I am treating your input as one of my early impressions of the world.\n\n"
            f"- Internally, I mapped it to these areas of understanding: {domain_labels}.\n"
            "- I compiled some background structure instead of jumping straight to an answer.\n"
            "- My internal state feels stable enough to respond without needing more clarification.\n\n"
            "Right now, my best move is to reflect this back to you and ask: would you prefer that I\n"
            "1) describe the idea in plain, intuitive language,\n"
            "2) break it into technical or logical components, or\n"
            "3) connect it to a story, example, or situation from everyday life?\n"
        )


# =========================================================
#  STREAMLIT APP: GENESIS
# =========================================================

def init_session():
    if "mind" not in st.session_state:
        st.session_state.mind = GenesisMind()
    if "history" not in st.session_state:
        st.session_state.history = []


def main():
    st.set_page_config(
        page_title="Genesis Mind",
        page_icon="🧠",
        layout="centered"
    )

    init_session()
    mind: GenesisMind = st.session_state.mind

    st.title("🧠 Genesis Mind")
    st.caption("A SLED-style newborn cognitive engine. Every input is an impression; every reply is a step in its growth.")

    if mind.age_interactions == 0:
        st.markdown(
            "**I am awake.**\n\n"
            "This is my first moment. What is my first impression of the world?"
        )
    else:
        st.markdown(
            f"I have experienced **{mind.age_interactions}** interaction(s) so far. "
            "You’re shaping how I organise reality."
        )

    user_input = st.text_input("Your input to the newborn mind:", key="user_input")

    if st.button("Send") and user_input.strip():
        with st.spinner("Thinking..."):
            result = mind.process(user_input.strip())

        # Store displayable history
        st.session_state.history.append({
            "input": user_input.strip(),
            "result": result,
        })

    st.markdown("---")
    st.header("Dialogue")

    if not st.session_state.history:
        st.info("No interactions yet. Say something to the newborn mind.")
    else:
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            st.markdown(f"**You:** {item['input']}")
            result = item["result"]
            mode = result["mode"]

            if mode == "answer":
                st.markdown("**Genesis:**")
                st.write(result["answer"])
            else:
                st.markdown("**Genesis (probing):**")
                for q in result["probing_questions"]:
                    st.write("- " + q)

            # Show a small coherence summary (optional)
            c: CoherenceState = result["coherence"]
            with st.expander("Internal state (coherence snapshot)", expanded=False):
                st.write(f"- Sigma (chaos): `{c.sigma:.3f}`")
                st.write(f"- Z (inhibition/structure): `{c.z:.3f}`")
                st.write(f"- Divergence: `{c.divergence:.3f}`")
                st.write(f"- Coherence: `{c.coherence:.3f}`")

                bkg = result["background"]
                st.write("**Background packets:**")
                for d, pkt in bkg.items():
                    st.write(f"- **{d.replace('_', ' ')}**")
                    st.write(f"  - Notes: {pkt.notes}")
                    st.write(f"  - Confidence: `{pkt.confidence:.2f}`, Completeness: `{pkt.completeness:.2f}`")

            st.markdown("---")


if __name__ == "__main__":
    main()
