"use client"

import * as React from "react"
import { ThemeProvider } from "./theme.context"
import { AuthProvider } from "./auth.context"

interface ProvidersProps {
  children: React.ReactNode
  initialAuth: boolean
}

export function RootProviders({ children, initialAuth }: ProvidersProps) {
  return (
    <ThemeProvider>
      <AuthProvider initialAuth={initialAuth}>
        {children}
      </AuthProvider>
    </ThemeProvider>
  )
} 