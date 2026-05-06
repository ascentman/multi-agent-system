import re
import gradio as gr

from src.graph import app
from src.state import AgentState

_NODE_TO_AGENT = {
    "planner_decompose": "planner",
    "planner_query": "planner",
    "planner_validate": "planner",
    "next_subtask": "planner",
    "researcher": "researcher",
    "synthesizer": "synthesizer",
}

_AGENT_META = [
    ("planner",     "Planner",     "#2563eb", "Decomposes task, generates search queries, validates results"),
    ("researcher",  "Researcher",  "#0891b2", "Web search, page fetch, content extraction"),
    ("synthesizer", "Synthesizer", "#b45309", "Synthesizes research notes into final briefing"),
]

_TRACE_COLORS = {
    "planner":     "#2563eb",
    "validator":   "#16a34a",
    "invalid":     "#dc2626",
    "researcher":  "#0891b2",
    "synthesizer": "#b45309",
    "system":      "#64748b",
}

ARCH_CSS = """
@keyframes agentPulse {
  0%,100% { transform:scale(1); }
  50%      { transform:scale(1.03); }
}
"""

CSS = """
/* ── Force light mode ─────────────────────────────────── */
body,
.gradio-container,
.gradio-container > .main,
.gradio-container > .main > .wrap,
.gradio-container > .main > .wrap > .gap {
  background: #f1f5f9 !important;
  color: #1e293b !important;
}

/* ── Typography ───────────────────────────────────────── */
.gradio-container {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif !important;
}

/* ── Trace panel ──────────────────────────────────────── */
#trace-panel {
  max-height: 64vh;
  overflow-y: auto;
  padding: 6px;
  background: #e8edf3;
  border-radius: 10px;
  border: 1px solid #d1d9e0;
}

/* ── Report panel ─────────────────────────────────────── */
#report-panel {
  background: #ffffff !important;
  border-radius: 10px !important;
  border: 1px solid #d1d9e0 !important;
  padding: 16px 20px !important;
  min-height: 200px;
}

/* ── Input row ────────────────────────────────────────── */
.section-label {
  font-size: .78em;
  font-weight: 700;
  color: #475569;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin: 0 0 6px;
}

footer { display: none !important; }
"""


def _render_architecture(active: str = "") -> str:
    parts = [f"<style>{ARCH_CSS}</style>"]
    parts.append(
        '<div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;'
        'gap:0;padding:20px 28px;background:#ffffff;border:1px solid #d1d9e0;border-radius:14px;">'
    )
    for i, (key, name, color, desc) in enumerate(_AGENT_META):
        is_active = active == key
        if is_active:
            box = (
                f"border:2px solid {color};"
                f"background:#f0f7ff;"
                f"outline:3px solid {color}33;outline-offset:3px;"
                "animation:agentPulse 1.6s ease-in-out infinite;"
            )
            title = f"color:{color};font-weight:700;font-size:.92em;"
            badge = (
                f'<span style="background:{color};color:#fff;font-size:.62em;'
                f'padding:2px 7px;border-radius:8px;margin-left:7px;vertical-align:middle;'
                f'letter-spacing:.05em;font-weight:700">ACTIVE</span>'
            )
        else:
            box = "border:2px solid #e2e8f0;background:#f8fafc;"
            title = "color:#94a3b8;font-weight:600;font-size:.92em;"
            badge = ""

        parts.append(
            f'<div style="{box}border-radius:10px;padding:14px 20px;min-width:150px;max-width:220px;transition:all .3s ease;">'
            f'<div style="{title}">{name}{badge}</div>'
            f'<div style="color:#64748b;font-size:.72em;margin-top:5px;line-height:1.45;">{desc}</div>'
            f'</div>'
        )
        if i < len(_AGENT_META) - 1:
            parts.append(
                '<div style="color:#94a3b8;font-size:1.4em;margin:0 10px;align-self:center;flex-shrink:0;">→</div>'
            )
    parts.append("</div>")
    return "".join(parts)


def _classify(msg: str) -> tuple[str, str]:
    if "**Researcher" in msg:
        return "Researcher", _TRACE_COLORS["researcher"]
    if "**Synthesizer" in msg:
        return "Synthesizer", _TRACE_COLORS["synthesizer"]
    if "**Validator" in msg:
        if "`invalid`" in msg:
            return "Validator ✗", _TRACE_COLORS["invalid"]
        return "Validator ✓", _TRACE_COLORS["validator"]
    if "**Planner" in msg:
        return "Planner", _TRACE_COLORS["planner"]
    return "System", _TRACE_COLORS["system"]


def _md_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="display:inline-block;max-width:min(100%,38ch);overflow:hidden;'
        r'text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;'
        r'background:#e2e8f0;color:#334155;padding:1px 6px;border-radius:4px;font-size:.82em;">\1</code>',
        text,
    )
    text = re.sub(r"_\((.+?)\)_", r'<span style="color:#94a3b8;font-size:.8em">(\1)</span>', text)
    return text


