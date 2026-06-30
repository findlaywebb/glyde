<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';
	import { cn } from '$lib/utils';

	// shadcn-svelte components are *owned source* — review them as our code. Components speak
	// semantic tokens (bg-primary, text-primary-foreground), never the raw palette, so they
	// flip correctly under `.dark`.
	type Variant = 'primary' | 'secondary' | 'destructive' | 'ghost';

	type Props = HTMLButtonAttributes & {
		variant?: Variant;
		children: Snippet;
	};

	let { variant = 'primary', class: className, children, ...rest }: Props = $props();

	const variants: Record<Variant, string> = {
		primary: 'bg-primary text-primary-foreground hover:opacity-90',
		secondary: 'bg-secondary text-secondary-foreground hover:opacity-90',
		destructive: 'bg-destructive text-white hover:opacity-90',
		ghost: 'hover:bg-accent hover:text-accent-foreground'
	};
</script>

<button
	class={cn(
		'inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 py-2 font-ui text-sm font-medium transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50',
		variants[variant],
		className
	)}
	{...rest}
>
	{@render children()}
</button>
