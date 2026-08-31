import { configureStore } from "@reduxjs/toolkit";
import createSagaMiddleware from "redux-saga";
import { authReducer } from "../../features/auth/auth.slice";
import { authSaga } from "../../features/auth/auth.saga";
import { latencyReducer } from "../../features/latency/latency.slice";
import { latencySaga } from "../../features/latency/latency.saga";
import { qualityReducer } from "../../features/quality/quality.slice";
import { qualitySaga } from "../../features/quality/quality.saga";
import { overviewReducer } from "../../features/overview/overview.slice";
import { overviewSaga } from "../../features/overview/overview.saga";
import { tracesReducer } from "../../features/traces/traces.slice";
import { tracesSaga } from "../../features/traces/traces.saga";
import { costsReducer } from "../../features/costs/costs.slice";
import { costsSaga } from "../../features/costs/costs.saga";

const sagaMiddleware = createSagaMiddleware();

export const store = configureStore({
  reducer: {
    auth: authReducer,
    latency: latencyReducer,
    quality: qualityReducer,
    overview: overviewReducer,
    traces: tracesReducer,
    costs: costsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ thunk: false }).concat(sagaMiddleware),
});

sagaMiddleware.run(authSaga);
sagaMiddleware.run(latencySaga);
sagaMiddleware.run(qualitySaga);
sagaMiddleware.run(overviewSaga);
sagaMiddleware.run(tracesSaga);
sagaMiddleware.run(costsSaga);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
