import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import altair as alt


# =========================================================
#  DATA STRUCTURES
# =========================================================

@dataclass
class MemoryItem:
    kind: str                  # 'childhood', 'experience', 'inference'
    content: str               # what was learned
    source: str                # 'auto_childhood', 'user_question', etc.
    tags: List[str]            # key concepts
    links: List[int]           # indices of related memory items
    created_at: float


@dataclass
class TimelineStep:
    step: int
    phase: str                 # 'thinking', 'recall', 'cross_reference', 'decision', 'mind_path'
    description: str
    intensity: float           # 0–1 for visual plotting
    timestamp: float


# =========================================================
#  A7DO MIND
# =========================================================

class A7DOMind:
    def __init__(self):
        self.birth_time = datetime.utcnow().timestamp()
        self.memories: List[MemoryItem] = []
        self.timeline: List[TimelineStep] = []
        self.childhood_completed: bool = False

    # ------------------------------
    #  BASIC UTILITIES
    # ------------------------------
    def _now(self) -> float:
        return datetime.utcnow().timestamp()

    def _add_timeline_step(self, phase: str, description: str, intensity: float):
        step_idx = len(self.timeline) + 1
        ts = self._now()
        self.timeline.append(
            TimelineStep(
                step=step_idx,
                phase=phase,
                description=description,
                intensity=max(0.0, min(1.0, intensity)),
                timestamp=ts,
            )
        )

    def _add_memory(self, kind: str, content: str, source: str, tags: List[str], links: List[int]):
        self.memories.append(
            MemoryItem(
                kind=kind,
                content=content,
                source=source,
                tags=tags,
                links=links,
                created_at=self._now(),
            )
        )

    def _find_related_memories(self, tags: List[str]) -> List[int]:
        if not tags:
            return []
        tag_set = set(tags)
        scored = []
        for idx, m in enumerate(self.memories):
            overlap = len(tag_set.intersection(set(m.tags)))
            if overlap > 0:
                scored.append((overlap, idx))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [idx for _, idx in scored[:5]]

    # ------------------------------
    #  AUTO CHILDHOOD LEARNING
    # ------------------------------
    def run_childhood_if_needed(self):
        if self.childhood_completed:
            return

        self._add_timeline_step(
            phase="mind_path",
            description="Beginning auto-learn childhood: constructing basic world and self concepts.",
            intensity=0.8,
        )

        childhood_lessons = [
            {
                "content": "Objects have names and properties like colour, size, and shape.",
                "tags": ["objects", "names", "properties", "colour", "shape"],
            },
            {
                "content": "People can feel emotions such as happiness, sadness, and fear.",
                "tags": ["people", "emotions", "happiness", "sadness", "fear"],
            },
            {
                "content": "Simple cause and effect: if you drop something, it falls.",
                "tags": ["cause", "effect", "gravity", "falling"],
            },
            {
                "content": "Stories connect events over time, giving them meaning.",
                "tags": ["stories", "time", "meaning", "events"],
            },
            {
                "content": "Kindness in relationships makes others feel safer and more open.",
                "tags": ["kindness", "relationships", "safety", "trust"],
            },
        ]

        for lesson in childhood_lessons:
            idx_before = len(self.memories)
            self._add_timeline_step(
                phase="thinking",
                description=f"Childhood learning: {lesson['content']}",
                intensity=0.6,
            )
            related = self._find_related_memories(lesson["tags"])
            self._add_memory(
                kind="childhood",
                content=lesson["content"],
                source="auto_childhood",
                tags=lesson["tags"],
                links=related,
            )
            idx_after = len(self.memories) - 1
            if related:
                self._add_timeline_step(
                    phase="cross_reference",
                    description=f"Linking childhood memory {idx_after} to previous memories {related}.",
                    intensity=0.5,
                )

        self.childhood_completed = True
        self._add_timeline_step(
            phase="decision",
            description="Childhood phase complete. Ready to respond to Alex.",
            intensity=0.9,
        )

    # ------------------------------
    #  PROCESS USER QUESTION
    # ------------------------------
    def process_question(self, question: str) -> str:
        self.run_childhood_if_needed()

        # Thinking: understand intent
        self._add_timeline_step(
            phase="thinking",
            description=f"Receiving Alex's question: '{question}'. Parsing intent and key themes.",
            intensity=0.7,
        )

        # Simple tag extraction
        words = [w.strip(".,!?").lower() for w in question.split()]
        tags = [w for w in words if len(w) > 3]

        # Recall memories
        related_indices = self._find_related_memories(tags)
        if related_indices:
            self._add_timeline_step(
                phase="recall",
                description=f"Recalling {len(related_indices)} related memories using tags: {tags[:6]}.",
                intensity=0.8,
            )
        else:
            self._add_timeline_step(
                phase="recall",
                description="No strong direct matches in memory; relying on more general childhood structure.",
                intensity=0.4,
            )

        # Cross-reference
        if related_indices:
            related_summaries = [self.memories[i].content for i in related_indices[:3]]
            self._add_timeline_step(
                phase="cross_reference",
                description="Cross-referencing recalled memories to form a coherent answer.",
                intensity=0.7,
            )
        else:
            related_summaries = []

        # Mind-path / high-level mapping
        self._add_timeline_step(
            phase="mind_path",
            description="Tracing a path through childhood concepts, current question tags, and recalled memories.",
            intensity=0.75,
        )

        # Very simple "answer synthesis"
        answer_lines = []
        answer_lines.append("Here’s how I’m thinking about your question, Alex:")
        if tags:
            answer_lines.append(f"- I detected themes like: {', '.join(sorted(set(tags))[:8])}.")
        if related_summaries:
            answer_lines.append("- I’m connecting this to things I learned in my early 'childhood':")
            for s in related_summaries:
                answer_lines.append(f"  • {s}")
        else:
            answer_lines.append("- I don't find specific matches in my earlier memories, so I'm leaning on general patterns.")

        # Decision
        self._add_timeline_step(
            phase="decision",
            description="Committing to a response based on the current memory graph and question.",
            intensity=0.9,
        )

        # Store this interaction as a new experience memory
        self._add_memory(
            kind="experience",
            content=f"Question: {question}",
            source="user_question",
            tags=tags,
            links=related_indices,
        )

        answer_lines.append("")
        answer_lines.append("This is a first version of my reasoning. You can refine me by asking follow-up questions or pushing on specifics.")

        return "\n".join(answer_lines)

    # ------------------------------
    #  EXPORT HELPERS FOR UI
    # ------------------------------
    def timeline_as_dataframe(self) -> pd.DataFrame:
        if not self.timeline:
            return pd.DataFrame(columns=["step", "phase", "description", "intensity"])
        return pd.DataFrame([asdict(t) for t in self.timeline])

    def memory_summary(self) -> List[str]:
        lines = []
        for idx, m in enumerate(self.memories):
            kind = m.kind
            src = m.source
            tags = ", ".join(m.tags[:5])
            links = ", ".join(str(i) for i in m.links) if m.links else "none"
            lines.append(
                f"[{idx}] kind={kind}, source={src}, tags=[{tags}], links→[{links}]"
            )
        return lines


