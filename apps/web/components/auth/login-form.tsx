"use client";

import { cn } from "@repo/ui/lib/utils"
import { Button } from "@repo/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@repo/ui/components/card"
import { Input } from "@repo/ui/components/input"
import { Label } from "@repo/ui/components/label"
import { login } from "@/actions/auth"
import { useActionState } from "react"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@repo/ui/components/alert"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState, useEffect, useRef } from "react"
import { useAuth } from "@/contexts/auth.context";
import type { AuthActionState } from "@/types";

export function LoginForm({
  className,
  ...props
}: React.ComponentPropsWithoutRef<"div">) {
  const router = useRouter();
  const { setAuth } = useAuth();
  const [isPending, setIsPending] = useState(false);
  const formSubmitRef = useRef(false);
  const [state, formAction] = useActionState(login, {
    error: null,
    success: false,
  } as AuthActionState);

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

  const handleRegisterClick = () => {
    router.push("/register");
  };

  useEffect(() => {
    if (formSubmitRef.current) {
      formSubmitRef.current = false;
      
      if (state.success) {
        setAuth(true);
        router.push("/");
      }
      
      setIsPending(false);
    }
  }, [state, router, setAuth]);

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">登录</CardTitle>
          <CardDescription>
            输入您的邮箱和密码登录您的账户
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
                <div className="flex items-center">
                  <Label htmlFor="password">密码</Label>
                  <Link
                    href="#"
                    className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                  >
                    忘记密码?
                  </Link>
                </div>
                <Input 
                  id="password" 
                  name="password" 
                  type="password" 
                  required 
                  disabled={isPending}
                  autoComplete="current-password"
                />
              </div>
              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "登录中..." : "登录"}
              </Button>
            </div>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col">
          <div className="mt-4 text-center text-sm">
            还没有账号?{" "}
            <Button 
              variant="link" 
              className="p-0 h-auto font-normal underline underline-offset-4"
              onClick={handleRegisterClick}
            >
              注册
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
} 