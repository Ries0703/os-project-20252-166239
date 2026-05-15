# MLFQ OS Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-quality Streamlit app that simulates exactly one scheduling algorithm: Multi-Level Feedback Queue (MLFQ), with deterministic behavior, reproducible validation, and a local-first repo setup that can be executed from zero ambiguity.

**Architecture:** Use a `src`-layout Python package with a pure scheduling engine separated from Streamlit UI and JSON persistence. The scheduler is the single source of truth; UI only validates input, invokes the engine, and renders metrics/history from typed models.

**Tech Stack:** Python 3.12, `uv`, Streamlit, Pydantic v2, Pandas, Plotly, FileLock, Pytest, Ruff, `ty`

---

## Locked Decisions

This section closes the gaps left open in `docs/master-plan.md`.

1. Runtime is a local/web Streamlit app, not a desktop-only script.
2. Project layout uses `src/` package structure, not scattered `core/` and `features/` folders at repo root.
3. Python package/dependency management is `uv` with committed `pyproject.toml` and `uv.lock`.
4. All Python tooling must be Astral-native wherever a realistic Astral option exists: `uv` for env/package/run, `ruff` for format/lint, `ty` for type checking.
5. The app implements exactly one scheduling algorithm and one product mode: preemptive MLFQ with three queues `Q0`, `Q1`, `Q2`.
6. No other scheduling algorithms are implemented, exposed, compared, or scaffolded for future switching.
7. Anti-starvation uses exactly one mechanism: global priority boost every `aging_boost_interval` ticks. There is no second aging mode based on per-process waiting time.
8. Scheduler mode is strictly preemptive for `Q0` arrivals against running `Q1`/`Q2` processes.
9. Simulation is discrete tick-based in integer milliseconds; all Gantt intervals are end-exclusive `[start, finish)`.
10. Context-switch overhead is logged as `CS Overhead` and charged only when switching directly from one process to another. No overhead is charged for the first dispatch of the simulation or when CPU wakes from `Idle`.
11. Priority boost is global and deterministic: at each tick where `time_current > 0` and `time_current % aging_boost_interval == 0`, all waiting processes in `Q1` and `Q2` move to the tail of `Q0` in stable order; a running process has `current_queue = 0` and `quantum_used = 0` reset in place and is not requeued.
12. When a running `Q1` or `Q2` process is preempted by newly available `Q0` work, it returns to the front of its current queue to preserve partial-service order.
13. A preempted process keeps the quantum it has already used in its current queue; preemption does not reset `quantum_used`.
14. `Q2` remains a simplified final queue: when a process uses up its quantum in `Q2` and is still unfinished, it remains in `Q2`. No extra mode selection is introduced.
15. Adjacent Gantt ticks for the same `Task` and `Queue` are merged into a single segment before presentation/persistence.
16. Input validation rejects empty tables, duplicate `pid`, negative `arrival_time`, non-positive `burst_time`, and non-integer values after normalization.
17. Repository storage stays JSON-only; no database is introduced.
18. Local execution is the primary deployment target; Docker is out of scope for the initial deliverable.
19. Production-grade for this project means deterministic behavior, typed boundaries, repeatable tests, lint/type gates, and reproducible local execution. It does not mean distributed deployment or auth.
20. Global machine tooling is limited to cross-project Python tooling: `uv`, Python `3.12`, `ruff`, and `ty`.
21. Application and test libraries such as `streamlit`, `pytest`, `pydantic`, `pandas`, `plotly`, and `filelock` must remain project-local dependencies managed through `pyproject.toml` and `uv sync`.

## Core Product Scope

This project exists to teach and demonstrate one algorithm clearly, not to become a general scheduling framework.

- The app must show the four core MLFQ behaviors: new process enters `Q0`, CPU chooses `Q0 -> Q1 -> Q2`, quantum exhaustion demotes a process, and periodic boost prevents starvation.
- The app must let a lecturer or reviewer enter a small process table, run the simulation, and visually inspect the result through metrics, Gantt chart, and history.
- The app must stay simple enough that a reader can map the UI back to the algorithm described in `docs/project-draft.md`.

## Out Of Scope

The following are explicitly forbidden for the initial deliverable:

