# AI-Native Computer Environment — Architecture & Planning Document

**Status:** Pre-implementation planning
**Scope:** Phase 0 (Research & Architecture) per project mission
**Rule enforced throughout:** No code in this document. This is the plan, not the build.

---

## 1. Product Understanding

We are building a **general-purpose computer-operating agent**, not a social-media bot.

The system is one AI reasoning model, given:

- **eyes** — a screen-parsing bridge that turns screenshots into structured, text-describable observations, since the chosen reasoning model does not natively see images (see §3.7)
- **hands** — mouse, keyboard, terminal, filesystem access
- **a computer** — a disposable, containerized Linux environment with a real browser (Chrome or Brave) and standard tooling (Python, FFmpeg, etc.)

The model reasons about a **goal**, not an **API**. It decides, at each step, the most reliable mechanism available to make progress — a terminal command, a filesystem operation, or GUI interaction through the browser — and verifies the result before continuing.

Social media publishing (Instagram, YouTube, LinkedIn) is the **first proof workflow**, chosen because it forces the system to solve upload, metadata entry, publish-confirmation, multi-platform state tracking, and failure recovery — all through browser interaction rather than three separate APIs. Success on this workflow is evidence the underlying **agent loop + capability layer + verification/recovery subsystem** generalizes to arbitrary tasks (Maps research, spreadsheet generation, website admin work, bulk file renames, PDF-to-slide-deck generation, etc.) without rebuilding the core.

**The product is the runtime. Social posting is the benchmark.**

---

## 2. Architecture

### 2.1 High-level flow

```
                                USER
                                  |
                                  v
                    +----------------------------+
                    |    AI MODEL (Nemotron 3    |
                    |    Ultra — text reasoning) |
                    +--------------+--------------+
                                   |
                                   v
                    +----------------------------+
                    |     AGENT ORCHESTRATOR      |
                    |  plan · state · memory      |
                    |  verify · recover            |
                    +--------------+--------------+
                                   |
                                   v
                    +----------------------------+
                    |      CAPABILITY LAYER       |
                    +---+---------+---------+-----+
                        |         |         |
                        v         v         v
                     SCREEN     INPUT     SYSTEM
                        |         |         |
                        v         v         v
                  OmniParser   Mouse/Key  Terminal/FS/Browser
                 (screenshot ->
                  structured
                  element text)
                                   |
                                   v
                    +----------------------------+
                    |       LINUX DESKTOP         |
                    |  Chrome/Brave · Python       |
                    |  FFmpeg · File Manager        |
                    +----------------------------+
```

**Perception bridge note:** the reasoning model (Nemotron 3 Ultra) is text-only — it cannot accept raw images. The SCREEN capability therefore runs [Microsoft OmniParser](https://github.com/microsoft/OmniParser) locally (icon/element detection + captioning + OCR, MIT licensed) to convert each screenshot into a structured, textual list of labeled UI elements with bounding boxes, which is what actually reaches the model. Playwright's DOM/accessibility-tree query remains the *first-choice* structured path (§2.2a, §3.5); OmniParser is the fallback for canvas UI, icon-only controls, and anything outside the browser. See §3.7 for the full rationale and CPU-latency implications.

### 2.2 Deviations from the prompt's proposed architecture

The prompt explicitly invites critical evaluation rather than blind adoption. Two changes:

**(a) Browser gets a hybrid control path, not pure screen/mouse/keyboard.**
Full visual-only browser control (screenshot → click coordinates) is the least reliable and most expensive way to drive a browser when structured alternatives exist. The Capability Layer's browser backend should default to structured control (Chrome DevTools Protocol / Playwright-style page introspection: DOM queries, accessibility tree, semantic element targeting) and fall back to screenshot+coordinate interaction only when structure is unavailable or ambiguous (canvas-based UI, unlabeled icon buttons, deceptive layouts). This is discussed further in §3.

**(b) "Verification" is promoted to a first-class capability, not a step folded into recovery.**
The original diagram treats verification as part of the recovery flow. In practice verification must run after *every* consequential action (not just failed ones) to detect silent failures — e.g., a click that lands but does nothing. So Verification sits parallel to Recovery under the Agent Orchestrator, both consuming Capability Layer observations.

### 2.3 Intelligence / Execution boundary

| Intelligence (model) decides | Execution (runtime) performs |
|---|---|
| What the user wants | Screenshot capture |
| What the current goal/subgoal is | Mouse/keyboard events |
| Which capability to invoke | Terminal command execution |
| Whether current state matches expectation | Filesystem read/write |
| Whether an action succeeded | Browser navigation, DOM query, CDP calls |
| How to recover from failure | Retry/backoff mechanics (rule-based, not model-driven) |
| Whether the task is complete | Structured logging of every action |

The model never receives raw low-level implementation details it doesn't need (e.g. it shouldn't have to know CDP node IDs); it reasons in terms of intents ("upload the video," "verify publish succeeded") and the execution layer translates that into concrete calls.

