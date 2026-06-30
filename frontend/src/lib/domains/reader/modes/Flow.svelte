<script lang="ts">
	/**
	 * The Flow view — Guided sweep and Fading trail; R-MODES owns this file.
	 *
	 * Both variants read at clause granularity: only the CURRENT clause (the run of words between the
	 * parser's retained terminators, via `clauseAt`) is rendered, at a fixed vertical band, and it
	 * swaps DISCRETELY (keyed on the clause start — a jump/replace, never a smooth scroll) when the
	 * engine advances past the clause. Nothing beyond the current clause is rendered, so neither
	 * variant invites skip-ahead. Two treatments, chosen by `mode`:
	 *   - guided: already-read words are REMOVED (not dimmed); the current word onward to the clause
	 *     end remains, the current word carrying a pivot-coloured underline (no bold — bold reflows).
	 *   - fading: every clause word is rendered; already-read words fade fully out, the current word
	 *     is at full presence, and the road ahead within the clause is dimmed.
	 *
	 * Motion discipline: the only animation is the compositor-only opacity transition on the fade
	 * trail, gated on `prefers-reduced-motion` (read once at mount) — a reduced-motion reader gets the
	 * instant outcome with no fade travel. Words render through the shared `Word` renderer (full
	 * punctuation + emphasis). Sizing comes from the stage via `--reading-size-flow`; this view reads
	 * no preferences and computes no pacing — it derives the clause from `wordIndex` over `words`.
	 */
	import type { ModeProps } from '../types';
	import { clauseAt } from './clause';
	import Word from './Word.svelte';

	// Renamed off the `state` prop: a local binding named `state` would make a `$state` rune
	// ambiguous with a store auto-subscription (`store_rune_conflict`).
	let { mode, state: reader, words }: ModeProps = $props();

	const wordIndex = $derived(reader.wordIndex);
	const clause = $derived(clauseAt(words, wordIndex));
	const clauseWords = $derived(words.slice(clause.start, clause.end));

	// Read once at mount — the motion gate. A reduced-motion reader never gets the fade transition.
	const reducedMotion =
		typeof window !== 'undefined' &&
		typeof window.matchMedia === 'function' &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/** The read/current/ahead state of a clause word at absolute stream index `abs`. */
	function flowState(abs: number): 'read' | 'cur' | 'ahead' {
		if (abs < wordIndex) return 'read';
		if (abs === wordIndex) return 'cur';
		return 'ahead';
	}
</script>

<div
	class="flow font-reading text-reading-foreground"
	class:reduced={reducedMotion}
	data-mode={mode}
>
	<!-- Keyed on the clause start so a clause change destroys-and-recreates the band content: a
	     discrete swap (jump/replace), never an animated transition between clauses. -->
	{#key clause.start}
		<div class="flow-content">
			{#each clauseWords as token, i (clause.start + i)}
				{@const abs = clause.start + i}
				{@const fstate = flowState(abs)}
				<!-- Guided REMOVES already-read words; fading keeps them (to fade out). The single
				     `data-flow-state` attribute is the one source of the per-word treatment (CSS keys
				     off it), rather than mirroring it into separate classes. -->
				{#if mode === 'fading' || fstate !== 'read'}
					<span class="fw" data-flow-state={fstate}>
						<Word {token} />
					</span>
				{/if}
			{/each}
		</div>
	{/key}
</div>

<style>
	.flow {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	/* The current clause sits at a fixed band ~⅗ down the stage and is replaced in place on a
	   clause change (never scrolled), so the eye returns to the same line every time. */
	.flow-content {
		position: absolute;
		top: 60%;
		left: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: center;
		gap: 0.1em 0.32em;
		width: min(60ch, 90%);
		line-height: 1.5;
		font-size: var(--reading-size-flow, clamp(1.5rem, 5vw, 2.4rem));
	}

	/* The single animation: compositor-only opacity, gated off for reduced-motion readers. */
	.flow:not(.reduced) .fw {
		transition: opacity 0.35s ease;
	}

	/* Fading trail: read words fade fully out (guided removes them from the DOM instead). */
	.flow[data-mode='fading'] .fw[data-flow-state='read'] {
		opacity: 0;
	}

	/* Fading trail: the road ahead within the clause is dimmed, never bright. */
	.flow[data-mode='fading'] .fw[data-flow-state='ahead'] {
		opacity: 0.35;
	}

	/* The current word's marker: the pivot-coloured underline (no bold — bold reflows the line). */
	.fw[data-flow-state='cur'] {
		text-decoration-line: underline;
		text-decoration-color: var(--color-pivot);
		text-decoration-thickness: 0.08em;
		text-underline-offset: 0.18em;
	}
</style>
