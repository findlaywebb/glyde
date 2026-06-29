# <Project / proposal name> — one-pager

- **Audience:** <who reads this — exec sponsor / budget owner / customer leadership>
- **Date:** YYYY-MM-DD · **Author:** <name>

> Written for a non-technical decision-maker. Lead with the outcome. Quantify, don't adjective. Name the downside — it's what makes the upside believable. Keep it to one page. NB: jargon that doesn't change their decision gets cut or defined in five words.

## The outcome (one line)

What this does and why it matters, in a sentence a busy reader gets on the first pass.

> e.g. "Auto-drafts the first reply to ~70% of support tickets, cutting average handle time ~30% while a human still reviews and sends."

## The problem

What hurts today, and what it costs us (time / money / risk / missed opportunity). Two or three sentences. Make the pain concrete and, where you can, numbered.

## The proposed approach

What we'd build, in plain terms — the *decision*, not the mechanism. One short paragraph. A diagram helps even non-technical readers; embed a simple one if it clarifies. Remember: the model is one component in a system we build and measure, not a magic box.

## Trade-offs (what we're choosing, and what we'd give up)

Honest, brief. A sceptical reader trusts the proposal that names its own costs.

- **We chose this because:** <the binding reason>
- **The alternative was:** <option not taken> — <why not>
- **What we give up:** <the real downside, stated plainly>

## Cost and latency

The numbers, or an honest "we'll confirm with a pilot".

- **Cost:** ~$<x> per <unit>, ~$<y>/month at expected volume
- **Speed:** responses in ~<n> seconds (or "overnight batch" / "real-time")
- **Build effort:** ~<n> weeks for a thin pilot; <n> for production

## Risks and how we manage them

- **<Risk 1>** (e.g. wrong ~1 in 20 times) → <mitigation: human reviews low-confidence cases>
- **<Risk 2>** (e.g. data handling) → <mitigation>
- **How we'll know it's working:** <the success metric we'll measure — see build-evals>

## The ask

The single decision or resource you want from the reader. Be specific.

> e.g. "Approve a 3-week pilot on the billing ticket queue, with a go/no-go review against an 80%-resolution bar."
