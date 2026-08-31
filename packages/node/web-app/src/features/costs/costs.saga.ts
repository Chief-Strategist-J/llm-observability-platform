import { call, put, takeEvery } from "redux-saga/effects";
import { costsActions } from "./costs.slice";
import { costsClientService } from "./service/costs-client.service";
import { eventBus } from "@observability/shared-infra";
import type { CostSummaryResult, CostByProvider } from "./types";

function* handleFetchCosts(action: ReturnType<typeof costsActions.fetchCostsSubmitted>): Generator<any, void, any> {
  const { timeRange = "30d" } = action.payload || {};

  try {
    const summary: CostSummaryResult = yield call([costsClientService, "getCostSummary"], timeRange);
    const providers: CostByProvider[] = yield call([costsClientService, "getCostProviders"], timeRange);

    yield put(
      costsActions.costsSuccess({
        summary,
        providers: Array.isArray(providers) ? providers : [],
      })
    );

    eventBus.emit("costs.fetched", { timeRange });
  } catch (err: any) {
    const errorMsg = err?.message || "Failed to fetch cost metrics";
    yield put(costsActions.costsFailed(errorMsg));
    eventBus.emit("costs.failed", errorMsg);
  }
}

export function* costsSaga() {
  yield takeEvery(costsActions.fetchCostsSubmitted.type, handleFetchCosts);
}
