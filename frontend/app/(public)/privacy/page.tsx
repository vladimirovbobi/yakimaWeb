import type { Metadata } from "next";
import Container from "@/components/layout/Container";

export const metadata: Metadata = {
  title: "Privacy policy",
  description: "How Yakima Web handles your data.",
};

export default function PrivacyPage() {
  return (
    <article className="section-y">
      <Container>
        <header className="max-w-3xl mb-10">
          <div className="ey mb-4">Legal</div>
          <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3.25rem)] leading-[1.1]">
            Privacy policy
          </h1>
          <p className="text-mist mt-5 leading-relaxed">
            Effective May 2026. We collect what we need to run the platform.
            Nothing extra.
          </p>
        </header>

        <div className="prose-page max-w-3xl">
          <h2>What we collect</h2>
          <ul>
            <li>
              <strong>Account data:</strong> email, display name, password
              hash, and (for realtors) license number used for ARELLO
              verification.
            </li>
            <li>
              <strong>Content you create:</strong> posts, comments, replies,
              listings, reviews, inquiries.
            </li>
            <li>
              <strong>Usage telemetry:</strong> page views, click events,
              error reports. We use Sentry for errors and Better Stack for
              uptime.
            </li>
            <li>
              <strong>Cookies:</strong> session cookies for auth (httpOnly,
              SameSite=Lax). No third-party tracking pixels.
            </li>
          </ul>

          <h2>What we don't collect</h2>
          <ul>
            <li>Your social-security number.</li>
            <li>Your bank or payment details. We don't process payments.</li>
            <li>Your real-time location.</li>
            <li>Anything from third-party trackers we'd embed for ad money.</li>
          </ul>

          <h2>How we use it</h2>
          <p>
            Account data lets you sign in. License data lets us verify
            realtors. Content lets the platform exist. Telemetry lets us fix
            bugs and keep the site fast. We do not sell your data, and we do
            not share it with marketing partners.
          </p>

          <h2>Who sees your content</h2>
          <p>
            Posts, threads, replies, listings, and reviews are public by
            default. Inquiries to vendors are visible to the vendor and to
            you. Direct messages between users (not yet built) will be
            end-to-end visible only to participants and to a moderator if
            flagged.
          </p>

          <h2>How long we keep it</h2>
          <p>
            Content stays as long as your account does. If you delete your
            account, we anonymize your authored content (replacing your name
            with "deleted user") within 30 days. License verification logs are
            retained for 7 years per ARELLO requirements.
          </p>

          <h2>Your rights</h2>
          <p>
            Email us to: see what we have on you, fix a record, delete your
            account, or export your data. We respond within 30 days.
          </p>

          <h2>Children</h2>
          <p>
            Yakima Web is not for users under 13. We don't knowingly collect
            data from anyone under 13.
          </p>

          <h2>Changes</h2>
          <p>
            If this policy changes materially, we email registered users at
            least 14 days before the change takes effect.
          </p>
        </div>
      </Container>
    </article>
  );
}
