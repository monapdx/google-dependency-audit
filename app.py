import streamlit as st
import pandas as pd
import os

# ----------------------------
# Page
# ----------------------------
st.set_page_config(page_title="Google Dependency Audit", page_icon="🧭", layout="wide")
st.title("Google Dependency Audit")
st.caption("A structural audit of how centralized your digital life is around a Google account.")

# ----------------------------
# Helpers
# ----------------------------
LEVELS_ID_15 = [
    ("Low", 0, 3),
    ("Moderate", 4, 7),
    ("High", 8, 10),
    ("Very High", 11, 15),
]

LEVELS_12 = [
    ("Low", 0, 3),
    ("Moderate", 4, 7),
    ("High", 8, 10),
    ("Very High", 11, 12),
]


def level_for(score: int, max_score: int) -> str:
    levels = LEVELS_ID_15 if max_score == 15 else LEVELS_12
    for name, lo, hi in levels:
        if lo <= score <= hi:
            return name
    return levels[-1][0]


def meter(label: str, score: int, max_score: int):
    pct = int((score / max_score) * 100) if max_score else 0
    st.write(f"**{label}** — {level_for(score, max_score)} ({score}/{max_score})")
    st.progress(pct)


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def unanswered_keys(required_keys: list[str]) -> list[str]:
    return [k for k in required_keys if st.session_state.get(k) is None]


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "audit"  # "audit" | "results"
    if "submitted" not in st.session_state:
        st.session_state.submitted = False


init_state()

# ----------------------------
# Required question keys (gate Results)
# ----------------------------
REQUIRED_KEYS = [
    "id_q1", "id_q2", "id_q3", "id_q4", "id_q5",
    "ar_q1", "ar_q2", "ar_q3", "ar_q4",
    "wf_q1", "wf_q2", "wf_q3", "wf_q4",
    "re_q1", "re_q2", "re_q3", "re_q4",
]

