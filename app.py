import gradio as gr

from src.graph import app
from src.state import AgentState


def run_research(company_name: str):
    """Generator: streams agent trace + final report to the Gradio UI."""
    if not company_name.strip():
        yield "Please enter a company name.", ""
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

    yield "Starting research...", ""

    for step_output in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_delta in step_output.items():
            # Append any new trace messages
            new_trace = node_delta.get("trace", [])
            if new_trace:
                # Only append the last entry (each node appends exactly one)
                accumulated_trace.append(new_trace[-1])

            if "final_report" in node_delta and node_delta["final_report"]:
                final_report = node_delta["final_report"]

        trace_md = "\n\n".join(accumulated_trace) if accumulated_trace else "Working..."
        yield trace_md, final_report

    if not final_report:
        final_report = "Research did not produce a report. Check trace for details."
    yield "\n\n".join(accumulated_trace), final_report


with gr.Blocks(title="Multi-Agent Competitive Research") as demo:
    gr.Markdown(
        """# Multi-Agent Competitive Research Tool

**How it works:** Enter a company name. Three AI agents collaborate:
1. **Planner** decomposes your request into research subtasks and validates results
2. **Researcher** searches the web and summarizes findings per subtask
3. **Synthesizer** writes the final structured briefing

Watch the **Live Trace** panel to see each agent's decisions in real time.
"""
    )

    with gr.Row():
        company_input = gr.Textbox(
            label="Company Name",
            placeholder="e.g. Anthropic, OpenAI, Stripe...",
            scale=4,
        )
        run_btn = gr.Button("Research", variant="primary", scale=1)

    with gr.Row():
        with gr.Column(scale=1):
            trace_output = gr.Markdown(label="Live Trace", value="Enter a company name and click Research.")
        with gr.Column(scale=2):
            report_output = gr.Markdown(label="Final Report", value="Report will appear here after all subtasks complete.")

    run_btn.click(
        fn=run_research,
        inputs=[company_input],
        outputs=[trace_output, report_output],
    )

    company_input.submit(
        fn=run_research,
        inputs=[company_input],
        outputs=[trace_output, report_output],
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
