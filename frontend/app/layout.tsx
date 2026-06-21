import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const sans = IBM_Plex_Sans({ subsets: ["latin"], variable: "--font-sans", weight: ["400", "500", "600", "700"] });
const mono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["400", "500", "600"] });
export const metadata: Metadata = { title: "Vigil AI | Vigil Summit", description: "Triagem segura para o Vigil Summit." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="pt-BR"><body className={`${sans.variable} ${mono.variable}`}>{children}</body></html>; }