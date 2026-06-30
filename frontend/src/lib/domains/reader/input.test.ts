// Reader input classifiers — node `unit` project (pure functions, NO DOM). The `bindSwipe` DOM
// adapter is exercised by the jsdom `Reader.component.test.ts`; here we pin only the pure core:
// the key→intent map, the swipe classifier (tap / axis-lock / distance-or-velocity commit), and
// the wpm clamp R-STAGE owns.
import { describe, expect, it } from 'vitest';
import {
	classifySwipe,
	clampWpm,
	keyToIntent,
	MAX_WPM,
	MIN_WPM,
	type ReaderIntent,
	type SwipeAction
} from './input';

describe('keyToIntent', () => {
	it.each<[string, ReaderIntent | null]>([
		[' ', 'toggle'],
		['Spacebar', 'toggle'],
		['ArrowRight', 'stepForward'],
		['ArrowLeft', 'reshowLastBlock'],
		['ArrowUp', null],
		['ArrowDown', null],
		['a', null],
		['Enter', null],
		['Escape', null]
	])('maps %j to %j', (key, intent) => {
		expect(keyToIntent(key)).toBe(intent);
	});
});

describe('clampWpm', () => {
	it('passes an in-range value through (rounded)', () => {
		expect(clampWpm(300)).toBe(300);
		expect(clampWpm(317.6)).toBe(318);
	});

	it('clamps below the floor to MIN_WPM', () => {
		expect(clampWpm(10)).toBe(MIN_WPM);
		expect(clampWpm(-5)).toBe(MIN_WPM);
	});

	it('clamps above the ceiling to MAX_WPM', () => {
		expect(clampWpm(9999)).toBe(MAX_WPM);
	});

	it('falls NaN to MIN_WPM and saturates ±Infinity to the bounds', () => {
		expect(clampWpm(Number.NaN)).toBe(MIN_WPM);
		expect(clampWpm(Number.POSITIVE_INFINITY)).toBe(MAX_WPM);
		expect(clampWpm(Number.NEGATIVE_INFINITY)).toBe(MIN_WPM);
	});
});

describe('classifySwipe', () => {
	it('treats a near-stationary gesture as a tap', () => {
		expect(classifySwipe({ dx: 2, dy: -3, dt: 120 })).toBe('tap');
	});

	it('yields a vertical-dominant gesture to native scroll (null)', () => {
		expect(classifySwipe({ dx: 10, dy: 80, dt: 200 })).toBeNull();
	});

	it('commits a long leftward swipe to next', () => {
		expect(classifySwipe({ dx: -60, dy: 5, dt: 300 })).toBe('next');
	});

	it('commits a long rightward swipe to prev', () => {
		expect(classifySwipe({ dx: 60, dy: 5, dt: 300 })).toBe('prev');
	});

	it('commits a short-but-fast horizontal flick by velocity', () => {
		// 40px in 100ms = 0.4 px/ms (> 0.3 flick velocity) → committed despite < 45px distance.
		expect(classifySwipe({ dx: -42, dy: 4, dt: 100 })).toBe('next');
	});

	it('rejects a short, slow horizontal drag (neither distance nor velocity)', () => {
		// 20px in 400ms = 0.05 px/ms, and 20px < 45px distance → no commit.
		const result: SwipeAction = classifySwipe({ dx: -20, dy: 3, dt: 400 });
		expect(result).toBeNull();
	});

	it('treats an exactly-diagonal gesture (ax === ay) as vertical (null)', () => {
		expect(classifySwipe({ dx: 50, dy: 50, dt: 200 })).toBeNull();
	});
});
