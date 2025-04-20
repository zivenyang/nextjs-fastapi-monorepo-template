/**
 * 用户更新操作的状态类型
 */
export type UserUpdateActionState = {
  status: "idle" | "error" | "success";
  message?: string;
}; 