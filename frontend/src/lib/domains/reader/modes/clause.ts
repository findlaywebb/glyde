/**
 * Clause-window derivation for the Focus and Flow chunk views — R-MODES owns this file.
 *
 * A clause is the run of words between pause terminators. The parser RETAINS punctuation in
 * `token.text`, so a clause boundary is a word whose text ends with a terminator (`, ; : . ! ? …`),
 * allowing for trailing closing quotes/brackets. Pure and node-testable: given the full word stream
 * and the engine's current `wordIndex`, it returns the half-open window `[start, end)` of the clause
 * containing that word. `Focus.svelte` renders exactly this window; `Flow.svelte`'s guided/fading
 * variants render it with per-word read/future treatments.
 *
 * What it does NOT do: it reads no pauses from the IR (the engine already folded those into dwell)
 * and computes no pacing — clause structure is derived purely from the retained terminators in the
 * text, so a mode view needs only `words` + `wordIndex`, never the segment timeline.
 */
import type { TokenView } from '../types';

/**
 * A clause-closing terminator, optionally trailed by closing quotes/brackets.
 *
 * The character class is the pause terminator set the parser retains (`, ; : . ! ? …`, the last
 * being the U+2026 ellipsis); the trailing class swallows closing wrappers so `word."` or `end!)`
 * still register as clause ends (covers ASCII `" ' ) ]` and the curly U+2019/U+201D quotes).
 */
const CLAUSE_END = /[,;:.!?…]['")\]’”]*$/;

/** A half-open clause window `[start, end)` into the word stream. */
export interface ClauseWindow {
	/** Index of the first word of the clause. */
	start: number;
	/** Index one past the last word of the clause (exclusive). */
	end: number;
}

/** Whether a word's text closes a clause (ends with a terminator, allowing trailing wrappers). */
export function endsClause(text: string): boolean {
	return CLAUSE_END.test(text);
}

/**
 * The clause window containing `wordIndex`, derived from the retained terminators in `words`.
 *
 * `wordIndex` is clamped into range (so a past-the-end engine position still yields the final
 * clause); an empty stream yields an empty window. `start` is the word after the previous
 * clause-ending word (or 0); `end` is one past the next clause-ending word at or after `wordIndex`
 * (or the stream length when no terminator follows).
 */
export function clauseAt(words: TokenView[], wordIndex: number): ClauseWindow {
	const n = words.length;
	if (n === 0) return { start: 0, end: 0 };
	const i = Math.max(0, Math.min(wordIndex, n - 1));

	let start = 0;
	for (let k = i - 1; k >= 0; k--) {
		const w = words[k];
		if (w && endsClause(w.text)) {
			start = k + 1;
			break;
		}
	}

	let end = n;
	for (let k = i; k < n; k++) {
		const w = words[k];
		if (w && endsClause(w.text)) {
			end = k + 1;
			break;
		}
	}

	return { start, end };
}
