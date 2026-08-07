import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { Sidebar } from '../components/shell/Sidebar';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'LLM Observability Platform',
  description: 'Real-time latency, cost, and quality monitoring for LLM operations',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))] antialiased">
        <Providers>
          <div className="flex w-full min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
