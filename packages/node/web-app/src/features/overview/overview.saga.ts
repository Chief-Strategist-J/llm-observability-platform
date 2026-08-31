import { call, put, takeEvery } from "redux-saga/effects";
import { overviewActions } from "./overview.slice";
import { overviewClientService } from "./service/overview-client.service";
import { eventBus } from "@observability/shared-infra";
import type { OverviewKPIAggregates, SystemHealthSLOBanner, RecentTracePreview } from "./types";

function* handleFetchOverview(action: ReturnType<typeof overviewActions.fetchOverviewSubmitted>): Generator<any, void, any> {
  const { timeRange = "24h" } = action.payload || {};

  try {
    const kpi: OverviewKPIAggregates = yield call([overviewClientService, "getKPISummary"], timeRange);
    const health: SystemHealthSLOBanner = yield call([overviewClientService, "getSystemHealth"]);
    const recentTraces: RecentTracePreview[] = yield call([overviewClientService, "getRecentTraces"]);

    yield put(
      overviewActions.overviewSuccess({
        kpi,
        health,
        recentTraces: Array.isArray(recentTraces) ? recentTraces : [],
      })
    );

    eventBus.emit("overview.fetched", { timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || "Failed to fetch overview summary";
    yield put(overviewActions.overviewFailed(errorMsg));
    eventBus.emit("overview.failed", errorMsg);
  }
}

export function* overviewSaga() {
  yield takeEvery(overviewActions.fetchOverviewSubmitted.type, handleFetchOverview);
}