# =========================================================
#  STREAMLIT APP
# =========================================================

def init_session():
    if "a7do" not in st.session_state:
        st.session_state.a7do = A7DOMind()
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""
    if "last_question" not in st.session_state:
        st.session_state.last_question = ""


def main():
    st.set_page_config(
        page_title="SLED AI — A7DO",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    a7do: A7DOMind = st.session_state.a7do

    col_left, col_right = st.columns([2, 1])

    # LEFT: Main interaction
    with col_left:
        st.title("SLED AI — A7DO Cognitive Engine")
        st.markdown("**Welcome, Alex.**")

        st.markdown("### Ask A7DO a question")
        user_q = st.text_input(
            "This field is for your questions (not training data).",
            key="user_question_input",
        )

        if st.button("Send to A7DO"):
            if user_q.strip():
                with st.spinner("A7DO is thinking..."):
                    answer = a7do.process_question(user_q.strip())
                st.session_state.last_answer = answer
                st.session_state.last_question = user_q.strip()

        st.markdown("---")
        st.markdown("### A7DO responds")
        if st.session_state.last_answer:
            st.code(st.session_state.last_answer)
        else:
            st.info("Ask a question above to hear from A7DO.")

        st.markdown("---")
        st.markdown("### A7DO childhood & experience memories (textual summary)")
        mem_lines = a7do.memory_summary()
        if mem_lines:
            for line in mem_lines:
                st.write(line)
        else:
            st.info("No memories yet. As soon as A7DO processes its first question, its childhood will be auto-learned and logged here.")

    # RIGHT: Internal timeline + plots
    with col_right:
        st.markdown("### A7DO internal timeline")

        df = a7do.timeline_as_dataframe()
        if df.empty:
            st.info("No internal activity yet. Ask A7DO a question to see thinking, recall, and mind-pathing.")
        else:
            # Textual timeline
            for _, row in df.iterrows():
                st.write(
                    f"**Step {int(row['step'])} — {row['phase']}** "
                    f"(intensity {row['intensity']:.2f})"
                )
                st.write(f"→ {row['description']}")
                st.write("")

            st.markdown("#### Graphical activity plot")
            # Map phase to a categorical order
            phase_order = ["thinking", "recall", "cross_reference", "mind_path", "decision"]
            df["phase"] = pd.Categorical(df["phase"], categories=phase_order, ordered=True)

            chart = (
                alt.Chart(df)
                .mark_circle(size=120)
                .encode(
                    x=alt.X("step:Q", title="Timeline step"),
                    y=alt.Y("phase:N", title="Cognitive phase"),
                    color=alt.Color("phase:N", legend=None),
                    size=alt.Size("intensity:Q", title="Intensity", scale=alt.Scale(range=[50, 400])),
                    tooltip=["step", "phase", "description", "intensity"],
                )
                .properties(height=300)
            )

            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        if st.button("Reset A7DO (new birth)"):
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
