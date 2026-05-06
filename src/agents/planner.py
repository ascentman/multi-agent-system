import json
import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import MAX_RETRIES
from src.llm import get_json_llm, get_llm
from src.prompts import (
    DECOMPOSE_SYSTEM,
    DECOMPOSE_USER,
    QUERY_SYSTEM,
    QUERY_USER,
    VALIDATE_SYSTEM,
    VALIDATE_USER,
)
from src.state import AgentState


def planner_decompose(state: AgentState) -> dict:
    """Break the user request into 3-4 specific research subtasks."""
    llm = get_json_llm()
    messages = [
        SystemMessage(content=DECOMPOSE_SYSTEM),
        HumanMessage(content=DECOMPOSE_USER.format(company=state["user_request"])),
    ]
    time.sleep(0.3)
    response = llm.invoke(messages)
    parsed = json.loads(response.content)
    subtasks = parsed.get("subtasks", [])

    trace_msg = f"**Planner:** Decomposed into {len(subtasks)} subtasks: {subtasks}"
    return {
        "subtasks": subtasks,
        "current_subtask_idx": 0,
        "retry_count": 0,
        "notes": {},
        "pending_notes": "",
        "validation_verdict": "",
        "validation_reason": "",
        "trace": state.get("trace", []) + [trace_msg],
    }


def planner_query(state: AgentState) -> dict:
    """Generate a focused search query for the current subtask."""
    subtask = state["subtasks"][state["current_subtask_idx"]]
    retry_count = state.get("retry_count", 0)

    retry_context = ""
    if retry_count > 0:
        reason = state.get("validation_reason", "")
        prev_query = state.get("current_query", "")
        retry_context = f"Previous query '{prev_query}' failed: {reason}. Try a different angle."

    llm = get_llm()
    messages = [
        SystemMessage(content=QUERY_SYSTEM),
        HumanMessage(content=QUERY_USER.format(subtask=subtask, retry_context=retry_context)),
    ]
    time.sleep(0.3)
    query = llm.invoke(messages).content.strip().strip('"')

    label = "Retry query" if retry_count > 0 else "Query"
    trace_msg = f"**Planner → {label}:** `{query}` _(subtask {state['current_subtask_idx'] + 1}/{len(state['subtasks'])})_"

    # Increment retry_count only when this is an actual retry (verdict was invalid)
    new_retry_count = retry_count + 1 if state.get("validation_verdict") == "invalid" else retry_count

    return {
        "current_query": query,
        "retry_count": new_retry_count,
        "trace": state.get("trace", []) + [trace_msg],
    }


def planner_validate(state: AgentState) -> dict:
    """Validate that the researcher's pending notes answer the current subtask."""
    subtask = state["subtasks"][state["current_subtask_idx"]]
    pending = state.get("pending_notes", "")

    llm = get_json_llm()
    messages = [
        SystemMessage(content=VALIDATE_SYSTEM),
        HumanMessage(content=VALIDATE_USER.format(subtask=subtask, notes=pending)),
    ]
    time.sleep(0.3)
    response = llm.invoke(messages)
    parsed = json.loads(response.content)
    verdict = parsed.get("verdict", "invalid")
    reason = parsed.get("reason", "")

    trace_msg = f"**Validator:** `{verdict}` — {reason}"
    return {
        "validation_verdict": verdict,
        "validation_reason": reason,
        "trace": state.get("trace", []) + [trace_msg],
    }


def next_subtask(state: AgentState) -> dict:
    """Promote pending notes (valid or retry-exhausted) and advance to next subtask."""
    subtask = state["subtasks"][state["current_subtask_idx"]]
    notes = dict(state.get("notes", {}))
    pending = state.get("pending_notes", "")

    if pending:
        notes[subtask] = pending
    else:
        notes[subtask] = "Limited information available."

    new_idx = state["current_subtask_idx"] + 1
    trace_msg = f"**Planner:** Subtask {state['current_subtask_idx'] + 1} complete. Moving to subtask {new_idx + 1}." if new_idx < len(state["subtasks"]) else "**Planner:** All subtasks complete. Handing off to Synthesizer."

    return {
        "notes": notes,
        "current_subtask_idx": new_idx,
        "retry_count": 0,
        "current_query": "",
        "pending_notes": "",
        "validation_verdict": "",
        "validation_reason": "",
        "trace": state.get("trace", []) + [trace_msg],
    }


# ── Routing helpers (used as conditional edge functions in graph.py) ─────────

def route_after_validate(state: AgentState) -> str:
    """Route: retry planner_query if invalid + retries left, else next_subtask."""
    verdict = state.get("validation_verdict", "invalid")
    retries = state.get("retry_count", 0)
    if verdict == "invalid" and retries < MAX_RETRIES:
        return "retry"
    return "accept"


def route_after_next_subtask(state: AgentState) -> str:
    """Route: more subtasks → planner_query, all done → synthesizer."""
    if state["current_subtask_idx"] < len(state["subtasks"]):
        return "more"
    return "done"
