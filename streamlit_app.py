import streamlit as st
import pandas as pd
import altair as alt

from a7do import A7DOMind


def init_session():
    if "mind" not in st.session_state:
        st.session_state.mind = A7DOMind()
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""
    if "last_question" not in st.session_state:
        st.session_state.last_question = ""
    if "last_mode" not in st.session_state:
        st.session_state.last_mode = None


def main():
    st.set_page_config(
        page_title="SLED AI — A7DO",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    mind: A7DOMind = st.session_state.mind

    # Top-level header
    st.title("SLED AI — A7DO Cognitive Engine")
    st.caption(
        f"Developmental stage: {mind.developmental_stage()} · "
        f"Age: {mind.interaction_count} interactions · "
        f"Total memories: {mind.memory_size()}"
    )
    st.caption(mind.thinking_style_summary())

    # Character panel
    st.markdown("### Who I am right now")
    st.write(mind.generate_character_paragraph())

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    # LEFT: main interaction
    with col_left:
        st.markdown("### Ask A7DO a question")
        user_q = st.text_input(
            "This field is for your questions (not training data).",
            key="user_question_input",
        )

        col_q1, col_q2 = st.columns([1, 1])
        with col_q1:
            send = st.button("Send to A7DO")
        with col_q2:
            dev = st.button("Advance development (no question)")

        if dev:
            mind.maybe_auto_develop()

        if send and user_q.strip():
            with st.spinner("A7DO is thinking..."):
                result = mind.process_question(user_q.strip())
            st.session_state.last_answer = result["answer"]
            st.session_state.last_question = user_q.strip()
            st.session_state.last_mode = result["mode"]

        st.markdown("---")
        st.markdown("### A7DO responds")

        if st.session_state.last_answer:
            mode = st.session_state.last_mode
            if mode == "need_more_info":
                st.info("A7DO needs more information to answer clearly.")
            elif mode == "research":
                st.info(
                    "A7DO has given an internal answer and is ready to be paired with external research if you want."
                )
            else:
                st.success("A7DO has committed to an answer based on its internal development and memory graph.")

            st.code(st.session_state.last_answer)
        else:
            st.info(
                "Ask a question above to hear from A7DO. "
                "You can also advance its development without a question using the button."
            )

        st.markdown("---")
        st.markdown("### What A7DO just learned from the last question")
        learning_summary = mind.learning_summary()
        if learning_summary:
            st.markdown(learning_summary)
        else:
            st.info("Once you ask a question, A7DO will show you what it learned here.")

        st.markdown("---")
        st.markdown("### A7DO memories (latest slice)")
        mem_lines = mind.memory_summary_lines()
        if mem_lines:
            for line in mem_lines[-80:]:
                st.write(line)
        else:
            st.info("No memories yet — this should only appear briefly at first launch.")

    # RIGHT: internal timeline + mind-map
    with col_right:
        st.markdown("### Cognitive timeline (plot)")

        records = mind.timeline_records()
        if not records:
            st.info("No internal activity yet. This should disappear quickly as development runs.")
        else:
            df = pd.DataFrame(records)
            phase_order = [
                "thinking",
                "recall",
                "cross_reference",
                "mind_path",
                "decision",
                "development",
                "internal_question",
            ]
            df["phase"] = pd.Categorical(df["phase"], categories=phase_order, ordered=True)

            chart = (
                alt.Chart(df)
                .mark_circle()
                .encode(
                    x=alt.X("step:Q", title="Timeline step"),
                    y=alt.Y("phase:N", title="Cognitive phase"),
                    color=alt.Color(
                        "emotion_valence:Q",
                        title="Emotion",
                        scale=alt.Scale(scheme="redblue"),
                    ),
                    size=alt.Size(
                        "intensity:Q",
                        title="Intensity",
                        scale=alt.Scale(range=[50, 400]),
                    ),
                    tooltip=["step", "phase", "description", "intensity", "emotion_valence"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)

        st.markdown("### Narrative timeline (recent steps)")
        if not records:
            st.info("No narrative timeline yet.")
        else:
            for r in records[-30:]:
                st.write(
                    f"**Step {int(r['step'])} — {r['phase']}** "
                    f"(intensity {r['intensity']:.2f}, emotion {r['emotion_valence']:+.2f})"
                )
                st.write(f"→ {r['description']}")
                st.write("")

        st.markdown("---")
        st.markdown("### Memory mind-map")

        graph = mind.build_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]

        if not nodes:
            st.info("No memories yet to display in the mind-map.")
        else:
            nodes_df = pd.DataFrame(nodes)
            edges_df = pd.DataFrame(edges) if edges else pd.DataFrame(columns=["source", "target"])

            st.caption(
                "Nodes are memories. Active nodes (used in the last answer) are highlighted in red and larger. "
                "Edges between active nodes are bold. Development adds new nodes over time."
            )

            nodes_chart = (
                alt.Chart(nodes_df)
                .mark_circle()
                .encode(
                    x=alt.X("x:Q", axis=None),
                    y=alt.Y("y:Q", axis=None),
                    color=alt.condition(
                        alt.datum.active,
                        alt.value("#ff4b4b"),
                        alt.Color("kind:N"),
                    ),
                    size=alt.condition(
                        alt.datum.active,
                        alt.value(600),
                        alt.Size(
                            "abs(emotion_valence):Q",
                            title="|Emotion|",
                            scale=alt.Scale(range=[50, 300]),
                        ),
                    ),
                    tooltip=["id", "label", "kind", "emotion_valence", "active"],
                )
            )

            if not edges_df.empty:
                edges_df = (
                    edges_df
                    .merge(nodes_df[["id", "x", "y"]], left_on="source", right_on="id")
                    .rename(columns={"x": "x_source", "y": "y_source"})
                    .drop(columns=["id"])
                    .merge(nodes_df[["id", "x", "y"]], left_on="target", right_on="id")
                    .rename(columns={"x": "x_target", "y": "y_target"})
                    .drop(columns=["id"])
                )

                edges_chart = (
                    alt.Chart(edges_df)
                    .mark_line()
                    .encode(
                        x="x_source:Q",
                        y="y_source:Q",
                        x2="x_target:Q",
                        y2="y_target:Q",
                        stroke=alt.condition(
                            alt.datum.active,
                            alt.value("#ff4b4b"),
                            alt.value("#999999"),
                        ),
                        strokeWidth=alt.condition(
                            alt.datum.active,
                            alt.value(3),
                            alt.value(1),
                        ),
                        opacity=alt.condition(
                            alt.datum.active,
                            alt.value(1.0),
                            alt.value(0.3),
                        ),
                    )
                )

                mindmap_chart = (edges_chart + nodes_chart).properties(height=300)
            else:
                mindmap_chart = nodes_chart.properties(height=300)

            st.altair_chart(mindmap_chart, use_container_width=True)

        st.markdown("---")
        if st.button("Reset A7DO (new birth)"):
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
