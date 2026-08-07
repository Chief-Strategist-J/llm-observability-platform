import { all } from 'redux-saga/effects';
import { featureRegistry } from './feature-registry';

export function* rootSaga(): Generator {
  const sagas = featureRegistry.getAll().map(([, mod]) => mod.saga());
  yield all(sagas);
}
