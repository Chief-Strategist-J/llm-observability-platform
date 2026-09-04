import { all, call, put, takeEvery } from "redux-saga/effects";
import { qualityActions } from "./quality.slice";
import { qualityClientService } from "./service/quality-client.service";
import { eventBus } from "../../core/event-bus/event-bus";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "./types";

import { QUALITY_CONFIG_DEFAULTS } from "./constants";

function* handleFetchQuality(action: ReturnType<typeof qualityActions.fetchQualitySubmitted>): Generator<any, void, any> {
  const {
    model = QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL,
    timeRange = QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE,
    days = QUALITY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS,
    service,
  } = action.payload || {};

  try {
    const [summary, trend, models, flaggedAlerts]: [
      QualitySummaryResult,
      QualityTrendPoint[],
      ModelQualityBreakdown[],
      FlaggedContentAlert[]
    ] = yield all([
      call([qualityClientService, "getQualitySummary"], model, timeRange, service),
      call([qualityClientService, "getQualityTrend"], model, days),
      call([qualityClientService, "getModelBreakdown"], timeRange),
      call([qualityClientService, "getFlaggedContent"]),
    ]);

    yield put(
      qualityActions.qualitySuccess({
        summary,
        trend: Array.isArray(trend) ? trend : [],
        models: Array.isArray(models) ? models : [],
        flaggedAlerts: Array.isArray(flaggedAlerts) ? flaggedAlerts : [],
      })
    );

    eventBus.emit("quality.fetched", { model, timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || "Failed to fetch quality evaluation metrics";
    yield put(qualityActions.qualityFailed(errorMsg));
    eventBus.emit("quality.failed", { error: errorMsg });
  }
}


export function* qualitySaga() {
  yield takeEvery(qualityActions.fetchQualitySubmitted.type, handleFetchQuality);
}
