import { featureRegistry } from "@observability/shared-infra";
import { qualityReducer } from "./quality.slice";
import { qualitySaga } from "./quality.saga";

featureRegistry.register("quality", { reducer: qualityReducer, saga: qualitySaga });

export * from "./types";
export * from "./schema";
export * from "./queries";
export * from "./rules";
export * from "./service";
export * from "./constants";
export * from "./quality.slice";
export * from "./quality.saga";
export * from "./hooks";
export * from "./ui";

