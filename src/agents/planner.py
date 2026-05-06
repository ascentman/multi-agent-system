import json
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import MAX_RETRIES
from src.llm import call_llm, get_json_llm, get_llm
from src.prompts import (
    DECOMPOSE_SYSTEM,
    DECOMPOSE_USER,
    LANG_SUFFIX,
    QUERY_SYSTEM,
    QUERY_USER,
    VALIDATE_SYSTEM,
    VALIDATE_USER,
)
from src.state import AgentState


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM output, stripping markdown code fences if present."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text.strip())


def planner_decompose(state: AgentState) -> dict:
    """Break the user request into 3-4 specific research subtasks."""
    lang = state.get("language", "en")
    lang_note = LANG_SUFFIX.get(lang, "")
    llm = get_json_llm()
    messages = [
        SystemMessage(content=DECOMPOSE_SYSTEM),
        HumanMessage(content=DECOMPOSE_USER.format(company=state["user_request"]) + lang_note),
    ]
    time.sleep(2)
    parsed = _parse_json(call_llm(llm, messages))
    subtasks = parsed.get("subtasks", [])

    numbered = " | ".join(f"({i+1}) {s[:50]}{'…' if len(s)>50 else ''}" for i, s in enumerate(subtasks))
    trace_msg = f"**Planner:** Decomposed into {len(subtasks)} subtasks — {numbered}"
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

    is_retry = state.get("validation_verdict") == "invalid"

    retry_context = ""
    if is_retry:
        reason = state.get("validation_reason", "")
        prev_query = state.get("current_query", "")
        retry_context = f"Previous query '{prev_query}' failed validation: {reason}. Try a completely different angle or add a year like 2024."

    llm = get_llm()
    messages = [
        SystemMessage(content=QUERY_SYSTEM),
        HumanMessage(content=QUERY_USER.format(subtask=subtask, retry_context=retry_context)),
    ]
    time.sleep(2)
    query = call_llm(llm, messages).strip().strip('"')

    label = "Retry query" if is_retry else "Query"
    q_display = query[:50] + "…" if len(query) > 50 else query
    short = subtask[:50] + "…" if len(subtask) > 50 else subtask
    trace_msg = (
        f"**Planner → {label}:** `{q_display}` "
        f'_(subtask {state["current_subtask_idx"] + 1}/{len(state["subtasks"])}: "{short}")_'
    )

    new_retry_count = retry_count + 1 if is_retry else retry_count

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
    time.sleep(2)
    parsed = _parse_json(call_llm(llm, messages))
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
    short_done = subtask[:55] + "…" if len(subtask) > 55 else subtask
    trace_msg = (
        f'**Planner:** Subtask {state["current_subtask_idx"] + 1} done — "{short_done}". Moving to subtask {new_idx + 1}.'
        if new_idx < len(state["subtasks"])
        else f'**Planner:** All {len(state["subtasks"])} subtasks complete — handing off to Synthesizer.'
    )

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


# ── Routing helpers ──────────────────────────────────────────────────────────

def route_after_validate(state: AgentState) -> str:
    verdict = state.get("validation_verdict", "invalid")
    retries = state.get("retry_count", 0)
    if verdict == "invalid" and retries < MAX_RETRIES:
        return "retry"
    return "accept"


def route_after_next_subtask(state: AgentState) -> str:
    if state["current_subtask_idx"] < len(state["subtasks"]):
        return "more"
    return "done"
