import Link from "next/link";

interface VerifySentPageProps {
  searchParams: Promise<{ email?: string }>;
}

export default async function VerifyEmailSentPage({
  searchParams,
}: VerifySentPageProps) {
  const sp = await searchParams;
  const email = sp.email || null;

  return (
    <div className="text-center">
      <div className="ey mb-5">Check your inbox</div>
      <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
        We sent a verification link.
      </h1>
      {email ? (
        <p className="text-mist mt-4 leading-relaxed">
          Check{" "}
          <span className="text-ivory font-mono text-sm">{email}</span>{" "}
          and click the link to confirm your account.
        </p>
      ) : (
        <p className="text-mist mt-4 leading-relaxed">
          Check your inbox and click the link to confirm your account.
        </p>
      )}
      <p className="text-mist mt-3 text-sm">
        Didn't get it? Look in spam, or sign up again.
      </p>
      <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href="/login"
          className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
        >
          Continue to sign in
        </Link>
        <Link
          href="/signup"
          className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
        >
          Sign up again
        </Link>
      </div>
    </div>
  );
}
