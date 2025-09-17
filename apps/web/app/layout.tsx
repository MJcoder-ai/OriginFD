import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "OriginFD - Energy System Platform",
  description:
    "Enterprise platform for solar PV, BESS, and hybrid energy system design, procurement, and operations.",
  keywords: [
    "solar",
    "energy storage",
    "BESS",
    "PV",
    "renewable energy",
    "ODL-SD",
  ],
  authors: [{ name: "OriginFD Team" }],
  creator: "OriginFD",
  publisher: "OriginFD",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXTAUTH_URL || "http://localhost:3000"),
  openGraph: {
    title: "OriginFD - Energy System Platform",
    description:
      "Enterprise platform for solar PV, BESS, and hybrid energy system design",
    url: "/",
    siteName: "OriginFD",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "OriginFD Platform",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OriginFD - Energy System Platform",
    description:
      "Enterprise platform for solar PV, BESS, and hybrid energy system design",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <link rel="stylesheet" href="/styles.css" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:bg-primary focus:text-primary-foreground px-3 py-1 rounded"
        >
          Skip to content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
