import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Founder Insight Tool", page_icon="🧠", layout="wide")

# ── Sidebar: API key ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password",
                            help="Get yours at aistudio.google.com")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("API key set ✓")
    st.markdown("---")
    st.caption("Built for entrepreneurs who want to prioritize based on real customer evidence.")

# ── Session state ─────────────────────────────────────────────────────────────
if "insights" not in st.session_state:
    st.session_state.insights = None
if "ranked" not in st.session_state:
    st.session_state.ranked = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🧠 Founder Insight & Backlog Prioritizer")
st.markdown(
    "Stop guessing what to build next. Paste your raw customer feedback, "
    "then score your backlog against real evidence."
)
st.markdown("---")

# ── Two columns layout ────────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 – Insight Synthesis
# ═══════════════════════════════════════════════════════════════════════════════
with col1:
    st.header("Step 1 — Insight Synthesis")
    st.markdown(
        "Paste any raw customer feedback: interview notes, emails, "
        "meeting transcripts, chat messages."
    )

    raw_input = st.text_area(
        "Raw customer feedback",
        height=300,
        placeholder=(
            "Example:\n"
            "- User interview 1: 'I spend hours every week manually copying data "
            "from spreadsheets into our reports. It's the most painful part of my job.'\n"
            "- Email from prospect: 'We tried three tools but none of them integrate "
            "with our existing workflow...'\n"
            "- Meeting notes: Customer said prioritization feels random, no clear process."
        ),
    )

    if st.button("🔍 Extract Insights", use_container_width=True, type="primary"):
        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar first.")
        elif not raw_input.strip():
            st.error("Please paste some customer feedback first.")
        else:
            with st.spinner("Analyzing feedback..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""You are an expert in customer discovery and entrepreneurship.
Analyze the following raw customer feedback and extract structured insights.

Return ONLY valid JSON with this exact structure:
{{
  "pain_points": [
    {{"title": "short title", "description": "1-2 sentence description", "frequency": "high/medium/low", "quotes": ["direct quote if available"]}}
  ],
  "recurring_patterns": [
    {{"pattern": "description of recurring theme", "evidence": "which inputs support this"}}
  ],
  "validated_assumptions": [
    {{"assumption": "what this feedback confirms", "confidence": "high/medium/low"}}
  ],
  "opportunity_areas": [
    {{"area": "where AI or a tool could help", "rationale": "why"}}
  ]
}}

Raw feedback to analyze:
{raw_input}

Return only the JSON, no markdown, no explanation."""

                try:
                    response = model.generate_content(prompt)
                    raw_json = response.text.strip()
                    # Strip markdown fences if present
                    if raw_json.startswith("```"):
                        raw_json = raw_json.split("```")[1]
                        if raw_json.startswith("json"):
                            raw_json = raw_json[4:]
                    st.session_state.insights = json.loads(raw_json.strip())
                    st.session_state.ranked = None  # reset step 2
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    # Display insights
    if st.session_state.insights:
        ins = st.session_state.insights
        st.success("Insights extracted!")

        with st.expander("🔴 Pain Points", expanded=True):
            for p in ins.get("pain_points", []):
                badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p.get("frequency", ""), "⚪")
                st.markdown(f"**{badge} {p['title']}** _(frequency: {p.get('frequency','?')})_")
                st.markdown(f"&nbsp;&nbsp;&nbsp;{p['description']}")
                for q in p.get("quotes", []):
                    st.markdown(f"&nbsp;&nbsp;&nbsp;> _{q}_")

        with st.expander("🔁 Recurring Patterns"):
            for p in ins.get("recurring_patterns", []):
                st.markdown(f"**{p['pattern']}**")
                st.caption(p.get("evidence", ""))

        with st.expander("✅ Validated Assumptions"):
            for a in ins.get("validated_assumptions", []):
                conf = a.get("confidence", "?")
                icon = {"high": "✅", "medium": "🟡", "low": "❓"}.get(conf, "⚪")
                st.markdown(f"{icon} {a['assumption']} _(confidence: {conf})_")

        with st.expander("💡 Opportunity Areas"):
            for o in ins.get("opportunity_areas", []):
                st.markdown(f"**{o['area']}**")
                st.caption(o.get("rationale", ""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 – Backlog Prioritization
# ═══════════════════════════════════════════════════════════════════════════════
with col2:
    st.header("Step 2 — Backlog Prioritization")
    st.markdown(
        "Add your backlog items below (one per line). "
        "The AI will score each one against the insights from Step 1."
    )

    backlog_input = st.text_area(
        "Backlog items (one per line)",
        height=300,
        placeholder=(
            "Example:\n"
            "Auto-generate weekly reports from raw data\n"
            "Add dark mode to the dashboard\n"
            "Build Slack integration\n"
            "Create onboarding tutorial video\n"
            "API connection to Google Sheets"
        ),
    )

    disabled = st.session_state.insights is None
    if disabled:
        st.caption("⬅️ Complete Step 1 first to unlock prioritization.")

    if st.button("📊 Score & Prioritize Backlog", use_container_width=True,
                 type="primary", disabled=disabled):
        if not backlog_input.strip():
            st.error("Please enter your backlog items first.")
        else:
            items = [line.strip() for line in backlog_input.strip().splitlines() if line.strip()]
            with st.spinner("Scoring backlog against customer insights..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""You are an expert product strategist helping a founder prioritize their backlog.

Here are the customer insights extracted from real feedback:
{json.dumps(st.session_state.insights, indent=2)}

Here are the backlog items to score:
{json.dumps(items, indent=2)}

Score each backlog item from 1-10 based on how directly it addresses the pain points, 
patterns, and validated assumptions above. 10 = directly solves a high-frequency pain point, 
1 = no clear connection to customer evidence.

Return ONLY valid JSON in this exact structure:
{{
  "ranked_items": [
    {{
      "item": "exact backlog item text",
      "score": 8,
      "rationale": "2-3 sentence explanation of why this score",
      "supporting_evidence": "which specific pain point or pattern supports this",
      "risk": "what could go wrong or what's still unknown"
    }}
  ]
}}

Sort by score descending. Return only the JSON, no markdown, no explanation."""

                try:
                    response = model.generate_content(prompt)
                    raw_json = response.text.strip()
                    if raw_json.startswith("```"):
                        raw_json = raw_json.split("```")[1]
                        if raw_json.startswith("json"):
                            raw_json = raw_json[4:]
                    st.session_state.ranked = json.loads(raw_json.strip())
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    # Display ranked backlog
    if st.session_state.ranked:
        st.success("Backlog scored!")
        items_list = st.session_state.ranked.get("ranked_items", [])

        for i, item in enumerate(items_list):
            score = item.get("score", 0)
            color = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"
            with st.expander(f"{color} #{i+1} — {item['item']}  ·  Score: **{score}/10**", expanded=(i == 0)):
                st.markdown(f"**Rationale:** {item.get('rationale', '')}")
                st.markdown(f"**Supporting evidence:** {item.get('supporting_evidence', '')}")
                st.markdown(f"**Risk / unknowns:** {item.get('risk', '')}")

        # Download button
        export = "\n".join(
            [f"#{i+1} [{r['score']}/10] {r['item']}\n  → {r['rationale']}\n"
             for i, r in enumerate(items_list)]
        )
        st.download_button(
            "⬇️ Export ranked list as .txt",
            data=export,
            file_name="prioritized_backlog.txt",
            mime="text/plain",
            use_container_width=True,
        )
