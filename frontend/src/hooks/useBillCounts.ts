import { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { BILLS_CHANGED_EVENT, billApi } from '../services/api';

/** Same window the 未處理的帳單 page starts with, so the badge matches its default list. */
const UPCOMING_DAYS = 45;

export interface BillCounts {
  draft: number;
  processing: number;
}

/** Sidebar badge counts; refetched on navigation, window focus and after bill/contract updates. */
export function useBillCounts(): BillCounts {
  const location = useLocation();
  const [counts, setCounts] = useState<BillCounts>({ draft: 0, processing: 0 });

  const refresh = useCallback(async () => {
    try {
      const [draft, processing] = await Promise.all([
        billApi.getAll({ status: ['DRAFT'], within_days: UPCOMING_DAYS }),
        billApi.getAll({ status: ['SENT', 'PROCESSING'] }),
      ]);
      setCounts({ draft: draft.length, processing: processing.length });
    } catch (e) {
      console.error('Failed to fetch bill counts:', e);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, location.pathname]);

  useEffect(() => {
    window.addEventListener(BILLS_CHANGED_EVENT, refresh);
    window.addEventListener('focus', refresh);
    return () => {
      window.removeEventListener(BILLS_CHANGED_EVENT, refresh);
      window.removeEventListener('focus', refresh);
    };
  }, [refresh]);

  return counts;
}
