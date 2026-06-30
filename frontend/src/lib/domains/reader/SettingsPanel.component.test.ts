/**
 * Component tests for SettingsPanel.svelte (jsdom project, @testing-library/svelte).
 *
 * Covers: panel visibility gated by `open`; `store.set` fires with the correct patch for each
 * control (mode radios, sliders, ramp checkbox, font/theme/context selects); and `onClose`
 * fires through all three close paths (close button, Escape, backdrop). No visual layout or
 * animation is asserted — those are verified via the seed-then-screenshot verify path.
 */
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';
import SettingsPanel from './SettingsPanel.svelte';
import type { PrefsStore } from '$lib/domains/preferences/prefs.svelte';
import { DEFAULT_PREFERENCES, type PreferencesView } from '$lib/domains/preferences/prefs.svelte';

// jsdom does not implement matchMedia — stub a non-matching query so Sheet and any
// component that checks display-mode or reduced-motion don't throw.
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

/**
 * Build a stub PrefsStore that records each patch passed to `set()`.
 *
 * `current` is a plain (non-reactive) object sufficient for initial-value seeding in tests.
 * It is mutated synchronously by `set()` so subsequent assertions see the updated value.
 */
function makeStore(initial: Partial<PreferencesView> = {}): {
	store: PrefsStore;
	patches: Partial<PreferencesView>[];
} {
	const patches: Partial<PreferencesView>[] = [];
	const current: PreferencesView = { ...DEFAULT_PREFERENCES, ...initial };
	const store: PrefsStore = {
		get current() {
			return current;
		},
		async set(patch: Partial<PreferencesView>): Promise<void> {
			patches.push(patch);
			Object.assign(current, patch);
		},
		async reload(): Promise<void> {}
	};
	return { store, patches };
}

// ---------------------------------------------------------------------------
// Panel visibility
// ---------------------------------------------------------------------------

describe('SettingsPanel visibility', () => {
	it('renders nothing when closed', () => {
		const { store } = makeStore();
		render(SettingsPanel, { store, open: false, onClose: () => {} });
		expect(screen.queryByRole('dialog')).toBeNull();
	});

	it('renders a dialog when open', () => {
		const { store } = makeStore();
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		expect(screen.getByRole('dialog')).toBeInTheDocument();
	});

	it('includes all four mode options when open', () => {
		const { store } = makeStore();
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		// Focus is new in v2 — verify it is present alongside the three existing modes.
		expect(screen.getByRole('radio', { name: 'Guided sweep' })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: 'RSVP' })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: 'Fading trail' })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: 'Focus' })).toBeInTheDocument();
	});
});

// ---------------------------------------------------------------------------
// onClose paths
// ---------------------------------------------------------------------------

describe('SettingsPanel onClose', () => {
	it('calls onClose when the close button is clicked', async () => {
		const { store } = makeStore();
		const onClose = vi.fn();
		render(SettingsPanel, { store, open: true, onClose });
		await fireEvent.click(screen.getByRole('button', { name: 'Close settings' }));
		expect(onClose).toHaveBeenCalledOnce();
	});

	it('calls onClose when Escape is pressed', async () => {
		const { store } = makeStore();
		const onClose = vi.fn();
		render(SettingsPanel, { store, open: true, onClose });
		await fireEvent.keyDown(window, { key: 'Escape' });
		expect(onClose).toHaveBeenCalledOnce();
	});

	it('calls onClose when the backdrop is clicked', async () => {
		const { store } = makeStore();
		const onClose = vi.fn();
		render(SettingsPanel, { store, open: true, onClose });
		// Sheet renders the backdrop as a <button> with aria-label="Close {title}".
		await fireEvent.click(screen.getByRole('button', { name: 'Close Reading settings' }));
		expect(onClose).toHaveBeenCalledOnce();
	});
});

// ---------------------------------------------------------------------------
// Mode radios → store.set
// ---------------------------------------------------------------------------

describe('SettingsPanel mode radios', () => {
	it('calls store.set with the selected mode when a radio changes', async () => {
		const { store, patches } = makeStore({ mode: 'guided' });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		await fireEvent.click(screen.getByRole('radio', { name: 'RSVP' }));
		expect(patches).toContainEqual(expect.objectContaining({ mode: 'rsvp' }));
	});

	it('supports selecting Focus mode', async () => {
		const { store, patches } = makeStore({ mode: 'guided' });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		await fireEvent.click(screen.getByRole('radio', { name: 'Focus' }));
		expect(patches).toContainEqual(expect.objectContaining({ mode: 'focus' }));
	});
});

