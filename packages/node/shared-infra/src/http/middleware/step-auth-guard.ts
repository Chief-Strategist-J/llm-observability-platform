/**
 * @file step-auth-guard.ts
 * @description Middleware Step: Session Authentication & Redirect Guard.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Authentication Verification:
 *    - Verifies route publicity (`ctx.isPublic`) vs presence of valid session token (`ctx.sessionToken`).
 * 2. Automated Callback Redirect Construction:
 *    - If unauthenticated on a protected route, constructs sign-in redirect URL with `callbackUrl` query parameter.
 */

import { HTTP_CONSTANTS } from "../constants";
import type { HttpMiddleware, HttpMiddlewareCtx } from "./types";

export const withAuthGuard = (
  signInRoute = HTTP_CONSTANTS.ENDPOINT_AUTH_SIGN_IN
): HttpMiddleware<HttpMiddlewareCtx, unknown> => {
  return (next) => async (ctx) => {
    try {
      if (!ctx.isPublic && !ctx.sessionToken) {
        const redirect = new URL(signInRoute, ctx.reqUrl);
        redirect.searchParams.set(HTTP_CONSTANTS.PARAM_CALLBACK_URL, ctx.pathname);

        console.log(`Middleware Step - 3 - [StepAuthGuard] - Session Token Verification & Redirect Enforcement - [DONE]`);
        return next({
          ...ctx,
          redirectUrl: redirect.toString(),
        });
      }
      const res = await next(ctx);
      console.log(`Middleware Step - 3 - [StepAuthGuard] - Session Token Verification & Redirect Enforcement - [DONE]`);
      return res;
    } catch (err: any) {
      console.error(`Middleware Step - 3 - [StepAuthGuard] - Session Token Verification & Redirect Enforcement - [FAILED]`);
      throw err;
    }
  };
};
