from __future__ import annotations

import json
import re
from pathlib import Path

from agents.base import BaseAgent
from agents.discovery.claude_discovery_search import run_discovery_search
from agents.discovery.config import (
    MIDMARKET_MIN_EMPLOYEES,
    MIDMARKET_MAX_EMPLOYEES,
)
from config.settings import ANTHROPIC_API_KEY

_PROMPT_PATH = Path(__file__).parent / "prompt.md"


class CompanyDiscoveryAgent(BaseAgent):
    """
    Builds a candidate Velocity account list from country + industry + count inputs.
    Uses Claude web search to find real mid-market companies.
    Returns a list of {company, domain, country, industry} dicts ready for the director.
    """

    def run(
        self,
        countries: list[str],
        industries: list[str],
        count: int,
    ) -> tuple[list[dict], list[str]]:
        """
        Returns (accounts, limitations).
        accounts = [{"company": str, "domain": str, "country": str, "industry": str}]
        limitations = list of strings describing any issues encountered.
        """
        if not ANTHROPIC_API_KEY:
            return [], ["ANTHROPIC_API_KEY is not configured."]

        system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
        user_message = self._build_prompt(countries, industries, count)

        try:
            raw_text, loop_limitations = run_discovery_search(
                client=self.client,
                model=self.model,
                system_prompt=system_prompt,
                user_message=user_message,
            )
        except Exception as e:
            return [], [f"Discovery search API error: {e}"]

        if not raw_text:
            return [], ["Discovery search returned no usable response."]

        accounts, parse_limitations = self._parse_response(raw_text, countries, industries)
        limitations = loop_limitations + parse_limitations

        # Trim to requested count after dedup
        accounts = accounts[:count]

        return accounts, limitations

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        countries: list[str],
        industries: list[str],
        count: int,
    ) -> str:
        countries_str = ", ".join(countries) if countries else "any"
        industries_str = ", ".join(industries) if industries else "any"

        # Ask for more than needed to have buffer after dedup
        target = min(count + 10, count * 2)

        return (
            f"## Discovery Request\n\n"
            f"Find {target} mid-market companies matching ALL of the following criteria:\n\n"
            f"- **Countries:** {countries_str}\n"
            f"- **Industries:** {industries_str}\n"
            f"- **Employee count:** {MIDMARKET_MIN_EMPLOYEES}–{MIDMARKET_MAX_EMPLOYEES} employees\n"
            f"- Must have an in-house software engineering or software development function\n\n"
            f"## Search strategy\n\n"
            f"Run web searches to discover real companies. Suggested searches:\n"
            + self._build_search_queries(countries, industries)
            + "\n\n"
            f"## Required output\n\n"
            "Return ONLY valid JSON with no markdown fences:\n\n"
            "{\n"
            '  "companies": [\n'
            '    {\n'
            '      "company": "Exact company name",\n'
            '      "domain": "example.com",\n'
            '      "country": "United Kingdom",\n'
            '      "industry": "Financial Services"\n'
            '    }\n'
            '  ],\n'
            '  "limitations": ["any issues encountered"]\n'
            "}\n\n"
            "Rules:\n"
            "- Only include companies found through web search. Do not invent any.\n"
            "- domain must be the root domain only (e.g. example.com, not https://www.example.com/about).\n"
            "- No duplicate companies.\n"
            f"- Return fewer than {target} results if you cannot find enough real companies.\n"
        )

    def _build_search_queries(self, countries: list[str], industries: list[str]) -> str:
        lines = []
        for country in countries[:3]:
            for industry in industries[:3]:
                lines.append(f'- mid-market "{industry}" companies in {country} software engineering')
                lines.append(f'- "{industry}" technology companies {country} 100 500 employees')
        if not lines:
            lines.append("- mid-market software companies with engineering teams")
        return "\n".join(lines)

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_response(
        self,
        text: str,
        countries: list[str],
        industries: list[str],
    ) -> tuple[list[dict], list[str]]:
        data = self._safe_json_loads(text)
        limitations: list[str] = []

        if not isinstance(data, dict):
            return [], ["Could not parse discovery response as JSON."]

        raw = data.get("companies", [])
        if not isinstance(raw, list):
            return [], ["Discovery response had unexpected format."]

        limitations.extend(
            str(lim) for lim in data.get("limitations", [])
            if isinstance(lim, str)
        )

        accounts: list[dict] = []
        seen: set[str] = set()

        for item in raw:
            if not isinstance(item, dict):
                continue

            company = str(item.get("company", "")).strip()
            domain = str(item.get("domain", "")).strip()
            country = str(item.get("country", countries[0] if countries else "")).strip()
            industry = str(item.get("industry", industries[0] if industries else "")).strip()

            if not company:
                continue

            # Normalise domain — strip protocol/path if Claude included them
            domain = re.sub(r"^https?://", "", domain)
            domain = domain.split("/")[0].lower().removeprefix("www.")

            key = company.lower()
            if key in seen:
                continue
            seen.add(key)

            accounts.append({
                "company": company,
                "domain": domain,
                "country": country,
                "industry": industry,
            })

        if not accounts:
            limitations.append(
                "Discovery agent found no companies matching the criteria. "
                "Try broader country or industry inputs."
            )

        return accounts, limitations

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _safe_json_loads(self, text: str) -> dict:
        text = text.strip()
        text = re.sub(r"```(?:json)?", "", text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        if start == -1:
            return {}
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        return {}
