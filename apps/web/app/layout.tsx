import { Geist, Geist_Mono } from "next/font/google"
import { checkAuthStatus } from "@/actions/auth"

import "@repo/ui/globals.css"
import { RootProviders } from "@/contexts/providers"

const fontSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  // 服务器端检查认证状态
  const isAuthenticated = await checkAuthStatus();

  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body
        className={`${fontSans.variable} ${fontMono.variable} font-sans antialiased `}
      >
        <RootProviders initialAuth={isAuthenticated}>
          {children}
        </RootProviders>
      </body>
    </html>
  )
}