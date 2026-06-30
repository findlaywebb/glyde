import { render } from '@testing-library/svelte';
import { beforeEach, describe, expect, it } from 'vitest';
import Flow from './Flow.svelte';
import type { Mode, ModeProps, ReaderState, TokenView } from '../types';

/** A word `TokenView` for fixtures (punctuation retained verbatim, as the parser emits it). */
function word(text: string, emphasis: TokenView['emphasis'] = 'none'): TokenView {
	return { text, kind: 'word', emphasis };
}

/** Assert a queried element exists and narrow it (avoids `!` under noUncheckedIndexedAccess). */
function must<T extends Element>(el: T | null): T {
	if (el === null) throw new Error('expected element to exist');
	return el;
}

/** The rendered clause-word spans, in document order. */
function fwSpans(container: HTMLElement): HTMLElement[] {
	return Array.from(container.querySelectorAll<HTMLElement>('.fw'));
}

/** The text of each rendered clause word. */
function fwTexts(container: HTMLElement): string[] {
	return fwSpans(container).map((s) => s.textContent?.trim() ?? '');
}

/** Index into an array, asserting the element is present. */
function at<T>(arr: T[], i: number): T {
	const v = arr[i];
	if (v === undefined) throw new Error(`expected an element at index ${i}`);
	return v;
}

/** Stub `prefers-reduced-motion` for the next mount (the gate is read once at component init). */
function stubReducedMotion(reduce: boolean): void {
	window.matchMedia = (query: string) =>
		({
			matches: reduce && query.includes('reduce'),
			media: query,
			onchange: null,
			addEventListener: () => {},
			removeEventListener: () => {},
			addListener: () => {},
			removeListener: () => {},
			dispatchEvent: () => false
		}) as MediaQueryList;
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

/** Mount `Flow` at a word position in a given mode. */
function mountFlow(mode: Mode, wordIndex: number, words: TokenView[] = WORDS) {
	const props: ModeProps = {
		mode,
		state: readerState({ wordIndex, wordCount: words.length }),
		words
	};
	return render(Flow, props);
}

beforeEach(() => {
	stubReducedMotion(false);
});

describe('Flow renders only the current clause (no skip-ahead)', () => {
	it('keeps the flow root and the mode marker', () => {
		const { container } = mountFlow('guided', 0);
		expect(container.querySelector('.flow')).not.toBeNull();
		expect(container.querySelector('[data-mode="guided"]')).not.toBeNull();
	});

	it('never renders words from a future clause', () => {
		const { container } = mountFlow('guided', 1);
		const texts = fwTexts(container);
		// The next clause ("jumps", "over.") must not be present anywhere in the DOM.
		expect(texts).not.toContain('jumps');
		expect(texts).not.toContain('over.');
		expect(container.textContent).not.toContain('jumps');
	});

	it('swaps discretely to the next clause once the position crosses the terminator', () => {
		const { container } = mountFlow('fading', 4);
		const texts = fwTexts(container);
		expect(texts).toContain('jumps');
		expect(texts).toContain('over.');
		// The previous clause is gone entirely.
		expect(container.textContent).not.toContain('brown');
	});
});

describe('Flow guided sweep', () => {
	it('removes already-read words and marks the current word', () => {
		const { container } = mountFlow('guided', 2);
		const texts = fwTexts(container);
		// Read words ("the", "quick") are removed from the DOM, not merely dimmed.
		expect(texts).not.toContain('the');
		expect(texts).not.toContain('quick');
		// The current word and the remaining road within the clause stay.
		expect(texts).toEqual(['brown', 'fox,']);
		const cur = must(container.querySelector('.fw[data-flow-state="cur"]'));
		expect(cur.textContent?.trim()).toBe('brown');
	});
});

describe('Flow fading trail', () => {
	it('keeps read words (to fade out), marks the current, and dims the road ahead', () => {
		const { container } = mountFlow('fading', 2);
		const spans = fwSpans(container);
		// All four words of the clause remain in the DOM.
		expect(fwTexts(container)).toEqual(['the', 'quick', 'brown', 'fox,']);
		expect(at(spans, 0).getAttribute('data-flow-state')).toBe('read');
		expect(at(spans, 1).getAttribute('data-flow-state')).toBe('read');
		expect(at(spans, 2).getAttribute('data-flow-state')).toBe('cur');
		expect(at(spans, 3).getAttribute('data-flow-state')).toBe('ahead');
	});
});

describe('Flow emphasis', () => {
	it('renders agent emphasis on the clause words', () => {
		const words = [word('plain'), word('vivid', 'strong'), word('done.')];
		const { container } = mountFlow('guided', 0, words);
		expect(container.querySelector(`.fw .w[data-em='strong']`)).not.toBeNull();
	});
});

describe('Flow reduced motion', () => {
	it('flags the motion gate when prefers-reduced-motion is set', () => {
		stubReducedMotion(true);
		const { container } = mountFlow('fading', 2);
		expect(must(container.querySelector('.flow')).className).toContain('reduced');
	});

	it('leaves the transition on when reduced motion is not set', () => {
		stubReducedMotion(false);
		const { container } = mountFlow('fading', 2);
		expect(must(container.querySelector('.flow')).className).not.toContain('reduced');
	});
});
