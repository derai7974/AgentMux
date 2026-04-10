# Review of PR #103 (https://github.com/markuswondrak/AgentMux/pull/103/changes)

This is a documentation of all findings of the mentioned pull request. All findings must be classifiied into: 

- **small fixes** - easy effort / single file
- **medium fixes** - medium effort / multiple files, but clear target state
- **large refactorings** - mutliple files and unclear target state
- **questions** - open points / unclear state, just need answer for now, but might transistion to a fix

## General findings

- phases docs should have a common structure (prequisists / conditions, transistions from, transistions to, artifacts, ...) - **[medium fix]**
- `state.json` (workflow phase + metadata) and `runtime_state.json` (pane IDs, PIDs, role mapping) serve different concerns but should be merged into a single unified session artifact - **[medium fix]** → JIRA-XYZ
- We should have a dedicated **artifact documentation** for all important session artefacts that describe the schema and semantics - **[medium fix]**
- **research** tasks can be spawn by the **product-manager**, **architect** and **planner** --> results (if available) must be injected to **architect**, **planner** and **coder** - **[medium fix]** ✅ solved


## `docs/phases/completion.md`
- `summary_prompt.md` is actively used in `reviewing.py:203` — no action needed

## `docs/phases/design.md`

## `docs/phases/implementation.md`
- having a special phase fixing is weird - would be more straigh forward to call it implementation, just the tasks, plan and transition differs from the "normal" coding phase - **[large refactoring]** → JIRA-XYZ

## `docs/phases/planning.md`
- **architecting** and **planning** need to be seperated and get their own folder - **[medium fix]** ✅ solved
- **research** as well needs to be in its own session folder - **[medium fix]** ✅ solved

## `docs/phases/product-management.md`

- "Its output is advisory — if it conflicts with `requirements.md`, `requirements.md` wins." --> This should not be true - The product managers Job is to clarify stuff. If during the session requirements change because of user input, then `requirements.md` need to be updated - **[medium fix]**
- `analysis.md` is advisory context written by the PM and optionally injected into the architect prompt — no action needed

## `docs/phases/review.md`

- Specialist reviewers run sequentially (one per cycle, selected by `review_strategy`); parallel activation is not supported — would require redesign of the single-pane-per-role model and the sequential state machine - **[large refactoring]** → JIRA-XYZ

## `docs/completing-phase.md`

- These contents should be included into `docs/phases/completion.md` - **[small fix]** ✅ solved
