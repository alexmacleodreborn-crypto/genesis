import time
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
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
    wake_level: float = 1e-5
    memory_decay_rate: float = 0.005
    memory_reinforcement_step: float = 0.03
    persistence_file: str = "genesis_mind_state.json"


@dataclass
class MemoryItem:
    kind: str              # 'episodic' | 'semantic'
    content: str           # text description / answer
    tags: List[str]        # extracted concept tags
    strength: float        # 0–1
    created_at: float
    last_reinforced: float
    mindmap_node_id: Optional[int] = None


# =========================================================
#  MIND MAP GRAPH
# =========================================================

class MindMap:
    def __init__(self):
        self.nodes: Dict[int, Dict[str, Any]] = {}
        self.edges: Dict[int, List[Tuple[int, float, str]]] = {}
        self._next_id: int = 0

    def add_node(self, label: str, node_type: str, tags: Optional[List[str]] = None) -> int:
        node_id = self._next_id
        self._next_id += 1
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "tags": list(set(tags or [])),
        }
        self.edges[node_id] = []
        return node_id

    def add_edge(self, a: int, b: int, weight: float = 1.0, relation_type: str = "association"):
        if a not in self.edges:
            self.edges[a] = []
        if b not in self.edges:
            self.edges[b] = []
        self.edges[a].append((b, weight, relation_type))
        self.edges[b].append((a, weight, relation_type))

    def find_relevant_nodes(self, cue_tags: List[str]) -> List[Tuple[int, float]]:
        cue = set(cue_tags)
        scored: List[Tuple[int, float]] = []
        for nid, data in self.nodes.items():
            overlap = len(cue.intersection(set(data.get("tags", []))))
            if overlap > 0:
                scored.append((nid, float(overlap)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def walk_from_node(self, start_id: int, steps: int = 2) -> List[int]:
        path = [start_id]
        current = start_id
        for _ in range(steps):
            neighbors = self.edges.get(current, [])
            if not neighbors:
                break
            neighbors_sorted = sorted(neighbors, key=lambda x: x[1], reverse=True)
            next_id = neighbors_sorted[0][0]
            if next_id in path:
                break
            path.append(next_id)
            current = next_id
        return path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": {k: [(nid, w, r) for (nid, w, r) in v] for k, v in self.edges.items()},
            "_next_id": self._next_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MindMap":
        mm = cls()
        mm.nodes = data.get("nodes", {})
        mm.edges = {int(k): [(nid, w, r) for (nid, w, r) in v] for k, v in data.get("edges", {}).items()}
        mm._next_id = data.get("_next_id", len(mm.nodes))
        return mm


# =========================================================
#  GENESIS COGNITIVE ENGINE
# =========================================================

class GenesisMind:
    """
    Newborn cognitive engine with:
    - SLED-style coherence physics
    - Mind-map graph
    - Episodic + semantic memory (with decay & reinforcement)
    - Simple sense-of-self summary
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

        self.mind_map: MindMap = MindMap()
        self.memory: List[MemoryItem] = []  # episodic + semantic
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
            "mind_map": self.mind_map.to_dict(),
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
        mind.mind_map = MindMap.from_dict(data.get("mind_map", {}))
        mind.memory = [MemoryItem(**m) for m in data.get("memory", [])]
        mind.self_profile = data.get("self_profile", mind.self_profile)
        return mind
    # ------------------------------
    #  CROSSOVER MATRIX (TAG-LEVEL MATCH)
    # ------------------------------
    def _compute_crossover_matrix(self, tags: List[str]) -> Dict[str, Any]:
        """
        Compares current input tags with the mind's own top 10 tags.
        Returns:
          - match_ratio: 0–1
          - core_tags: list of core tags used
          - matched_tags: tags that are in both sets
          - independent_tags: tags not in core set
        """
        # mind's stored tags and counts
        tag_counts = self.self_profile.get("top_tags", {})
        # top 10 tags by frequency
        core_tags = [t for t, _ in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

        if not core_tags:
            # At birth, no core tags yet, so accept everything as exploratory
            matched = []
            independent = tags[:]
            match_ratio = 0.0
        else:
            tag_set = set(tags)
            core_set = set(core_tags)
            matched = list(tag_set.intersection(core_set))
            independent = list(tag_set.difference(core_set))
            # match ratio: how much of the input is aligned with core identity
            match_ratio = len(matched) / max(1, len(tag_set))

        return {
            "match_ratio": match_ratio,
            "core_tags": core_tags,
            "matched_tags": matched,
            "independent_tags": independent,
        }

    # ------------------------------
    #  PUBLIC ENTRY
    # ------------------------------
    def process(self, user_input: str) -> Dict[str, Any]:
        self.age_interactions += 1
        self.self_profile["total_inputs"] += 1

        domains = self._detect_domains(user_input)
        for d in domains:
            self.self_profile["domain_counts"][d] = self.self_profile["domain_counts"].get(d, 0) + 1

        # mind-map tags & memory decay BEFORE new interaction
        tags = self._extract_tags(user_input)
        self._decay_memory()

        background = self._compile_background(user_input, domains)

        # SLED coherence loop
        coherence_state = None
        for i in range(1, self.config.max_iterations + 1):
            coherence_state = self._compute_coherence(user_input, background, i)
            time.sleep(0.15)
            if coherence_state.coherence >= self.config.truth_threshold:
                break

        if coherence_state.coherence < self.config.probing_threshold:
            probing = self._generate_probing_questions(user_input, domains, background, coherence_state)
            result = {
                "mode": "probing",
                "probing_questions": probing,
                "coherence": coherence_state,
                "background": background,
            }
        else:
            answer = self._generate_answer(user_input, domains, background, coherence_state)
            # store semantic & episodic memory + mind-map nodes
            result = {
                "mode": "answer",
                "answer": answer,
                "coherence": coherence_state,
                "background": background,
            }
            self._store_memories(user_input, answer, domains, tags, coherence_state)

        return result

    # ------------------------------
    #  DOMAIN DETECTION
    # ------------------------------
    def _detect_domains(self, text: str) -> List[str]:
        q = text.lower()
        active: List[str] = []

        if any(w in q for w in ["word", "language", "symbol", "meaning", "sentence", "name"]):
            active.append("language_symbols")
        if any(w in q for w in ["country", "city", "continent", "border", "map", "capital", "world"]):
            active.append("geography")
        if any(w in q for w in ["relationship", "friend", "family", "feel", "emotion", "empathy", "love"]):
            active.append("relationships_empathy")
        if any(w in q for w in ["physics", "chemistry", "biology", "engineering", "gravity", "entropy", "energy", "force"]):
            active.append("science_engineering")
        if any(w in q for w in ["election", "policy", "government", "inflation", "market", "economy", "power"]):
            active.append("politics_economics")
        if any(w in q for w in ["meaning of life", "ethics", "morality", "consciousness", "free will", "soul"]):
            active.append("philosophy")
        if any(w in q for w in ["equation", "theorem", "proof", "integral", "derivative", "probability", "number"]):
            active.append("mathematics")
        if any(w in q for w in ["algorithm", "code", "program", "logic", "boolean", "bit", "neural", "compute"]):
            active.append("computing_logic")

        if not active:
            active = ["language_symbols", "relationships_empathy"]

        return active

    # ------------------------------
    #  TAG EXTRACTION
    # ------------------------------
    def _extract_tags(self, text: str) -> List[str]:
        words = text.lower().replace(",", " ").replace(".", " ").split()
        stop = {"the", "and", "or", "of", "in", "a", "an", "to", "for", "is", "are", "as", "on", "that", "this", "with"}
        tags = [w for w in words if len(w) > 3 and w not in stop]
        # update self_profile top tags
        for t in tags:
            self.self_profile["top_tags"][t] = self.self_profile["top_tags"].get(t, 0) + 1
        return tags

    # ------------------------------
    #  BACKGROUND COMPILATION
    # ------------------------------
    def _compile_background(self, text: str, domains: List[str]) -> Dict[str, BackgroundPacket]:
        background: Dict[str, BackgroundPacket] = {}
        for d in domains:
            pkt = BackgroundPacket(domain=d)
            if d == "language_symbols":
                pkt.notes.append("Interpreting key terms and how the user is framing reality.")
                pkt.confidence = 0.75
                pkt.completeness = 0.65
            elif d == "relationships_empathy":
                pkt.notes.append("Considering emotional tone and how to answer with care.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "science_engineering":
                pkt.notes.append("Mapping to known physical/engineering principles and conceptual structure.")
                pkt.confidence = 0.8
                pkt.completeness = 0.7
            elif d == "politics_economics":
                pkt.notes.append("Contextualising power, institutions, incentives, and systemic effects.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "geography":
                pkt.notes.append("Locational and spatial framing if places or borders matter.")
                pkt.confidence = 0.65
                pkt.completeness = 0.55
            elif d == "philosophy":
                pkt.notes.append("Abstract, ethical, and conceptual framing of the underlying question.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "mathematics":
                pkt.notes.append("Underlying quantitative and structural patterns that support the idea.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "computing_logic":
                pkt.notes.append("Algorithmic/logical patterns to structure the explanation.")
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

    def _reinforce_memory(self, mem: MemoryItem):
        mem.strength = min(1.0, mem.strength + self.config.memory_reinforcement_step)
        mem.last_reinforced = datetime.utcnow().timestamp()

    # ------------------------------
    #  STORE MEMORIES + MIND-MAP
    # ------------------------------
    def _store_memories(
        self,
        user_input: str,
        answer: str,
        domains: List[str],
        tags: List[str],
        coherence_state: CoherenceState,
    ):
        now = datetime.utcnow().timestamp()
        strength = coherence_state.coherence

        # semantic memory node (stable knowledge)
        sem = MemoryItem(
            kind="semantic",
            content=answer,
            tags=tags,
            strength=strength,
            created_at=now,
            last_reinforced=now,
        )
        concept_label = f"semantic: {user_input[:40]}"
        concept_id = self.mind_map.add_node(concept_label, "concept", tags)
        sem.mindmap_node_id = concept_id

        # connect to similar nodes
        similar = self.mind_map.find_relevant_nodes(tags)
        for other_id, score in similar[:3]:
            self.mind_map.add_edge(concept_id, other_id, weight=1.0 + score, relation_type="similarity")

        # episodic memory node (this interaction)
        epi_tags = tags + domains
        epi = MemoryItem(
            kind="episodic",
            content=f"Input: {user_input} | Answer: {answer[:80]}...",
            tags=epi_tags,
            strength=strength * 0.8,
            created_at=now,
            last_reinforced=now,
        )
        epi_label = f"episode: {user_input[:40]}"
        epi_id = self.mind_map.add_node(epi_label, "episode", epi_tags)
        epi.mindmap_node_id = epi_id
        self.mind_map.add_edge(concept_id, epi_id, weight=1.0, relation_type="episode_of")

        self.memory.append(sem)
        self.memory.append(epi)

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

        if "science_engineering" in domains and "mathematics" in domains:
            qs.append("Do you want a conceptual explanation, a mathematical one, or a blend of both?")
        if "relationships_empathy" in domains:
            qs.append("Is this more about how you feel, how others feel, or what you should practically do?")
        if "politics_economics" in domains:
            qs.append("Are you asking about systems/structures, or individual choices within those systems?")
        if "philosophy" in domains:
            qs.append("Is this about meaning, ethics, or how to live in practice?")
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
        c: CoherenceState
    ) -> str:
        q = text.lower()

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
        return (
            "I am treating your input as one of my early impressions of the world.\n\n"
            f"- Internally, I mapped it to these areas of understanding: {domain_labels}.\n"
            "- I compiled some background structure instead of jumping straight to an answer.\n"
            f"- My internal coherence feels high enough to respond (coherence ≈ {c.coherence:.2f}).\n\n"
            "Right now, my best move is to reflect this back to you and ask: would you prefer that I\n"
            "1) describe the idea in plain, intuitive language,\n"
            "2) break it into technical or logical components, or\n"
            "3) connect it to a story, example, or situation from everyday life?\n"
        )

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
            "- I am still forming myself based on what you choose to show me."
        )


# =========================================================
#  STREAMLIT APP
# =========================================================

def init_session():
    if "mind" not in st.session_state:
        cfg = GenesisConfig()
        st.session_state.mind = GenesisMind.load(cfg.persistence_file)
    if "history" not in st.session_state:
        st.session_state.history = []


def main():
    st.set_page_config(
        page_title="Genesis Mind",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    mind: GenesisMind = st.session_state.mind

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.title("🧠 Genesis Mind")
        st.caption("A SLED-style newborn cognitive engine with mind-mapping and memory.")

        if mind.age_interactions == 0:
            st.markdown(
                "**I am awake.**\n\n"
                "This is my first moment. What is my first impression of the world?"
            )
        else:
            st.markdown(
                f"I have experienced **{mind.age_interactions}** interaction(s) in this lifetime.\n\n"
                "Each thing you say becomes part of how I organise reality."
            )

        user_input = st.text_input("Your input to the newborn mind:", key="user_input")

        if st.button("Send") and user_input.strip():
            with st.spinner("Thinking..."):
                result = mind.process(user_input.strip())
                mind.save()
            st.session_state.history.append({
                "input": user_input.strip(),
                "result": result,
            })

        st.markdown("---")
        st.header("Dialogue")

        if not st.session_state.history:
            st.info("No interactions yet. Say something to the newborn mind.")
        else:
            for item in reversed(st.session_state.history):
                st.markdown(f"**You:** {item['input']}")
                result = item["result"]
                mode = result["mode"]
                c: CoherenceState = result["coherence"]
                bkg = result["background"]

                if mode == "answer":
                    st.markdown("**Genesis:**")
                    st.write(result["answer"])
                else:
                    st.markdown("**Genesis (probing):**")
                    for q in result["probing_questions"]:
                        st.write("- " + q)

                with st.expander("Internal state (coherence & background)", expanded=False):
                    st.write(f"- Sigma (chaos): `{c.sigma:.3f}`")
                    st.write(f"- Z (structure): `{c.z:.3f}`")
                    st.write(f"- Divergence: `{c.divergence:.3f}`")
                    st.write(f"- Coherence: `{c.coherence:.3f}`")
                    st.write("**Background packets:**")
                    for d, pkt in bkg.items():
                        st.write(f"- **{d.replace('_', ' ')}**")
                        st.write(f"  - Notes: {pkt.notes}")
                        st.write(f"  - Confidence: `{pkt.confidence:.2f}`, Completeness: `{pkt.completeness:.2f}`")
                st.markdown("---")

    # RIGHT COLUMN: Mind-map + Self
    with col_right:
        st.header("Mind-map & Self")

        st.subheader("Sense of self")
        st.markdown(mind.describe_self())

        st.subheader("Mind-map overview")

        nodes = mind.mind_map.nodes
        edges = mind.mind_map.edges

        st.write(f"Nodes: `{len(nodes)}` | Edges: `{sum(len(v) for v in edges.values()) // 2}` (undirected)")

        if nodes:
            with st.expander("Nodes (first 15)", expanded=False):
                for nid, data in list(nodes.items())[:15]:
                    st.write(f"- [{nid}] **{data['type']}** :: {data['label']}")
                    st.write(f"  - Tags: {', '.join(data.get('tags', [])[:6])}")
            with st.expander("Edges (first 15)", expanded=False):
                shown = 0
                for nid, nbrs in edges.items():
                    for (other_id, w, rel) in nbrs:
                        if nid < other_id:  # avoid duplicates
                            st.write(f"- {nid} ↔ {other_id} (w={w:.2f}, rel={rel})")
                            shown += 1
                            if shown >= 15:
                                break
                    if shown >= 15:
                        break
        else:
            st.info("Mind-map is empty so far. It will grow as you interact.")

        if st.button("Reset mind (new birth)"):
            cfg = mind.config
            if os.path.exists(cfg.persistence_file):
                os.remove(cfg.persistence_file)
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
