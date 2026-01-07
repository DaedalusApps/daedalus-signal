import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'DaedalusSignal - Intelligence Aggregator',
    description: 'Surface high-signal content about agentic development, context engineering, and frontier tooling.',
    keywords: ['machine learning', 'agentic systems', 'LLM', 'context engineering', 'tech news'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <head>
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body>{children}</body>
        </html>
    );
}
