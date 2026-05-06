from langgraph.graph import END, START, StateGraph

from src.agents.planner import (
    next_subtask,
    planner_decompose,
    planner_query,
    planner_validate,
    route_after_next_subtask,
    route_after_validate,
)
from src.agents.researcher import researcher
from src.agents.synthesizer import synthesizer
from src.state import AgentState


def build_graph():
    builder = StateGraph(AgentState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    builder.add_node("planner_decompose", planner_decompose)
    builder.add_node("planner_query", planner_query)
    builder.add_node("researcher", researcher)
    builder.add_node("planner_validate", planner_validate)
    builder.add_node("next_subtask", next_subtask)
    builder.add_node("synthesizer", synthesizer)

    # ── Direct edges ─────────────────────────────────────────────────────────
    builder.add_edge(START, "planner_decompose")
    builder.add_edge("planner_decompose", "planner_query")
    builder.add_edge("planner_query", "researcher")
    builder.add_edge("researcher", "planner_validate")
    builder.add_edge("synthesizer", END)

    # ── Conditional: after validation → retry query OR accept + advance ──────
    builder.add_conditional_edges(
        "planner_validate",
        route_after_validate,
        {
            "retry": "planner_query",   # bump retry_count happens in planner_query
            "accept": "next_subtask",
        },
    )

    # ── Conditional: after advancing → next subtask OR synthesize ────────────
    builder.add_conditional_edges(
        "next_subtask",
        route_after_next_subtask,
        {
            "more": "planner_query",
            "done": "synthesizer",
        },
    )

    return builder.compile()


app = build_graph()