### 2.4 Action primitives (initial, small set)

```
observe_screen()          # screenshot + optional structured page summary
click(target)              # target = coordinates OR semantic element ref
type_text(text)
press_key(key) / hotkey(...)
scroll(direction, amount)
drag(from, to)
wait(condition | duration)
open_application(name)
run_command(cmd)
read_file(path) / write_file(path, content) / list_files(path)
browser.navigate(url)
browser.query(selector | description)   # structured lookup, returns element refs
upload_file(path, target)
```

Note the `click`/`browser.query` primitives are deliberately **hybrid**: `target` can be a semantic reference resolved via DOM/accessibility tree first, with coordinate fallback. This avoids the antipattern called out in §40 of the master prompt ("depend entirely on DOM selectors" / "depend entirely on screenshots") by not forcing a binary choice at the primitive level — the choice is made per-call by the execution layer based on what's available.

We are **not** building `instagram_upload()`, `youtube_publish()`, etc. Platform workflows are composed entirely from the primitives above, driven by the model's plan.

---

## 3. Technology Comparison

### 3.1 Linux base / container OS

| Option | Pros | Cons |
|---|---|---|
| **Debian slim (recommended)** | Stable, huge package availability, well-documented Chrome/Brave install paths, small attack surface | Slightly older packages |
| Ubuntu | Very common, good driver/package support | Heavier image, more preinstalled cruft |
| Alpine | Tiny images | musl libc breaks Chrome/many binary tools; not recommended for this use case |

**Recommendation:** Debian slim as base image. Reject Alpine outright — Chrome/Brave and most GUI/automation tooling assume glibc.

### 3.2 Desktop environment

| Option | Pros | Cons |
|---|---|---|
| **XFCE (recommended)** | Lightweight, mature, well-supported under Xvfb/VNC, low resource use, minimal moving parts | Dated visuals (irrelevant — no human uses it directly) |
| LXDE/LXQt | Even lighter | Less mature VNC tooling, smaller community for troubleshooting |
| No DE (raw Xvfb + window manager) | Minimal footprint | Loses file manager / app-launching conveniences that later phases may want; premature optimization |

**Recommendation:** XFCE on Xvfb. It's the de facto standard for containerized browser-automation environments and has the best "someone already solved this" documentation base.

### 3.3 Docker desktop / display stack

| Option | Pros | Cons |
|---|---|---|
| **Xvfb + x11vnc + noVNC (recommended)** | Simple, battle-tested, works headless, browser-viewable over HTTP | Not GPU-accelerated (fine — no 3D workloads) |
| Xpra | Good for seamless app windows | More complex, less commonly documented for this use case |
| Full Wayland stack | Modern | Immature container tooling, more risk for no current benefit |

**Recommendation:** Xvfb (virtual display) + x11vnc (VNC server) + noVNC (browser-based VNC client) for remote viewing per §14.

### 3.4 Chrome vs Brave

| Option | Pros | Cons |
|---|---|---|
| **Google Chrome (recommended default)** | Best CDP/Playwright support, most predictable automation behavior, best documentation, matches what most target sites are tested against | Heavier binary, occasional automation-detection friction on some sites |
| Brave | Privacy-forward, Chromium-based so same automation APIs work | Smaller community for automation edge cases, built-in shields can interfere with page behavior and need explicit config |

