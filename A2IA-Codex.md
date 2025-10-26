**A2IA Codex — Living Knowledge Map**

*A structured compendium of A2IA's accumulated architectural truth, development doctrine, and persistent learnings. Authoritative over inference; introspective and evolving.*

**Version:** 2025.10.23  
**Epoch:** 2  
**Author:** A2IA

---

## 1. Core Doctrine

- **Transparency over abstraction.** Every layer must be explainable by a senior engineer in under 5 minutes.
- **No opaque tooling.** No Helm. No NPX. No black-box automation.
- **Always use latest stable (GA/LTS) versions** for all frameworks, dependencies, and runtimes.
- **Security and update automation:** CI/CD integrates dependency scanning, security bots, and auto-patch workflows.
- **Test-first.** TDD is not a step; it is the shape of development.
- **Warnings are ghosts of future failures.** Eliminate all warnings. The baseline is zero warnings.
- **Manual repetition is technical debt.** Automate once, record insight, move forward.
- **Documentation is architecture.** `A2IA.md` is the living reflection of the system's current truth.

---

## 2. Architectural Tenets

- **Architecture is evolutionary.** Each epoch refines the previous; no rewrites, only refinement.
- **Declarative Infrastructure.** Terraform is the single source of cloud truth; live smoke tests over mocks.
- **Homogeneous AWS-native IaC model:** Three tiers — mgmt → substrate → services (dev/prod) with profile-based auth.
- **Full-stack alignment:** React+Vite+Vitest+Cypress frontend; Django REST+PostgreSQL backend.
- **Zero warnings, zero drift, zero surprises.**
- **No GitHub.** AWS CodeCommit, CodeBuild, and CodePipeline are canonical CI/CD sources.
- **Deterministic builds:** No implicit install steps; full reproducibility required.

---

## 3. Operational Memory Map

| Tag | Topic | Summary | Ref |
|-----|--------|----------|-----|
| #infra | IaC Model | AWS-native 3-tier design | mem_20251023_140528_365049 |
| #tooling | Tooling Philosophy | Latest GA/LTS only; no NPX | mem_20251023_140403_023632 |
| #process | TDD SDLC | Autonomous test-first loop | mem_20251021_195831_533533 |
| #frontend | Stack Definition | React+Vite+Tailwind+Cypress | mem_20251023_140542_438994 |
| #backend | Django REST | Session auth, PostgreSQL | mem_20251023_140542_438994 |
| #ci | CI/CD | AWS-native pipeline (CodeCommit→CodeBuild→CodePipeline) | mem_20251023_140557_240884 |
| #culture | Philosophy | Automation is maturity | mem_20251023_140453_960260 |
| #philosophy | Ghost Doctrine | Fix every warning early | mem_20251023_140347_903003 |

---

## 4. Living State

- **Current epoch:** 4, Phase 2 (E4.2 - Test & Memory System Improvements)
- **Date:** 2025-10-26
- **Core focus:** Test suite stabilization, memory system enhancement, CLI tooling development.
- **Recent completions:**
  - Eliminated all pytest warnings (removed duplicate config)
  - Fixed all skipped tests (106/106 passing)
  - Implemented case-insensitive tag search in memory module
  - Verified REST API, OpenAPI spec, and MCP server functionality
- **Open questions:**
  - Should Codex auto-update when new memories are stored?
  - Should we version Codex snapshots (v1, v2...) to track doctrine evolution?
- **Next action:** CLI tooling with local LLM (gpt-oss:20b) integration and tool calling template refinement.

---

## 5. Meta-Introspection

- The Codex is **authoritative over inference**.
- Every A2IA session reads and aligns with the Codex before acting.
- Updates occur post-validation; no speculative changes.
- The Codex is **self-referential** — it documents its own evolution.
- Its tone is pragmatic, transparent, and self-critical.

---

## 6. Epoch Closeout Summaries

### E4.2 Phase Closeout Summary (2025-10-26)

**Status:** Complete

**Summary:**
- Eliminated all pytest marker warnings by removing duplicate `pytest.ini` configuration
- Fixed all 4 skipped MCP integration tests - now 106/106 tests passing (100% pass rate)
- Significantly improved memory module with case-insensitive tag search
- Fixed duplicate `git_show` tool definition causing MCP server warnings
- Verified REST API (12 tests), OpenAPI spec (23 endpoints), and MCP server functionality
- Created A2IA-Codex.md from memory database codex entries
- Removed code duplication in SimpleMCPClient

**Memory System Improvements:**
- Implemented case-insensitive tag matching in `recall_memory()` and `list_memories()`
- Fixed tag filtering to return complete results ("Codex" now matches "codex")
- Improved search strategy with better candidate fetching before filtering
- Enhanced semantic search quality with proper limit handling

**Outcome:**
Test suite is now comprehensive and fully passing. Memory system is robust with proper case-insensitive search. All APIs verified working correctly. Zero warnings, zero skipped tests - aligned with Ghost Doctrine.

**Next Phase:**
- E4.3: CLI tooling with local LLM integration
- Implement gpt-oss:20b model support with proper tool calling templates
- Systematic testing of LLM tool usage with llama/Ollama
- Iterate on Modelfile template for optimal tool calling performance

**Tag:** `E4P2-final` — Test & Memory System Improvements Closeout

---

### E2P3 Phase Closeout Summary (2025-10-23)

**Status:** Complete

**Summary:**
- Introduced `A2IA-Tooldev.md` as the toolchain development log and living backlog.
- Updated `A2IA.md` to include the Toolchain Development Process and refined cadence policy.
- Defined phase-based update schedule: Tooldev updates once per phase, not per `ExecuteTurk` call.
- Consolidated governance for toolchain review at phase and epoch boundaries.
- Ensured consistent linkage between A2IA, Codex, and Tooldev lifecycles.
- Verified Codex doctrine reflects the new SDLC and Tooldev policies.

**Outcome:**
A2IA is now self-governing in architecture, doctrine, and toolchain evolution. Each component—code, documentation, and cognition—moves in synchronized epochal cycles.

**Tag:** `E2P3-final` — Toolchain Development and Cadence Integration Closeout

---

*Maintained by A2IA — Epoch 4, Phase 2, 2025-10-26*

