"""
Multi-Agent Research - Final Clean Version
- No rainbow gradient
- No confusing metrics (time, tokens, pages)
- Button height matches text field (60px)
- Simplified pipeline display
"""

import gradio as gr
import time
from typing import Dict, List, Any

from src.graph import app as graph_app
from src.state import AgentState

_AGENT_META = {
    "planner":    {"label": "PLANNER",    "color": "#a78bfa", "bg": "rgba(167,139,250,0.12)"},
    "researcher": {"label": "RESEARCHER", "color": "#22d3ee", "bg": "rgba(34,211,238,0.10)"},
    "validator":  {"label": "VALIDATOR",  "color": "#34d399", "bg": "rgba(52,211,153,0.10)"},
    "synth":      {"label": "SYNTHESIZER","color": "#fbbf24", "bg": "rgba(251,191,36,0.10)"},
}

_NODE_TO_AGENT = {
    "planner_decompose": "planner",
    "planner_query": "planner",
    "planner_validate": "validator",
    "next_subtask": "planner",
    "researcher": "researcher",
    "synthesizer": "synth",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #07090c;
  --bg-1: #0b0e13;
  --bg-2: #10141b;
  --line: rgba(255,255,255,0.07);
  --line-2: rgba(255,255,255,0.12);
  --ink: #e8ecf3;
  --ink-2: #b8c1cf;
  --ink-3: #7b8597;
  --ink-4: #525a6b;
  --accent: #bdf94a;
  --accent-ink: #0a0d05;
  --planner: #a78bfa;
  --researcher: #22d3ee;
  --synth: #fbbf24;
  --validator: #34d399;
}

* { box-sizing: border-box; }
body, .gradio-container {
  background: var(--bg) !important;
  color: var(--ink) !important;
  font-family: 'Geist', sans-serif !important;
}
.gradio-container::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    linear-gradient(to right, rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 90% 70% at 50% 30%, #000 40%, transparent 100%);
}
.gradio-container > .main, .gradio-container > .main > .wrap, .gradio-container > .main > .wrap > .gap {
  background: transparent !important;
  position: relative;
  z-index: 1;
}
.mono { font-family: 'Geist Mono', monospace !important; }
.header-row {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 20px 32px 4px !important;
}
.header-row h1 {
  font-size: 1.5em;
  font-weight: 600;
  margin: 0;
  color: var(--ink);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
#lang-btn {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: 10px !important;
  font-size: 22px !important;
  line-height: 1 !important;
  padding: 0 !important;
  width: 48px !important;
  min-width: 48px !important;
  max-width: 48px !important;
  height: 44px !important;
  cursor: pointer !important;
  transition: background 0.15s, border-color 0.15s !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}
#lang-btn:hover {
  background: rgba(255,255,255,0.08) !important;
  border-color: var(--line-2) !important;
}
.search-container {
  margin: 20px auto;
  max-width: 900px;
  padding: 0 32px;
}
.search-container .gradio-row {
  gap: 16px !important;
  align-items: stretch !important;
  display: flex !important;
  flex-direction: row !important;
}
.search-container textbox {
  flex: 1 !important;
  min-width: 0 !important;
}
.search-container input {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid var(--line-2) !important;
  color: var(--ink) !important;
  font-size: 16px !important;
  border-radius: 12px !important;
  padding: 20px 20px !important;
  height: 44px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}
