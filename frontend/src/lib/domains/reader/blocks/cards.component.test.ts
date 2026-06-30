/**
 * Component tests for the R-BLOCKS block card family.
 *
 * Runs in the jsdom `component` project (vitest.config.ts). Each card is mounted with a
 * `BlockCardProps` fixture and asserted on rendered DOM — no screenshots, no pixels; the DOM
 * assertion is the binding gate (§5.9 PATH A).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';

import BlockAheadCue from './BlockAheadCue.svelte';
import CodeCard from './CodeCard.svelte';
import ImageCard from './ImageCard.svelte';
import MathCard from './MathCard.svelte';
import NoteCard from './NoteCard.svelte';
import QuoteCard from './QuoteCard.svelte';
import TableCard from './TableCard.svelte';

import type { BlockView } from '$lib/domains/reader/types';

type BlockExtras = Partial<Omit<BlockView, 'kind' | 'type' | 'content'>>;

/** Build a minimal BlockView fixture for the given kind. */
function block(
	kind: BlockView['kind'],
	overrides: Partial<Omit<BlockView, 'kind' | 'type'>> = {}
): BlockView {
	const contents: Record<BlockView['kind'], string> = {
		code: 'x = 1\ny = 2',
		table: '| Name | Score |\n| --- | --- |\n| Alice | 42 |\n| Bob | 17 |',
		image: 'https://example.com/cat.png',
		math: 'E = mc^2',
		quote: 'To be or not to be.',
		note: 'Take a breath before continuing.'
	};
	const extras: Record<BlockView['kind'], BlockExtras> = {
		code: { lang: 'py' },
		table: {},
		image: { alt: 'a cat' },
		math: {},
		quote: {},
		note: {}
	};
	return { type: 'block', kind, content: contents[kind], ...extras[kind], ...overrides };
}

// --- BlockAheadCue ---

describe('BlockAheadCue', () => {
	it('renders the kind label when visible', () => {
		render(BlockAheadCue, { kind: 'code', visible: true });
		expect(screen.getByRole('status')).toBeInTheDocument();
		expect(screen.getByText('code ahead')).toBeInTheDocument();
	});

	it('does not render when not visible', () => {
		render(BlockAheadCue, { kind: 'table', visible: false });
		expect(screen.queryByRole('status')).toBeNull();
		expect(screen.queryByText('table ahead')).toBeNull();
	});

	it('shows the correct label for each kind', () => {
		const kinds: BlockView['kind'][] = ['code', 'table', 'image', 'math', 'quote', 'note'];
		for (const kind of kinds) {
			const { unmount } = render(BlockAheadCue, { kind, visible: true });
			expect(screen.getByText(`${kind} ahead`)).toBeInTheDocument();
			unmount();
		}
	});
});

// --- CodeCard ---

