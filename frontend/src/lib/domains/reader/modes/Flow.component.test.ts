import { render } from '@testing-library/svelte';
import { beforeEach, describe, expect, it } from 'vitest';
import Flow from './Flow.svelte';
import type { Mode, ModeProps, ReaderState, TokenView } from '../types';

/** A word `TokenView` for fixtures. */
function word(text: string): TokenView {
	return { text, kind: 'word', emphasis: 'none' };
}

/** Assert a queried element exists and narrow it (avoids `!` under noUncheckedIndexedAccess). */
function must<T extends Element>(el: T | null): T {
	if (el === null) throw new Error('expected element to exist');
	return el;
}

/** The `.fw` word spans as a definite-length array of elements. */
function fwSpans(container: HTMLElement): HTMLElement[] {
	return Array.from(container.querySelectorAll<HTMLElement>('.fw'));
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

const WORDS = ['the', 'quick', 'brown', 'fox', 'jumps'].map(word);

/** Mount `Flow` at a word position in a given mode. */
function mountFlow(mode: Mode, wordIndex: number) {
	const props: ModeProps = {
		mode,
		state: readerState({ wordIndex, wordCount: WORDS.length }),
		words: WORDS
	};
	return render(Flow, props);
}

beforeEach(() => {
	stubReducedMotion(false);
});

describe('Flow guided sweep', () => {
	it('renders every word and tracks the current position', () => {
		const { container } = mountFlow('guided', 2);
		const spans = fwSpans(container);
		expect(spans).toHaveLength(WORDS.length);
		expect(container.querySelector('[data-mode="guided"]')).not.toBeNull();

		const cur = at(spans, 2);
		// The current word carries the `cur` marker class (its underline is styled in CSS).
		expect(cur.className).toContain('cur');
		expect(cur.getAttribute('data-flow-state')).toBe('cur');
	});

	it('separates words with real whitespace so the line can wrap', () => {
		const { container } = mountFlow('guided', 0);
		// Each word keeps a trailing space (a runtime expression survives compile-time trimming),
		// so words are visually separated and the inline spans have line-break opportunities.
		expect(at(fwSpans(container), 0).textContent).toBe('the ');
		expect(must(container.querySelector('.flow-content')).textContent).toContain(
			'the quick brown fox jumps'
		);
	});

	it('marks already-read words and leaves the road ahead un-read', () => {
		const { container } = mountFlow('guided', 2);
		const spans = fwSpans(container);
		expect(at(spans, 0).getAttribute('data-flow-state')).toBe('read');
		expect(at(spans, 1).getAttribute('data-flow-state')).toBe('read');
		expect(at(spans, 1).className).toContain('read');
		expect(at(spans, 3).getAttribute('data-flow-state')).toBe('ahead');
		expect(at(spans, 4).getAttribute('data-flow-state')).toBe('ahead');
	});
});

describe('Flow fading trail', () => {
	it('marks read words for the fade-out and keeps the fading data-mode', () => {
		const { container } = mountFlow('fading', 3);
		expect(container.querySelector('[data-mode="fading"]')).not.toBeNull();
		const spans = fwSpans(container);
		for (let i = 0; i < 3; i++) {
			expect(at(spans, i).className).toContain('read');
		}
		expect(at(spans, 3).className).toContain('cur');
		expect(at(spans, 4).className).not.toContain('read');
	});
});

describe('Flow reduced motion', () => {
	it('flags the motion gate when prefers-reduced-motion is set', () => {
		stubReducedMotion(true);
		const { container } = mountFlow('fading', 2);
		// `.reduced` switches off the opacity transition (the only animation), so a reduced-motion
		// reader gets the instant outcome with no fade travel.
		expect(must(container.querySelector('.flow')).className).toContain('reduced');
	});

	it('leaves the transition on when reduced motion is not set', () => {
		stubReducedMotion(false);
		const { container } = mountFlow('fading', 2);
		expect(must(container.querySelector('.flow')).className).not.toContain('reduced');
	});
});
