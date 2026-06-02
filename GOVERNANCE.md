# Governance

The Heirloom License aims to be a stable, trustworthy standard. The value of a
license is its permanence: adopters and their buyers must be able to rely on the
exact terms not shifting under them. This document describes how the license is
stewarded.

## Stewardship

The license is currently stewarded by its maintainers via this repository. The
steward's job is narrow on purpose: shepherd versions, keep the text and tooling
accurate, and protect the marks. The steward does **not** have the power to alter
the terms of an already-published version.

## Versioning and immutability

- Every published version of the license is **immutable**. Once a version is
  tagged and released, its text is never edited. Typos and ambiguities are fixed
  only by issuing a **new** version.
- Versions are identified by a tag and a GitHub Release (e.g. `v1.0`). The
  Release is the canonical, archival copy.
- The machine-readable identifier encodes the version and parameters:
  `HL-<version>-<ChangeLicense>-<DormancyWindow>` (e.g. `HL-1.0-MPL2.0-12mo`).
- Software released under a given version stays governed by that version forever,
  regardless of later versions. New versions never apply retroactively.

## Proposing changes

- Open an issue to discuss a problem or a proposed change. Substantive proposals
  should explain the problem, the affected clause, and the impact on existing
  adopters.
- Changes that affect meaning ship only in a new numbered version, with a
  changelog entry explaining what changed and why.
- Editorial changes (docs, examples, tooling) can land on `main` without a new
  license version, as long as they don't touch `LICENSE.md`'s operative text.

## The marks

The license **text** is dedicated to the public domain (CC0 1.0) — fork it freely.
The **name "Heirloom License" and the badge** are project marks. Use them only for
software released under an unmodified, published version of the license, so the
badge reliably means one specific thing to buyers. Modified derivatives must use a
different name.

## What will not change

- Existing published versions are permanent.
- The license text stays CC0.
- The Sunset grant, once it has occurred for a version of an adopter's software,
  is governed solely by that adopter's chosen Change License and is outside this
  project's control.

## Status

`v1.0-draft` is a community draft pending legal review (see `LEGAL-REVIEW.md`).
Until a version is marked stable, terms may still change between drafts.