describe('CodeCard', () => {
	it('renders the code content and lang label', () => {
		const { container } = render(CodeCard, { block: block('code'), reshown: false });
		const pre = container.querySelector('pre');
		expect(pre).toBeTruthy();
		expect(pre?.textContent?.trim()).toContain('x = 1');
		expect(screen.getByText('py')).toBeInTheDocument();
		expect(screen.getByText('code')).toBeInTheDocument();
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(CodeCard, { block: block('code'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});

	it('does not show the reshown affordance when reshown=false', () => {
		render(CodeCard, { block: block('code'), reshown: false });
		expect(screen.queryByText('reshown')).toBeNull();
	});

	it('renders without a lang when lang is null', () => {
		const b = block('code', { lang: null });
		const { container } = render(CodeCard, { block: b, reshown: false });
		const pre = container.querySelector('pre');
		expect(pre).toBeTruthy();
		expect(pre?.textContent?.trim()).toContain('x = 1');
		expect(screen.queryByText('py')).toBeNull();
	});

	it('toggles between scroll and wrap mode', async () => {
		render(CodeCard, { block: block('code'), reshown: false });
		const toggleBtn = screen.getByRole('button', { name: /wrap|scroll/i });
		// Initial state: scroll mode, button says "wrap"
		expect(toggleBtn).toHaveAttribute('aria-pressed', 'false');
		expect(toggleBtn.textContent?.trim()).toBe('wrap');
		await fireEvent.click(toggleBtn);
		expect(toggleBtn).toHaveAttribute('aria-pressed', 'true');
		expect(toggleBtn.textContent?.trim()).toBe('scroll');
	});
});

// --- TableCard ---

describe('TableCard', () => {
	it('renders table headers and row values', () => {
		render(TableCard, { block: block('table'), reshown: false });
		expect(screen.getAllByText('Name').length).toBeGreaterThan(0);
		expect(screen.getAllByText('Score').length).toBeGreaterThan(0);
		expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
		expect(screen.getAllByText('42').length).toBeGreaterThan(0);
		expect(screen.getAllByText('Bob').length).toBeGreaterThan(0);
		expect(screen.getAllByText('17').length).toBeGreaterThan(0);
	});

	it('renders a stacked label view for narrow layout', () => {
		render(TableCard, { block: block('table'), reshown: false });
		// The stacked layout uses dl/dt/dd elements with "header:" labels
		const dts = document.querySelectorAll('dt');
		expect(dts.length).toBeGreaterThan(0);
		// Each dt should show a header name
		const dtTexts = Array.from(dts).map((dt) => dt.textContent?.trim());
		expect(dtTexts).toContain('Name:');
		expect(dtTexts).toContain('Score:');
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(TableCard, { block: block('table'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});

// --- ImageCard ---

describe('ImageCard', () => {
	it('renders the img element with alt text', () => {
		render(ImageCard, { block: block('image'), reshown: false });
		const img = screen.getByRole('img', { name: 'a cat' });
		expect(img).toBeInTheDocument();
		expect(img).toHaveAttribute('src', 'https://example.com/cat.png');
	});

	it('falls back to alt text when the image fails to load', async () => {
		render(ImageCard, { block: block('image'), reshown: false });
		const img = document.querySelector('img');
		expect(img).toBeTruthy();
		await fireEvent.error(img!);
		await waitFor(() => {
			expect(screen.queryByRole('img', { name: /a cat/ })).toBeTruthy();
			// After error, there should be no <img> src element visible
			expect(document.querySelector('img')).toBeNull();
		});
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(ImageCard, { block: block('image'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});

// --- MathCard ---

describe('MathCard', () => {
	it('renders the raw content when no linear_form is present', () => {
		render(MathCard, { block: block('math'), reshown: false });
		expect(screen.getByText('E = mc^2')).toBeInTheDocument();
	});

	it('renders the linear_form when present', () => {
		const b = block('math', { linear_form: 'E equals m c squared', content: 'E = mc^2' });
		render(MathCard, { block: b, reshown: false });
		expect(screen.getByText('E equals m c squared')).toBeInTheDocument();
		// Raw source still shown as a secondary label
		expect(screen.getByText('E = mc^2')).toBeInTheDocument();
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(MathCard, { block: block('math'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});

// --- QuoteCard ---

describe('QuoteCard', () => {
	it('renders the quote content in a blockquote', () => {
		render(QuoteCard, { block: block('quote'), reshown: false });
		expect(screen.getByText('To be or not to be.')).toBeInTheDocument();
		expect(document.querySelector('blockquote')).toBeTruthy();
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(QuoteCard, { block: block('quote'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});

// --- NoteCard ---

describe('NoteCard', () => {
	it('renders the note content', () => {
		render(NoteCard, { block: block('note'), reshown: false });
		expect(screen.getByText('Take a breath before continuing.')).toBeInTheDocument();
	});

	it('shows the reshown affordance when reshown=true', () => {
		render(NoteCard, { block: block('note'), reshown: true });
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});
