# The Heirloom License — in plain English

*This summary is not the license. It explains the intent. The legal text in
`LICENSE.md` governs. Where they differ, the license wins.*

## The promise

You bought software from an indie developer. One day that developer might stop
working on it — life happens, companies fold, people move on. The usual fear is:
**when they go, your software dies with them.** No updates, no source, no way to
keep it alive.

The Heirloom License removes that fear. It is a commercial license with a
built-in promise: **if the developer truly abandons the software, it
automatically becomes open source for everyone — permanently.**

## How it works, in three sentences

1. **While the developer is active**, the software is a normal paid commercial
   product. You can use it, but you can't resell it or build a competitor from it.
2. **If the developer goes silent** — no updates and no support response for a set
   window (default 12 months) — the software automatically "Sunsets."
3. **On Sunset**, the full source code is released publicly under a strong
   open-source license (default MPL-2.0), so anyone can use it, fix it, fork it,
   and keep it alive forever. This is irrevocable.

## What "abandoned" means (it's objective on purpose)

We deliberately avoid fuzzy judgment calls. Sunset triggers only when **both**
are true:

- The developer hasn't posted any maintenance signal (a release, a commit, or a
  signed heartbeat) for the full dormancy window, **and**
- The developer hasn't answered a good-faith support request within 90 days.

A single update resets the clock. An active developer never triggers it. There's
no committee, no court, no one to petition — it's mechanical.

## What you can and can't do

**While active:** use and run it for any purpose except building a competing
product. Source may or may not be visible — that's the developer's choice and
doesn't change the promise.

**After Sunset:** everything the Change License allows — use, modify, and sell
commercially. The default Change License (MPL-2.0) is *share-alike*: you can
combine it with your own code, but improvements to the original files stay open.
Nobody can re-lock the abandoned code into a closed product. That's the point.

## Why share-alike and not MIT

If the Sunset code became MIT/permissive, the first company to grab it could
re-privatize it and the community promise would be hollow. Copyleft guarantees
the code, and every future improvement to it, stays in the open for good.

## For developers adopting it

You keep selling your product normally. You opt into a promise that costs you
nothing while you're active, and earns buyer trust immediately. You set three
values — your Change License, your dormancy window, and your repository — drop in
the reference dead-man's-switch, and display the badge. That's it.

## The honest caveat

A license is a promise; the dead-man's switch is the delivery mechanism. The
switch can be defeated by deleting the account or disabling it before
disappearing — so the *contract* (this license, legally binding) and the
*automation* (good-faith delivery) back each other up. Buyers trust the
combination, and the obligation to publish exists in the text whether or not the
automation fires.
