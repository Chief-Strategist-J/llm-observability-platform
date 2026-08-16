import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Sidebar } from '../components/shell/Sidebar';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});

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
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="flex min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))] font-sans antialiased">
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
