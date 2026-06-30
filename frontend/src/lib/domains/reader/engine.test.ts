/**
 * Headless engine + pure cadence tests — the node `unit` project (no DOM, no rAF, no jsdom).
 *
 * The engine is constructed with a fake injected clock and stepped deterministically, proving the
 * headless-constructibility defect-fix: it never touches `window`, `performance.now`, or
 * `requestAnimationFrame`. The cadence math is exercised directly as a pure module.
 */
import { describe, expect, it } from 'vitest';
import * as cadence from './cadence';
import { createReaderEngine } from './engine.svelte';
import type {
	BlockView,
	PauseView,
	PreferencesView,
	ProseSegmentView,
	ReaderClock,
	SegmentView,
	TokenView
} from './types';

// --- Fixtures ---

function makePrefs(overrides: Partial<PreferencesView> = {}): PreferencesView {
	return {
		owner_id: 'local',
		mode: 'guided',
		wpm: 300,
		context: 'ab',
		ctx_scale: 0.7,
		chunk: 1,
		size_px: 64,
		letter_spacing_em: 0.04,
		font: 'atkinson',
		theme: 'dark',
		ramp: true,
		...overrides
	};
}

function word(text: string, emphasis: TokenView['emphasis'] = 'none'): TokenView {
	return { text, kind: 'word', emphasis };
}

function prose(tokens: TokenView[], role: ProseSegmentView['role'] = 'body'): ProseSegmentView {
	return { type: 'prose', role, tokens };
}

function pause(reason: PauseView['reason'], durationScale = 1): PauseView {
	return { type: 'pause', reason, duration_scale: durationScale };
}

function block(
	kind: BlockView['kind'],
	content: string,
	extra: Partial<BlockView> = {}
): BlockView {
	return { type: 'block', kind, content, ...extra };
}

/** A manual frame scheduler: holds one pending tick (rAF-style); `advance` fires it once. */
function makeFakeClock(): { clock: ReaderClock; advance: (ms: number) => void } {
	let now = 0;
	let queued: ((n: number) => void) | null = null;
	return {
		clock: {
			now: () => now,
			schedule: (tick) => {
				queued = tick;
				return () => {
					if (queued === tick) queued = null;
				};
			}
		},
		advance(ms: number) {
			now += ms;
			const tick = queued;
			queued = null;
			if (tick) tick(now);
		}
	};
}

const texts = (tokens: TokenView[]): string[] => tokens.map((t) => t.text);

// --- Pure cadence ---

describe('cadence', () => {
	it('a 12-letter word ending a sentence is ~493ms at 300 wpm', () => {
		expect(
			cadence.dwellMs({
				wpm: 300,
				wordLength: 12,
				emphasised: false,
				firstAfterPause: false,
				pauseReason: 'sentence'
			})
		).toBe(493);
	});

	it('a short mid-sentence word is ~200ms at 300 wpm', () => {
		expect(
			cadence.dwellMs({
				wpm: 300,
				wordLength: 4,
				emphasised: false,
				firstAfterPause: false,
				pauseReason: null
			})
		).toBe(200);
	});

	it('emphasis and first-after-pause multipliers compound onto the base', () => {
		// 200 * 1.25 (emphasis) * 1.15 (first-after-pause) = 287.5 -> 288
		expect(
			cadence.dwellMs({
				wpm: 300,
				wordLength: 3,
				emphasised: true,
				firstAfterPause: true,
				pauseReason: null
			})
		).toBe(288);
	});

	it('reduced motion floors the dwell so a flashing reader never strobes', () => {
		expect(
			cadence.dwellMs({
				wpm: 300,
				wordLength: 4,
				emphasised: false,
				firstAfterPause: false,
				pauseReason: null,
				reducedMotion: true
			})
		).toBe(cadence.REDUCED_MOTION_MIN_DWELL_MS);
	});

	it('the pivot bucket boundaries fall at lengths 1/5/9/13', () => {
		expect(cadence.pivotIndex(1)).toBe(0);
		expect(cadence.pivotIndex(5)).toBe(1);
		expect(cadence.pivotIndex(9)).toBe(2);
		expect(cadence.pivotIndex(13)).toBe(3);
		expect(cadence.pivotIndex(14)).toBe(4);
	});

	it('the long-word multiplier is 1 at the threshold and caps at 1.4', () => {
		expect(cadence.longWordMultiplier(8)).toBe(1);
		expect(cadence.longWordMultiplier(12)).toBeCloseTo(1.12, 5);
		expect(cadence.longWordMultiplier(1000)).toBe(cadence.LONG_WORD_CAP);
	});

	it('pause weights scale by reason and duration_scale', () => {
		expect(cadence.pauseWeight('clause')).toBe(1.5);
		expect(cadence.pauseWeight('sentence')).toBe(2.2);
		expect(cadence.pauseWeight('paragraph')).toBe(2.8);
		expect(cadence.pauseWeight('clause', 2)).toBe(3);
	});

	it('the ramp eases from 45% of target to target over RAMP_WORDS', () => {
		expect(cadence.rampedWpm(300, 0, true)).toBeCloseTo(135, 5);
		expect(cadence.rampedWpm(300, cadence.RAMP_WORDS, true)).toBe(300);
		expect(cadence.rampedWpm(300, 1000, true)).toBe(300);
		expect(cadence.rampedWpm(300, 0, false)).toBe(300);
	});

	it('base milliseconds per word is 60000 / wpm', () => {
		expect(cadence.baseMs(300)).toBe(200);
		expect(cadence.baseMs(600)).toBe(100);
	});

	it('property: the pivot index always lands inside the word and within 0..4', () => {
		for (let len = 1; len <= 40; len++) {
			const p = cadence.pivotIndex(len);
			expect(p).toBeGreaterThanOrEqual(0);
			expect(p).toBeLessThanOrEqual(4);
			expect(p).toBeLessThanOrEqual(len - 1);
		}
	});

	it('property: dwell is non-decreasing in word length and never below the base', () => {
		for (const wpm of [120, 300, 600]) {
			const base = Math.round(cadence.baseMs(wpm));
			let prev = 0;
			for (let len = 1; len <= 30; len++) {
				const ms = cadence.dwellMs({
					wpm,
					wordLength: len,
					emphasised: false,
					firstAfterPause: false,
					pauseReason: null
				});
				expect(ms).toBeGreaterThanOrEqual(base - 1); // -1 tolerates rounding
				expect(ms).toBeGreaterThanOrEqual(prev);
				prev = ms;
			}
		}
	});
});

