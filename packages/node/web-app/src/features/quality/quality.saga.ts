import { call, put, takeEvery } from "redux-saga/effects";
import { qualityActions } from "./quality.slice";
import { qualityClientService } from "./service/quality-client.service";
import { eventBus } from "../../core/event-bus/event-bus";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "./types";

function* handleFetchQuality(action: ReturnType<typeof qualityActions.fetchQualitySubmitted>): Generator<any, void, any> {
  const { model = "gpt-4o", timeRange = "24h", days = 7, service } = action.payload || {};

  try {
    const summary: QualitySummaryResult = yield call([qualityClientService, "getQualitySummary"], model, timeRange, service);
    const trend: QualityTrendPoint[] = yield call([qualityClientService, "getQualityTrend"], model, days);
    const models: ModelQualityBreakdown[] = yield call([qualityClientService, "getModelBreakdown"], timeRange);
    const flaggedAlerts: FlaggedContentAlert[] = yield call([qualityClientService, "getFlaggedContent"]);

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
    eventBus.emit("quality.failed", errorMsg);
  }
}

export function* qualitySaga() {
  yield takeEvery(qualityActions.fetchQualitySubmitted.type, handleFetchQuality);
}
