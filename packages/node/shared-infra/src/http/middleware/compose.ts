/**
 * @file compose.ts
 * @description Higher-Order Middleware Chain Composer.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Functional Right-to-Left Pipeline Composition:
 *    - Composes an ordered array of HttpMiddleware handlers into a single nested execution chain using `reduceRight`.
 *    - Guarantees execution order: Step 1 -> Step 2 -> ... -> Final Handler.
 */

import type { HttpMiddleware, HttpNext } from "./types";

export function compose<Ctx, Result>(
  ...middlewares: HttpMiddleware<Ctx, Result>[]
): HttpMiddleware<Ctx, Result> {
  return (finalNext: HttpNext<Ctx, Result>) =>
    middlewares.reduceRight((next, mw) => mw(next), finalNext);
}
