import { NavBar } from "@/components/layout/nav-bar";
import { checkAuthStatus } from "@/actions/auth";
import { redirect } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Button } from "@repo/ui/components/button";

// 使用服务器端认证检查
export default async function ProfilePage() {
  // 在服务器端检查认证状态
  const isAuthenticated = await checkAuthStatus();
  
  // 如果未认证，直接重定向到登录页
  if (!isAuthenticated) {
    redirect("/login");
  }
  
  return (
    <div className="flex flex-col min-h-svh">
      <NavBar />
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">个人资料</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>用户信息</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center">
                <div className="w-32 h-32 rounded-full bg-muted flex items-center justify-center text-4xl mb-4">
                  👤
                </div>
                <h2 className="text-xl font-semibold">用户名</h2>
                <p className="text-muted-foreground">user@example.com</p>
                <Button variant="outline" className="mt-4 w-full">编辑资料</Button>
              </CardContent>
            </Card>
          </div>
          
          <div className="md:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>账户信息</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">用户名</p>
                      <p className="font-medium">user123</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">邮箱</p>
                      <p className="font-medium">user@example.com</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">注册时间</p>
                      <p className="font-medium">2024-01-01</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">账户状态</p>
                      <p className="font-medium">活跃</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>安全设置</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">修改密码</p>
                      <p className="text-sm text-muted-foreground">上次修改时间: 从未</p>
                    </div>
                    <Button variant="outline" size="sm">修改</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">双因素认证</p>
                      <p className="text-sm text-muted-foreground">增强账户安全</p>
                    </div>
                    <Button variant="outline" size="sm">启用</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
} 