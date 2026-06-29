# Explanation — understanding-oriented

Explanation is discursive, contextual writing that deepens **understanding**: why the system is built this way, what alternatives were weighed, what the trade-offs are. The reader is *studying*, reading at leisure — not mid-task, not under deadline. (Diátaxis: theory + acquisition.)

## The discipline

- **Why, not how.** Explanation gives reasons, context, history, connections. It does not give steps (how-to) or facts to look up (reference) or a first-run (tutorial).
- **Allowed to be discursive.** This is the one mode where you can wander a little: discuss design forces, draw analogies, compare to alternatives, admit trade-offs. It's read by someone who *wants* the fuller picture.
- **Make the trade-offs explicit.** The most valuable explanation names what was given up, not just what was gained. "We chose X over Y because Z, accepting the cost of W." This is where it overlaps with `technical-writeup`'s trade-off discipline.
- **Connect things.** Explanation is where the reader learns how the pieces relate, why the boundaries are where they are, how this fits the bigger system.
- **Bounded scope, even so.** Discursive isn't unbounded — one topic of understanding per document. "Why our auth uses short-lived tokens" is a topic; "everything about auth" is not.

## Shape

Looser than the other modes, but typically:
1. The question or topic ("Why does X work this way?").
2. The context / forces at play.
3. The approach taken and the alternatives considered.
4. The trade-offs accepted, named honestly.
5. Connections to related concepts / docs.

## The tell that you've drifted

If you find yourself writing numbered steps, you've slipped into a how-to. If you're listing every config key, that's reference. Explanation is the prose that makes the *other three* make sense — keep it to understanding.
