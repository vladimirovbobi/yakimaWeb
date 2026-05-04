import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import PostEditorForm from "@/components/content/PostEditorForm";

export default async function NewPostPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/realtor/posts/new");
  if (!user.is_realtor && !user.is_staff) redirect("/dashboard");

  return (
    <div className="max-w-3xl">
      <div className="ey mb-3">New blog post</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-8">
        Write a new post
      </h1>
      <PostEditorForm mode="create" />
    </div>
  );
}