// --- Headless engine construction + clock-driven cadence ---

describe('createReaderEngine — headless construction', () => {
	const hello: SegmentView[] = [prose([word('Hello'), word('world')])];

	it('constructs with no DOM and exposes the static word stream', () => {
		const engine = createReaderEngine({ segments: hello, prefs: makePrefs() });
		expect(texts(engine.words)).toEqual(['Hello', 'world']);
		expect(engine.wordCount).toBe(2);
		expect(engine.blockNotches).toEqual([]);
		expect(engine.atEnd).toBe(false);
	});

	it('token is null before the first play', () => {
		const engine = createReaderEngine({ segments: hello, prefs: makePrefs() });
		expect(engine.token).toBeNull();
		expect(engine.isPlaying).toBe(false);
		expect(engine.pivotIndex).toBe(0);
		expect(engine.dwellMs).toBe(0);
	});

	it('play shows the first word with its pivot and dwell', () => {
		const engine = createReaderEngine({
			segments: hello,
			prefs: makePrefs({ ramp: false })
		});
		engine.play();
		expect(engine.token?.text).toBe('Hello');
		expect(engine.wordIndex).toBe(0);
		expect(engine.isPlaying).toBe(true);
		expect(engine.pivotIndex).toBe(cadence.pivotIndex('Hello'.length));
		expect(engine.dwellMs).toBe(200);
	});

	it('the injected clock drives word-by-word auto-advance to the end', () => {
		const fc = makeFakeClock();
		const engine = createReaderEngine({
			segments: hello,
			prefs: makePrefs({ ramp: false }),
			clock: fc.clock
		});
		engine.play();
		expect(engine.wordIndex).toBe(0);
		fc.advance(1000);
		expect(engine.token?.text).toBe('world');
		expect(engine.wordIndex).toBe(1);
		fc.advance(1000);
		expect(engine.atEnd).toBe(true);
		expect(engine.isPlaying).toBe(false);
		expect(engine.token).toBeNull();
	});

	it('setPrefs re-derives the dwell at the new speed', () => {
		const engine = createReaderEngine({
			segments: hello,
			prefs: makePrefs({ ramp: false })
		});
		engine.play();
		expect(engine.dwellMs).toBe(200);
		engine.setPrefs(makePrefs({ ramp: false, wpm: 600 }));
		expect(engine.dwellMs).toBe(100);
	});

	it('reduced motion floors the engine dwell', () => {
		const engine = createReaderEngine({
			segments: hello,
			prefs: makePrefs({ ramp: false }),
			reducedMotion: true
		});
		engine.play();
		expect(engine.dwellMs).toBe(cadence.REDUCED_MOTION_MIN_DWELL_MS);
	});

	it('manual transport steps, replays and scrubs the cursor', () => {
		const engine = createReaderEngine({
			segments: hello,
			prefs: makePrefs({ ramp: false })
		});
		engine.play();
		engine.stepForward();
		expect(engine.token?.text).toBe('world');
		expect(engine.wordIndex).toBe(1);
		engine.replayWord();
		expect(engine.token?.text).toBe('Hello');
		expect(engine.wordIndex).toBe(0);
		engine.scrubTo(1);
		expect(engine.token?.text).toBe('world');
		expect(engine.wordIndex).toBe(1);
	});

	it('exposes the RSVP context window each side of the current word', () => {
		const segments: SegmentView[] = [prose([word('Hello'), word('world'), word('there')])];
		const engine = createReaderEngine({
			segments,
			prefs: makePrefs({ ramp: false, context: 'ab' })
		});
		engine.play();
		expect(texts(engine.contextBefore)).toEqual([]);
		expect(texts(engine.contextAfter)).toEqual(['world']);
		engine.stepForward();
		expect(texts(engine.contextBefore)).toEqual(['Hello']);
		expect(texts(engine.contextAfter)).toEqual(['there']);
	});
});