# ----------------------------
# Common: compute scores from current answers
# ----------------------------
def compute_scores():
    # Identity
    q1 = st.session_state.get("id_q1")
    q2 = st.session_state.get("id_q2")
    q3 = st.session_state.get("id_q3")
    q4 = st.session_state.get("id_q4")
    q5 = st.session_state.get("id_q5")

    id_q1 = {"Yes, for almost everything": 3, "Yes, but I also actively use another email": 2, "No": 0}.get(q1, 0)
    id_q2 = {"Yes, for most": 3, "For some": 2, "No": 0, "I'm not sure": 3}.get(q2, 0)
    id_q3 = {"Yes, frequently": 3, "Occasionally": 2, "Rarely": 1, "Never": 0, "I don't know": 3}.get(q3, 0)
    id_q4 = {"Yes": 3, "Possibly": 2, "No": 0, "I'm not sure": 3}.get(q4, 0)
    id_q5 = {"Yes, for years and across many services": 3, "Yes, for some important services": 2, "No": 0, "I'm not sure": 2}.get(q5, 0)

    identity_score = id_q1 + id_q2 + id_q3 + id_q4 + id_q5
    identity_max = 15

    # Archive
    a1 = st.session_state.get("ar_q1")
    a2 = st.session_state.get("ar_q2")
    a3 = st.session_state.get("ar_q3")
    a4 = st.session_state.get("ar_q4")

    ar_q1 = {"Yes, almost all": 3, "Yes, but I also store copies elsewhere": 2, "Some": 1, "No": 0}.get(a1, 0)
    ar_q2 = {"Yes, exclusively": 3, "Yes, but I maintain backups": 2, "Some": 1, "No": 0}.get(a2, 0)
    ar_q3 = {"Extremely important": 3, "Somewhat important": 2, "Not very important": 1, "Not important": 0}.get(a3, 0)
    # Reverse-scored (backups reduce concentration/exposure)
    ar_q4 = {"Yes, regularly": 0, "Yes, occasionally": 1, "No": 3, "I'm not sure": 2}.get(a4, 0)

    archive_score = ar_q1 + ar_q2 + ar_q3 + ar_q4
    archive_max = 12

    # Workflow
    w1 = st.session_state.get("wf_q1")
    w2 = st.session_state.get("wf_q2")
    w3 = st.session_state.get("wf_q3")
    w4 = st.session_state.get("wf_q4")

    wf_q1 = {"Yes": 3, "Partially": 2, "No": 0}.get(w1, 0)
    wf_q2 = {"Yes, extensively": 3, "Occasionally": 2, "Rarely": 1, "Never": 0}.get(w2, 0)
    wf_q3 = {"Yes": 3, "Somewhat": 2, "No": 0}.get(w3, 0)
    wf_q4 = {"Yes": 3, "Some disruption": 2, "Minimal disruption": 1, "No": 0}.get(w4, 0)

    workflow_score = wf_q1 + wf_q2 + wf_q3 + wf_q4
    workflow_max = 12

    # Resilience exposure (higher = less resilient)
    r1 = st.session_state.get("re_q1")
    r2 = st.session_state.get("re_q2")
    r3 = st.session_state.get("re_q3")
    r4 = st.session_state.get("re_q4")

    re_q1 = {"Yes, regularly": 0, "Yes, but rarely": 1, "No": 3}.get(r1, 0)
    re_q2 = {"Yes, comprehensive backups": 0, "Partial backups": 1, "No": 3, "I'm not sure": 2}.get(r2, 0)
    re_q3 = {"Yes": 0, "More than a year ago": 1, "Never": 3, "I'm not sure what that is": 2}.get(r3, 0)
    re_q4 = {"Yes": 0, "No": 2, "I'm not sure": 1}.get(r4, 0)

    resilience_exposure = re_q1 + re_q2 + re_q3 + re_q4
    redundancy_strength = 12 - resilience_exposure

    # Composite (same as before)
    risk_total = identity_score + archive_score + workflow_score
    resilience_benefit = 12 - resilience_exposure
    capped_benefit = min(resilience_benefit, int(risk_total * 0.5))  # cap at 50% mitigation
    lock_in_index = clamp(risk_total - capped_benefit, 0, 39)

    return {
        "identity_score": identity_score,
        "identity_max": identity_max,
        "archive_score": archive_score,
        "archive_max": archive_max,
        "workflow_score": workflow_score,
        "workflow_max": workflow_max,
        "resilience_exposure": resilience_exposure,
        "redundancy_strength": redundancy_strength,
        "lock_in_index": lock_in_index,
    }


scores = compute_scores()

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.markdown("## Research")
    show_research = st.checkbox(
        "Ecosystem Login Adoption Research",
        value=False,
        help="Show a research panel that estimates how often high-traffic domains offer Sign in with Google (public-page detection only).",
    )

# ----------------------------
# Layout
# ----------------------------
left, right = st.columns([1.35, 1])

