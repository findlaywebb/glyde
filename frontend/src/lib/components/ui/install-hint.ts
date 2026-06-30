// Detection logic for the iOS "Add to Home Screen" hint, kept as a pure function so it is
// node-testable without a DOM (the component just feeds it the live navigator + localStorage).
// iOS Safari has no `beforeinstallprompt`, so a manual, dismissible hint is the only install
// affordance there — and it must NOT show on non-iOS, in non-Safari iOS browsers, once the app
// is already installed (standalone), or after the user dismisses it.

/** localStorage key recording that the user dismissed the install hint. */
export const INSTALL_HINT_DISMISSED_KEY = 'glyde:install-hint-dismissed';

/** Return whether the dismissible iOS install hint should be shown. */
export function isIosInstallable(
	userAgent: string,
	isStandalone: boolean,
	dismissed: boolean
): boolean {
	if (dismissed || isStandalone) return false;
	const isIos = /iphone|ipad|ipod/i.test(userAgent);
	// Add-to-Home-Screen lives in Safari's share sheet; other iOS browsers (Chrome=CriOS,
	// Firefox=FxiOS, Edge=EdgiOS) have a different or absent flow, so only hint in Safari.
	const isSafari = /safari/i.test(userAgent) && !/crios|fxios|edgios/i.test(userAgent);
	return isIos && isSafari;
}