// --- The block state machine (command-verifiable, no DOM) ---

describe('createReaderEngine — block state machine', () => {
	const codeAhead = (): SegmentView[] => [
		prose([word('Run'), word('this')]),
		pause('block_ahead'),
		block('code', 'x=1', { lang: 'py', lead: 'Run this' }),
		prose([word('Done')])
	];

	it('cues the block during the lead words, then auto-pauses on it when reached', () => {
		const fc = makeFakeClock();
		const engine = createReaderEngine({
			segments: codeAhead(),
			prefs: makePrefs({ ramp: false }),
			clock: fc.clock
		});
		expect(engine.blockNotches).toEqual([2]);

		engine.play();
		expect(engine.token?.text).toBe('Run');
		expect(engine.blockAhead).toBe(true);
		expect(engine.activeBlock).toBeNull();

		fc.advance(1000);
		expect(engine.token?.text).toBe('this');
		expect(engine.blockAhead).toBe(true);

		fc.advance(1000);
		expect(engine.activeBlock?.kind).toBe('code');
		expect(engine.activeBlock?.content).toBe('x=1');
		expect(engine.isPlaying).toBe(false);
		expect(engine.token).toBeNull();
		expect(engine.blockAhead).toBe(false);
		expect(engine.wordIndex).toBe(2);
	});

	it('toggle clears the active block and advances past it', () => {
		const fc = makeFakeClock();
		const engine = createReaderEngine({
			segments: codeAhead(),
			prefs: makePrefs({ ramp: false }),
			clock: fc.clock
		});
		engine.play();
		fc.advance(1000);
		fc.advance(1000);
		expect(engine.activeBlock?.kind).toBe('code');

		engine.toggle();
		expect(engine.activeBlock).toBeNull();
		expect(engine.token?.text).toBe('Done');
		expect(engine.isPlaying).toBe(true);
	});

	it('reshowLastBlock re-surfaces the most recent block, then toggle resumes', () => {
		const fc = makeFakeClock();
		const engine = createReaderEngine({
			segments: codeAhead(),
			prefs: makePrefs({ ramp: false }),
			clock: fc.clock
		});
		engine.play();
		fc.advance(1000);
		fc.advance(1000);
		engine.toggle(); // past the block, now on "Done"
		expect(engine.token?.text).toBe('Done');

		engine.reshowLastBlock();
		expect(engine.activeBlock?.content).toBe('x=1');
		expect(engine.isPlaying).toBe(false);
		expect(engine.token).toBeNull();

		engine.toggle();
		expect(engine.activeBlock).toBeNull();
		expect(engine.token?.text).toBe('Done');
		expect(engine.isPlaying).toBe(true);
	});

	it('reshowLastBlock is a no-op before any block has been seen', () => {
		const engine = createReaderEngine({
			segments: [prose([word('Hello')])],
			prefs: makePrefs({ ramp: false })
		});
		engine.play();
		engine.reshowLastBlock();
		expect(engine.activeBlock).toBeNull();
		expect(engine.token?.text).toBe('Hello');
	});

	it('a digest that opens on a block shows it on first play', () => {
		const segments: SegmentView[] = [
			pause('block_ahead'),
			block('table', '| a | b |'),
			prose([word('After')])
		];
		const engine = createReaderEngine({ segments, prefs: makePrefs({ ramp: false }) });
		expect(engine.activeBlock).toBeNull(); // nothing shown before play
		engine.play();
		expect(engine.activeBlock?.kind).toBe('table');
		expect(engine.isPlaying).toBe(false);
		engine.toggle();
		expect(engine.activeBlock).toBeNull();
		expect(engine.token?.text).toBe('After');
		expect(engine.isPlaying).toBe(true);
	});
});
