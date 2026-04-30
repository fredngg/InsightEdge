# Sonar AI Sales Agent — MVP

## Working Agreement

> **Always brief the user before building anything.** Present the plan, get confirmation, then proceed. Never start coding or creating files without explicit approval first.

## Project Overview

**Full name:** Multi Role AI Digital Sales Agent  
**Short name:** Sonar AI Signal / Sales Agent  
**Status:** MVP — build step by step, validate before proceeding to next phase  
**Stakeholders:** Sponsor, Project Owner, Sales Lead, Technical Lead

## Problem Statement

Sonar's sales teams face:
- Inefficient ability to schedule meetings
- Unable to spark conversations with the right target audience
- Lack of quality leads
- Insufficient lead volume

## Vision

A single desktop application serving two GTM segments:
- **Velocity / mid-market reps** — outreach to immediate opportunities based on propensity-to-buy signals
- **Territory Managers (ENT)** — feed a target account list and identify key buying signals across defined indicators

Three business pillars: **Listen → Market → Outbound**

---

## User Roles & Modes

### Role A: Territory Manager (Enterprise)
- **Input:** Feed an account list of 100–500 regulated-industry accounts
- **Agent behavior:** Ingests list → chooses ENT indicators → runs analysis → ranks by propensity to buy
- **Output:**
  - Report with data across all analyzed signal categories, ranked by propensity to buy
  - Customized email targeting a specific personality (e.g. Head of AI, CTO) based on social/inference signals
  - Customized product marketing message to keep Sonar top-of-mind

### Role B: Velocity (Mid-market / SMB)
- **Input (two options):**
  - Option A: "Create a list" — agent curates mid-market accounts from SFDC or web, programmed with ICP criteria (excludes ENT list)
  - Option B: Feed a Velocity list manually
- **Agent behavior:** Ingests input → chooses Velocity indicators (ENT-specific indicators excluded) → runs analysis
- **Output:**
  - Report ranked by propensity to buy
  - Customized email based on developer pain points / social listening signals (Stack Overflow, Reddit, GitHub, Sonar community)

---

## Signal Indicators

| Indicator | Velocity (V) | Enterprise (ENT) | Data Sources |
|---|---|---|---|
| Hiring patterns | ✅ | ✅ | LinkedIn, target account careers page |
| Public news (tech-related) | ✅ | ✅ | Web scraping, news APIs |
| Technology stack analyzer | ✅ | ✅ | GitHub, ZoomInfo, CI/CD tools, Cloud presence |
| Regulatory impact analysis | ❌ | ✅ | Regulatory news, industry publications |
| Pain points / Social listening | ✅ | ❌ | Stack Overflow, Reddit, GitHub, Sonar community |
| Company position (leader / skeptic / laggard) | ❌ | ✅ | Web inference |
| Personality inference (4-colour model) | ❌ | ✅ | LinkedIn, speeches, events, articles |
| Contact role mapping (power map) | ❌ | ✅ | LinkedIn |

### Notes on Indicators
- **Tech stack, hiring, public news** are deterministic / black-and-white — high confidence
- **Personality inference** is subjective — agent infers from online data (speech style, event attendance, article tone). Flag as probabilistic, not definitive. Sales team must understand this caveat.
- **Scoring model** is prompt-driven. Team can adjust weights per indicator in the prompt without code changes. Different regions / salespeople may weight differently.

---

## Architecture: Multi-Agent Sequential System

```
User Input
    │
    ▼
[Director / Coordinator Agent]
    │
    ├──► [Hiring Signal Agent]
    ├──► [Tech Stack Agent]
    ├──► [Public News Agent]
    ├──► [Regulatory Impact Agent]     ← ENT only
    ├──► [Social Listening Agent]      ← Velocity only
    ├──► [Company Position Agent]      ← ENT only
    ├──► [Personality Inference Agent] ← ENT only
    │
    ▼
[Scoring & Ranking Agent]
    │
    ▼
[Email / EDM Drafting Agent]
    │
    ▼
Output (Report + Emails)
```

**Architecture principles:**
- **Sequential, not orchestrator** — no branching or parallel orchestration needed
- **Independent agents** — each signal agent is a separate, self-contained module (easier to maintain, fine-tune, swap)
- Each agent has its own memory / skill prompt
- Director agent coordinates the pipeline and aggregates results
- Human-in-the-loop for email sending (agent drafts, human reviews and sends)

---

### Data Sources & APIs
- LinkedIn (scraping or API)
- GitHub (API)
- ZoomInfo (API)
- Stack Overflow (API / scraping)
- Reddit (API)
- Sonar community (scraping)
- SFDC / Salesforce (CRM data for Velocity list)
- General web / news scraping

### Agent Memory System
- Agents must retain context of what they are supposed to do on every invocation
- Skills written in structured 3-part format (to be defined)
- Memory refreshes on each skill call so agent "remembers" its role and instructions

### Skills / Prompt Structure
- Skills written in a 3-part structured format (research required)
- Framework to be documented so the team can write and maintain skills independently

---

## Output Specifications

1. **Propensity-to-Buy Report** — ranked list of accounts with signal data per category
2. **Customized Outreach Email** — tailored to target personality (ENT) or developer pain point (Velocity)
3. **Product Marketing Message** — thought leadership / content recommendation to keep Sonar top-of-mind

Email style: short, direct, personalized — goal is to get a reply / spark a conversation, not a generic blast.

---

## Non-Functional Requirements

- **Maintainability:** The solution architect team must be able to fine-tune prompts and scoring without vendor help
- **Training:** 2-day training planned for solution architects / technical sales profiles post-build
- **Fine-tuning vs fixing:** Team trained to fine-tune (adjust prompts, add indicators, change scoring weights); vendor not expected to provide ongoing Day 2 support
- **Clean engagement model:** MVP is self-contained; integration into Sonar environment is a separate paid engagement if approved


---

## Open Questions / Decisions Pending

1. Confirm 3-part skill format for agent prompts
2. Confirm deployment: Docker standalone vs Sonar internal environment
3. LinkedIn data access method (scraping vs official API — compliance risk)
4. ZoomInfo API access — does Sonar have an existing subscription?
5. SFDC integration for Velocity list curation — API access needed
6. Exact ICP criteria for Velocity "create a list" mode
7. Finalize 4-colour personality model to use (DISC, Insights, etc.)
8. Define propensity-to-buy scoring weights per indicator
9. Whether email send is fully automated or always human-in-the-loop

---

## Key Constraints

- Must work within Sonar's IT security environment (Island browser, no direct installs)
- MVP is self-funded — keep infra costs minimal
- No ongoing vendor dependency for Day 2 support — team must be self-sufficient after training
- Personality inference is probabilistic — must be communicated clearly to users as a guide, not ground truth
