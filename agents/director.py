from __future__ import annotations

from urllib.parse import urlparse

from agents.tech_stack.agent import TechStackAgent
from agents.hiring.agent import HiringPatternAgent
from agents.news.agent import PublicNewsAgent
from agents.company_position.agent import CompanyPositionAgent
from agents.regulatory.agent import RegulatoryImpactAgent
from agents.company_profile.agent import CompanyProfileAgent
from agents.stakeholder.agent import StakeholderIntelligenceAgent
from agents.pain_points.agent import PainPointAgent

ROLE_TERRITORY_MANAGER = "Territory Manager (Enterprise)"
ROLE_VELOCITY = "Velocity (Mid-market)"

# Stable keys used by the UI checkboxes and the run() filter
AGENT_TECH_STACK = "tech_stack"
AGENT_HIRING = "hiring_patterns"
AGENT_NEWS = "public_news"
AGENT_POSITION = "company_position"
AGENT_REGULATORY = "regulatory_impact"
AGENT_PROFILE = "company_profile"
AGENT_STAKEHOLDER = "stakeholder_intelligence"
AGENT_PAIN_POINTS = "pain_points"
AGENT_ADVISOR = "signal_advisor"

ALL_AGENTS = {
    AGENT_TECH_STACK,
    AGENT_HIRING,
    AGENT_NEWS,
    AGENT_POSITION,
    AGENT_REGULATORY,
    AGENT_PROFILE,
    AGENT_STAKEHOLDER,
    AGENT_PAIN_POINTS,
    AGENT_ADVISOR,
}


