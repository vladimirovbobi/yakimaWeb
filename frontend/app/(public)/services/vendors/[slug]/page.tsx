import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import ServiceCard from "@/components/marketplace/ServiceCard";
import SignInPrompt from "@/components/auth/SignInPrompt";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { safeServerFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import type { Pagination, Review, Service, VendorProfile } from "@/lib/api/types";
import { formatDate, pluralize } from "@/lib/utils";

interface VendorPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({
  params,
}: VendorPageProps): Promise<Metadata> {
  const { slug } = await params;
  const vendor = await safeServerFetch<VendorProfile>(
    `/api/public/v1/services/vendors/${slug}/`,
    {},
    { cache: "no-store" },
  );
  if (!vendor) return { title: "Vendor" };
  return {
    title: vendor.business_name,
    description: vendor.tagline || vendor.about || undefined,
  };
}

export default async function VendorProfilePage({ params }: VendorPageProps) {
  const { slug } = await params;
  const [vendor, services, reviews, user] = await Promise.all([
    safeServerFetch<VendorProfile>(
      `/api/public/v1/services/vendors/${slug}/`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Service>>(
      `/api/public/v1/services/?vendor=${slug}&limit=12`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Review>>(
      `/api/public/v1/services/vendors/${slug}/reviews/?limit=10`,
      {},
      { cache: "no-store" },
    ),
    getCurrentUser(),
  ]);

  if (!vendor) notFound();

  return (
    <>
      <section className="relative bg-deep border-b border-gold/14 overflow-hidden">
        {vendor.hero_url && (
          <>
            <div
              className="absolute inset-0 bg-cover bg-center opacity-30"
              style={{ backgroundImage: `url(${vendor.hero_url})` }}
              aria-hidden
            />
            <div
              className="absolute inset-0 bg-gradient-to-t from-deep via-deep/80 to-deep/40"
              aria-hidden
            />
          </>
        )}
        <Container>
          <div className="relative py-16 flex flex-col md:flex-row gap-8 items-start">
            {vendor.logo_url ? (
              <Image
                src={vendor.logo_url}
                alt=""
                width={120}
                height={120}
                className="rounded-full border border-gold/30 flex-shrink-0"
              />
            ) : (
              <div
                aria-hidden
                className="w-[120px] h-[120px] rounded-full bg-warm border border-gold/30 flex items-center justify-center text-gold font-serif text-4xl flex-shrink-0"
              >
                {vendor.business_name.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-[11px] uppercase tracking-luxe text-gold">
                  Vendor
                </span>
                {vendor.is_verified && <Badge tone="verified">Verified</Badge>}
              </div>
              <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3.5rem)] leading-[1.1]">
                {vendor.business_name}
              </h1>
              {vendor.tagline && (
                <p className="text-mist mt-4 text-lg leading-relaxed max-w-2xl">
                  {vendor.tagline}
                </p>
              )}
              <div className="mt-6 flex flex-wrap gap-6 text-[11px] uppercase tracking-luxe">
                {vendor.rating_avg != null && (
                  <span className="text-mist">
                    <span className="text-ivory">
                      {vendor.rating_avg.toFixed(1)}
                    </span>{" "}
                    rating ({vendor.rating_count}{" "}
                    {pluralize(vendor.rating_count, "review")})
                  </span>
                )}
                {vendor.service_area && (
                  <span className="text-mist">
                    Serves <span className="text-ivory">{vendor.service_area}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="section-y">
        <Container>
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-12">
            <div>
              {vendor.about && (
                <div className="mb-12">
                  <h2 className="font-serif font-light text-ivory text-3xl mb-5">
                    About
                  </h2>
                  <div
                    className="prose-page max-w-3xl"
                    dangerouslySetInnerHTML={{ __html: vendor.about }}
                  />
                </div>
              )}

              <div>
                <h2 className="font-serif font-light text-ivory text-3xl mb-8">
                  Services
                </h2>
                {services && services.results.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {services.results.map((s, i) => (
                      <ScrollReveal key={s.id} delay={0.05 + (i % 4) * 0.05}>
                        <ServiceCard service={s} />
                      </ScrollReveal>
                    ))}
                  </div>
                ) : (
                  <p className="text-mist text-sm">
                    No services published yet.
                  </p>
                )}
              </div>

              {reviews && reviews.results.length > 0 && (
                <div className="mt-16">
                  <h2 className="font-serif font-light text-ivory text-3xl mb-8">
                    Reviews
                  </h2>
                  <div className="space-y-6">
                    {reviews.results.map((r) => (
                      <div
                        key={r.id}
                        className="border border-gold/14 bg-deep p-5"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-sm text-ivory">
                            {r.reviewer.display_name}
                          </span>
                          <div
                            className="flex gap-0.5"
                            aria-label={`${r.rating} of 5`}
                          >
                            {[0, 1, 2, 3, 4].map((i) => (
                              <svg
                                key={i}
                                width="12"
                                height="12"
                                viewBox="0 0 12 12"
                                fill={i < r.rating ? "currentColor" : "none"}
                                stroke="currentColor"
                                className="text-gold"
                                aria-hidden
                              >
                                <path
                                  d="M6 1l1.545 3.13L11 4.635 8.5 7.07l.59 3.43L6 8.885 2.91 10.5l.59-3.43L1 4.635l3.455-.505L6 1z"
                                  strokeWidth="0.8"
                                />
                              </svg>
                            ))}
                          </div>
                          <span className="text-[11px] uppercase tracking-luxe text-dim ml-auto">
                            {formatDate(r.created_at)}
                          </span>
                        </div>
                        <p className="text-mist text-sm leading-relaxed">
                          {r.body}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <aside className="lg:sticky lg:top-28 lg:self-start">
              <Card hover={false} className="border-gold/30">
                <CardBody>
                  <div className="ey mb-3">Contact</div>
                  {user ? (
                    <div>
                      <p className="text-mist text-sm mb-5">
                        Reach out through any of their services. Inquiries go
                        straight to the vendor.
                      </p>
                      {services && services.results.length > 0 && (
                        <Link
                          href={`/services/${services.results[0].slug}`}
                          className="inline-flex w-full items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
                        >
                          Send inquiry
                        </Link>
                      )}
                    </div>
                  ) : (
                    <SignInPrompt
                      verb="contact this vendor"
                      next={`/services/vendors/${vendor.slug}`}
                    />
                  )}
                </CardBody>
              </Card>
            </aside>
          </div>
        </Container>
      </section>
    </>
  );
}
