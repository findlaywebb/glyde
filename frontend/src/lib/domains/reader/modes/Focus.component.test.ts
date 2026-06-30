import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Focus from './Focus.svelte';
import type { ModeProps, ReaderState, TokenView } from '../types';

/** A word `TokenView` for fixtures (punctuation retained verbatim, as the parser emits it). */
function word(text: string, emphasis: TokenView['emphasis'] = 'none'): TokenView {
	return { text, kind: 'word', emphasis };
}

/** A full `ReaderState` with overridable fields. */
function readerState(over: Partial<ReaderState>): ReaderState {
	return {
		token: null,
		pivotIndex: 0,
		dwellMs: 0,
		contextBefore: [],
		contextAfter: [],
		wordIndex: 0,
		wordCount: 0,
		isPlaying: false,
		activeBlock: null,
		blockAhead: false,
		atEnd: false,
		remainingMs: 0,
		blockNotches: [],
		...over
	};
}

// Two clauses: "the quick brown fox," (0..3) and "jumps over." (4..5).
const WORDS = ['the', 'quick', 'brown', 'fox,', 'jumps', 'over.'].map((w) => word(w));

/** The text of each rendered clause word, in document order. */
function clauseTexts(container: HTMLElement): string[] {
	return Array.from(container.querySelectorAll<HTMLElement>('.clause .w')).map(
		(s) => s.textContent?.trim() ?? ''
	);
}

/** Mount `Focus` at a word position. */
function mountFocus(wordIndex: number, words: TokenView[] = WORDS) {
	const props: ModeProps = {
		mode: 'focus',
		state: readerState({ wordIndex, wordCount: words.length }),
		words
	};
	return render(Focus, props);
}

describe('Focus clause window', () => {
	it('renders only the current clause, with no past or future clause text', () => {
		const { container } = mountFocus(1);
		expect(clauseTexts(container)).toEqual(['the', 'quick', 'brown', 'fox,']);
		// Nothing from the next clause is anywhere in the DOM — future is hidden, not just off-screen.
		expect(container.textContent).not.toContain('jumps');
		expect(container.textContent).not.toContain('over.');
	});

	it('keeps the full punctuation of the clause words', () => {
		const { container } = mountFocus(3);
		expect(clauseTexts(container)).toContain('fox,');
	});

	it('swaps discretely to the next clause once the position crosses the terminator', () => {
		const { container } = mountFocus(5);
		expect(clauseTexts(container)).toEqual(['jumps', 'over.']);
		// The previous clause is removed entirely.
		expect(container.textContent).not.toContain('brown');
		expect(container.textContent).not.toContain('fox,');
	});

	it('clamps a past-the-end position to the final clause', () => {
		const { container } = mountFocus(99);
		expect(clauseTexts(container)).toEqual(['jumps', 'over.']);
	});
});

describe('Focus emphasis', () => {
	it('renders agent emphasis on the clause words', () => {
		const words = [word('plain'), word('vivid', 'strong'), word('done.')];
		const { container } = mountFocus(0, words);
		expect(container.querySelector(`.clause .w[data-em='strong']`)).not.toBeNull();
	});
});
