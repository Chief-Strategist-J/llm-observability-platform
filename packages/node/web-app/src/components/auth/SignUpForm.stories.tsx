import type { Meta, StoryObj } from "@storybook/react";
import { SignUpForm } from "./SignUpForm";

const meta: Meta<typeof SignUpForm> = {
  title: "Auth/SignUpForm",
  component: SignUpForm,
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

export const PreFilled: Story = {
  args: {
    initialName: "Jaydeep",
    initialOrgName: "Scaibu",
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: false,
    errorMsg: null,
  },
};

export const Loading: Story = {
  args: {
    initialName: "Jaydeep",
    initialOrgName: "Scaibu",
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: true,
    errorMsg: null,
  },
};

export const ErrorState: Story = {
  args: {
    initialName: "Jaydeep",
    initialOrgName: "Scaibu",
    initialEmail: "jaydeep@gmail.com",
    initialPassword: "password12345",
    loading: false,
    errorMsg: "Organization name 'Scaibu' already exists in registry.",
  },
};
