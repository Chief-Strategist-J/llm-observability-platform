import { featureRegistry } from "@observability/core";
import { authReducer } from "./auth.slice";
import { authSaga } from "./auth.saga";

featureRegistry.register("auth", { reducer: authReducer, saga: authSaga });

export * from "./auth.slice";
export * from "./auth.saga";
export * from "./ui/SignUpForm";
export * from "./ui/SignInForm";
export * from "./ui/RegisterOrgForm";
