import { call, put, takeEvery } from "redux-saga/effects";
import { overviewActions } from "./overview.slice";
import { overviewClientService } from "./service/overview-client.service";
import { eventBus } from "@observability/shared-infra";
import { OVERVIEW_CONFIG_DEFAULTS, OVERVIEW_EVENTS } from "./constants";
import type { OverviewKPIAggregates, SystemHealthSLOBanner, RecentTracePreview } from "./types";

function* handleFetchOverview(action: ReturnType<typeof overviewActions.fetchOverviewSubmitted>): Generator<any, void, any> {
  const payload = (action.payload || {}) as Record<string, any>;
  const { timeRange = OVERVIEW_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE } = payload;


  try {
    const kpi: OverviewKPIAggregates = yield call(() => overviewClientService.getKPISummary(timeRange));
    const health: SystemHealthSLOBanner = yield call(() => overviewClientService.getSystemHealth());
    const recentTraces: RecentTracePreview[] = yield call(() => overviewClientService.getRecentTraces());

    yield put(
      overviewActions.overviewSuccess({
        kpi,
        health,
        recentTraces: Array.isArray(recentTraces) ? recentTraces : [],
      })
    );

    eventBus.emit(OVERVIEW_EVENTS.FETCHED, { timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || OVERVIEW_CONFIG_DEFAULTS.ERROR_FETCH_FAILED;
    yield put(overviewActions.overviewFailed(errorMsg));
    eventBus.emit(OVERVIEW_EVENTS.FAILED, errorMsg);
  }
}

export function* overviewSaga() {
  yield takeEvery(overviewActions.fetchOverviewSubmitted.type, handleFetchOverview);
}

