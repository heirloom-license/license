<p align="center">
  <img src="badges/heirloom-badge.svg" alt="Heirloom License" height="40">
</p>

<h1 align="center">The Heirloom License</h1>

<p align="center">
  <em>Commercial software that outlives its maker.</em><br>
  A source-available commercial license that automatically becomes open source
  if the developer abandons it.
</p>

---

## Why this exists

When you buy software from an indie developer, you take a quiet risk: if they
disappear, your software stops getting updates and you never see the source. The
Heirloom License removes that risk with a binding, self-executing promise — **if
the developer goes dormant, the code becomes open source for everyone, forever.**

It's modeled on the [Business Source License](https://mariadb.com/bsl-faq-mariadb/)
and [Functional Source License](https://fsl.software/), with one key change: those
convert on a **fixed calendar date**; the Heirloom License converts on an
**abandonment condition**, detected by a dead-man's switch.

## The 60-second version

| | |
|---|---|
| **While active** | Normal paid commercial product. Use it, don't resell or clone it. |
| **Trigger** | No maintenance signal for the dormancy window (default 12 mo) **and** no support response in 90 days. |
| **On Sunset** | Full source published publicly under the Change License (default MPL-2.0). Irrevocable. |

Read the [plain-English summary](SUMMARY.md) or the [full license](LICENSE.md).

## Adopt it in four steps

1. **Pick your parameters.** Change License (default `MPL-2.0`), dormancy window
   (default `12mo`), and your repository URL.
2. **Add the license.** Copy [`LICENSE.md`](LICENSE.md) into your project and fill
   in the Parameters table.
3. **Install the switch.** Drop in the reference
   [dead-man's-switch workflow](reference/.github/workflows/dead-mans-switch.yml)
   and keep it alive with your normal commits or a manual heartbeat.
4. **Show the badge.** Add the [badge](badges/) to your README and About box so
   buyers can see the promise.

Full walkthrough (with safe testing and hardening): **[SETUP.md](SETUP.md)**.

Then [submit your app](https://github.com/heirloom-license/license/issues/new?template=adopter-submission.yml) to the **[adopters directory](https://heirloomlicense.org/adopters)** — the bot verifies your badge and opens the PR.

## The identifier convention

Like SPDX and FSL, the license encodes its parameters in the name:

```
HL-1.0-<ChangeLicense>-<DormancyWindow>
```

Examples:

- `HL-1.0-MPL2.0-12mo` — recommended default
- `HL-1.0-GPL3.0-24mo` — stronger copyleft, longer window
- `HL-1.0-AGPL3.0-6mo` — network copyleft, short window

## Repository structure

```
heirloom-license/
├── LICENSE.md                 The license text v1.0 (parameterized)
├── SUMMARY.md                 Plain-English explanation
├── README.md                  This file
├── SETUP.md                   Step-by-step dead-man's switch setup guide
├── adopters.yml               Source of truth for the adopters directory
├── ADOPTERS.md                Generated adopters table (do not edit by hand)
├── LEGAL-REVIEW.md            What still needs a lawyer, and open questions
├── ROADMAP.md                 Website, funding, launch, governance plan
├── badges/                    SVG badge + usage rules
├── templates/
│   └── HL-1.0-MPL2.0-12mo.md  Pre-filled example for the default variant
├── reference/
│   └── .github/workflows/
│       └── dead-mans-switch.yml   Drop-in auto-publish workflow
└── site/
    └── index.html             Landing page for heirloomlicense.org
```

## License of the license

The Heirloom License text itself is dedicated to the public domain under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Copy it, adopt it,
fork it. The **"Heirloom License" name and badge** are project marks — use them
only for software released under an unmodified version of the license, so the
badge keeps meaning one specific thing.

## Status

`v1.0-draft` — community draft, pending legal review. See [`LEGAL-REVIEW.md`](LEGAL-REVIEW.md).
Feedback and red-lines welcome via issues.
