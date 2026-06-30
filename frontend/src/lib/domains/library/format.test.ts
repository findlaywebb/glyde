import { describe, expect, it } from 'vitest';
import { formatBlockMix, formatProvenance, formatReadingTime } from './format';

describe('formatReadingTime', () => {
	it('returns seconds when under a minute', () => {
		// Sub-minute estimate renders as "~Xs".
		expect(formatReadingTime(45_000)).toBe('~45s');
	});

	it('returns whole minutes when no seconds remain', () => {
		// Exact minute boundary: no trailing "0s".
		expect(formatReadingTime(120_000)).toBe('~2m');
	});

	it('returns minutes and seconds for a mixed value', () => {
		// Both parts are present for a non-round estimate.
		expect(formatReadingTime(90_000)).toBe('~1m 30s');
	});

	it('rounds to the nearest second', () => {
		// 1500 ms rounds up to 2 s.
		expect(formatReadingTime(1_500)).toBe('~2s');
	});

	it('handles zero', () => {
		// Zero ms yields "~0s" (not an error or blank).
		expect(formatReadingTime(0)).toBe('~0s');
	});
});

describe('formatBlockMix', () => {
	it('returns empty string for no blocks', () => {
		// Empty map → empty string (badge is hidden by the caller).
		expect(formatBlockMix({})).toBe('');
	});

	it('formats a single block kind', () => {
		// One kind renders without any separator.
		expect(formatBlockMix({ code: 3 })).toBe('3 code');
	});

	it('joins multiple kinds with a middle dot separator', () => {
		// Multiple kinds are joined by " · ".
		expect(formatBlockMix({ code: 3, table: 1 })).toBe('3 code · 1 table');
	});

	it('omits kinds with a count of zero', () => {
		// Zero-count entries are filtered; only non-zero kinds appear.
		expect(formatBlockMix({ code: 2, table: 0 })).toBe('2 code');
	});

	it('returns empty string when all counts are zero', () => {
		// All-zero map is equivalent to an empty map.
		expect(formatBlockMix({ code: 0, table: 0 })).toBe('');
	});
});

describe('formatProvenance', () => {
	it('produces "sourceKind · date" when there is no producer', () => {
		// Two-part string: source kind and formatted date, no producer segment.
		expect(formatProvenance('cli', null, '2024-01-15T10:00:00Z')).toBe('cli · 15 Jan 2024');
	});

	it('produces "sourceKind · producer · date" when a producer is present', () => {
		// Three-part string: all segments present.
		expect(formatProvenance('agent', 'claude-3', '2024-01-15T10:00:00Z')).toBe(
			'agent · claude-3 · 15 Jan 2024'
		);
	});

	it('returns a fallback em-dash date for an invalid timestamp', () => {
		// An unparseable createdAt renders as "—" rather than "Invalid Date".
		expect(formatProvenance('cli', null, 'not-a-date')).toBe('cli · —');
	});
});
