"use client";

import { cn } from "@repo/ui/lib/utils";
import { Button } from "@repo/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@repo/ui/components/card";
import { Input } from "@repo/ui/components/input";
import { Label } from "@repo/ui/components/label";
import { register } from "@/actions/auth";
import { useActionState } from "react";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@repo/ui/components/alert";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";

export function RegisterForm({
  className,
  ...props
}: React.ComponentPropsWithoutRef<"div">) {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);
  const formSubmitRef = useRef(false);
  const [state, formAction] = useActionState(register, {
    error: null,
    success: false,
  });

  // 在表单提交时设置loading状态
  const handleAction = async (formData: FormData) => {
    setIsPending(true);
    formSubmitRef.current = true;
    try {
      await formAction(formData);
    } catch (error) {
      console.error("表单提交错误:", error);
      setIsPending(false);
    }
  };

  // 使用useEffect处理成功注册后的路由跳转和重置loading状态
  useEffect(() => {
    // 只有在表单提交后才重置状态
    if (formSubmitRef.current) {
      // 重置表单提交标记
      formSubmitRef.current = false;
      
      if (state.success) {
        router.push("/login");
      }
      
      // 无论成功或失败都重置loading状态
      setIsPending(false);
    }
  }, [state, router]);

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">注册</CardTitle>
          <CardDescription>
            创建您的账户以访问所有功能
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action={handleAction}>
            <div className="flex flex-col gap-6">
              {state.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{state.error}</AlertDescription>
                </Alert>
              )}
              <div className="grid gap-2">
                <Label htmlFor="username">用户名</Label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="johndoe"
                  required
                  disabled={isPending}
                  autoComplete="username"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">邮箱</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="your@email.com"
                  required
                  disabled={isPending}
                  autoComplete="email"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">密码</Label>
                <Input 
                  id="password" 
                  name="password" 
                  type="password" 
                  required 
                  disabled={isPending}
                  autoComplete="new-password"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="confirmPassword">确认密码</Label>
                <Input 
                  id="confirmPassword" 
                  name="confirmPassword" 
                  type="password" 
                  required 
                  disabled={isPending}
                  autoComplete="new-password"
                />
              </div>
              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "注册中..." : "注册"}
              </Button>
            </div>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col">
          <div className="mt-4 text-center text-sm">
            已有账号?{" "}
            <Link href="/login" className="underline underline-offset-4">
              登录
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
} 