<script lang="ts">
	/**
	 * The single-word RSVP view — Glyde's signature presentation; R-MODES owns this file.
	 *
	 * Reads the engine snapshot (`ReaderState`) and renders the current word split into
	 * left / pivot / right around the engine's optimal-recognition-point (`pivotIndex`), through the
	 * shared `Word` renderer (which also applies the token's agent emphasis). The pivot glyph is the
	 * one reserved reading colour (`text-pivot`) and is locked to a fixed reticle column by a DOM
	 * measure-and-translate in the `$effect` below — measuring the rendered glyph (`[data-pivot]`) and
	 * shifting the word so the glyph's centre sits on the column, font- and length-agnostic.
	 * Surrounding context words are dimmed (`text-reading-dim`) on their own rows above and below,
	 * positioned clear of the word band and centred on the same column as the pivot, so they never
	 * perturb or crowd the pivot.
	 *
	 * What it does NOT do: it computes no pacing (dwell is the engine's), binds no keys or `window`
	 * listeners (R-STAGE owns the single global listener), and never colours anything but the pivot.
	 * Exception: when the engine's `token` is null (before first play, or paused) it falls back to
	 * `words[wordIndex]` so the view is never blank at rest, and it computes the pivot index for
	 * that fallback word itself (the engine emits `pivotIndex === 0` when `token` is null). During
	 * playback the engine's `pivotIndex` is used directly. Sizing comes from the stage via
	 * `--reading-size` / `--reading-letter-spacing` custom properties, so this view inherits the
	 * user's preferences without reading them directly.
	 */
	import type { ModeProps } from '../types';
	import { pivotIndex as computePivot } from '../cadence';
	import { pivotTranslateX } from './measure';
	import Word from './Word.svelte';

	// Renamed off the `state` prop: a local binding named `state` would make the `$state` rune
	// below ambiguous with a store auto-subscription (`store_rune_conflict`).
	let { state: reader, words }: ModeProps = $props();

	const token = $derived(reader.token);
	const pivot = $derived(reader.pivotIndex);
	const contextBefore = $derived(reader.contextBefore);
	const contextAfter = $derived(reader.contextAfter);
	const wordIndex = $derived(reader.wordIndex);

	// At rest (before first play, or while paused) the engine's `token` is null. Fall back to the
	// word at `wordIndex` in the full `words` stream — the same source Focus/Flow use — so the
	// reader is never blank at the initial position or at any paused position.
	const displayToken = $derived(token ?? words[wordIndex] ?? null);

	// The engine sets `pivotIndex === 0` whenever `token` is null (engine.svelte.ts). For the
	// fallback word we compute the true ORP ourselves so the red glyph lands on the right character.
	// During playback `token` is non-null and we use the engine's pre-computed value directly.
	const displayPivot = $derived(
		token ? pivot : displayToken ? computePivot(displayToken.text.length) : 0
	);

	let wordEl = $state<HTMLSpanElement | null>(null);
	let translateX = $state(0);

	// DOM boundary: after each word renders, measure the pivot glyph (the `[data-pivot]` span the
	// shared Word renderer marks) and translate the word so the glyph centre lands on the reticle
	// column. Reading `displayToken` + `displayPivot` registers them as deps so the measure re-runs
	// on every word change; `translateX` is written but not read, so no loop.
	$effect(() => {
		void displayToken;
		void displayPivot;
		const word = wordEl;
		const wrap = word?.parentElement;
		const mark = word?.querySelector<HTMLElement>('[data-pivot]');
		if (!word || !wrap || !mark) return;
		translateX = pivotTranslateX(wrap.clientWidth, mark.offsetLeft, mark.offsetWidth);
	});
</script>

<div class="rsvp-stage font-reading text-reading-foreground">
	{#if displayToken}
		{#if contextBefore.length > 0}
			<div class="ctx-row ctx-above text-reading-dim" aria-hidden="true">
				<span class="ctx-text">{contextBefore.map((t) => t.text).join(' ')}</span>
			</div>
		{/if}

		<div class="reticle" aria-hidden="true">
			<span class="tick tick-top bg-muted-foreground/40"></span>
			<span class="tick tick-bottom bg-muted-foreground/40"></span>
		</div>

		<div class="word-wrap">
			<span class="word" bind:this={wordEl} style:transform="translate({translateX}px, -50%)">
				<Word token={displayToken} pivot={displayPivot} />
			</span>
		</div>

		{#if contextAfter.length > 0}
			<div class="ctx-row ctx-below text-reading-dim" aria-hidden="true">
				<span class="ctx-text">{contextAfter.map((t) => t.text).join(' ')}</span>
			</div>
		{/if}
	{/if}
</div>

<style>
	.rsvp-stage {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		height: 100%;
		font-size: var(--reading-size, clamp(2.5rem, 9vw, 4.5rem));
		letter-spacing: var(--reading-letter-spacing, 0.04em);
	}

	/* The word layer: measured then translated so the pivot glyph sits on the reticle column. */
	.word-wrap {
		position: relative;
		width: 100%;
		height: 1.5em;
		overflow: hidden;
	}

	.word {
		position: absolute;
		top: 50%;
		left: 0;
		white-space: nowrap;
		font-weight: 700;
		line-height: 1;
	}

	/* Fixation reticle — ticks above and below the pivot column. Never red (only the glyph is). */
	.reticle {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		pointer-events: none;
	}

	.tick {
		position: absolute;
		left: 50%;
		width: 2px;
		height: 0.55em;
		transform: translateX(-50%);
		border-radius: 1px;
	}

	.tick-top {
		bottom: 1.05em;
	}

	.tick-bottom {
		top: 1.05em;
	}

	/* Context rows live on their own zero-height layer so they never shift the pivot. The layer
	   inherits the stage font-size (the small text size is on .ctx-text), so the vertical offset is
	   expressed in STAGE em and scales with the reading size — clearing the word band above/below
	   rather than overlapping it (the previous offset was in the shrunk context font, far too small).
	   `justify-content: center` locks the row to the stage midpoint, the column the reticle sits on
	   and onto which the pivot glyph is translated — so context stays aligned with the pivot. */
	.ctx-row {
		position: absolute;
		left: 0;
		right: 0;
		top: 50%;
		height: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		line-height: 1;
		pointer-events: none;
	}

	.ctx-above {
		transform: translateY(-1.5em);
	}

	.ctx-below {
		transform: translateY(1.5em);
	}

	.ctx-text {
		max-width: 100%;
		font-size: 0.42em;
		font-weight: 400;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
</style>