.search-container input::placeholder {
  color: var(--ink-3);
}
.search-container button.primary {
  background: var(--accent) !important;
  color: var(--accent-ink) !important;
  border: none !important;
  font-family: 'Geist Mono', monospace !important;
  font-size: 16px !important;
  letter-spacing: 0.25em !important;
  text-transform: uppercase !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  min-width: 240px !important;
  height: 44px !important;
  padding: 0 32px !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-sizing: border-box !important;
}
.search-container button.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(189,249,74,0.4);
}
.pipeline-container {
  margin: 24px 32px;
  padding: 0;
  background: transparent;
  border: none;
}
#trace-panel, #report-panel {
  background: rgba(255,255,255,0.01);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 16px;
  min-height: 300px;
  overflow: visible !important;
  max-width: 100% !important;
}
#report-panel {
  min-height: 400px;
}
#report-panel h1, #report-panel h2, #report-panel h3 {
  color: var(--ink) !important;
  font-family: 'Geist', sans-serif !important;
  margin-top: 24px !important;
  margin-bottom: 12px !important;
}
#report-panel h1 { font-size: 28px !important; font-weight: 700 !important; }
#report-panel h2 { font-size: 22px !important; font-weight: 600 !important; }
#report-panel h3 { font-size: 18px !important; font-weight: 600 !important; }
#report-panel p {
  color: var(--ink-2) !important;
  line-height: 1.7 !important;
  font-size: 15px !important;
  margin-bottom: 12px !important;
}
#report-panel ul, #report-panel ol {
  color: var(--ink-2) !important;
  line-height: 1.7 !important;
  font-size: 15px !important;
  margin-bottom: 16px !important;
  padding-left: 24px !important;
}
#report-panel li {
  margin-bottom: 8px !important;
}
#report-panel strong {
  color: var(--ink) !important;
  font-weight: 600 !important;
}
#report-panel table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 20px 0 !important;
  font-size: 14px !important;
}
#report-panel th {
  background: rgba(255,255,255,0.05) !important;
  color: var(--ink) !important;
  font-weight: 600 !important;
  text-align: left !important;
  padding: 12px 16px !important;
  border: 1px solid var(--line-2) !important;
}
#report-panel td {
  color: var(--ink-2) !important;
  padding: 12px 16px !important;
  border: 1px solid var(--line) !important;
}
#report-panel tr:nth-child(even) {
  background: rgba(255,255,255,0.02) !important;
}
#report-panel tr:hover {
  background: rgba(255,255,255,0.03) !important;
}
#report-panel a {
  color: var(--accent) !important;
  text-decoration: none !important;
}
#report-panel a:hover {
  text-decoration: underline !important;
}
#report-panel code {
  background: rgba(255,255,255,0.05) !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-family: 'Geist Mono', monospace !important;
  font-size: 13px !important;
  color: var(--accent) !important;
}
#report-panel pre {
  background: rgba(255,255,255,0.03) !important;
  padding: 16px !important;
  border-radius: 8px !important;
  overflow-x: auto !important;
  margin: 16px 0 !important;
}
#report-panel pre code {
  background: transparent !important;
  padding: 0 !important;
}
#report-panel blockquote {
  border-left: 3px solid var(--accent) !important;
  padding-left: 16px !important;
  margin: 16px 0 !important;
  color: var(--ink-3) !important;
  font-style: italic !important;
}
#report-panel hr {
  border: none !important;
  border-top: 1px solid var(--line-2) !important;
  margin: 24px 0 !important;
}

/* Tables */
#report-panel .table-wrapper {
  overflow-x: auto !important;
  margin: 20px 0 !important;
  border-radius: 8px !important;
  border: 1px solid var(--line-2) !important;
}
#report-panel table {
  width: 100% !important;
  border-collapse: collapse !important;
  font-size: 14px !important;
  margin: 0 !important;
}
#report-panel th {
  background: rgba(255,255,255,0.05) !important;
  color: var(--ink) !important;
  font-weight: 600 !important;
  text-align: left !important;
  padding: 14px 16px !important;
  border: 1px solid var(--line-2) !important;
}
#report-panel td {
  color: var(--ink-2) !important;
  padding: 12px 16px !important;
  border: 1px solid var(--line) !important;
}
#report-panel tr:nth-child(even) {
  background: rgba(255,255,255,0.02) !important;
}
#report-panel tr:hover {
  background: rgba(255,255,255,0.03) !important;
}

/* Stat Cards */
#report-panel .stat-card {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: 8px !important;
  padding: 16px !important;
  margin: 12px 0 !important;
}
#report-panel .stat-label {
  color: var(--ink-3) !important;
  font-size: 13px !important;
  margin-bottom: 6px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}
