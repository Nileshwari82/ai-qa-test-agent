"""Functionality Detection Agent for grouping webpage elements into user-facing features."""

from __future__ import annotations

import json
import logging

from strands import Agent

from agents.utils import safe_structured_output
from models import DiscoveredFunctionalityCollection, PageAnalysisData
from prompts import FUNCTIONALITY_DETECTOR_PROMPT

logger = logging.getLogger(__name__)


class FunctionalityDetectorAgent:
    """Agent that interprets structured page elements into high-level user functionalities."""

    def __init__(self, model) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=FUNCTIONALITY_DETECTOR_PROMPT,
            name="FunctionalityDetector",
        )

    def detect(self, page_data: PageAnalysisData) -> DiscoveredFunctionalityCollection:
        logger.info("Detecting functionalities for page: %s (%s)", page_data.title, page_data.url)
        summary = {
            "url": page_data.url,
            "title": page_data.title,
            "headings": page_data.headings[:10],
            "sections": page_data.sections[:10],
            "buttons": [b.text for b in page_data.buttons[:25]],
            "inputs": [{"name": i.name, "type": i.input_type, "placeholder": i.placeholder} for i in page_data.inputs[:20]],
            "forms": [f.form_id for f in page_data.forms[:5]],
            "dropdowns": [d.get("name") for d in page_data.dropdowns[:10]],
            "checkboxes": [c.get("label") for c in page_data.checkboxes[:10]],
            "cards": [c.get("title") for c in page_data.cards[:10]],
            "links": [l.text for l in page_data.links[:25]],
        }
        prompt = (
            f"Page URL: {page_data.url}\n"
            f"Page Title: {page_data.title}\n"
            f"Page Elements Summary:\n{json.dumps(summary, indent=2)}\n\n"
            "Analyze these DOM elements and group them into logical user-facing Functionalities for this page."
        )
        result = safe_structured_output(self._agent, DiscoveredFunctionalityCollection, prompt)
        for func in result.functionalities:
            func.page_url = page_data.url
            func.page_title = page_data.title
        logger.info("Detected %d functionalities for %s", len(result.functionalities), page_data.title)
        return result