// ---------------------------------------------------------------------------
// Slider controls → store.set (commit via change event)
// ---------------------------------------------------------------------------

describe('SettingsPanel sliders', () => {
	it('calls store.set with wpm on speed slider commit', async () => {
		const { store, patches } = makeStore({ wpm: 300 });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const slider = screen.getByRole('slider', { name: 'Reading speed in words per minute' });
		await fireEvent.change(slider, { target: { value: '500' } });
		expect(patches).toContainEqual(expect.objectContaining({ wpm: 500 }));
	});

	it('calls store.set with chunk on words-per-flash slider commit', async () => {
		const { store, patches } = makeStore({ chunk: 1 });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const slider = screen.getByRole('slider', { name: 'Words shown per flash' });
		await fireEvent.change(slider, { target: { value: '3' } });
		expect(patches).toContainEqual(expect.objectContaining({ chunk: 3 }));
	});

	it('calls store.set with size_px on word-size slider commit', async () => {
		const { store, patches } = makeStore({ size_px: 64 });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const slider = screen.getByRole('slider', { name: 'Reading word size in pixels' });
		await fireEvent.change(slider, { target: { value: '80' } });
		expect(patches).toContainEqual(expect.objectContaining({ size_px: 80 }));
	});

	it('calls store.set with letter_spacing_em on letter-spacing slider commit', async () => {
		const { store, patches } = makeStore({ letter_spacing_em: 0.04 });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const slider = screen.getByRole('slider', { name: 'Letter spacing in em' });
		await fireEvent.change(slider, { target: { value: '0.1' } });
		expect(patches).toContainEqual(expect.objectContaining({ letter_spacing_em: 0.1 }));
	});

	it('calls store.set with ctx_scale on context-size slider commit', async () => {
		const { store, patches } = makeStore({ ctx_scale: 0.7 });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const slider = screen.getByRole('slider', { name: 'Relative size of context words' });
		await fireEvent.change(slider, { target: { value: '0.85' } });
		expect(patches).toContainEqual(expect.objectContaining({ ctx_scale: 0.85 }));
	});
});

// ---------------------------------------------------------------------------
// Ramp checkbox → store.set
// ---------------------------------------------------------------------------

describe('SettingsPanel ramp checkbox', () => {
	it('calls store.set with ramp=false when checkbox is unchecked', async () => {
		// DEFAULT_PREFERENCES has ramp=true; clicking toggles to false.
		const { store, patches } = makeStore({ ramp: true });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const checkbox = screen.getByRole('checkbox');
		await fireEvent.click(checkbox);
		expect(patches).toContainEqual(expect.objectContaining({ ramp: false }));
	});

	it('calls store.set with ramp=true when checkbox is checked', async () => {
		const { store, patches } = makeStore({ ramp: false });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const checkbox = screen.getByRole('checkbox');
		await fireEvent.click(checkbox);
		expect(patches).toContainEqual(expect.objectContaining({ ramp: true }));
	});
});

// ---------------------------------------------------------------------------
// Select controls → store.set
// ---------------------------------------------------------------------------

describe('SettingsPanel selects', () => {
	it('calls store.set with font on typeface select change', async () => {
		const { store, patches } = makeStore({ font: 'atkinson' });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const select = screen.getByLabelText('Typeface');
		await fireEvent.change(select, { target: { value: 'lexend' } });
		expect(patches).toContainEqual(expect.objectContaining({ font: 'lexend' }));
	});

	it('calls store.set with theme on theme select change', async () => {
		const { store, patches } = makeStore({ theme: 'dark' });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const select = screen.getByLabelText('Theme');
		await fireEvent.change(select, { target: { value: 'sepia' } });
		expect(patches).toContainEqual(expect.objectContaining({ theme: 'sepia' }));
	});

	it('calls store.set with context on context-window select change', async () => {
		const { store, patches } = makeStore({ context: 'ab' });
		render(SettingsPanel, { store, open: true, onClose: () => {} });
		const select = screen.getByLabelText('Context window');
		await fireEvent.change(select, { target: { value: 'sentence' } });
		expect(patches).toContainEqual(expect.objectContaining({ context: 'sentence' }));
	});
});
