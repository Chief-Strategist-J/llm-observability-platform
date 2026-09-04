import { HTTP_CONSTANTS } from "@observability/shared-infra";
import { webAppRegistryManager } from "@/lib/service-registry/web-app-registration";

export async function register() {
  if (process.env[HTTP_CONSTANTS.ENV_NEXT_RUNTIME] === HTTP_CONSTANTS.RUNTIME_NODEJS) {
    await webAppRegistryManager.register();
  }
}
