import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { Post } from "@/lib/api/types";
import PostEditorForm from "@/components/content/PostEditorForm";

export default async function EditPostPage(props: {
  params: Promise<{ slug: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (!user.is_realtor && !user.is_staff) redirect("/dashboard");

  const { slug } = await props.params;
  const post = await safeServerFetch<Post & { body?: string }>(
    `/api/v1/posts/${encodeURIComponent(slug)}/`,
    { method: "GET" },
    { auth: true },
  );

  if (!post) {
    return (
      <div className="max-w-3xl">
        <h1 className="font-serif font-light text-ivory text-3xl">
          Post not found
        </h1>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <div className="ey mb-3">Edit post</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-8">
        {post.title}
      </h1>
      <PostEditorForm
        mode="edit"
        initial={{
          slug: post.slug,
          title: post.title,
          excerpt: post.excerpt,
          body: post.body ?? "",
          tag_slugs: (post.tags || []).map((t) =>
            typeof t === "string" ? t : (t as { slug: string }).slug,
          ),
        }}
      />
    </div>
  );
}
