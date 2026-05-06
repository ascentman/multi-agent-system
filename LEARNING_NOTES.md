# Learning Notes — Multi-Agent Competitive Research Tool

A concept-by-concept companion to the code. Read this alongside the source files.

---

## Concept 1: What is a multi-agent system?

A **multi-agent system** is a program where multiple AI "agents" collaborate on a task.
Each agent has a specific role and only does that role well.

In this project:
- **Planner** knows how to break problems apart and judge results. It doesn't search.
- **Researcher** knows how to find information. It doesn't write reports.
- **Synthesizer** knows how to write structured reports. It doesn't search.

Why split them? A single LLM asked to "research Anthropic and write a report" tends to hallucinate
when it runs out of real information. Separating search (grounded in real web data) from synthesis
(structuring validated notes) produces more reliable output.

---

## Concept 2: LangGraph — state machines for agents

LangGraph models your agent system as a **directed graph**:

- **Nodes** = functions (your agents). Each node receives the current state and returns a delta.
- **Edges** = fixed transitions between nodes.
- **Conditional edges** = branches: "go here if X, go there if Y".

The key insight: **state is shared memory**. Every agent reads from and writes to the same
`AgentState` TypedDict. No agent calls another directly — they just write to state and the
graph routes to the next node.

Look at `src/state.py` to see every piece of information that flows through the system.
Look at `src/graph.py` to see how nodes connect.

---

## Concept 3: The AgentState TypedDict

```python
class AgentState(TypedDict):
    user_request: str
    subtasks: list[str]
    current_subtask_idx: int
    current_query: str
    pending_notes: str        # ← IMPORTANT: staging area
    notes: dict[str, str]
    retry_count: int
    validation_verdict: Literal["valid", "invalid", ""]
    validation_reason: str
    final_report: str
    trace: list[str]
```

Notice `pending_notes` vs `notes`:
- `pending_notes` = researcher's candidate output, not yet validated
- `notes` = validated, committed research

This is like a code review gate: you can't merge to `main` (notes) until someone reviews the PR
(validator). The `next_subtask` node is the "merge" step.

---

## Concept 4: Tool use (search + fetch)

Look at `src/tools/search.py` and `src/tools/fetch.py`.

These are **just Python functions**. There's no magic. The "tool use" pattern means the LLM
*decides* when to call them — but in this architecture, the researcher node always calls them
as part of its logic. The LLM's job is summarization, not search.

Why fetch full pages when we have search snippets?
Search snippets are ~150 chars — too short for a real briefing. Fetching the top 1–2 URLs
gets 2000–4000 chars of substantive content. `trafilatura` strips navigation, ads, and
boilerplate, leaving clean article text.

---

## Concept 5: Structured output (JSON mode)

The planner's `decompose` and `validate` nodes use `get_json_llm()` which sets:
```python
model_kwargs={"response_format": {"type": "json_object"}}
```

Without this, the LLM might return `{"subtasks": [...]}` wrapped in markdown code fences, or
add explanation text. JSON mode forces it to output only valid JSON. This is important for
parsing reliability — one bad response breaks the whole pipeline.

---

## Concept 6: The Validator-Retry Pattern ("Reflexion")

The `planner_validate` node asks: "Are these notes on-topic, non-empty, and useful?"

If **invalid** and retries < `MAX_RETRIES`:
  - `route_after_validate` returns `"retry"`
  - LangGraph routes back to `planner_query`
  - `planner_query` sees `validation_verdict == "invalid"` and crafts a better search query
  - `retry_count` increments

This is a simplified version of [Reflexion](https://arxiv.org/abs/2303.11366) — an AI pattern
where the model evaluates its own output and tries again with refined inputs.

The conditional edge in `src/graph.py`:
```python
builder.add_conditional_edges(
    "planner_validate",
    route_after_validate,   # function returning "retry" or "accept"
    {"retry": "planner_query", "accept": "next_subtask"},
)
```

---

## Concept 7: Streaming intermediate steps to the UI

Without streaming, the user sees a spinner for 30–60 seconds, then suddenly a full report.
That's opaque — they learn nothing about what happened.

With streaming (`app.stream(..., stream_mode="updates")`), LangGraph yields the state delta
after *each node completes*. The Gradio generator in `app.py` appends each node's trace message
and yields `(trace_md, report_md)` after every step.

This is the whole pedagogical point: **the architecture becomes visible during execution**.

---

## Concept 8: Visualizing the graph

Run this in a Python REPL to see the architecture as a Mermaid diagram:
```python
from src.graph import app
print(app.get_graph().draw_mermaid())
```

Paste the output into [mermaid.live](https://mermaid.live) to see the graph.
The conditional retry loop will appear as a back-edge from `planner_validate` to `planner_query`.

---

## Concept 9: HF Spaces — free public hosting

HF Spaces runs your `app.py` on a free container. Key conventions:
1. `app.py` = entrypoint (by convention, not config)
2. `requirements.txt` = auto-installed on build
3. Secrets added in Space settings are injected as environment variables
4. Every `git push space main` triggers a rebuild (~3 min)

The `---` YAML block at the top of `README.md` is the Space metadata card — HF reads it to
configure the display name, emoji, and SDK.

---

## Stretch Goal: Parallelizing with LangGraph's Send API

In the MVP, subtasks run sequentially (one at a time). For faster runs you can use the
[`Send` API](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/) to fan out all
subtasks in parallel, collecting results via a `Reducer`.

This is a great Phase 2 exercise once you understand the sequential version well.
