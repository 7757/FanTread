import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.includes("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  const ogImage = `${origin}/og.png`;
  const description =
    "FanTread is an open-source DeepSeek-powered terminal reader that extracts, cleans, and organizes webpages, articles, and posts.";

  return {
    title: "FanTread — Turn any link into what you actually need",
    description,
    authors: [{ name: "musk", url: "https://github.com/7757" }],
    creator: "musk",
    keywords: [
      "FanTread",
      "DeepSeek",
      "AI reader",
      "terminal",
      "CLI",
      "summarizer",
      "WeChat",
      "open source",
    ],
    openGraph: {
      title: "FanTread — Read less noise. Keep more meaning.",
      description,
      type: "website",
      siteName: "FanTread",
      images: [
        {
          url: ogImage,
          width: 1200,
          height: 630,
          alt: "FanTread — Read less noise. Keep more meaning.",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "FanTread — Read less noise. Keep more meaning.",
      description,
      images: [ogImage],
    },
  };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f2eee5",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
