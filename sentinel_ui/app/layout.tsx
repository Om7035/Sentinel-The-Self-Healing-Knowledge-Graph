import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'Sentinel Knowledge Graph',
    description: 'Self-Healing Temporal Knowledge Graph Visualization',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
