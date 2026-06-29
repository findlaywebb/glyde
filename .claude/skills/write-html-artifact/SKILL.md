---
name: write-html-artifact
description: Use when the deliverable is better seen than read — a spec/plan with side-by-side options, a code review with severity-coloured findings, a research report with charts or SVG diagrams, a design prototype with live sliders, or a custom mini-tool (form with copy-as-JSON / copy-as-prompt export). Triggers include "make this an HTML page", "render this as HTML", "build a little tool/dashboard for this", "show the options side by side", "make this interactive", "I want to tweak this and feed it back", "a page I can share". Default output is still markdown; reach here only when visual density, interactivity, or a single shareable file earns the extra tokens. Embodies one self-contained file, with a path back to Claude.
---

# write-html-artifact

Claude defaults to markdown for every artifact. This skill makes Claude *choose HTML when it earns its place* and produce a **single self-contained `.html` file** that opens by double-click — richer than markdown (tables, CSS, SVG, charts, interactive controls) and, crucially, closing the loop back to Claude via export buttons. (Anthropic blog, "the unreasonable effectiveness of HTML for Claude Code".)

## The one principle

**One self-contained file, with a path back to Claude.** Everything inline (CSS, JS, data, images as data-URIs) so the file works offline, over `file://`, and when emailed or hosted untouched. And because the whole point is staying *in the loop*, an interactive artifact should offer a way for the user's edits to return to you — but **fit the affordance to the artifact** (see "The path back", below). The reflexive page-top "copy as prompt" button is the trap, not the goal.

## When to use

Reach for HTML when at least one of these is the actual win — otherwise markdown is correct:
- **Density** — tabular data, CSS layout, SVG illustration, or a chart says it better than ASCII or a markdown table (research reports, data summaries).
- **Comparison** — several options shown *side by side* (spec variations, design alternatives, before/after).
- **Interactivity** — sliders/knobs to tune a parameter, toggles, tabs, a filterable table, a live preview (design prototypes, "what-if" explorations).
- **Shareability** — a single file the user can open, host, or send, and a non-technical reader will actually engage with.
- **A purpose-built mini-tool** — a form or editor that exports its state (copy as JSON / as prompt) so the round-trip comes back to you.

## When NOT to use

- The destination is a **markdown renderer** (Jira ticket, GitHub PR/README, a `.md` in the repo, a Slack message) → write markdown; HTML renders as raw tags there. This is the most common misfire.
- A quick answer, a short plan, anything under ~1 screen → markdown. HTML's token cost only pays off above a threshold of richness.
- The question is **doc structure / mode** (tutorial vs how-to vs reference) → use `write-docs`. That decides *what the doc is*; this skill is *what format it ships in*. They compose — render a how-to as an HTML artifact when density/interactivity earns it.
- The content must land for **two audiences at once** (engineer + stakeholder), or it's an ADR / architecture diagram → use `technical-writeup` for the altitude split; come here only to render the result as a shareable page.
- It's a **real web app / production frontend** (build step, backend, framework, multi-page) → that's software, not an artifact. This skill is one throwaway-grade file.

## The procedure

1. **Confirm HTML earns it.** Name which win above applies. If none, stop and write markdown.
2. **Start from `templates/artifact.html`** — a self-contained base (inline reset CSS, neutral light/dark via `prefers-color-scheme`, the FMP brand themes, system font stack, item-level + whole-state export wiring). Don't hand-roll the chrome each time.
3. **Inline everything.** Data as a `<script>` object or `<script type="application/json">`; images as `data:` URIs; no `<link>`/`<script src>` to any CDN. (See gotchas — this is the trap that bites.)
4. **Add the right path back to Claude** (see "The path back"). Whole-state export, item-level copy-prompt, or nothing — chosen, not reflexive.
4b. **Theme for the audience.** Neutral auto light/dark is the default. For something shared inside FMP, set `<html data-theme="fmp">` (navy bg, on-brand dark — the usual choice) or `data-theme="fmp-light">` (cream/navy, matches the slide deck). The `--fmp-*` accent tokens are available in any theme for chart series and severity colours.
4c. **Code blocks come pre-styled.** Any `<pre>` renders Monokai-dimmed and gets a hover *Copy* button automatically; the template's CSS comment documents the `t-*` token classes for highlighting. No CDN highlighter (see gotchas).
5. **Escape any embedded code/user content** before injecting into HTML (`&` `<` `>`), or use `textContent`/`<pre>`. Rendering a diff or code block unescaped breaks layout and is an injection vector.
6. **Deliver, don't ambush.** Write the file, then surface it with `SendUserFile` (or offer `open <file>`). Don't auto-open a browser unprompted.
7. **Sanity-check it renders** — open it yourself if a browser tool is available, or at minimum validate the HTML is well-formed and the inlined data parses.

