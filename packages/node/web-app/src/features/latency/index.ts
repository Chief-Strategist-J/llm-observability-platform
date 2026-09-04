import { featureRegistry } from "@observability/shared-infra";
import { latencyReducer } from "./latency.slice";
import { latencySaga } from "./latency.saga";

featureRegistry.register("latency", { reducer: latencyReducer, saga: latencySaga });

export * from "./types";
export * from "./schema";
export * from "./queries";
export * from "./rules";
export * from "./service";
export * from "./constants";
export * from "./latency.slice";
export * from "./latency.saga";

