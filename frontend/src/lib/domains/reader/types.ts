/**
 * The reader prop contract — R-CORE owns and FREEZES this file.
 *
 * Every reader unit (modes, blocks, chrome, stage) imports its types from here and never
 * amends this file. The single cross-cutting decision the reader fan-out turns on: the engine
 * is the sole owner of position + pivot + dwell + the block state machine, so no presentational
 * unit ever recomputes pacing. The wire types are aliased directly off the typed seam
 * (`$lib/api/schema`), which emits each as a named `components['schemas'][…]` member.
 *
 * What this file does NOT do: it declares no runtime values. The `createReaderEngine` factory
 * and the default rAF clock live in `engine.svelte.ts` (runes require a `.svelte.ts` module);
 * the pure pacing math lives in `cadence.ts`. Consumers import the factory via `./index`.
 */
import type { components } from '$lib/api/schema';
import type { PrefsStore } from '$lib/domains/preferences/prefs.svelte';

// --- Wire types, aliased off the typed seam (F0 emits NAMED members; do not hand-alias) ---

export type TokenView = components['schemas']['TokenView'];
export type ProseSegmentView = components['schemas']['ProseSegmentView'];
export type PauseView = components['schemas']['PauseView'];
export type BlockView = components['schemas']['BlockView'];
export type PreferencesView = components['schemas']['PreferencesView'];

// Re-export PrefsStore so SettingsPanelProps and other reader units import
// through this contract file rather than crossing into the preferences domain directly.
export type { PrefsStore };

/** The reading-timeline element union, discriminated on `type` (mirrors the wire `SegmentView`). */
export type SegmentView = ProseSegmentView | PauseView | BlockView;

/**
 * The reading mode: "rsvp" | "guided" | "fading" | "focus".
 * "focus" routes to the Focus view (reuses ModeProps; no new view-prop type needed).
 */
export type Mode = PreferencesView['mode'];

// --- The engine's reactive snapshot ---

/**
 * The engine's reactive snapshot. Every field is computed ONCE by the engine; no presentational
 * unit recomputes pacing. Backed by `$state`/`$derived` inside `engine.svelte.ts`.
 */
export interface ReaderState {
	/** Word on the reticle now; null before first play and while a block shows. */
	token: TokenView | null;
	/** ORP glyph index into `token.text` (Spritz bucket); 0 when `token` is null. */
	pivotIndex: number;
	/** Engine-computed hold for `token` at current prefs; 0 when paused or `token` is null. */
	dwellMs: number;
	/** Already-read words for RSVP context, oldest→newest; length ≤ the prefs context window. */
	contextBefore: TokenView[];
	/** Upcoming words for RSVP context, nearest→furthest; length ≤ the prefs context window. */
	contextAfter: TokenView[];
	/** 0-based ordinal of `token` across all prose words; 0 at start. */
	wordIndex: number;
	/** Total prose word tokens in the digest (static). */
	wordCount: number;
	/** Transport state. */
	isPlaying: boolean;
	/** Non-null exactly while the stream is paused on a block card. */
	activeBlock: BlockView | null;
	/** True during the block-ahead cue window (the lead words before a block). */
	blockAhead: boolean;
	/** Stream exhausted (last word shown, no block pending). */
	atEnd: boolean;
	/** Estimated time-left at current pace (drives Progress "~2m 14s left"). */
	remainingMs: number;
	/** `wordIndex` of each block in the digest (Progress notches). */
	blockNotches: number[];
}

/**
 * The engine: the sole owner of position + pivot + dwell + the block state machine, and
 * headless-constructible — the factory holds ZERO `$effect`. Pure pacing (pivot, dwell,
 * remaining) is `$derived`; the next-token cadence is driven imperatively through the INJECTED
 * clock — started in `play()`, cancelled in `pause()`/`destroy()` — never a module-level
 * `requestAnimationFrame`/`performance.now` and never a reactive `$effect`. The pivot glyph's DOM
 * measure-and-translate onto the reticle is NOT the engine's job: it lives in R-MODES's
 * `Rsvp.svelte` `$effect` at the DOM boundary, reading `engine.pivotIndex` + `engine.token`. The
 * returned object exposes `ReaderState` via getters — read e.g. `engine.token`; NEVER destructure
 * (Svelte-5 rule) — plus the command surface.
 */
export interface ReaderEngine extends Readonly<ReaderState> {
	/** The full ordered prose word stream (Flow renders this). */
	readonly words: TokenView[];
	/** Current mode (drives R-STAGE's Rsvp-vs-Flow choice). */
	readonly mode: Mode;
	play(): void;
	pause(): void;
	/** Unified: if `activeBlock` → resume; else flip play/pause (Space / tap-stage). */
	toggle(): void;
	/** Advance one word/segment (Transport step button). */
	stepForward(): void;
	/** Step back one word (Transport replay button). */
	replayWord(): void;
	/** Re-display the most-recent block card (ArrowLeft); no-op if none. */
	reshowLastBlock(): void;
	/** Progress tap-to-scrub to a word ordinal. */
	scrubTo(wordIndex: number): void;
	/** Switch mode (R-STAGE persists it via PREF). */
	setMode(mode: Mode): void;
	/** Re-derive pacing when settings change. */
	setPrefs(prefs: PreferencesView): void;
	/** Clear timers (called from the owning `$effect` cleanup). */
	destroy(): void;
}

