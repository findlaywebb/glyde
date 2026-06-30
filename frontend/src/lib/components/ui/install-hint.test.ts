import { describe, expect, it } from 'vitest';
import { isIosInstallable } from './install-hint';

// Real UA strings (truncated): the detection must distinguish iOS Safari (the only place the
// Add-to-Home-Screen flow exists) from iOS Chrome and from desktop Safari.
const IPHONE_SAFARI =
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const IPHONE_CHROME =
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1';
const MAC_SAFARI =
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';

describe('isIosInstallable', () => {
	it('shows on iOS Safari when not installed and not dismissed', () => {
		expect(isIosInstallable(IPHONE_SAFARI, false, false)).toBe(true);
	});

	it('hides once dismissed', () => {
		expect(isIosInstallable(IPHONE_SAFARI, false, true)).toBe(false);
	});

	it('hides when already installed (standalone)', () => {
		expect(isIosInstallable(IPHONE_SAFARI, true, false)).toBe(false);
	});

	it('hides in non-Safari iOS browsers (Chrome)', () => {
		expect(isIosInstallable(IPHONE_CHROME, false, false)).toBe(false);
	});

	it('hides on non-iOS platforms (desktop Safari)', () => {
		expect(isIosInstallable(MAC_SAFARI, false, false)).toBe(false);
	});
});
