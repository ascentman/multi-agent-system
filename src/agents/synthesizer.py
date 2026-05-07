import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import call_llm, get_llm
from src.prompts import LANG_SUFFIX, SYNTHESIZER_SYSTEM, SYNTHESIZER_USER
from src.state import AgentState


def synthesizer(state: AgentState) -> dict:
    """Aggregate all validated notes into a structured briefing."""
    notes = state.get("notes", {})

    notes_block = "\n\n".join(
        f"### {subtask}\n{text}" for subtask, text in notes.items()
    )
    if not notes_block:
        notes_block = "No research notes available."

    lang = state.get("language", "en")
    lang_note = LANG_SUFFIX.get(lang, "")
    llm = get_llm(temperature=0.3)
    messages = [
        SystemMessage(content=SYNTHESIZER_SYSTEM),
        HumanMessage(content=SYNTHESIZER_USER.format(notes_block=notes_block) + lang_note),
    ]
    time.sleep(2)
    report = call_llm(llm, messages).strip()

    # Check if report indicates failure to find information
    failure_indicators = [
        "не вдалося ідентифікувати",
        "відсутня пряма згадка",
        "no information found",
        "unable to identify",
        "no specific information",
        "недостатньо інформації",
    ]

    if any(indicator in report.lower() for indicator in failure_indicators):
        report = f"""# Research Results

**Note:** Limited verified information was found about this company in publicly available sources.

## Summary
The research agents searched multiple sources but could not find comprehensive, verified information about this specific company. This could mean:

- The company operates under a different legal name or brand
- Limited online presence or media coverage
- Primarily a local/regional business with minimal digital footprint
- The company name provided may be incomplete or informal

## Recommendations
1. Verify the exact legal/company name
2. Check alternative spellings or brand names
3. Search for parent company or subsidiaries
4. Look for official website, social media, or business registries

## Sources Searched
Research was conducted using web search engines and publicly available business directories.
"""

    trace_msg = f"**Synthesizer:** Writing briefing from {len(notes)} research section(s)…"
    return {
        "final_report": report,
        "trace": state.get("trace", []) + [trace_msg],
    }