# ----------------------------
# AUDIT PAGE
# ----------------------------
if st.session_state.page == "audit":
    with left:
        st.subheader("Audit")
        st.caption("Note: When uncertainty is selected, exposure is scored conservatively.")

        st.markdown("### 1) Identity Centralization")

        st.radio(
            "Is your Gmail address your primary email address?",
            ["Yes, for almost everything", "Yes, but I also actively use another email", "No"],
            index=None,
            key="id_q1",
        )

        st.radio(
            "Is this Gmail account used as the password reset email for most of your important accounts?",
            ["Yes, for most", "For some", "No", "I'm not sure"],
            index=None,
            key="id_q2",
            help=(
                "How to check quickly:\n"
                "- Think of your top 10 accounts (banking, phone, utilities, domain registrar, creator platforms, "
                "shopping, identity/credit, etc.)\n"
                "- Check each account’s “email / recovery” settings.\n\n"
                "If you’re not sure, assume this is a risk: uncertainty often means the Gmail account is a central reset node."
            ),
        )

        st.radio(
            "Do you use “Sign in with Google” for high-impact services?",
            ["Yes, frequently", "Occasionally", "Rarely", "Never", "I don't know"],
            index=None,
            key="id_q3",
            help=(
                "High-impact examples include:\n"
                "- Banking or financial apps\n"
                "- Subscription services\n"
                "- Work or creator platforms\n"
                "- Domain registrars\n\n"
                "Check your connected services here:\n"
                "https://myaccount.google.com/connections\n\n"
                "If you see 10+ apps listed and don't recognize them all, dependency is likely high."
            ),
        )
        st.caption("Optional: check your connected services here → https://myaccount.google.com/connections")

        st.radio(
            "If your Google account were inaccessible tomorrow, would you immediately lose access to services that are difficult to recreate?",
            ["Yes", "Possibly", "No", "I'm not sure"],
            index=None,
            key="id_q4",
            help=(
                "“Difficult to recreate” examples:\n"
                "- Accounts that rely on Gmail for login + reset\n"
                "- OAuth-based accounts (Sign in with Google)\n"
                "- Accounts protected by Google Voice / Google Authenticator\n"
                "- Long-term archives (email history, photos)\n\n"
                "If you haven’t tested recovery on a few key accounts recently, it’s normal to be unsure."
            ),
        )

        st.radio(
            "Have you used Google Voice as your primary long-term phone number for account verification or important contact?",
            ["Yes, for years and across many services", "Yes, for some important services", "No", "I'm not sure"],
            index=None,
            key="id_q5",
            help=(
                "How to check:\n"
                "- Review your account recovery and 2FA phone numbers for key services.\n"
                "- If many accounts list a Google Voice number (instead of your carrier number), that’s a dependency.\n\n"
                "Tip: Search your password manager for the Voice number, if you store it in notes."
            ),
        )

        st.markdown("### 2) Archive Concentration")

        st.radio(
            "Are your primary documents stored in Google Drive?",
            ["Yes, almost all", "Yes, but I also store copies elsewhere", "Some", "No"],
            index=None,
            key="ar_q1",
            help=(
                "This refers to the *source of truth*.\n\n"
                "If your important docs live primarily in Drive and you’d feel pain losing them, select a higher option. "
                "If Drive is just a convenience layer and you keep local copies, select lower."
            ),
        )

        st.radio(
            "Are your photos primarily stored in Google Photos?",
            ["Yes, exclusively", "Yes, but I maintain backups", "Some", "No"],
            index=None,
            key="ar_q2",
            help=(
                "Backups mean: photos exist somewhere outside Google (local drive, external drive, another provider) "
                "and are accessible without logging into Google."
            ),
        )

        st.radio(
            "Is your Gmail archive important to your personal or professional history?",
            ["Extremely important", "Somewhat important", "Not very important", "Not important"],
            index=None,
            key="ar_q3",
            help=(
                "If you rely on your inbox for receipts, legal/paperwork trails, work history, important relationships, "
                "or long-term memory, your Gmail archive is structurally significant."
            ),
        )

        st.radio(
            "Do you maintain complete backups of your Google data outside of Google?",
            ["Yes, regularly", "Yes, occasionally", "No", "I'm not sure"],
            index=None,
            key="ar_q4",
            help=(
                "A true backup means:\n"
                "- Data exists on a local drive or offline storage\n"
                "- It is accessible without logging into Google\n"
                "- It is updated at least yearly (or on a schedule you can repeat)\n\n"
                "If your only copy is inside Google, that is NOT a backup."
            ),
        )

        st.markdown("### 3) Workflow Reliance")

        st.radio(
            "Is Google Calendar your primary scheduling system?",
            ["Yes", "Partially", "No"],
            index=None,
            key="wf_q1",
            help=(
                "If most of your scheduling truth lives in Google Calendar (appointments, reminders, recurring events), "
                "select Yes. If it’s mirrored elsewhere or you use another calendar in parallel, choose Partially."
            ),
        )

        st.radio(
            "Do you use Google Docs / Sheets / Workspace for professional or collaborative work?",
            ["Yes, extensively", "Occasionally", "Rarely", "Never"],
            index=None,
            key="wf_q2",
            help=(
                "This includes any work where Google is the collaboration layer: shared docs, sheets, folders, permissions, "
                "comments, version history, etc."
            ),
        )

        st.radio(
            "Do you rely on Google services for active projects or business operations?",
            ["Yes", "Somewhat", "No"],
            index=None,
            key="wf_q3",
            help=(
                "Examples: Drive-based project files, Gmail as a business inbox, Calendar for operations, YouTube/Ads, "
                "Sheets for tracking, etc."
            ),
        )

        st.radio(
            "If access to Google services were lost for 7 days, would it significantly disrupt your work or routines?",
            ["Yes", "Some disruption", "Minimal disruption", "No"],
            index=None,
            key="wf_q4",
            help=(
                "Consider what happens if you lose access to Gmail, Drive, Docs/Sheets, Calendar, Photos, YouTube—"
                "not permanently, but for a week."
            ),
        )

        st.markdown("### 4) Resilience / Redundancy")

        st.radio(
            "Do you actively use a secondary non-Google email provider?",
            ["Yes, regularly", "Yes, but rarely", "No"],
            index=None,
            key="re_q1",
            help=(
                "This should be an email you can access independently (Proton, Outlook, iCloud, custom domain, etc.) "
                "and that is actually used—not just created and forgotten."
            ),
        )

        st.radio(
            "Do you maintain local backups of important Google Drive or Photos data?",
            ["Yes, comprehensive backups", "Partial backups", "No", "I'm not sure"],
            index=None,
            key="re_q2",
            help=(
                "“Local backup” means copies exist on your computer or external storage.\n\n"
                "If the only place your files/photos exist is online inside Google, select No."
            ),
        )

        st.radio(
            "Have you exported your data using Google Takeout within the past year?",
            ["Yes", "More than a year ago", "Never", "I'm not sure what that is"],
            index=None,
            key="re_q3",
            help=(
                "Google Takeout lets you export Gmail, Drive, Photos, Calendar, and more.\n\n"
                "If you've never exported your data, you likely do not know your total data volume or whether your exports are usable.\n\n"
                "Start here: https://takeout.google.com/"
            ),
        )

        st.radio(
            "Do you use a custom domain email (not tied to Gmail infrastructure)?",
            ["Yes", "No", "I'm not sure"],
            index=None,
            key="re_q4",
            help=(
                "Custom domain email means you own the domain (e.g., you@yourdomain.com) and can move providers "
                "without changing your address. This can reduce long-term lock-in."
            ),
        )

        # Submit / Navigate
        st.divider()
        missing = unanswered_keys(REQUIRED_KEYS)

        col_a, col_b = st.columns([1, 1])

        with col_a:
            if st.button("Submit & View Results", type="primary"):
                if missing:
                    st.warning(f"Please answer all questions before continuing. ({len(missing)} unanswered)")
                else:
                    st.session_state.submitted = True
                    st.session_state.page = "results"
                    st.rerun()

        with col_b:
            if st.button("Reset All Answers"):
                # Clear just the questionnaire keys (and any extras you want)
                keys_to_clear = REQUIRED_KEYS + ["takeout_size_gb", "page", "submitted"]
                for k in keys_to_clear:
                    if k in st.session_state:
                        del st.session_state[k]
                init_state()
                st.rerun()

    with right:
        st.subheader("Live Meters")

        missing = unanswered_keys(REQUIRED_KEYS)
        if missing:
            st.caption(f"Status: **Incomplete** — {len(missing)} unanswered (meters update as you answer).")
        else:
            st.caption("Status: **Complete** — ready to submit.")

        meter("Identity Centralization", scores["identity_score"], scores["identity_max"])
        meter("Archive Concentration", scores["archive_score"], scores["archive_max"])
        meter("Workflow Reliance", scores["workflow_score"], scores["workflow_max"])

        st.write(f"**Resilience / Redundancy** — {level_for(scores['redundancy_strength'], 12)} ({scores['redundancy_strength']}/12)")
        st.progress(int((scores["redundancy_strength"] / 12) * 100))

        st.divider()
        st.subheader("Lock-In Index")
        st.caption("Composite is intentionally hidden until you submit.")

