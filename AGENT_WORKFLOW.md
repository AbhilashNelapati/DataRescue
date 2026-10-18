# OmniRush agent workflow integration plan

The repository intentionally separates deterministic data operations from any optional agent layer. This prevents a model from silently modifying data or claiming a repair passed without executing checks.

## Recommended tool contract

Expose only these typed operations to the permitted OmniRush agent:

- `profile_dataset(dataset_id)` → row/column counts, types, null counts, duplicate count
- `list_quality_issues(dataset_id)` → structured issue codes, severities and row counts
- `propose_repair(issue_ids)` → a JSON plan using an allowlisted repair name, target columns and expected side effects
- `validate_repair_plan(plan)` → reject unknown operations, missing approvals, unsafe row drops or out-of-scope columns
- `execute_repair(plan, working_copy_id)` → run only an allowlisted Python function on a copy
- `verify_output(output_id, quality_contract)` → rerun checks and compare invariants
- `export_audit(run_id)` → immutable report of input hash, action, parameters and verification results

## Agent loop

1. Observe profile and issues.
2. Select the highest-severity actionable issue.
3. Propose a structured repair with rationale and expected side effects.
4. Validate the proposal against the allowlist and safety policy.
5. Request human approval for row deletion or lossy transformations.
6. Execute in a sandbox.
7. Re-run checks and compare row counts, schema and invariants.
8. If verification fails, keep the original working copy and mark the run as failed; never report success based on the model's text alone.

## Buildathon compliance checklist

- Confirm official rules on allowed models, agent platforms, external APIs, team eligibility and submission format.
- If OmniRush is mandatory or exclusive, use only its authorized capabilities for generative AI and agent orchestration.
- Do not use an external LLM as a hidden fallback.
- Keep data cleaning and metrics deterministic in Python.
- Preserve agent session logs and the actual tool-call traces if the event requires them.
- Disclose use of public UCI data and retain its attribution.
- Include a clean build, tests, screenshots or a demo recording generated from the actual running project.
- Do not claim the project is OmniRush-powered until the integration is actually implemented and evidenced.
