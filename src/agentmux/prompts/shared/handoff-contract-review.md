## Submitting Your Review

Use the `agentmux_submit_review` MCP tool to submit your review. This ensures structured, validated output.

**Tool parameters:**
- `verdict` (required) — `"pass"` or `"fail"`
- `summary` (required) — What was reviewed and the outcome
- `findings` (on fail) — List of issues: `[{location, issue, severity, recommendation}]`
- `commit_message` (on pass, optional) — Suggested commit message

The tool validates your input and writes `review.yaml` + `review.md` to the review directory.

**If the MCP tool is unavailable**, write `06_review/review.yaml` directly:

On pass:
```yaml
verdict: pass
summary: |
  All checks passed. Implementation matches the plan.
commit_message: "feat: implement feature X"
```

On fail:
```yaml
verdict: fail
summary: |
  Found issues that need fixing.
findings:
  - location: src/file.py:42
    issue: Missing input validation
    severity: high
    recommendation: Add email format check before database lookup.
```

Then write `06_review/review.md` with `verdict: pass` or `verdict: fail` as the **first line**, followed by the review content.
