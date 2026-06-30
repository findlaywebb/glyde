import { describe, expect, it } from 'vitest';
import { isIosInstallable } from './install-hint';

// Real UA strings (truncated): the detection must distinguish iOS Safari (the only place the
// Add-to-Home-Screen flow exists) from iOS Chrome and from a real desktop Mac.
const IPHONE_SAFARI =
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const IPHONE_CHROME =
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1';
// iPadOS 13+ Safari reports a desktop "Macintosh" UA — distinguished from a real Mac only by
// multi-touch (maxTouchPoints > 1).
const MAC_UA =
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';

describe('isIosInstallable', () => {
	it('shows on iOS Safari when not installed and not dismissed', () => {
		expect(isIosInstallable(IPHONE_SAFARI, 5, false, false)).toBe(true);
	});

	it('shows on iPadOS Safari (Macintosh UA + multi-touch)', () => {
		expect(isIosInstallable(MAC_UA, 5, false, false)).toBe(true);
	});

	it('hides once dismissed', () => {
		expect(isIosInstallable(IPHONE_SAFARI, 5, false, true)).toBe(false);
	});

	it('hides when already installed (standalone)', () => {
		expect(isIosInstallable(IPHONE_SAFARI, 5, true, false)).toBe(false);
	});

	it('hides in non-Safari iOS browsers (Chrome)', () => {
		expect(isIosInstallable(IPHONE_CHROME, 5, false, false)).toBe(false);
	});

	it('hides on a real Mac (Macintosh UA, no touch)', () => {
		expect(isIosInstallable(MAC_UA, 0, false, false)).toBe(false);
	});
});
