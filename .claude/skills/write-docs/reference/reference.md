# Reference — information-oriented

Reference is the dry, accurate, exhaustive technical description: API surface, config keys, CLI flags, schema fields. The reader is *working* and needs to **look up a fact fast**. (Diátaxis: theory + application.)

## The discipline

- **Mirror the product, not the journey.** Reference is structured like the thing it describes — one section per module/endpoint/command — not like a story. The reader arrives knowing what they're looking for; let them find it by structure.
- **Describe, don't instruct or explain.** State what each thing *is* and does. No "you should", no rationale, no tutorials. Rationale belongs in explanation; tasks belong in how-tos. Link out.
- **Exhaustive and accurate over readable.** Every parameter, every default, every return value, every error. Omissions are the failure mode — a reference you can't trust for completeness is useless.
- **Consistency is the readability.** Same structure for every entry (name, type, default, description, example). Predictability lets the reader scan. A consistent dull format beats varied prose.
- **Examples are minimal and illustrative**, showing the shape, not teaching.

## Shape

Per item, a consistent block:
- **Name / signature**
- **Type** (and default, if applicable)
- **Description** — one or two precise sentences
- **Parameters / fields** — table: name, type, required?, default, meaning
- **Returns / emits** — type and meaning
- **Errors** — what can go wrong and the condition
- **Example** — one minimal, correct snippet

## The tell that you've drifted

If a reference entry contains "first you'll want to…" (how-to) or "the reason we designed it this way…" (explanation), it's in the wrong mode. Cut it and link to the doc that owns it. Reference answers *what*, never *why* or *how-to-accomplish*.