def _render_trace(messages: list[str]) -> str:
    if not messages:
        return '<p style="color:#94a3b8;padding:16px;font-style:italic;font-size:.88em;">Waiting to start…</p>'

    cards = []
    for i, msg in enumerate(messages, 1):
        label, color = _classify(msg)
        cards.append(
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin:5px 0;animation:fadein .2s ease">'
            f'<div style="flex:1;min-width:0;background:#ffffff;border:1px solid #dde3eb;'
            f'border-left:3px solid {color};border-radius:0 8px 8px 0;'
            f'padding:9px 12px;font-size:.84em;line-height:1.7;color:#1e293b;word-break:break-word;overflow-wrap:break-word;">'
            f'<span style="display:inline-block;background:{color};color:#fff;'
            f'font-size:.64em;font-weight:700;padding:2px 8px;border-radius:8px;'
            f'margin-right:8px;letter-spacing:.05em;vertical-align:middle;'
            f'white-space:nowrap;margin-bottom:2px">{label.upper()}</span>'
            f'{_md_to_html(msg)}'
            f'</div>'
            f'<span style="color:#94a3b8;font-size:.68em;min-width:22px;text-align:right;'
            f'padding-top:12px;flex-shrink:0;">#{i}</span>'
            f'</div>'
        )

    return (
        '<style>@keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;}}</style>'
        + "\n".join(cards)
    )


def _translate_report(text: str, target_lang: str) -> str:
    """Call the LLM to translate an existing report into target_lang."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from src.llm import call_llm, get_llm

    if target_lang == "ua":
        instruction = (
            "Translate the following competitive research briefing into Ukrainian (Українська мова). "
            "Keep all markdown headings, bullet points, and hyperlinks exactly as they are — only translate the text."
        )
    else:
        instruction = (
            "Translate the following competitive research briefing into English. "
            "Keep all markdown headings, bullet points, and hyperlinks exactly as they are — only translate the text."
        )
    llm = get_llm(temperature=0)
    return call_llm(llm, [SystemMessage(content=instruction), HumanMessage(content=text)]).strip()


def switch_language(lang_choice: str, stored_report: str, stored_lang: str) -> tuple[str, str]:
    """Translate the stored report when the user switches language."""
    target = "ua" if "UA" in lang_choice else "en"
    if not stored_report or target == stored_lang:
        return stored_report, stored_lang
    translated = _translate_report(stored_report, target)
    return translated, target


def run_research(company_name: str, lang_choice: str):
    if not company_name.strip():
        yield _render_architecture(), _render_trace([]), "", "", "en"
        return

    language = "ua" if "UA" in lang_choice else "en"

    initial_state: AgentState = {
        "user_request": company_name.strip(),
        "subtasks": [],
        "current_subtask_idx": 0,
        "current_query": "",
        "pending_notes": "",
        "notes": {},
        "retry_count": 0,
        "validation_verdict": "",
        "validation_reason": "",
        "final_report": "",
        "language": language,
        "trace": [],
    }

    accumulated_trace: list[str] = []
    final_report = ""

    yield _render_architecture("planner"), _render_trace(["**System:** Starting — initialising agents"]), "", "", language

    for step_output in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_delta in step_output.items():
            active = _NODE_TO_AGENT.get(node_name, "")
            new_trace = node_delta.get("trace", [])
            if new_trace:
                accumulated_trace.append(new_trace[-1])
            if node_delta.get("final_report"):
                final_report = node_delta["final_report"]

        yield _render_architecture(active), _render_trace(accumulated_trace), final_report, final_report, language

    if not final_report:
        final_report = "_Research completed but no report was produced. Check the trace for errors._"
    yield _render_architecture(""), _render_trace(accumulated_trace), final_report, final_report, language


with gr.Blocks(title="Multi-Agent Research") as demo:
    gr.HTML("""
<div style="text-align:center;padding:20px 0 4px">
  <h1 style="font-size:1.65em;font-weight:700;margin:0;color:#0f172a;
             font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;">
    Multi-Agent Competitive Research
  </h1>
  <p style="color:#64748b;margin:5px 0 0;font-size:.9em;">
    Three AI agents collaborate live — watch each decision unfold in real time
  </p>
</div>
""")

    with gr.Row(equal_height=True):
        company_input = gr.Textbox(
            label="",
            placeholder="Company name — e.g. Stripe, Anthropic, Notion…",
            scale=6,
            container=False,
        )
        lang_selector = gr.Radio(
            choices=["🇬🇧 EN", "🇺🇦 UA"],
            value="🇬🇧 EN",
            label="",
            container=False,
            scale=1,
        )
        run_btn = gr.Button("Research ▶", variant="primary", scale=1, min_width=110)

    report_state = gr.State("")      # last generated report text
    report_lang_state = gr.State("en")  # language it was generated in

    architecture_output = gr.HTML(value=_render_architecture())

    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            gr.HTML('<p class="section-label">⚡ Live Agent Trace</p>')
            trace_output = gr.HTML(
                value='<p style="color:#94a3b8;padding:16px;font-style:italic;font-size:.88em;">'
                      'Enter a company name and click Research ▶</p>',
                elem_id="trace-panel",
            )
        with gr.Column(scale=2):
            gr.HTML('<p class="section-label">📄 Final Report</p>')
            report_output = gr.Markdown(
                value="*Report will appear here once all subtasks complete.*",
                elem_id="report-panel",
            )

    _run_outputs = [architecture_output, trace_output, report_output, report_state, report_lang_state]

    run_btn.click(fn=run_research, inputs=[company_input, lang_selector], outputs=_run_outputs)
    company_input.submit(fn=run_research, inputs=[company_input, lang_selector], outputs=_run_outputs)

    lang_selector.change(
        fn=switch_language,
        inputs=[lang_selector, report_state, report_lang_state],
        outputs=[report_output, report_lang_state],
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Base(), css=CSS)
