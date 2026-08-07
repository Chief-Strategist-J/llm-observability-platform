import { createEntityAdapter as createRtkAdapter, createSlice, type PayloadAction } from '@reduxjs/toolkit';

export function createEntitySlice<T extends { id: string }>(name: string) {
  const rtkAdapter = createRtkAdapter<T>();
  const slice = createSlice({
    name,
    initialState: rtkAdapter.getInitialState({
      status: 'idle' as 'idle' | 'loading' | 'error',
      error: null as string | null,
    }),
    reducers: {
      setAll(state, action: PayloadAction<T[]>) {
        rtkAdapter.setAll(state as any, action.payload);
      },
      upsertOne(state, action: PayloadAction<T>) {
        rtkAdapter.upsertOne(state as any, action.payload);
      },
      removeOne(state, action: PayloadAction<string>) {
        rtkAdapter.removeOne(state as any, action.payload);
      },
      setStatus(state, action: PayloadAction<'idle' | 'loading' | 'error'>) {
        state.status = action.payload;
      },
      setError(state, action: PayloadAction<string | null>) {
        state.error = action.payload;
      },
    },
  });

  return { slice, selectors: rtkAdapter.getSelectors() };
}