# ----------------------------
# RESULTS PAGE
# ----------------------------
else:
    # Guard: if someone lands here without completion, send back
    missing = unanswered_keys(REQUIRED_KEYS)
    if missing:
        st.warning("Results require completing the audit. Redirecting you back to the questionnaire…")
        st.session_state.page = "audit"
        st.rerun()

    # Top navigation
    nav_l, nav_r = st.columns([1, 1])
    with nav_l:
        if st.button("← Back to Questionnaire"):
            st.session_state.page = "audit"
            st.rerun()
    with nav_r:
        if st.button("Start Over (Clear Answers)"):
            keys_to_clear = REQUIRED_KEYS + ["takeout_size_gb", "page", "submitted"]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]
            init_state()
            st.rerun()

    st.divider()
    st.header("Results")

    # Collapsible guidance sections live on Results page now
    with st.expander("Helpful links (optional)", expanded=False):
        st.markdown(
            "- Connected third-party apps & services (Sign in with Google / access grants): "
            "https://myaccount.google.com/connections\n"
            "- Security overview: https://myaccount.google.com/security\n"
            "- Google Takeout (export your data): https://takeout.google.com/"
        )
        st.caption(
            "Tip: The connections page can be long. You can use your browser Find (Ctrl+F) to scan for big services."
        )

    with st.expander("How to Find Accurate Answers (Step-by-Step)", expanded=False):
        st.markdown(
            """
### 1) Review Connected Apps (OAuth / “Sign in with Google”)

Go to:
https://myaccount.google.com/connections

- Scroll through **“Third-party apps & services.”**
- Look for high-impact services: financial tools, creator platforms, subscriptions, work software.
- If you see **many services** and don’t recognize them all, your dependency is probably higher than you think.

---

### 2) Review Account Security & Recovery

Go to:
https://myaccount.google.com/security

Check:
- Recovery email
- Recovery phone
- 2-step verification methods
- Devices signed in

Ask yourself:
If this account were locked, how hard would recovery be?

---

### 3) Export Your Data (Google Takeout)

Google Takeout:
https://takeout.google.com/

**Suggested export steps:**
1. Click **“Deselect all.”**
2. Select only key services (Gmail, Drive, Photos, Calendar).
3. Click **“Next step.”**
4. Choose:
   - File type: **.zip**
   - File size: **2GB or 4GB**
   - Delivery method: **Send download link via email**
5. Click **“Create export.”**

When it finishes:
- Download the archive(s).
- Note the **total size** (this reveals your “archive gravity”).
- Store the export somewhere **outside Google** (local drive, external drive, etc.)

If you’ve never done this → your redundancy is likely low.
"""
        )

    with st.expander("Selective Backup Strategy (Recommended)", expanded=False):
        st.markdown(
            """
This is a **high-leverage approach**: instead of exporting *everything*, you deliberately organize and preserve the parts
of your Google account that matter most.

A selective strategy is not a replacement for Takeout — it’s a **practical backup layer** that is faster to execute and easier to maintain.

---

## A) Google Photos: Album-Based “Most Valuable” Backup

If your Photos library is massive, Takeout can be heavy and messy. A lighter strategy:

1. In Google Photos, create a few meaningful albums.
2. Add only your **most valuable / irreplaceable** photos to those albums.
3. On desktop, open an album → use **Download all** (downloads a .zip for that album).
4. Store the downloaded album zips somewhere outside Google (external drive, local archive folder, etc.).
5. Repeat on a schedule (monthly/quarterly/yearly).

**Album ideas:**
- “Family / People I Care About”
- “My Dog / Loki”
- “Identity & Documents” (IDs, medical, insurance, important paperwork photos)
- “Work / Portfolio”
- “Sentimental / Core Memories”
- “Receipts / Purchases”

Why this works:
- You don’t need to export 100% of a library to materially reduce risk.
- If albums already exist, updating and re-downloading is quick.
- A few curated albums can preserve the *meaningful* history even if you never run a full Takeout.

---

## B) Drive: “Vault” Folder + Offline Mirror

Create a single folder in Drive called something like:
**Drive Vault** / **Archive Vault** / **Critical**

Then:
- Move or copy your most important docs into that folder.
- Periodically download the folder to local storage.
- Optional: keep a second copy on an external drive.

---

## C) Gmail: Labels as an Export Plan (Optional)

If Gmail is huge:
- Create labels like: **Receipts**, **Legal**, **Medical**, **Taxes**, **Identity**, **Work**, **Important People**
- Label emails over time (or use filters).
- Later, you can export and store key categories (even if you never export the entire inbox).

Note: Takeout still exports the full mailbox, but labeling helps you *organize value* before exporting.

---

## The principle

**Don’t “backup everything” as a fantasy. Backup the irreplaceable as a reality.**
"""
        )

    with st.expander("Optional: Archive Gravity Check (Advanced)", expanded=False):
        st.caption(
            "If you’ve generated a Google Takeout export, you can record the approximate total size here. "
            "This does not affect your score yet—it's just a visibility tool."
        )
        st.number_input(
            "Approximate total size of your latest Google Takeout export (GB)",
            min_value=0.0,
            step=1.0,
            value=float(st.session_state.get("takeout_size_gb", 0.0) or 0.0),
            help="After Takeout finishes, the downloaded .zip parts (or folder) will have a total size. Enter that rough number here.",
            key="takeout_size_gb",
        )

    # Results content
    id_level = level_for(scores["identity_score"], scores["identity_max"])
    ar_level = level_for(scores["archive_score"], scores["archive_max"])
    wf_level = level_for(scores["workflow_score"], scores["workflow_max"])
    rd_level = level_for(scores["redundancy_strength"], 12)

    lock_in_index = scores["lock_in_index"]
    if lock_in_index <= 10:
        overall = "Low"
    elif lock_in_index <= 20:
        overall = "Moderate"
    elif lock_in_index <= 30:
        overall = "Elevated"
    else:
        overall = "High"

    st.markdown("## Google Dependency Profile")
    st.write(
        "This audit evaluates how structurally centralized your digital identity and data are around a single Google account. "
        "It does not measure trust or privacy posture. It measures infrastructure concentration."
    )

    st.markdown("### 🔎 Dimension Breakdown")

    st.markdown(f"**Identity Centralization — {id_level}**")
    st.write(
        "Your Google account functions as a primary identity authority. "
        "This can include email, password resets, OAuth login, and phone verification (e.g., Google Voice)."
    )

    st.markdown(f"**Archive Concentration — {ar_level}**")
    st.write(
        "A significant portion of your documents, photos, or email history resides within Google systems. "
        "Recovery depends on exports and active backups."
    )

    st.markdown(f"**Workflow Reliance — {wf_level}**")
    st.write(
        "Some daily operations are connected to Google services. A temporary loss of access can affect scheduling, "
        "collaboration, and project continuity."
    )

    st.markdown(f"**Resilience / Redundancy — {rd_level}**")
    st.write(
        "Resilience reflects whether alternate pathways exist (secondary email, exports, backups, portability). "
        "Higher resilience reduces single-point exposure."
    )

    st.markdown("### 🧮 Lock-In Index")
    st.write(f"**Overall Centralization Level: {overall}**")
    st.caption(
        f"Lock-In Index: {lock_in_index} "
        f"(identity + archive + workflow, mitigated by resilience; mitigation capped)."
    )

    st.markdown("### Structural Observations")
    bullets = []
    if scores["identity_score"] >= 10:
        bullets.append("Google operates as a master identity node (email / resets / OAuth / phone verification).")
    if scores["archive_score"] >= 8:
        bullets.append("Archive gravity is high relative to redundancy.")
    if scores["workflow_score"] >= 8:
        bullets.append("Operational reliance on Google is significant.")
    if scores["redundancy_strength"] <= 4:
        bullets.append("Alternate recovery pathways appear limited.")
    if not bullets:
        bullets.append("No single dimension dominates strongly; centralization appears distributed or mitigated.")
    for b in bullets:
        st.write(f"- {b}")

    st.markdown("### Strategic Mitigation Options")
    st.write("Reducing centralization does not require abandoning Google. Structural shifts can be incremental:")
    st.write("- Establish a secondary non-Google email for account recovery.")
    st.write("- Reduce OAuth reliance for high-impact services.")
    st.write("- Export and locally store critical Drive and Photos data.")
    st.write("- Use a selective backup strategy (albums / vault folders) to preserve the irreplaceable fast.")
    st.write("- Maintain periodic Google Takeout exports.")

    st.info("This report is a snapshot of your current configuration. It’s designed to make structure visible.")

