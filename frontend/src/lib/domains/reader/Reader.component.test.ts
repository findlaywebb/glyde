// R-STAGE integration tests — jsdom `component` project (mounts the composing reader). These
// gate the headline behaviours as DOM assertions, not screenshots (§5.9 PATH A): default Guided on
// first run, the last-used-mode persist/restore round-trip through PREF, and the block state
// machine driven through the stage's global keyboard listener. A stopped clock is injected so
// play() never auto-advances — every advance is an explicit step/key, keeping the assertions
// deterministic.
import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import Reader from './Reader.svelte';
import type { ReaderClock } from './types';
import type { BlockView, ProseSegmentView, SegmentView, TokenView } from './types';
import {
	createPrefsStore,
	DEFAULT_PREFERENCES,
	PREFS_STORAGE_KEY,
	type PreferencesView
} from '$lib/domains/preferences/prefs.svelte';

/** A word token. */
function word(text: string): TokenView {
	return { text, kind: 'word', emphasis: 'none' };
}

/** A prose run over the given words. */
function prose(...words: string[]): ProseSegmentView {
	return { type: 'prose', role: 'body', tokens: words.map(word) };
}

/** A code block. */
function codeBlock(content: string, lang = 'py'): BlockView {
	return { type: 'block', kind: 'code', content, lang };
}

/** A clock whose scheduler never ticks, so the engine advances only on explicit step/key. */
const stoppedClock: ReaderClock = { now: () => 0, schedule: () => () => {} };

/** A recorded request the fake `fetch` saw. */
interface RecordedCall {
	method: string;
	path: string;
	body: unknown;
}

/** An injected `fetch` that answers GET/PUT `/preferences` and records what it saw. */
function makeFetch(): { fetchImpl: typeof fetch; calls: RecordedCall[] } {
	const calls: RecordedCall[] = [];
	const fetchImpl = (async (input: RequestInfo | URL): Promise<Response> => {
		const request = input as Request;
		const path = new URL(request.url).pathname;
		if (request.method === 'GET') {
			calls.push({ method: 'GET', path, body: undefined });
			return jsonResponse(DEFAULT_PREFERENCES);
		}
		const body = (await request.json()) as unknown;
		calls.push({ method: request.method, path, body });
		return jsonResponse(body);
	}) as typeof fetch;
	return { fetchImpl, calls };
}

/** A 200 JSON `Response` the typed client parses as `{ data }`. */
function jsonResponse(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { 'content-type': 'application/json' }
	});
}

beforeEach(() => localStorage.clear());
afterEach(() => localStorage.clear());

describe('Reader default mode', () => {
	it('mounts the Flow (guided) view on first run, not RSVP', () => {
		const store = createPrefsStore({ fetch: makeFetch().fetchImpl });
		const { container } = render(Reader, {
			segments: [prose('hello', 'world')] as SegmentView[],
			store,
			clock: stoppedClock
		});
		// Default preferences are mode "guided" → the Flow view, never the RSVP view.
		expect(container.querySelector('.flow')).not.toBeNull();
		expect(container.querySelector('.rsvp-stage')).toBeNull();
		expect(container.querySelector('[data-mode="guided"]')).not.toBeNull();
	});
});

describe('Reader last-used mode round-trip', () => {
	it('persists a mode switch through PREF and restores it on a fresh store', async () => {
		const { fetchImpl, calls } = makeFetch();
		const store = createPrefsStore({ fetch: fetchImpl });
		const first = render(Reader, {
			segments: [prose('hello', 'world')] as SegmentView[],
			store,
			clock: stoppedClock
		});

		// Switch mode through the stage's own control.
		await fireEvent.click(screen.getByRole('button', { name: 'RSVP' }));

		// The localStorage mirror is written synchronously (full object, mode rsvp).
		const mirror = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) ?? '{}') as PreferencesView;
		expect(mirror.mode).toBe('rsvp');
		// The write-through PUT carries the full object with the new mode.
		await waitFor(() => expect(calls.some((c) => c.method === 'PUT')).toBe(true));
		const put = calls.find((c) => c.method === 'PUT');
		expect(put?.path).toBe('/api/preferences');
		expect(put?.body).toMatchObject({ mode: 'rsvp' });

		first.unmount();

		// A brand-new store (next open) reads the mirror synchronously → RSVP is restored.
		const restored = createPrefsStore({ fetch: makeFetch().fetchImpl });
		expect(restored.current.mode).toBe('rsvp');
		const { container } = render(Reader, {
			segments: [prose('hello', 'world')] as SegmentView[],
			store: restored,
			clock: stoppedClock
		});
		expect(container.querySelector('.rsvp-stage')).not.toBeNull();
		expect(container.querySelector('.flow')).toBeNull();
	});
});

describe('Reader block state machine through the stage', () => {
	it('pauses on a block, resumes on Space, and re-shows on ArrowLeft', async () => {
		const store = createPrefsStore({ fetch: makeFetch().fetchImpl });
		const segments: SegmentView[] = [prose('alpha', 'beta'), codeBlock('print(1)'), prose('gamma')];
		render(Reader, { segments, store, clock: stoppedClock });

		// Frames: word(alpha), word(beta), block, word(gamma). Step forward onto the block.
		await fireEvent.keyDown(window, { key: 'ArrowRight' });
		await fireEvent.keyDown(window, { key: 'ArrowRight' });

		// The CodeCard is shown and playback is paused (the play button offers "Play").
		expect(screen.getByText(/print\(1\)/)).toBeInTheDocument();
		expect(screen.getByLabelText('Play')).toBeInTheDocument();

		// Space resumes: the card is dismissed and playback runs (the button now offers "Pause").
		await fireEvent.keyDown(window, { key: ' ' });
		expect(screen.queryByText(/print\(1\)/)).toBeNull();
		expect(screen.getByLabelText('Pause')).toBeInTheDocument();

		// ArrowLeft re-shows the most-recent block with the "reshown" affordance.
		await fireEvent.keyDown(window, { key: 'ArrowLeft' });
		expect(screen.getByText(/print\(1\)/)).toBeInTheDocument();
		expect(screen.getByText('reshown')).toBeInTheDocument();
	});
});
