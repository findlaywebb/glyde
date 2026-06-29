import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge class lists, resolving Tailwind conflicts (the shadcn-svelte `cn` helper). */
export function cn(...inputs: ClassValue[]): string {
	return twMerge(clsx(inputs));
}
