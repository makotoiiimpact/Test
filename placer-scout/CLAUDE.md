# placer-scout: standing rules from the owner

Approved by the owner on 2026-10-31 (rules wizard). These replace the earlier "ask before any git work" rule for this project only.

## Git
- When a piece of placer-scout work is finished, commit and push it to the `placer-scout-plan` branch without asking, then tell the owner the commit id.
- Never commit to or push `main`, never force-push, never rewrite history, never open a pull request, and never create a GitHub repository without asking first.
- An automatic commit may include `src/`, `out/`, `IMPLEMENTATION_PLAN.md`, this file, and small cited-evidence files (under about 1 MB, force-added from `data/`).
- Downloaded data in `data/` and `cache/` stays out of git (see `.gitignore`).

## Pages (Artifacts)
- Private pages for this project (review pages, field plans, maps) may be published or updated without asking; give the owner the link.
- Never share a page with anyone else; sharing is the owner's call.

## Unchanged stop conditions
- Stop and ask if a source needs a login or API key (give the exact Terminal command; never ask for a secret).
- Stop if downloads would pass 10 GB or memory becomes a problem.
- Mark a layer missing rather than invent data; every fact needs a traceable source.
