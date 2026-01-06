import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'DaedalusSignal - AI Intelligence Aggregator',
    description: 'Surface high-signal content about agentic development, context engineering, and frontier AI tooling.',
    keywords: ['AI', 'machine learning', 'agentic systems', 'LLM', 'context engineering'],
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
