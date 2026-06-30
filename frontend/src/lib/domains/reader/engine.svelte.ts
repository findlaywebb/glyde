/**
 * The reader pacing engine — R-CORE owns and FREEZES this file.
 *
 * `createReaderEngine` is the sole owner of position + pivot + dwell + the block state machine.
 * It is HEADLESS-constructible: the factory holds ZERO `$effect`, takes an INJECTED clock, and
 * exposes `$state`/`$derived` via getters plus an imperative command surface — so it constructs
 * and steps in a node test with no DOM (see `engine.test.ts`). Pure pacing (pivot, dwell,
 * remaining) is `$derived`; the next-token cadence runs imperatively through the clock, started
 * in `play()` and cancelled in `pause()`/`destroy()` — never a module-level `requestAnimationFrame`
 * / `performance.now`, never a reactive `$effect`.
 *
 * This is the THIN `.svelte.ts` shell of the assay pure-core / thin-rAF-shell split: all pure
 * logic — the pacing math AND the IR timeline flattening — lives in `cadence.ts`; this file holds
 * only reactive state, the frame-scheduler wiring, and the command surface. What it does NOT do:
 * it never measures or translates the pivot glyph onto the reticle (that DOM work is R-MODES's
 * `$effect` at the boundary), and it registers no `window` listeners (R-STAGE owns the single
 * global keyboard + tap listener). It reads `reducedMotion` once at construction and gates the
 * word-flash cadence on it via a dwell floor.
 */
import * as cadence from './cadence';
import type {
	BlockView,
	CreateReaderEngineArgs,
	PreferencesView,
	ReaderClock,
	ReaderEngine,
	TokenView
} from './types';

/** The real rAF clock; falls back to `setTimeout`/`Date.now` when no rAF exists (node default). */
function defaultClock(): ReaderClock {
	return {
		now: () => (typeof performance !== 'undefined' ? performance.now() : Date.now()),
		schedule: (tick) => {
			if (typeof requestAnimationFrame === 'undefined') {
				const id = setTimeout(() => tick(Date.now()), 16);
				return () => clearTimeout(id);
			}
			const id = requestAnimationFrame(tick);
			return () => cancelAnimationFrame(id);
		}
	};
}

/** Whether the platform reports a reduced-motion preference (false where `matchMedia` is absent). */
function defaultReducedMotion(): boolean {
	return (
		typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
	);
}

/** The number of RSVP context words shown each side, per the context treatment. */
function ctxWindow(context: PreferencesView['context']): number {
	switch (context) {
		case 'off':
			return 0;
		case 'ab':
			return 1;
		case 'line':
			return 3;
		case 'sentence':
			return 6;
	}
}

/**
 * Construct a headless reader pacing engine over an IR timeline.
 *
 * The returned object exposes `ReaderState` via getters (never destructure — Svelte-5 rule) plus
 * the imperative command surface. Pacing recomputes reactively when `setPrefs`/`setMode` change
 * the preferences; the word cadence advances through the injected `clock`.
 */