- Additional scheduling algorithms such as FCFS, SJF, Priority, or standalone RR
- Multiple MLFQ variants or a user-selectable algorithm mode
- Multiple anti-starvation strategies in the same product
- Benchmarking dashboards, performance comparison pages, or algorithm tournament views
- Database backends, multi-user auth, cloud deployment, or plugin-style extensibility
- Architecture work done only for hypothetical future expansion

## Gap Review

These are the concrete weaknesses in `docs/master-plan.md` that make one-shot execution risky:

- File structure is inconsistent: `features/1_mlfq_engine/service.py` and `features/mlfq/service.py` both appear.
- Dependency/runtime setup is missing: no `uv`, `pyproject.toml`, version policy, or exact commands to bootstrap the app.
- Acceptance criteria are too weak: "in thử Gantt log ra Console" is not a reliable correctness gate.
- Scheduler semantics are still ambiguous around context-switch timing, preemption order, throughput formula, and boost interaction with the running process.
- Test strategy is absent, so there is no way to prove the engine is correct after refactors.
- Persistence hardening is underspecified: no atomic-write strategy, corrupt-file recovery, or schema versioning.
- UI contract is incomplete: no unique PID rule, no empty-state behavior, no data normalization policy.
- The old plan does not distinguish between cross-project tooling and project-local dependencies, which leads to avoidable global installs.
- The old plan still leaves room to overbuild beyond the actual course objective, which is a single MLFQ simulator rather than a scheduling workbench.

## Target File Map

### Application files

- Create: `app.py`
- Create: `src/mlfq_os_simulator/__init__.py`
- Create: `src/mlfq_os_simulator/config.py`
- Create: `src/mlfq_os_simulator/models.py`
- Create: `src/mlfq_os_simulator/scheduler.py`
- Create: `src/mlfq_os_simulator/metrics.py`
- Create: `src/mlfq_os_simulator/repository.py`
- Create: `src/mlfq_os_simulator/ui/sidebar.py`
- Create: `src/mlfq_os_simulator/ui/simulator_tab.py`
- Create: `src/mlfq_os_simulator/ui/dashboard_tab.py`
- Create: `src/mlfq_os_simulator/ui/history_tab.py`
- Create: `src/mlfq_os_simulator/ui/animation.py`

### Project and runtime files

- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.streamlit/config.toml`
- Create: `data/config.json`
- Create: `data/history.json`
- Create: `README.md`
- Create: `scripts/setup-python-tooling.ps1`

### Test files

- Create: `tests/conftest.py`
- Create: `tests/unit/test_config.py`
- Create: `tests/unit/test_models.py`
- Create: `tests/unit/test_scheduler_basic.py`
- Create: `tests/unit/test_scheduler_preemption.py`
- Create: `tests/unit/test_scheduler_boost.py`
- Create: `tests/unit/test_scheduler_idle.py`
- Create: `tests/unit/test_repository.py`
- Create: `tests/integration/test_app.py`

## Domain Rules To Implement

### Scheduler invariants

- Total executed process time equals the sum of all `burst_time`.
- No process may have `remaining_time < 0`.
- `start_time` is written exactly once, at first CPU execution tick.
- `completion_time` is the tick immediately after the final unit of execution.
- Each input process appears exactly once in completed results.
- Queue selection is always `Q0`, then `Q1`, then `Q2`.
- Tie-breaker for same-arrival processes is the original input row order.
- Throughput formula is `completed_process_count / makespan`, where `makespan = max(completion_time)` and must be greater than zero.

### Tick order

For every tick, the scheduler must execute logic in this order:

1. Circuit breaker.
2. Arrival ingestion.
3. Priority boost.
4. Context-switch cooldown handling.
5. Preemption check.
6. Dispatch if CPU is free.
7. Execute one time unit.
8. Resolve completion or demotion.

No alternative ordering is allowed.

### Repository behavior

- `data/config.json` stores exactly one config document with schema version.
- `data/history.json` stores a list of at most 20 runs, newest last.
- Every write uses `FileLock`, writes to a temporary file, then replaces the target atomically.
- Missing files are auto-created with defaults.
- Corrupt JSON triggers safe fallback: config resets to defaults, history resets to empty list, and the error is surfaced to UI as a warning.

## Acceptance Fixtures

These fixtures are mandatory golden tests. They replace vague "looks correct" validation.

### Fixture A: Single process demotion path

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=0`
- Input:
  - `P1 arrival=0 burst=20`
