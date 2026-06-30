/**
 * Reader input — the pure key/gesture classifiers and the `bindSwipe` DOM adapter (R-STAGE owns).
 *
 * R-STAGE is the SOLE owner of the reader's global keyboard and pointer input (§5.7): no mode,
 * block, or chrome unit registers a `window` listener. This module splits that ownership the
 * assay way (docs/research/assay-adoption.md §1) — a pure, node-testable core and a thin DOM
 * shell:
 *
 *   - `keyToIntent(key)` — a pure `switch` mapping a `KeyboardEvent.key` to a reader command, so
 *     the markup handler stays tiny and the mapping is unit-testable with no DOM.
 *   - `classifySwipe(trajectory)` — a pure classifier turning a pointer trajectory into a tap, a
 *     forward/back seek, or nothing (axis-locked: a vertical drag yields to native scroll).
 *   - `clampWpm(wpm)` — the REAL speed clamp R-STAGE owns; R-CHROME's Transport only
 *     display-clamps (a documented hand-off, §5.7), so R-STAGE clamps before pacing/persisting.
 *   - `bindSwipe(target, handlers)` — the Pointer-Events adapter: single primary pointer,
 *     axis-lock past 8px, feature-detected `setPointerCapture`, an injected ignore predicate for
 *     interactive controls, returning a teardown for an owning `$effect`.
 *
 * What this module does NOT do: it holds no reactive state (no runes), reads no preferences, and
 * touches the engine through none of its own imports — the caller wires intents to engine methods.
 */

/** A reader command the keyboard/gesture layer can request of the engine. */
export type ReaderIntent = 'toggle' | 'stepForward' | 'reshowLastBlock';

/** The Transport-supported speed-rail lower bound (wpm); R-STAGE clamps to these before pacing. */
export const MIN_WPM = 100;
/** The Transport-supported speed-rail upper bound (wpm). */
export const MAX_WPM = 800;

/** Movement under this (px) on BOTH axes is a tap, not a swipe. Also the axis-lock threshold. */
export const SWIPE_LOCK_PX = 8;
/** A swipe committed purely by distance once the horizontal travel reaches this (px). */
export const SWIPE_DISTANCE_PX = 45;
/** The minimum horizontal travel (px) a velocity flick still needs. */
export const SWIPE_FLICK_PX = 40;
/** The flick velocity (px/ms) that commits a short-but-fast horizontal swipe. */
export const SWIPE_FLICK_VELOCITY = 0.3;

/**
 * Clamp a words-per-minute value into the Transport-supported range.
 *
 * R-STAGE owns the real clamp (§5.7): `NaN` (a parse failure) falls to the safe {@link MIN_WPM},
 * and any other value is rounded then bounded to `[MIN_WPM, MAX_WPM]` (so `±Infinity` saturate to
 * the ceiling/floor) — neither the engine's pacing nor the persisted preference ever carries an
 * out-of-range speed.
 *
 * @param wpm The requested speed.
 * @returns The speed clamped to `[MIN_WPM, MAX_WPM]`.
 */
export function clampWpm(wpm: number): number {
	if (Number.isNaN(wpm)) return MIN_WPM;
	return Math.min(Math.max(Math.round(wpm), MIN_WPM), MAX_WPM);
}

/**
 * Map a `KeyboardEvent.key` to a reader command, or `null` when the key is not a shortcut.
 *
 * The reader's three keyboard shortcuts (§5.7): Space toggles play/pause (and resumes from a
 * block); ArrowRight steps one word/segment forward; ArrowLeft re-shows the most-recent block.
 * `'Spacebar'` is accepted for older engines that report the legacy key name.
 *
 * @param key The `key` property of a `KeyboardEvent`.
 * @returns The mapped {@link ReaderIntent}, or `null` for any unhandled key.
 */
export function keyToIntent(key: string): ReaderIntent | null {
	switch (key) {
		case ' ':
		case 'Spacebar':
			return 'toggle';
		case 'ArrowRight':
			return 'stepForward';
		case 'ArrowLeft':
			return 'reshowLastBlock';
		default:
			return null;
	}
}

/** A completed pointer trajectory: net displacement and elapsed time. */
export interface SwipeTrajectory {
	/** Net horizontal displacement (px); negative = leftward (forward). */
	dx: number;
	/** Net vertical displacement (px). */
	dy: number;
	/** Elapsed time of the gesture (ms). */
	dt: number;
}

/** The outcome of classifying a pointer trajectory. */
export type SwipeAction = 'tap' | 'next' | 'prev' | null;

/**
 * Classify a completed pointer trajectory as a tap, a forward/back seek, or nothing.
 *
 * Axis-locked the assay way (docs/research/assay-adoption.md §1): a near-stationary gesture is a
 * `tap`; a predominantly vertical gesture yields to native scroll (`null`); a predominantly
 * horizontal gesture commits by distance OR velocity (not both), seeking forward on a leftward
 * swipe (`next`) and back on a rightward swipe (`prev`).
 *
 * @param t The completed trajectory.
 * @returns `'tap'`, `'next'`, `'prev'`, or `null` when the gesture commits to nothing.
 */