export function createReaderEngine(args: CreateReaderEngineArgs): ReaderEngine {
	const { words, wordMeta, frames, blocks, blockNotches, wordFrameIndexByWord, wordsBeforeFrame } =
		cadence.buildTimeline(args.segments);
	const wordCount = words.length;
	const reducedMotion = args.reducedMotion ?? defaultReducedMotion();
	const clock = args.clock ?? defaultClock();

	let frameIndex = $state(0);
	let playing = $state(false);
	let hasStarted = $state(false);
	let prefs = $state(args.prefs);
	let reshownBlockIndex = $state<number | null>(null);
	let lastBlockIndex = $state<number | null>(null);

	let cancel: (() => void) | null = null;
	let wordStartedAt = 0;

	// --- Pure helpers over the (non-reactive) timeline ---

	function frameIsBlock(i: number): boolean {
		const f = frames[i];
		return !!f && f.type === 'block';
	}

	/** The dwell (ms) the word at `wIdx` holds, at the current prefs and ramp position. */
	function dwellForWord(wIdx: number): number {
		const tok = words[wIdx];
		const meta = wordMeta[wIdx];
		if (!tok || !meta) return 0;
		return cadence.dwellMs({
			wpm: cadence.rampedWpm(prefs.wpm, wIdx, prefs.ramp),
			wordLength: tok.text.length,
			emphasised: tok.emphasis !== 'none',
			firstAfterPause: meta.firstAfterPause,
			pauseReason: meta.trailingPause ? meta.trailingPause.reason : null,
			pauseScale: meta.trailingPause ? meta.trailingPause.duration_scale : 1,
			reducedMotion
		});
	}

	function prevWordFrame(i: number): number | null {
		for (let k = Math.min(i, frames.length) - 1; k >= 0; k--) {
			const f = frames[k];
			if (f && f.type === 'word') return k;
		}
		return null;
	}

	// --- Cadence loop (imperative; the only timing path — no `$effect`) ---

	function stopLoop(): void {
		if (cancel) {
			cancel();
			cancel = null;
		}
	}

	function tick(now: number): void {
		cancel = null;
		if (!playing) return;
		const f = frames[frameIndex];
		if (!f || f.type !== 'word') {
			playing = false;
			return;
		}
		if (now - wordStartedAt >= dwellForWord(f.wIdx)) {
			goTo(frameIndex + 1);
			wordStartedAt = now;
			if (frameIndex >= frames.length) playing = false;
		}
		if (playing) cancel = clock.schedule(tick);
	}

	/** Move the cursor to a frame; landing on a block auto-pauses and records it for re-show. */
	function goTo(i: number): void {
		reshownBlockIndex = null;
		frameIndex = i;
		const f = frames[i];
		if (f && f.type === 'block') {
			lastBlockIndex = f.bIdx;
			playing = false;
			stopLoop();
		}
	}

	// --- Reactive snapshot (every field a `$derived` of state; no `$effect`) ---

	const activeBlock = $derived.by((): BlockView | null => {
		if (reshownBlockIndex !== null) return blocks[reshownBlockIndex]?.block ?? null;
		if (!hasStarted) return null;
		const f = frames[frameIndex];
		return f && f.type === 'block' ? (blocks[f.bIdx]?.block ?? null) : null;
	});

	const token = $derived.by((): TokenView | null => {
		if (!hasStarted || reshownBlockIndex !== null) return null;
		const f = frames[frameIndex];
		if (!f || f.type !== 'word') return null;
		return words[f.wIdx] ?? null;
	});

	const wordIndex = $derived(wordsBeforeFrame[Math.min(frameIndex, frames.length)] ?? wordCount);
	const pivotIndex = $derived(token ? cadence.pivotIndex(token.text.length) : 0);
	const atEnd = $derived(frameIndex >= frames.length);
	const remainingMs = $derived(
		Math.max(0, Math.round(((wordCount - wordIndex) * 60000) / prefs.wpm))
	);

	const dwellMs = $derived.by((): number => {
		if (!playing) return 0;
		const f = frames[frameIndex];
		if (!f || f.type !== 'word') return 0;
		return dwellForWord(f.wIdx);
	});

	const blockAhead = $derived.by((): boolean => {
		if (!hasStarted || reshownBlockIndex !== null) return false;
		const f = frames[frameIndex];
		if (!f || f.type !== 'word') return false;
		return (wordMeta[f.wIdx]?.leadsToBlockKind ?? null) !== null;
	});

	const contextBefore = $derived.by((): TokenView[] => {
		const w = ctxWindow(prefs.context);
		if (!token || w <= 0) return [];
		return words.slice(Math.max(0, wordIndex - w), wordIndex);
	});

	const contextAfter = $derived.by((): TokenView[] => {
		const w = ctxWindow(prefs.context);
		if (!token || w <= 0) return [];
		return words.slice(wordIndex + 1, wordIndex + 1 + w);
	});

	// --- Command surface ---

	function play(): void {
		hasStarted = true;
		if (reshownBlockIndex !== null) reshownBlockIndex = null;
		if (frameIndex >= frames.length) {
			playing = false;
			return;
		}
		if (frameIsBlock(frameIndex)) {
			goTo(frameIndex); // show the block (auto-pause); play cannot run through it
			return;
		}
		playing = true;
		wordStartedAt = clock.now();
		if (!cancel) cancel = clock.schedule(tick);
	}

	function pause(): void {
		playing = false;
		stopLoop();
	}

	function toggle(): void {
		if (activeBlock) {
			if (reshownBlockIndex !== null) {
				reshownBlockIndex = null; // dismiss the re-show overlay, resume the underlying stream
			} else {
				goTo(frameIndex + 1); // advance past the block we were viewing
			}
			play();
			return;
		}
		if (playing) pause();
		else play();
	}

	function stepForward(): void {
		hasStarted = true;
		reshownBlockIndex = null;
		if (frameIndex >= frames.length) return;
		goTo(frameIndex + 1);
		if (frameIndex >= frames.length) {
			pause();
			return;
		}
		if (playing && !frameIsBlock(frameIndex)) wordStartedAt = clock.now();
	}

	function replayWord(): void {
		hasStarted = true;
		reshownBlockIndex = null;
		const j = prevWordFrame(frameIndex);
		goTo(j ?? 0);
		if (playing && !frameIsBlock(frameIndex)) wordStartedAt = clock.now();
	}

	function reshowLastBlock(): void {
		if (lastBlockIndex === null) return;
		reshownBlockIndex = lastBlockIndex;
		playing = false;
		stopLoop();
	}

	function scrubTo(target: number): void {
		if (words.length === 0) return;
		hasStarted = true;
		reshownBlockIndex = null;
		const clamped = Math.max(0, Math.min(target, words.length - 1));
		const fi = wordFrameIndexByWord[clamped];
		if (fi === undefined) return;
		goTo(fi);
		if (playing && !frameIsBlock(frameIndex)) wordStartedAt = clock.now();
	}

	function setMode(mode: PreferencesView['mode']): void {
		prefs.mode = mode;
	}

	function setPrefs(next: PreferencesView): void {
		prefs = next;
	}

	function destroy(): void {
		playing = false;
		stopLoop();
	}

	return {
		get token() {
			return token;
		},
		get pivotIndex() {
			return pivotIndex;
		},
		get dwellMs() {
			return dwellMs;
		},
		get contextBefore() {
			return contextBefore;
		},
		get contextAfter() {
			return contextAfter;
		},
		get wordIndex() {
			return wordIndex;
		},
		get wordCount() {
			return wordCount;
		},
		get isPlaying() {
			return playing;
		},
		get activeBlock() {
			return activeBlock;
		},
		get blockAhead() {
			return blockAhead;
		},
		get atEnd() {
			return atEnd;
		},
		get remainingMs() {
			return remainingMs;
		},
		get blockNotches() {
			return blockNotches;
		},
		get words() {
			return words;
		},
		get mode() {
			return prefs.mode;
		},
		play,
		pause,
		toggle,
		stepForward,
		replayWord,
		reshowLastBlock,
		scrubTo,
		setMode,
		setPrefs,
		destroy
	};
}
