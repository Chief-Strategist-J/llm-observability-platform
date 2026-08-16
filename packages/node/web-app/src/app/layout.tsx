import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { AppShell } from '../components/shell/AppShell';

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
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
