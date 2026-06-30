<!--
  Progress (R-CHROME).

  Hairline scrubber bar with block notches and prominent time-remaining. The range input is the
  sole interactive element (aria-label + keyboard navigation); the visual track and notches are
  decorative (aria-hidden). Time is rendered in tabular-nums. No global event listeners.

  The thumb shows `wordIndex` (the engine's live position) EXCEPT during an active drag, when the
  user owns it: `dragValue` holds the in-flight position so an engine word-advance mid-drag does
  not snap the thumb back. `dragValue` is genuine UI state; `displayValue` is a pure `$derived`.
  When `wordCount` is 0 (empty digest) the scrubber is disabled, so no out-of-range `onScrub`
  fires.
-->
<script lang="ts">
	import type { ProgressProps } from './types';

	let { wordIndex, wordCount, remainingMs, blockNotches, onScrub }: ProgressProps = $props();

	// The user's in-flight drag position, or null when the engine owns the thumb. While non-null,
	// `displayValue` ignores `wordIndex`, so the thumb does not flicker as the engine advances.
	let dragValue = $state<number | null>(null);

	/** Thumb position: the live drag value while dragging, else the engine's `wordIndex`. */
	const displayValue = $derived(dragValue ?? wordIndex);

	/** The highest valid 0-based scrub target (0 when the digest has no words). */
	const maxIndex = $derived(Math.max(wordCount - 1, 0));

	/** Filled percentage of the scrubber bar (0–100). */
	const pct = $derived(wordCount > 0 ? (wordIndex / wordCount) * 100 : 0);

	/** Human-readable time remaining: "~2m 14s left", "~45s left", "~0s left". */
	const timeLeft = $derived(formatTime(remainingMs));

	/**
	 * Format milliseconds as a short, human-readable remaining-time string.
	 *
	 * Returns "~Xm Ys left" when minutes are present, "~Ys left" when under a minute,
	 * and "~0s left" for zero or negative durations.
	 */
	function formatTime(ms: number): string {
		if (ms <= 0) return '~0s left';
		const totalSeconds = Math.ceil(ms / 1000);
		const m = Math.floor(totalSeconds / 60);
		const s = totalSeconds % 60;
		if (m > 0) return `~${m}m ${s}s left`;
		return `~${s}s left`;
	}
</script>

<div class="w-full font-ui">
	<!-- Time remaining — polite live region so screen readers announce updates. -->
	<div class="mb-1 flex items-baseline justify-between">
		<span class="text-xs tabular-nums text-muted-foreground" aria-live="polite">{timeLeft}</span>
		<span class="text-xs tabular-nums text-muted-foreground/60">{wordIndex} / {wordCount}</span>
	</div>

	<!--
    Scrubber container: min-h-11 so the touch target meets the ≥44px floor while the visible
    track stays a hairline. The visual layer is pointer-events-none; the transparent range input
    sits on top and handles all interaction.
  -->
	<div class="relative flex min-h-11 items-center">
		<!-- Visual track and notches (decorative; interaction via the range input below) -->
		<div
			class="pointer-events-none absolute inset-x-0 h-1 overflow-visible rounded-full bg-border"
			aria-hidden="true"
		>
			<!-- Fill -->
			<div class="h-full rounded-full bg-primary" style="width: {pct}%"></div>

			<!-- Block notches: one tick per upcoming block position. -->
			{#each blockNotches as notch (notch)}
				<div
					class="absolute top-0 h-full w-0.5 -translate-x-1/2 bg-cue"
					style="left: {wordCount > 0 ? (notch / wordCount) * 100 : 0}%"
					data-testid="notch"
					aria-hidden="true"
				></div>
			{/each}
		</div>

		<!-- Transparent range input: provides role=slider, aria-label, keyboard navigation. -->
		<input
			type="range"
			min={0}
			max={maxIndex}
			value={displayValue}
			step={1}
			disabled={wordCount === 0}
			aria-label="Reading position"
			class="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-default"
			oninput={(e) => (dragValue = e.currentTarget.valueAsNumber)}
			onchange={(e) => {
				onScrub(e.currentTarget.valueAsNumber);
				dragValue = null;
			}}
			onpointercancel={() => (dragValue = null)}
		/>
	</div>
</div>
