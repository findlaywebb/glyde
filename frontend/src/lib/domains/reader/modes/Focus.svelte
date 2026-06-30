<script lang="ts">
	/**
	 * The Focus view — clause-granularity reading; R-MODES owns this file.
	 *
	 * Distinct from RSVP (one word flashed) and Flow (the surrounding stream): Focus renders ONLY the
	 * current clause — the run of words between the parser's retained terminators (`clauseAt`). Past
	 * and future clauses are NOT rendered at all, so future text is never legible ahead of the band
	 * (future-hidden / read-removed is inherent to rendering a single clause). The clause sits at a
	 * fixed vertical band (~⅔ down); when the engine advances past the clause's last word the window
	 * changes and the block is keyed on its start index, so it DISCRETELY swaps (jump/replace) to the
	 * next clause — never a smooth scroll, never a translateY pursuit, no lookahead.
	 *
	 * Each clause word renders normally through the shared `Word` renderer, keeping full punctuation
	 * (`token.text`) and agent emphasis. Sizing comes from the stage via `--reading-size-flow`; this
	 * view reads no preferences and computes no pacing — it derives the clause purely from the
	 * engine's `wordIndex` over the full `words` stream (`ModeProps`), with no engine/contract change.
	 */
	import type { ModeProps } from '../types';
	import { clauseAt } from './clause';
	import Word from './Word.svelte';

	// Renamed off the `state` prop: a local binding named `state` would make a `$state` rune
	// ambiguous with a store auto-subscription (`store_rune_conflict`).
	let { state: reader, words }: ModeProps = $props();

	const clause = $derived(clauseAt(words, reader.wordIndex));
	const clauseWords = $derived(words.slice(clause.start, clause.end));
</script>

<div class="focus font-reading text-reading-foreground">
	<!-- Keyed on the clause start so a clause change destroys-and-recreates the band content: a
	     discrete swap (jump/replace), never an animated transition between clauses. -->
	{#key clause.start}
		<!-- Flex + gap separates the words and provides the wrap opportunities, so no whitespace
		     text nodes are needed between the inline word spans. -->
		<p class="clause">
			{#each clauseWords as token, i (clause.start + i)}
				<Word {token} />
			{/each}
		</p>
	{/key}
</div>

<style>
	.focus {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	/* The clause sits at a fixed band ~⅔ down the stage; it is replaced in place on a clause
	   change (never scrolled), so the eye returns to the same line every time. */
	.clause {
		position: absolute;
		top: 64%;
		left: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: center;
		gap: 0.1em 0.32em;
		width: min(60ch, 90%);
		margin: 0;
		line-height: 1.5;
		font-size: var(--reading-size-flow, clamp(1.5rem, 5vw, 2.4rem));
	}
</style>
