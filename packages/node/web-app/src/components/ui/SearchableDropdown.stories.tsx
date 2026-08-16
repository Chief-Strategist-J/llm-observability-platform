import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { SearchableDropdown } from './SearchableDropdown';
import { Monitor, Smartphone, Tablet, Tv, Watch, Globe } from 'lucide-react';

const devices = [
  { id: 1, label: 'Desktop', description: 'Windows, Mac, Linux', icon: <Monitor className="h-4 w-4" />, value: 'desktop' },
  { id: 2, label: 'Laptop', description: 'Portable computer', icon: <Monitor className="h-4 w-4" />, value: 'laptop' },
  { id: 3, label: 'Tablet', description: 'iPad, Android tablets', icon: <Tablet className="h-4 w-4" />, value: 'tablet' },
  { id: 4, label: 'Smartphone', description: 'iPhone, Android phones', icon: <Smartphone className="h-4 w-4" />, value: 'smartphone' },
  { id: 5, label: 'Smart TV', description: 'Connected television', icon: <Tv className="h-4 w-4" />, value: 'smart_tv' },
  { id: 6, label: 'Smartwatch', description: 'Wearable device', icon: <Watch className="h-4 w-4" />, value: 'smartwatch' },
  { id: 7, label: 'Web Browser', description: 'Any platform', icon: <Globe className="h-4 w-4" />, value: 'web' },
];

const meta: Meta<typeof SearchableDropdown> = {
  title: 'UI/SearchableDropdown',
  component: SearchableDropdown,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex w-80 flex-col gap-4 p-8 bg-[hsl(var(--background))] rounded-2xl border border-[hsl(var(--border))]">
      <SearchableDropdown
        emptyMessage="No devices found"
        items={devices}
        label="Choose a device"
        placeholder="Search devices..."
      />
    </div>
  ),
};
