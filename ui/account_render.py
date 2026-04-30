"""
Shared rendering helpers for account list and account detail tabs.
Used by ent_accounts.py and velocity_accounts.py.
"""
from __future__ import annotations

import json
import re
import streamlit as st
import streamlit.components.v1 as components
from collections import Counter

from agents.director import (
    AGENT_TECH_STACK, AGENT_HIRING, AGENT_NEWS,
    AGENT_POSITION, AGENT_REGULATORY, AGENT_PROFILE, AGENT_STAKEHOLDER, AGENT_PAIN_POINTS,
    AGENT_ADVISOR,
)
from config.settings import MIN_NEWS_COUNT

_CATEGORY_LABELS = {
    # Current agent category keys
    "devsecops_appsec":            "DevSecOps / AppSec",
    "devops_platform":             "DevOps / Platform",
    "software_engineering_growth": "Software Engineering",
    "cloud_infrastructure":        "Cloud / Infrastructure",
    "security_compliance":         "Security / Compliance",
    # Legacy keys from prior agent version
    "devsecops":                   "DevSecOps / AppSec",
    "devops":                      "DevOps / Platform",
    "software_engineer":           "Software Engineering",
    "security":                    "Security",
    "cloud":                       "Cloud / Infrastructure",
    "language":                    "Language Signal",
}

_WHY_NEWS = {
    # Current category keys
    "cybersecurity_incident":   "Active security incident — urgent pressure to improve code security posture",
    "cloud_ai_transformation":  "Cloud/AI transformation means new code being written — quality gate needs grow",
    "product_platform_launch":  "New product or platform launch signals active development — potential quality gaps",
    "engineering_investment":   "Engineering investment signals growing dev teams — code quality standards need to scale",
    "leadership_change":        "Leadership change often triggers technology stack reviews",
    # Legacy keys from prior agent version
    "security_incident":        "Active security incident — urgent pressure to improve code security posture",
    "compliance_regulatory":    "Regulatory requirement — compliance deadlines drive SAST/code quality investment",
    "cloud_ai_initiative":      "Cloud/AI expansion means more code being written — quality gate needs grow",
    "product_launch":           "New product launch signals active development — potential quality gaps",
    "acquisition":              "M&A activity creates code integration challenges across teams",
    "hiring_wave":              "Hiring surge indicates growing dev teams — code quality standards need to scale",
}

_REG_RELEVANCE = {
    "active_fine_lawsuit":          "Active enforcement — urgent compliance need",
    "specific_regulation_applies":  "Direct regulation — Sonar addresses requirement",
    "compliance_audit":             "Audit activity — code quality under scrutiny",
    "regulated_industry":           "Regulated industry — compliance baseline expected",
    "regional_regulator_relevance": "Regional regulator active in this space",
    "general_regulatory_mention":   "General regulatory context",
}

_PAIN_CATEGORY_LABELS = {
    "security_incident_pain":   "Security Incident",
    "code_quality_pain":        "Code Quality",
    "static_analysis_pain":     "Static Analysis",
    "ci_cd_integration_pain":   "CI/CD Integration",
    "technical_debt_pain":      "Technical Debt",
    "developer_velocity_pain":  "Developer Velocity",
    "competitor_tooling_pain":  "Competitor Tooling",
    "sonar_specific_pain":      "Sonar-Specific",
}

_PAIN_CATEGORY_COLORS = {
    "security_incident_pain":   "#ef4444",
    "code_quality_pain":        "#f59e0b",
    "static_analysis_pain":     "#3b82f6",
    "ci_cd_integration_pain":   "#8b5cf6",
    "technical_debt_pain":      "#f97316",
    "developer_velocity_pain":  "#06b6d4",
    "competitor_tooling_pain":  "#ec4899",
    "sonar_specific_pain":      "#00d4aa",
}

_PERSONALITY_OPTIONS = ["Red", "Blue", "Green", "Yellow", "Unknown"]
_PERSONALITY_CAPTIONS = ["Direct/ROI", "Analytical", "Relationship", "Vision", "Neutral"]
_PERSONALITY_COLORS = {
    "Red": "#ef4444", "Blue": "#3b82f6",
    "Green": "#22c55e", "Yellow": "#eab308", "Unknown": "#94a3b8",
}

_TABLE_CSS = """
<style>
.si-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 6px;
    font-size: 0.875rem;
}
.si-table th {
    text-align: left; padding: 10px 12px; color: #94a3b8;
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    border-bottom: 1px solid #1e293b;
}
.si-table td {
    padding: 14px 12px;
    background: #111827;
    color: #f8fafc;
    vertical-align: middle;
    border-top: 1px solid #1e293b;
    border-bottom: 1px solid #1e293b;
    word-break: break-word;
    white-space: normal;
    line-height: 1.5;
}
.si-table td:first-child { border-left: 1px solid #1e293b; border-radius: 8px 0 0 8px; }
.si-table td:last-child  { border-right: 1px solid #1e293b; border-radius: 0 8px 8px 0; }
.si-table tr:hover td { background: #1a2638; }
.si-link {
    color: #00d4aa; text-decoration: none; font-weight: 600;
    display: inline-flex; align-items: center; gap: 4px;
}
.si-link:hover { color: #00b894; text-decoration: underline; }
.si-badge {
    display: inline-block;
    background: rgba(0,212,170,0.12); color: #00d4aa;
    padding: 3px 10px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.si-news-card {
    background: #111827; border: 1px solid #1e293b;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
    transition: border-color 0.2s ease;
}
.si-news-card:hover { border-color: #00d4aa; }
.si-row-card {
    background: #111827; border: 1px solid #1e293b;
    border-radius: 8px; padding: 12px 14px; margin-bottom: 6px;
}
</style>
"""


