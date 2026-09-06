import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { useForm, FormProvider } from 'react-hook-form';
import { NumberField } from './NumberField';
import { Button } from '../primitives/Button';

function NumberFieldDemo() {
  const methods = useForm({
    defaultValues: { maxLatencyMs: 500, maxBudgetUsd: 100 },
  });

  return (
    <FormProvider {...methods}>
      <form className="space-y-4" onSubmit={(e) => { void methods.handleSubmit((data) => alert(JSON.stringify(data)))(e); }}>
        <NumberField name="maxLatencyMs" label="Max Latency" unit="ms" min={0} max={5000} />
        <NumberField name="maxBudgetUsd" label="Monthly Budget" unit="$" min={0} max={10000} />
        <Button type="submit" size="sm">Save Thresholds</Button>
      </form>
    </FormProvider>
  );
}

const meta = {
  title: 'Forms/NumberField',
  component: NumberField,
  parameters: { layout: 'centered' },
  args: { name: 'maxLatencyMs', label: 'Max Latency', unit: 'ms' },
  decorators: [(Story) => <div style={{ width: 320 }}><Story /></div>],
} satisfies Meta<typeof NumberField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <NumberFieldDemo />,
};
