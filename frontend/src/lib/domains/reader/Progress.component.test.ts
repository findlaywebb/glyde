/**
 * Component tests for Progress.svelte (jsdom project, @testing-library/svelte).
 *
 * Covers: time-remaining format, block notches, tap-to-scrub callback, edge cases for
 * sub-minute and zero remaining time.
 */
import { beforeAll, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';
import Progress from './Progress.svelte';
import type { ProgressProps } from './types';

beforeAll(() => {
	if (!window.matchMedia) {
		window.matchMedia = (query: string) =>
			({
				matches: false,
				media: query,
				onchange: null,
				addEventListener: () => {},
				removeEventListener: () => {},
				addListener: () => {},
				removeListener: () => {},
				dispatchEvent: () => false
			}) as MediaQueryList;
	}
});

/** Build a minimal ProgressProps fixture. */
function makeProps(overrides: Partial<ProgressProps> = {}) {
	return {
		wordIndex: 30,
		wordCount: 100,
		remainingMs: 134000, // 2 min 14 s
		blockNotches: [20, 50, 80],
		onScrub: () => {},
		...overrides
	};
}

describe('Progress', () => {
	it('renders the time-remaining string with minutes and seconds', () => {
		render(Progress, makeProps({ remainingMs: 134000 }));
		// 134 s = 2 m 14 s → "~2m 14s left"
		expect(screen.getByText('~2m 14s left')).toBeInTheDocument();
	});

	it('renders sub-minute remaining time without the minutes component', () => {
		render(Progress, makeProps({ remainingMs: 45000 }));
		expect(screen.getByText('~45s left')).toBeInTheDocument();
	});

	it('renders "~0s left" when remainingMs is zero', () => {
		render(Progress, makeProps({ remainingMs: 0 }));
		expect(screen.getByText('~0s left')).toBeInTheDocument();
	});

	it('renders one notch element per blockNotches entry', () => {
		const { container } = render(Progress, makeProps({ blockNotches: [20, 50, 80] }));
		const notches = container.querySelectorAll('[data-testid="notch"]');
		expect(notches).toHaveLength(3);
	});

	it('renders no notches when blockNotches is empty', () => {
		const { container } = render(Progress, makeProps({ blockNotches: [] }));
		expect(container.querySelectorAll('[data-testid="notch"]')).toHaveLength(0);
	});

	it('calls onScrub with the selected word index when the scrubber changes', async () => {
		let scrubbed: number | null = null;
		render(
			Progress,
			makeProps({
				onScrub: (idx: number) => {
					scrubbed = idx;
				}
			})
		);
		const slider = screen.getByRole('slider', { name: 'Reading position' });
		await fireEvent.change(slider, { target: { value: '42' } });
		expect(scrubbed).toBe(42);
	});

	it('drives the fill from wordIndex before any drag', () => {
		const { container } = render(Progress, makeProps({ wordIndex: 30, wordCount: 100 }));
		const fill = container.querySelector<HTMLElement>('[data-testid="fill"]');
		expect(fill?.style.width).toBe('30%');
	});

	it('tracks the fill to the in-flight drag value, not wordIndex, while dragging', async () => {
		const { container } = render(Progress, makeProps({ wordIndex: 30, wordCount: 100 }));
		const slider = screen.getByRole('slider', { name: 'Reading position' });
		const fill = container.querySelector<HTMLElement>('[data-testid="fill"]');
		// A drag fires `input` (not `change`); the visible fill must follow the drag (70%), not
		// stay pinned at the engine's wordIndex (30%) — otherwise the bar gives no drag feedback.
		await fireEvent.input(slider, { target: { value: '70' } });
		expect(fill?.style.width).toBe('70%');
	});

	it('caps the scrubber max at the last valid 0-based word index', () => {
		render(Progress, makeProps({ wordCount: 100 }));
		const slider = screen.getByRole('slider', { name: 'Reading position' }) as HTMLInputElement;
		// 100 words → valid ordinals 0..99, so max is 99 (never 100, which would be out of bounds).
		expect(slider.max).toBe('99');
	});

	it('disables the scrubber on an empty digest so no out-of-range scrub can fire', () => {
		// With no words, the browser delivers no interaction events to a disabled control, so
		// onScrub can never fire with an out-of-range index (max collapses to 0).
		render(Progress, makeProps({ wordIndex: 0, wordCount: 0, blockNotches: [] }));
		const slider = screen.getByRole('slider', { name: 'Reading position' }) as HTMLInputElement;
		expect(slider.disabled).toBe(true);
		expect(slider.max).toBe('0');
	});

	it('renders word count display', () => {
		render(Progress, makeProps({ wordIndex: 30, wordCount: 100 }));
		expect(screen.getByText('30 / 100')).toBeInTheDocument();
	});

	it('renders all notches without throwing when blockNotches contains duplicate positions', () => {
		// Regression: consecutive blocks with no prose between them share the same word index.
		// Keying by value caused each_key_duplicate → blank reader. Key must be by index.
		const { container } = render(
			Progress,
			makeProps({ blockNotches: [262, 262, 262], wordCount: 500 })
		);
		const notches = container.querySelectorAll('[data-testid="notch"]');
		expect(notches).toHaveLength(3);
	});
});
