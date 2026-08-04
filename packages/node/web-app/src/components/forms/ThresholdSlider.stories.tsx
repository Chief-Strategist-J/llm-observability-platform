import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { useForm, FormProvider } from 'react-hook-form';
import { ThresholdSlider } from './ThresholdSlider';
import { Button } from '../primitives/Button';

function ThresholdSliderDemo() {
  const methods = useForm({
    defaultValues: { latencySloMs: 200, costCapMicroUsd: 5000 },
  });

  return (
    <FormProvider {...methods}>
      <form className="space-y-6" onSubmit={methods.handleSubmit((data) => alert(JSON.stringify(data)))}>
        <ThresholdSlider name="latencySloMs" label="Latency SLO Threshold" min={50} max={1000} step={10} unit="ms" />
        <ThresholdSlider name="costCapMicroUsd" label="Cost Cap" min={1000} max={50000} step={500} unit="µ$" />
        <Button type="submit" size="sm">Update SLO Config</Button>
      </form>
    </FormProvider>
  );
}

const meta = {
  title: 'Forms/ThresholdSlider',
  component: ThresholdSlider,
  parameters: { layout: 'centered' },
  args: { name: 'latencySloMs', label: 'Threshold', min: 0, max: 1000 },
  decorators: [(Story) => <div style={{ width: 360 }}><Story /></div>],
} satisfies Meta<typeof ThresholdSlider>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <ThresholdSliderDemo />,
};
