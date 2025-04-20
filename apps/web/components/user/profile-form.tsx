"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Button } from "@repo/ui/components/button";
import { Input } from "@repo/ui/components/input";
import { Label } from "@repo/ui/components/label";
import { Textarea } from "@repo/ui/components/textarea";
import { useActionState } from "react";
import { updateCurrentUser } from "@/actions/user";
import { FormErrorMessage } from "@/components/common/form-error";
import type { UserUpdateActionState } from "@/types/user";

// 定义用户类型（简化版）
type UserProfile = {
  avatar_url?: string | null;
  bio?: string | null;
  phone_number?: string | null;
  address?: string | null;
};

type User = {
  email?: string | null;
  username?: string | null;
  full_name?: string | null;
  id: string;
  created_at: string;
  updated_at?: string | null;
  last_login?: string | null;
  profile?: UserProfile | null;
  role?: string | null;
  is_superuser?: boolean | null;
};

// 定义初始状态
const initialState: UserUpdateActionState = {
  status: "idle",
  message: "",
};

// 用户个人资料表单组件
export function UserProfileForm({ user }: { user: User }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [formState, formAction] = useActionState(updateCurrentUser, initialState);
  
  // 监听表单状态变化
  useEffect(() => {
    if (formState.status === "success") {
      setShowSuccess(true);
      const timer = setTimeout(() => {
        setShowSuccess(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [formState.status]);
  
  // 处理表单提交
  const handleFormAction = async (formData: FormData) => {
    setIsSubmitting(true);
    try {
      await formAction(formData);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>编辑个人资料</CardTitle>
        <CardDescription>更新您的个人信息和联系方式</CardDescription>
      </CardHeader>
      <CardContent>
        {showSuccess && (
          <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">
            更新成功：您的个人资料已成功更新
          </div>
        )}
        
        <form action={handleFormAction} className="space-y-6">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">用户名</Label>
                <Input 
                  id="username" 
                  name="username" 
                  defaultValue={user.username || ""} 
                  placeholder="请输入用户名" 
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="full_name">全名</Label>
                <Input 
                  id="full_name" 
                  name="full_name" 
                  defaultValue={user.full_name || ""} 
                  placeholder="请输入您的全名" 
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">电子邮箱</Label>
                <Input 
                  id="email" 
                  name="email" 
                  type="email" 
                  defaultValue={user.email || ""} 
                  placeholder="your@email.com" 
                  required 
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="phone_number">手机号码</Label>
                <Input 
                  id="phone_number" 
                  name="phone_number" 
                  defaultValue={user.profile?.phone_number || ""} 
                  placeholder="请输入您的手机号码" 
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="address">地址</Label>
              <Input 
                id="address" 
                name="address" 
                defaultValue={user.profile?.address || ""} 
                placeholder="请输入您的地址" 
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="bio">个人简介</Label>
              <Textarea 
                id="bio" 
                name="bio" 
                defaultValue={user.profile?.bio || ""} 
                placeholder="请简单介绍一下您自己" 
                rows={3} 
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="avatar_url">头像URL</Label>
              <Input 
                id="avatar_url" 
                name="avatar_url" 
                defaultValue={user.profile?.avatar_url || ""} 
                placeholder="请输入您的头像URL地址" 
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">
                密码 <span className="text-sm text-muted-foreground">(如不修改请留空)</span>
              </Label>
              <Input 
                id="password" 
                name="password" 
                type="password" 
                placeholder="请输入新密码" 
              />
            </div>
          </div>
          
          {/* 表单错误信息 */}
          {formState.status === "error" && (
            <FormErrorMessage message={formState.message} />
          )}
          
          <div className="flex justify-end mt-6">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
              ) : null}
              保存更改
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
} 