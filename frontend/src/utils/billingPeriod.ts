// Contract/bill dates arrive as naive timestamps (e.g. "2026-11-19T00:00:00", no timezone).
// `new Date()` reads them as local time, which is also how the UI displays them, so all
// calendar math here uses local getters. Mixing in getUTC*/toISOString shifts the day.

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

/** 解析日期；純日期 YYYY-MM-DD 視為本地午夜（`new Date('2026-11-19')` 會被當成 UTC）。 */
function parseLocal(value: string | null | undefined): Date | null {
  if (!value) return null;
  const d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function toYmd(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** 日期輸入框用的 YYYY-MM-DD（與畫面顯示的日期一致）。 */
export function toLocalYmd(iso: string | null | undefined): string {
  const d = parseLocal(iso);
  return d ? toYmd(d) : '';
}

/** 起始日 + 月數，回傳 YYYY-MM-DD；若日超過當月最後一天則取該月最後一天。 */
export function addMonthsToDate(iso: string | null | undefined, months: number): string {
  const d = parseLocal(iso);
  if (!d || !Number.isInteger(months) || months < 0) return '';
  const total = d.getMonth() + months;
  const y = d.getFullYear() + Math.floor(total / 12);
  const m = total % 12;
  const lastDay = new Date(y, m + 1, 0).getDate();
  return toYmd(new Date(y, m, Math.min(d.getDate(), lastDay)));
}

/**
 * 帳單結束日期 = (帳單起始日 + 帳單週期月數) - 1 日，且不超過合約結束日（最後一期可能較短）。
 * 例：起始 2026-11-19、週期 12 個月 → 2027-11-18。回傳 YYYY-MM-DD。
 */
export function getBillEndDate(
  startIso: string | null | undefined,
  intervalMonths: number,
  contractEndIso?: string | null
): string {
  const nextStart = addMonthsToDate(startIso, intervalMonths);
  if (!nextStart) return '';
  const [y, m, day] = nextStart.split('-').map(Number);
  const end = toYmd(new Date(y, m - 1, day - 1));
  const contractEnd = toLocalYmd(contractEndIso);
  return contractEnd && contractEnd < end ? contractEnd : end;
}

/** 合約涵蓋的整月數；結束日為最後一天（含）。例：2026-11-19 ~ 2029-11-18 = 36。與後端 `_contract_months` 相同。 */
export function contractMonths(
  startIso: string | null | undefined,
  endIso: string | null | undefined
): number {
  const end = parseLocal(endIso);
  if (!end || !parseLocal(startIso)) return 0;
  const limit = toYmd(new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1));
  let n = 0;
  while (n < 1200 && addMonthsToDate(startIso, n + 1) <= limit) n += 1;
  return n;
}

/** 合約月數無法被帳單週期整除時回傳提示訊息；可建立則回傳 null。 */
export function getIntervalMismatchMessage(
  startIso: string | null | undefined,
  endIso: string | null | undefined,
  intervalMonths: number
): string | null {
  const months = contractMonths(startIso, endIso);
  if (!months || !Number.isInteger(intervalMonths) || intervalMonths < 1) return null;
  if (months % intervalMonths === 0) return null;
  return `合約期間共 ${months} 個月，無法被帳單週期 ${intervalMonths} 個月整除，因此無法建立。請調整合約的開始／結束日期，或改選可整除的帳單週期。`;
}
