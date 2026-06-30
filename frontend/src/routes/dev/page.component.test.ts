import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Page from './+page.svelte';

describe('/dev harness', () => {
	it('renders the gallery in all three theme scopes', () => {
		const { container } = render(Page);
		expect(container.querySelector('.dark')).not.toBeNull();
		expect(container.querySelector('.light')).not.toBeNull();
		expect(container.querySelector('.sepia')).not.toBeNull();
	});

	it('shows the coral pivot on the Atkinson reading face in each scope', () => {
		const { container } = render(Page);
		// the reading line marks one pivot glyph per scope (×3); the font-reading face is applied.
		expect(container.querySelectorAll('.text-pivot').length).toBeGreaterThanOrEqual(3);
		expect(container.querySelector('.font-reading')).not.toBeNull();
	});

	it('mounts the shell primitives (one slider per scope, plus buttons)', () => {
		const { getAllByRole } = render(Page);
		expect(getAllByRole('slider').length).toBeGreaterThanOrEqual(3);
		expect(getAllByRole('button').length).toBeGreaterThanOrEqual(3);
	});
});
