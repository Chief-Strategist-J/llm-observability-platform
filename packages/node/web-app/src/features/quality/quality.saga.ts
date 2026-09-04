import { all, call, put, takeEvery } from "redux-saga/effects";
import { qualityActions } from "./quality.slice";
import { qualityClientService } from "./service/quality-client.service";
import { eventBus } from "../../core/event-bus/event-bus";
import { QUALITY_CONFIG_DEFAULTS, QUALITY_EVENTS } from "./constants";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "./types";

function* handleFetchQuality(action: ReturnType<typeof qualityActions.fetchQualitySubmitted>): Generator<any, void, any> {
  const payload = (action.payload || {}) as Record<string, any>;
  const model = payload.model ?? QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL;
  const timeRange = payload.timeRange ?? QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE;
  const days = payload.days ?? QUALITY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS;
  const service = payload.service;



  try {
    const [summary, trend, models, flaggedAlerts]: [
      QualitySummaryResult,
      QualityTrendPoint[],
      ModelQualityBreakdown[],
      FlaggedContentAlert[]
    ] = yield all([
      call(() => qualityClientService.getQualitySummary(model, timeRange, service)),
      call(() => qualityClientService.getQualityTrend(model, days)),
      call(() => qualityClientService.getModelBreakdown(timeRange)),
      call(() => qualityClientService.getFlaggedContent()),
    ]);

    yield put(
      qualityActions.qualitySuccess({
        summary,
        trend: Array.isArray(trend) ? trend : [],
        models: Array.isArray(models) ? models : [],
        flaggedAlerts: Array.isArray(flaggedAlerts) ? flaggedAlerts : [],
      })
    );

    eventBus.emit(QUALITY_EVENTS.FETCHED, { model, timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || QUALITY_CONFIG_DEFAULTS.ERROR_FETCH_FAILED;
    yield put(qualityActions.qualityFailed(errorMsg));
    eventBus.emit(QUALITY_EVENTS.FAILED, { error: errorMsg });
  }
}



export function* qualitySaga() {
  yield takeEvery(qualityActions.fetchQualitySubmitted.type, handleFetchQuality);
}
