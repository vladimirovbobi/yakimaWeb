import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-black flex flex-col lg:grid lg:grid-cols-2">
      <aside className="hidden lg:flex relative bg-deep border-r border-gold/14 flex-col p-10 overflow-hidden">
        <div
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_rgba(191,160,106,0.18)_0%,_transparent_55%)]"
          aria-hidden
        />
        <div
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_rgba(191,160,106,0.08)_0%,_transparent_55%)]"
          aria-hidden
        />
        <Link
          href="/"
          className="relative z-10 font-serif tracking-luxe uppercase text-gold text-xl"
        >
          Yakima Web
        </Link>
        <div className="relative z-10 flex-1 flex flex-col justify-center max-w-lg">
          <div className="ey mb-6">For the people actually here</div>
          <h1 className="font-serif font-light text-ivory text-[clamp(2rem,3.5vw,3rem)] leading-[1.1]">
            Central Washington's home for realtors, services, and market truth.
          </h1>
          <p className="text-mist mt-6 leading-relaxed">
            License-verified blogs, a vendor marketplace with no middleman
            cut, AI tools, and a community that runs on real moderation.
          </p>
          <ul className="mt-10 space-y-3 text-sm text-mist">
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-gold" /> Verified
              Yakima Valley realtors
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-gold" /> Vendor
              lead-gen, no commissions
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-gold" />{" "}
              Reddit-shaped, AI-moderated forum
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-gold" /> Tools that
              actually save time
            </li>
          </ul>
        </div>
        <p className="relative z-10 text-[11px] uppercase tracking-luxe text-dim">
          (c) {new Date().getFullYear()} Yakima Web
        </p>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="flex items-center justify-between px-6 sm:px-10 py-6 lg:hidden">
          <Link
            href="/"
            className="font-serif tracking-luxe uppercase text-gold text-lg"
          >
            Yakima Web
          </Link>
        </header>
        <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </main>
    </div>
  );
}
