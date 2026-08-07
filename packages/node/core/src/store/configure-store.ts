import { configureStore } from '@reduxjs/toolkit';
import createSagaMiddleware from 'redux-saga';
import { featureRegistry } from './feature-registry';
import { rootSaga } from './root-saga';

export function createApplicationStore(extraReducers: Record<string, any> = {}) {
  const sagaMiddleware = createSagaMiddleware();
  const registeredReducers = Object.fromEntries(
    featureRegistry.getAll().map(([name, mod]) => [name, mod.reducer]),
  );

  const store = configureStore({
    reducer: {
      ...registeredReducers,
      ...extraReducers,
    },
    middleware: (getDefault) => getDefault({ serializableCheck: false }).concat(sagaMiddleware),
  });

  sagaMiddleware.run(rootSaga);
  return store;
}