## The path back

The artifact should let the user's engagement return to you — but the *form* must fit, and a generic page-top "copy as prompt" button is usually the wrong one. Pick:

- **Whole-state export** (`copy-as-JSON` / download) — when the user tweaks the page *as a whole* and you want it all back (a tuned config, an edited form, a prototype's slider state). Honest because it exports state, not a fake prompt.
- **Item-level copy-prompt** — when the artifact is a *list of discrete things* and the natural next step is acting on *one* (a review finding → "open a fix for this", an option → "go with this one", a task → "draft this"). Put the button **on the item**, make the prompt **specific to that item**, and **surface the prompt text** (`title=` on hover, or rendered inline) so the user sees what they're about to send. A hidden generic placeholder is noise.
- **Nothing** — a read-only one-shot report (a data summary, a chart) may have no meaningful round-trip. That's fine; don't bolt one on for form's sake.

## Gotchas

- **Don't inline a syntax highlighter for the dimmed look.** The template's code blocks are Monokai-dimmed and copy-buttoned out of the box; "highlighting" is just `<span class="t-*">` token classes you apply when emitting the code. Reaching for highlight.js/Prism means inlining a tokenizer (kilobytes, against the throwaway-grade ethos) — only worth it for a page that is genuinely *about* showing lots of varied code. Otherwise hand-wrap the few tokens that matter, or leave the block plain on the dimmed base.
- **CDN links break the artifact.** A `<script src="https://cdn.tailwindcss.com">` or Google Fonts `<link>` looks fine on your machine and dies the moment the file is opened offline, over `file://`, or behind a corporate proxy — exactly when it's been shared. Inline the CSS; use the system font stack. If you genuinely need a chart lib, inline its minified source, don't link it.
- **`fetch()` of a sibling file fails under `file://`.** Loading `data.json` next to the HTML throws a CORS error when double-clicked (no server). Inline the data into the page instead — that's *why* it's one file.
- **Unescaped code content corrupts the page.** Embedding a diff, log, or user string containing `<`, `>`, `&` straight into innerHTML mangles rendering and opens XSS. Escape, or set via `textContent`.
- **Token cost is real above a threshold.** A big interactive page is genuinely expensive. The 1M window makes it affordable, not free — don't reflexively HTML-ify a three-line answer. The blog gives *no evidence* HTML improves outcomes; the honest benefit is the human staying in the loop, so only spend the tokens when that loop matters.
- **The reflexive page-top copy-prompt.** A header "copy as prompt" button that dumps the whole `DATA` blob with a placeholder "update it so that ..." fires on every artifact whether or not a whole-page round-trip is the next step, and hides what it sends. It's noise, not a path back. Use whole-state *export* (copy-as-JSON) for genuine whole-page tweaking; use item-level copy-prompt where acting on one item is the natural move; otherwise nothing. See "The path back".
- **The dead-end interactive artifact.** A *tool/prototype* the user is meant to tweak, with no way to feed changes back, throws away the two-way thesis. (A read-only report needs no path back — this gotcha is about the interactive case.)
- **No build step, no framework.** Reaching for React/Vite/npm turns a shareable file into a project nobody can open by double-clicking. Vanilla HTML/CSS/JS, one file.

## Anti-patterns

- **HTML where markdown belongs** — pasting `<table>` into a Jira ticket or GitHub PR. Check the destination renderer first.
- **The multi-file webapp** — `index.html` + `style.css` + `app.js` + a `node_modules`. The single-file constraint *is* the shareability.
- **External dependencies** — CDN scripts, web fonts, remote images. Inline or omit.
- **Decoration over information** — gradients and animation on a page whose job is to convey three numbers. Density and clarity are the point, not polish.
- **Auto-opening the browser** without asking, or dumping a 2000-line HTML blob into the chat instead of writing it to a file and sending it.

## Templates

- `templates/artifact.html` — the self-contained starting point: inline reset + neutral light/dark CSS, the opt-in `data-theme="fmp"` (on-brand dark) / `fmp-light` brand themes plus `--fmp-*` accent tokens, Monokai-dimmed code blocks with auto copy buttons (`t-*` token classes), system font stack, a responsive container, and both export shapes wired up (a page-level *copy-as-JSON* and a per-item *copy-prompt* whose text is visible via `title=`). Copy it, fill the body, inline your data, and **delete the export affordance you don't need**.
