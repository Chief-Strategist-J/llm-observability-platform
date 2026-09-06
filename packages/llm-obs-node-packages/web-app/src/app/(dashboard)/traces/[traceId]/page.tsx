'use client';

import React, { useEffect, use } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { TraceDetailWaterfallUI } from '../../../../features/traces/ui/TraceDetailWaterfallUI';
import { tracesActions } from '../../../../features/traces/traces.slice';
import type { RootState } from '../../../../core/store/configure-store';

export default function TraceDetailPage({ params }: { params: Promise<{ traceId: string }> }) {
  const resolvedParams = use(params);
  const dispatch = useDispatch();
  const tracesState = useSelector((state: RootState) => state.traces);

  useEffect(() => {
    if (resolvedParams.traceId) {
      dispatch(tracesActions.fetchTraceDetailSubmitted({ traceId: resolvedParams.traceId }));
    }
  }, [dispatch, resolvedParams.traceId]);

  return (
    <TraceDetailWaterfallUI
      trace={tracesState?.activeTrace || null}
      loading={tracesState?.detailStatus === "loading"}
      error={tracesState?.detailError || null}
    />
  );
}

