"use client";

import { Badge } from "@repo/ui/components/badge";

// 用户角色类型
type UserRole = "admin" | "user" | "guest";

type RoleBadgeProps = {
  role: UserRole;
};

export function UserRoleBadge({ role }: RoleBadgeProps) {
  const badgeConfig = {
    admin: {
      variant: "destructive" as const,
      text: "管理员",
    },
    user: {
      variant: "default" as const,
      text: "普通用户",
    },
    guest: {
      variant: "outline" as const,
      text: "访客",
    },
  };

  const config = badgeConfig[role] || badgeConfig.guest;

  return (
    <Badge variant={config.variant}>
      {config.text}
    </Badge>
  );
} 