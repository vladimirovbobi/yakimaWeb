import Link from "next/link";
import { serverFetch } from "@/lib/api/server";

interface VerifyPageProps {
  params: Promise<{ key: string }>;
}

export default async function VerifyEmailPage({ params }: VerifyPageProps) {
  const { key } = await params;
  let success = false;
  let errorMsg: string | null = null;

  try {
    await serverFetch(`/api/v1/auth/verify-email/${key}/`, {
      method: "POST",
    });
    success = true;
  } catch (err) {
    const e = err as { problem?: { detail?: string; title?: string } };
    errorMsg =
      e.problem?.detail ||
      e.problem?.title ||
      "We couldn't verify this link. It may have expired.";
  }

  return (
    <div className="text-center">
      <div className="ey mb-5">Email verification</div>
      {success ? (
        <>
          <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
            You're in.
          </h1>
          <p className="text-mist mt-4 leading-relaxed">
            Your email is verified. Sign in to start using Yakima Web.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors mt-8"
          >
            Continue to sign in
          </Link>
        </>
      ) : (
        <>
          <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
            Couldn't verify.
          </h1>
          <p className="text-err mt-4 text-sm">{errorMsg}</p>
          <p className="text-mist mt-3 leading-relaxed">
            The link may have expired or already been used.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
            >
              Sign up again
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 text-mist hover:text-gold transition-colors"
            >
              Sign in
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
