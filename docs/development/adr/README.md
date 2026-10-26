# Architecture decision records

- `OKF Library Template - Design Decision Record.md` (the DDR) keeps its exact file name. Its series AD- (in the SDD), QA- and DR- are frozen: existing entries stay citable and are not renumbered (DDR QA-68).
- New decisions are one file each, `ADR-NNN-title.md`, numbered in sequence from ADR-001, lowercase hyphenated title.
- Each ADR states context, decision, consequences and status (`Proposed|Accepted|Superseded by ADR-NNN`), and links its RFC if there is one (and the RFC links back).
- ADRs are never deleted. A reversed decision gets a new ADR that supersedes the old one, which may be an ADR or an entry in the frozen series.