- Expected Gantt:
  - `P1 Q0 0-4`
  - `P1 Q1 4-12`
  - `P1 Q2 12-20`
- Expected metrics:
  - `turnaround=20`
  - `waiting=0`
  - `response=0`
  - `throughput=0.05`

### Fixture B: Preemption by new Q0 work

- Config: `q0=2`, `q1=4`, `q2=8`, `boost=50`, `cs=0`
- Input:
  - `P1 arrival=0 burst=7`
  - `P2 arrival=3 burst=1`
- Expected Gantt:
  - `P1 Q0 0-2`
  - `P1 Q1 2-3`
  - `P2 Q0 3-4`
  - `P1 Q1 4-7`
  - `P1 Q2 7-8`
- Expected process metrics:
  - `P2 response=0`
  - `P1 completion=9`

### Fixture C: Global boost returns waiting work to Q0

- Config: `q0=1`, `q1=1`, `q2=2`, `boost=4`, `cs=0`
- Input:
  - `P1 arrival=0 burst=5`
  - `P2 arrival=0 burst=5`
- Expected Gantt:
  - `P1 Q0 0-1`
  - `P2 Q0 1-2`
  - `P1 Q1 2-3`
  - `P2 Q1 3-4`
  - `P1 Q0 4-5`
  - `P2 Q0 5-6`
  - `P1 Q1 6-7`
  - `P2 Q1 7-8`
  - `P1 Q0 8-9`
  - `P2 Q0 9-10`

### Fixture D: Context switch is charged between processes

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=1`
- Input:
  - `P1 arrival=0 burst=1`
  - `P2 arrival=0 burst=1`
- Expected Gantt:
  - `P1 Q0 0-1`
  - `CS Overhead N/A 1-2`
  - `P2 Q0 2-3`

### Fixture E: Idle CPU before first arrival

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=0`
- Input:
  - `P1 arrival=3 burst=2`
- Expected Gantt:
  - `Idle N/A 0-3`
  - `P1 Q0 3-5`
- Expected metrics:
  - `turnaround=2`
  - `waiting=0`
  - `response=0`

### Fixture F: Invalid input is rejected before scheduling

- Config: any valid config
- Input:
  - duplicate `pid`, or
  - `arrival_time < 0`, or
  - `burst_time <= 0`, or
  - empty process table
- Expected behavior:
  - scheduler is not invoked
  - UI renders a readable error message
  - no history entry is written

## Quality Gates

Every implementation pass must satisfy all of these commands:

- `uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run ty check src`
- `uv run pytest`
- `uv run streamlit run app.py --server.headless true`

The app is not considered done if any one of these fails.

### Task 1: Bootstrap the project skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.streamlit/config.toml`
- Create: `README.md`

- [ ] **Step 1: Write the failing environment smoke test**

Create `tests/integration/test_app.py` with a minimal app boot smoke test.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_app.py -v`
Expected: FAIL because package files do not exist yet.

- [ ] **Step 3: Create project metadata and dependency definitions**

Add:
- runtime deps: `streamlit`, `pydantic`, `pandas`, `plotly`, `filelock`
- dev deps: `pytest`, `pytest-cov`, `ruff`, `ty`
- machine-level prerequisites documented separately: Python `3.12`, `uv`, global `ruff`, global `ty`
- Python constraint: `>=3.12,<3.13`

- [ ] **Step 4: Create basic package structure**

Create empty package files under `src/mlfq_os_simulator/` and point `pyproject.toml` to the `src` layout.

- [ ] **Step 5: Sync environment and regenerate lock**

Run: `uv sync`
Expected: environment created and `uv.lock` written.

- [ ] **Step 6: Commit**

Run:
```bash
git add pyproject.toml uv.lock .python-version .gitignore .streamlit/config.toml README.md src/mlfq_os_simulator tests/integration/test_app.py
git commit -m "chore: bootstrap mlfq simulator project"
```

### Task 2: Define typed domain models and config IO

**Files:**
- Create: `src/mlfq_os_simulator/config.py`
- Create: `src/mlfq_os_simulator/models.py`
- Create: `data/config.json`
- Test: `tests/unit/test_config.py`
- Test: `tests/unit/test_models.py`

- [ ] **Step 1: Write failing model tests**

Tests must cover:
- `AppConfig` rejects zero/negative quantum values.
- `ProcessInput` rejects invalid rows.
- `ProcessState` computes turnaround, waiting, response correctly.
- `SimulationRun` includes `avg_response`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_config.py tests/unit/test_models.py -v`
Expected: FAIL because models do not exist.

