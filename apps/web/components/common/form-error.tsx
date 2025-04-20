"use client";

import { Alert, AlertDescription } from "@repo/ui/components/alert";
import { AlertCircle } from "lucide-react";

/**
 * 表单错误消息组件
 */
export function FormErrorMessage({ message }: { message?: string }) {
  if (!message) return null;
  
  return (
    <Alert variant="destructive" className="mt-4">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
} 