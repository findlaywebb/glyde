<script lang="ts">
	/**
	 * The single-word RSVP view — Glyde's signature presentation.
	 *
	 * Reads the engine snapshot (`ReaderState`) and renders the current word split into
	 * left / pivot / right around the engine's optimal-recognition-point (`pivotIndex`). The
	 * pivot glyph is the one reserved reading colour (`text-pivot`) and is locked to a fixed
	 * reticle column by a DOM measure-and-translate in the `$effect` below — measuring the
	 * rendered glyph and shifting the word so the glyph's centre sits on the column, font- and
	 * length-agnostic. Surrounding context words are dimmed (`text-reading-dim`) on their own
	 * rows above and below, so they never perturb the pivot.
	 *
	 * What it does NOT do: it computes no pacing (pivot index and dwell are the engine's), binds
	 * no keys or `window` listeners (R-STAGE owns the single global listener), and never colours
	 * anything but the pivot. Sizing comes from the stage via `--reading-size` /
	 * `--reading-letter-spacing` custom properties, so this view inherits the user's preferences
	 * without reading them directly.
	 */
	import type { ModeProps } from '../types';
	import { pivotTranslateX } from './measure';

	// Renamed off the `state` prop: a local binding named `state` would make the `$state` rune
	// below ambiguous with a store auto-subscription (`store_rune_conflict`).
	let { state: reader }: ModeProps = $props();

	const token = $derived(reader.token);
	const text = $derived(token?.text ?? '');
	const pivot = $derived(reader.pivotIndex);
	const before = $derived(text.slice(0, pivot));
	const glyph = $derived(text.charAt(pivot));
	const after = $derived(text.slice(pivot + 1));
	const contextBefore = $derived(reader.contextBefore);
	const contextAfter = $derived(reader.contextAfter);

	let wordEl = $state<HTMLSpanElement | null>(null);
	let glyphEl = $state<HTMLSpanElement | null>(null);
	let translateX = $state(0);

	// DOM boundary: after each word renders, measure the pivot glyph and translate the word so the
	// glyph centre lands on the reticle column. Reading `text` + `pivot` registers them as deps so
	// the measure re-runs on every word change; `translateX` is written but not read, so no loop.
	$effect(() => {
		void text;
		void pivot;
		const word = wordEl;
		const mark = glyphEl;
		const wrap = word?.parentElement;
		if (!word || !mark || !wrap) return;
		translateX = pivotTranslateX(wrap.clientWidth, mark.offsetLeft, mark.offsetWidth);
	});
</script>

<div class="rsvp-stage font-reading text-reading-foreground">
	{#if token}
		{#if contextBefore.length > 0}
			<div class="ctx-row ctx-above text-reading-dim" aria-hidden="true">
				{contextBefore.map((t) => t.text).join(' ')}
			</div>
		{/if}

		<div class="reticle" aria-hidden="true">
			<span class="tick tick-top bg-muted-foreground/40"></span>
			<span class="tick tick-bottom bg-muted-foreground/40"></span>
		</div>

		<div class="word-wrap">
			<span class="word" bind:this={wordEl} style:transform="translate({translateX}px, -50%)">
				<span>{before}</span><span class="text-pivot" data-pivot bind:this={glyphEl}>{glyph}</span
				><span>{after}</span>
			</span>
		</div>

		{#if contextAfter.length > 0}
			<div class="ctx-row ctx-below text-reading-dim" aria-hidden="true">
				{contextAfter.map((t) => t.text).join(' ')}
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

	/* Context rows live on their own layer so they never shift the pivot. */
	.ctx-row {
		position: absolute;
		left: 0;
		right: 0;
		text-align: center;
		font-size: 0.42em;
		font-weight: 400;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		pointer-events: none;
	}

	.ctx-above {
		top: 50%;
		margin-top: -1.5em;
	}

	.ctx-below {
		top: 50%;
		margin-top: 1.5em;
	}
</style>
