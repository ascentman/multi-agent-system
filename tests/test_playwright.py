"""
Playwright MCP - Browser Automation for Multi-Agent Research

This module provides browser automation capabilities using Playwright.
It can be used to:
- Test the UI automatically
- Capture screenshots during execution
- Automate research workflows
- Validate UI elements and interactions
"""

from playwright.sync_api import sync_playwright, Page, expect
import time
from typing import Optional, List, Dict, Any


class MultiAgentResearchBrowser:
    """Browser automation wrapper for Multi-Agent Research UI."""

    def __init__(self, base_url: str = "http://127.0.0.1:7862"):
        self.base_url = base_url
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self, headless: bool = False):
        """Start the browser and open a new page."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )
        self.page.goto(self.base_url)
        return self

    def close(self):
        """Close the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def wait_for_load(self, timeout: int = 5000):
        """Wait for the page to fully load."""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self

    def take_screenshot(self, path: str = "screenshot.png"):
        """Take a screenshot of the current page."""
        self.page.screenshot(path=path, full_page=True)
        print(f"✓ Screenshot saved to {path}")
        return self

    def enter_company(self, company_name: str):
        """Enter a company name in the search box."""
        input_field = self.page.locator("#company-input")
        input_field.fill(company_name)
        print(f"✓ Entered company: {company_name}")
        return self

    def select_language(self, lang: str = "EN"):
        """Select language (EN or UA)."""
        lang_btn = self.page.locator(f'button[data-lang="{lang}"]')
        lang_btn.click()
        print(f"✓ Selected language: {lang}")
        return self

    def click_research(self):
        """Click the RESEARCH button."""
        research_btn = self.page.locator("#run-btn")
        research_btn.click()
        print("✓ Clicked RESEARCH button")
        return self

    def wait_for_pipeline_active(self, timeout: int = 10000):
        """Wait for the pipeline to become active (running state)."""
        pipeline = self.page.locator(".pipeline-container")
        expect(pipeline).to_be_visible(timeout=timeout)
        print("✓ Pipeline is visible")
        return self

    def wait_for_completion(self, timeout: int = 60000):
        """Wait for research to complete (status changes from RUNNING to IDLE)."""
        # Wait for status to change back to IDLE
        status = self.page.locator("text=IDLE")
        try:
            status.wait_for(state="visible", timeout=timeout)
            print("✓ Research completed")
        except Exception:
            print("⚠ Timeout waiting for completion")
        return self

    def get_trace_events(self) -> List[Dict[str, Any]]:
        """Extract trace events from the UI."""
        trace_items = self.page.locator(".anim-in").all()
        events = []
        for item in trace_items:
            try:
                text = item.inner_text()
                events.append({"text": text})
            except Exception:
                pass
        return events

    def get_report_content(self) -> str:
        """Get the final report content."""
        report_panel = self.page.locator("#report-panel")
        return report_panel.inner_text()

    def run_research(self, company: str, lang: str = "EN", screenshot_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a complete research workflow.

        Args:
            company: Company name to research
            lang: Language (EN or UA)
            screenshot_dir: Optional directory to save screenshots

        Returns:
            Dictionary with research results
        """
        print(f"\n🔍 Starting research for: {company}")
        print("=" * 60)

        # Initial screenshot
        if screenshot_dir:
            self.take_screenshot(f"{screenshot_dir}/00_initial.png")

        # Enter company and start research
        self.enter_company(company)
        self.select_language(lang)

        if screenshot_dir:
            self.take_screenshot(f"{screenshot_dir}/01_entered.png")

        # Click research
        self.click_research()

        if screenshot_dir:
            self.take_screenshot(f"{screenshot_dir}/02_started.png")

        # Wait for pipeline to activate
        self.wait_for_pipeline_active()

        # Wait for completion
        self.wait_for_completion(timeout=120000)

        if screenshot_dir:
            self.take_screenshot(f"{screenshot_dir}/03_completed.png")

        # Get results
        trace_events = self.get_trace_events()
        report_content = self.get_report_content()

        print("=" * 60)
        print(f"✓ Research completed for: {company}")
        print(f"  - Trace events: {len(trace_events)}")
        print(f"  - Report length: {len(report_content)} chars")

        return {
            "company": company,
            "language": lang,
            "trace_events": trace_events,
            "report": report_content,
            "success": len(report_content) > 0
        }

    def test_ui_elements(self) -> Dict[str, bool]:
        """Test that all required UI elements are present."""
        tests = {}

        # Check header
        tests["header_title"] = self.page.locator("text=Multi-Agent Competitive Research").is_visible()

        # Check search bar
        tests["search_input"] = self.page.locator("#company-input").is_visible()

        # Check language buttons
        tests["lang_en"] = self.page.locator('button[data-lang="EN"]').is_visible()
        tests["lang_ua"] = self.page.locator('button[data-lang="UA"]').is_visible()

        # Check research button
        tests["research_btn"] = self.page.locator("#run-btn").is_visible()

        # Check pipeline
        tests["pipeline"] = self.page.locator(".pipeline-container").is_visible()

        # Check trace panel
        tests["trace_panel"] = self.page.locator("#trace-panel").is_visible()

        # Check report panel
        tests["report_panel"] = self.page.locator("#report-panel").is_visible()

        # Check tweaks button
        tests["tweaks_btn"] = self.page.locator('button[onclick*="tweaks-panel"]').is_visible()

        return tests

    def run_ui_tests(self) -> bool:
        """Run UI element tests and report results."""
        print("\n🧪 Running UI Tests")
        print("=" * 60)

        tests = self.test_ui_elements()
        all_passed = True

        for test_name, passed in tests.items():
            status = "✓" if passed else "✗"
            print(f"{status} {test_name}: {'PASS' if passed else 'FAIL'}")
            if not passed:
                all_passed = False

        print("=" * 60)
        print(f"Overall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

        return all_passed


def demo_automation():
    """Demo script showing browser automation capabilities."""
    import os
    from datetime import datetime

    # Create screenshot directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = f"screenshots_{timestamp}"
    os.makedirs(screenshot_dir, exist_ok=True)

    # Start browser
    browser = MultiAgentResearchBrowser()

    try:
        browser.start(headless=False)
        browser.wait_for_load()

        # Run UI tests
        browser.run_ui_tests()

        # Run research demo
        results = browser.run_research(
            company="Notion",
            lang="EN",
            screenshot_dir=screenshot_dir
        )

        # Save report
        if results["success"]:
            with open(f"{screenshot_dir}/report.md", "w") as f:
                f.write(results["report"])
            print(f"\n✓ Report saved to {screenshot_dir}/report.md")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        browser.take_screenshot(f"{screenshot_dir}/error.png")

    finally:
        browser.close()
        print("\n✓ Browser closed")


if __name__ == "__main__":
    demo_automation()
