/**
 * Centralized currency and number formatting utilities for FinPilot AI.
 * Uses Indian Rupee (INR - ₹) with standard Indian number system (en-IN).
 */

export interface FormatINROptions {
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  compact?: boolean;
}

/**
 * Format a number or numeric string as INR (₹).
 * Examples:
 *   formatINR(100000) -> "₹1,00,000"
 *   formatINR(2500.5, { minimumFractionDigits: 2 }) -> "₹2,500.50"
 *   formatINR(null) -> "₹0"
 */
export function formatINR(
  value: number | string | null | undefined,
  options: FormatINROptions = {}
): string {
  if (value === null || value === undefined || value === '') {
    return '₹0';
  }

  const num = typeof value === 'number' ? value : Number(value);
  if (isNaN(num)) {
    return '₹0';
  }

  const {
    minimumFractionDigits = 0,
    maximumFractionDigits = 2,
    compact = false,
  } = options;

  if (compact && Math.abs(num) >= 10000000) {
    // Crores
    const cr = num / 10000000;
    return `₹${cr.toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
  } else if (compact && Math.abs(num) >= 100000) {
    // Lakhs
    const lk = num / 100000;
    return `₹${lk.toLocaleString('en-IN', { maximumFractionDigits: 2 })} L`;
  }

  const formatted = num.toLocaleString('en-IN', {
    minimumFractionDigits,
    maximumFractionDigits,
  });

  return `₹${formatted}`;
}

/**
 * Format a number as compact INR.
 * Example: formatINRCompact(150000) -> "₹1.5 L"
 */
export function formatINRCompact(value: number | string | null | undefined): string {
  return formatINR(value, { compact: true });
}

/**
 * Format a percentage value.
 * Example: formatPercent(12.5) -> "12.5%"
 */
export function formatPercent(
  value: number | string | null | undefined,
  decimals: number = 1
): string {
  if (value === null || value === undefined || value === '') {
    return '0%';
  }
  const num = typeof value === 'number' ? value : Number(value);
  if (isNaN(num)) {
    return '0%';
  }
  return `${num.toFixed(decimals)}%`;
}