def _html_table(rows: list[dict], link_cols: set | None = None, col_styles: dict | None = None) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    link_cols = link_cols or set()
    col_styles = col_styles or {}
    ths = "".join(f"<th style='{col_styles.get(h, '')}'>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        tds = ""
        for h in headers:
            val = row.get(h, "") or ""
            style = col_styles.get(h, "")
            if h in link_cols and val:
                tds += f"<td style='{style}'><a class='si-link' href='{val}' target='_blank'>VIEW ↗</a></td>"
            else:
                tds += f"<td style='{style}'>{val}</td>"
        body += f"<tr>{tds}</tr>"
    return f"{_TABLE_CSS}<table class='si-table'><thead><tr>{ths}</tr></thead><tbody>{body}</tbody></table>"


def _ck(company: str) -> str:
    """Safe session-state key prefix from company name."""
    return re.sub(r"\W+", "_", company.lower()).strip("_")


def prefetch_advisor(r: dict):
    """Load stored Signal Advisor result into session state — no API call."""
    ck = _ck(r["company"])
    if f"adv_result_{ck}" in st.session_state:
        return
    stored = r.get("signals", {}).get(AGENT_ADVISOR)
    st.session_state[f"adv_result_{ck}"] = stored if stored else {}


def add_tab(tabs_key: str, tab_config: dict):
    for i, existing in enumerate(st.session_state[tabs_key]):
        if existing.get("type") == tab_config.get("type") and existing.get("label") == tab_config.get("label"):
            # Already exists — navigate to it
            st.session_state[tabs_key + "_navigate_to"] = i + 1  # +1 for dashboard tab
            return
    st.session_state[tabs_key].append(tab_config)
    st.session_state[tabs_key + "_navigate_to"] = len(st.session_state[tabs_key])  # new last tab


# ── Account list (ranked table) ───────────────────────────────────────────────

def render_run_content(results: list, run_path: str, tabs_key: str, show_position: bool = True):
    _POS_COLORS = {
        "AI Leader":     "#00d4aa",
        "Early Adopter": "#3b82f6",
        "Mainstream":    "#f59e0b",
        "Skeptic":       "#f97316",
        "Laggard":       "#ef4444",
    }

    if show_position:
        h1, h2, h3, h4, h5 = st.columns([0.5, 3, 2.5, 1, 2])
        for col, label in zip([h1, h2, h3, h4, h5], ["RANK", "COMPANY", "INDUSTRY", "SCORE", "POSITION"]):
            col.markdown(
                f"<span style='color:#94a3b8;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em'>{label}</span>",
                unsafe_allow_html=True,
            )
    else:
        h1, h2, h3, h4 = st.columns([0.5, 3, 2.5, 1])
        for col, label in zip([h1, h2, h3, h4], ["RANK", "COMPANY", "INDUSTRY", "SCORE"]):
            col.markdown(
                f"<span style='color:#94a3b8;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em'>{label}</span>",
                unsafe_allow_html=True,
            )
    st.markdown("<hr style='border:0;border-top:1px solid #1e293b;margin:6px 0'>", unsafe_allow_html=True)

    for i, r in enumerate(results):
        industry = (
            r.get("industry") or r.get("Industry")
            or r["signals"].get(AGENT_REGULATORY, {}).get("industry_detected", "—")
            or "—"
        ).capitalize()
        score = round(r["total_score"], 1)

        if show_position:
            position = r["signals"].get(AGENT_POSITION, {}).get("position_label", "—")
            pos_color = _POS_COLORS.get(position, "#94a3b8")
            c1, c2, c3, c4, c5 = st.columns([0.5, 3, 2.5, 1, 2])
        else:
            c1, c2, c3, c4 = st.columns([0.5, 3, 2.5, 1])

        c1.markdown(f"<span style='color:#94a3b8;font-weight:600'>{r['rank']}</span>", unsafe_allow_html=True)
        if c2.button(r["company"], key=f"row_{tabs_key}_{i}", type="tertiary"):
            add_tab(tabs_key, {"type": "account", "run_path": run_path, "idx": i, "label": r["company"]})
            st.rerun()
        c3.markdown(f"<span style='color:#94a3b8'>{industry}</span>", unsafe_allow_html=True)
        c4.markdown(f"<span style='font-weight:700;color:#f8fafc'>{score}</span>", unsafe_allow_html=True)
        if show_position:
            c5.markdown(f"<span style='color:{pos_color};font-weight:600'>{position}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:0;border-top:1px solid #1e293b;margin:2px 0'>", unsafe_allow_html=True)


# ── Account detail ────────────────────────────────────────────────────────────

def render_account_content(r: dict, show_email: bool = False, velocity_mode: bool = False, run_path: str = ""):
    sigs = r["signals"]
    ck = _ck(r["company"])
    selected_items: list[dict] = []

    st.markdown(
        f"<span style='color:#94a3b8;font-size:0.85rem'>Rank #{r['rank']}  ·  Domain: {r.get('domain', '—')}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span class='si-badge'>Propensity Score: {round(r['total_score'], 2)}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(_TABLE_CSS, unsafe_allow_html=True)
    st.markdown("---")

    # ── Company Profile ───────────────────────────────────────────────────────
    profile = sigs.get(AGENT_PROFILE)
    if profile and profile.get("snapshot"):
        snap = profile["snapshot"]
        with st.expander("Company Profile", expanded=True):
            for label, key in [
                ("What they do",     "what_they_do"),
                ("Who they sell to", "who_they_sell_to"),
                ("Business model",   "business_model"),
                ("Key acquisitions", "key_acquisition"),
                ("AI posture",       "ai_posture"),
            ]:
                val = snap.get(key, "")
                if val:
                    st.markdown(f"<span style='color:#f8fafc'><strong>{label}:</strong> {val}</span>", unsafe_allow_html=True)

    # ── Tech Stack ────────────────────────────────────────────────────────────
    ts = sigs.get(AGENT_TECH_STACK)
    if ts:
        with st.expander(f"Technology Stack  ·  Score: {ts.get('sonar_relevance_score', 0)}/10", expanded=True):
            ev_lookup = {e["id"]: e for e in ts.get("evidence", [])}
            grouped_rows = []
            detail_rows = []
            for cat_label, items in [
                ("Language",       ts.get("languages", [])),
                ("CI/CD",          ts.get("cicd_tools", [])),
                ("Cloud / DevOps", ts.get("cloud", [])),
                ("Security Tool",  ts.get("security_tools", [])),
            ]:
                if not items:
                    continue
                findings_str = "  ·  ".join(item.get("name", "") for item in items)
                first_url = next(
                    (ev_lookup[ids[0]].get("source_url") or ev_lookup[ids[0]].get("repo_url", "")
                     for item in items
                     for ids in [item.get("evidence_ids", [])]
                     if ids and ids[0] in ev_lookup
                     and (ev_lookup[ids[0]].get("source_url") or ev_lookup[ids[0]].get("repo_url"))),
                    ""
                )
                grouped_rows.append({
                    "cat": cat_label, "findings": findings_str,
                    "count": len(items), "url": first_url,
                })
                for item in items:
                    ev_ids = item.get("evidence_ids", [])
                    first_ev = ev_lookup.get(ev_ids[0]) if ev_ids else None
                    detail_rows.append({
                        "Category":   cat_label,
                        "Finding":    item.get("name", "—"),
                        "Evidence":   first_ev["evidence_text"] if first_ev else "—",
                        "Source":     (first_ev.get("source_url") or first_ev.get("repo_url", "")) if first_ev else "",
                        "Confidence": item.get("confidence", "—"),
                    })

            if grouped_rows:
                hc = st.columns([0.04, 1.2, 2.5, 0.4, 0.5]) if show_email else st.columns([1.2, 2.5, 0.4, 0.5])
                labels = ["CATEGORY", "FINDINGS", "#", "SOURCE"]
                for col, lbl in zip(hc[1:] if show_email else hc, labels):
                    col.markdown(
                        f"<span style='color:#94a3b8;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em'>{lbl}</span>",
                        unsafe_allow_html=True,
                    )
                st.markdown("<hr style='border:0;border-top:1px solid #1e293b;margin:2px 0 6px 0'>", unsafe_allow_html=True)

                for idx, row in enumerate(grouped_rows):
                    cols = st.columns([0.04, 1.2, 2.5, 0.4, 0.5]) if show_email else st.columns([1.2, 2.5, 0.4, 0.5])
                    data_cols = cols[1:] if show_email else cols
                    if show_email:
                        key = f"eml_{ck}_ts_{idx}"
                        cols[0].checkbox("", key=key, label_visibility="collapsed")
                        if st.session_state.get(key):
                            selected_items.append({"type": "tech_stack", "content": f"{row['cat']}: {row['findings']}"})
                    data_cols[0].markdown(f"<span style='color:#f8fafc;font-weight:600;font-size:0.85rem'>{row['cat']}</span>", unsafe_allow_html=True)
                    data_cols[1].markdown(f"<span style='color:#f8fafc;font-size:0.85rem'>{row['findings']}</span>", unsafe_allow_html=True)
                    data_cols[2].markdown(f"<span style='color:#f8fafc;font-size:0.85rem'>{row['count']}</span>", unsafe_allow_html=True)
                    if row["url"]:
                        data_cols[3].markdown(f"<a class='si-link' href='{row['url']}' target='_blank'>VIEW ↗</a>", unsafe_allow_html=True)
                    st.markdown("<hr style='border:0;border-top:1px solid #1e293b;margin:2px 0'>", unsafe_allow_html=True)

                if detail_rows:
                    with st.expander("View full evidence detail"):
                        st.markdown(_html_table(detail_rows, link_cols={"Source"}), unsafe_allow_html=True)
            else:
                st.caption("No tech stack signals detected.")

    # ── Hiring Signals ────────────────────────────────────────────────────────
    hiring = sigs.get(AGENT_HIRING)
    if hiring:
        with st.expander(f"Hiring Signals  ·  Score: {hiring.get('sonar_relevance_score', 0)}/10", expanded=True):
            if hiring.get("summary"):
                st.caption(hiring["summary"])
            all_evidence = [e for e in hiring.get("evidence", []) if e.get("counted_in_score")] or hiring.get("evidence", [])
            evidence = [e for e in all_evidence if e.get("source_url", "").strip()]
            hidden_count = len(all_evidence) - len(evidence)

            if evidence:
                counts = Counter((e.get("value", ""), e.get("type", "")) for e in evidence)
                seen: set = set()
                deduped = []
                for e in evidence:
                    key = (e.get("value", ""), e.get("type", ""))
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(e)

                for idx, e in enumerate(deduped):
                    cat = _CATEGORY_LABELS.get(e.get("type", ""), e.get("type", "—"))
                    count_str = f"{counts[(e.get('value',''), e.get('type',''))]}+"
                    url = e.get("source_url", "")
                    link_html = f'<a class="si-link" href="{url}" target="_blank">VIEW ↗</a>' if url else ""

                    if show_email:
                        cb_col, card_col = st.columns([0.04, 0.96])
                        sel_key = f"eml_{ck}_hire_{idx}"
                        cb_col.checkbox("", key=sel_key, label_visibility="collapsed")
                        if st.session_state.get(sel_key):
                            selected_items.append({"type": "hiring", "content": f"Hiring for {e.get('value','—')} ({cat}) — {count_str} postings"})
                    else:
                        card_col = st.container()

                    with card_col:
                        st.markdown(f"""
<div class="si-row-card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-weight:600;color:#f8fafc;font-size:0.875rem">{e.get('value','—')}</span>
    <span style="color:#00d4aa;font-size:0.75rem;font-weight:700">{count_str} postings</span>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
    <span style="color:#94a3b8;font-size:0.78rem">{cat}  ·  {e.get('confidence','—')}</span>
    {link_html}
  </div>
</div>""", unsafe_allow_html=True)

                if hidden_count > 0:
                    st.caption(f"ℹ {hidden_count} signal(s) not shown — no source URL available to verify.")
            else:
                st.caption("No hiring signals detected.")

    # ── Public News ───────────────────────────────────────────────────────────
    news = sigs.get(AGENT_NEWS)
    if news:
        with st.expander(f"Public News  ·  Score: {news.get('sonar_relevance_score', 0)}/10", expanded=True):
            evidence = [e for e in news.get("evidence", []) if e.get("counted_in_score")]
            if evidence:
                for idx, e in enumerate(evidence):
                    signal    = e.get("signal_type", "")
                    date      = e.get("published_date", "") or ""
                    headline  = e.get("title", "—")
                    why       = _WHY_NEWS.get(signal, signal.replace("_", " ").title())
                    url       = e.get("url", "")
                    link_html = f'<a class="si-link" href="{url}" target="_blank">READ ARTICLE ↗</a>' if url else ""

                    if show_email:
                        cb_col, card_col = st.columns([0.04, 0.96])
                        sel_key = f"eml_{ck}_news_{idx}"
                        cb_col.checkbox("", key=sel_key, label_visibility="collapsed")
                        if st.session_state.get(sel_key):
                            snippet = e.get("snippet", "").strip()
                            content = f"{headline} ({date}) | Signal: {signal.replace('_', ' ')} | Why relevant to Sonar: {why}"
                            if snippet:
                                content += f" | Article excerpt: {snippet}"
                            selected_items.append({"type": "news", "content": content})
                    else:
                        card_col = st.container()

                    article_summary = e.get("article_summary", "")
                    summary_html = (
                        f"<div style='color:#cbd5e1;font-size:0.82rem;margin-bottom:10px;"
                        f"line-height:1.55;font-style:italic'>{article_summary}</div>"
                        if article_summary else ""
                    )
                    with card_col:
                        st.markdown(f"""
<div class="si-news-card">
  <div style="color:#00d4aa;font-size:0.7rem;font-weight:700;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em">{date}</div>
  <div style="font-weight:600;color:#f8fafc;margin-bottom:8px;line-height:1.45;font-size:0.9rem">{headline}</div>
  {summary_html}
  <div style="margin-bottom:10px">
    <span style="color:#00d4aa;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em">Why it matters to Sonar</span>
    <div style="color:#94a3b8;font-size:0.82rem;margin-top:3px;line-height:1.5">{why}</div>
  </div>
  {link_html}
</div>""", unsafe_allow_html=True)
            else:
                st.caption("No news evidence found.")

    # ── Developer Pain Points (Velocity only) ────────────────────────────────
    pain = sigs.get(AGENT_PAIN_POINTS)
    if pain:
        score_val = pain.get("sonar_relevance_score", 0)
        with st.expander(f"Developer Pain Points  ·  Score: {round(score_val, 1)}/10", expanded=True):
            def _bullets(text: str, color: str = "#94a3b8") -> str:
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
                items = "".join(
                    f"<li style='color:{color};font-size:0.83rem;line-height:1.6;margin-bottom:3px'>{s}</li>"
                    for s in sentences
                )
                return f"<ul style='margin:4px 0 0 0;padding-left:18px'>{items}</ul>"

            if pain.get("summary"):
                st.markdown(
                    f"<span style='color:#00d4aa;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.07em'>Summary</span>"
                    + _bullets(pain["summary"]),
                    unsafe_allow_html=True,
                )
            if pain.get("sonar_relevance_reason"):
                st.markdown(
                    f"<div style='margin-top:10px'><span style='color:#00d4aa;font-size:0.68rem;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.07em'>Why Sonar</span>"
                    + _bullets(pain["sonar_relevance_reason"])
                    + "</div>",
                    unsafe_allow_html=True,
                )
            if pain.get("recommended_sales_angle"):
                angle_bullets = _bullets(pain["recommended_sales_angle"], color="#f8fafc")
                st.markdown(
                    f"<div style='background:rgba(0,212,170,0.08);border-left:3px solid #00d4aa;"
                    f"padding:10px 14px;border-radius:0 8px 8px 0;margin:10px 0'>"
                    f"<span style='color:#00d4aa;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.07em'>Recommended Sales Angle</span>"
                    f"{angle_bullets}</div>",
                    unsafe_allow_html=True,
                )

            evidence = [e for e in pain.get("evidence", []) if e.get("counted_in_score")]
            if not evidence:
                evidence = pain.get("evidence", [])

            if evidence:
                st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
                for e in evidence:
                    cat_key   = e.get("category", "")
                    cat_label = _PAIN_CATEGORY_LABELS.get(cat_key, cat_key.replace("_", " ").title())
                    cat_color = _PAIN_CATEGORY_COLORS.get(cat_key, "#94a3b8")
                    conf      = e.get("confidence", "—")
                    ev_text   = e.get("evidence_text", "—")
                    url       = e.get("source_url", "")
                    title     = e.get("title", "")
                    keywords  = e.get("matched_keywords", [])
                    link_html = f'<a class="si-link" href="{url}" target="_blank">SOURCE ↗</a>' if url else ""
                    kw_html   = (
                        "  ·  " + "  ".join(
                            f"<span style='background:rgba(0,212,170,0.1);color:#00d4aa;padding:1px 7px;"
                            f"border-radius:4px;font-size:0.68rem'>{kw}</span>"
                            for kw in keywords[:5]
                        )
                        if keywords else ""
                    )

                    ev_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', ev_text.strip()) if s.strip()]
                    ev_bullets = "".join(
                        f"<li style='color:#94a3b8;font-size:0.82rem;line-height:1.55;margin-bottom:3px'>{s}</li>"
                        for s in ev_sentences
                    )
                    ev_html = f"<ul style='margin:0 0 10px 0;padding-left:18px'>{ev_bullets}</ul>" if ev_sentences else ""

                    st.markdown(f"""
<div class="si-news-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="background:{cat_color}22;color:{cat_color};padding:2px 10px;border-radius:5px;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em">{cat_label}</span>
    <span style="color:#94a3b8;font-size:0.75rem">{conf}</span>
  </div>
  {"<div style='font-weight:600;color:#f8fafc;font-size:0.875rem;margin-bottom:6px;line-height:1.4'>" + title + "</div>" if title else ""}
  {ev_html}
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:0.75rem">{kw_html}</span>
    {link_html}
  </div>
</div>""", unsafe_allow_html=True)
            elif pain.get("status") == "no_data":
                st.caption("No company-linked pain signals found in public sources.")

            if pain.get("limitations"):
                with st.expander("⚠ Research Limitations", expanded=False):
                    for lim in pain["limitations"]:
                        st.caption(lim)

    # ── Company Position ──────────────────────────────────────────────────────
    pos = sigs.get(AGENT_POSITION)
    if pos:
        _pos_colors = {
            "AI Leader":     "#00d4aa",
            "Early Adopter": "#3b82f6",
            "Mainstream":    "#f59e0b",
            "Skeptic":       "#f97316",
            "Laggard":       "#ef4444",
        }
        label = pos.get("position_label", "—")
        color = _pos_colors.get(label, "#94a3b8")
        with st.expander(f"Company Position  ·  {label}", expanded=True):
            st.markdown(
                f"<span style='color:{color};font-weight:700;font-size:1rem'>{label}</span>"
                f"<span style='color:#94a3b8;font-size:0.82rem;margin-left:12px'>"
                f"Score: {pos.get('classification_score',0)}/10</span>",
                unsafe_allow_html=True,
            )
            summary = pos.get("summary", "")
            if summary:
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary.strip()) if s.strip()]
                bullets = "".join(
                    f"<li style='color:#f8fafc;font-size:0.85rem;line-height:1.6;margin-bottom:4px'>{s}</li>"
                    for s in sentences[:5]
                )
                st.markdown(
                    f"<ul style='margin:10px 0 0 0;padding-left:18px'>{bullets}</ul>",
                    unsafe_allow_html=True,
                )

    # ── Regulatory Impact ─────────────────────────────────────────────────────
    reg = sigs.get(AGENT_REGULATORY)
    if reg:
        with st.expander(f"Regulatory Impact  ·  Score: {round(reg.get('sonar_relevance_score', 0), 2)}/10", expanded=True):
            all_evidence = [e for e in reg.get("evidence", []) if e.get("counted_in_score")] or reg.get("evidence", [])
            evidence = [e for e in all_evidence if e.get("source_url", "").strip()]
            hidden_count = len(all_evidence) - len(evidence)

            if evidence:
                for idx, e in enumerate(evidence):
                    regulation = e.get("regulation", "—") or "—"
                    finding    = e.get("evidence_text", "—")
                    relevance  = _REG_RELEVANCE.get(e.get("type", ""), e.get("type", "—").replace("_", " ").title())
                    url        = e.get("source_url", "")
                    conf       = e.get("confidence", "—")
                    link_html  = f'<a class="si-link" href="{url}" target="_blank">VIEW ↗</a>' if url else ""

                    if show_email:
                        cb_col, card_col = st.columns([0.04, 0.96])
                        sel_key = f"eml_{ck}_reg_{idx}"
                        cb_col.checkbox("", key=sel_key, label_visibility="collapsed")
                        if st.session_state.get(sel_key):
                            selected_items.append({"type": "regulatory", "content": f"{regulation}: {finding}"})
                    else:
                        card_col = st.container()

                    with card_col:
                        st.markdown(f"""
<div class="si-row-card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-weight:700;color:#f8fafc;font-size:0.875rem">{regulation}</span>
    <span style="color:#94a3b8;font-size:0.75rem">{conf}</span>
  </div>
  <div style="color:#94a3b8;font-size:0.82rem;margin-top:5px;line-height:1.45">{finding}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
    <span style="color:#00d4aa;font-size:0.72rem;font-weight:600">{relevance}</span>
    {link_html}
  </div>
</div>""", unsafe_allow_html=True)

                if hidden_count > 0:
                    st.caption(f"ℹ {hidden_count} industry-mapping finding(s) not shown — no direct source URL available.")
            else:
                st.caption("No regulatory evidence found.")

    # ── Stakeholders ──────────────────────────────────────────────────────────
    sk = sigs.get(AGENT_STAKEHOLDER)
    if sk and sk.get("stakeholders"):
        with st.expander("Stakeholder Intelligence", expanded=True):
            sk_rows = [{
                "Name":                 p.get("name", ""),
                "Role":                 p.get("role", ""),
                "LinkedIn":             p.get("linkedin_url", ""),
                "Confidence":           p.get("confidence", ""),
                "Personality":          p.get("personality_display", ""),
                "Why this personality": p.get("personality_reasoning", "—"),
            } for p in sk["stakeholders"]]
            st.markdown(_html_table(
                sk_rows, link_cols={"LinkedIn"},
                col_styles={
                    "LinkedIn":    "width:80px;text-align:center",
                    "Confidence":  "width:80px",
                    "Personality": "width:120px",
                },
            ), unsafe_allow_html=True)

    # ── Email Draft Panel ─────────────────────────────────────────────────────
    if show_email:
        _render_email_panel(r, sigs, selected_items, ck, velocity_mode=velocity_mode, run_path=run_path)