- [ ] **Step 3: Implement typed models**

Implement:
- `AppConfig`
- `ProcessInput`
- `ProcessState`
- `GanttLogEntry`
- `SimulationRun`

Requirements:
- include `schema_version`
- include `avg_response`
- store stable `input_order` in process state for tie-breaking

- [ ] **Step 4: Implement config load/save helpers**

Config module must expose:
- `default_config()`
- `load_config(path)`
- `save_config(path, config)`

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_config.py tests/unit/test_models.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add src/mlfq_os_simulator/config.py src/mlfq_os_simulator/models.py data/config.json tests/unit/test_config.py tests/unit/test_models.py
git commit -m "feat: add typed scheduler models and config"
```

### Task 3: Build the scheduler with golden tests first

**Files:**
- Create: `src/mlfq_os_simulator/scheduler.py`
- Create: `src/mlfq_os_simulator/metrics.py`
- Test: `tests/unit/test_scheduler_basic.py`
- Test: `tests/unit/test_scheduler_preemption.py`
- Test: `tests/unit/test_scheduler_boost.py`
- Test: `tests/unit/test_scheduler_idle.py`

- [ ] **Step 1: Write failing scheduler tests from Fixtures A-E**

Each fixture becomes an exact assertion over merged Gantt segments and per-process metrics.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_scheduler_basic.py tests/unit/test_scheduler_preemption.py tests/unit/test_scheduler_boost.py tests/unit/test_scheduler_idle.py -v`
Expected: FAIL because scheduler does not exist.

- [ ] **Step 3: Implement the scheduling engine**

Implement `MLFQScheduler.run(processes, config) -> SimulationRun` with:
- strict tick order from this plan
- merged segment logging
- deterministic queue handling
- timeout guard at `100_000`
- throughput and average metrics calculation

- [ ] **Step 4: Add invariant helpers**

Implement internal validation that:
- all processes complete once
- no negative remaining time exists
- burst sum equals executed non-overhead time

- [ ] **Step 5: Run the targeted scheduler suite**

Run: `uv run pytest tests/unit/test_scheduler_basic.py tests/unit/test_scheduler_preemption.py tests/unit/test_scheduler_boost.py tests/unit/test_scheduler_idle.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add src/mlfq_os_simulator/scheduler.py src/mlfq_os_simulator/metrics.py tests/unit/test_scheduler_basic.py tests/unit/test_scheduler_preemption.py tests/unit/test_scheduler_boost.py tests/unit/test_scheduler_idle.py
git commit -m "feat: implement deterministic mlfq scheduler"
```

### Task 4: Implement hardened JSON repository behavior

**Files:**
- Create: `src/mlfq_os_simulator/repository.py`
- Create: `data/history.json`
- Test: `tests/unit/test_repository.py`

- [ ] **Step 1: Write failing repository tests**

