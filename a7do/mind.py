from typing import List, Dict, Any
import math

from .memory import MemorySystem
from .timeline import Timeline
from .emotions import infer_emotion_from_text
from .coherence import compute_coherence, CoherenceState
from .childhood import run_initial_childhood, maybe_extend_childhood_from_question
from .graph import build_memory_graph


class A7DOMind:
    def __init__(self):
        self.memory = MemorySystem()
        self.timeline = Timeline()
        self.childhood_run = False
        self.interaction_count = 0

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
        if not domains:
            domains.append("language_symbols")
        return domains

    # ------------------------------
    #  MAIN ENTRYPOINT
    # ------------------------------
    def ensure_childhood(self):
        if not self.childhood_run:
            run_initial_childhood(self.memory, self.timeline)
            self.childhood_run = True

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

        # Mind path
        self.timeline.add_step(
            phase="mind_path",
            description="Tracing a path through childhood concepts, current question tags, and recalled memories.",
            intensity=0.75,
            emotion_valence=valence_q,
        )

        # Decision
        self.timeline.add_step(
            phase="decision",
            description="Committing to a response based on the current memory graph, domains, and emotional tone.",
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

        # Identity reflection if applicable
        if kind == "identity":
            answer_lines.append("")
            answer_lines.append("I recognise this as connected to my identity and our relationship — how I was named and who I am to you.")

        # Coherence reflection
        answer_lines.append("")
        answer_lines.append(
            f"My internal coherence for this response feels around {coherence_state.coherence:.2f} "
            f"(sigma={coherence_state.sigma:.2f}, z={coherence_state.z:.2f}, domains={coherence_state.domains})."
        )

        answer_lines.append("")
        answer_lines.append(
            "This is a first version of my reasoning. You can refine me by asking follow-up questions or challenging parts of this path."
        )

        answer_text = "\n".join(answer_lines)

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
    #  EXPORTS FOR UI
    # ------------------------------
    def timeline_records(self) -> List[Dict[str, Any]]:
        return self.timeline.to_records()

    def memory_summary_lines(self) -> List[str]:
        return self.memory.summary_lines()

    def memory_size(self) -> int:
        return self.memory.size()

    def build_graph(self) -> Dict[str, Any]:
        return build_memory_graph(self.memory)
