# ADR-004: Archive content hash across zlib implementations

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** none; amends QA-61 and SDD I-12. **RFC:** none.

## Context

QA-61 requires a reproducible archive whose rebuild yields the same SHA-256. V-12: the tar is byte-identical on all eight runs, but the `.tar.gz` differs when Python is linked to zlib-ng (Python 3.14 on Windows) rather than zlib. Only gzip level 0 matched across the two on the test input.

## Decision

The manifest records the SHA-256 of the **uncompressed tar** as the canonical content hash, beside the `.tar.gz` digest, and records the Python and zlib versions used to build. W-12 and release verification compare the tar digest; they compare the `.tar.gz` digest only when the recorded versions match. Citations verify against the tar digest.

## Consequences

- I-12 and `release.py` change as in the SDD. FR6.6 and FR7.3 acceptance text ("matches its recorded checksum") is read as the tar digest; the owner confirmed this reading by approving this ADR. The SRS wording is not edited here.
- P2 gains 0.25 to 0.5 day to test the rule on Python 3.11 and 3.14.

## Alternatives

Gzip level 0 everywhere (about ten times the size on the 30 KB test input); one pinned interpreter build for all archives (kept as the recorded-versions condition, not a rule); a compressor with specified output.
