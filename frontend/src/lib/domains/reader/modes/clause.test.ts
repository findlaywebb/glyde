import { describe, expect, it } from 'vitest';
import { clauseAt, endsClause } from './clause';
import type { TokenView } from '../types';

/** A word `TokenView` whose text is verbatim (punctuation retained, as the parser emits it). */
function word(text: string): TokenView {
	return { text, kind: 'word', emphasis: 'none' };
}

describe('endsClause', () => {
	it.each([
		['fox,', true],
		['ran.', true],
		['list:', true],
		['wait;', true],
		['really?', true],
		['stop!', true],
		['well…', true],
		['quote."', true],
		['(end!)', true],
		['plain', false],
		['mid-word', false],
		['', false]
	])('treats %j as clause-ending=%s', (text, expected) => {
		expect(endsClause(text)).toBe(expected);
	});
});

describe('clauseAt', () => {
	// Two clauses: "The quick brown fox," (0..3) then "then it ran." (4..6).
	const words = ['The', 'quick', 'brown', 'fox,', 'then', 'it', 'ran.'].map(word);

	it('returns the first clause for an index inside it', () => {
		expect(clauseAt(words, 0)).toEqual({ start: 0, end: 4 });
		expect(clauseAt(words, 2)).toEqual({ start: 0, end: 4 });
	});

	it('includes the terminating word as the clause end (exclusive bound past it)', () => {
		// wordIndex on the comma word itself still belongs to the clause it closes.
		expect(clauseAt(words, 3)).toEqual({ start: 0, end: 4 });
	});

	it('starts the next clause after the previous terminator', () => {
		expect(clauseAt(words, 4)).toEqual({ start: 4, end: 7 });
		expect(clauseAt(words, 5)).toEqual({ start: 4, end: 7 });
		expect(clauseAt(words, 6)).toEqual({ start: 4, end: 7 });
	});

	it('clamps an out-of-range index to the final clause', () => {
		expect(clauseAt(words, 99)).toEqual({ start: 4, end: 7 });
		expect(clauseAt(words, -5)).toEqual({ start: 0, end: 4 });
	});

	it('treats a stream with no terminators as a single clause', () => {
		const plain = ['hello', 'there', 'friend'].map(word);
		expect(clauseAt(plain, 1)).toEqual({ start: 0, end: 3 });
	});

	it('returns an empty window for an empty stream', () => {
		expect(clauseAt([], 0)).toEqual({ start: 0, end: 0 });
	});
});
