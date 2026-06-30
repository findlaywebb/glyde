import { fireEvent, render, screen } from '@testing-library/svelte';
import { Play } from '@lucide/svelte';
import { createRawSnippet } from 'svelte';
import { beforeAll, beforeEach, describe, expect, it } from 'vitest';
import Button from './Button.svelte';
import Icon from './Icon.svelte';
import InstallHint from './InstallHint.svelte';
import Sheet from './Sheet.svelte';
import Slider from './Slider.svelte';
import { INSTALL_HINT_DISMISSED_KEY } from './install-hint';

// jsdom has no matchMedia; InstallHint's display-mode probe needs it. Stub a non-matching
// query (not standalone) so the iOS install hint is allowed to show.
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

/** A text snippet for the `children` prop of Button / Sheet. */
const textSnippet = (text: string) =>
	createRawSnippet(() => ({ render: () => `<span>${text}</span>` }));

describe('Button', () => {
	it('renders its label and meets the 44px touch target', () => {
		render(Button, { children: textSnippet('Save') });
		const button = screen.getByRole('button', { name: 'Save' });
		expect(button).toBeInTheDocument();
		expect(button.className).toContain('min-h-11');
	});
});

describe('Icon', () => {
	it('is a labelled image when given an aria-label', () => {
		render(Icon, { icon: Play, 'aria-label': 'Play' });
		expect(screen.getByRole('img', { name: 'Play' })).toBeInTheDocument();
	});

	it('is decorative (aria-hidden, no role) without an aria-label', () => {
		const { container } = render(Icon, { icon: Play });
		const svg = container.querySelector('svg');
		expect(svg?.getAttribute('aria-hidden')).toBe('true');
		expect(container.querySelector('[role="img"]')).toBeNull();
	});
});

describe('Slider', () => {
	it('exposes a labelled slider and reports the committed value', async () => {
		let committed: number | null = null;
		render(Slider, {
			value: 300,
			min: 100,
			max: 900,
			step: 25,
			'aria-label': 'Speed',
			onValueChange: (value: number) => {
				committed = value;
			}
		});
		const slider = screen.getByRole('slider', { name: 'Speed' });
		expect(slider).toBeInTheDocument();
		await fireEvent.change(slider, { target: { value: '500' } });
		expect(committed).toBe(500);
	});
});

describe('Sheet', () => {
	it('renders a labelled dialog and dismisses on a backdrop tap', async () => {
		let closes = 0;
		render(Sheet, {
			open: true,
			title: 'Settings',
			onClose: () => {
				closes += 1;
			},
			children: textSnippet('Body')
		});
		expect(screen.getByRole('dialog', { name: 'Settings' })).toBeInTheDocument();
		await fireEvent.click(screen.getByRole('button', { name: 'Close Settings' }));
		expect(closes).toBe(1);
	});

	it('dismisses on Escape', async () => {
		let closes = 0;
		render(Sheet, {
			open: true,
			title: 'Settings',
			onClose: () => {
				closes += 1;
			},
			children: textSnippet('Body')
		});
		await fireEvent.keyDown(window, { key: 'Escape' });
		expect(closes).toBe(1);
	});
});

describe('InstallHint', () => {
	const IPHONE_SAFARI =
		'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

	beforeEach(() => {
		Object.defineProperty(window.navigator, 'userAgent', {
			value: IPHONE_SAFARI,
			configurable: true
		});
		(window.navigator as Navigator & { standalone?: boolean }).standalone = false;
		window.localStorage.clear();
	});

	it('shows on iOS Safari with a 44px dismiss control, then persists dismissal', async () => {
		render(InstallHint);
		const close = await screen.findByRole('button', { name: 'Dismiss install hint' });
		expect(close.className).toContain('min-h-11');
		expect(close.className).toContain('min-w-11');
		await fireEvent.click(close);
		expect(screen.queryByRole('button', { name: 'Dismiss install hint' })).toBeNull();
		expect(window.localStorage.getItem(INSTALL_HINT_DISMISSED_KEY)).toBe('1');
	});
});
