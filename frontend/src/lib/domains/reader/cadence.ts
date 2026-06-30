/**
 * The pure, headless reader core — R-CORE owns this file; `engine.svelte.ts` imports it.
 *
 * Two responsibilities, both pure functions of their arguments — no Svelte runes, no DOM, no
 * clock, no side effects — so the whole core is node-testable in isolation and the `.svelte.ts`
 * shell holds only reactive `$state` plus the rAF wiring:
 *
 *   1. Pacing math: `dwell = base × Π(multipliers)`, `base = 60000 / wpm` (default wpm 300 →
 *      base ≈ 200 ms), the ORP pivot bucket, the pause-after weights, and the speed ramp.
 *   2. Timeline flattening: walk the IR `SegmentView` list into the walkable frames + per-word
 *      pacing metadata the engine steps through (`buildTimeline`).
 *
 * The trailing-pause weight of a `Pause` that immediately follows a word is folded into that
 * word's dwell (RSVP holds the last word of a clause/sentence longer rather than showing a blank
 * beat). Designed gaps (capability facts, not roadmap): `Token.hold` and the `number`/`low_freq`
 * token classes are carried by the IR but NOT consumed here — there is no frequency lexicon in v1,
 * so the multiplier set below is the whole science. Reduced-motion gating is a dwell floor: a
 * reduced-motion reader never strobes.
 */
import type { BlockView, PauseView, SegmentView, TokenView } from './types';

// --- Pacing math ---

/** Why a pause occurs — the wire `PauseView['reason']`, aliased (not hand-duplicated) so a new
 *  backend reason makes `PAUSE_WEIGHTS` below fail exhaustiveness rather than silently gap. */
export type PauseReason = PauseView['reason'];

/** A word longer than this many characters earns the long-word multiplier. */
export const LONG_WORD_THRESHOLD = 8;
/** Extra dwell per character beyond the long-word threshold. */
export const LONG_WORD_PER_CHAR = 0.03;
/** The long-word multiplier never exceeds this. */
export const LONG_WORD_CAP = 1.4;
/** Multiplier for an agent-emphasised token (`emphasis !== 'none'`). */
export const EMPHASIS_MULTIPLIER = 1.25;
/** Multiplier for the first token after a pause or block. */
export const FIRST_AFTER_PAUSE_MULTIPLIER = 1.15;

/** Pause-after beat weights; the reader maps `reason` (× `duration_scale`) onto a dwell. */
export const PAUSE_WEIGHTS: Record<PauseReason, number> = {
	clause: 1.5,
	sentence: 2.2,
	paragraph: 2.8,
	// A block-ahead pause is a full stop plus the "block ahead" cue (sentence-weight beat).
	block_ahead: 2.2
};

/** Words over which the ramp eases speed in from its starting fraction to the target. */
export const RAMP_WORDS = 30;
/** The ramp starts at this fraction of the target wpm and eases to 1.0. */
export const RAMP_START_FRACTION = 0.45;
/** A reduced-motion reader's dwell never drops below this floor (no strobing). */
export const REDUCED_MOTION_MIN_DWELL_MS = 600;

/**
 * Base milliseconds per word at a given speed: `60000 / wpm`. The wpm is floored at 1 so a stray
 * non-positive preference can never freeze the reader (`Infinity` dwell) or yield a negative dwell.
 */
export function baseMs(wpm: number): number {
	return 60000 / Math.max(wpm, 1);
}

/** The long-word multiplier: `1` up to the threshold, then `1 + 0.03·(len − 8)` capped at 1.4. */
export function longWordMultiplier(wordLength: number): number {
	if (wordLength <= LONG_WORD_THRESHOLD) return 1;
	return Math.min(1 + LONG_WORD_PER_CHAR * (wordLength - LONG_WORD_THRESHOLD), LONG_WORD_CAP);
}

/** The pause-after weight for a reason, scaled by the pause's coarse `duration_scale`. */
export function pauseWeight(reason: PauseReason, durationScale = 1): number {
	return PAUSE_WEIGHTS[reason] * durationScale;
}

/**
 * The ORP pivot glyph index for a word — the Spritz bucket (`len ≤ 1 → 0, ≤ 5 → 1, ≤ 9 → 2,
 * ≤ 13 → 3, else 4`), clamped to a valid glyph index so it always lands inside the word.
 */
export function pivotIndex(wordLength: number): number {
	const bucket =
		wordLength <= 1 ? 0 : wordLength <= 5 ? 1 : wordLength <= 9 ? 2 : wordLength <= 13 ? 3 : 4;
	return Math.min(bucket, Math.max(wordLength - 1, 0));
}

/**
 * The eased speed for a word position: `targetWpm` once `ramp` is off or past `RAMP_WORDS`, else
 * linearly eased from `RAMP_START_FRACTION · targetWpm` up to `targetWpm` over the first words.
 */
export function rampedWpm(targetWpm: number, wordIndex: number, ramp: boolean): number {
	if (!ramp) return targetWpm;
	const progress = Math.min(Math.max(wordIndex, 0) / RAMP_WORDS, 1);
	const fraction = RAMP_START_FRACTION + (1 - RAMP_START_FRACTION) * progress;
	return targetWpm * fraction;
}

