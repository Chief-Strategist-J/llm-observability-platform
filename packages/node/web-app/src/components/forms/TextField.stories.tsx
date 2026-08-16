import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { useForm, FormProvider } from 'react-hook-form';
import { TextField } from './TextField';
import { Button } from '../primitives/Button';

function TextFieldDemo({ defaultValues = { modelName: 'gpt-4o' } }: { defaultValues?: Record<string, string> }) {
  const methods = useForm({ defaultValues });

  return (
    <FormProvider {...methods}>
      <form className="space-y-4" onSubmit={(e) => { void methods.handleSubmit((data) => alert(JSON.stringify(data)))(e); }}>
        <TextField name="modelName" label="Model Name" placeholder="e.g. gpt-4o" />
        <Button type="submit" size="sm">Submit</Button>
      </form>
    </FormProvider>
  );
}

const meta = {
  title: 'Forms/TextField',
  component: TextField,
  parameters: { layout: 'centered' },
  args: { name: 'modelName', label: 'Model Name' },
  decorators: [(Story) => <div style={{ width: 320 }}><Story /></div>],
} satisfies Meta<typeof TextField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <TextFieldDemo />,
};

export const Empty: Story = {
  render: () => <TextFieldDemo defaultValues={{ modelName: '' }} />,
};
