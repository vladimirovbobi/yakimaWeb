import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";

export default async function InvestigateIndexPage(props: {
  searchParams: Promise<{ user_id?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod/investigate");
  if (!user.is_staff) redirect("/dashboard");

  const { user_id } = await props.searchParams;
  if (user_id) {
    redirect(`/dashboard/mod/investigate/${encodeURIComponent(user_id)}`);
  }

  return (
    <div className="max-w-3xl">
      <div className="ey mb-3">Moderation</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-2">
        Investigate user
      </h1>
      <p className="text-mist mt-2">
        Open a composite dossier — posts, comments, flags, and mod history.
      </p>

      <form
        method="GET"
        className="mt-8 border border-gold/22 bg-deep p-6 space-y-4"
      >
        <label className="block">
          <span className="ey mb-2 block">User ID</span>
          <input
            type="number"
            name="user_id"
            min={1}
            required
            className="w-full bg-warm/40 border border-gold/22 text-ivory px-3 py-2"
          />
        </label>
        <button
          type="submit"
          className="px-5 py-3 border border-gold/40 text-gold uppercase tracking-luxe text-[11px] hover:bg-gold/10"
        >
          Open dossier
        </button>
      </form>

      <Link
        href="/dashboard/mod"
        className="inline-block mt-6 text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
      >
        ← Back to moderation
      </Link>
    </div>
  );
}
