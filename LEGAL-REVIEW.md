# Legal review checklist

This is a community draft. Before promoting the license or relying on it for
commercial sales, a licensing attorney in the relevant jurisdiction(s) should
review the following. Flag these specifically — don't just ask "is this okay."

## Must-review clauses

1. **Self-executing future grant (Section 5–6).** The license grants public
   rights automatically on a future condition, with no act by the Licensor. BSL
   does essentially this on a fixed date and is widely relied upon; confirm the
   *conditional* trigger (dormancy rather than a date) is equally clean and that
   the irrevocable grant survives the Licensor's bankruptcy or death (i.e. it
   binds successors, estates, and acquirers).

2. **Dormancy definition (Section 4).** Is "no maintenance signal + no support
   response in 90 days" objective enough to be enforceable, and does it create
   any unintended trigger (e.g. a developer on medical leave)? Consider whether a
   cure/notice period before Sunset is desirable or whether it undermines the
   promise.

3. **Disclaimer & liability on/after Sunset (Sections 8–9).** Releasing
   unmaintained code to the public "as is" — confirm the disclaimer is effective
   against downstream users in consumer-protection jurisdictions (EU, etc.).

4. **Patent grant (Section 7).** Confirm scope and the litigation-termination
   clause are consistent with the chosen Change License's own patent terms
   (MPL-2.0, GPL-3.0, AGPL-3.0 each handle patents differently).

5. **Trademark / badge use.** The plan keeps the license text CC0 but the name
   and badge as marks. Confirm this split is enforceable and decide whether to
   register the mark.

## Open design questions (decide with counsel)

- Should there be a **maximum** Sunset date as a backstop (like BSL's 4-year cap),
  so the promise holds even if the dormancy detection somehow never fires?
- Should prior **purchasers** get any rights *before* public Sunset (e.g. a head
  start), or is fully-public-on-trigger the final answer? (Current draft: fully
  public.)
- Jurisdiction / governing-law clause — currently omitted; add one?

## Not legal advice

These notes were drafted by a non-lawyer to scope the review, not to substitute
for it.
