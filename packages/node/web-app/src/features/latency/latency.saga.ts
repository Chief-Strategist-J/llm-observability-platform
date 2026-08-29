import { call, put, takeEvery } from "redux-saga/effects";
import { latencyActions } from "./latency.slice";
import { latencyClientService } from "./service/latency-client.service";
import { eventBus } from "@/core/event-bus/event-bus";
import type { PercentilesResult, SLOResult, AttributionResult, BaselinePoint } from "./types";

function* handleFetchLatency(action: ReturnType<typeof latencyActions.fetchLatencySubmitted>): Generator<any, void, any> {
  const { model, hourOfDay, days = 7, endpoint = "/v1/chat/completions", hour = new Date().toISOString().substring(0, 10) } = action.payload;

  try {
    const percentiles: PercentilesResult = yield call([latencyClientService, "getPercentiles"], model, hourOfDay);
    const slo: SLOResult = yield call([latencyClientService, "getSLO"], model, endpoint);
    const attribution: AttributionResult = yield call([latencyClientService, "getAttribution"], model, hour);
    const baseline: BaselinePoint[] = yield call([latencyClientService, "getBaseline"], model, hourOfDay, days);

    yield put(
      latencyActions.latencySuccess({
        percentiles,
        slo,
        attribution,
        baseline: Array.isArray(baseline) ? baseline : [],
      })
    );

    eventBus.emit("latency.fetched", { model, hourOfDay });
  } catch (err: any) {
    const errorMsg = err?.message || "Failed to fetch latency metrics";
    yield put(latencyActions.latencyFailed(errorMsg));
    eventBus.emit("latency.failed", errorMsg);
  }
}

export function* latencySaga() {
  yield takeEvery(latencyActions.fetchLatencySubmitted.type, handleFetchLatency);
}
