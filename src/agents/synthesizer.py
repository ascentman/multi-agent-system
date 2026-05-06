import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import call_llm, get_llm
from src.prompts import SYNTHESIZER_SYSTEM, SYNTHESIZER_USER
from src.state import AgentState


def synthesizer(state: AgentState) -> dict:
    """Aggregate all validated notes into a structured competitive briefing."""
    notes = state.get("notes", {})

    notes_block = "\n\n".join(
        f"### {subtask}\n{text}" for subtask, text in notes.items()
    )
    if not notes_block:
        notes_block = "No research notes available."

    llm = get_llm(temperature=0.3)
    messages = [
        SystemMessage(content=SYNTHESIZER_SYSTEM),
        HumanMessage(content=SYNTHESIZER_USER.format(notes_block=notes_block)),
    ]
    time.sleep(2)
    report = call_llm(llm, messages).strip()

    trace_msg = "**Synthesizer:** Competitive briefing generated."
    return {
        "final_report": report,
        "trace": state.get("trace", []) + [trace_msg],
    }
