import React from 'react';
import Link from 'next/link';
import { EmptyState } from '../components/states/EmptyState';
import { Button } from '../components/primitives/Button';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[500px] flex-col items-center justify-center p-8">
      <EmptyState
        title="404 — Page Not Found"
        description="The requested observability view or configuration route does not exist."
        action={
          <Link href="/">
            <Button variant="default">Return to Dashboard</Button>
          </Link>
        }
      />
    </div>
  );
}
