import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { AppShell } from "./AppShell";
import { SignUpForm } from "../../features/auth/ui/SignUpForm";

const meta: Meta<typeof AppShell> = {
  title: "Shell/AppShell",
  component: AppShell,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const AuthRouteCleanView: Story = {
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/auth/sign-up",
      },
    },
  },
  render: () => (
    <div className="auth-container">
      <SignUpForm
        initialName="Jaydeep"
        initialOrgName="Scaibu"
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        onSubmit={() => {}}
      />
    </div>
  ),
};

export const DashboardRouteView: Story = {
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/",
      },
    },
  },
  render: () => (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">System Overview Dashboard</h1>
      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        Real-time latency, cost, and quality monitoring for LLM operations.
      </p>
    </div>
  ),
};
