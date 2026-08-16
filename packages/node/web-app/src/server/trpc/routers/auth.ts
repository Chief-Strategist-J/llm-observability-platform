import { z } from "zod";
import { router, publicProcedure, protectedProcedure } from "../trpc";
import { authApiClient } from "../../../lib/auth-client";

export const authRouter = router({
  // 1. Create Organization
  createOrganization: publicProcedure
    .input(z.object({ name: z.string().min(2), slug: z.string().optional() }))
    .mutation(async ({ input }) => {
      return authApiClient.createOrganization(input.name, input.slug);
    }),

  // 2. Soft Delete Organization
  deleteOrganization: protectedProcedure
    .input(z.object({ orgId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return authApiClient.deleteOrganization(input.orgId, ctx.session?.user?.email);
    }),

  // 3. Create User in Organization with Permissions
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
    .mutation(async ({ input, ctx }) => {
      return authApiClient.createUser(input, ctx.session?.user?.email);
    }),

  // 4. Block User
  blockUser: protectedProcedure
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return authApiClient.blockUser(input.userId, ctx.session?.user?.email);
    }),

  // 5. Soft Delete User
  deleteUser: protectedProcedure
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return authApiClient.deleteUser(input.userId, ctx.session?.user?.email);
    }),

  // 6. Sign Up
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
    .mutation(async ({ input }) => {
      return authApiClient.signUp(input);
    }),

  // 7. Sign In
  signIn: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string() }))
    .mutation(async ({ input }) => {
      return authApiClient.signIn(input);
    }),

  // 8. Forgot Password
  forgotPassword: publicProcedure
    .input(z.object({ email: z.string().email() }))
    .mutation(async ({ input }) => {
      return authApiClient.forgotPassword(input.email);
    }),

  // 9. Reset Password
  resetPassword: publicProcedure
    .input(z.object({ token: z.string(), new_password: z.string().min(12) }))
    .mutation(async ({ input }) => {
      return authApiClient.resetPassword(input.token, input.new_password);
    }),

  // 10. Change Password
  changePassword: protectedProcedure
    .input(z.object({ current_password: z.string(), new_password: z.string().min(12) }))
    .mutation(async ({ input, ctx }) => {
      return authApiClient.changePassword(input.current_password, input.new_password, ctx.session?.user?.email);
    }),

  // 11. Create API Key
  createApiKey: protectedProcedure
    .input(
      z.object({
        name: z.string(),
        org_id: z.string(),
        key_type: z.string().optional(),
        permissions: z.array(z.string()),
      })
    )
    .mutation(async ({ input, ctx }) => {
      return authApiClient.createApiKey(input, ctx.session?.user?.email);
    }),

  // 12. Verify API Key
  verifyApiKey: publicProcedure
    .input(z.object({ key: z.string(), required_permission: z.string().optional() }))
    .mutation(async ({ input }) => {
      return authApiClient.verifyApiKey(input.key, input.required_permission);
    }),

  // 13. List System Permissions
  listPermissions: publicProcedure.query(async () => {
    return authApiClient.listPermissions();
  }),

  // 14. Fetch Audit Logs
  fetchAuditLogs: protectedProcedure.query(async ({ ctx }) => {
    return authApiClient.fetchAuditLogs(ctx.session?.user?.email);
  }),
});
