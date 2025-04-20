import { NavBar } from "@/components/layout/nav-bar";
import { checkAuthStatus } from "@/actions/auth";
import { checkUserPermission } from "@/actions/user";
import { redirect } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Button } from "@repo/ui/components/button";
import { UserRoleBadge } from "@/components/user/role-badge";
import Link from "next/link";
import { readUsers } from "@/openapi/sdk";
import { cookies } from "next/headers";

// 用户列表页面
export default async function UsersPage() {
  // 检查认证状态
  const isAuthenticated = await checkAuthStatus();
  
  if (!isAuthenticated) {
    redirect("/login");
  }
  
  // 检查当前用户是否有权限访问用户列表
  const hasPermission = await checkUserPermission("admin");
  
  if (!hasPermission) {
    // 如果不是管理员，显示无权限信息
    return (
      <div className="flex flex-col min-h-svh">
        <NavBar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-6">用户管理</h1>
            <p>您没有权限访问此页面</p>
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
  
  // 获取所有用户
  let users: any[] = [];
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;
    
    if (token) {
      const response = await readUsers({
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      users = response.data || [];
    }
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
  
  return (
    <div className="flex flex-col min-h-svh">
      <NavBar />
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">用户管理</h1>
          <Button>添加新用户</Button>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>用户列表</CardTitle>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <p className="text-center py-4">没有找到用户</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">用户</th>
                      <th className="text-left py-3 px-2">邮箱</th>
                      <th className="text-left py-3 px-2">角色</th>
                      <th className="text-left py-3 px-2">状态</th>
                      <th className="text-left py-3 px-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-2 flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs overflow-hidden">
                            {user.profile?.avatar_url ? (
                              <img 
                                src={user.profile.avatar_url} 
                                alt={user.username || ""} 
                                className="w-full h-full object-cover" 
                              />
                            ) : (
                              "👤"
                            )}
                          </div>
                          <span>{user.username || user.full_name || "未命名"}</span>
                        </td>
                        <td className="py-3 px-2">{user.email}</td>
                        <td className="py-3 px-2">
                          <UserRoleBadge role={user.role || "guest"} />
                        </td>
                        <td className="py-3 px-2">
                          <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {user.is_active ? "活跃" : "禁用"}
                          </span>
                        </td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-2">
                            <Link href={`/users/${user.id}`}>
                              <Button variant="outline" size="sm">查看</Button>
                            </Link>
                            <Button variant="outline" size="sm">编辑</Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 