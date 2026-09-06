import type { Meta, StoryObj } from "@storybook/react";
import { SignInForm } from "./SignInForm";

const meta: Meta<typeof SignInForm> = {
  title: "Auth/SignInForm",
  component: SignInForm,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    onSubmit: { action: "submitted" },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    loading: false,
    errorMsg: null,
  },
};

export const PreFilledJaydeep: Story = {
  args: {
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: false,
    errorMsg: null,
  },
};

export const LoadingState: Story = {
  args: {
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: true,
    errorMsg: null,
  },
};

export const UserBlockedError: Story = {
  args: {
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: false,
    errorMsg: "Access Denied: Your user account has been blocked by your organization administrator.",
  },
};

export const MobileView: Story = {
  parameters: {
    viewport: {
      defaultViewport: "mobile1",
    },
  },
  args: {
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: false,
    errorMsg: null,
  },
};
