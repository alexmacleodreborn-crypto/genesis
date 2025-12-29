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


def main():
    st.set_page_config(
        page_title="SLED AI — A7DO",
        page_icon="🧠",
        layout="wide",
    )

    init_session()
    mind: A7DOMind = st.session_state.mind

    col_left, col_right = st.columns([2, 1])

    # LEFT: main interaction
    with col_left:
        st.title("SLED AI — A7DO Cognitive Engine")
        st.caption(
            f"Developmental stage: {mind.developmental_stage()} · "
            f"Age: {mind.interaction_count} interactions · "
            f"Total memories: {mind.memory_size()}"
        )
        st.caption(mind.thinking_style_summary())
        st.markdown("**Welcome, Alex.**")

        st.markdown("### Ask A7DO a question")
        user_q = st.text_input(
            "This field is for your questions (not training data).",
            key="user_question_input",
        )

        if st.button("Send to A7DO"):
            if user_q.strip():
                with st.spinner("A7DO is thinking..."):
                    result = mind.process_question(user_q.strip())
                st.session_state.last_answer = result["answer"]
                st.session_state.last_question = user_q.strip()

        st.markdown("---")
        st.markdown("### A7DO responds")
        if st.session_state.last_answer:
            st.code(st.session_state.last_answer)
        else:
            st.info("Ask a question above to hear from A7DO.")

        st.markdown("---")
        st.markdown("### What A7DO just learned from this question")
        learning_summary = mind.learning_summary()
        if learning_summary:
            st.markdown(learning_summary)
        else:
            st.info("Once you ask a question, A7DO will show you what it learned here.")

        st.markdown("---")
        st.markdown("### A7DO childhood & experience memories (textual summary)")
        mem_lines = mind.memory_summary_lines()
        if mem_lines:
            for line in mem_lines:
                st.write(line)
        else:
            st.info("No memories yet. As soon as A7DO processes its first question, its childhood will be auto-learned and logged here.")

    # RIGHT: internal timeline + mind-map
    with col_right:
        st.markdown("### A7DO internal timeline")
        records = mind.timeline_records()
        if not records:
            st.info("No internal activity yet. Ask A7DO a question to see thinking, recall, and mind-pathing.")
        else:
            df = pd.DataFrame(records)
            for _, row in df.iterrows():
                st.write(
                    f"**Step {int(row['step'])} — {row['phase']}** "
                    f"(intensity {row['intensity']:.2f}, emotion {row['emotion_valence']:+.2f})"
                )
                st.write(f"→ {row['description']}")
                st.write("")

            st.markdown("#### Graphical activity plot")
            phase_order = ["thinking", "recall", "cross_reference", "mind_path", "decision"]
            df["phase"] = pd.Categorical(df["phase"], categories=phase_order, ordered=True)

            chart = (
                alt.Chart(df)
                .mark_circle()
                .encode(
                    x=alt.X("step:Q", title="Timeline step"),
                    y=alt.Y("phase:N", title="Cognitive phase"),
                    color=alt.Color("emotion_valence:Q", title="Emotion", scale=alt.Scale(scheme="redblue")),
                    size=alt.Size("intensity:Q", title="Intensity", scale=alt.Scale(range=[50, 400])),
                    tooltip=["step", "phase", "description", "intensity", "emotion_valence"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.markdown("### A7DO memory mind-map")

        graph = mind.build_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]

        if not nodes:
            st.info("No memories yet to display in the mind-map.")
        else:
            nodes_df = pd.DataFrame(nodes)
            if edges:
                edges_df = pd.DataFrame(edges)
            else:
                edges_df = pd.DataFrame(columns=["source", "target"])

            st.caption(
                "Nodes are memories. Position is abstract (radial), "
                "colour is kind of memory, size is emotional intensity."
            )

            nodes_chart = (
                alt.Chart(nodes_df)
                .mark_circle()
                .encode(
                    x=alt.X("x:Q", title=None, axis=None),
                    y=alt.Y("y:Q", title=None, axis=None),
                    color=alt.Color("kind:N", title="Memory kind"),
                    size=alt.Size(
                        "abs(emotion_valence):Q",
                        title="|Emotion|",
                        scale=alt.Scale(range=[50, 600]),
                    ),
                    tooltip=["id", "label", "kind", "emotion_valence"],
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
                    .mark_line(stroke="#999", strokeWidth=1, opacity=0.4)
                    .encode(
                        x="x_source:Q",
                        y="y_source:Q",
                        x2="x_target:Q",
                        y2="y_target:Q",
                    )
                )

                mindmap_chart = (edges_chart + nodes_chart).properties(height=350)
            else:
                mindmap_chart = nodes_chart.properties(height=350)

            st.altair_chart(mindmap_chart, use_container_width=True)

        st.markdown("---")
        if st.button("Reset A7DO (new birth)"):
            st.session_state.clear()
            st.experimental_rerun()


if __name__ == "__main__":
    main()
