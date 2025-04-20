import { NavBar } from "@/components/layout/nav-bar";
import { checkAuthStatus } from "@/actions/auth";
import { getCurrentUser } from "@/actions/user";
import { redirect } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Button } from "@repo/ui/components/button";
import { UserProfileForm } from "@/components/user/profile-form";
import { UserRoleBadge } from "@/components/user/role-badge";

// 使用服务器端认证检查
export default async function ProfilePage() {
  // 在服务器端检查认证状态
  const isAuthenticated = await checkAuthStatus();
  
  // 如果未认证，直接重定向到登录页
  if (!isAuthenticated) {
    redirect("/login");
  }
  
  // 获取当前用户信息
  const user = await getCurrentUser();
  
  if (!user) {
    return (
      <div className="flex flex-col min-h-svh">
        <NavBar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-6">个人资料</h1>
            <p>获取用户信息失败，请重新登录</p>
            <Button 
              onClick={() => redirect("/login")} 
              className="mt-4"
            >
              返回登录
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col min-h-svh">
      <NavBar />
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">个人资料</h1>
          <UserRoleBadge role={user.role || "guest"} />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>用户信息</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center">
                <div className="w-32 h-32 rounded-full bg-muted flex items-center justify-center text-4xl mb-4">
                  {user.profile?.avatar_url ? (
                    <img 
                      src={user.profile.avatar_url} 
                      alt={user.username || "用户头像"} 
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    "👤"
                  )}
                </div>
                <h2 className="text-xl font-semibold">{user.username || "未设置用户名"}</h2>
                <p className="text-muted-foreground">{user.email}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  注册时间: {new Date(user.created_at).toLocaleDateString()}
                </p>
                {user.last_login && (
                  <p className="text-sm text-muted-foreground">
                    最后登录: {new Date(user.last_login).toLocaleDateString()}
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
          
          <div className="md:col-span-2">
            <UserProfileForm user={user} />
          </div>
        </div>
        
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
              {user.is_superuser && (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">管理员控制面板</p>
                    <p className="text-sm text-muted-foreground">管理用户和系统设置</p>
                  </div>
                  <Button variant="default" size="sm">访问</Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 