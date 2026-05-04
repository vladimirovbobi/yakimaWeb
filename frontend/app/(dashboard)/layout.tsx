import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import DashboardSidebar from "./DashboardSidebar";
import DashboardHeader from "./DashboardHeader";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard");

  return (
    <div className="min-h-screen bg-black flex flex-col">
      <DashboardHeader user={user} />
      <div className="flex-1 flex flex-col lg:flex-row">
        <DashboardSidebar user={user} />
        <main
          id="main"
          className="flex-1 min-w-0 px-4 sm:px-6 md:px-8 lg:px-12 py-8 sm:py-10 pb-[calc(72px+env(safe-area-inset-bottom))] lg:pb-12"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