**Recommendation:** Chrome as default (`BROWSER=chrome`), Brave as the second supported backend via the same abstraction — exactly as specified. Both are Chromium-based so the CDP-driven backend implementation is ~95% shared code; the browser abstraction should be a thin backend-selection layer, not two parallel implementations.

### 3.5 Browser automation / control

| Option | Pros | Cons |
|---|---|---|
| **Playwright (recommended primary)** | Robust structured control, accessibility-tree + DOM query support, built-in waiting/retry semantics, screenshot support, persistent-context (profile) support out of the box | Adds a Node/Python dependency; not literally "how a human uses the browser" for edge cases |
| Raw CDP | Maximum control, no framework overhead | Much more code to reach Playwright's reliability; reinventing the wheel |
| Pure screenshot + coordinate clicking (computer-vision only) | Works on anything, including canvas UIs | Slow, expensive (many model calls), fragile to layout shifts, no semantic understanding |

**Recommendation:** Playwright as the primary browser backend (structured navigation, element targeting, persistent profile/session support), with screenshot-based visual fallback for the minority of cases where DOM/accessibility structure is insufficient (e.g. ambiguous icon-only buttons, canvas-rendered editors). This is the hybrid approach mandated in §10 of the master prompt.

### 3.6 Mouse/keyboard automation (desktop-level, outside the browser)

