import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Videxa — Video intelligence, made clear",
  description: "Turn long videos into useful notes and grounded answers.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
