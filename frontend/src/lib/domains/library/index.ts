/**
 * Library domain public surface.
 *
 * The digest library home: the card component, its primitive prop type, and the formatting
 * utilities used to build those props from the wire shape. Consumers that need the card import
 * it directly from its `.svelte` file; this barrel re-exports the non-Svelte surface so
 * unit tests and other domain files can import without a `.svelte` path.
 */
export type { DigestCardProps } from './types';
export { formatBlockMix, formatProvenance, formatReadingTime } from './format';
