<script lang="ts">
	import '../app.css';
	import { browser, dev } from '$app/environment';
	import InstallHint from '$lib/components/ui/InstallHint.svelte';

	let { children } = $props();

	// Guarded service-worker registration (the X1 half of the §5.11 PWA split). The worker
	// payload (/sw.js) is LAN-owned and referenced by RUNTIME URL only — never imported — so
	// if LAN is cut the registration `.catch()`es the 404 and the shell stays green. Skipped
	// in dev (HMR + a cache worker fight) and during SSR. A service worker needs a secure
	// context (HTTPS or localhost), so over plain-HTTP LAN it simply never registers.
	$effect(() => {
		if (browser && !dev && 'serviceWorker' in navigator) {
			navigator.serviceWorker.register('/sw.js').catch(() => {
				// /sw.js is absent when LAN is cut, or the context is insecure — both fine.
			});
		}
	});
</script>

<svelte:head>
	<!-- Installable-PWA hooks, referenced by runtime URL (LAN serves the payload; 404 is
		harmless when LAN is cut). theme-color matches the dark-first background. -->
	<link rel="manifest" href="/manifest.json" />
	<meta name="theme-color" content="#11151c" />
	<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
</svelte:head>

<!-- Single page landmark for the whole app; `overflow-x-clip` stops a stray wide child
	(a code card, a long slug) from forcing horizontal scroll on a phone (§5.11). -->
<main class="min-h-dvh overflow-x-clip">
	{@render children()}
</main>

<InstallHint />
