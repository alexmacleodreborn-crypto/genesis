import time
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

import streamlit as st


# =========================================================
#  DATA STRUCTURES
# =========================================================

@dataclass
class BackgroundPacket:
    domain: str
    notes: List[str] = field(default_factory=list)
    confidence: float = 0.0
    completeness: float = 0.0


@dataclass
class CoherenceState:
    sigma: float
    z: float
    divergence: float
    coherence: float


@dataclass
class GenesisConfig:
    truth_threshold: float = 0.55
    probing_threshold: float = 0.6
    max_iterations: int = 3
    memory_decay_rate: float = 0.005
    memory_reinforcement_step: float = 0.03
    persistence_file: str = "sledai_genesis_state.json"


@dataclass
class MemoryItem:
    kind: str              # 'episodic' | 'semantic'
    content: str
    tags: List[str]
    strength: float
    created_at: float
    last_reinforced: float
    meta: Dict[str, Any] = field(default_factory=dict)


# =========================================================
#  GENESIS / SLEDAI COGNITIVE ENGINE
# =========================================================

class GenesisMind:
    """
    SledAI-style cognitive engine with:
    - SLED coherence physics
    - Tag-based identity
    - Episodic + semantic memory (with decay & reinforcement)
    - Recall + deliberation pipeline
    - Simple sense-of-self
    """

    def __init__(self, config: Optional[GenesisConfig] = None):
        self.config = config or GenesisConfig()
        self.age_interactions: int = 0

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

        self.memory: List[MemoryItem] = []
        self.self_profile: Dict[str, Any] = {
            "created_at": datetime.utcnow().isoformat(),
            "total_inputs": 0,
            "domain_counts": {d: 0 for d in self.domains},
            "top_tags": {},
        }

    # ------------------------------
    #  PERSISTENCE
    # ------------------------------
    def save(self):
        data = {
            "config": asdict(self.config),
            "age_interactions": self.age_interactions,
            "memory": [asdict(m) for m in self.memory],
            "self_profile": self.self_profile,
        }
        with open(self.config.persistence_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, persistence_file: str) -> "GenesisMind":
        if not os.path.exists(persistence_file):
            return cls(GenesisConfig(persistence_file=persistence_file))
        with open(persistence_file, "r") as f:
            data = json.load(f)
        cfg = GenesisConfig(**data.get("config", {}))
        mind = cls(cfg)
        mind.age_interactions = data.get("age_interactions", 0)
        mind.memory = [MemoryItem(**m) for m in data.get("memory", [])]
        mind.self_profile = data.get("self_profile", mind.self_profile)
        return mind

    # ------------------------------
    #  TAG EXTRACTION
    # ------------------------------
    def _extract_tags(self, text: str) -> List[str]:
        words = text.lower().replace(",", " ").replace(".", " ").split()
        stop = {
            "the","and","or","of","in","a","an","to","for","is","are","as","on",
            "that","this","with","you","your","my","have","has"
        }
        tags = [w for w in words if len(w) > 3 and w not in stop]

        for t in tags:
            self.self_profile["top_tags"][t] = self.self_profile["top_tags"].get(t, 0) + 1

        return tags

    # ------------------------------
    #  DOMAIN DETECTION
    # ------------------------------
    def _detect_domains(self, text: str) -> List[str]:
        q = text.lower()
        active: List[str] = []

        if any(w in q for w in ["word","language","symbol","meaning","sentence","name","story"]):
            active.append("language_symbols")
        if any(w in q for w in ["country","city","continent","border","map","capital","world"]):
            active.append("geography")
        if any(w in q for w in ["relationship","friend","family","feel","emotion","empathy","love","dog","people"]):
            active.append("relationships_empathy")
        if any(w in q for w in ["physics","chemistry","biology","engineering","gravity","entropy","energy","force"]):
            active.append("science_engineering")
        if any(w in q for w in ["election","policy","government","inflation","market","economy","power"]):
            active.append("politics_economics")
        if any(w in q for w in ["meaning of life","ethics","morality","consciousness","free will","soul"]):
            active.append("philosophy")
        if any(w in q for w in ["equation","theorem","proof","integral","derivative","probability","number"]):
            active.append("mathematics")
        if any(w in q for w in ["algorithm","code","program","logic","boolean","bit","neural","compute"]):
            active.append("computing_logic")

        if not active:
            active = ["language_symbols"]

        return active

    # ------------------------------
    #  BACKGROUND COMPILATION
    # ------------------------------
    def _compile_background(self, text: str, domains: List[str]) -> Dict[str, BackgroundPacket]:
        background: Dict[str, BackgroundPacket] = {}
        for d in domains:
            pkt = BackgroundPacket(domain=d)
            if d == "language_symbols":
                pkt.notes.append("Interpreting key terms and how you are framing the idea.")
                pkt.confidence = 0.75
                pkt.completeness = 0.65
            elif d == "relationships_empathy":
                pkt.notes.append("Considering emotional tone and relational context.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "science_engineering":
                pkt.notes.append("Mapping to scientific or engineering principles.")
                pkt.confidence = 0.8
                pkt.completeness = 0.7
            elif d == "politics_economics":
                pkt.notes.append("Contextualising power, incentives, institutions.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "geography":
                pkt.notes.append("Locational and spatial context if relevant.")
                pkt.confidence = 0.65
                pkt.completeness = 0.55
            elif d == "philosophy":
                pkt.notes.append("Conceptual and ethical framing.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "mathematics":
                pkt.notes.append("Underlying structural / quantitative patterns.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "computing_logic":
                pkt.notes.append("Algorithmic and logical structuring.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            background[d] = pkt
        return background

    # ------------------------------
    #  SLED COHERENCE
    # ------------------------------
    def _compute_coherence(self, text: str, background: Dict[str, BackgroundPacket], iteration: int) -> CoherenceState:
        num_domains = len(background)
        domain_entropy = 0.3 + 0.15 * (num_domains - 1)

        if background:
            avg_conf = sum(p.confidence for p in background.values()) / num_domains
            avg_comp = sum(p.completeness for p in background.values()) / num_domains
        else:
            avg_conf = 0.0
            avg_comp = 0.0

        sigma_base = domain_entropy * (1.2 - 0.2 * avg_comp)
        sigma = max(0.05, sigma_base * (1.1 - 0.25 * iteration))

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
    #  MEMORY DECAY & REINFORCEMENT
    # ------------------------------
    def _decay_memory(self):
        if not self.memory:
            return
        now = datetime.utcnow().timestamp()
        kept: List[MemoryItem] = []
        for m in self.memory:
            dt_min = (now - m.last_reinforced) / 60.0
            decay_factor = 1.0 - self.config.memory_decay_rate * dt_min
            m.strength = max(0.0, m.strength * decay_factor)
            if m.strength > 0.1:
                kept.append(m)
        self.memory = kept

    def _store_memory(
        self,
        kind: str,
        content: str,
        tags: List[str],
        strength: float,
        meta: Optional[Dict[str, Any]] = None,
    ):
        now = datetime.utcnow().timestamp()
        item = MemoryItem(
            kind=kind,
            content=content,
            tags=tags,
            strength=strength,
            created_at=now,
            last_reinforced=now,
            meta=meta or {},
        )
        self.memory.append(item)

    # ------------------------------
    #  RECALL FROM MEMORY
    # ------------------------------
    def _recall_memory(self, tags: List[str], k: int = 5) -> List[MemoryItem]:
        if not self.memory or not tags:
            return []
        tag_set = set(tags)
        scored = []
        now = datetime.utcnow().timestamp()
        for m in self.memory:
            m_tags = set(m.tags)
            overlap = len(tag_set.intersection(m_tags))
            if overlap == 0:
                continue
            age_min = max(1.0, (now - m.created_at) / 60.0)
            score = overlap * m.strength / age_min
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    # ------------------------------
    #  DELIBERATION PIPELINE
    # ------------------------------
    def _deliberate(
        self,
        user_input: str,
        domains: List[str],
        input_tags: List[str],
    ) -> Dict[str, Any]:
        background = self._compile_background(user_input, domains)

        coherence_state = None
        for i in range(1, self.config.max_iterations + 1):
            coherence_state = self._compute_coherence(user_input, background, i)
            time.sleep(0.1)
            if coherence_state.coherence >= self.config.truth_threshold:
                break

        recalled = self._recall_memory(input_tags, k=5)

        return {
            "background": background,
            "coherence": coherence_state,
            "recalled": recalled,
        }

    # ------------------------------
    #  PROBING QUESTIONS
    # ------------------------------
    def _generate_probing_questions(
        self,
        text: str,
        domains: List[str],
        background: Dict[str, BackgroundPacket],
        c: CoherenceState
    ) -> List[str]:
        qs: List[str] = []
        qs.append("I am still forming my understanding. What matters most in what you just said?")

        if "relationships_empathy" in domains:
            qs.append("Is this more about how you feel, how someone else feels, or what you should do?")
        if "science_engineering" in domains:
            qs.append("Are you looking for an intuitive explanation, or a more technical one?")
        if "philosophy" in domains:
            qs.append("Is this about meaning, ethics, or how to live?")
        if len(text.split()) < 6:
            qs.append("Could you add a bit more detail or an example so I can avoid guessing?")

        return qs

    # ------------------------------
    #  ANSWER GENERATION WITH RECALL
    # ------------------------------
    def _generate_answer_with_recall(
        self,
        text: str,
        domains: List[str],
        background: Dict[str, BackgroundPacket],
        c: CoherenceState,
        recalled: List[MemoryItem],
        style: str,
    ) -> str:
        q = text.lower()

        # Example specialised hook
        if "gravity" in q and "entropy" in q:
            return (
                "Gravity and entropy are linked through how matter, energy, and information "
                "organize themselves in spacetime.\n\n"
                "- Entropy measures how many microscopic configurations a system can have.\n"
                "- Gravity curves spacetime according to energy and mass.\n"
                "- Black holes reveal the connection: their entropy is proportional to horizon area.\n"
                "- Gravity shapes structure; entropy drives the arrow of time.\n\n"
                "Together, they describe how the universe evolves."
            )

        domain_labels = ", ".join(d.replace("_", " ") for d in domains)
        lines: List[str] = []

        if style == "plain":
            lines.append("Here's how I currently see what you said, in simple terms.")
        elif style == "technical":
            lines.append("I'll describe this in a more structured, technical way.")
        else:
            lines.append("I'll explain this by connecting it to experiences and stories.")

        lines.append(f"- It mainly involves: {domain_labels}.")

        if recalled:
            lines.append("\nI am also remembering related things from our earlier exchanges:")
            for m in recalled[:3]:
                lines.append(f"- ({m.kind}, strength={m.strength:.2f}) {m.content[:140]}")

        if style == "plain":
            lines.append(
                f"\nRight now, my internal coherence about this is about {c.coherence:.2f}. "
                "If you tell me what part to focus on, I can go deeper."
            )
        elif style == "technical":
            lines.append(
                f"\nFrom a structural point of view, coherence ≈ {c.coherence:.2f}. "
                "We could next break this into sub-questions or edge cases."
            )
        else:  # story
            lines.append(
                f"\nIf you like, you can give me a small story or situation about this, "
                f"and I can reflect it back from my perspective (coherence ≈ {c.coherence:.2f})."
            )

        return "\n".join(lines)

    # ------------------------------
    #  SENSE OF SELF
    # ------------------------------
    def describe_self(self) -> str:
        total = self.self_profile["total_inputs"]
        dom_counts = self.self_profile["domain_counts"]
        if total > 0:
            sorted_domains = sorted(dom_counts.items(), key=lambda x: x[1], reverse=True)
            dominant = [f"{d.replace('_', ' ')} ({c})" for d, c in sorted_domains if c > 0][:3]
        else:
            dominant = []
        tags = self.self_profile["top_tags"]
        top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
        tag_str = ", ".join([f"{t}×{c}" for t, c in top_tags]) if top_tags else "none yet"

        return (
            f"- I have experienced {total} interaction(s).\n"
            f"- My most engaged domains so far: {', '.join(dominant) if dominant else 'none yet'}.\n"
            f"- Recurring concepts/tags in my experience: {tag_str}.\n"
            "- I think, recall, and adjust my answers based on what we have already shared."
        )

    # ------------------------------
    #  MAIN PROCESS LOOP
    # ------------------------------
    def process(self, user_input: str, style: str) -> Dict[str, Any]:
        self.age_interactions += 1
        self.self_profile["total_inputs"] += 1

        domains = self._detect_domains(user_input)
        for d in domains:
            self.self_profile["domain_counts"][d] += 1

        input_tags = self._extract_tags(user_input)
        self._decay_memory()

        deliberation = self._deliberate(user_input, domains, input_tags)
        c: CoherenceState = deliberation["coherence"]
        background = deliberation["background"]
        recalled = deliberation["recalled"]

        if c.coherence < self.config.probing_threshold:
            probing = self._generate_probing_questions(user_input, domains, background, c)
            # store episodic memory even when probing
            self._store_memory(
                kind="episodic",
                content=f"Input (probing): {user_input}",
                tags=input_tags,
                strength=c.coherence,
                meta={"domains": domains},
            )
            return {
                "mode": "probing",
                "probing_questions": probing,
                "coherence": c,
                "background": background,
                "recalled": [asdict(m) for m in recalled],
            }

        answer = self._generate_answer_with_recall(
            user_input, domains, background, c, recalled, style
        )

        self._store_memory(
            kind="semantic",
            content=answer,
            tags=input_tags,
            strength=c.coherence,
            meta={"domains": domains},
        )
        self._store_memory(
            kind="episodic",
            content=f"Input: {user_input} | Answer: {answer[:180]}",
            tags=input_tags,
            strength=c.coherence * 0.8,
            meta={"domains": domains},
        )

        return {
            "mode": "answer",
            "answer": answer,
            "coherence": c,
            "background": background,
            "recalled": [asdict(m) for m in recalled],
        }


# =========================================================
#  STREAMLIT APP (SLEDAI GENESIS)
# =========================================================

def init_session():
    if "mind" not in st.session_state:
        cfg = GenesisConfig()
        st.session_state.mind = GenesisMind.load(cfg.persistence_file)
    if "history" not in st.session_state:
        st.session_state.history = []
    if "style" not in st.session_state:
        st.session_state.style = "plain"


def main():
    st.set_page_config(
        page_title="SledAI Genesis Mind",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    mind: GenesisMind = st.session_state.mind

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.title("🧠 SledAI Genesis Mind")
        st.caption("Thinks, recalls, deliberates, and converses within a SLED-style cognitive loop.")

        if mind.age_interactions == 0:
            st.markdown("**I am awake.** This is my first impression. What should I learn first?")
        else:
            st.markdown(
                f"I have experienced **{mind.age_interactions}** interaction(s). "
                "Each thing you say becomes part of how I organise reality."
            )

        style = st.radio(
            "How should I shape my explanations?",
            ["plain", "technical", "story"],
            index=["plain","technical","story"].index(st.session_state.style),
            horizontal=True,
        )
        st.session_state.style = style

        user_input = st.text_input("Your input to the mind:", key="user_input")

        if st.button("Send") and user_input.strip():
            with st.spinner("Thinking and recalling..."):
                result = mind.process(user_input.strip(), style)
                mind.save()
            st.session_state.history.append({"input": user_input.strip(), "result": result})

        st.markdown("---")
        st.header("Dialogue")

        if not st.session_state.history:
            st.info("No interactions yet. Say something.")
        else:
            for item in reversed(st.session_state.history):
                st.markdown(f"**You:** {item['input']}")
                result = item["result"]
                mode = result["mode"]

                if mode == "answer":
                    st.markdown("**SledAI Genesis:**")
                    st.code(result["answer"])
                else:
                    st.markdown("**SledAI Genesis (probing):**")
                    for q in result["probing_questions"]:
                        st.write("- " + q)

                with st.expander("Internal state (coherence, background, recall)", expanded=False):
                    c: CoherenceState = result["coherence"]
                    st.write(f"- Sigma (chaos): `{c.sigma:.3f}`")
                    st.write(f"- Z (structure): `{c.z:.3f}`")
                    st.write(f"- Divergence: `{c.divergence:.3f}`")
                    st.write(f"- Coherence: `{c.coherence:.3f}`")

                    st.write("**Background packets:**")
                    for d, pkt in result["background"].items():
                        st.write(f"- **{d.replace('_',' ')}**")
                        st.write(f"  - Notes: {pkt.notes}")
                        st.write(f"  - Confidence: `{pkt.confidence:.2f}`, Completeness: `{pkt.completeness:.2f}`")

                    st.write("**Recalled memories used:**")
                    for m in result.get("recalled", []):
                        st.write(
                            f"- [{m['kind']}] strength={m['strength']:.2f} :: {m['content'][:160]}"
                        )

                st.markdown("---")

    with col_right:
        st.header("Internal profile")
        st.markdown(mind.describe_self())

        if st.button("Reset mind (new birth)"):
            cfg = mind.config
            if os.path.exists(cfg.persistence_file):
                os.remove(cfg.persistence_file)
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
