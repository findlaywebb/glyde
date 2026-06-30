/**
 * Component tests for Transport.svelte (jsdom project, @testing-library/svelte).
 *
 * Covers: callback firing (onToggle, onReplayWord, onStepForward, onSpeed), play/pause label
 * toggle, speed slider, and ≥44px touch-target class guards. No global-listener side effects.
 */
import { beforeAll, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';
import Transport from './Transport.svelte';

// jsdom does not implement matchMedia — stub a non-matching query so components that check
// display-mode or reduced-motion don't throw.
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

/** Build a minimal TransportProps fixture. */
function makeProps(overrides: Record<string, unknown> = {}) {
	return {
		isPlaying: false,
		wpm: 300,
		onToggle: () => {},
		onReplayWord: () => {},
		onStepForward: () => {},
		onSpeed: () => {},
		...overrides
	};
}

describe('Transport', () => {
	it('shows Play label when not playing', () => {
		render(Transport, makeProps());
		expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument();
	});

	it('shows Pause label when playing', () => {
		render(Transport, makeProps({ isPlaying: true }));
		expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument();
	});

	it('calls onToggle when the play-pause button is clicked', async () => {
		let fired = false;
		render(
			Transport,
			makeProps({
				onToggle: () => {
					fired = true;
				}
			})
		);
		await fireEvent.click(screen.getByRole('button', { name: 'Play' }));
		expect(fired).toBe(true);
	});

	it('calls onReplayWord when the replay button is clicked', async () => {
		let fired = false;
		render(
			Transport,
			makeProps({
				onReplayWord: () => {
					fired = true;
				}
			})
		);
		await fireEvent.click(screen.getByRole('button', { name: 'Replay previous word' }));
		expect(fired).toBe(true);
	});

	it('calls onStepForward when the step button is clicked', async () => {
		let fired = false;
		render(
			Transport,
			makeProps({
				onStepForward: () => {
					fired = true;
				}
			})
		);
		await fireEvent.click(screen.getByRole('button', { name: 'Step forward one word' }));
		expect(fired).toBe(true);
	});

	it('calls onSpeed with the committed wpm value from the speed slider', async () => {
		let speed = 0;
		render(
			Transport,
			makeProps({
				onSpeed: (wpm: number) => {
					speed = wpm;
				}
			})
		);
		const slider = screen.getByRole('slider', { name: 'Reading speed in words per minute' });
		await fireEvent.change(slider, { target: { value: '500' } });
		expect(speed).toBe(500);
	});

	it('renders exactly three control buttons with ≥44px touch targets', () => {
		render(Transport, makeProps());
		const buttons = screen.getAllByRole('button');
		expect(buttons).toHaveLength(3);
		for (const btn of buttons) {
			expect(btn.className).toContain('min-h-11');
			expect(btn.className).toContain('min-w-11');
		}
	});

	it('displays the current wpm value', () => {
		render(Transport, makeProps({ wpm: 400 }));
		expect(screen.getByText('400 wpm')).toBeInTheDocument();
	});
});
