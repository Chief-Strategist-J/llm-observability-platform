import { call, put, takeEvery } from "redux-saga/effects";
import { tracesActions } from "./traces.slice";
import { tracesClientService } from "./service/traces-client.service";
import { eventBus } from "@observability/shared-infra";
import type { TraceSummary } from "./types";

function* handleFetchTraces(action: ReturnType<typeof tracesActions.fetchTracesSubmitted>): Generator<any, void, any> {
  const { model, status, service, limit = 20 } = action.payload || {};

  try {
    const items: TraceSummary[] = yield call([tracesClientService, "listTraces"], model, status, service, limit);
    yield put(tracesActions.tracesSuccess(Array.isArray(items) ? items : []));
    eventBus.emit("traces.fetched", { count: items.length });
  } catch (err: any) {
    const errorMsg = err?.message || "Failed to fetch distributed traces";
    yield put(tracesActions.tracesFailed(errorMsg));
    eventBus.emit("traces.failed", errorMsg);
  }
}

export function* tracesSaga() {
  yield takeEvery(tracesActions.fetchTracesSubmitted.type, handleFetchTraces);
}
