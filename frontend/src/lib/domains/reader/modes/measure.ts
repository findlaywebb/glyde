/**
 * The RSVP pivot-centring maths — R-MODES owns this file; `Rsvp.svelte` imports it.
 *
 * Split out as a pure function so the signature behaviour (the optimal-recognition-point glyph
 * locked to a fixed reticle column) is node-testable without a layout engine: `Rsvp.svelte`
 * measures the rendered glyph at the DOM boundary, this function turns those measurements into
 * the horizontal translate. It does NOT pick the pivot glyph — that index is the engine's
 * `pivotIndex` (Spritz bucket), carried on `ReaderState`; this file only positions it.
 */

/**
 * The horizontal translate (px) that lands the pivot glyph's centre on the reticle column.
 *
 * The reticle sits at the container's horizontal midpoint, so the word must shift by the gap
 * between that midpoint and the glyph's measured centre. A positive result moves the word right.
 */
export function pivotTranslateX(
	containerWidth: number,
	pivotOffsetLeft: number,
	pivotWidth: number
): number {
	return containerWidth / 2 - (pivotOffsetLeft + pivotWidth / 2);
}
