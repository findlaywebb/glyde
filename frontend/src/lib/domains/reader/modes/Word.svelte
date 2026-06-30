<script lang="ts">
	/**
	 * The shared emphasis word renderer — R-MODES owns this file; Rsvp / Flow / Focus import it.
	 *
	 * Renders a single prose token with its agent emphasis applied as distinct, NON-colour
	 * treatments (`strong` → heavier weight, `em` → italic, `code` → inline-code styling), so colour
	 * stays reserved for the RSVP pivot glyph. Emphasis lives here in one place rather than being
	 * re-implemented in each mode view. When `pivot` is a glyph index the word is split so that glyph
	 * is marked (`text-pivot`, `data-pivot`) as the optimal-recognition-point for RSVP; otherwise the
	 * word renders whole (Flow / Focus). The full `token.text` — punctuation retained by the parser —
	 * is always rendered verbatim.
	 *
	 * What it does NOT do: it computes no pacing, picks no pivot index (that is the engine's
	 * `pivotIndex`, passed in), and does no DOM measurement (Rsvp's `$effect` measures the marked
	 * glyph at the boundary by querying `[data-pivot]`). The split spans carry no whitespace between
	 * them, so left + pivot + right reconstruct the word exactly.
	 */
	import type { TokenView } from '../types';

	interface WordProps {
		/** The token to render (its `emphasis` drives the styling, its `text` the glyphs). */
		token: TokenView;
		/** ORP glyph index to mark as the pivot (RSVP); null/omitted renders the word whole. */
		pivot?: number | null;
	}

	let { token, pivot = null }: WordProps = $props();

	const text = $derived(token.text);
	const p = $derived(pivot ?? -1);
	const split = $derived(p >= 0 && p < text.length);
	const before = $derived(split ? text.slice(0, p) : '');
	const glyph = $derived(split ? text.charAt(p) : '');
	const after = $derived(split ? text.slice(p + 1) : '');
</script>

{#if split}<span class="w" data-em={token.emphasis}
		><span>{before}</span><span class="text-pivot" data-pivot>{glyph}</span><span>{after}</span
		></span
	>{:else}<span class="w" data-em={token.emphasis}>{text}</span>{/if}

<style>
	/* Emphasis treatments — distinct and non-colour; colour is reserved for the pivot glyph.
	   `none` matches no rule, so an un-emphasised word inherits the view's base styling. */
	.w[data-em='strong'] {
		font-weight: 800;
	}

	.w[data-em='em'] {
		font-style: italic;
	}

	.w[data-em='code'] {
		font-family: var(--font-mono);
		font-size: 0.9em;
		padding: 0 0.15em;
		border-radius: 0.2em;
		background: color-mix(in srgb, currentColor 12%, transparent);
	}
</style>