/** Inputs to a single word's dwell computation. */
export interface DwellInput {
	/** The effective speed for this word (already ramped, if ramping). */
	wpm: number;
	/** The word's character length. */
	wordLength: number;
	/** Whether the token carries agent emphasis. */
	emphasised: boolean;
	/** Whether this is the first word after a pause or block. */
	firstAfterPause: boolean;
	/** The reason of a pause that immediately follows this word, else null. */
	pauseReason: PauseReason | null;
	/** The `duration_scale` of that trailing pause (1 when there is none). */
	pauseScale?: number;
	/** Whether reduced motion is active (applies the dwell floor). */
	reducedMotion?: boolean;
}

/**
 * The dwell (ms) a word holds on the reticle: `base × long-word × emphasis × first-after-pause ×
 * trailing-pause-weight`, rounded; floored when reduced motion is active.
 */
export function dwellMs(input: DwellInput): number {
	let ms = baseMs(input.wpm) * longWordMultiplier(input.wordLength);
	if (input.emphasised) ms *= EMPHASIS_MULTIPLIER;
	if (input.firstAfterPause) ms *= FIRST_AFTER_PAUSE_MULTIPLIER;
	if (input.pauseReason) ms *= pauseWeight(input.pauseReason, input.pauseScale ?? 1);
	if (input.reducedMotion) ms = Math.max(ms, REDUCED_MOTION_MIN_DWELL_MS);
	return Math.round(ms);
}

// --- IR timeline flattening ---

/** A scheduled stop in the read timeline: a streamed word, or a block the stream pauses on. */
export type Frame = { type: 'word'; wIdx: number } | { type: 'block'; bIdx: number };

/** Per-word pacing metadata, computed once while walking the segment timeline. */
export interface WordMeta {
	/** This word is the first of its run AND a pause/block precedes it. */
	firstAfterPause: boolean;
	/** A pause that immediately follows this word (its weight folds into the word's dwell). */
	trailingPause: PauseView | null;
	/** The kind of the block this word leads into (the cue window), else null. */
	leadsToBlockKind: BlockView['kind'] | null;
}

/** The flattened timeline the engine walks: word stream, per-word meta, frames, and block index. */
export interface Timeline {
	words: TokenView[];
	wordMeta: WordMeta[];
	frames: Frame[];
	blocks: { block: BlockView; wordsBefore: number }[];
	blockNotches: number[];
	/** word ordinal → its frame index. */
	wordFrameIndexByWord: number[];
	/** frame index → number of words consumed before it (length `frames.length + 1`). */
	wordsBeforeFrame: number[];
}

/**
 * Flatten the IR segment timeline into a walkable list of frames plus per-word pacing metadata.
 * Pure: pauses are folded into the preceding word (not frames of their own), blocks become stop
 * frames, and the words of the run before a `block_ahead` pause are tagged as that block's cue.
 */
export function buildTimeline(segments: SegmentView[]): Timeline {
	const words: TokenView[] = [];
	const wordMeta: WordMeta[] = [];
	const frames: Frame[] = [];
	const blocks: { block: BlockView; wordsBefore: number }[] = [];
	let prevWasPauseOrBlock = false;
	let runWordIdxs: number[] = [];
	let pendingCue: number[] | null = null;

	for (const seg of segments) {
		if (seg.type === 'prose') {
			runWordIdxs = [];
			for (const tok of seg.tokens) {
				if (tok.kind !== 'word') continue;
				const wIdx = words.length;
				const firstAfterPause = runWordIdxs.length === 0 && prevWasPauseOrBlock;
				words.push(tok);
				wordMeta.push({ firstAfterPause, trailingPause: null, leadsToBlockKind: null });
				frames.push({ type: 'word', wIdx });
				runWordIdxs.push(wIdx);
			}
			prevWasPauseOrBlock = false;
		} else if (seg.type === 'pause') {
			const lastMeta = wordMeta[words.length - 1];
			if (lastMeta) lastMeta.trailingPause = seg;
			if (seg.reason === 'block_ahead') pendingCue = runWordIdxs.slice();
			prevWasPauseOrBlock = true;
		} else {
			const bIdx = blocks.length;
			blocks.push({ block: seg, wordsBefore: words.length });
			frames.push({ type: 'block', bIdx });
			if (pendingCue) {
				for (const wi of pendingCue) {
					const m = wordMeta[wi];
					if (m) m.leadsToBlockKind = seg.kind;
				}
				pendingCue = null;
			}
			prevWasPauseOrBlock = true;
			runWordIdxs = [];
		}
	}

	const blockNotches = blocks.map((b) => b.wordsBefore);
	const wordFrameIndexByWord: number[] = [];
	const wordsBeforeFrame: number[] = [];
	let consumed = 0;
	for (let i = 0; i < frames.length; i++) {
		wordsBeforeFrame[i] = consumed;
		const f = frames[i];
		if (f && f.type === 'word') {
			wordFrameIndexByWord[f.wIdx] = i;
			consumed++;
		}
	}
	wordsBeforeFrame[frames.length] = consumed;
	return { words, wordMeta, frames, blocks, blockNotches, wordFrameIndexByWord, wordsBeforeFrame };
}