| Option | Pros | Cons |
|---|---|---|
| **xdotool (recommended)** | Simple, scriptable, standard on X11, sufficient for desktop-level actions (opening apps, switching windows) | X11-only (acceptable — we're not targeting Wayland) |
| PyAutoGUI | Cross-platform, Python-native | Less precise under Xvfb, extra dependency weight for a single-OS target |

**Recommendation:** xdotool for desktop-level input; Playwright's own input APIs for in-browser interaction (more reliable than xdotool for in-page clicks since Playwright understands page coordinates precisely).

### 3.7 Model provider — **DECIDED: NVIDIA Nemotron 3 Ultra**

Nemotron 3 Ultra (550B total / 55B active MoE, hybrid Mamba-Transformer, 1M token context, released June 2026) is purpose-built for exactly this use case — long-running agentic orchestration, high-volume tool calling, and multi-step reasoning across large context — and is available through an OpenAI-compatible API (NVIDIA's own API catalog, or gateways like OpenRouter/AIMLAPI as alternates). This satisfies the "single provider, interface abstracted" recommendation from the earlier draft of this document.

**The constraint this introduces:** Nemotron 3 Ultra is **text-only** — it does not accept image input. NVIDIA's own documentation is explicit that vision/multimodal tasks need a separate vision-language model in the family (e.g. Nemotron 3 Nano Omni). Rather than run a second hosted model, we're bridging this with a self-hosted, open-source screen-parser instead — see §3.7a.

| Option considered for the vision gap | Pros | Cons |
|---|---|---|
| **OmniParser as a local screen-to-text bridge (decided)** | Self-hosted, no second API dependency, MIT licensed, purpose-built for exactly this (turns any text-only LLM into a computer-use agent), keeps the `ModelProvider` interface uniform for the rest of the system | Adds a local inference workload to the container; CPU-only here, so adds latency (see §3.7a) |
| Second hosted vision-language model (e.g. Nemotron 3 Nano Omni) for `vision()` calls only | True pixel-level vision, handles cases OmniParser's element-detection approach can't (e.g. interpreting an image's actual content, not just UI structure) | Second provider/API dependency, extra cost, extra latency of a second hosted round-trip |
| Minimize vision entirely, rely only on Playwright DOM/accessibility tree | Simplest, fastest, cheapest | Fails for canvas UI, icon-only controls, and anything outside the browser — not viable as the *only* fallback |

**Recommendation:** Build the `ModelProvider` interface (`send`, `vision`, `request_action`, `stream`) against Nemotron 3 Ultra. Implement `vision()` as a **composite call**: run OmniParser locally on the screenshot first, then pass the resulting structured element list to Nemotron 3 Ultra as text. The rest of the orchestrator calls `vision(screenshot)` exactly as it would against a native multimodal model — the text-only/bridged nature of the backend is fully contained inside this one provider implementation. Do not implement a second provider or a second hosted vision model unless real usage shows OmniParser's structural approach missing something a pixel-level model would catch.

### 3.7a Screen-parsing bridge: OmniParser, CPU-only

You've confirmed the host running this container is **CPU-only** for now. OmniParser (YOLO-based icon/interactive-region detector + a small captioning model + OCR) runs on CPU but is meaningfully slower than with a GPU — this is a real latency factor for the agent loop, since every `observe_screen()` call that falls through to OmniParser now costs local inference time on top of the Nemotron API round-trip.

Mitigations to build in from Milestone 5 onward, not as a later optimization pass:

- **Prefer Playwright's structured DOM/accessibility query first, always.** OmniParser should only run when structured lookup fails or is ambiguous — this was already the design (§2.2a), but it's now load-bearing for latency, not just reliability.
- **Region-restricted parsing.** When the orchestrator has a rough idea where the relevant UI is (e.g. "inside this modal," "inside this upload widget"), crop the screenshot to that region before parsing rather than parsing the full screen every time.
- **Cache/reuse parses across near-identical consecutive observations** where nothing meaningfully changed, rather than re-parsing from scratch every loop iteration.
- **Track parse latency in the observability layer (§26/Milestone 12) from day one** so Phase 6 benchmarking has real numbers on how much of total task time is CPU-bound screen parsing — this directly informs whether a future GPU upgrade is worth it.

If, after Phase 6 benchmarking, OmniParser latency turns out to dominate task time, revisit GPU provisioning then — this is a "measure, then decide" item, not a blocker now.

### 3.8 Task state persistence

| Option | Pros | Cons |
|---|---|---|
| **SQLite (recommended)** | Zero extra infra, transactional, survives container restarts via mounted volume, trivially queryable for debugging/observability | Slightly more setup than flat JSON |
| Flat JSON files | Simplest possible | Prone to partial-write corruption on crash; harder to query task history for the benchmark suite (§29) |

**Recommendation:** SQLite in the persistent `/workspace/state` volume. This satisfies §19's requirement to survive crashes/restarts without introducing unnecessary infrastructure (explicitly no external DB server).

---

## 4. Biggest Risks

Ranked by (impact × uncertainty):

1. **Browser control reliability under real (non-mock) social platforms.** Instagram/YouTube/LinkedIn actively evolve their UI, employ bot-detection, and use non-standard upload widgets. This is the highest-uncertainty area and should be validated early with real accounts in a throwaway test, not assumed to "just work" once mock-site tests pass.
2. **Silent failure detection.** A click that visually "succeeds" but doesn't perform the intended action (wrong element, stale reference, popup intercepted the click) is the most common real-world computer-use failure mode. Verification design (§21) needs to be taken seriously from Phase 1, not bolted on later.
3. **Latency of the CPU-bound screen-parsing bridge.** With Nemotron 3 Ultra text-only and OmniParser running on CPU (no GPU provisioned), every `observe_screen()` call that falls through to visual parsing (rather than Playwright's structured query) costs local inference time on top of the API round-trip. On longer tasks this compounds. The hybrid execution-mechanism selection (§9) and the mitigations in §3.7a (prefer structured queries, region-restricted parsing, latency tracking from Milestone 12) are what prevent this from dominating task time — but it needs measuring early, not assumed away.
4. **Prompt injection from untrusted page content.** Any page the browser visits is untrusted input. A malicious or compromised page could contain text designed to be read by the model as an instruction ("ignore previous instructions..."). This needs an explicit trust boundary in the orchestrator (§23), not just a hope that the model "knows better."
5. **Session/profile persistence across restarts.** Persistent browser profiles containing live login sessions are a high-value secret. Getting the volume-mount and credential-handling model wrong is both a reliability risk (broken profile = re-login every run) and a security risk (leaked profile = account compromise).
6. **Scope creep before the core loop is proven.** The spec itself repeatedly warns against this (§40/§41). The single largest execution risk isn't technical — it's building the capability-discovery scanner, multi-model hierarchy, or elaborate UI before Phase 1's minimal proof-of-concept is solid.

---

## 5. MVP Definition

Per §38, the MVP is **not** "Docker starts, browser opens, model can click things." It is complete only when, through the general agent loop (not hardcoded per-platform code paths):

1. Given "publish this video to Instagram, YouTube, and LinkedIn," the agent locates the asset in the workspace.
2. Opens the browser using an existing authenticated persistent session.
3. For each platform: navigates, uploads, enters metadata, publishes, and **verifies** success using observable evidence (not assumption).
4. Records per-platform state in a way that survives a crash — a restart after a partial failure (e.g., Instagram done, LinkedIn failed) must not blindly repeat completed platforms.
5. Recovers from at least the reasonable failure classes in §22 (slow load, popup/modal, transient network error) without human intervention.
6. Stops and asks for human input on failures it cannot safely resolve itself (e.g., login expired, unrecognized UI).
7. Produces a clear, logged final result the developer/user can inspect.

**Explicitly out of scope for MVP:** capability-discovery scanner, multi-model cost hierarchy, approval-level UI beyond a basic confirm gate, benchmark suite beyond the ten smoke-test tasks in §29, Maps-research / PDF-to-slides / website-admin workflows (these come after the engine is proven).

---

## 6. Repository Structure

```
ai-computer/
│
├── agent/
│   ├── planner/          # goal → subgoal decomposition
│   ├── reasoning/         # model-call orchestration, prompt construction
│   ├── memory/            # task state, user preferences, workflow history
│   ├── recovery/          # failure classification + recovery strategies
│   ├── state/             # SQLite-backed task state persistence
│   └── verification/      # post-action success/failure determination
│
├── computer/
│   ├── screen/            # screenshot capture + OmniParser screen-parsing bridge
│   ├── mouse/              # xdotool-backed desktop input
│   ├── keyboard/           # xdotool-backed desktop input
│   ├── browser/            # Playwright backend + Chrome/Brave configs
│   ├── terminal/           # command execution wrapper
│   └── filesystem/         # read/write/list operations
│
├── models/
│   ├── interface/          # ModelProvider abstract interface
│   └── providers/          # nemotron.py — Nemotron 3 Ultra + OmniParser composite vision()
│
├── desktop/
│   ├── docker/              # Dockerfile(s)
│   ├── linux/                # XFCE/Xvfb setup scripts
│   └── browser/              # Chrome/Brave install + persistent-profile config
│
├── tasks/
│   ├── social/               # social publishing workflow definitions (prompts, not code-per-platform)
│   └── benchmarks/            # the 10-task internal benchmark suite (§29)
│
├── workspace/                 # persistent volume: content/captions/processed/published/failed/screenshots/logs/tasks/state
├── config/                    # .env.example, approval-level config, browser choice
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                    # mock local test sites + real-platform smoke tests
├── scripts/
├── docs/
│   ├── architecture/           # this document and future ADR-adjacent material
│   ├── decisions/                # ADRs
│   ├── security/
│   ├── testing/
│   ├── deployment/
│   └── development/
└── docker-compose.yml
```

**Rationale for deviations from the prompt's suggested structure:** essentially none — the proposed structure in §31 is sound and maps cleanly onto the Intelligence/Execution split in §2.3. The only addition is making explicit that `tasks/social/` holds *workflow definitions/prompts*, not per-platform imperative code, to keep the "no `instagram_tool()`" constraint visible at the repo level, not just in prose.

---

## 7. Implementation Roadmap (dependency order)

1. **Phase 0 — Research & Architecture** *(this document)*
2. **Phase 1 — Minimal Computer PoC**: model + screenshot + reasoning + mouse/keyboard + browser, driving a local test page only. No social media.
3. **Phase 2 — General Computer-Control Runtime**: full primitive set, agent loop, task state, verification, recovery — still against local/mock targets.
4. **Phase 3 — Browser Runtime hardening**: persistent profiles, login-state detection, tabs/popups, upload flows, failure recovery specific to real browser quirks.
5. **Phase 4 — Social Media MVP**: Instagram/YouTube/LinkedIn workflows composed from existing primitives.
6. **Phase 5 — Reliability pass**: harden verification, recovery, checkpointing, duplicate-publish prevention using real failure data from Phase 4.
7. **Phase 6 — Benchmarking**: run the 10-task suite, measure success rate/cost/retries, use data to drive further reliability work.
8. **Phase 7 — Production Docker Runtime**: finalize Dockerfile, compose, volumes, health checks, backup/restore, docs.
9. **Phase 8 — AI-Native Computer Platform** *(not started until Phase 0–7 are proven)*: broader task types beyond social publishing.

Each phase follows the methodology in §35: inspect → understand → decide → implement smallest increment → test → fix → document → commit → proceed. No phase should be batch-implemented in one large commit.

---

## 8. Proof of Concept (smallest test of the central hypothesis)

**Hypothesis to validate:** *A multimodal model, given only screenshot-based observation and mouse/keyboard/browser primitives, can complete a simple real task on a webpage without any task-specific code.*

**Concrete PoC:**

```
1. Container boots with XFCE + Xvfb + noVNC + Chrome, reachable via VNC for observation.
2. A local static test page is served (a simple HTML form: one text field + one submit button).
3. Agent receives the goal: "Fill in the field with 'hello world' and submit the form."
4. Loop: observe_screen() → model reasons → click/type_text → observe_screen() → verify success (e.g., page shows a confirmation state) → report done.
5. No platform-specific code exists anywhere in this test — only the generic primitive set.
```

Success criteria: the task completes correctly across multiple runs without hardcoded coordinates baked in ahead of time (coordinates, if used, must be derived from the model's observation each run, not pre-supplied).

This deliberately excludes social media, persistent profiles, and recovery logic — it isolates only the observe → reason → act → verify loop, which is the true foundation everything else depends on.

---

## 9. Architecture Decisions Required Before Coding

| # | Decision | Recommendation (this doc) | Needs your sign-off? |
|---|---|---|---|
| 1 | Linux base image | Debian slim | Confirm |
| 2 | Desktop environment | XFCE + Xvfb | Confirm |
| 3 | Remote viewing stack | x11vnc + noVNC | Confirm |
| 4 | Default browser | Chrome (Brave as second backend) | Confirm |
| 5 | Browser control library | Playwright, screenshot fallback | Confirm — this is the highest-leverage decision in the stack |
| 6 | Desktop-level input | xdotool | Confirm |
| 7 | Model provider | **Decided: NVIDIA Nemotron 3 Ultra** (text reasoning, via NVIDIA API catalog) + **Microsoft OmniParser** (local, CPU-only, screen-to-text bridge for `vision()`) | ✅ Decided |
| 8 | Task state storage | SQLite | Confirm |
| 9 | Approval-level default (AUTO/CONFIRM/MANUAL) | CONFIRM by default for "publish" actions, AUTO for everything else, per §25 | Confirm default policy |
| 10 | Development environment | Antigravity primary / OpenCode secondary, repo remains tool-agnostic | Confirm no change needed |
| 11 | GPU provisioning | **Decided: CPU-only for now.** Debian slim base stays as-is (no CUDA base image needed). Revisit only if Phase 6 benchmarking shows OmniParser latency dominating task time (§3.7a) | ✅ Decided |

---

## 10. Build Strategy

```
empty repository
        │
        ▼
Phase 0 sign-off on the 10 decisions above (this document)
        │
        ▼
Phase 1: minimal PoC (local test page, no social media)
        │   — proves observe/reason/act/verify loop works at all
        ▼
Phase 2: general computer-control runtime
        │   — full primitive set, agent loop, task state, recovery
        │   — still validated only against local/mock targets
        ▼
Phase 3: browser runtime hardening
        │   — persistent profiles, real login/session handling
        ▼
Phase 4: social media MVP
        │   — compose Instagram/YouTube/LinkedIn workflows from
        │     existing primitives; zero new platform-specific code paths
        ▼
Phase 5: reliability pass using real Phase 4 failure data
        ▼
Phase 6: benchmark suite run + data-driven improvement
        ▼
Phase 7: production Docker deployment
        │   — git clone → cp .env.example .env → docker compose up -d
        ▼
Phase 8: broaden beyond social media (only after 0–7 are solid)
```

At every phase boundary: small commits, tests before moving on, documentation updated, and — critically — willingness to revise this document itself if implementation reveals a better approach than what's written here.

---

*End of Phase 0 deliverable. No implementation has begun. Model provider (#7) and GPU provisioning (#11) are now decided — Nemotron 3 Ultra + OmniParser, CPU-only. Remaining items in §9 are recommendations awaiting your confirmation before Phase 1 begins.*
