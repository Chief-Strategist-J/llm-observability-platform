/**
 * @file route-guard.ts
 * @description Public Route Inspector & Route Endpoints Dictionary.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Declarative Endpoint Inspection:
 *    - Uses centralized `HTTP_CONSTANTS` for public routes (`/`, `/auth/sign-in`, `/auth/sign-up`, `/auth/callback`).
 *    - Automatically bypasses internal Next.js assets (`/_next`), API endpoints (`/api`), static assets, and favicon (`/favicon.ico`).
 */

import { HTTP_CONSTANTS } from "../constants";

export const PUBLIC_ROUTES: string[] = [
  HTTP_CONSTANTS.ENDPOINT_ROOT,
  HTTP_CONSTANTS.ENDPOINT_AUTH_SIGN_IN,
  HTTP_CONSTANTS.ENDPOINT_AUTH_SIGN_UP,
  HTTP_CONSTANTS.ENDPOINT_AUTH_CALLBACK,
];

export function isPublicRoute(
  pathname: string,
  publicRoutes: string[] = PUBLIC_ROUTES
): boolean {
  if (
    pathname.startsWith(HTTP_CONSTANTS.PREFIX_NEXT) ||
    pathname.startsWith(HTTP_CONSTANTS.PREFIX_API) ||
    pathname.includes(".") ||
    pathname === HTTP_CONSTANTS.ENDPOINT_FAVICON
  ) {
    return true;
  }
  return publicRoutes.some((route) => pathname.startsWith(route));
}