export function classifySwipe(t: SwipeTrajectory): SwipeAction {
	const ax = Math.abs(t.dx);
	const ay = Math.abs(t.dy);
	if (ax < SWIPE_LOCK_PX && ay < SWIPE_LOCK_PX) return 'tap';
	if (ax <= ay) return null; // vertical-dominant → yield to native scroll
	const velocity = t.dt > 0 ? ax / t.dt : 0;
	const committed =
		ax >= SWIPE_DISTANCE_PX || (ax >= SWIPE_FLICK_PX && velocity >= SWIPE_FLICK_VELOCITY);
	if (!committed) return null;
	return t.dx < 0 ? 'next' : 'prev';
}

/** The callbacks `bindSwipe` invokes once a gesture is classified. */
export interface SwipeHandlers {
	/** A near-stationary tap on the stage (→ toggle play/pause). */
	onTap?: () => void;
	/** A committed forward (leftward) seek. */
	onNext?: () => void;
	/** A committed back (rightward) seek. */
	onPrev?: () => void;
	/** Predicate: a gesture starting on a matching target is left to native handling. */
	isIgnored?: (target: EventTarget | null) => boolean;
}

/**
 * Bind tap/swipe gestures on a stage element, returning a teardown for the owning `$effect`.
 *
 * Pointer Events only (one model for touch/pen/mouse), a single primary pointer guarded by
 * `pointerId`, axis-lock on the first move past {@link SWIPE_LOCK_PX} (a vertical lock yields the
 * rest of the gesture to native scroll), and feature-detected `setPointerCapture` (absent in
 * jsdom — wrapped so it is non-fatal). The decision itself is the pure {@link classifySwipe}, so
 * only the wiring lives here. A gesture whose `pointerdown` target satisfies `isIgnored` (e.g. a
 * Transport button inside the stage) is left entirely to native handling.
 *
 * @param target The stage element to listen on.
 * @param handlers The tap/seek callbacks and the optional ignore predicate.
 * @returns A teardown that detaches every listener.
 */
export function bindSwipe(target: HTMLElement, handlers: SwipeHandlers): () => void {
	let activePointer: number | null = null;
	let startX = 0;
	let startY = 0;
	let startT = 0;
	let axis: 'horizontal' | 'vertical' | null = null;

	function onPointerDown(event: PointerEvent): void {
		if (activePointer !== null) return; // ignore a second finger mid-gesture
		if (handlers.isIgnored?.(event.target)) return;
		activePointer = event.pointerId;
		startX = event.clientX;
		startY = event.clientY;
		startT = event.timeStamp;
		axis = null;
		try {
			target.setPointerCapture(event.pointerId);
		} catch {
			// jsdom and some browsers lack pointer capture — non-fatal.
		}
	}

	function onPointerMove(event: PointerEvent): void {
		if (event.pointerId !== activePointer || axis !== null) return;
		const dx = Math.abs(event.clientX - startX);
		const dy = Math.abs(event.clientY - startY);
		if (dx > SWIPE_LOCK_PX || dy > SWIPE_LOCK_PX) {
			axis = dx > dy ? 'horizontal' : 'vertical';
		}
	}

	function onPointerUp(event: PointerEvent): void {
		if (event.pointerId !== activePointer) return;
		const trajectory: SwipeTrajectory = {
			dx: event.clientX - startX,
			dy: event.clientY - startY,
			dt: Math.max(0, event.timeStamp - startT)
		};
		const lockedVertical = axis === 'vertical';
		release(event.pointerId);
		if (lockedVertical) return; // a vertical drag is native scroll, never a seek
		const action = classifySwipe(trajectory);
		if (action === 'tap') handlers.onTap?.();
		else if (action === 'next') handlers.onNext?.();
		else if (action === 'prev') handlers.onPrev?.();
	}

	function onPointerCancel(event: PointerEvent): void {
		if (event.pointerId !== activePointer) return;
		release(event.pointerId);
	}

	function release(pointerId: number): void {
		activePointer = null;
		axis = null;
		try {
			target.releasePointerCapture(pointerId);
		} catch {
			// Already released or unsupported — non-fatal.
		}
	}

	target.addEventListener('pointerdown', onPointerDown);
	target.addEventListener('pointermove', onPointerMove);
	target.addEventListener('pointerup', onPointerUp);
	target.addEventListener('pointercancel', onPointerCancel);

	return () => {
		target.removeEventListener('pointerdown', onPointerDown);
		target.removeEventListener('pointermove', onPointerMove);
		target.removeEventListener('pointerup', onPointerUp);
		target.removeEventListener('pointercancel', onPointerCancel);
	};
}
