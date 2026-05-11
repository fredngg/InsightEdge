import streamlit as st
import pandas as pd
from ui.results_store import (
    begin_run,
    finalize_run,
    find_partial_run,
    load_partial_run,
    save_checkpoint,
)
from ui.theme import inject_theme
from agents.discovery.agent import CompanyDiscoveryAgent

inject_theme()

from agents.director import (
    DirectorAgent,
    ROLE_TERRITORY_MANAGER,
    ROLE_VELOCITY,
    AGENT_TECH_STACK,
    AGENT_HIRING,
    AGENT_NEWS,
    AGENT_POSITION,
    AGENT_REGULATORY,
    AGENT_PROFILE,
    AGENT_STAKEHOLDER,
    AGENT_PAIN_POINTS,
    AGENT_ADVISOR,
)

st.markdown("""
<div style="display:flex;align-items:center;gap:14px;margin-bottom:28px">
  <div style="background:#00d4aa;width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
    <span style="color:#050a14;font-weight:900;font-size:1.1rem">S</span>
  </div>
  <div>
    <div style="color:#f8fafc;font-size:1.35rem;font-weight:700;line-height:1.2">Sonar AI Sales Agent</div>
    <div style="color:#94a3b8;font-size:0.8rem">Multi-Role Intelligence Pipeline</div>
  </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.4], gap="large")

with col_left:
    st.subheader("Configuration")

    role = st.radio(
        "SELECT WORKSTREAM",
        options=[ROLE_TERRITORY_MANAGER, ROLE_VELOCITY],
        horizontal=False,
    )

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    st.subheader("Target Accounts")

    df = None
    uploaded_file = None

    # Velocity Mode A inputs (declared here so they're in scope for the run block below)
    vel_countries_input = ""
    vel_industries_input = ""
    vel_count = 20
    vel_mode_a = False

    if role == ROLE_TERRITORY_MANAGER:
        st.caption("Upload a CSV or Excel file with 100–500 target accounts.")
        uploaded_file = st.file_uploader("ACCOUNT LIST (CSV / XLSX)", type=["csv", "xlsx"], key="ent_upload")
        if uploaded_file:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.success(f"{len(df)} accounts loaded.")
            st.dataframe(df.head(5), use_container_width=True)
            # Store ENT accounts for Velocity dedup
            ent_set: set[str] = set()
            for _, row in df.iterrows():
                company = (
                    row.get("company") or row.get("Company")
                    or row.get("Account Name", "")
                )
                if company:
                    ent_set.add(str(company).strip().lower())
                domain = (
                    row.get("domain") or row.get("Domain")
                    or row.get("Website", "")
                )
                if domain:
                    ent_set.add(str(domain).strip().lower())
            st.session_state["ent_company_set"] = ent_set
    else:
        list_option = st.radio(
            "LIST SOURCE",
            options=["Upload my own Velocity list", "Create a list (agent curates from web)"],
            key="vel_source",
        )
        if list_option == "Upload my own Velocity list":
            uploaded_file = st.file_uploader("VELOCITY LIST (CSV / XLSX)", type=["csv", "xlsx"], key="vel_upload")
            if uploaded_file:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                st.success(f"{len(df)} accounts loaded.")
                st.dataframe(df.head(5), use_container_width=True)
        else:
            vel_mode_a = True
            st.caption("Agent will search the web for mid-market companies matching your criteria.")
            st.caption("Separate multiple values with commas.")
            vel_countries_input = st.text_input(
                "COUNTRIES",
                placeholder="e.g. Singapore, Malaysia, Indonesia",
                key="vel_countries",
            )
            vel_industries_input = st.text_input(
                "INDUSTRIES",
                placeholder="e.g. Finance, Healthcare, Technology",
                key="vel_industries",
            )
            vel_count = st.number_input(
                "NUMBER OF ACCOUNTS",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                key="vel_count",
            )

with col_right:
    st.subheader("Intelligence Agents")
    st.caption("Select the signals you wish to extract.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            "<span style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em'>Signal Agents</span>",
            unsafe_allow_html=True,
        )
        run_tech    = st.checkbox("Tech Stack",     value=True, key="cb_tech")
        run_hiring  = st.checkbox("Hiring Signals", value=True, key="cb_hiring")
        run_news    = st.checkbox("Public News",    value=True, key="cb_news")

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<span style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em'>Context Agents</span>",
            unsafe_allow_html=True,
        )
        run_profile = st.checkbox("Company Profile", value=True, key="cb_profile")

    with c2:
        st.markdown(
            "<span style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em'>Synthesis Agents</span>",
            unsafe_allow_html=True,
        )
        run_position = st.checkbox(
            "Company Position",
            value=True,
            key="cb_position",
            help="Requires Tech Stack, Hiring, or News to be meaningful.",
        )
        run_advisor = st.checkbox(
            "Outreach Suggest",
            value=True,
            key="cb_advisor",
            help="Reads all researched signals and recommends the strongest email hook. Always runs last.",
        )

        if role == ROLE_TERRITORY_MANAGER:
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<span style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em'>ENT Only</span>",
                unsafe_allow_html=True,
            )
            run_reg   = st.checkbox("Regulatory Impact",        value=True, key="cb_reg")
            run_stake = st.checkbox("Stakeholder Intelligence", value=True, key="cb_stake",
                                    help="Finds technical leadership and infers personality colour. Slowest agent.")
            run_pain  = False
        else:
            run_reg   = False
            run_stake = False
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<span style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em'>Velocity Only</span>",
                unsafe_allow_html=True,
            )
            run_pain = st.checkbox("Developer Pain Points", value=True, key="cb_pain",
                                   help="Searches public sources for company-linked developer pain signals relevant to Sonar.")

    agents_to_run: set[str] = set()
    if run_tech:     agents_to_run.add(AGENT_TECH_STACK)
    if run_hiring:   agents_to_run.add(AGENT_HIRING)
    if run_news:     agents_to_run.add(AGENT_NEWS)
    if run_profile:  agents_to_run.add(AGENT_PROFILE)
    if run_position: agents_to_run.add(AGENT_POSITION)
    if run_reg:      agents_to_run.add(AGENT_REGULATORY)
    if run_stake:    agents_to_run.add(AGENT_STAKEHOLDER)
    if run_pain:     agents_to_run.add(AGENT_PAIN_POINTS)
    if run_advisor:  agents_to_run.add(AGENT_ADVISOR)

    if not agents_to_run:
        st.warning("Select at least one agent to run.")

    st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)

    mode_a_ready = vel_mode_a and bool(vel_countries_input.strip()) and bool(vel_industries_input.strip())
    run_disabled = (not vel_mode_a and df is None) or (vel_mode_a and not mode_a_ready) or not agents_to_run
    run_button = st.button(
        "EXECUTE RESEARCH PIPELINE",
        type="primary",
        use_container_width=True,
        disabled=run_disabled,
    )

    if run_button and agents_to_run and (df is not None or mode_a_ready):
        agent_labels = {
            AGENT_TECH_STACK:  "Tech Stack",
            AGENT_HIRING:      "Hiring Signals",
            AGENT_NEWS:        "Public News",
            AGENT_POSITION:    "Company Position",
            AGENT_REGULATORY:  "Regulatory Impact",
            AGENT_PROFILE:     "Company Profile",
            AGENT_STAKEHOLDER: "Stakeholder Intelligence",
            AGENT_PAIN_POINTS: "Developer Pain Points",
            AGENT_ADVISOR:     "Outreach Suggest",
        }
        running_names = ", ".join(agent_labels[k] for k in agent_labels if k in agents_to_run)
        st.markdown(f"**Running:** {running_names}")

        progress_bar = st.progress(0)
        status_text  = st.empty()

        # ── Mode A: discover accounts first ──────────────────────────────────
        accounts: list[dict] = []
        src_name = ""

        if vel_mode_a:
            countries = [c.strip() for c in vel_countries_input.split(",") if c.strip()]
            industries = [i.strip() for i in vel_industries_input.split(",") if i.strip()]

            status_text.caption("Discovering candidate companies...")
            discovery_agent = CompanyDiscoveryAgent()
            accounts, disc_limitations = discovery_agent.run(
                countries=countries,
                industries=industries,
                count=int(vel_count),
            )
            if disc_limitations:
                for lim in disc_limitations:
                    st.caption(f"Discovery: {lim}")

            src_name = f"agent_curated_{'+'.join(countries)}_{'+'.join(industries)}"
        else:
            accounts = df.to_dict(orient="records")
            src_name = uploaded_file.name if uploaded_file else "velocity_list"

        # ── ENT dedup (both modes, silently skipped if no ENT list) ──────────
        ent_set: set[str] = st.session_state.get("ent_company_set", set())
        if ent_set:
            before = len(accounts)
            accounts = [
                acc for acc in accounts
                if acc.get("company", "").strip().lower() not in ent_set
                and acc.get("domain", "").strip().lower() not in ent_set
            ]
            removed = before - len(accounts)
            if removed:
                st.caption(f"{removed} ENT account(s) removed from Velocity list.")

        if not accounts:
            st.error("No accounts to analyze after filtering. Adjust your inputs and try again.")
            st.stop()

        def update_progress(current, total, company):
            progress_bar.progress(current / total)
            status_text.caption(f"Analyzing {current}/{total}: {company}")

        director = DirectorAgent(role=role)

        # Resume from a prior interrupted run if one exists for this source
        resume_from: list = []
        partial_path = find_partial_run(role, src_name)
        if partial_path:
            try:
                resume_from, _ = load_partial_run(partial_path)
                if resume_from:
                    st.caption(
                        f"Resuming previous run — {len(resume_from)} account(s) "
                        "already analysed will be skipped."
                    )
            except Exception:
                resume_from = []

        handle = begin_run(role, src_name)

        def checkpoint(_account_result, all_so_far):
            save_checkpoint(handle, all_so_far)

        with st.spinner("Agent pipeline running..."):
            results = director.run(
                accounts,
                progress_callback=update_progress,
                agents_to_run=agents_to_run,
                on_account_complete=checkpoint,
                resume_from=resume_from,
            )

        progress_bar.progress(1.0)
        status_text.caption("Analysis complete.")

        saved_path = finalize_run(handle, results)

        tabs_key = "ent_tabs" if "Territory" in role else "vel_tabs"
        if tabs_key not in st.session_state:
            st.session_state[tabs_key] = []
        st.session_state[tabs_key].append({
            "type":  "run",
            "path":  saved_path,
            "label": src_name,
        })

        if "Territory" in role:
            st.switch_page("ui/ent_accounts.py")
        else:
            st.switch_page("ui/velocity_accounts.py")
