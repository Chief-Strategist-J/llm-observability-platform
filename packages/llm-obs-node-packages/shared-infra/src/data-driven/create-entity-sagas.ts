import { call, put, takeEvery } from 'redux-saga/effects';
import { eventBus } from '../event-bus/event-bus';
import type { CrudPort } from './create-entity-adapter';

export function createEntitySagas<T extends { id: string }>(
  name: string,
  adapter: CrudPort<T>,
  slice: any,
) {
  function* fetchAll(): Generator {
    yield put(slice.actions.setStatus('loading'));
    try {
      const items = (yield call([adapter, adapter.list])) as T[];
      yield put(slice.actions.setAll(items));
      yield put(slice.actions.setStatus('idle'));
    } catch (err: any) {
      yield put(slice.actions.setError(err.message ?? 'Failed to fetch'));
      yield put(slice.actions.setStatus('error'));
    }
  }

  function* createOne(action: { type: string; payload: Partial<T> }): Generator {
    try {
      const item = (yield call([adapter, adapter.create], action.payload)) as T;
      yield put(slice.actions.upsertOne(item));
      eventBus.emit(`${name}.created`, item);
    } catch (err: any) {
      yield put(slice.actions.setError(err.message ?? 'Failed to create'));
    }
  }

  function* removeOne(action: { type: string; payload: string }): Generator {
    try {
      yield call([adapter, adapter.remove], action.payload);
      yield put(slice.actions.removeOne(action.payload));
      eventBus.emit(`${name}.removed`, { id: action.payload });
    } catch (err: any) {
      yield put(slice.actions.setError(err.message ?? 'Failed to remove'));
    }
  }

  return function* rootSaga(): Generator {
    yield takeEvery(`${name}/fetchAll`, fetchAll);
    yield takeEvery(`${name}/createOne`, createOne);
    yield takeEvery(`${name}/removeOne`, removeOne);
  };
}
