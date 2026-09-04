import { featureRegistry } from "@observability/shared-infra";
import { tracesReducer } from "./traces.slice";
import { tracesSaga } from "./traces.saga";

featureRegistry.register("traces", { reducer: tracesReducer, saga: tracesSaga });

export * from "./types";
export * from "./schema";
export * from "./queries";
export * from "./rules";
export * from "./service";
export * from "./constants";
export * from "./traces.slice";
export * from "./traces.saga";
export * from "./hooks";
export * from "./ui";

