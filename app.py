import re
import gradio as gr

from src.graph import app
from src.state import AgentState

# ── Agent card styles: (emoji, border colour, background) ────────────────────
_STYLES = {
    "decompose":  ("🧠", "#4285f4", "#e8f0fe"),
    "query":      ("🔎", "#7c3aed", "#f5f3ff"),
    "researcher": ("🌐", "#0891b2", "#e0f7fa"),
    "valid":      ("✅", "#16a34a", "#f0fdf4"),
    "invalid":    ("⚠️",  "#ea580c", "#fff7ed"),
    "advance":    ("➡️",  "#64748b", "#f8fafc"),
    "synthesizer":("✍️",  "#d97706", "#fffbeb"),
    "default":    ("💬", "#9ca3af", "#f9fafb"),
}

def _classify(msg: str) -> str:
    if "Decomposed into" in msg:                              return "decompose"
    if "Query:**" in msg or "Retry query:**" in msg:         return "query"
    if "**Researcher:**" in msg:                              return "researcher"
    if "**Validator:**" in msg and "`invalid`" in msg:       return "invalid"
    if "**Validator:**" in msg:                               return "valid"
    if "**Synthesizer:**" in msg:                             return "synthesizer"
    if "Subtask" in msg or "Handing off" in msg:             return "advance"
    return "default"

def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML for trace cards (bold + inline code only)."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`",
                  r'<code style="background:#0001;padding:1px 5px;border-radius:3px;'
                  r'font-size:.9em;">\1</code>', text)
    text = re.sub(r"_\((.+?)\)_", r'<span style="opacity:.6;font-size:.85em;">(\1)</span>', text)
    return text

def _render_trace(messages: list[str]) -> str:
    if not messages:
        return '<p style="color:#94a3b8;padding:16px;font-style:italic;">Waiting to start…</p>'

    cards = []
    for i, msg in enumerate(messages, 1):
        key = _classify(msg)
        icon, border, bg = _STYLES[key]
        cards.append(f"""
<div style="display:flex;align-items:flex-start;gap:8px;margin:5px 0;animation:fadein .3s ease">
  <span style="font-size:1.15em;min-width:26px;padding-top:3px">{icon}</span>
  <div style="flex:1;background:{bg};border-left:3px solid {border};
              padding:8px 12px;border-radius:0 8px 8px 0;
              font-size:.88em;line-height:1.55;color:#1e293b;">
    {_md_to_html(msg)}
  </div>
  <span style="color:#cbd5e1;font-size:.72em;min-width:22px;text-align:right;padding-top:7px">#{i}</span>
</div>""")

    return (
        '<style>@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}</style>'
        + "\n".join(cards)
    )

# ── Main research generator ───────────────────────────────────────────────────
def run_research(company_name: str):
    if not company_name.strip():
        yield _render_trace([]), ""
        return

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
        "trace": [],
    }

    accumulated_trace: list[str] = []
    final_report = ""

    yield _render_trace(["**Starting…** Initialising agents"]), ""

    for step_output in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_delta in step_output.items():
            new_trace = node_delta.get("trace", [])
            if new_trace:
                accumulated_trace.append(new_trace[-1])
            if node_delta.get("final_report"):
                final_report = node_delta["final_report"]

        yield _render_trace(accumulated_trace), final_report

    if not final_report:
        final_report = "_Research completed but no report was produced. Check the trace for errors._"
    yield _render_trace(accumulated_trace), final_report


# ── UI layout ─────────────────────────────────────────────────────────────────
CSS = """
#trace-panel { max-height: 72vh; overflow-y: auto; }
#report-panel .prose { font-size: .92em; }
footer { display: none !important; }
"""

with gr.Blocks(title="Multi-Agent Research") as demo:
    gr.HTML("""
<div style="text-align:center;padding:24px 0 8px">
  <h1 style="font-size:1.8em;font-weight:700;margin:0">🔎 Multi-Agent Competitive Research</h1>
  <p style="color:#64748b;margin:6px 0 0;font-size:.95em">
    Three AI agents collaborate live — watch each decision unfold in real time
  </p>
</div>
<div style="display:flex;justify-content:center;gap:24px;padding:8px 0 16px;font-size:.82em;color:#94a3b8">
  <span>🧠 Planner &nbsp;→&nbsp; 🔎 Query &nbsp;→&nbsp; 🌐 Researcher &nbsp;→&nbsp; ✅ Validator &nbsp;→&nbsp; ✍️ Synthesizer</span>
</div>
""")

    with gr.Row():
        company_input = gr.Textbox(
            label="",
            placeholder="Company name — e.g. Stripe, Anthropic, Notion…",
            scale=5,
            container=False,
        )
        run_btn = gr.Button("Research ▶", variant="primary", scale=1, min_width=120)

    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            gr.HTML('<p style="font-weight:600;color:#475569;margin:0 0 4px;font-size:.85em">⚡ LIVE AGENT TRACE</p>')
            trace_output = gr.HTML(
                value='<p style="color:#94a3b8;padding:16px;font-style:italic;">Enter a company name and click Research ▶</p>',
                elem_id="trace-panel",
            )
        with gr.Column(scale=2):
            gr.HTML('<p style="font-weight:600;color:#475569;margin:0 0 4px;font-size:.85em">📄 FINAL REPORT</p>')
            report_output = gr.Markdown(
                value="*Report will appear here once all subtasks complete.*",
                elem_id="report-panel",
            )

    run_btn.click(fn=run_research, inputs=[company_input], outputs=[trace_output, report_output])
    company_input.submit(fn=run_research, inputs=[company_input], outputs=[trace_output, report_output])

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CSS)
