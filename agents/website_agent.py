"""Website feature understanding agent."""

from __future__ import annotations

import json
import logging

from strands import Agent

from agents.utils import safe_structured_output
from models import WebsiteAnalysis, WebsiteFeatureUnderstanding
from prompts import WEBSITE_FEATURE_PROMPT
from website_analyzer import website_analysis_summary

logger = logging.getLogger(__name__)


class WebsiteAnalyzerAgent:
    """Interprets Playwright inspection results into testable features."""

    def __init__(self, model) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=WEBSITE_FEATURE_PROMPT,
            name="WebsiteAnalyzer",
        )

    def analyze(self, website: WebsiteAnalysis) -> WebsiteFeatureUnderstanding:
        logger.info("Website feature understanding started for %s", website.url)
        summary = website_analysis_summary(website)
        prompt = (
            f"Website URL: {website.url}\n"
            f"Page title: {website.page_title}\n"
            f"Accessible: {website.accessible}\n"
            f"Structured inspection data:\n{json.dumps(summary, indent=2)}\n\n"
            "Infer features, flows, and synthesize a testable requirement."
        )
        result = safe_structured_output(self._agent, WebsiteFeatureUnderstanding, prompt)
        logger.info("Website feature understanding completed")
        return result