Tests must cover:
- auto-create missing files
- prune history to 20 items
- atomic write path
- corrupt config fallback
- corrupt history fallback

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_repository.py -v`
Expected: FAIL because repository does not exist.

- [ ] **Step 3: Implement JSON repository**

Expose:
- `load_config()`
- `save_config(config)`
- `get_all_runs()`
- `save_run(run)`

Use `FileLock`, temp file replace, and explicit Pydantic validation on load.

- [ ] **Step 4: Run repository tests**

Run: `uv run pytest tests/unit/test_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add src/mlfq_os_simulator/repository.py data/history.json tests/unit/test_repository.py
git commit -m "feat: add hardened json persistence"
```

### Task 5: Build the Streamlit UI around the engine

**Files:**
- Create: `app.py`
- Create: `src/mlfq_os_simulator/ui/sidebar.py`
- Create: `src/mlfq_os_simulator/ui/simulator_tab.py`
- Create: `src/mlfq_os_simulator/ui/dashboard_tab.py`
- Create: `src/mlfq_os_simulator/ui/history_tab.py`
- Create: `src/mlfq_os_simulator/ui/animation.py`
- Modify: `tests/integration/test_app.py`

- [ ] **Step 1: Extend the failing app integration test**

Test the following pure helpers instead of browser automation:
- process-table normalization
- validation error collection
- app boot and run flow
- animation component render
- history persistence after run

- [ ] **Step 2: Run targeted integration test**

Run: `uv run pytest tests/integration/test_app.py -v`
Expected: FAIL because app flow is not implemented yet.

- [ ] **Step 3: Implement UI modules**

Requirements:
- Sidebar loads/saves config through repository.
- Simulator tab supports manual rows and generated demo data.
- Run action validates rows before invoking scheduler.
- Simulator tab renders animation playback using client-side HTML/JS, not server-side tick reruns.
- Dashboard tab renders metrics, numeric-time Gantt chart, and process table.
- History tab renders persisted runs.

- [ ] **Step 4: Add user-facing error and empty states**

Required behaviors:
- empty table blocks run
- duplicate PID blocks run
- negative arrival blocks run
- non-positive burst blocks run
- repository recovery warning is shown once
- no history state renders a readable placeholder

- [ ] **Step 5: Run integration and scheduler tests**

Run: `uv run pytest tests/integration/test_app.py tests/unit/test_scheduler_basic.py tests/unit/test_scheduler_preemption.py tests/unit/test_scheduler_boost.py tests/unit/test_scheduler_idle.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add app.py src/mlfq_os_simulator/ui tests/integration/test_app.py
git commit -m "feat: add streamlit interface for mlfq simulator"
```

### Task 6: Add local bootstrap script and final runbook

**Files:**
- Create: `scripts/setup-python-tooling.ps1`
- Modify: `README.md`

- [ ] **Step 1: Write the failing local bootstrap smoke checks**

Add commands to README and verify they currently fail:
- `powershell -ExecutionPolicy Bypass -File .\scripts\setup-python-tooling.ps1`
- `uv run streamlit run app.py`

- [ ] **Step 2: Implement one-shot PowerShell bootstrap**

Requirements:
- install or update `uv` if missing
- install Python `3.12` via `uv python install 3.12`
- install global `ruff` and `ty` via `uv tool install`
- optionally run `uv sync` when `pyproject.toml` exists
- avoid global install of `streamlit` or any runtime library
- print a post-run verification summary

- [ ] **Step 3: Document exact operator commands**

README must include:
- first-time bootstrap
- local run
- test suite
- lint/typecheck
- re-running the bootstrap script safely
- data file locations

- [ ] **Step 4: Run full verification**

Run:
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run ty check src`
- `uv run pytest`
- `uv run streamlit run app.py --server.headless true`

Expected: all PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add scripts/setup-python-tooling.ps1 README.md
git commit -m "chore: add local bootstrap workflow"
```

## Non-Negotiable Review Checklist

Before calling the project done, verify all of the following:

- The delivered product still solves exactly one problem: simulate MLFQ clearly. No extra scheduling modes have been added.
- Every scheduler rule in `docs/master-plan.md` is either implemented or explicitly superseded by a locked decision in this plan.
- All six acceptance fixtures exist as automated tests or direct UI validation checks, with exact expected outcomes.
- `avg_response` is shown in UI and persisted in history.
- No Streamlit code contains business logic that duplicates scheduler rules.
- Repository code never writes JSON without lock-and-replace.
- `uv.lock` is committed.
- `scripts/setup-python-tooling.ps1` installs only cross-project tooling globally and leaves app libraries project-local.
- `app.py` remains the only official entrypoint for the application.

## Execution Notes

- Do not start with packaging extras. Build the pure scheduler and tests first.
- Do not refactor the file structure after Task 1. The package map is fixed.
- Do not merge UI validation and scheduler validation into one layer; keep UI for user messages and engine for hard invariants.
- Do not add extensibility layers for future algorithms. Build the one MLFQ path cleanly and stop there.
- If a rule in `docs/project-draft.md` conflicts with this plan, this plan wins because it resolves ambiguity into executable behavior.

Plan complete and saved to `docs/superpowers/plans/2026-05-15-mlfq-os-simulator.md`.
