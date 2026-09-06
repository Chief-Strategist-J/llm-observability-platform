import { featureRegistry } from "@observability/shared-infra";
import { overviewReducer } from "./overview.slice";
import { overviewSaga } from "./overview.saga";

featureRegistry.register("overview", { reducer: overviewReducer, saga: overviewSaga });

export * from "./types";
export * from "./schema";
export * from "./queries";
export * from "./rules";
export * from "./service";
export * from "./constants";
export * from "./overview.slice";
export * from "./overview.saga";
export * from "./hooks";
export * from "./ui";

