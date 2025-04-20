import { Geist, Geist_Mono } from "next/font/google"
import { checkAuthStatus } from "@/actions/auth"

import "@repo/ui/globals.css"
import { Providers } from "@/components/providers"
import { AuthProvider } from "@/components/auth-provider"

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
        <Providers>
          <AuthProvider initialAuth={isAuthenticated}>
            {children}
          </AuthProvider>
        </Providers>
      </body>
    </html>
  )
}