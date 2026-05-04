import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import { Cormorant_Garamond, Raleway } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import { organizationLD, websiteLD, jsonLDScript } from "@/lib/seo";

const serif = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
  preload: true,
});

const sans = Raleway({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
  preload: true,
});

export const viewport: Viewport = {
  themeColor: "#080604",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
  colorScheme: "dark",
};

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: {
    default: "Yakima Real Estate Hub — Central Washington's grounded real estate community",
    template: "%s · Yakima Real Estate Hub",
  },
  description:
    "Central Washington's grounded hub for verified realtors, real conversations, and local market truth. Yakima Valley first.",
  metadataBase: new URL(SITE),
  manifest: "/manifest.json",
  applicationName: "Yakima Real Estate Hub",
  authors: [{ name: "Yakima Real Estate Hub" }],
  creator: "Yakima Real Estate Hub",
  publisher: "Yakima Real Estate Hub",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Yakima Web",
  },
  formatDetection: { telephone: false, address: false, email: false },
  alternates: { canonical: SITE },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE,
    siteName: "Yakima Real Estate Hub",
    title: "Yakima Real Estate Hub — Central Washington's grounded real estate community",
    description:
      "Central Washington's grounded hub for verified realtors, real conversations, and local market truth. Yakima Valley first.",
    images: [{ url: `${SITE}/og/default.jpg`, width: 1200, height: 630, alt: "Yakima Real Estate Hub" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Yakima Real Estate Hub",
    description: "Central Washington's grounded real estate community.",
    images: [`${SITE}/og/default.jpg`],
  },
  robots: {
    index: true,
    follow: true,
    "max-image-preview": "large",
    "max-snippet": -1,
    "max-video-preview": -1,
  },
  icons: {
    icon: [
      { url: "/icon.png", type: "image/png", sizes: "any" },
      { url: "/icon-192.png", type: "image/png", sizes: "192x192" },
      { url: "/icon-512.png", type: "image/png", sizes: "512x512" },
    ],
    apple: [{ url: "/apple-touch-icon.png" }],
  },
  category: "real estate",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const nonce = (await headers()).get("x-csp-nonce") || undefined;
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${serif.variable} ${sans.variable}`}
    >
      <head>
        <script
          type="application/ld+json"
          nonce={nonce}
          dangerouslySetInnerHTML={jsonLDScript([organizationLD(), websiteLD()])}
        />
      </head>
      <body className="min-h-screen flex flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[200] focus:px-4 focus:py-2 focus:bg-gold focus:text-black focus:text-xs focus:uppercase focus:tracking-luxe"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
