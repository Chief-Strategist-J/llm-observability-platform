import { call, put, takeEvery } from "redux-saga/effects";
import { tracesActions } from "./traces.slice";
import { tracesClientService } from "./service/traces-client.service";
import { eventBus } from "@observability/shared-infra";
import { TRACES_CONFIG_DEFAULTS, TRACES_EVENTS } from "./constants";
import type { TraceSummary, TraceDetailResult } from "./types";

function* handleFetchTraces(action: ReturnType<typeof tracesActions.fetchTracesSubmitted>): Generator<any, void, any> {
  const payload = (action.payload || {}) as Record<string, any>;
  const { model, status, service, limit = TRACES_CONFIG_DEFAULTS.DEFAULT_PAGE_SIZE } = payload;


  try {
    const items: TraceSummary[] = yield call(() => tracesClientService.listTraces(model, status, service, limit));
    yield put(tracesActions.tracesSuccess(Array.isArray(items) ? items : []));
    eventBus.emit(TRACES_EVENTS.FETCHED, { count: items.length });
  } catch (err: any) {
    const errorMsg = err?.message || TRACES_CONFIG_DEFAULTS.ERROR_FETCH_TRACES;
    yield put(tracesActions.tracesFailed(errorMsg));
    eventBus.emit(TRACES_EVENTS.FAILED, errorMsg);
  }
}

function* handleFetchTraceDetail(action: ReturnType<typeof tracesActions.fetchTraceDetailSubmitted>): Generator<any, void, any> {
  const { traceId } = action.payload;

  try {
    const detail: TraceDetailResult = yield call(() => tracesClientService.getTraceDetail(traceId));
    yield put(tracesActions.traceDetailSuccess(detail));
    eventBus.emit(TRACES_EVENTS.DETAIL_FETCHED, { traceId });
  } catch (err: any) {
    const errorMsg = err?.message || `${TRACES_CONFIG_DEFAULTS.ERROR_FETCH_DETAIL} for ${traceId}`;
    yield put(tracesActions.traceDetailFailed(errorMsg));
    eventBus.emit(TRACES_EVENTS.DETAIL_FAILED, { traceId, error: errorMsg });
  }
}

export function* tracesSaga() {
  yield takeEvery(tracesActions.fetchTracesSubmitted.type, handleFetchTraces);
  yield takeEvery(tracesActions.fetchTraceDetailSubmitted.type, handleFetchTraceDetail);
}