# ----------------------------
# RESEARCH PANEL (optional)
# ----------------------------
if "show_research" in globals() and show_research:
    st.divider()
    st.header("🌍 Consumer Google Login Adoption (Research Panel)")
    st.markdown(
        "This panel analyzes a domain sample and detects whether public login surfaces appear to offer **Sign in with Google**. "
        "It does **not** attempt authentication or collect user data."
    )

    default_path = os.path.join("assets", "research", "google_login_results.csv")
    uploaded = st.file_uploader("Upload google_login_results.csv (optional)", type=["csv"], key="research_upload")

    if uploaded is not None:
        df = pd.read_csv(uploaded)
    elif os.path.exists(default_path):
        df = pd.read_csv(default_path)
    else:
        st.info(
            "To use this panel, run the detector script and save the output as `assets/research/google_login_results.csv`, "
            "or upload the CSV here.

"
            "Expected columns: `domain`, `google_login_detected` (optional: `apple_login_detected`, `facebook_login_detected`, `evidence_url`)."
        )
        st.stop()

    def _count_true(series: pd.Series) -> int:
        if series is None:
            return 0
        s = series.astype(str).str.strip().str.lower()
        return int(s.isin(["true", "1", "yes", "y", "t"]).sum())

    total = len(df)
    google_yes = _count_true(df.get("google_login_detected"))
    apple_yes = _count_true(df.get("apple_login_detected"))
    facebook_yes = _count_true(df.get("facebook_login_detected"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Domains Scanned", f"{total:,}")
    c2.metric("Google Login Adoption", f"{(google_yes / total * 100):.1f}%" if total else "—")
    c3.metric("Apple Login Adoption", f"{(apple_yes / total * 100):.1f}%" if total else "—")

    st.subheader("Provider comparison")
    provider_df = pd.DataFrame(
        {
            "Provider": ["Google", "Apple", "Facebook"],
            "Adoption %": [
                (google_yes / total * 100) if total else 0,
                (apple_yes / total * 100) if total else 0,
                (facebook_yes / total * 100) if total else 0,
            ],
        }
    )
    st.bar_chart(provider_df.set_index("Provider"))

    st.subheader("Raw results")
    st.dataframe(df, use_container_width=True)
