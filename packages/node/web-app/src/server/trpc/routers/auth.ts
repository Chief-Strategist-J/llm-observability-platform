import { z } from "zod";
import { router, publicProcedure, protectedProcedure } from "../trpc";
import { authApiClient } from "../../../lib/auth-client";

export const authRouter = router({
  createOrganization: publicProcedure
    .input(z.object({ name: z.string().min(2), slug: z.string().optional() }))
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.createOrganization(input.name, input.slug);
    }),

  deleteOrganization: protectedProcedure
    .input(z.object({ orgId: z.string() }))
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.deleteOrganization(input.orgId, ctx.session?.user?.email);
    }),

  createUser: protectedProcedure
    .input(
      z.object({
        email: z.string().email(),
        password: z.string().min(12).optional(),
        name: z.string(),
        org_id: z.string(),
        role: z.string().optional(),
        permissions: z.array(z.string()),
      })
    )
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.createUser(input, ctx.session?.user?.email);
    }),

  blockUser: protectedProcedure
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.blockUser(input.userId, ctx.session?.user?.email);
    }),

  deleteUser: protectedProcedure
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.deleteUser(input.userId, ctx.session?.user?.email);
    }),

  signUp: publicProcedure
    .input(
      z.object({
        email: z.string().email(),
        password: z.string().min(12),
        name: z.string(),
        organization_name: z.string(),
        role: z.string().optional(),
      })
    )
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.signUp(input);
    }),

  signIn: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string() }))
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.signIn(input);
    }),

  forgotPassword: publicProcedure
    .input(z.object({ email: z.string().email() }))
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.forgotPassword(input.email);
    }),

  resetPassword: publicProcedure
    .input(z.object({ token: z.string(), new_password: z.string().min(12) }))
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.resetPassword(input.token, input.new_password);
    }),

  changePassword: protectedProcedure
    .input(z.object({ current_password: z.string(), new_password: z.string().min(12) }))
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.changePassword(input.current_password, input.new_password, ctx.session?.user?.email);
    }),

  createApiKey: protectedProcedure
    .input(
      z.object({
        name: z.string(),
        org_id: z.string(),
        key_type: z.string().optional(),
        permissions: z.array(z.string()),
      })
    )
    .mutation(async ({ input, ctx }): Promise<unknown> => {
      return authApiClient.createApiKey(input, ctx.session?.user?.email);
    }),

  verifyApiKey: publicProcedure
    .input(z.object({ key: z.string(), required_permission: z.string().optional() }))
    .mutation(async ({ input }): Promise<unknown> => {
      return authApiClient.verifyApiKey(input.key, input.required_permission);
    }),

  listPermissions: publicProcedure.query(async (): Promise<unknown> => {
    return authApiClient.listPermissions();
  }),

  fetchAuditLogs: protectedProcedure.query(async ({ ctx }): Promise<unknown> => {
    return authApiClient.fetchAuditLogs(ctx.session?.user?.email);
  }),
});
