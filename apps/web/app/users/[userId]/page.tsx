import { NavBar } from "@/components/layout/nav-bar";
import { checkAuthStatus } from "@/actions/auth";
import { getCurrentUser, getUserById, checkUserPermission } from "@/actions/user";
import { redirect } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Button } from "@repo/ui/components/button";
import { UserRoleBadge } from "@/components/user/role-badge";

// 用户详情页面
export default async function UserDetailPage({ 
  params 
}: { 
  params: { userId: string } 
}) {
  // 检查认证状态
  const isAuthenticated = await checkAuthStatus();
  
  if (!isAuthenticated) {
    redirect("/login");
  }
  
  // 检查当前用户是否有权限访问用户详情
  const hasPermission = await checkUserPermission("admin");
  
  // 如果不是管理员，检查是否是查看自己的信息
  if (!hasPermission) {
    const currentUser = await getCurrentUser();
    
    if (!currentUser || currentUser.id !== params.userId) {
      // 如果不是管理员，且不是查看自己的信息，则显示无权限信息
      return (
        <div className="flex flex-col min-h-svh">
          <NavBar />
          <div className="container mx-auto px-4 py-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold mb-6">用户详情</h1>
              <p>您没有权限查看此用户信息</p>
              <Button 
                onClick={() => redirect("/profile")} 
                className="mt-4"
              >
                返回个人资料
              </Button>
            </div>
          </div>
        </div>
      );
    }
  }
  
  // 获取用户信息
  const user = await getUserById(params.userId);
  
  if (!user) {
    return (
      <div className="flex flex-col min-h-svh">
        <NavBar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-6">用户详情</h1>
            <p>用户不存在或已被删除</p>
            <Button 
              onClick={() => redirect("/profile")} 
              className="mt-4"
            >
              返回个人资料
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
          <h1 className="text-2xl font-bold">用户详情</h1>
          <div className="flex items-center gap-3">
            <UserRoleBadge role={user.role || "guest"} />
            {hasPermission && (
              <Button variant="outline" size="sm">编辑用户</Button>
            )}
          </div>
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
            <Card>
              <CardHeader>
                <CardTitle>账户信息</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">用户ID</p>
                      <p className="font-medium break-all">{user.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">用户名</p>
                      <p className="font-medium">{user.username || "未设置"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">全名</p>
                      <p className="font-medium">{user.full_name || "未设置"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">电子邮箱</p>
                      <p className="font-medium">{user.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">账户状态</p>
                      <p className="font-medium">{user.is_active ? "活跃" : "已禁用"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">邮箱验证</p>
                      <p className="font-medium">{user.is_verified ? "已验证" : "未验证"}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {user.profile && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>个人资料</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground">个人简介</p>
                      <p className="font-medium">{user.profile.bio || "未设置"}</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">手机号码</p>
                        <p className="font-medium">{user.profile.phone_number || "未设置"}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">地址</p>
                        <p className="font-medium">{user.profile.address || "未设置"}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {hasPermission && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>管理员操作</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">重置密码</p>
                        <p className="text-sm text-muted-foreground">向用户发送密码重置链接</p>
                      </div>
                      <Button variant="outline" size="sm">发送</Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{user.is_active ? "禁用账户" : "启用账户"}</p>
                        <p className="text-sm text-muted-foreground">
                          {user.is_active ? "暂时阻止用户登录" : "允许用户登录系统"}
                        </p>
                      </div>
                      <Button 
                        variant={user.is_active ? "destructive" : "default"} 
                        size="sm"
                      >
                        {user.is_active ? "禁用" : "启用"}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 