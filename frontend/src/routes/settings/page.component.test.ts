// Settings page DOM render — jsdom `component` project (§5.9 PATH A, no pixels). Mounts the real
// route and asserts the grouped controls, the mode radios, and the live preview are present and
// reflect the stored preferences. The page's store talks to the platform `fetch` (no server here);
// `reload` is offline-safe, so the mount renders from the localStorage mirror without throwing.
import { render } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { DEFAULT_PREFERENCES, PREFS_STORAGE_KEY } from '$lib/domains/preferences/prefs.svelte';
import Page from './+page.svelte';

beforeEach(() => {
	localStorage.clear();
});

afterEach(() => {
	localStorage.clear();
});

describe('/settings', () => {
	it('renders the grouped sections and the sliders/selects/radios', () => {
		const { getByRole, getAllByRole } = render(Page);
		expect(getByRole('heading', { name: /reading settings/i })).toBeInTheDocument();
		// Reading speed / chunk / word size / spacing / context size = five range sliders.
		expect(getAllByRole('slider').length).toBe(5);
		// Typeface / theme / context = three selects.
		expect(getAllByRole('combobox').length).toBe(3);
		// Three reading-mode radios.
		expect(getAllByRole('radio').length).toBe(3);
	});

	it('reflects the stored last-used mode in the checked radio', () => {
		localStorage.setItem(
			PREFS_STORAGE_KEY,
			JSON.stringify({ ...DEFAULT_PREFERENCES, mode: 'rsvp' })
		);
		const { getByRole } = render(Page);
		const rsvp = getByRole('radio', { name: /rsvp/i }) as HTMLInputElement;
		expect(rsvp.checked).toBe(true);
	});

	it('shows the live preview word with the coral pivot', () => {
		const { getByLabelText, container } = render(Page);
		expect(getByLabelText('Live preview')).toBeInTheDocument();
		expect(container.querySelector('.text-pivot')).not.toBeNull();
	});
});
