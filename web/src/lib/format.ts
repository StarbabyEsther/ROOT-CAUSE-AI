/** Currency + numeric formatting that never hides a sub-cent discrepancy. */

const isNumeric = (value: string) => value !== "" && Number.isFinite(Number(value));

export function money(value: string, options: { signed?: boolean; decimals?: number } = {}): string {
  const { signed = false, decimals = 2 } = options;
  if (!isNumeric(value)) return value;
  const amount = Number(value);
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(Math.abs(amount));
  if (amount < 0) return `−${formatted}`;
  return signed && amount > 0 ? `+${formatted}` : formatted;
}

/**
 * Exact decimal rendering. `4E-17` becomes `0.00000000000000004` so the UI can
 * show the drift digit-by-digit instead of rounding it away to `$0.00`.
 */
export function exactDecimal(value: string, maxFractionDigits = 24): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return value;
  if (!/e/i.test(value)) return value;
  const fixed = numeric.toFixed(maxFractionDigits).replace(/0+$/, "");
  return fixed.endsWith(".") ? fixed.slice(0, -1) : fixed;
}

/** Scientific split for display as mantissa × 10⁻ⁿ. */
export function scientific(value: string): { mantissa: string; exponent: number } | null {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric === 0) return null;
  const exponent = Math.floor(Math.log10(Math.abs(numeric)));
  const mantissa = numeric / Math.pow(10, exponent);
  return { mantissa: mantissa.toFixed(1).replace(/\.0$/, ""), exponent };
}

/** Renders a signed exponent as superscript digits, e.g. -17 → "⁻¹⁷". */
export const superscript = (n: number): string =>
  (n < 0 ? "⁻" : "") +
  String(Math.abs(n))
    .split("")
    .map((digit) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[Number(digit)] ?? digit)
    .join("");

/** "0.20000000000000004" → "0.20" with the divergent tail separated. */
export function splitDecimals(actual: string, expected: string) {
  const [whole, fraction = ""] = actual.split(".");
  const [, expectedFraction = ""] = expected.split(".");
  const stable = fraction.slice(0, Math.max(expectedFraction.length, 2));
  const drift = fraction.slice(stable.length);
  return { whole, stable, drift };
}

export function pad(value: number, length = 2): string {
  return String(value).padStart(length, "0");
}
