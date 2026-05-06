"""Smoke tests with monkeypatched LLM + tools — no real API calls."""
import pytest

from src.state import AgentState


FAKE_SUBTASKS = [
    "What does FakeCo do?",
    "Who are FakeCo's competitors?",
]

FAKE_NOTES = "- FakeCo makes widgets\n- Competitors: WidgetCorp, AcmeWidgets"


def _base_state(**overrides) -> AgentState:
    state: AgentState = {
        "user_request": "FakeCo",
        "subtasks": FAKE_SUBTASKS,
        "current_subtask_idx": 0,
        "current_query": "FakeCo overview",
        "pending_notes": "",
        "notes": {},
        "retry_count": 0,
        "validation_verdict": "",
        "validation_reason": "",
        "final_report": "",
        "trace": [],
    }
    state.update(overrides)
    return state


# ── planner_decompose ────────────────────────────────────────────────────────

def test_planner_decompose(monkeypatch):
    import json
    from src.agents import planner

    class FakeLLM:
        def invoke(self, _):
            class R:
                content = json.dumps({"subtasks": FAKE_SUBTASKS})
            return R()

    monkeypatch.setattr(planner, "get_json_llm", lambda **kw: FakeLLM())
    state = _base_state(subtasks=[], current_subtask_idx=0)
    delta = planner.planner_decompose(state)

    assert delta["subtasks"] == FAKE_SUBTASKS
    assert delta["current_subtask_idx"] == 0
    assert delta["notes"] == {}
    assert len(delta["trace"]) == 1


# ── planner_query ────────────────────────────────────────────────────────────

def test_planner_query(monkeypatch):
    from src.agents import planner

    class FakeLLM:
        def invoke(self, _):
            class R:
                content = "FakeCo company overview"
            return R()

    monkeypatch.setattr(planner, "get_llm", lambda **kw: FakeLLM())
    state = _base_state()
    delta = planner.planner_query(state)

    assert delta["current_query"] == "FakeCo company overview"
    assert len(delta["trace"]) == 1


# ── researcher ───────────────────────────────────────────────────────────────

def test_researcher(monkeypatch):
    from src.agents import researcher as r_module

    monkeypatch.setattr(r_module, "web_search", lambda q, **kw: [
        {"title": "FakeCo", "href": "https://fakeco.com", "body": "FakeCo makes widgets."}
    ])
    monkeypatch.setattr(r_module, "fetch_url", lambda url, **kw: "FakeCo makes widgets for industry.")

    class FakeLLM:
        def invoke(self, _):
            class R:
                content = FAKE_NOTES
            return R()

    monkeypatch.setattr(r_module, "get_llm", lambda **kw: FakeLLM())
    state = _base_state()
    delta = r_module.researcher(state)

    assert FAKE_NOTES in delta["pending_notes"]
    assert len(delta["trace"]) == 1


# ── planner_validate ─────────────────────────────────────────────────────────

def test_planner_validate_valid(monkeypatch):
    import json
    from src.agents import planner

    class FakeLLM:
        def invoke(self, _):
            class R:
                content = json.dumps({"verdict": "valid", "reason": "Looks good."})
            return R()

    monkeypatch.setattr(planner, "get_json_llm", lambda **kw: FakeLLM())
    state = _base_state(pending_notes=FAKE_NOTES)
    delta = planner.planner_validate(state)

    assert delta["validation_verdict"] == "valid"


def test_planner_validate_invalid(monkeypatch):
    import json
    from src.agents import planner

    class FakeLLM:
        def invoke(self, _):
            class R:
                content = json.dumps({"verdict": "invalid", "reason": "Too vague."})
            return R()

    monkeypatch.setattr(planner, "get_json_llm", lambda **kw: FakeLLM())
    state = _base_state(pending_notes="some notes")
    delta = planner.planner_validate(state)

    assert delta["validation_verdict"] == "invalid"


# ── next_subtask ─────────────────────────────────────────────────────────────

def test_next_subtask_promotes_notes():
    from src.agents.planner import next_subtask

    state = _base_state(pending_notes=FAKE_NOTES, validation_verdict="valid")
    delta = next_subtask(state)

    assert delta["current_subtask_idx"] == 1
    assert FAKE_SUBTASKS[0] in delta["notes"]
    assert delta["notes"][FAKE_SUBTASKS[0]] == FAKE_NOTES
    assert delta["retry_count"] == 0


# ── route_after_validate ─────────────────────────────────────────────────────

def test_route_retry():
    from src.agents.planner import route_after_validate
    state = _base_state(validation_verdict="invalid", retry_count=0)
    assert route_after_validate(state) == "retry"


def test_route_accept_when_retries_exhausted():
    from src.agents.planner import route_after_validate
    from src.config import MAX_RETRIES
    state = _base_state(validation_verdict="invalid", retry_count=MAX_RETRIES)
    assert route_after_validate(state) == "accept"


def test_route_accept_when_valid():
    from src.agents.planner import route_after_validate
    state = _base_state(validation_verdict="valid", retry_count=0)
    assert route_after_validate(state) == "accept"


# ── route_after_next_subtask ─────────────────────────────────────────────────

def test_route_more_subtasks():
    from src.agents.planner import route_after_next_subtask
    state = _base_state(current_subtask_idx=0)
    assert route_after_next_subtask(state) == "more"


def test_route_done():
    from src.agents.planner import route_after_next_subtask
    state = _base_state(current_subtask_idx=len(FAKE_SUBTASKS))
    assert route_after_next_subtask(state) == "done"


# ── graph compiles ───────────────────────────────────────────────────────────

def test_graph_compiles():
    from src.graph import app
    assert app is not None
    mermaid = app.get_graph().draw_mermaid()
    assert "planner_decompose" in mermaid
    assert "synthesizer" in mermaid
