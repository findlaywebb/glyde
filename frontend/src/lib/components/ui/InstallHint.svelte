<script lang="ts">
	// Dismissible iOS "Add to Home Screen" hint (the §5.8 shell primitive, mounted once in
	// +layout.svelte). Shown only on iOS Safari, not already-installed, not previously
	// dismissed (see `isIosInstallable`); the dismissal persists in localStorage. On every
	// other platform it renders nothing.
	import { browser } from '$app/environment';
	import { X } from '@lucide/svelte';
	import Icon from './Icon.svelte';
	import { INSTALL_HINT_DISMISSED_KEY, isIosInstallable } from './install-hint';

	let visible = $state(false);

	$effect(() => {
		if (!browser) return;
		const dismissed = localStorage.getItem(INSTALL_HINT_DISMISSED_KEY) === '1';
		const nav = navigator as Navigator & { standalone?: boolean };
		const standalone =
			nav.standalone === true || window.matchMedia('(display-mode: standalone)').matches;
		visible = isIosInstallable(navigator.userAgent, standalone, dismissed);
	});

	function dismiss() {
		visible = false;
		try {
			localStorage.setItem(INSTALL_HINT_DISMISSED_KEY, '1');
		} catch {
			// localStorage can throw in private mode — a non-persisted dismiss is fine.
		}
	}
</script>

{#if visible}
	<div
		class="fixed inset-x-3 bottom-3 z-30 flex items-center gap-3 rounded-xl border border-border bg-card p-3 text-card-foreground shadow-2xl"
	>
		<p class="flex-1 font-ui text-sm">
			Install Glyde: tap <span class="font-semibold">Share</span>, then
			<span class="font-semibold">Add to Home Screen</span>.
		</p>
		<button
			type="button"
			onclick={dismiss}
			aria-label="Dismiss install hint"
			class="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-muted-foreground transition hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
		>
			<Icon icon={X} />
		</button>
	</div>
{/if}
