'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search, Check } from 'lucide-react';
import { cn } from '../../lib/utils/cn';

export interface DropdownItem {
  id: string | number;
  label: string;
  value?: string;
  description?: string;
  icon?: React.ReactNode;
}

interface SearchableDropdownProps {
  readonly items: readonly DropdownItem[];
  readonly value?: string;
  readonly onChange?: (val: string) => void;
  readonly placeholder?: string;
  readonly label?: string;
  readonly emptyMessage?: string;
  readonly className?: string;
  readonly disabled?: boolean;
  readonly showSearch?: boolean;
  readonly align?: 'left' | 'right';
}

export function SearchableDropdown({
  items = [],
  value,
  onChange,
  placeholder = 'Search...',
  label,
  emptyMessage = 'No options found',
  className,
  disabled = false,
  showSearch = false,
  align = 'left',
}: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedItem = items.find((i) => (i.value ?? String(i.id)) === value) || items[0];
  const shouldShowSearch = showSearch || items.length > 5;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredItems = search.trim()
    ? items.filter(
        (item) =>
          item.label.toLowerCase().includes(search.toLowerCase()) ||
          (item.description && item.description.toLowerCase().includes(search.toLowerCase()))
      )
    : items;

  const handleSelect = (item: DropdownItem) => {
    const val = item.value ?? String(item.id);
    if (onChange) {
      onChange(val);
    }
    setIsOpen(false);
    setSearch('');
  };

  return (
    <div ref={dropdownRef} className={cn('relative w-full text-left', className)}>
      {label && (
        <label className="block mb-1.5 text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
          {label}
        </label>
      )}

      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3.5 py-2 text-xs font-semibold text-[hsl(var(--foreground))] shadow-xs hover:border-purple-500/60 focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 cursor-pointer transition-all"
      >
        <div className="flex items-center gap-2 truncate">
          {selectedItem?.icon && <span className="text-purple-400 shrink-0">{selectedItem.icon}</span>}
          <span className="truncate">{selectedItem ? selectedItem.label : placeholder}</span>
        </div>
        <ChevronDown size={14} className={cn('text-[hsl(var(--muted-foreground))] transition-transform duration-200 shrink-0', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div
          className={cn(
            'absolute top-[calc(100%+6px)] z-[100] min-w-[210px] w-max max-w-xs rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-2xl p-2 animate-in fade-in duration-150 text-xs backdrop-blur-md',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {shouldShowSearch && (
            <div className="flex items-center px-3 py-1.5 mb-2 rounded-xl bg-[hsl(var(--background))] border border-[hsl(var(--border))]">
              <Search size={14} className="text-[hsl(var(--muted-foreground))] mr-2 shrink-0" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={placeholder}
                className="w-full bg-transparent text-xs text-[hsl(var(--foreground))] outline-none placeholder:text-[hsl(var(--muted-foreground))]"
                autoFocus
              />
            </div>
          )}

          <div className="max-h-56 overflow-y-auto space-y-1">
            {filteredItems.length > 0 ? (
              filteredItems.map((item) => {
                const itemVal = item.value ?? String(item.id);
                const isSelected = itemVal === (selectedItem ? (selectedItem.value ?? String(selectedItem.id)) : '');
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelect(item)}
                    className={cn(
                      'flex w-full items-center justify-between gap-3 px-3 py-2 rounded-xl text-left transition-colors cursor-pointer',
                      isSelected
                        ? 'bg-purple-950/40 text-purple-200 font-bold border border-purple-500/40'
                        : 'hover:bg-[hsl(var(--muted)/.4)] text-[hsl(var(--foreground))]'
                    )}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      {item.icon && <span className="text-purple-400 shrink-0">{item.icon}</span>}
                      <div>
                        <div className="font-semibold leading-tight">{item.label}</div>
                        {item.description && (
                          <div className="text-[10px] text-[hsl(var(--muted-foreground))] font-normal mt-0.5">{item.description}</div>
                        )}
                      </div>
                    </div>
                    {isSelected && <Check size={14} className="text-purple-400 shrink-0" />}
                  </button>
                );
              })
            ) : (
              <div className="p-4 text-center text-xs text-[hsl(var(--muted-foreground))]">{emptyMessage}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
