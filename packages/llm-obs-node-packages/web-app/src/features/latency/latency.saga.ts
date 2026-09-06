import { call, put, takeEvery } from "redux-saga/effects";
import { latencyActions } from "./latency.slice";
import { latencyClientService } from "./service/latency-client.service";
import { eventBus } from "../../core/event-bus/event-bus";
import { LATENCY_CONFIG_DEFAULTS, LATENCY_EVENTS } from "./constants";
import type { PercentilesResult, SLOResult, AttributionResult, BaselinePoint } from "./types";

function* handleFetchLatency(action: ReturnType<typeof latencyActions.fetchLatencySubmitted>): Generator<any, void, any> {
  const {
    model,
    hourOfDay,
    days = LATENCY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS,
    endpoint = LATENCY_CONFIG_DEFAULTS.DEFAULT_SLO_ENDPOINT,
    hour = new Date().toISOString().substring(0, 10),
  } = action.payload;

  try {
    const percentiles: PercentilesResult = yield call(() => latencyClientService.getPercentiles(model, hourOfDay));
    const slo: SLOResult = yield call(() => latencyClientService.getSLO(model, endpoint));
    const attribution: AttributionResult = yield call(() => latencyClientService.getAttribution(model, hour));
    const baseline: BaselinePoint[] = yield call(() => latencyClientService.getBaseline(model, hourOfDay, days));

    yield put(
      latencyActions.latencySuccess({
        percentiles,
        slo,
        attribution,
        baseline: Array.isArray(baseline) ? baseline : [],
      })
    );

    eventBus.emit(LATENCY_EVENTS.FETCHED, { model, hourOfDay });
  } catch (err: any) {
    const errorMsg = err?.message || LATENCY_CONFIG_DEFAULTS.ERROR_FETCH_FAILED;
    yield put(latencyActions.latencyFailed(errorMsg));
    eventBus.emit(LATENCY_EVENTS.FAILED, errorMsg);
  }
}

export function* latencySaga() {
  yield takeEvery(latencyActions.fetchLatencySubmitted.type, handleFetchLatency);
}