/**
 * The injected clock makes the engine DOM-free and steppable in a HEADLESS (node) test — the
 * `engine.test.ts` suite constructs the engine with a fake clock and advances it deterministically
 * (no rAF, no `performance.now`, no jsdom). The cadence math lives in the pure `cadence.ts`; this
 * shell holds only the frame-scheduler wiring.
 */
export interface ReaderClock {
	/** ms timestamp; default `() => performance.now()`. */
	now(): number;
	/**
	 * Request the next frame; returns its canceller. Default: `requestAnimationFrame` /
	 * `cancelAnimationFrame`. The tick receives the current `now()`.
	 */
	schedule(tick: (now: number) => void): () => void;
}

/** Constructor arguments for `createReaderEngine`. */
export interface CreateReaderEngineArgs {
	/** The IR timeline to read (prose, pauses, blocks). */
	segments: SegmentView[];
	/** The reading preferences that drive pacing. */
	prefs: PreferencesView;
	/** Injected time source + frame scheduler; defaults to the real rAF clock. */
	clock?: ReaderClock;
	/**
	 * Read ONCE at construction (default `matchMedia('(prefers-reduced-motion: reduce)')`); gates
	 * the word-flash cadence — a flashing reader is a seizure concern.
	 */
	reducedMotion?: boolean;
}

// --- Presentational prop contracts (no pacing maths in any of these) ---

/** Mode views (R-MODES: `Rsvp.svelte`, `Flow.svelte`). R-STAGE passes the engine as `state`. */
export interface ModeProps {
	/** "rsvp" → `Rsvp.svelte`; "guided" | "fading" → `Flow.svelte` (variant by mode). */
	mode: Mode;
	/** Reads token, pivotIndex, contextBefore/After, wordIndex. */
	state: ReaderState;
	/** Full prose stream (Flow renders all words, highlighting `state.wordIndex`). */
	words: TokenView[];
}

/** Block cards (R-BLOCKS: one component per `block.kind`). R-STAGE mounts the right card. */
export interface BlockCardProps {
	/** `kind` discriminates code | table | image | math | quote | note. */
	block: BlockView;
	/** True when surfaced by the ArrowLeft re-show (subtle "again" affordance). */
	reshown: boolean;
}

/** The "code ahead" chip (R-BLOCKS). */
export interface BlockAheadCueProps {
	/** Chip label ("code ahead", "table ahead", …). */
	kind: BlockView['kind'];
	/** = `ReaderState.blockAhead`. */
	visible: boolean;
}

/** Transport (R-CHROME: `Transport.svelte`). Stateless chrome; every action calls the engine. */
export interface TransportProps {
	/** = `ReaderState.isPlaying`. */
	isPlaying: boolean;
	/** Current speed (from Preferences). */
	wpm: number;
	/** → `engine.toggle()`. */
	onToggle: () => void;
	/** → `engine.replayWord()`. */
	onReplayWord: () => void;
	/** → `engine.stepForward()`. */
	onStepForward: () => void;
	/** Edge speed rail → PREF write-through. */
	onSpeed: (wpm: number) => void;
}

/** Progress (R-CHROME: `Progress.svelte`). */
export interface ProgressProps {
	/** = `ReaderState.wordIndex`. */
	wordIndex: number;
	/** = `ReaderState.wordCount`. */
	wordCount: number;
	/** = `ReaderState.remainingMs` (rendered "~2m 14s left", tabular-nums). */
	remainingMs: number;
	/** = `ReaderState.blockNotches` (block ticks). */
	blockNotches: number[];
	/** → `engine.scrubTo()`. */
	onScrub: (wordIndex: number) => void;
}

/**
 * Settings panel (R-CHROME). Props-down / callback-up: the panel reads and writes
 * preferences through `store`, never binding directly to its internals. Both U2
 * (the settings panel unit) and the integrator (R-STAGE) code against this shape.
 *
 * `$bindable` is deliberately absent — the panel does not co-own the store; it
 * calls `store.set(patch)` and the store drives reactivity.
 */
export interface SettingsPanelProps {
	/** The reactive preferences store (PREF's `createPrefsStore`). */
	store: PrefsStore;
	/** Whether the settings panel is open. */
	open: boolean;
	/** Called when the panel requests to be closed (e.g. Escape or overlay tap). */
	onClose: () => void;
}
