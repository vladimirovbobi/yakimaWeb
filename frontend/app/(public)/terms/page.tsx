import type { Metadata } from "next";
import Container from "@/components/layout/Container";

export const metadata: Metadata = {
  title: "Terms of service",
  description: "Terms governing use of Yakima Web.",
};

export default function TermsPage() {
  return (
    <article className="section-y">
      <Container>
        <header className="max-w-3xl mb-10">
          <div className="ey mb-4">Legal</div>
          <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3.25rem)] leading-[1.1]">
            Terms of service
          </h1>
          <p className="text-mist mt-5 leading-relaxed">
            Effective May 2026. By using Yakima Web, you agree to these terms.
          </p>
        </header>

        <div className="prose-page max-w-3xl">
          <h2>The platform</h2>
          <p>
            Yakima Web is a platform connecting Central Washington realtors,
            vendors, and locals. We host published content. We do not represent
            any party in any real estate transaction. We are not a real estate
            broker, agent, attorney, or lender.
          </p>

          <h2>Your account</h2>
          <p>
            You're responsible for what happens under your account. Use a
            unique password. Enable 2FA. Don't share your account. If you
            suspect compromise, change your password and contact us.
          </p>

          <h2>What you publish</h2>
          <p>
            You retain ownership of content you post. By posting, you grant
            Yakima Web a non-exclusive worldwide license to display,
            distribute, and moderate that content on the platform. You promise
            you have the right to post it and that it doesn't violate the law,
            our guidelines, or anyone else's rights.
          </p>

          <h2>License verification</h2>
          <p>
            Realtors who claim a verified pip must hold a current, active real
            estate license in the state on file. We re-verify periodically.
            Misrepresenting license status is grounds for permanent ban and we
            may report violations to the appropriate state real estate
            commission.
          </p>

          <h2>Marketplace</h2>
          <p>
            The marketplace is lead-generation only. We don't process payments,
            we don't escrow funds, we don't guarantee work quality. Your
            agreement is between you and the vendor. Reviews are honest
            opinions of users; we don't validate them as fact.
          </p>

          <h2>Fair Housing</h2>
          <p>
            All listings, descriptions, and recommendations on Yakima Web must
            comply with the federal Fair Housing Act and Washington state
            anti-discrimination law. Violations are removed without notice and
            may result in account termination.
          </p>

          <h2>Prohibited use</h2>
          <ul>
            <li>Scraping the platform for commercial use without permission.</li>
            <li>Posting malware, phishing links, or attack payloads.</li>
            <li>Impersonating another person or organization.</li>
            <li>Using the platform to harass or threaten anyone.</li>
            <li>Circumventing rate limits or moderation.</li>
          </ul>

          <h2>Liability</h2>
          <p>
            The platform is provided as-is. We do our best to keep it up,
            secure, and accurate, but we make no warranties. We are not
            liable for indirect or consequential damages, lost profits, or
            losses arising from third-party content.
          </p>

          <h2>Termination</h2>
          <p>
            We may suspend or terminate accounts that violate these terms or
            our guidelines. You may close your account anytime - see our
            privacy policy for what happens to your data.
          </p>

          <h2>Changes</h2>
          <p>
            If we change these terms materially, we email registered users at
            least 14 days before the change takes effect. Continued use after
            the effective date counts as acceptance.
          </p>

          <h2>Governing law</h2>
          <p>
            These terms are governed by Washington state law. Any disputes go
            to courts located in Yakima County, WA.
          </p>
        </div>
      </Container>
    </article>
  );
}
