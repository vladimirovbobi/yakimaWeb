import Link from "next/link";
import Container from "@/components/layout/Container";

export default function NotFound() {
  return (
    <main className="min-h-screen flex items-center justify-center py-32">
      <Container className="text-center">
        <div className="ey mb-6">404</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(3rem,7vw,5rem)] leading-[1.05]">
          Lost in the valley.
        </h1>
        <p className="text-mist mt-6 max-w-md mx-auto leading-relaxed">
          The page you wanted has moved on - or never existed. Head home and
          start over.
        </p>
        <div className="mt-10">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
          >
            Back to home
          </Link>
        </div>
      </Container>
    </main>
  );
}