def _save_advisor_to_run(run_path: str, company: str, adv_result: dict):
    """Persist a freshly-run advisor result back into the saved run JSON."""
    if not run_path:
        return
    try:
        import json as _json
        from ui.results_store import load_run
        run = load_run(run_path)
        for res in run.get("results", []):
            if res["company"] == company:
                res["signals"][AGENT_ADVISOR] = adv_result
                break
        with open(run_path, "w", encoding="utf-8") as f:
            _json.dump(run, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _render_email_panel(r: dict, sigs: dict, selected_items: list, ck: str, velocity_mode: bool = False, run_path: str = ""):
    st.markdown("---")
    st.markdown("### Draft Outreach Email")

    # ── Signal Advisor — loaded from stored research result ──────────────────
    adv_result = st.session_state.get(f"adv_result_{ck}", {})

    # Advisor output
    advisor_selected_items: list[dict] = []
    strategy_note = ""

    if not adv_result:
        st.markdown(
            "<div style='background:rgba(148,163,184,0.06);border:1px solid #1e293b;"
            "border-radius:10px;padding:14px 18px;margin-bottom:14px'>"
            "<span style='color:#94a3b8;font-size:0.83rem'>"
            "Signal Advisor was not included in this research run. "
            "Enable <strong>Signal Advisor</strong> on the Home page before running research, "
            "or click <strong>Run Advisor Now</strong> below.</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("Run Advisor Now", key=f"adv_run_now_{ck}", type="secondary"):
            from agents.advisor.agent import SignalAdvisorAgent
            with st.spinner("Analysing signals..."):
                adv_result = SignalAdvisorAgent().analyse(r["company"], sigs)
            st.session_state[f"adv_result_{ck}"] = adv_result
            _save_advisor_to_run(run_path, r["company"], adv_result)
            st.rerun()

    if adv_result:
        if adv_result.get("error") and not adv_result.get("hook_title"):
            st.warning(f"Advisor could not analyse signals: {adv_result['error']}")
        else:
            hook_title     = adv_result.get("hook_title", "")
            hook_rationale = adv_result.get("hook_rationale", "")
            strategy_note  = adv_result.get("strategy_note", "")
            suggested      = adv_result.get("suggested_signals", [])

            # Recommendation card
            st.markdown(
                f"<div style='background:rgba(0,212,170,0.06);border:1px solid rgba(0,212,170,0.3);"
                f"border-radius:12px;padding:18px 20px;margin:10px 0 14px 0'>"
                f"<div style='color:#00d4aa;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:0.08em;margin-bottom:8px'>Recommended Hook</div>"
                f"<div style='color:#f8fafc;font-weight:700;font-size:1rem;line-height:1.4;"
                f"margin-bottom:10px'>{hook_title}</div>"
                f"<div style='color:#94a3b8;font-size:0.83rem;line-height:1.6'>{hook_rationale}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if suggested:
                st.markdown(
                    "<div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;"
                    "letter-spacing:0.06em;margin-bottom:8px'>Recommended Signals "
                    "<span style='color:#1e293b;font-size:0.68rem'>"
                    "— tick to include in email</span></div>",
                    unsafe_allow_html=True,
                )

                _SIG_COLORS = {
                    "news":        "#3b82f6",
                    "hiring":      "#00d4aa",
                    "tech_stack":  "#8b5cf6",
                    "regulatory":  "#f59e0b",
                    "pain_points": "#ef4444",
                }

                for idx, sig in enumerate(suggested):
                    adv_key = f"adv_sig_{ck}_{idx}"
                    if adv_key not in st.session_state:
                        st.session_state[adv_key] = True  # pre-ticked

                    cb_col, card_col = st.columns([0.04, 0.96])
                    cb_col.checkbox("", key=adv_key, label_visibility="collapsed")
                    if st.session_state.get(adv_key):
                        advisor_selected_items.append({
                            "type":    sig.get("type", "signal"),
                            "content": sig.get("content", ""),
                        })

                    sig_type  = sig.get("type", "")
                    type_color = _SIG_COLORS.get(sig_type, "#94a3b8")
                    with card_col:
                        st.markdown(
                            f"<div class='si-row-card'>"
                            f"<div style='display:flex;align-items:flex-start;gap:10px'>"
                            f"<span style='background:{type_color}22;color:{type_color};padding:2px 8px;"
                            f"border-radius:4px;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
                            f"white-space:nowrap'>{sig_type.replace('_', ' ')}</span>"
                            f"<div>"
                            f"<div style='color:#f8fafc;font-size:0.85rem;font-weight:600;"
                            f"line-height:1.35'>{sig.get('label', '')}</div>"
                            f"<div style='color:#94a3b8;font-size:0.78rem;margin-top:3px;"
                            f"line-height:1.4'>{sig.get('why', '')}</div>"
                            f"</div></div></div>",
                            unsafe_allow_html=True,
                        )

            col_note, col_rerun = st.columns([3, 1])
            col_note.markdown(
                "<div style='color:#94a3b8;font-size:0.72rem;margin-top:6px'>"
                "Untick any signal you want to remove.</div>",
                unsafe_allow_html=True,
            )
            if col_rerun.button("Re-analyse", key=f"adv_rerun_{ck}", type="secondary"):
                from agents.advisor.agent import SignalAdvisorAgent
                with st.spinner("Re-analysing signals..."):
                    adv_result = SignalAdvisorAgent().analyse(r["company"], sigs)
                st.session_state[f"adv_result_{ck}"] = adv_result
                _save_advisor_to_run(run_path, r["company"], adv_result)
                st.rerun()

    # Determine which signals to pass to the email agent
    # Advisor items take priority; fall back to manually ticked if advisor not run
    effective_selected = (
        advisor_selected_items
        if (adv_result and not (adv_result.get("error") and not adv_result.get("hook_title")))
        else selected_items
    )

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    sender_name = st.text_input(
        "YOUR NAME (appears in sign-off)",
        key=f"eml_sender_{ck}",
        placeholder="e.g. Sarah Lim",
    )

    if velocity_mode:
        # ── Velocity: manual contact only, no stakeholder / personality ───────
        col_name, col_role = st.columns(2, gap="large")
        target_name = col_name.text_input(
            "CONTACT NAME", key=f"eml_name_{ck}", placeholder="e.g. Thomas Müller"
        )
        target_role = col_role.text_input(
            "CONTACT ROLE", key=f"eml_role_{ck}", placeholder="e.g. Head of Engineering"
        )
        personality = "Unknown"

    else:
        # ── ENT: stakeholder dropdown + personality colour ────────────────────
        col_target, col_personality = st.columns(2, gap="large")

        with col_target:
            st.markdown("**Target Contact**")
            stakeholders = sigs.get(AGENT_STAKEHOLDER, {}).get("stakeholders", []) if sigs.get(AGENT_STAKEHOLDER) else []

            target_name = ""
            target_role = ""

            if stakeholders:
                options = [f"{p['name']}  —  {p['role']}" for p in stakeholders] + ["Enter manually"]
                choice = st.selectbox("SELECT STAKEHOLDER", options, key=f"eml_target_{ck}")
                if choice == "Enter manually":
                    target_name = st.text_input("CONTACT NAME", key=f"eml_name_{ck}", placeholder="e.g. Thomas Müller")
                    target_role = st.text_input("CONTACT ROLE", key=f"eml_role_{ck}", placeholder="e.g. Head of Engineering")
                else:
                    idx = options.index(choice)
                    target_name = stakeholders[idx]["name"]
                    target_role = stakeholders[idx]["role"]
                    inferred = stakeholders[idx].get("personality_display", "")
                    if inferred:
                        st.caption(f"Inferred personality: **{inferred}**")
            else:
                st.caption("No stakeholders found from analysis. Enter manually.")
                target_name = st.text_input("CONTACT NAME", key=f"eml_name_{ck}", placeholder="e.g. Thomas Müller")
                target_role = st.text_input("CONTACT ROLE", key=f"eml_role_{ck}", placeholder="e.g. Head of Engineering")

        with col_personality:
            st.markdown("**Personality Colour**")

            default_personality = "Unknown"
            if stakeholders and sigs.get(AGENT_STAKEHOLDER):
                choice_key = f"eml_target_{ck}"
                choice_val = st.session_state.get(choice_key, "")
                if choice_val and choice_val != "Enter manually":
                    try:
                        si = [f"{p['name']}  —  {p['role']}" for p in stakeholders].index(choice_val)
                        raw = stakeholders[si].get("personality_display", "")
                        for c in ["Red", "Blue", "Green", "Yellow"]:
                            if c.lower() in raw.lower():
                                default_personality = c
                                break
                    except (ValueError, IndexError):
                        pass

            personality_key = f"eml_personality_{ck}"
            if personality_key not in st.session_state:
                st.session_state[personality_key] = default_personality

            personality = st.radio(
                "TONE",
                options=_PERSONALITY_OPTIONS,
                key=personality_key,
                horizontal=True,
            )

            pers_color = _PERSONALITY_COLORS.get(personality, "#94a3b8")
            desc = {
                "Red":     "Direct, results-focused, no fluff",
                "Blue":    "Analytical, evidence-based, detailed",
                "Green":   "Relationship-driven, collaborative, warm",
                "Yellow":  "Visionary, enthusiastic, big-picture",
                "Unknown": "Neutral, professional, fact-led",
            }
            st.markdown(
                f"<span style='color:{pers_color};font-size:0.8rem'>{desc.get(personality,'')}</span>",
                unsafe_allow_html=True,
            )

    # ── Generate ──────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    can_generate = bool((target_name or "").strip())

    profile = sigs.get(AGENT_PROFILE, {})
    company_context = profile.get("snapshot", {}) if profile else {}
    company_position = sigs.get(AGENT_POSITION, {}).get("position_label", "—") if sigs.get(AGENT_POSITION) else "—"

    gen_col, regen_col = st.columns([2, 1])
    with gen_col:
        if st.button(
            "Generate Email Draft",
            type="primary",
            key=f"eml_btn_{ck}",
            disabled=not can_generate,
        ):
            from agents.email.agent import EmailDraftAgent
            with st.spinner("Drafting email..."):
                result = EmailDraftAgent().draft(
                    company=r["company"],
                    target_name=target_name,
                    target_role=target_role,
                    personality=personality,
                    selected_items=effective_selected,
                    company_context=company_context,
                    company_position=company_position,
                    strategy_note=strategy_note,
                )
            st.session_state[f"eml_result_{ck}"] = result
            st.session_state[f"eml_params_{ck}"] = dict(
                company=r["company"], target_name=target_name, target_role=target_role,
                personality=personality, selected_items=effective_selected,
                company_context=company_context, company_position=company_position,
                strategy_note=strategy_note,
            )
            st.rerun()

    # ── Output ────────────────────────────────────────────────────────────────
    result = st.session_state.get(f"eml_result_{ck}")
    if not result:
        return

    if result.get("error") and not result.get("body"):
        st.error(f"Draft failed: {result['error']}")
        return

    if result.get("length_warning"):
        st.warning(result["length_warning"])

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    hook_title = result.get("hook_title", "")

    # ── Email preview (full width) ────────────────────────────────────────────
    st.markdown(
        "<div style='color:#94a3b8;font-size:0.7rem;text-transform:uppercase;"
        "letter-spacing:0.1em;margin-bottom:12px'>Email Preview</div>",
        unsafe_allow_html=True,
    )

    subject = result.get("subject", "")
    body    = result.get("body", "")
    sender  = st.session_state.get(f"eml_sender_{ck}", "").strip() or "[Sender Name]"
    body    = body.replace("[Sender Name]", sender)

    if not any(w in body.lower() for w in ("best regards", "kind regards", "regards,")):
        body = body.rstrip() + f"\n\nBest regards,\n{sender}"

    full_email_json = json.dumps(f"Subject: {subject}\n\n{body}")

    components.html(f"""
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  .card {{ background:#111827; border:1px solid #1e293b; border-radius:10px; padding:20px 24px; position:relative; max-height:480px; overflow-y:auto; }}
  .copy-btn {{
    position:absolute; top:14px; right:14px;
    background:#00d4aa; color:#050a14; border:none;
    padding:6px 14px; border-radius:6px;
    font-weight:700; cursor:pointer; font-size:0.78rem;
    font-family:inherit;
  }}
  .copy-btn:hover {{ background:#00b894; }}
  .lbl {{ color:#94a3b8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; min-width:64px; }}
  .val {{ color:#f8fafc; font-size:0.875rem; }}
  .meta {{ display:flex; align-items:baseline; gap:10px; margin-bottom:5px; }}
  hr  {{ border:none; border-top:1px solid #1e293b; margin:14px 0; }}
  .subject {{ color:#00d4aa; font-weight:600; font-size:0.95rem; margin-bottom:16px; }}
  .body {{ color:#f8fafc; font-size:0.875rem; line-height:1.8; white-space:pre-wrap; }}
</style>
<div class="card">
  <button class="copy-btn" id="cb" onclick="
    navigator.clipboard.writeText({full_email_json}).then(function(){{
      var b=document.getElementById('cb');
      b.innerHTML='✓ Copied!'; b.style.background='#00b894';
      setTimeout(function(){{ b.innerHTML='&#128203; Copy'; b.style.background='#00d4aa'; }},2000);
    }});
  ">&#128203; Copy</button>

  <div class="meta"><span class="lbl">To</span><span class="val">{target_name or '—'}</span></div>
  <div class="meta"><span class="lbl">Role</span><span class="val">{target_role or '—'}</span></div>
  <div class="meta"><span class="lbl">Company</span><span class="val">{r['company']}</span></div>
  <hr>
  <div class="lbl" style="margin-bottom:4px">Subject</div>
  <div class="subject">{subject}</div>
  <div class="body">{body}</div>
</div>
""", height=520)

    # ── Regenerate / Different Hook ───────────────────────────────────────────
    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
    regen1, regen2, _ = st.columns([1, 1, 2])
    with regen1:
        if st.button("Regenerate", key=f"eml_regen_{ck}", use_container_width=True):
            params = st.session_state.get(f"eml_params_{ck}", {})
            if params:
                from agents.email.agent import EmailDraftAgent
                with st.spinner("Regenerating..."):
                    new_result = EmailDraftAgent().draft(**params)
                st.session_state[f"eml_result_{ck}"] = new_result
                st.rerun()
    with regen2:
        if st.button("Different Hook", key=f"eml_diffhook_{ck}", use_container_width=True):
            params = st.session_state.get(f"eml_params_{ck}", {})
            if params:
                from agents.email.agent import EmailDraftAgent
                with st.spinner("Finding different angle..."):
                    new_result = EmailDraftAgent().draft(
                        **params, avoid_hook=hook_title
                    )
                st.session_state[f"eml_result_{ck}"] = new_result
                st.rerun()
