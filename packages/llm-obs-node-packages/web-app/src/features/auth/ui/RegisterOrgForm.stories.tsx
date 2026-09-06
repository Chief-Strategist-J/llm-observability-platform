import type { Meta, StoryObj } from "@storybook/react";
import { RegisterOrgForm } from "./RegisterOrgForm";

const meta: Meta<typeof RegisterOrgForm> = {
  title: "Auth/RegisterOrgForm",
  component: RegisterOrgForm,
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

export const PreFilledScaibu: Story = {
  args: {
    initialOrgName: "Scaibu",
    initialSlug: "scaibu",
    loading: false,
    errorMsg: null,
  },
};

export const LoadingState: Story = {
  args: {
    initialOrgName: "Scaibu",
    initialSlug: "scaibu",
    loading: true,
    errorMsg: null,
  },
};

export const ErrorState: Story = {
  args: {
    initialOrgName: "Scaibu",
    initialSlug: "scaibu",
    loading: false,
    errorMsg: "Organization name 'Scaibu' is already registered.",
  },
};

export const MobileView: Story = {
  parameters: {
    viewport: {
      defaultViewport: "mobile1",
    },
  },
  args: {
    initialOrgName: "Scaibu",
    initialSlug: "scaibu",
    loading: false,
    errorMsg: null,
  },
};
