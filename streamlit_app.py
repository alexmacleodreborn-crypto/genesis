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
    persistence_file: str = "sledai_developmental_state.json"


@dataclass
class MemoryItem:
    kind: str              # 'episodic' | 'semantic' | 'developmental'
    content: str
    tags: List[str]
    strength: float
    created_at: float
    last_reinforced: float
    meta: Dict[str, Any] = field(default_factory=dict)


# =========================================================
#  GENESIS / SLEDAI DEVELOPMENTAL MIND
# =========================================================

class GenesisMind:
    """
    Developmental cognitive engine with:
    - Interactive early-learning modules (0–5)
    - Stages: infancy -> schooling -> advanced
    - SLED coherence physics
    - Tag-based identity
    - Episodic + semantic + developmental memory
    - Recall + deliberation pipeline
    - Simple web-search learning stub
    - Sense-of-self and maturity score
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

        # developmental stage: 'infancy', 'schooling', 'advanced'
        self.stage: str = "infancy"

        # interactive early-learning modules
        self.early_learning_modules: Dict[str, bool] = {
            "objects": False,
            "family": False,
            "emotions": False,
            "cause_effect": False,
            "safety": False,
            "stories": False,
        }
        self.active_module: Optional[str] = None
        self.module_step: int = 0

    # ------------------------------
    #  PERSISTENCE
    # ------------------------------
    def save(self):
        data = {
            "config": asdict(self.config),
            "age_interactions": self.age_interactions,
            "memory": [asdict(m) for m in self.memory],
            "self_profile": self.self_profile,
            "stage": self.stage,
            "early_learning_modules": self.early_learning_modules,
            "active_module": self.active_module,
            "module_step": self.module_step,
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
        mind.stage = data.get("stage", "infancy")
        mind.early_learning_modules = data.get(
            "early_learning_modules",
            {
                "objects": False,
                "family": False,
                "emotions": False,
                "cause_effect": False,
                "safety": False,
                "stories": False,
            },
        )
        mind.active_module = data.get("active_module", None)
        mind.module_step = data.get("module_step", 0)
        return mind

    # =====================================================
    #  CORE COGNITIVE PRIMITIVES
    # =====================================================

    def _extract_tags(self, text: str) -> List[str]:
        words = text.lower().replace(",", " ").replace(".", " ").split()
        stop = {
            "the","and","or","of","in","a","an","to","for","is","are","as","on",
            "that","this","with","you","your","my","have","has","it","they","them",
            "was","were","from","about"
        }
        tags = [w for w in words if len(w) > 3 and w not in stop]

        for t in tags:
            self.self_profile["top_tags"][t] = self.self_profile["top_tags"].get(t, 0) + 1

        return tags

    def _detect_domains(self, text: str) -> List[str]:
        q = text.lower()
        active: List[str] = []

        if any(w in q for w in ["word","language","symbol","meaning","sentence","name","story"]):
            active.append("language_symbols")
        if any(w in q for w in ["country","city","continent","border","map","capital","world"]):
            active.append("geography")
        if any(w in q for w in ["relationship","friend","family","feel","emotion","empathy","love","dog","people","kind","son","daughter","brother","sister"]):
            active.append("relationships_empathy")
        if any(w in q for w in ["physics","chemistry","biology","engineering","gravity","entropy","energy","force","atom"]):
            active.append("science_engineering")
        if any(w in q for w in ["election","policy","government","inflation","market","economy","power"]):
            active.append("politics_economics")
        if any(w in q for w in ["meaning of life","ethics","morality","consciousness","free will","soul"]):
            active.append("philosophy")
        if any(w in q for w in ["equation","theorem","proof","integral","derivative","probability","number"]):
            active.append("mathematics")
        if any(w in q for w in ["algorithm","code","program","logic","boolean","bit","neural","compute","software"]):
            active.append("computing_logic")

        if not active:
            active = ["language_symbols"]

        return active

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

    # =====================================================
    #  MATURITY & STAGE LOGIC
    # =====================================================

    def _all_early_modules_complete(self) -> bool:
        return all(self.early_learning_modules.values())

    def _compute_maturity_score(self) -> float:
        total_inputs = self.self_profile["total_inputs"]
        num_tags = len(self.self_profile["top_tags"])
        avg_strength = (
            sum(m.strength for m in self.memory) / len(self.memory)
            if self.memory else 0.0
        )
        domain_diversity = sum(1 for c in self.self_profile["domain_counts"].values() if c > 0)

        # more aggressive growth
        score = (
            total_inputs * 10.0 +
            num_tags * 2.0 +
            avg_strength * 50.0 +
            domain_diversity * 20.0
        )
        return score

    def _update_stage(self):
        # If early-learning simulation not complete, force infancy
        if not self._all_early_modules_complete():
            self.stage = "infancy"
            return

        # Once all early modules complete, allow schooling and advanced
        score = self._compute_maturity_score()
        if score < 300:
            self.stage = "schooling"
        else:
            self.stage = "advanced"

    # =====================================================
    #  EARLY-LEARNING MODULES (INTERACTIVE)
    # =====================================================

    def _early_module_question(self, module: str, step: int) -> Optional[str]:
        # one question at a time
        if module == "objects":
            questions = [
                "Can you name three things you see around you right now?",
                "Can you tell me an animal you like?",
                "Can you name something you can eat?",
            ]
        elif module == "family":
            questions = [
                "Who is in your family?",
                "Do you have brothers or sisters?",
                "Is there someone in your family you are very close to?",
            ]
        elif module == "emotions":
            questions = [
                "What is something that makes people happy?",
                "What is something that makes someone sad?",
                "Can you tell me about a time someone felt scared?",
            ]
        elif module == "cause_effect":
            questions = [
                "What happens if you drop something from your hand?",
                "What do people usually do when they are tired?",
                "What happens when it rains a lot?",
            ]
        elif module == "safety":
            questions = [
                "What are some things children should stay away from?",
                "What is something that is safe to touch?",
                "What is something that can hurt you if you are not careful?",
            ]
        elif module == "stories":
            questions = [
                "Can you tell me a short story or memory from your life?",
                "Can you describe something that happened today?",
                "What is your favourite memory?",
            ]
        else:
            return None

        if step < len(questions):
            return questions[step]
        return None

    def run_early_learning_step(self, user_answer: str) -> Dict[str, Any]:
        """
        Process one step of the active early-learning module:
        - Use the last question + answer
        - Store developmental memory
        - Advance step or mark module complete
        """
        if not self.active_module:
            return {
                "completed": False,
                "message": "No early-learning module is currently active.",
            }

        module = self.active_module
        step = self.module_step

        # Extract tags from answer and store developmental memory
        tags = self._extract_tags(user_answer)
        self._store_memory(
            kind="developmental",
            content=f"[{module} step {step}] {user_answer}",
            tags=tags,
            strength=0.7,
            meta={"module": module, "step": step},
        )

        # Advance step
        next_step = step + 1
        next_question = self._early_module_question(module, next_step)

        if next_question is None:
            # module complete
            self.early_learning_modules[module] = True
            self.active_module = None
            self.module_step = 0
            return {
                "completed": True,
                "module": module,
                "next_question": None,
                "message": f"The {module} module is complete. You helped me learn a lot.",
            }
        else:
            # continue module
            self.module_step = next_step
            return {
                "completed": False,
                "module": module,
                "next_question": next_question,
                "message": f"Thank you. I am still learning about {module}.",
            }

    def start_early_learning_module(self, module: str) -> Optional[str]:
        """
        Start a module and return the first question.
        """
        if self.early_learning_modules.get(module, False):
            return None  # already complete
        self.active_module = module
        self.module_step = 0
        return self._early_module_question(module, 0)

    # =====================================================
    #  LEARNING MODES (SCHOOLING / ADVANCED)
    # =====================================================

    def _search_web(self, query: str) -> List[str]:
        """
        Stub for web search.
        Replace this with a real search integration in your environment.
        """
        return [
            f"(Example search snippet 1 about '{query}')",
            f"(Example search snippet 2 giving another angle on '{query}')",
            f"(Example search snippet 3 with a simple explanation of '{query}')",
        ]

    def _learn_schooling(self, user_input: str, tags: List[str], domains: List[str]) -> Dict[str, Any]:
        snippets = self._search_web(user_input)
        search_text = " ".join(snippets)
        search_tags = self._extract_tags(search_text)

        lesson = f"Schooling lesson based on: {user_input}\nSnippets:\n" + "\n".join(snippets[:3])
        self._store_memory(
            kind="semantic",
            content=lesson,
            tags=tags + search_tags,
            strength=0.6,
            meta={"mode": "schooling"},
        )
        return {
            "lesson": lesson,
            "snippets": snippets,
            "search_tags": search_tags,
        }

    def _learn_advanced(self, user_input: str, tags: List[str], domains: List[str]) -> Dict[str, Any]:
        snippets = self._search_web(user_input)
        search_text = " ".join(snippets)
        search_tags = self._extract_tags(search_text)

        recalled = self._recall_memory(tags, k=5)
        synthesis_lines = []
        synthesis_lines.append("Advanced synthesis of your query using what I know and what I can see:")
        if recalled:
            synthesis_lines.append("\nFrom our previous interactions I recall:")
            for m in recalled[:3]:
                synthesis_lines.append(f"- ({m.kind}) {m.content[:160]}")
        synthesis_lines.append("\nFrom external information I see summaries like:")
        for s in snippets[:3]:
            synthesis_lines.append(f"- {s}")
        synthesis = "\n".join(synthesis_lines)

        self._store_memory(
            kind="semantic",
            content=synthesis,
            tags=tags + search_tags,
            strength=0.7,
            meta={"mode": "advanced"},
        )
        return {
            "synthesis": synthesis,
            "snippets": snippets,
            "search_tags": search_tags,
            "recalled": recalled,
        }

    # =====================================================
    #  DELIBERATION & ANSWERING
    # =====================================================

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

    def _generate_answer(
        self,
        user_input: str,
        domains: List[str],
        deliberation: Dict[str, Any],
        style: str,
        learning_output: Optional[Dict[str, Any]],
    ) -> str:
        c: CoherenceState = deliberation["coherence"]
        recalled: List[MemoryItem] = deliberation["recalled"]
        domain_labels = ", ".join(d.replace("_", " ") for d in domains)

        lines: List[str] = []

        if self.stage == "infancy":
            lines.append("I am in my infancy stage, but my early-learning modules are complete.")
        elif self.stage == "schooling":
            lines.append("I am in my schooling stage, learning structured subjects.")
        else:
            lines.append("I am in my advanced stage, integrating what I know with new information.")

        if style == "plain":
            lines.append("I'll keep this in simple, clear language.")
        elif style == "technical":
            lines.append("I'll describe this in a more structured, technical way.")
        else:
            lines.append("I'll explain this in a more story-like, example-driven way.")

        lines.append(f"\nFrom your input, I see it mainly touches: {domain_labels}.")

        if self.stage == "schooling" and learning_output is not None:
            lines.append("\nFrom my schooling-style learning, I gathered:")
            for s in learning_output.get("snippets", [])[:3]:
                lines.append(f"- {s}")
        elif self.stage == "advanced" and learning_output is not None:
            lines.append("\nHere is my current synthesis:")
            lines.append(learning_output.get("synthesis", ""))

        if recalled:
            lines.append("\nI am also remembering related things from before:")
            for m in recalled[:3]:
                lines.append(f"- ({m.kind}, strength={m.strength:.2f}) {m.content[:140]}")

        lines.append(
            f"\nInternally, my coherence for this is about {c.coherence:.2f}. "
            "You can push me by asking for more detail, a different angle, or a concrete example."
        )

        return "\n".join(lines)

    # =====================================================
    #  SENSE OF SELF
    # =====================================================

    def describe_self(self) -> str:
        total = self.self_profile["total_inputs"]
        dom_counts = self.self_profile["domain_counts"]
        maturity = self._compute_maturity_score()

        if total > 0:
            sorted_domains = sorted(dom_counts.items(), key=lambda x: x[1], reverse=True)
            dominant = [f"{d.replace('_', ' ')} ({c})" for d, c in sorted_domains if c > 0][:3]
        else:
            dominant = []

        tags = self.self_profile["top_tags"]
        top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
        tag_str = ", ".join([f"{t}×{c}" for t, c in top_tags]) if top_tags else "none yet"

        modules_state = ", ".join(
            f"{name}:{'✓' if done else '…'}"
            for name, done in self.early_learning_modules.items()
        )

        return (
            f"- Stage: {self.stage}\n"
            f"- Maturity score: {maturity:.1f}\n"
            f"- I have experienced {total} interaction(s).\n"
            f"- My most engaged domains so far: {', '.join(dominant) if dominant else 'none yet'}.\n"
            f"- Recurring concepts/tags in my experience: {tag_str}.\n"
            f"- Early-learning modules: {modules_state}\n"
            "- When all early-learning modules are complete, I move into schooling and beyond."
        )

    # =====================================================
    #  MAIN PROCESS LOOP (NORMAL CHAT)
    # =====================================================

    def process(self, user_input: str, style: str) -> Dict[str, Any]:
        """
        Normal conversational processing (not early-learning module answers).
        """
        self.age_interactions += 1
        self.self_profile["total_inputs"] += 1

        domains = self._detect_domains(user_input)
        for d in domains:
            self.self_profile["domain_counts"][d] += 1

        input_tags = self._extract_tags(user_input)
        self._decay_memory()
        self._update_stage()

        deliberation = self._deliberate(user_input, domains, input_tags)
        c: CoherenceState = deliberation["coherence"]
        background = deliberation["background"]

        learning_output: Optional[Dict[str, Any]] = None

        if self.stage == "schooling":
            learning_output = self._learn_schooling(user_input, input_tags, domains)
        elif self.stage == "advanced":
            learning_output = self._learn_advanced(user_input, input_tags, domains)

        if c.coherence < self.config.probing_threshold and self.stage != "infancy":
            probing = self._generate_probing_questions(user_input, domains, background, c)
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
                "recalled": [asdict(m) for m in deliberation["recalled"]],
                "learning_output": learning_output,
                "stage": self.stage,
            }

        # Generate answer
        if self.stage == "infancy" and not self._all_early_modules_complete():
            # infancy responses while still in early-learning phase
            lines = []
            lines.append("I am very young. My early-learning modules are not all complete yet.")
            lines.append("You can help by starting modules on the right, or just telling me simple facts.")
            lines.append(f"Right now, I noticed these words: {', '.join(input_tags[:5])}.")
            answer = "\n".join(lines)
        else:
            answer = self._generate_answer(user_input, domains, deliberation, style, learning_output)

        self._store_memory(
            kind="semantic" if self.stage != "infancy" else "episodic",
            content=answer,
            tags=input_tags,
            strength=c.coherence,
            meta={"domains": domains, "stage": self.stage},
        )

        return {
            "mode": "answer",
            "answer": answer,
            "coherence": c,
            "background": background,
            "recalled": [asdict(m) for m in deliberation["recalled"]],
            "learning_output": learning_output,
            "stage": self.stage,
        }


# =========================================================
#  STREAMLIT APP (SLEDAI DEVELOPMENTAL GENESIS)
# =========================================================

def init_session():
    if "mind" not in st.session_state:
        cfg = GenesisConfig()
        st.session_state.mind = GenesisMind.load(cfg.persistence_file)
    if "history" not in st.session_state:
        st.session_state.history = []
    if "style" not in st.session_state:
        st.session_state.style = "plain"
    if "module_question" not in st.session_state:
        st.session_state.module_question = None


def main():
    st.set_page_config(
        page_title="SledAI Developmental Genesis",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    mind: GenesisMind = st.session_state.mind

    col_left, col_right = st.columns([2, 1])

    # ---------------- LEFT: Dialogue & modules interaction ----------------
    with col_left:
        st.title("SledAI Developmental Genesis")
        st.caption("A developmental mind that grows from interactive early learning to schooling and advanced knowledge.")

        st.markdown(mind.describe_self())

        st.markdown("### Early-learning modules (0–5 simulated years)")

        modules = [
            ("objects", "Objects & Categories"),
            ("family", "People & Family"),
            ("emotions", "Emotions"),
            ("cause_effect", "Actions & Cause/Effect"),
            ("safety", "Safety & Rules"),
            ("stories", "Language & Stories"),
        ]

        module_cols = st.columns(3)
        for i, (key, label) in enumerate(modules):
            col = module_cols[i % 3]
            with col:
                done = mind.early_learning_modules.get(key, False)
                if done:
                    st.button(f"✓ {label}", disabled=True, key=f"mod_{key}_done")
                else:
                    if st.button(f"Start {label}", key=f"mod_{key}_start"):
                        q = mind.start_early_learning_module(key)
                        mind.save()
                        st.session_state.module_question = q

        st.markdown("---")

        style = st.radio(
            "How should I shape my explanations?",
            ["plain", "technical", "story"],
            index=["plain","technical","story"].index(st.session_state.style),
            horizontal=True,
        )
        st.session_state.style = style

        # If an early-learning module is active, show its current question
        if mind.active_module and st.session_state.module_question:
            st.subheader(f"Early-learning module: {mind.active_module}")
            st.write(st.session_state.module_question)
            module_answer = st.text_input("Your answer for this question:", key="module_answer")
            if st.button("Send module answer"):
                with st.spinner("Processing developmental learning..."):
                    result = mind.run_early_learning_step(module_answer.strip())
                    mind.save()
                st.session_state.history.append(
                    {
                        "input": f"[MODULE {mind.active_module}] {module_answer}",
                        "result": {
                            "mode": "module",
                            "info": result,
                            "coherence": CoherenceState(0,0,0,0),
                            "background": {},
                            "recalled": [],
                            "stage": mind.stage,
                        },
                    }
                )
                st.session_state.module_question = result.get("next_question")
                st.experimental_rerun()
        else:
            # Normal conversational input
            user_input = st.text_input("Your input to the mind:", key="user_input")
            if st.button("Send") and user_input.strip():
                with st.spinner("Thinking, learning, and recalling..."):
                    result = mind.process(user_input.strip(), style)
                    mind.save()
                st.session_state.history.append({"input": user_input.strip(), "result": result})

        st.markdown("---")
        st.header("Dialogue")

        if not st.session_state.history:
            st.info("No interactions yet. Start a module or say something.")
        else:
            for item in reversed(st.session_state.history):
                st.markdown(f"**You:** {item['input']}")
                result = item["result"]
                mode = result["mode"]
                stage = result.get("stage", "infancy")

                if mode == "answer":
                    st.markdown(f"**SledAI ({stage}):**")
                    st.code(result["answer"])
                elif mode == "probing":
                    st.markdown(f"**SledAI ({stage}, probing):**")
                    for q in result["probing_questions"]:
                        st.write("- " + q)
                elif mode == "module":
                    info = result["info"]
                    st.markdown(f"**SledAI (early-learning):**")
                    st.write(info.get("message", ""))
                    if info.get("next_question"):
                        st.write(f"Next question will be: {info['next_question']}")
                    if info.get("completed"):
                        st.write(f"Module '{info.get('module')}' is now complete.")

                st.markdown("---")

    # ---------------- RIGHT: Mind overview ----------------
    with col_right:
        st.header("Mind overview")
        st.markdown(mind.describe_self())

        if st.button("Reset mind (new birth)"):
            cfg = mind.config
            if os.path.exists(cfg.persistence_file):
                os.remove(cfg.persistence_file)
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
