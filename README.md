# 🤖 QA Agent Pro

**AI-Powered Website Testing & Test Case Generation Platform**

An agentic QA platform that supports:

1. **Requirement-Based Testing** — Convert software requirements into comprehensive test cases
2. **Website URL-Based Testing** — Inspect public websites with Playwright and generate grounded test cases

Built with Python, Strands Agents, Streamlit, Playwright, and Pydantic.

---

## Features

### Mode 1: Requirement-Based Testing
- Multi-agent pipeline (Analyze → Plan → Generate → Risk → Validate)
- Structured test cases with steps, expected results, priority
- Programmatic coverage scoring

### Mode 2: Website URL-Based Testing
- Playwright page inspection (buttons, inputs, forms, links, navigation)
- Controlled crawl depth (1 / 3 / 5 pages, same domain only)
- Screenshot capture
- AI-generated test cases grounded in discovered elements
- Safe browser checks (optional bonus — visibility only, no destructive actions)

### Professional UI
- SaaS-style dashboard with sidebar navigation
- Agent Activity panel
- Coverage dashboard with category breakdown
- Risk matrix
- Report history (session-based)
- Export: CSV, JSON, Markdown, HTML
- Demo Mode for presentations

---

## Architecture

```
Requirement Mode:
  Requirement → Requirement Analyzer → Scenario Planner → Test Case Generator
             → Risk Analyzer → Validator → QA Report

Website Mode:
  URL → Playwright Inspector → Website Analyzer Agent → Requirement Analyzer
     → Scenario Planner → Test Case Generator → Risk Analyzer → Validator → QA Report
```

### Agents
| Agent | Role |
|-------|------|
| Requirement Analyzer | Parses requirements / website context |
| Website Analyzer | Interprets Playwright inspection data |
| Scenario Planner | Creates categorized test scenarios |
| Test Case Generator | Produces detailed grounded test cases |
| Risk Analyzer | Edge cases, risks, recommendations |
| Validator | Coverage validation + tools |

---

## Installation

```bash
cd ai-qa-test-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.

---

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501

---

## Recommended Demo Website

**https://www.saucedemo.com/** — public demo e-commerce site with login form.

---

## Live Demo Flow (10–15 min)

1. Open app → show Dashboard
2. Go to **Website Analyzer** → enter SauceDemo URL
3. Set crawl depth to **3** → click **Analyze Website**
4. Show workflow progress + Agent Activity panel
5. Walk through: Website Dashboard → Buttons/Inputs tabs → Test Cases
6. Show Coverage dashboard and Risk matrix
7. Export CSV/JSON
8. Switch to **Test Case Generator** → run Login requirement example
9. Mention future: Playwright test execution from generated cases

---

## Limitations (Honest)

- Cannot inspect login-protected, CAPTCHA, or auth-required sites without credentials
- Does not perform destructive actions (purchases, deletions, form submissions on arbitrary sites)
- Coverage scores are programmatic/heuristic — not a substitute for human QA review
- Security items are **recommendations**, not verified vulnerabilities
- Report history is session-only (no database)
- Quality depends on LLM and website accessibility

---

## Future Improvements

- Full Playwright test script generation and execution
- TestRail / Jira integration
- Persistent report storage
- Authenticated site analysis (with user-provided credentials)
- Visual regression testing

---

## Project Structure

```
ai-qa-test-agent/
├── app.py                 # Main Streamlit entry
├── agent.py               # Orchestrator (both modes)
├── website_analyzer.py    # Playwright inspection
├── browser_checks.py      # Safe visibility checks
├── models.py              # Pydantic schemas
├── validators.py          # Coverage calculation
├── export_utils.py        # Report export
├── agents/                # Strands agent modules
├── ui/                    # Dashboard UI components
└── outputs/               # Screenshots & check evidence
```

---

## Presentation Guide

See original README sections for talking points on problem, agentic AI, architecture, and technical choices. Key message: **this is a multi-step agent pipeline with real Playwright inspection — not a single LLM prompt or fake results.**