#report-panel .stat-value {
  color: var(--ink) !important;
  font-size: 20px !important;
  font-weight: 600 !important;
}

/* Sources List */
#report-panel .sources-list {
  list-style: none !important;
  padding: 0 !important;
  margin: 20px 0 !important;
}
#report-panel .sources-list li {
  margin-bottom: 12px !important;
  padding: 12px !important;
  background: rgba(255,255,255,0.02) !important;
  border-radius: 6px !important;
  border-left: 3px solid var(--accent) !important;
}
#report-panel .sources-list a {
  color: var(--accent) !important;
  text-decoration: none !important;
  font-weight: 500 !important;
}
#report-panel .sources-list a:hover {
  text-decoration: underline !important;
}
#report-panel .sources-list small {
  display: block !important;
  margin-top: 4px !important;
  color: var(--ink-4) !important;
  word-break: break-all !important;
}
.trace-message {
  padding: 16px;
  margin: 12px 0;
  border-radius: 10px;
  border-left: 3px solid;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  overflow: visible !important;
  max-width: 100% !important;
  text-overflow: clip !important;
  display: block !important;
}
.trace-title {
  font-size: 15px !important;
  font-weight: 600 !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  text-overflow: clip !important;
  display: block !important;
}
.trace-body {
  font-size: 14.5px !important;
  line-height: 1.6 !important;
  color: var(--ink-2) !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  text-overflow: clip !important;
  max-width: 100% !important;
  overflow: visible !important;
  display: block !important;
}
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid;
  font-weight: 600;
}
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(189,249,74,0.5); }
  100% { box-shadow: 0 0 0 10px rgba(189,249,74,0); }
}
@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}
@keyframes sweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer {
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.02) 0%,
    rgba(255,255,255,0.05) 50%,
    rgba(255,255,255,0.02) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
