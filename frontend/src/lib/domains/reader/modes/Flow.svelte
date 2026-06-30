<script lang="ts">
	/**
	 * The Flow view — Guided sweep and Fading trail over the full word stream.
	 *
	 * Renders every prose word left-aligned and moves the reading position through them, driven by
	 * the engine's `wordIndex`. Two variants, chosen by `mode`:
	 *   - guided: all words sit at a calm base opacity, already-read words dim back, and the
	 *     current word is marked with a `text-pivot` underline (no bold — bold reflows the line).
	 *   - fading: already-read words fade fully out, leaving only the present and the road ahead.
	 *
	 * Motion discipline: the only animation is the compositor-only opacity transition on the fade
	 * trail, and it is gated on `prefers-reduced-motion` (read once at mount) — a reduced-motion
	 * reader gets the instant outcome with no travel or flashing. The view never teleprompter-
	 * scrolls: the text holds still and jumps discretely (an instant `translateY`, never animated)
	 * only when the current word drifts out of a comfortable band. Sizing comes from the stage via
	 * `--reading-size-flow`; this view reads no preferences and computes no pacing.
	 */
	import { untrack } from 'svelte';
	import type { ModeProps } from '../types';

	// Renamed off the `state` prop: a local binding named `state` would make the `$state` rune
	// below ambiguous with a store auto-subscription (`store_rune_conflict`).
	let { mode, state: reader, words }: ModeProps = $props();

	const wordIndex = $derived(reader.wordIndex);

	// Read once at mount — the motion gate. A reduced-motion reader never gets the fade transition.
	const reducedMotion =
		typeof window !== 'undefined' &&
		typeof window.matchMedia === 'function' &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	let viewport = $state<HTMLElement | null>(null);
	let spans = $state<(HTMLElement | null)[]>([]);
	let offsetY = $state(0);

	// Discrete band-jump: when the current word leaves the comfortable reading band, jump the text
	// so it sits ~40% down — instantly, never an animated scroll. Tracks only `wordIndex`; the read
	// of `offsetY` is untracked so writing it cannot loop the effect.
	$effect(() => {
		const wi = wordIndex;
		const vp = viewport;
		if (!vp) return;
		untrack(() => {
			const el = spans[wi];
			if (!el) return;
			const h = vp.clientHeight;
			if (h <= 0) return;
			const top = el.offsetTop - offsetY;
			if (top > h * 0.72 || top < h * 0.18) {
				offsetY = Math.max(0, el.offsetTop - h * 0.4);
			}
		});
	});
</script>

<div
	class="flow font-reading text-reading-foreground"
	class:reduced={reducedMotion}
	data-mode={mode}
	bind:this={viewport}
>
	<div class="flow-content" style:transform="translate(-50%, {-offsetY}px)">
		{#each words as word, i (i)}<span
				class="fw"
				class:read={i < wordIndex}
				class:cur={i === wordIndex}
				class:underline={i === wordIndex}
				class:decoration-pivot={i === wordIndex}
				class:decoration-2={i === wordIndex}
				class:underline-offset-4={i === wordIndex}
				data-flow-state={i < wordIndex ? 'read' : i === wordIndex ? 'cur' : 'ahead'}
				bind:this={spans[i]}>{word.text}</span
			><span class="sp" aria-hidden="true"> </span>{/each}
	</div>
</div>

<style>
	.flow {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	.flow-content {
		position: absolute;
		left: 50%;
		top: 0;
		width: min(62ch, 92%);
		text-align: left;
		line-height: 2.1;
		font-size: var(--reading-size-flow, clamp(1.25rem, 4.5vw, 1.9rem));
	}

	/* The single animation: compositor-only opacity, gated off for reduced-motion readers. */
	.flow:not(.reduced) .fw {
		transition:
			opacity 0.35s ease,
			color 0.2s ease;
	}

	/* Guided sweep: calm base, read words recede, current word at full presence. */
	.flow[data-mode='guided'] .fw {
		opacity: 0.8;
	}

	.flow[data-mode='guided'] .fw.read {
		opacity: 0.25;
	}

	.flow[data-mode='guided'] .fw.cur {
		opacity: 1;
	}

	/* Fading trail: read words fade fully out. */
	.flow[data-mode='fading'] .fw {
		opacity: 1;
	}

	.flow[data-mode='fading'] .fw.read {
		opacity: 0;
	}
</style>
