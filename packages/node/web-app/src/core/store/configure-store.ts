import { configureStore } from "@reduxjs/toolkit";
import createSagaMiddleware from "redux-saga";
import { authReducer } from "../../features/auth/auth.slice";
import { authSaga } from "../../features/auth/auth.saga";
import { latencyReducer } from "../../features/latency/latency.slice";
import { latencySaga } from "../../features/latency/latency.saga";

const sagaMiddleware = createSagaMiddleware();

export const store = configureStore({
  reducer: {
    auth: authReducer,
    latency: latencyReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ thunk: false }).concat(sagaMiddleware),
});

sagaMiddleware.run(authSaga);
sagaMiddleware.run(latencySaga);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
