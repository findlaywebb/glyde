<script lang="ts">
	// Single-thumb range slider (the §5.8 frozen primitive) for speed / size / spacing /
	// ctx_scale. Built on a native <input type="range"> — it brings keyboard support, the
	// `slider` role, and value semantics for free, so the zero-a11y gate is satisfied with an
	// `aria-label` alone. `value` is $bindable (two-way); `onValueChange` fires on COMMIT (the
	// native `change` event, i.e. pointer release), distinct from the live `bind:value` updates.
	import { cn } from '$lib/utils';

	interface Props {
		value: number;
		min: number;
		max: number;
		step?: number;
		onValueChange?: (value: number) => void;
		'aria-label': string;
		class?: string;
	}

	let {
		value = $bindable(),
		min,
		max,
		step = 1,
		onValueChange,
		'aria-label': ariaLabel,
		class: className
	}: Props = $props();
</script>

<input
	type="range"
	{min}
	{max}
	{step}
	aria-label={ariaLabel}
	bind:value
	onchange={(event) => onValueChange?.(event.currentTarget.valueAsNumber)}
	class={cn(
		'h-11 w-full cursor-pointer touch-none accent-pivot focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
		className
	)}
/>
