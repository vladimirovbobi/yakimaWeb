import type { Metadata } from "next";
import Container from "@/components/layout/Container";

export const metadata: Metadata = {
  title: "Community guidelines",
  description:
    "How Yakima Web keeps the platform useful, honest, and free of spam.",
};

export default function GuidelinesPage() {
  return (
    <article className="section-y">
      <Container>
        <header className="max-w-3xl mb-10">
          <div className="ey mb-4">Guidelines</div>
          <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3.25rem)] leading-[1.1]">
            Community guidelines
          </h1>
          <p className="text-mist mt-5 leading-relaxed">
            These rules apply to every comment, thread, reply, listing, and
            review on Yakima Web. AI moderates first, humans handle the close
            calls.
          </p>
        </header>

        <div className="prose-page max-w-3xl">
          <h2>Stay on topic</h2>
          <p>
            Yakima Web is for Central Washington real estate. Off-topic posts -
            national politics, crypto, recruiting pitches, MLM threads - get
            removed. If a thread drifts somewhere productive, that's fine. If
            it drifts into bait, it's not.
          </p>

          <h2>No personal attacks</h2>
          <p>
            Disagree with the take, not the person. Calling a take wrong is
            fine. Calling someone a fool is not. Repeated attacks earn a
            timeout, then a ban.
          </p>

          <h2>No fair-housing violations</h2>
          <p>
            We strictly enforce federal Fair Housing rules and Washington state
            law. Don't reference protected characteristics in listings,
            descriptions, or recommendations. Our AI flags this aggressively;
            human review confirms.
          </p>

          <h2>No spam, no SEO sludge</h2>
          <p>
            One link to your blog inside a useful comment is fine. Five threads
            in a week that all link to the same affiliate page is spam.
            Repeated low-effort posts get nuked.
          </p>

          <h2>No doxxing or privacy violations</h2>
          <p>
            Don't post anyone's home address, phone number, employer, or
            family details unless they've put it on their public profile. Don't
            reveal the identity of anonymous posters.
          </p>

          <h2>Realtors and vendors play it straight</h2>
          <p>
            If you're posting in a professional capacity, identify yourself.
            Don't pose as a buyer to seed reviews. Don't game vote scores with
            sock-puppets. We can see it, and we will remove the account.
          </p>

          <h2>How moderation works</h2>
          <p>
            Layer 1 is a structural check (length, link count, blocklist).
            Layer 2 is an AI classifier hardened against prompt-injection
            attempts. Layer 3 is human review for anything ambiguous. The
            pipeline fails closed: if something looks like an attack, we err on
            the side of removing it.
          </p>

          <h2>Appeals</h2>
          <p>
            If your content was removed and you think it shouldn't have been,
            email us through the contact link in the footer. A human will
            review.
          </p>

          <h2>Bans</h2>
          <p>
            Three strikes earn a temporary ban. Repeated patterns or severe
            violations earn a permanent one. License-verified accounts that
            abuse their pip lose verification on top of the ban.
          </p>
        </div>
      </Container>
    </article>
  );
}
