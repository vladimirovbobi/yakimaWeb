import Link from "next/link";
import Container from "./Container";

const columns = [
  {
    title: "Platform",
    links: [
      { name: "Marketplace", href: "/marketplace" },
      { name: "Community", href: "/community" },
      { name: "AI tools", href: "/tools" },
      { name: "Realtor blogs", href: "/blog" },
    ],
  },
  {
    title: "Resources",
    links: [
      { name: "Market data", href: "/market" },
      { name: "Help center", href: "/help" },
      { name: "Contact", href: "/contact" },
      { name: "Status", href: "/status" },
    ],
  },
  {
    title: "Legal",
    links: [
      { name: "Terms", href: "/terms" },
      { name: "Privacy", href: "/privacy" },
      { name: "License notice", href: "/license-notice" },
      { name: "Acceptable use", href: "/acceptable-use" },
    ],
  },
  {
    title: "Contact",
    links: [
      { name: "For realtors", href: "/realtors" },
      { name: "For vendors", href: "/vendors" },
      { name: "Press", href: "/press" },
      { name: "Careers", href: "/careers" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-deep border-t border-gold/14 mt-auto">
      <Container as="div" className="py-16">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10">
          <div className="md:col-span-1 space-y-4">
            <div className="font-serif tracking-luxe uppercase text-gold text-lg">
              Yakima Web
            </div>
            <p className="text-mist text-sm leading-relaxed max-w-xs">
              Central Washington's home for realtors, services, and market
              truth.
            </p>
          </div>

          {columns.map((col) => (
            <div key={col.title} className="space-y-3">
              <h3 className="ey">{col.title}</h3>
              <ul className="space-y-1">
                {col.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      data-touch
                      className="block py-2 text-mist hover:text-gold-hi text-sm transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-8 border-t border-gold/14 flex flex-col md:flex-row gap-4 justify-between text-xs text-dim safe-bottom-tight">
          <span className="tracking-label uppercase">
            (c) {new Date().getFullYear()} Yakima Web
          </span>
          <span className="max-w-2xl md:text-right text-[11px] leading-relaxed">
            Real estate licenses verified via ARELLO. Yakima Web does not
            represent buyers or sellers - see Terms.
          </span>
        </div>
      </Container>
    </footer>
  );
}
