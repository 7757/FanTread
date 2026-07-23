import type { Metadata, Viewport } from "next";
import "./globals.css";

const siteUrl = "https://7757.github.io/FanTread/";
const socialImage = "https://7757.github.io/FanTread/og.png";
const description =
  "FanTread is an open-source DeepSeek-powered terminal reader that extracts, cleans, and organizes webpages, articles, and posts.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
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
  alternates: {
    canonical: siteUrl,
  },
  openGraph: {
    title: "FanTread — Read less noise. Keep more meaning.",
    description,
    url: siteUrl,
    type: "website",
    siteName: "FanTread",
    images: [
      {
        url: socialImage,
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
    images: [socialImage],
  },
};

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
      <body>{children}</body>
    </html>
  );
}
