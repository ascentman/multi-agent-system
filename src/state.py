from typing import TypedDict, Literal


class AgentState(TypedDict):
    user_request: str               # e.g. "Acme Corp"
    subtasks: list[str]             # decomposed research questions
    current_subtask_idx: int        # which subtask we're on
    current_query: str              # current search query (refined on retry)
    pending_notes: str              # candidate notes awaiting validation
    notes: dict[str, str]           # subtask -> validated research notes
    retry_count: int                # retries on current subtask
    validation_verdict: Literal["valid", "invalid", ""]
    validation_reason: str
    final_report: str
    language: str                   # "en" or "ua" — output language for notes/report
    trace: list[str]                # human-readable log streamed to the UI
