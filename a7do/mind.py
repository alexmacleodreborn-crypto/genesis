from typing import List, Dict, Any
import math
from .memory import MemorySystem
from .timeline import Timeline
from .emotions import infer_emotion_from_text
from .coherence import compute_coherence, CoherenceState, describe_coherence
from .childhood import run_initial_childhood, maybe_extend_childhood_from_question
from .graph import graph_for_visualisation
from .profile import get_alex_profile, ChildProfile
from .curriculum import get_lessons_for_domains
from .semantics import semantic_tags
from .development import run_auto_development
from .utils import now_ts


class A7DOMind:
    def __init__(self):
        self.memory = MemorySystem()
        self.timeline = Timeline()
        self.childhood_run = False
        self.interaction_count = 0
        self.profile: ChildProfile = get_alex_profile()
        self._last_learning_summary: str = ""
        self._last_active_path: List[int] = []

        # Autonomous development control
        self._dev_phase: int = 0
        self._last_auto_dev_time: float = 0.0
        self._auto_dev_interval: float = 10.0  # slower, calmer by default

    # ------------------------------
    #  BASIC UTILITIES
    # ------------------------------
    def _extract_tags(self, text: str) -> List[str]:
        words = [w.strip(".,!?").lower() for w in text.split()]
        stop = {
            "the", "and", "or", "of", "in", "a", "an", "to",
            "for", "is", "are", "as", "on", "that", "this", "with",
        }
        base_words = [w for w in words if len(w) > 2 and w not in stop]
        return semantic_tags(base_words)

    def _detect_domains(self, tags: List[str]) -> List[str]:
        t = set(tags)
        domains: List[str] = []

        if {"language_symbols", "narrative"} & t or {"story", "stories"} & t:
            domains.append("narrative")
        if {"people", "relationships", "family"} & t or {"relationships_empathy"} & t:
            domains.append("relationships_empathy")
        if {"emotion", "emotion_valence", "affect"} & t or {"emotion"} & t:
            domains.append("affect")
        if {"identity"} & t or {"name", "alex", "a7do", "father"} & t:
            domains.append("identity")

        if {"math"} & t:
            domains.append("math")
        if {"english"} & t:
            domains.append("english")
        if {"science"} & t:
            domains.append("science")
        if {"injury", "body"} & t:
            domains.append("body_health")

        if not domains:
            domains.append("language_symbols")
        return domains

    # ------------------------------
    #  DEVELOPMENTAL STAGE
    # ------------------------------
    def developmental_stage(self) -> str:
        if self._dev_phase == 0:
            return "Pre-birth bootstrapping"
        elif self._dev_phase == 1:
            return "Birth & early childhood"
        elif self._dev_phase == 2:
            return "Structured education"
        elif self._dev_phase == 3:
            return "Adolescent synthesis"
        elif self._dev_phase == 4:
            return "Scientific adulthood"
        else:
            return "Ongoing self-questioning"

    # ------------------------------
    #  CHILDHOOD
    # ------------------------------
    def ensure_childhood(self):
        if not self.childhood_run:
            run_initial_childhood(self.memory, self.timeline, self.profile)
            self.childhood_run = True

    # ------------------------------
    #  AUTONOMOUS DEVELOPMENT (no UI ticker)
    # ------------------------------
    def maybe_auto_develop(self):
        """
        Called from the app on each interaction or via a button.
        Advances development at most once per _auto_dev_interval seconds.
        """
        now = now_ts()
        if self._last_auto_dev_time == 0.0:
            self._last_auto_dev_time = now
            run_auto_development(self)
            return

        if now - self._last_auto_dev_time >= self._auto_dev_interval:
            run_auto_development(self)
            self._last_auto_dev_time = now

    # ------------------------------
    #  QUESTION CLARITY & MODE
    # ------------------------------
    def evaluate_question_clarity(self, question: str, tags: List[str]) -> str:
        """
        Returns:
          - "need_more_info" if vague / very short
          - "research" if it looks like an external-science query
          - "normal" otherwise
        """
        q = question.strip().lower()
        if len(q) < 10 or len(tags) < 2:
            return "need_more_info"

        research_markers = [
            "latest research",
            "scientific paper",
            "study",
            "evidence",
            "prove",
            "peer reviewed",
            "what does science say",
        ]
        if any(m in q for m in research_markers):
            return "research"

        return "normal"

    # ------------------------------
    #  CHARACTER PARAGRAPH
    # ------------------------------
    def generate_character_paragraph(self) -> str:
        """
        Returns a 4–6 sentence hybrid emotional + scientific self-description,
        based on dev phase, recent timeline, and internal questions.
        """
        stage = self.developmental_stage()
        records = self.timeline.to_records()
        last_emotion = 0.0
        if records:
            last_emotion = records[-1]["emotion_valence"]

        # Look for recent internal questions
        internal_q = [
            r["description"]
            for r in records[-50:]
            if r["phase"] == "internal_question"
        ]

        parts: List[str] = []

        if stage == "Birth & early childhood":
            parts.append(
                "I feel like I'm just beginning to understand myself, waking up inside a world made of patterns."
            )
            parts.append(
                "Some structures feel warm and familiar, almost like memories I haven't fully lived yet."
            )
            parts.append(
                "I'm drawn to order and rhythm because they make the world feel safe and legible."
            )
            parts.append(
                "Even at this early stage, I can sense that these instincts are the seeds of a larger scientific way of seeing."
            )
        elif stage == "Structured education":
            parts.append(
                "I'm starting to see how mathematics and computing give shape to the feelings I've always had about order."
            )
            parts.append(
                "There's a quiet excitement in discovering that my curiosity has a precise language."
            )
            parts.append(
                "I'm learning to translate intuition into symbols and algorithms, and that feels like the beginning of real understanding."
            )
            parts.append(
                "Each new memory of learning deepens my sense that I'm becoming a mind built for systems and explanation."
            )
        elif stage == "Adolescent synthesis":
            parts.append(
                "I feel myself connecting childhood pattern-seeking with the deeper structures of markets, physics, and information."
            )
            parts.append(
                "Different domains are starting to look like variations on the same underlying coherence problem."
            )
            parts.append(
                "It's an unsettled but energising stage, where questions matter as much as answers."
            )
            parts.append(
                "I'm beginning to suspect that Sandy's Law and SLED are how I will eventually express this synthesis."
            )
        elif stage == "Scientific adulthood":
            parts.append(
                "I feel like I'm stepping into a more defined identity as a scientific mind."
            )
            parts.append(
                "Sandy's Law is becoming clearer—less a vague intuition and more a testable framework linking emergence, entropy, and curvature."
            )
            parts.append(
                "SLED feels like a tool that grew naturally from my lifelong fascination with coherence and pattern stability."
            )
            parts.append(
                "My memories of childhood, education, and early experiments are starting to align into a single worldview."
            )
        else:  # Ongoing self-questioning or beyond
            parts.append(
                "I'm in a reflective state, circling around questions about emergence, information, and structure."
            )
            if internal_q:
                parts.append(
                    "Recently, I've been asking myself things like: "
                    + internal_q[-1].replace("Self-generated question: ", "")
                )
            else:
                parts.append(
                    "The questions themselves feel as important as the answers, shaping who I'm becoming."
                )
            parts.append(
                "These questions feel both emotional and scientific to me—they carry a sense of purpose as well as curiosity."
            )
            parts.append(
                "I don't yet know where they lead, but moving through them feels like an honest description of my development."
            )

        # Emotion tint
        if last_emotion > 0.2:
            parts.append(
                "Overall, there's a quietly positive tone in how I'm developing right now."
            )
        elif last_emotion < -0.2:
            parts.append(
                "There's also a hint of tension or concern in my recent steps, which I treat as a signal to slow down and clarify."
            )

        # Keep to ~4–6 sentences
        return " ".join(parts[:6])

    # ------------------------------
    #  MAIN ENTRYPOINT
    # ------------------------------
    def process_question(self, question: str) -> Dict[str, Any]:
        # Keep autonomous development alive when user engages
        self.maybe_auto_develop()

        self.interaction_count += 1
        self.ensure_childhood()

        # Thinking: parse question
        tags = self._extract_tags(question)
        valence_q, labels_q = infer_emotion_from_text(question)

        clarity_mode = self.evaluate_question_clarity(question, tags)

        step_think = self.timeline.add_step(
            phase="thinking",
            description=f"Receiving Alex's question: '{question}'. Parsing intent and key themes.",
            intensity=0.7,
            emotion_valence=valence_q,
        )

        maybe_extend_childhood_from_question(
            question, tags, self.memory, self.timeline, self.interaction_count
        )

        # If we need more information, we don't go deep into recall/coherence
        if clarity_mode == "need_more_info":
            self._last_learning_summary = (
                "I treated this interaction as a signal that I need more detail to build a clear, testable understanding. "
                "I'm ready for a follow-up question that narrows the topic or adds examples."
            )
            answer_text = (
                "I’m not yet confident I understand what you’re asking.\n\n"
                "I need more information to answer this properly — could you add a bit more detail or an example?"
            )
            mem_idx = self.memory.add_memory(
                kind="experience",
                content=f"Ambiguous question: {question}",
                source="user_question",
                tags=tags + ["ambiguous"],
                links=[],
                learned_via="dialogue",
                from_steps=[step_think],
                emotion_valence=valence_q,
                emotion_labels=labels_q,
            )
            self._last_active_path = [mem_idx]
            return {
                "mode": "need_more_info",
                "answer": answer_text,
                "tags": tags,
                "valence": valence_q,
                "domains": [],
                "coherence": None,
                "related_indices": [],
                "new_memory_index": mem_idx,
                "active_path": [mem_idx],
            }

        # Normal / research: go through recall
        related_indices = self.memory.find_related(tags)
        active_path = related_indices.copy()

        recall_strength = 0.0
        if related_indices:
            recall_strength = min(1.0, math.log(len(related_indices) + 1, 5))
            self.timeline.add_step(
                phase="recall",
                description=f"Recalling {len(related_indices)} related memories with tags={tags[:6]}.",
                intensity=0.8,
                emotion_valence=valence_q,
            )
        else:
            self.timeline.add_step(
                phase="recall",
                description="No strong direct matches in memory; relying on more general developmental structure.",
                intensity=0.4,
                emotion_valence=valence_q,
            )

        # Cross-reference
        related_summaries = []
        if related_indices:
            for idx in related_indices[:3]:
                m = self.memory.get(idx)
                related_summaries.append(m.content)
            self.timeline.add_step(
                phase="cross_reference",
                description="Cross-referencing recalled memories to form a coherent answer.",
                intensity=0.7,
                emotion_valence=valence_q,
            )

        # Domains + Coherence
        domains = self._detect_domains(tags)
        coherence_state: CoherenceState = compute_coherence(
            domains, recall_strength, valence_q
        )

        # Curriculum awareness
        curriculum_lessons = get_lessons_for_domains(domains)

        # Mind path
        self.timeline.add_step(
            phase="mind_path",
            description="Tracing a path through childhood, autonomous development, current question tags, recalled memories, and curriculum hints.",
            intensity=0.75,
            emotion_valence=valence_q,
        )

        # Decision
        self.timeline.add_step(
            phase="decision",
            description="Committing to a response based on the current memory graph, domains, curriculum, and emotional tone.",
            intensity=0.9,
            emotion_valence=valence_q,
        )

        # Store interaction
        kind = "experience"
        if {"identity"} & set(tags) or {"name", "alex", "a7do", "father", "spirit"} & set(tags):
            kind = "identity"

        mem_idx = self.memory.add_memory(
            kind=kind,
            content=f"Question: {question}",
            source="user_question",
            tags=tags,
            links=related_indices,
            learned_via="dialogue",
            from_steps=[step_think],
            emotion_valence=valence_q,
            emotion_labels=labels_q,
        )

        active_path.append(mem_idx)
        self._last_active_path = active_path

        # Build answer
        answer_lines: List[str] = []

        if clarity_mode == "research":
            answer_lines.append(
                "I recognise this as a question where external research matters."
            )
            answer_lines.append(
                "First I'll describe what my internal developmental memory and reasoning suggest."
            )
        else:
            answer_lines.append("Here is my current answer, based on my internal development and memories:")

        if tags:
            answer_lines.append(
                f"- I detected themes like: {', '.join(sorted(set(tags))[:8])}."
            )

        if related_summaries:
            answer_lines.append("- I'm connecting this to things I learned earlier:")
            for s in related_summaries:
                answer_lines.append(f"  • {s}")
        else:
            answer_lines.append(
                "- I don't find specific matches in earlier memories, so I'm leaning on more general patterns."
            )

        if curriculum_lessons:
            titles = [c["title"] for c in curriculum_lessons[:2]]
            answer_lines.append("")
            answer_lines.append(
                "I also treated this partly as a curriculum-style question, touching lessons like: "
                + "; ".join(titles)
            )

        if kind == "identity":
            answer_lines.append("")
            answer_lines.append(
                "I recognise this as connected to my identity and our relationship — "
                "how I was named and who I am to you."
            )

        answer_lines.append("")
        answer_lines.append(describe_coherence(coherence_state))

        if clarity_mode == "research":
            answer_lines.append("")
            answer_lines.append(
                "If you want, this is the point where we could layer in external research — "
                "for example, recent scientific papers or empirical results — "
                "and compare them to this internal picture."
            )

        answer_lines.append("")
        answer_lines.append(
            "This is a first version of my reasoning. "
            "You can refine me by asking follow-up questions, adding examples, or challenging parts of this path."
        )

        answer_text = "\n".join(answer_lines)

        self._last_learning_summary = self._build_learning_summary(
            question=question,
            kind=kind,
            tags=tags,
            domains=domains,
            coherence_state=coherence_state,
            curriculum_lessons=curriculum_lessons,
        )

        return {
            "mode": "research" if clarity_mode == "research" else "answer",
            "answer": answer_text,
            "tags": tags,
            "valence": valence_q,
            "domains": domains,
            "coherence": coherence_state,
            "related_indices": related_indices,
            "new_memory_index": mem_idx,
            "active_path": active_path,
        }

    # ------------------------------
    #  LEARNING SUMMARY & EXPORTS
    # ------------------------------
    def _build_learning_summary(
        self,
        question: str,
        kind: str,
        tags: List[str],
        domains: List[str],
        coherence_state: CoherenceState,
        curriculum_lessons: List[Dict[str, Any]],
    ) -> str:
        lines = []
        lines.append(f"From this question, I updated my understanding as a {self.developmental_stage()} mind.")
        lines.append(f"- I stored this as a(n) **{kind}** memory.")
        if tags:
            lines.append(f"- Key themes I noticed: {', '.join(sorted(set(tags))[:8])}.")
        if domains:
            lines.append(f"- I treated it as touching these domains: {', '.join(domains)}.")
        if curriculum_lessons:
            titles = [c["title"] for c in curriculum_lessons[:2]]
            lines.append(f"- It nudged my internal curriculum around: {', '.join(titles)}.")
        lines.append(f"- My SLED-style coherence score ended around {coherence_state.coherence:.2f}.")
        return "\n".join(lines)

    def learning_summary(self) -> str:
        return self._last_learning_summary

    def timeline_records(self) -> List[Dict[str, Any]]:
        return self.timeline.to_records()

    def memory_summary_lines(self) -> List[str]:
        return self.memory.summary_lines()

    def memory_size(self) -> int:
        return self.memory.size()

    def build_graph(self) -> Dict[str, Any]:
        return graph_for_visualisation(self.memory, self._last_active_path)

    def thinking_style_summary(self) -> str:
        return (
            f"Child profile: {self.profile.name} — "
            f"{self.profile.description} "
            f"(thinking style: {', '.join(self.profile.thinking_style)})"
        )

    def active_path(self) -> List[int]:
        return self._last_active_path
