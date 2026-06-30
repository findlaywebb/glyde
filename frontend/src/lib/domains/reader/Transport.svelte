<!--
  Transport (R-CHROME).

  Stateless bottom-bar chrome for the reader: replay-word, play-pause, step-forward, and an
  edge speed rail. Every action is delegated to the engine through the frozen TransportProps
  callbacks — no engine logic lives here, no global event listeners are registered (that is
  R-STAGE's job). All interactive controls are real <button> or <input> elements with ≥44px
  touch targets and :focus-visible rings.

  The speed rail mirrors `wpm` into a reassignable `$derived` (`railWpm`) clamped to the rail's
  supported range, so the thumb and the numeric label always agree and both track the live drag
  (the Slider commits via `onValueChange` only on pointer release, but its internal `bind:value`
  updates `railWpm` continuously). An out-of-range `wpm` is clamped for display here; clamping it
  to the supported range before it reaches Transport is R-STAGE's responsibility.
-->
<script lang="ts">
	import { Pause, Play, RotateCcw, SkipForward } from '@lucide/svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import Slider from '$lib/components/ui/Slider.svelte';
	import type { TransportProps } from './types';

	/** The supported speed-rail range (wpm). Out-of-range input is clamped for display. */
	const MIN_WPM = 100;
	const MAX_WPM = 800;

	let { isPlaying, wpm, onToggle, onReplayWord, onStepForward, onSpeed }: TransportProps = $props();

	// Reassignable $derived: follows the `wpm` prop (clamped to the rail) and is overridden by the
	// Slider's `bind:value` during a drag, so the label tracks the thumb live. On commit the prop
	// updates and the derived recomputes to the same clamped value — no $effect needed.
	let railWpm = $derived(Math.min(Math.max(wpm, MIN_WPM), MAX_WPM));
</script>

<!--
  Fixed bottom bar: speed rail above the control row. The Slider is already h-11 (44px) from the
  X1 primitive. The three control buttons carry min-h-11 min-w-11 so every touch target meets the
  ≥44px floor (assay-adoption.md §3).
-->
<div class="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-card font-ui">
	<!-- Speed rail -->
	<div class="flex items-center gap-3 px-4 pt-2">
		<span class="w-20 shrink-0 text-right text-xs tabular-nums text-muted-foreground"
			>{railWpm} wpm</span
		>
		<Slider
			bind:value={railWpm}
			min={MIN_WPM}
			max={MAX_WPM}
			step={10}
			onValueChange={onSpeed}
			aria-label="Reading speed in words per minute"
			class="flex-1"
		/>
	</div>

	<!-- Control row -->
	<div class="flex items-center justify-center gap-4 px-4 py-2">
		<button
			class="flex min-h-11 min-w-11 items-center justify-center rounded-md transition hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onclick={onReplayWord}
			aria-label="Replay previous word"
		>
			<Icon icon={RotateCcw} size={20} class="text-foreground" />
		</button>

		<button
			class="flex min-h-11 min-w-11 items-center justify-center rounded-full bg-primary text-primary-foreground transition hover:opacity-90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onclick={onToggle}
			aria-label={isPlaying ? 'Pause' : 'Play'}
		>
			<Icon icon={isPlaying ? Pause : Play} size={24} class="text-primary-foreground" />
		</button>

		<button
			class="flex min-h-11 min-w-11 items-center justify-center rounded-md transition hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onclick={onStepForward}
			aria-label="Step forward one word"
		>
			<Icon icon={SkipForward} size={20} class="text-foreground" />
		</button>
	</div>
</div>