class DirectorAgent:
    def __init__(self, role: str):
        self.role = role
        self._tech_stack_agent = TechStackAgent()
        self._hiring_agent = HiringPatternAgent()
        self._news_agent = PublicNewsAgent()
        self._position_agent = CompanyPositionAgent()
        self._regulatory_agent = RegulatoryImpactAgent()
        self._profile_agent = CompanyProfileAgent()
        self._stakeholder_agent = StakeholderIntelligenceAgent()
        self._pain_points_agent = PainPointAgent()
        from agents.advisor.agent import SignalAdvisorAgent as _SignalAdvisorAgent
        self._advisor_agent = _SignalAdvisorAgent()

    def run(
        self,
        accounts: list[dict],
        progress_callback=None,
        agents_to_run: set[str] | None = None,
    ) -> list[dict]:
        """
        accounts        : list of dicts with at least 'company' key, optionally 'domain'
        progress_callback: optional function(current, total, company_name) for UI updates
        agents_to_run   : set of agent keys to run; None means run all available for the role
        returns         : list of result dicts ranked by total_score
        """
        active = agents_to_run if agents_to_run is not None else ALL_AGENTS

        results = []
        total = len(accounts)

        for i, account in enumerate(accounts):
            company = (
                account.get("company")
                or account.get("Company")
                or account.get("Account Name", "")
            )
            raw_domain = (
                account.get("domain")
                or account.get("Domain")
                or account.get("Domains")
                or account.get("domains")
                or account.get("Website", "")
            )
            # Strip full URLs down to hostname (e.g. https://www.siemens.com/en-gb/ → siemens.com)
            if raw_domain and ("://" in raw_domain or raw_domain.startswith("www.")):
                parsed = urlparse(raw_domain if "://" in raw_domain else f"https://{raw_domain}")
                raw_domain = parsed.hostname or raw_domain
                raw_domain = raw_domain.removeprefix("www.")
            domain = raw_domain or ""

            if not company:
                continue

            if progress_callback:
                progress_callback(i + 1, total, company)

            account_result = {
                "company": company,
                "domain": domain,
                "signals": {},
                "total_score": 0,
                "token_usage": {},
            }

            def _run_agent(agent, agent_key, **kwargs):
                agent._reset_usage()
                res = agent.run(**kwargs)
                account_result["token_usage"][agent_key] = agent._get_usage()
                return res

            # ── Tech Stack ────────────────────────────────────────────────────
            if AGENT_TECH_STACK in active:
                result = _run_agent(
                    self._tech_stack_agent, AGENT_TECH_STACK,
                    company=company, domain=domain,
                    country=account.get("country", account.get("Country", "")),
                    industry=account.get("industry", account.get("Industry", "")),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_TECH_STACK] = result
                account_result["total_score"] += result.get("sonar_relevance_score", 0)

            # ── Hiring Patterns ───────────────────────────────────────────────
            if AGENT_HIRING in active:
                result = _run_agent(
                    self._hiring_agent, AGENT_HIRING,
                    company=company, domain=domain,
                    country=account.get("country", account.get("Country", "")),
                    industry=account.get("industry", account.get("Industry", "")),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_HIRING] = result
                account_result["total_score"] += result.get("sonar_relevance_score", 0)

            # ── Public News ───────────────────────────────────────────────────
            if AGENT_NEWS in active:
                result = _run_agent(
                    self._news_agent, AGENT_NEWS,
                    company=company, domain=domain,
                    country=account.get("country", account.get("Country", "")),
                    industry=account.get("industry", account.get("Industry", "")),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_NEWS] = result
                account_result["total_score"] += result.get("sonar_relevance_score", 0)

            # ── Company Position (synthesis — uses whatever signals ran above) ─
            if AGENT_POSITION in active:
                result = _run_agent(
                    self._position_agent, AGENT_POSITION,
                    company=company,
                    tech_stack_result=account_result["signals"].get(AGENT_TECH_STACK),
                    hiring_result=account_result["signals"].get(AGENT_HIRING),
                    news_result=account_result["signals"].get(AGENT_NEWS),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_POSITION] = result

            # ── Regulatory Impact (ENT only) ──────────────────────────────────
            if AGENT_REGULATORY in active and self.role == ROLE_TERRITORY_MANAGER:
                result = _run_agent(
                    self._regulatory_agent, AGENT_REGULATORY,
                    company=company, domain=domain,
                    country=account.get("country", account.get("Country", "")),
                    industry=account.get("industry", account.get("Industry", "")),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_REGULATORY] = result
                account_result["total_score"] += result.get("sonar_relevance_score", 0)

            # ── Company Profile (both roles, context only) ────────────────────
            if AGENT_PROFILE in active:
                result = _run_agent(
                    self._profile_agent, AGENT_PROFILE,
                    company=company, domain=domain,
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_PROFILE] = result

            # ── Stakeholder Intelligence (ENT only, context only) ─────────────
            if AGENT_STAKEHOLDER in active and self.role == ROLE_TERRITORY_MANAGER:
                result = _run_agent(
                    self._stakeholder_agent, AGENT_STAKEHOLDER,
                    company=company, domain=domain,
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_STAKEHOLDER] = result

            # ── Pain Points (Velocity only) ───────────────────────────────────
            if AGENT_PAIN_POINTS in active and self.role == ROLE_VELOCITY:
                result = _run_agent(
                    self._pain_points_agent, AGENT_PAIN_POINTS,
                    company=company, domain=domain,
                    country=account.get("country", account.get("Country", "")),
                    industry=account.get("industry", account.get("Industry", "")),
                    tech_stack_result=account_result["signals"].get(AGENT_TECH_STACK),
                    hiring_result=account_result["signals"].get(AGENT_HIRING),
                    news_result=account_result["signals"].get(AGENT_NEWS),
                )
                result.pop("signal", None)
                account_result["signals"][AGENT_PAIN_POINTS] = result
                account_result["total_score"] += result.get("sonar_relevance_score", 0)

            # ── Signal Advisor (always last — synthesises all signals above) ──
            if AGENT_ADVISOR in active:
                self._advisor_agent._reset_usage()
                adv_result = self._advisor_agent.analyse(company, account_result["signals"])
                account_result["token_usage"][AGENT_ADVISOR] = self._advisor_agent._get_usage()
                account_result["signals"][AGENT_ADVISOR] = adv_result

            results.append(account_result)

        # Rank by propensity-to-buy score descending
        results.sort(key=lambda x: x["total_score"], reverse=True)
        for rank, result in enumerate(results, start=1):
            result["rank"] = rank

        return results
