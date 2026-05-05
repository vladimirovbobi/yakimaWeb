import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import ServiceCard from "@/components/marketplace/ServiceCard";
import VendorChip from "@/components/marketplace/VendorChip";
import SignInPrompt from "@/components/auth/SignInPrompt";
import { Card, CardBody } from "@/components/ui/Card";
import { safeServerFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import { servicePlaceholder } from "@/lib/placeholders";
import type { Pagination, Review, Service } from "@/lib/api/types";
import InquiryForm from "./InquiryForm";
import ServiceTabs from "./ServiceTabs";

interface ServiceDetailProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({
  params,
}: ServiceDetailProps): Promise<Metadata> {
  const { slug } = await params;
  const service = await safeServerFetch<Service>(
    `/api/public/v1/services/${slug}/`,
    {},
    { cache: "no-store" },
  );
  if (!service) return { title: "Service" };
  const heroImg =
    service.hero_image_url ||
    servicePlaceholder(service.slug || service.id);
  return {
    title: service.title,
    description: service.tagline,
    openGraph: {
      title: service.title,
      description: service.tagline,
      images: [heroImg],
    },
  };
}

export default async function ServiceDetailPage({ params }: ServiceDetailProps) {
  const { slug } = await params;

  const [service, reviews, related, user] = await Promise.all([
    safeServerFetch<Service>(
      `/api/public/v1/services/${slug}/`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Review>>(
      `/api/public/v1/services/${slug}/reviews/?limit=10`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Service>>(
      `/api/public/v1/services/?limit=3&exclude_slug=${slug}`,
      {},
      { cache: "no-store" },
    ),
    getCurrentUser(),
  ]);

  if (!service) notFound();

  const heroFallback = servicePlaceholder(service.slug || service.id);
  const gallery =
    service.gallery && service.gallery.length > 0
      ? service.gallery
      : [service.hero_image_url || heroFallback];

  return (
    <>
      <section className="bg-deep border-b border-gold/14">
        <Container>
          <div className="py-10">
            <Link
              href="/services"
              className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-mist hover:text-gold"
            >
              <svg
                width="12"
                height="10"
                viewBox="0 0 12 10"
                fill="none"
                aria-hidden
              >
                <path
                  d="M11 5H1m0 0l4-4M1 5l4 4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              All services
            </Link>
          </div>
        </Container>
      </section>

      <section>
        <Container>
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-12 py-12">
            <div>
              {gallery.length > 0 && (
                <div className="relative aspect-[16/10] bg-warm overflow-hidden border border-gold/14">
                  <Image
                    src={gallery[0]}
                    alt={service.title}
                    fill
                    priority
                    sizes="(max-width: 1024px) 100vw, 800px"
                    className="object-cover"
                  />
                </div>
              )}
              {gallery.length > 1 && (
                <div className="mt-3 grid grid-cols-4 gap-3">
                  {gallery.slice(1, 5).map((src, i) => (
                    <div
                      key={i}
                      className="relative aspect-square bg-warm overflow-hidden border border-gold/14"
                    >
                      <Image
                        src={src}
                        alt=""
                        fill
                        sizes="180px"
                        className="object-cover"
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-10">
                <Link
                  href={`/services?category=${service.category.slug}`}
                  className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
                >
                  {service.category.name}
                </Link>
                <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,3.25rem)] leading-[1.1] mt-3">
                  {service.title}
                </h1>
                <p className="text-mist mt-5 leading-relaxed text-lg max-w-2xl">
                  {service.tagline}
                </p>
                <div className="mt-7 flex items-center gap-5">
                  <VendorChip vendor={service.vendor} />
                </div>
              </div>

              <div className="mt-12">
                <ServiceTabs service={service} reviews={reviews?.results || []} />
              </div>
            </div>

            <aside className="lg:sticky lg:top-28 lg:self-start">
              <Card hover={false} className="border-gold/30">
                <CardBody>
                  <div className="ey mb-2">Inquire</div>
                  {service.starting_price != null ? (
                    <p className="font-serif text-gold text-3xl mb-1">
                      ${service.starting_price.toLocaleString()}+
                    </p>
                  ) : (
                    <p className="font-serif text-gold text-2xl mb-1">
                      Custom quote
                    </p>
                  )}
                  <p className="text-[11px] uppercase tracking-luxe text-mist mb-6">
                    Free to send. No commitment.
                  </p>
                  {user ? (
                    <InquiryForm service={service} user={user} />
                  ) : (
                    <SignInPrompt
                      verb="inquire"
                      next={`/services/${service.slug}`}
                    />
                  )}
                </CardBody>
              </Card>
            </aside>
          </div>
        </Container>
      </section>

      {related && related.results.length > 0 && (
        <section className="section-y bg-deep border-y border-gold/14">
          <Container>
            <ScrollReveal>
              <h2 className="font-serif font-light text-ivory text-3xl mb-10">
                Related services
              </h2>
            </ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {related.results.slice(0, 3).map((s, i) => (
                <ScrollReveal key={s.id} delay={0.05 + i * 0.06}>
                  <ServiceCard service={s} />
                </ScrollReveal>
              ))}
            </div>
          </Container>
        </section>
      )}
    </>
  );
}
