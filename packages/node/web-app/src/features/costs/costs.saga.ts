import { call, put, takeEvery } from "redux-saga/effects";
import { costsActions } from "./costs.slice";
import { costsClientService } from "./service/costs-client.service";
import { eventBus } from "@observability/shared-infra";
import { COSTS_CONFIG_DEFAULTS, COSTS_EVENTS } from "./constants";
import type { CostSummaryResult, CostByProvider } from "./types";

function* handleFetchCosts(action: ReturnType<typeof costsActions.fetchCostsSubmitted>): Generator<any, void, any> {
  const payload = (action.payload || {}) as Record<string, any>;
  const { timeRange = "30d" } = payload;


  try {
    const summary: CostSummaryResult = yield call(() => costsClientService.getCostSummary(timeRange));
    const providers: CostByProvider[] = yield call(() => costsClientService.getCostProviders(timeRange));

    yield put(
      costsActions.costsSuccess({
        summary,
        providers: Array.isArray(providers) ? providers : [],
      })
    );

    eventBus.emit(COSTS_EVENTS.FETCHED, { timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || COSTS_CONFIG_DEFAULTS.ERROR_FETCH_FAILED;
    yield put(costsActions.costsFailed(errorMsg));
    eventBus.emit(COSTS_EVENTS.FAILED, errorMsg);
  }
}

export function* costsSaga() {
  yield takeEvery(costsActions.fetchCostsSubmitted.type, handleFetchCosts);
}

