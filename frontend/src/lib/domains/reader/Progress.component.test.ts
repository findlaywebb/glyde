/**
 * Component tests for Progress.svelte (jsdom project, @testing-library/svelte).
 *
 * Covers: time-remaining format, block notches, tap-to-scrub callback, edge cases for
 * sub-minute and zero remaining time.
 */
import { beforeAll, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';
import Progress from './Progress.svelte';

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
function makeProps(overrides: Record<string, unknown> = {}) {
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

	it('renders word count display', () => {
		render(Progress, makeProps({ wordIndex: 30, wordCount: 100 }));
		expect(screen.getByText('30 / 100')).toBeInTheDocument();
	});
});
