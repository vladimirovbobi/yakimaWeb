import "server-only";
import { safeServerFetch } from "@/lib/api/server";

export interface CurrentUser {
  id: number;
  email: string;
  display_name: string;
  is_realtor: boolean;
  is_vendor: boolean;
  is_staff: boolean;
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  return await safeServerFetch<CurrentUser>("/api/v1/me/", {}, { auth: true });
}
