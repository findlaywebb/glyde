import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Rsvp from './Rsvp.svelte';
import { pivotTranslateX } from './measure';
import { pivotIndex } from '../cadence';
import type { ModeProps, ReaderState, TokenView } from '../types';

/** A word `TokenView` for fixtures. */
function word(text: string, emphasis: TokenView['emphasis'] = 'none'): TokenView {
	return { text, kind: 'word', emphasis };
}

/** A full `ReaderState` with overridable fields (every field defaulted so fixtures stay terse). */
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

/** Mount `Rsvp` over a token whose pivot index is the engine's Spritz bucket for its length. */
function mountWord(tok: TokenView, over: Partial<ReaderState> = {}) {
	const state = readerState({ token: tok, pivotIndex: pivotIndex(tok.text.length), ...over });
	const props: ModeProps = { mode: 'rsvp', state, words: [tok] };
	return render(Rsvp, props);
}

describe('Rsvp pivot glyph', () => {
	// The signature behaviour: the optimal-recognition-point glyph the engine chose is the one
	// marked red, across the full range of Spritz buckets (len 1 → 0 … len > 13 → 4).
	it.each([
		['I', 0],
		['cat', 1],
		['hello', 1],
		['wonderful', 2],
		['configuration', 3],
		['internationalization', 4]
	])('marks the ORP glyph for %s at bucket index %i', (text, expectedIndex) => {
		expect(pivotIndex(text.length)).toBe(expectedIndex);
		const { container } = mountWord(word(text));
		const mark = container.querySelector('[data-pivot]');
		expect(mark).not.toBeNull();
		expect(mark?.textContent).toBe(text[expectedIndex]);
		// The pivot glyph is the one reserved reading colour.
		expect(mark?.className).toContain('text-pivot');
	});

	it('splits the word so left + pivot + right reconstruct it exactly', () => {
		const { container } = mountWord(word('configuration'));
		const spans = container.querySelectorAll('.word .w > span');
		expect(spans).toHaveLength(3);
		const joined = Array.from(spans)
			.map((s) => s.textContent)
			.join('');
		expect(joined).toBe('configuration');
	});

	it('renders the full word text including retained punctuation', () => {
		const { container } = mountWord(word('end,'));
		expect(container.querySelector('.word .w')?.textContent).toBe('end,');
	});

	it('applies a measure-and-translate transform to the word layer', () => {
		const { container } = mountWord(word('configuration'));
		const wordEl = container.querySelector<HTMLElement>('.word');
		// The DOM measure ran (jsdom reports zero layout, so the translate is 0 — the mechanism,
		// not the pixel value, is what is assertable without a layout engine).
		expect(wordEl?.style.transform).toContain('translate(');
	});
});

describe('Rsvp emphasis', () => {
	it.each([['strong'], ['em'], ['code']] as const)(
		'renders %s emphasis distinctly on the streamed word',
		(emphasis) => {
			const { container } = mountWord(word('vivid', emphasis));
			expect(container.querySelector(`.word .w[data-em='${emphasis}']`)).not.toBeNull();
		}
	);
});

describe('pivotTranslateX (the centring maths)', () => {
	// The pivot glyph's centre must land on the container midpoint for any measured geometry.
	it('centres a glyph already on the midpoint to zero offset', () => {
		expect(pivotTranslateX(100, 40, 20)).toBe(0);
	});

	it('shifts a left-of-centre glyph rightwards onto the column', () => {
		expect(pivotTranslateX(100, 10, 10)).toBe(35);
	});

	it('shifts a right-of-centre glyph leftwards onto the column', () => {
		expect(pivotTranslateX(100, 80, 10)).toBe(-35);
	});
});

describe('Rsvp context rows', () => {
	it('renders the surrounding context words dimmed, in distinct above and below rows', () => {
		const { container } = mountWord(word('hello'), {
			contextBefore: [word('say')],
			contextAfter: [word('there')]
		});
		const above = container.querySelector('.ctx-above');
		const below = container.querySelector('.ctx-below');
		expect(above?.textContent?.trim()).toBe('say');
		expect(below?.textContent?.trim()).toBe('there');
		expect(above?.className).toContain('text-reading-dim');
		expect(below?.className).toContain('text-reading-dim');
	});

	it('places the context text on its own .ctx-text layer separate from the word band', () => {
		// The geometry fix: the small text lives on .ctx-text inside a zero-height .ctx-row whose
		// offset is in stage em (not the shrunk context font), so the rows clear the word vertically.
		// Pixel placement is screenshot-verified; here we assert the structural split is in place.
		const { container } = mountWord(word('hello'), {
			contextBefore: [word('say')],
			contextAfter: [word('there')]
		});
		expect(container.querySelector('.ctx-above .ctx-text')?.textContent).toBe('say');
		expect(container.querySelector('.ctx-below .ctx-text')?.textContent).toBe('there');
		// The context rows are siblings of the word band, never nested inside it (so they cannot
		// reflow the pivot).
		expect(container.querySelector('.word-wrap .ctx-row')).toBeNull();
	});

	it('omits the context rows when there is no context window', () => {
		const { container } = mountWord(word('hello'));
		expect(container.querySelector('.ctx-above')).toBeNull();
		expect(container.querySelector('.ctx-below')).toBeNull();
	});
});