footer { display: none !important; }
"""


def _translate_report(text: str, target_lang: str) -> str:
    """Translate an existing report into target_lang using the LLM."""
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


def toggle_language(current_lang: str, company_name: str, cache: dict) -> tuple:
    """Toggle report language. Translates on first switch, instant on repeat. Returns 4 values:
    (report_html, updated_cache, new_lang, new_btn_label)."""
    target = "ua" if current_lang == "en" else "en"
    # Button always shows the OTHER flag — what you'll switch to on the next press
    next_btn = "🇬🇧" if target == "ua" else "🇺🇦"

    if not cache:
        # No report yet — just flip language state so research will use the new language
        return gr.update(), cache, target, next_btn

    if target in cache:
        return _report_with_download(company_name.strip(), cache[target]), cache, target, next_btn

    # First switch to this language — translate and cache
    source_md = next(iter(cache.values()))
    translated = _translate_report(source_md, target)
    updated_cache = dict(cache) | {target: translated}
    return _report_with_download(company_name.strip(), translated), updated_cache, target, next_btn


def _render_pipeline(active_agent: str = None, running: bool = False, progress: int = 0, elapsed: str = "00:00") -> str:
    stages = [
        ("planner", "PLANNER", "Decompose · Query · Validate"),
        ("researcher", "RESEARCHER", "Search · Fetch · Extract"),
        ("synth", "SYNTHESIZER", "Synthesize · Report"),
    ]

    html_parts = ['<div class="pipeline-container">']

    # Progress bar at top
    if running:
        progress_pct = (progress / 4) * 100
        html_parts.append(f'''
        <div style="margin-bottom:16px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span class="mono" style="font-size:12px;color:var(--ink-3);letter-spacing:0.06em;">PROGRESS</span>
            <span class="mono" style="font-size:12px;color:var(--ink-3);">{progress}/4 subtasks · {elapsed}</span>
          </div>
          <div style="height:4px;border-radius:99px;background:var(--bg-2);overflow:hidden;">
            <div style="
              width:{progress_pct}%;
              height:100%;
              background:linear-gradient(90deg, var(--planner), var(--researcher), var(--synth), var(--accent));
              transition:width 0.6s ease;
              position:relative;
            ">
              {'<div style="position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);animation:sweep 2s linear infinite;"></div>' if running else ''}
            </div>
          </div>
        </div>
        ''')

    html_parts.append('<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;align-items:stretch;gap:0;">')

    for i, (key, name, sub) in enumerate(stages):
        meta = _AGENT_META[key]
        is_active = active_agent == key or (key == 'planner' and active_agent == 'validator')

        icon = (
            '<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><rect x="3" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="11" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="3" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="11" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/></svg>' if key == 'planner'
            else '<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.4"/><path d="M14 14l3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M5 9h8M9 5v8" stroke="currentColor" stroke-width="1" opacity=".5"/></svg>' if key == 'researcher'
            else '<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M4 5h12M4 10h12M4 15h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><circle cx="17" cy="15" r="2" fill="currentColor"/></svg>'
        )

        html_parts.append(f'''
        <div style="
          padding:16px 18px;
          border-radius:12px;
          border:1px solid {meta['color'] if is_active else 'var(--line)'};
          background: {f'linear-gradient(180deg, {meta["bg"]}, transparent)' if is_active else 'rgba(255,255,255,0.015)'};
          display:flex;gap:12px;align-items:flex-start;
        ">
          <div style="
            width:38px;height:38px;border-radius:10px;display:grid;place-items:center;
            background: {meta['bg']};
            color: {meta['color']};
            border:1px solid {meta['color']}33;
          ">{icon}</div>
          <div style="min-width:0;flex:1;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span class="mono" style="font-size:13px;letter-spacing:0.12em;color:{meta['color']};font-weight:600;">{name}</span>
              {'<span style="width:7px;height:7px;border-radius:99px;background:' + meta['color'] + ';display:inline-block;animation:pulse-ring 1.6s ease-out infinite;"></span>' if is_active and running else ''}
            </div>
            <div class="mono" style="font-size:12px;color:var(--ink-3);line-height:1.5;">{sub}</div>
          </div>
        </div>
        ''')

        if i < len(stages) - 1:
            html_parts.append('<div style="display:grid;place-items:center;padding:0 6px;"><svg width="40" height="20" viewBox="0 0 40 20" fill="none"><path d="M0 10 H30" stroke="var(--line-2)" stroke-width="1" stroke-dasharray="2 3"/><path d="M28 6 L34 10 L28 14" stroke="var(--ink-3)" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')

    html_parts.append('</div></div>')
    return ''.join(html_parts)


def _render_trace(events: List[Dict[str, Any]], running: bool = False) -> str:
    if not events:
        return '<div style="padding:40px;text-align:center;color:var(--ink-4);font-size:15px;">⚡ AGENT TRACE<br><br><span style="color:var(--ink-3);">Enter a company name and click RESEARCH</span></div>'

    html_parts = ['<div style="padding:8px;overflow:visible;max-width:100%;">']

    for i, ev in enumerate(events):
        agent = ev.get('agent', 'planner')
        meta = _AGENT_META.get(agent, _AGENT_META['planner'])

        html_parts.append(f'''
        <div class="trace-message" style="
          background: linear-gradient(180deg, {meta['bg']}, transparent 80%);
          border-color: {meta['color']};
          word-wrap: break-word !important;
          overflow-wrap: break-word !important;
          white-space: normal !important;
          overflow: visible !important;
          max-width: 100% !important;
          text-overflow: clip !important;
          display: block !important;
        ">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
            <span class="status-badge" style="color:{meta['color']};background:{meta['bg']};border-color:{meta['color']}40;">{meta['label']}</span>
            <span class="mono" style="font-size:11px;color:var(--ink-4);">t+{ev.get('t', '00:00')}</span>
          </div>
          <div class="trace-title" style="color:var(--ink);word-wrap:break-word;overflow-wrap:break-word;white-space:normal;text-overflow:clip;display:block;">{ev.get('title', '')}</div>
          <div class="trace-body" style="word-wrap:break-word;overflow-wrap:break-word;white-space:normal;text-overflow:clip;max-width:100%;overflow:visible;display:block;">{ev.get('body', '')}</div>
        </div>
        ''')

    if running:
        html_parts.append('<div style="padding:12px;color:var(--accent);font-size:18px;animation:blink 1s step-end infinite;">▋</div>')

    html_parts.append('</div>')
    return ''.join(html_parts)


_SHIMMER_TRACE = (
    '<div class="shimmer" style="padding:20px;border-radius:10px;min-height:200px;">'
    '<p style="color:var(--ink-3);font-size:16px;margin-bottom:12px;">Initializing agents...</p>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:80%;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:90%;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:70%;"></div>'
    '</div>'
)
_SHIMMER_REPORT = (
    '<div class="shimmer" style="padding:20px;border-radius:10px;min-height:300px;">'
    '<p style="color:var(--ink-3);font-size:16px;margin-bottom:12px;">Creating report...</p>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:80%;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:90%;"></div>'
    '<div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:8px;width:70%;"></div>'
    '</div>'
)


def _report_with_download(company: str, markdown: str) -> str:
    """Prepend a styled download link to the rendered report HTML."""
    import urllib.parse
    filename = company.strip().replace(' ', '_').replace('/', '_') + '_research.md'
    encoded = urllib.parse.quote(markdown, safe='')
    download_bar = (
        f'<div style="display:flex;justify-content:flex-end;margin-bottom:16px;">'
        f'<a href="data:text/markdown;charset=utf-8,{encoded}" download="{filename}" '
        f'style="display:inline-flex;align-items:center;gap:6px;padding:10px 24px;'
        f'background:var(--accent);color:var(--accent-ink) !important;border-radius:12px;'
        f'font-family:\'Geist Mono\',monospace !important;font-size:12px;font-weight:700;'
        f'letter-spacing:0.25em !important;text-decoration:none;text-transform:uppercase;'
        f'transition:all 0.2s ease;" '
        f'onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 8px 20px rgba(189,249,74,0.4)\'" '
        f'onmouseout="this.style.transform=\'none\';this.style.boxShadow=\'none\'">'
        f'⬇ Download .md</a>'
        f'</div>'
    )
    # Strip any LLM-generated title (first # heading) — it may be in the wrong language
    import re as _re
    clean_md = _re.sub(r'^# .+\n?', '', markdown.lstrip(), count=1)
    title_html = f'<h1>{company} — Research Report</h1>'
    return download_bar + title_html + markdown_to_html(clean_md)


def run_research(company_name: str, current_lang: str):
    _empty = '<p style="color:var(--ink-4);font-style:italic;font-size:15px;">Report will appear here after research completes.</p>'
    if not company_name.strip():
        yield _render_pipeline(None, False, 0, "00:00"), _render_trace([], False), _empty, {}
        return

    language = current_lang if current_lang in ("en", "ua") else "en"
    start_time = time.time()

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

    accumulated_trace = []
    final_report = ""
    active_agent = "planner"
    progress = 0
    total_subtasks = 4

    # Reset cache immediately so stale translations don't show during new research
    yield _render_pipeline("planner", True, 0, "00:00"), _SHIMMER_TRACE, _SHIMMER_REPORT, {}

    for step_output in graph_app.stream(initial_state, stream_mode="updates"):
        elapsed = time.time() - start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        for node_name, node_delta in step_output.items():
            active_agent = _NODE_TO_AGENT.get(node_name, active_agent)
            new_trace = node_delta.get("trace", [])

            if new_trace:
                trace_msg = new_trace[-1]
                # Split on first ":" only so URLs in the body aren't truncated
                colon_idx = trace_msg.find(":")
                raw_title = trace_msg[:colon_idx] if colon_idx != -1 else trace_msg
                raw_body = trace_msg[colon_idx + 1:].strip() if colon_idx != -1 else ""
                title = raw_title.replace("**", "").strip()
                body = raw_body.replace("**", "").replace("`", "")
                accumulated_trace.append({
                    'agent': active_agent,
                    't': elapsed_str,
                    'title': title,
                    'body': body,
                })

            if node_delta.get("final_report"):
                final_report = node_delta["final_report"]

            if "subtasks" in node_delta and node_delta["subtasks"]:
                total_subtasks = len(node_delta["subtasks"])

            # Progress = number of completed subtasks; only next_subtask carries the incremented index
            if node_name == "next_subtask" and "current_subtask_idx" in node_delta:
                progress = node_delta["current_subtask_idx"]

        trace_html = _render_trace(accumulated_trace, True) if accumulated_trace else _SHIMMER_TRACE
        report_html = markdown_to_html(final_report) if final_report else _SHIMMER_REPORT

        yield _render_pipeline(active_agent, True, progress, elapsed_str), trace_html, report_html, gr.update()

    elapsed = time.time() - start_time
    elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

    if not final_report:
        final_report = "_Research completed but no report was produced._"

    # Final yield: pipeline done, trace frozen, report with download, cache seeded with generated language
    cache = {language: final_report}
    yield (
        _render_pipeline(None, False, total_subtasks, elapsed_str),
        _render_trace(accumulated_trace, False),
        _report_with_download(company_name.strip(), final_report),
        cache,
    )

def markdown_to_html(md: str) -> str:
    """Convert markdown to nicely formatted HTML with tables and visualizations."""
    import re

    html = md

    # Statistics/Metrics cards — must run before bold conversion (pattern uses **)
    stat_pattern = r'\*\*(.+?):\*\*\s*(.+?)(?=\n|$)'
    def convert_stat(match):
        label = match.group(1).strip()
        value = match.group(2).strip()
        return f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>'
    html = re.sub(stat_pattern, convert_stat, html)

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Code blocks
    html = re.sub(r'```(\w+)?\n(.+?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Links - make sure they're clickable
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', html)

    # Convert standalone URLs to clickable links — skip URLs already inside an attribute (href="...", src="...")
    html = re.sub(r'(?<![="\'(])(https?://[^\s<>"\']+)', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', html)

    # Lists - unordered
    html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Lists - ordered (simple conversion)
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Wrap consecutive <li> in <ul>
    html = re.sub(r'(<li>.+</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', html)

# Tables - convert markdown tables to HTML (handles various formats)
    # Match tables with pipes, including leading/trailing pipes
    table_lines = html.split('\n')
    in_table = False
    table_rows = []
    processed_html = []

    for line in table_lines:
        stripped = line.strip()
        # Check if line is part of a table (contains pipes and table-like content)
        if '|' in stripped and (stripped.startswith('|') or stripped.endswith('|')):
            # Check if it's a header separator line (contains --- or :)
            if re.match(r'^\|?\s*[:-]+\s*\|', stripped) or re.match(r'^\|?\s*[:-]+\s*\|\s*[:-]+\s*\|', stripped):
                in_table = True
                continue  # Skip separator line
            elif in_table or (stripped.count('|') >= 3 and not stripped.startswith('#')):
                # This is a table row
                table_rows.append(stripped)
                in_table = True
                continue
        else:
            # Not a table line
            if in_table and table_rows:
                # Process accumulated table rows
                if len(table_rows) >= 2:  # Need at least header + 1 data row
                    html_table = '<div class="table-wrapper"><table><thead><tr>'

                    # First row is header
                    headers = [h.strip() for h in table_rows[0].split('|') if h.strip() and h.strip() != '---']
                    if headers:
                        for header in headers:
                            html_table += f'<th>{header}</th>'
                        html_table += '</tr></thead><tbody>'

                        # Remaining rows are data
                        for row in table_rows[1:]:
                            cells = [c.strip() for c in row.split('|') if c.strip() and not re.match(r'^[:-]+$', c.strip())]
                            if cells and len(cells) == len(headers):
                                html_table += '<tr>'
                                for cell in cells:
                                    # Clean up cell content
                                    cell = cell.strip('|').strip()
                                    if cell:
                                        html_table += f'<td>{cell}</td>'
                                html_table += '</tr>'

                        html_table += '</tbody></table></div>'
                        processed_html.append(html_table)

                table_rows = []
                in_table = False

            processed_html.append(line)

    # Handle any remaining table at end
    if in_table and table_rows and len(table_rows) >= 2:
        html_table = '<div class="table-wrapper"><table><thead><tr>'
        headers = [h.strip() for h in table_rows[0].split('|') if h.strip()]
        if headers:
            for header in headers:
                html_table += f'<th>{header}</th>'
            html_table += '</tr></thead><tbody>'

            for row in table_rows[1:]:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if cells:
                    html_table += '<tr>'
                    for cell in cells:
                        cell = cell.strip('|').strip()
                        if cell:
                            html_table += f'<td>{cell}</td>'
                    html_table += '</tr>'

            html_table += '</tbody></table></div>'
            processed_html.append(html_table)

    html = '\n'.join(processed_html)

    # Paragraphs (lines not already wrapped)
    lines = html.split('\n')
    processed_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('<ul>') or stripped.startswith('<li>'):
            in_list = True
        elif stripped.endswith('</ul>'):
            in_list = False

        if stripped and not stripped.startswith('<') and not stripped.endswith('>'):
            if not in_list and not any(stripped.startswith(tag) for tag in ['<h', '<ul', '<li', '<pre', '<table', '<tr', '<td', '<th', '<div']):
                if stripped and len(stripped) > 3:  # Avoid wrapping single characters
                    line = f'<p>{stripped}</p>'
        processed_lines.append(line)
    html = '\n'.join(processed_lines)

    # Horizontal rules
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

    # Blockquotes
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Clean up multiple br tags
    html = re.sub(r'(<br>){3,}', r'<br><br>', html)

    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    return html


with gr.Blocks(title="Multi-Agent Research") as demo:
    # ── Hidden state ─────────────────────────────────────────────────────────
    lang_state = gr.State("en")      # current displayed language
    reports_cache = gr.State({})     # {"en": raw_md, "ua": raw_md}

    # ── Header: title left, flag toggle right ────────────────────────────────
    with gr.Row(elem_classes="header-row"):
        gr.HTML('<h1 style="font-size:1.5em;font-weight:600;margin:0;color:var(--ink);letter-spacing:0.15em;text-transform:uppercase;">Multi-Agent Research</h1>')
        lang_btn = gr.Button("🇺🇦", elem_id="lang-btn", min_width=48)

    # ── Search row ───────────────────────────────────────────────────────────
    with gr.Row(elem_classes="search-container"):
        company_input = gr.Textbox(
            placeholder="Enter company name (e.g., Notion, Stripe, Apple)...",
            label="",
            container=False,
            scale=7,
            elem_id="company-input"
        )
        run_btn = gr.Button("RESEARCH", variant="primary", scale=2, elem_id="run-btn")

    pipeline_html = gr.HTML(value=_render_pipeline(None, False))

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=400):
            gr.HTML('<p class="mono" style="font-size:12px;color:var(--ink-4);letter-spacing:0.1em;margin:0 0 12px 8px;">⚡ AGENT TRACE</p>')
            trace_output = gr.HTML(value=_render_trace([], False), elem_id="trace-panel")
        with gr.Column(scale=2, min_width=500):
            gr.HTML('<p class="mono" style="font-size:12px;color:var(--ink-4);letter-spacing:0.1em;margin:0 0 12px 8px;">📄 REPORT</p>')
            report_output = gr.HTML(value='<p style="color:var(--ink-4);font-style:italic;font-size:15px;">Report will appear here after research completes.</p>', elem_id="report-panel")

    run_outputs = [pipeline_html, trace_output, report_output, reports_cache]
    run_inputs  = [company_input, lang_state]

    run_btn.click(fn=run_research, inputs=run_inputs, outputs=run_outputs)
    company_input.submit(fn=run_research, inputs=run_inputs, outputs=run_outputs)

    lang_btn.click(
        fn=toggle_language,
        inputs=[lang_state, company_input, reports_cache],
        outputs=[report_output, reports_cache, lang_state, lang_btn],
    )


if __name__ == "__main__":
    import os
    # For deployment on Render, Railway, etc.
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        css=CSS,
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
