<script>
  import { fly, fade } from "svelte/transition";

  const STORAGE_KEY = "gda_v2";

  const STEP_TITLES = ["Identity", "Archive", "Workflow", "Resilience"];

  const STEPS = [
    {
      title: "Identity Centralization",
      subtitle: "Note: “I’m not sure” is scored conservatively.",
      questions: [
        {
          key: "id_q1",
          label: "Is your Gmail address your primary email address?",
          options: ["Yes, for almost everything", "Yes, but I also actively use another email", "No"]
        },
        {
          key: "id_q2",
          label: "Is this Gmail used as the password reset email for most of your important accounts?",
          options: ["Yes, for most", "For some", "No", "I'm not sure"],
          help:
`How to check quickly:
- Think of your top 10 accounts (banking, phone, utilities, domain registrar, creator platforms, shopping, identity/credit, etc.)
- Check each account’s “email / recovery” settings.

If you’re not sure, assume this is a risk: uncertainty often means the Gmail account is a central reset node.`
        },
        {
          key: "id_q3",
          label: "Do you use “Sign in with Google” for high-impact services?",
          options: ["Yes, frequently", "Occasionally", "Rarely", "Never", "I don't know"],
          help:
`Connected services:
https://myaccount.google.com/connections`
        },
        {
          key: "id_q4",
          label: "If your Google account were inaccessible tomorrow, would you lose access to services that are difficult to recreate?",
          options: ["Yes", "Possibly", "No", "I'm not sure"]
        },
        {
          key: "id_q5",
          label: "Have you used Google Voice as your primary long-term verification number for important services?",
          options: ["Yes, for years and across many services", "Yes, for some important services", "No", "I'm not sure"]
        }
      ]
    },
    {
      title: "Archive Concentration",
      questions: [
        {
          key: "ar_q1",
          label: "Are your primary documents stored in Google Drive?",
          options: ["Yes, almost all", "Yes, but I also store copies elsewhere", "Some", "No"]
        },
        {
          key: "ar_q2",
          label: "Are your photos primarily stored in Google Photos?",
          options: ["Yes, exclusively", "Yes, but I maintain backups", "Some", "No"]
        },
        {
          key: "ar_q3",
          label: "Is your Gmail archive important to your personal or professional history?",
          options: ["Extremely important", "Somewhat important", "Not very important", "Not important"]
        },
        {
          key: "ar_q4",
          label: "Do you maintain complete backups of your Google data outside of Google?",
          options: ["Yes, regularly", "Yes, occasionally", "No", "I'm not sure"],
          help:
`A true backup means:
- Data exists on local/offline storage
- It is accessible without logging into Google
- It is updated on a schedule you can repeat`
        }
      ]
    },
    {
      title: "Workflow Reliance",
      questions: [
        { key: "wf_q1", label: "Is Google Calendar your primary scheduling system?", options: ["Yes", "Partially", "No"] },
        {
          key: "wf_q2",
          label: "Do you use Google Docs / Sheets / Workspace for professional or collaborative work?",
          options: ["Yes, extensively", "Occasionally", "Rarely", "Never"]
        },
        { key: "wf_q3", label: "Do you rely on Google services for active projects or business operations?", options: ["Yes", "Somewhat", "No"] },
        {
          key: "wf_q4",
          label: "If access to Google services were lost for 7 days, would it significantly disrupt your work or routines?",
          options: ["Yes", "Some disruption", "Minimal disruption", "No"]
        }
      ]
    },
    {
      title: "Resilience / Redundancy",
      questions: [
        { key: "re_q1", label: "Do you actively use a secondary non-Google email provider?", options: ["Yes, regularly", "Yes, but rarely", "No"] },
        {
          key: "re_q2",
          label: "Do you maintain local backups of important Google Drive or Photos data?",
          options: ["Yes, comprehensive backups", "Partial backups", "No", "I'm not sure"]
        },
        {
          key: "re_q3",
          label: "Have you exported your data using Google Takeout within the past year?",
          options: ["Yes", "More than a year ago", "Never", "I'm not sure what that is"]
        },
        { key: "re_q4", label: "Do you use a custom domain email (not tied to Gmail infrastructure)?", options: ["Yes", "No", "I'm not sure"] }
      ]
    }
  ];

  const REQUIRED_KEYS = STEPS.flatMap(s => s.questions.map(q => q.key));
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  let step = 0;
  let view = "audit"; // "audit" | "results"
  let answers = Object.fromEntries(REQUIRED_KEYS.map(k => [k, ""]));

  // ---------- persistence ----------
  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      step = Number.isFinite(parsed.step) ? clamp(parsed.step, 0, 3) : 0;
      view = parsed.view === "results" ? "results" : "audit";
      answers = { ...answers, ...(parsed.answers ?? {}) };
    } catch {
      // ignore
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ step, view, answers }));
    } catch {
      // ignore
    }
  }

  loadState();
  $: saveState();

  function setAnswer(k, v) {
    answers = { ...answers, [k]: v };
  }

  // ---------- missing ----------
  function missing(keys) {
    return keys.filter(k => !answers[k]);
  }
  function stepKeys(i) {
    return STEPS[i].questions.map(q => q.key);
  }
  $: missingHere = missing(stepKeys(step));
  $: missingAll = missing(REQUIRED_KEYS);
  $: completedByStep = STEPS.map((_, i) => missing(stepKeys(i)).length === 0);
  $: missingCounts = STEPS.map((_, i) => missing(stepKeys(i)).length);

  // ---------- scoring ----------
  function levelFor(score, max) {
    const levels =
      max === 15
        ? [["Low",0,3],["Moderate",4,7],["High",8,10],["Very High",11,15]]
        : [["Low",0,3],["Moderate",4,7],["High",8,10],["Very High",11,12]];
    for (const [name, lo, hi] of levels) {
      if (score >= lo && score <= hi) return name;
    }
    return levels[levels.length - 1][0];
  }

  function computeScores(a) {
    // Identity (max 15)
    const id_q1 = ({ "Yes, for almost everything":3, "Yes, but I also actively use another email":2, "No":0 })[a.id_q1] ?? 0;
    const id_q2 = ({ "Yes, for most":3, "For some":2, "No":0, "I'm not sure":3 })[a.id_q2] ?? 0;
    const id_q3 = ({ "Yes, frequently":3, "Occasionally":2, "Rarely":1, "Never":0, "I don't know":3 })[a.id_q3] ?? 0;
    const id_q4 = ({ "Yes":3, "Possibly":2, "No":0, "I'm not sure":3 })[a.id_q4] ?? 0;
    const id_q5 = ({ "Yes, for years and across many services":3, "Yes, for some important services":2, "No":0, "I'm not sure":2 })[a.id_q5] ?? 0;

    const identity_score = id_q1 + id_q2 + id_q3 + id_q4 + id_q5;

    // Archive (max 12)
    const ar_q1 = ({ "Yes, almost all":3, "Yes, but I also store copies elsewhere":2, "Some":1, "No":0 })[a.ar_q1] ?? 0;
    const ar_q2 = ({ "Yes, exclusively":3, "Yes, but I maintain backups":2, "Some":1, "No":0 })[a.ar_q2] ?? 0;
    const ar_q3 = ({ "Extremely important":3, "Somewhat important":2, "Not very important":1, "Not important":0 })[a.ar_q3] ?? 0;
    const ar_q4 = ({ "Yes, regularly":0, "Yes, occasionally":1, "No":3, "I'm not sure":2 })[a.ar_q4] ?? 0;

    const archive_score = ar_q1 + ar_q2 + ar_q3 + ar_q4;

    // Workflow (max 12)
    const wf_q1 = ({ "Yes":3, "Partially":2, "No":0 })[a.wf_q1] ?? 0;
    const wf_q2 = ({ "Yes, extensively":3, "Occasionally":2, "Rarely":1, "Never":0 })[a.wf_q2] ?? 0;
    const wf_q3 = ({ "Yes":3, "Somewhat":2, "No":0 })[a.wf_q3] ?? 0;
    const wf_q4 = ({ "Yes":3, "Some disruption":2, "Minimal disruption":1, "No":0 })[a.wf_q4] ?? 0;

    const workflow_score = wf_q1 + wf_q2 + wf_q3 + wf_q4;

    // Resilience exposure (max 12; higher = worse)
    const re_q1 = ({ "Yes, regularly":0, "Yes, but rarely":1, "No":3 })[a.re_q1] ?? 0;
    const re_q2 = ({ "Yes, comprehensive backups":0, "Partial backups":1, "No":3, "I'm not sure":2 })[a.re_q2] ?? 0;
    const re_q3 = ({ "Yes":0, "More than a year ago":1, "Never":3, "I'm not sure what that is":2 })[a.re_q3] ?? 0;
    const re_q4 = ({ "Yes":0, "No":2, "I'm not sure":1 })[a.re_q4] ?? 0;

    const resilience_exposure = re_q1 + re_q2 + re_q3 + re_q4;
    const redundancy_strength = 12 - resilience_exposure;

    // Composite + mitigation cap
    const risk_total = identity_score + archive_score + workflow_score; // 0..39
    const resilience_benefit = 12 - resilience_exposure;               // 0..12 good
    const capped_benefit = Math.min(resilience_benefit, Math.floor(risk_total * 0.5));
    const lock_in_index = clamp(risk_total - capped_benefit, 0, 39);

    return {
      identity_score, identity_max: 15,
      archive_score, archive_max: 12,
      workflow_score, workflow_max: 12,
      resilience_exposure,
      redundancy_strength,
      lock_in_index
    };
  }

  $: scores = computeScores(answers);

  function overallLevel(lockIn) {
    if (lockIn <= 10) return "Low";
    if (lockIn <= 20) return "Moderate";
    if (lockIn <= 30) return "Elevated";
    return "High";
  }

  function pct(score, max) {
    if (!max) return 0;
    return Math.round((score / max) * 100);
  }

  // ---------- navigation ----------
  function goStep(i) {
    step = clamp(i, 0, STEPS.length - 1);
  }
  function back() { goStep(step - 1); }
  function next() {
    if (missingHere.length > 0) return;
    goStep(step + 1);
  }
  function submit() {
    if (missingAll.length > 0) return;
    view = "results";
  }
  function resetAll() {
    answers = Object.fromEntries(REQUIRED_KEYS.map(k => [k, ""]));
    step = 0;
    view = "audit";
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }

  // ---------- report + export ----------
  let copied = false;

  function buildReport() {
    const idLevel = levelFor(scores.identity_score, scores.identity_max);
    const arLevel = levelFor(scores.archive_score, scores.archive_max);
    const wfLevel = levelFor(scores.workflow_score, scores.workflow_max);
    const rdLevel = levelFor(scores.redundancy_strength, 12);
    const ov = overallLevel(scores.lock_in_index);

    return [
      "Google Dependency Audit — Results",
      "",
      `Overall Centralization: ${ov}`,
      `Lock-In Index: ${scores.lock_in_index} / 39`,
      "",
      `Identity Centralization: ${idLevel} (${scores.identity_score}/15)`,
      `Archive Concentration: ${arLevel} (${scores.archive_score}/12)`,
      `Workflow Reliance: ${wfLevel} (${scores.workflow_score}/12)`,
      `Resilience / Redundancy: ${rdLevel} (${scores.redundancy_strength}/12)`,
      "",
      "Links:",
      "- Connected services: https://myaccount.google.com/connections",
      "- Security: https://myaccount.google.com/security",
      "- Takeout: https://takeout.google.com/"
    ].join("\n");
  }

  async function copyReport() {
    try {
      await navigator.clipboard.writeText(buildReport());
      copied = true;
      setTimeout(() => (copied = false), 1200);
    } catch {
      // ignore
    }
  }

  function downloadJson() {
    const data = { createdAt: new Date().toISOString(), answers, scores };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "google-dependency-audit.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }
</script>

<div class="container">
  <div class="header">
    <div>
      <h1>Google Dependency Audit</h1>
      <p class="subtle">
        A structural audit of how centralized your digital life is around a Google account.
        Runs entirely in your browser (localStorage).
      </p>
    </div>

    <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end;">
      {#if view === "audit"}
        <span class="badge">Step {step + 1} / 4</span>
        <span class="badge">{missingAll.length === 0 ? "✅ Ready to submit" : `⬜ ${missingAll.length} unanswered`}</span>
      {:else}
        <span class="badge">Results</span>
      {/if}
    </div>
  </div>

  {#if view === "audit"}
    <div class="grid">
      <!-- LEFT -->
      <div>
        <div class="card cardPad">
          <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:center;">
            <div>
              <div style="font-weight:900; letter-spacing:-0.2px;">Audit</div>
              <div class="subtle" style="margin:6px 0 0 0; font-size:13px;">
                Use the tabs or Next/Back. You can’t proceed until the current section is complete.
              </div>
            </div>
            <div class="badge">
              Progress&nbsp;<span class="kbd">{pct(step + 1, 4)}%</span>
            </div>
          </div>

          <div style="margin-top:12px;">
            <div class="progress">
              <div style={`width:${pct(step + 1, 4)}%`}></div>
            </div>
          </div>

          <!-- Animated tab bar -->
          <div class="tabsWrap" style={`--tabX:${step};`}>
            <div class="tabIndicator" aria-hidden="true"></div>
            <div class="tabs">
              {#each STEP_TITLES as t, i}
                <button
                  class={`tabBtn ${i === step ? "active" : ""}`}
                  on:click={() => goStep(i)}
                  title={completedByStep[i] ? "Complete" : "Incomplete"}
                >
                  {#if completedByStep[i]}✅ {/if}{t}
                </button>
              {/each}
            </div>
          </div>
        </div>

        <div style="margin-top: 14px;">
          <!-- single transition ONLY -->
          <div class="card cardPad" in:fly={{ y: 10, duration: 220 }}>
            <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:baseline;">
              <div>
                <div style="font-weight:950; font-size:16px; letter-spacing:-0.2px;">
                  Step {step + 1} — {STEPS[step].title}
                </div>
                {#if STEPS[step].subtitle}
                  <div class="subtle" style="margin-top:6px; font-size:13px;">{STEPS[step].subtitle}</div>
                {/if}
              </div>

              <span class="badge">
                {#if missingHere.length === 0}
                  ✅ Complete
                {:else}
                  ⬜ {missingHere.length} missing
                {/if}
              </span>
            </div>

            <div style="display:grid; gap:10px; margin-top: 12px;">
              {#each STEPS[step].questions as q (q.key)}
                <div class="q" in:fade={{ duration: 120 }}>
                  <h4>{q.label}</h4>

                  <div class="options">
                    {#each q.options as opt}
                      <label class="opt">
                        <input
                          type="radio"
                          name={q.key}
                          checked={answers[q.key] === opt}
                          on:change={() => setAnswer(q.key, opt)}
                        />
                        <div class="txt">{opt}</div>
                      </label>
                    {/each}
                  </div>

                  {#if q.help}
                    <div class="help">{q.help}</div>
                  {/if}
                </div>
              {/each}
            </div>

            <hr class="hr" />

            <div style="display:grid; grid-template-columns: 1fr 1fr 2fr; gap:10px; align-items:center;">
              <div>
                <button class="ghost" on:click={back} disabled={step === 0}>← Back</button>
              </div>

              <div>
                <button on:click={next} disabled={step === 3 || missingHere.length > 0}>Next →</button>
                {#if missingHere.length > 0}
                  <div style="margin-top:6px;" class="subtle">Answer {missingHere.length} more to continue.</div>
                {/if}
              </div>

              <div style="display:flex; justify-content:flex-end; gap:10px; flex-wrap:wrap;">
                <button class="primary" on:click={submit} disabled={missingAll.length > 0}>
                  Submit & View Results
                </button>
                <button class="ghost" on:click={resetAll}>Reset</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT -->
      <div>
        <div class="card cardPad">
          <div style="display:flex; justify-content:space-between; gap:10px; align-items:baseline;">
            <div style="font-weight:950; letter-spacing:-0.2px;">Live Meters</div>
            <span class="badge">
              {missingAll.length === 0 ? "✅ Complete" : `⬜ ${missingAll.length} unanswered`}
            </span>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Identity Centralization</strong>
              <span>{levelFor(scores.identity_score, scores.identity_max)} ({scores.identity_score}/{scores.identity_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.identity_score, scores.identity_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Archive Concentration</strong>
              <span>{levelFor(scores.archive_score, scores.archive_max)} ({scores.archive_score}/{scores.archive_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.archive_score, scores.archive_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Workflow Reliance</strong>
              <span>{levelFor(scores.workflow_score, scores.workflow_max)} ({scores.workflow_score}/{scores.workflow_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.workflow_score, scores.workflow_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Resilience / Redundancy</strong>
              <span>{levelFor(scores.redundancy_strength, 12)} ({scores.redundancy_strength}/12)</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.redundancy_strength, 12)}%`}></div></div>
          </div>

          <hr class="hr" />

          <div style="display:flex; justify-content:space-between; gap:10px; align-items:baseline;">
            <div style="font-weight:950; letter-spacing:-0.2px;">Lock-In Index</div>
            <span class="badge">{overallLevel(scores.lock_in_index)} · {scores.lock_in_index}/39</span>
          </div>

          <div class="callout" style="margin-top:10px;">
            <div style="font-weight:900;">How it’s calculated</div>
            <div style="margin-top:6px; color: rgba(15,26,19,0.72); font-size:12.5px; line-height:1.4;">
              Lock-In Index = (identity + archive + workflow) minus resilience mitigation, capped at 50%.
              “I’m not sure” is scored conservatively.
            </div>
          </div>

          <hr class="hr" />

          <div class="label">Section checklist</div>
          <div style="display:grid; gap:6px; margin-top:8px;">
            {#each STEP_TITLES as t, i}
              <div class="subtle" style="font-size:13px;">
                {#if missingCounts[i] === 0}
                  ✅ {t}
                {:else}
                  ⬜ {t} ({missingCounts[i]} unanswered)
                {/if}
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>

  {:else}
    <div class="card cardPad" in:fly={{ y: 12, duration: 260 }}>
      <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:center;">
        <div>
          <div style="font-weight:980; font-size:18px; letter-spacing:-0.2px;">Results</div>
          <div class="subtle" style="margin-top:6px; font-size:13px;">
            Snapshot of your current structure. Runs locally; nothing is uploaded.
          </div>
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end;">
          <button class="ghost" on:click={() => (view = "audit")}>← Back</button>
          <button class="ghost" on:click={resetAll}>Start Over</button>
          <button class="primary" on:click={copyReport}>{copied ? "Copied!" : "Copy Report"}</button>
          <button on:click={downloadJson}>Download JSON</button>
        </div>
      </div>

      <hr class="hr" />

      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <span class="badge">Overall: <strong style="color: var(--text)">{overallLevel(scores.lock_in_index)}</strong></span>
        <span class="badge">Lock-In: <strong style="color: var(--text)">{scores.lock_in_index}/39</strong></span>
      </div>

      <div class="twoCol" style="margin-top:14px;">
        <div class="card cardPad">
          <div style="font-weight:950; margin-bottom:8px;">Dimension Breakdown</div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Identity Centralization</strong>
              <span>{levelFor(scores.identity_score, scores.identity_max)} ({scores.identity_score}/{scores.identity_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.identity_score, scores.identity_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Archive Concentration</strong>
              <span>{levelFor(scores.archive_score, scores.archive_max)} ({scores.archive_score}/{scores.archive_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.archive_score, scores.archive_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Workflow Reliance</strong>
              <span>{levelFor(scores.workflow_score, scores.workflow_max)} ({scores.workflow_score}/{scores.workflow_max})</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.workflow_score, scores.workflow_max)}%`}></div></div>
          </div>

          <div class="meterRow">
            <div class="meterTitle">
              <strong>Resilience / Redundancy</strong>
              <span>{levelFor(scores.redundancy_strength, 12)} ({scores.redundancy_strength}/12)</span>
            </div>
            <div class="progress"><div style={`width:${pct(scores.redundancy_strength, 12)}%`}></div></div>
          </div>
        </div>

        <div class="card cardPad">
          <div style="font-weight:950;">High-leverage next steps</div>
          <ul style="margin: 10px 0 0 0; padding-left: 18px; color: rgba(15,26,19,0.78); line-height: 1.55;">
            <li>Set a non-Google recovery email on your highest-impact accounts.</li>
            <li>Reduce “Sign in with Google” on services you can’t afford to lose.</li>
            <li>Export and store critical Drive + Photos offline.</li>
            <li>Run Google Takeout periodically to validate portability.</li>
          </ul>

          <hr class="hr" />

          <div class="callout">
            <div style="font-weight:900;">Quick links</div>
            <div style="margin-top:6px; font-size:13px;">
              <div><a href="https://myaccount.google.com/connections" target="_blank" rel="noreferrer">Connected services</a></div>
              <div><a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer">Security</a></div>
              <div><a href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout</a></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <div class="subtle" style="margin-top:14px; font-size:12.5px;">
    Tip: If your graph paper tile isn’t showing, confirm the file exists at <span class="kbd">public/graph-paper.png</span>.
  </div>
</div>