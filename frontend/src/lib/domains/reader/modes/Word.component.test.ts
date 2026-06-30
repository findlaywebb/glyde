import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Word from './Word.svelte';
import type { TokenView } from '../types';

/** A token with a given emphasis (defaulting to none). */
function token(text: string, emphasis: TokenView['emphasis'] = 'none'): TokenView {
	return { text, kind: 'word', emphasis };
}

describe('Word emphasis rendering', () => {
	it('renders the verbatim text with no emphasis marker for a plain word', () => {
		const { container } = render(Word, { token: token('plain') });
		const w = container.querySelector('.w');
		expect(w?.textContent).toBe('plain');
		// `none` still tags data-em (the CSS simply matches no rule), so styling never leaks.
		expect(w?.getAttribute('data-em')).toBe('none');
	});

	it.each([['strong'], ['em'], ['code']] as const)(
		'marks %s emphasis distinctly via data-em',
		(emphasis) => {
			const { container } = render(Word, { token: token('word', emphasis) });
			expect(container.querySelector(`.w[data-em='${emphasis}']`)).not.toBeNull();
		}
	);

	it('keeps punctuation in the rendered text', () => {
		const { container } = render(Word, { token: token('end!,') });
		expect(container.querySelector('.w')?.textContent).toBe('end!,');
	});

	it('splits the word around the pivot glyph when a pivot index is given', () => {
		const { container } = render(Word, { token: token('configuration'), pivot: 3 });
		const mark = container.querySelector('[data-pivot]');
		expect(mark?.textContent).toBe('f'); // index 3 of "configuration"
		expect(mark?.className).toContain('text-pivot');
		// The three inner spans reconstruct the word exactly (no stray whitespace).
		const spans = container.querySelectorAll('.w > span');
		expect(spans).toHaveLength(3);
		expect(
			Array.from(spans)
				.map((s) => s.textContent)
				.join('')
		).toBe('configuration');
	});

	it('applies emphasis to a pivot-split word too', () => {
		const { container } = render(Word, { token: token('bold', 'strong'), pivot: 1 });
		expect(container.querySelector(`.w[data-em='strong']`)).not.toBeNull();
		expect(container.querySelector('[data-pivot]')?.textContent).toBe('o');
	});

	it('renders the whole word when the pivot index is out of range', () => {
		const { container } = render(Word, { token: token('hi'), pivot: 9 });
		expect(container.querySelector('[data-pivot]')).toBeNull();
		expect(container.querySelector('.w')?.textContent).toBe('hi');
	});
});
