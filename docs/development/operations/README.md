# Operations

Procedures for running and recovering the template and its workflows.

- Runbooks: `runbook-<task>.md`. Here, the template's own: `runbook-create-template-repository.md` (done 26 October 2026). The runbooks a library also needs are sections of `docs/guide/runbooks.md`, in the user guide that libraries keep (P4 PR U): instantiate a library (W-01 and the V-06 timing sheet), promote a library to public (W-11), move a git-local library to GitHub (W-12), recover the revision history, remove leaked content.
- Rollback plans: `rollback-<change>.md`, written before a risky change ships.
- Postmortems: `postmortem-YYYY-MM-DD-<slug>.md`, blameless, with actions linked to RFCs, ADRs or requirements.
