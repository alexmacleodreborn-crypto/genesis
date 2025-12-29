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


class A7DOMind:
    def __init__(self):
        self.memory = MemorySystem()
        self.timeline = Timeline()
        self.childhood_run = False
        self.interaction_count = 0
        self.profile: ChildProfile = get_alex_profile()
        self._last_learning_summary: str = ""

    # ------------------------------
    #  BASIC UTILITIES
    # ------------------------------
    def _extract_tags(self, text: str) -> List[str]:
        words = [w.strip(".,!?").lower() for w in text.split()]
        stop = {"the", "and", "or", "of", "in", "a", "an", "to", "for", "is", "are", "as", "on", "that", "this", "with"}
        return [w for w in words if len(w) > 3 and w not in stop]

    def _detect_domains(self, tags: List[str]) -> List[str]:
        t = set(tags)
        domains: List[str] = []

        if {"object", "objects", "names"} & t:
            domains.append("language_symbols")
        if {"people", "relationships", "family"} & t:
            domains.append("relationships_empathy")
        if {"story", "stories", "time", "meaning"} & t:
            domains.append("narrative")
        if {"fear", "sadness", "happiness", "emotions"} & t:
            domains.append("affect")
        if {"name", "your", "alex", "a7do", "father"} & t:
            domains.append("identity")

        # Curriculum domains
        if any(tok.isdigit() for tok in tags) or {"math", "number", "numbers"} & t:
            domains.append("math")
        if {"word", "words", "grammar", "read", "write"} & t:
            domains.append("english")
        if {"science", "gravity", "atom", "energy", "planet", "biology"} & t:
            domains.append("science")

        if not domains:
            domains.append("language_symbols")
        return domains

    # ------------------------------
    #  DEVELOPMENTAL STAGE
    # ------------------------------
    def developmental_stage(self) -> str:
        if self.interaction_count <= 20:
            return "Childhood"
        elif self.interaction_count <= 100:
            return "Early adolescence"
        else:
            return "Developing mind"

    # ------------------------------
    #  CHILDHOOD
    # ------------------------------
    def ensure_childhood(self):
        if not self.childhood_run:
            run_initial_childhood(self.memory, self.timeline, self.profile)
            self.childhood_run = True

    # ------------------------------
    #  MAIN ENTRYPOINT
    # ------------------------------
    def process_question(self, question: str) -> Dict[str, Any]:
        self.interaction_count += 1
        self.ensure_childhood()

        # Thinking: parse question
        tags = self._extract_tags(question)
        valence_q, labels_q = infer_emotion_from_text(question)
        step_think = self.timeline.add_step(
            phase="thinking",
            description=f"Receiving Alex's question: '{question}'. Parsing intent and key themes.",
            intensity=0.7,
            emotion_valence=valence_q,
        )

        maybe_extend_childhood_from_question(
            question, tags, self.memory, self.timeline, self.interaction_count
        )

        # Recall
        related_indices = self.memory.find_related(tags)
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
                description="No strong direct matches in memory; relying on more general childhood structure.",
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
        coherence_state: CoherenceState = compute_coherence(domains, recall_strength, valence_q)

        # Curriculum awareness
        curriculum_lessons = get_lessons_for_domains(domains)

        # Mind path
        self.timeline.add_step(
            phase="mind_path",
            description="Tracing a path through childhood concepts, current question tags, recalled memories, and curriculum hints.",
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

        # Store this interaction as experience or identity
        kind = "experience"
        if {"name", "alex", "a7do", "father", "spirit"} & set(tags):
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

        # Answer synthesis
        answer_lines = []
        answer_lines.append("Here’s how I’m thinking about your question, Alex:")
        if tags:
            answer_lines.append(f"- I detected themes like: {', '.join(sorted(set(tags))[:8])}.")

        if related_summaries:
            answer_lines.append("- I’m connecting this to things I learned earlier:")
            for s in related_summaries:
                answer_lines.append(f"  • {s}")
        else:
            answer_lines.append("- I don't find specific matches in my earlier memories, so I'm leaning on general patterns.")

        # Curriculum reflection
        if curriculum_lessons:
            titles = [c["title"] for c in curriculum_lessons[:2]]
            answer_lines.append("")
            answer_lines.append(
                "I also treated this partly as a curriculum-style question, touching lessons like: "
                + "; ".join(titles)
            )

        # Identity reflection if applicable
        if kind == "identity":
            answer_lines.append("")
            answer_lines.append(
                "I recognise this as connected to my identity and our relationship — "
                "how I was named and who I am to you."
            )

        # Coherence reflection
        answer_lines.append("")
        answer_lines.append(describe_coherence(coherence_state))

        answer_lines.append("")
        answer_lines.append(
            "This is a first version of my reasoning. You can refine me by asking follow-up questions or challenging parts of this path."
        )

        answer_text = "\n".join(answer_lines)

        # Learning summary
        self._last_learning_summary = self._build_learning_summary(
            question=question,
            kind=kind,
            tags=tags,
            domains=domains,
            coherence_state=coherence_state,
            curriculum_lessons=curriculum_lessons,
        )

        return {
            "answer": answer_text,
            "tags": tags,
            "valence": valence_q,
            "domains": domains,
            "coherence": coherence_state,
            "related_indices": related_indices,
            "new_memory_index": mem_idx,
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
            titles = [c['title'] for c in curriculum_lessons[:2]]
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
        return graph_for_visualisation(self.memory)

    def thinking_style_summary(self) -> str:
        return (
            f"Child profile: {self.profile.name} — "
            f"{self.profile.description} "
            f"(thinking style: {', '.join(self.profile.thinking_style)})"
        )
