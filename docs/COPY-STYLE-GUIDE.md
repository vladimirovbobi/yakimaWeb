# Copy Style Guide — Yakima Real Estate Hub

**Version:** 1.0
**Date:** 2026-05-03
**Owner:** Yakima Real Estate Hub Engineering
**Status:** Active
**Cross-references:** [SRS.md](./SRS.md), [ICD.md](./ICD.md), [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md)

---

## 1. Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Effective | 2026-05-03 |
| Owner | Yakima Real Estate Hub Engineering |
| Review cadence | Quarterly, plus before any new public surface ships |
| Approvers | Lead engineer + content reviewer (PR sign-off) |
| Supersedes | None — initial version |
| Distribution | Public to repo contributors. External writers receive an excerpt. |

Every PR that touches user-facing copy must reference this guide in its description. Reviewers reject copy that ignores the rules below — kindly, with the specific section number cited.

---

## 2. Voice Principles

The platform serves working realtors, vendors who already pay for leads elsewhere, and buyers who already know what a contingency is. Write for them, not at them.

### 2.1 Insider, not influencer

Real estate has its own vocabulary. Use it. We say *list*, *close*, *pending*, *backup offer*, *contingent*, *DOM*, *under contract*, *concession*, *escrow*, *FSBO*, *short sale*, *as-is*, *staging*, *comps*, *disclosure*. We do not say *leverage*, *synergy*, *ecosystem*, *journey*, *unlock value*, or *actionable insights*. If a sentence could appear in a SaaS company's quarterly earnings call, rewrite it.

A working agent reading our blog should think "yes, that's right." A buyer reading our marketplace copy should feel they're talking to someone who has done this before. Neither should think they're being sold to.

### 2.2 Local first

Yakima is not "the Pacific Northwest." It is dry, hot in summer, irrigated, agricultural, and very specifically *Yakima*. Write like you live here. References are welcome — and encouraged — when they're accurate:

- Yakima Valley, Lower Valley, Upper Valley
- Toppenish, Selah, Wapato, Sunnyside, Naches, Tieton, Zillah, Granger
- Ahtanum Ridge, Rattlesnake Hills, the Naches arm, the Yakima Greenway
- I-82, US-12, the Heritage Plaza, the Capitol Theatre
- Cascadia (region, not Seattle)
- "From Toppenish to Selah" as a regional shorthand

Avoid: Pacific Northwest as a default region tag, Seattle-coded phrasing ("rainy day", "ferry", "Sound"), generic "Washington" when you mean Central Washington, "the PNW" full stop.

### 2.3 Plain not corporate

- Short sentences. Active voice. Second person when the reader is the subject.
- Cut every word that does no work. *In order to* is *to*. *At this point in time* is *now*. *Utilize* is *use*. *Currently* is usually deletable.
- One idea per sentence. If you need a semicolon, you need two sentences.
- Front-load the verb. "Send the inquiry" beats "An inquiry can be sent."

### 2.4 Honest tradeoffs

We do lead-gen, not transactions. We say so. We do not pretend to handle escrow. We do not pretend the AI tools are flawless. We do not pretend an unverified license can post — we tell people why and how to fix it. Honest constraints are features, not apologies.

Examples:

- *"Lead-gen only — payments and contracts happen off-platform."* (Marketplace)
- *"Description writer drafts copy. You edit it. You sign it. You're the listing agent."* (AI tool)
- *"License verification can take up to a business day. We email you when ARELLO confirms."* (Realtor onboarding)

### 2.5 Quietly confident

No exclamation marks. No *amazing*, *truly*, *incredible*, *literally*. No *we're so excited*. The work speaks. Restraint reads as competence; enthusiasm reads as trying too hard.

| Cut | Use |
|---|---|
| Welcome to the future of Yakima real estate! | Yakima real estate, by the people who do it. |
| We're truly excited to launch... | We just shipped... |
| You'll absolutely love our new tool. | The new tool is here. |

---

## 3. Tone Matrix

Voice is constant. Tone shifts with context.

| Surface | Tone | Behavior |
|---|---|---|
| Marketing pages (home, about, category landings) | Warm-confident | Welcoming, specific, no hard sell. Lead with what we do; let the reader decide. |
| Auth flows (signup, signin, password reset) | Businesslike-helpful | Direct. State what's needed and why. No marketing copy in the form. |
| Onboarding (license verify, vendor application) | Patient-clear | Explain the steps. Set expectations on time. Acknowledge that this is friction, then justify it. |
| Error states | Blameless-specific | The system, not the user, is the subject of failure. Always include the next action. |
| Empty states | Useful-quiet | Three lines max. What's missing. Why it matters. The CTA. |
| Success states | Confirmation-only | "Saved." "Sent." Not "Awesome — saved!" |
| Mod actions | Firm-fair | State the rule. State what was done. No moralizing. |
| AI tool outputs | Cautiously precise | "Drafted from your inputs. Review before publishing." Always flag that it's machine-generated. |
| Email (transactional) | Action-clear | Subject says what happened. Body says what to do next, if anything. |
| Forum / comments rules | Direct-respectful | "We remove personal attacks. Disagree with the argument." |
| Status / outage messages | Composed-honest | What broke, what we're doing, when we'll update next. No "we apologize for any inconvenience." |

---

## 4. Word List

### 4.1 Use these

| Term | Notes |
|---|---|
| realtor | Lowercase, generic. The trademark "Realtor®" is reserved for NAR-member contexts. Use only when accuracy demands it (e.g., legal pages). |
| property | Generic. Specific types: house, condo, townhouse, lot, parcel. |
| listing | The MLS-side asset. "We help realtors draft listing copy." |
| vendor | Marketplace participant offering a service. Includes photographers, lenders, junk haulers, 3D tour operators, stagers. |
| lead | An inquiry sent through the marketplace. Always singular noun: "send a lead", "the lead landed in your inbox." |
| package | A bounded service offering by a vendor. Three tiers max: basic / standard / premium. |
| bundle | Multiple packages combined at a discount. |
| post | Content unit. Realtor blog post, Yakima Web post, lead-magnet page. |
| thread | Forum top-level item. |
| reply | Response to a thread or another reply. |
| license | Always WA real estate license. Specify type (broker, managing broker) when relevant. |
| verified | Status after ARELLO confirmation. Visible badge. |
| moderation | The process. *Moderator* is the role. *Mod console* is the tool. |
| close, closed, closing | Real estate transaction terms. |
| concession, contingency, escrow, comps, DOM, FSBO | Acceptable. Define on first mention only in beginner content. |
| Yakima Web | The organization. Always two words, both capitalized. |
| Yakima Real Estate Hub | The platform. Title case. Use full name on first mention; "the platform" or "the hub" thereafter. |
| Central Washington | Proper noun. Always capitalized. |
| real estate | Lowercase compound. Never one word. |

### 4.2 Avoid these

| Term | Why | Alternative |
|---|---|---|
| ninja, rockstar, guru | Hollow | The role itself ("agent", "vendor") |
| amazing, awesome, incredible | Empty | A specific claim |
| truly, really, very, super | Filler | Cut |
| leverage (verb) | Corporate | use, apply |
| utilize | Pretentious | use |
| in order to | Verbose | to |
| at this point in time | Verbose | now |
| at the end of the day | Cliche | Cut |
| robust, world-class, best-in-class | Empty marketing | A specific number or comparison |
| unique | Almost never literally true | Cut, or make a specific claim |
| game-changer, disruptor | SaaS theater | Cut |
| reach out | Corporate | email, call, message |
| circle back | Corporate | follow up |
| solution | Vague | the actual thing (tool, service, page, post) |
| ecosystem, platform play | Stop | Cut |
| journey | Saccharine | the process, the steps |
| unlock | Hollow | enable, allow, open |
| empower | Condescending | A specific verb |
| transformative, revolutionary | Hyperbole | Cut |
| seamless | Lying | Just describe the experience |
| effortless | Lying | Just describe the experience |
| at scale | Tech-bro | a specific number |
| bandwidth (figurative) | Office speak | time, capacity |
| stakeholder | Corporate | the actual people |
| optimize | Vague | A specific verb |
| solutionize | Not a word | Cut |

### 4.3 Capitalization rules

| Term | Form |
|---|---|
| Yakima Web | Two words. Both capitalized. The org. |
| Yakima Real Estate Hub | Title case. The platform. |
| real estate | Lowercase, two words, never *real-estate* or *realestate*. |
| Central Washington | Proper. Capitalized. |
| Pacific Northwest | Proper, but avoid as a region tag for our content. |
| ARELLO | All caps. Acronym. |
| MLS | All caps. |
| WA, Washington | Use *Washington* in long-form copy; *WA* in addresses or tight UI labels. |
| broker, managing broker | Lowercase except in titles. |
| license number | Lowercase. |
| Yakima Valley | Proper. |
| Lower Valley, Upper Valley | Proper when geographic, lowercase when figurative. |
| Realtor® | Reserved. Use only in NAR-trademark contexts. |

### 4.4 Numerals

Real estate runs on numbers. We default to numerals.

| Context | Form |
|---|---|
| Property metrics | 3 bed, 2 bath, 1,840 sqft, 0.31 acres |
| Prices | $429K, $1.2M, $429,000 (precise) |
| Year | 2026 (always four digits) |
| Phone | (509) 555-0142 |
| MLS, license numbers | Numerals as-is |
| Counts in narrative prose | Spell out zero through nine; use numerals for 10 and up. *Three offers came in. The 12 comparable sales were within 3% of asking.* |
| Time | 9:00 AM, 4:30 PM. AM/PM in caps, with the colon, single space. |
| Dates | May 3, 2026. Avoid 5/3/26. ISO (2026-05-03) in admin/tech surfaces only. |
| Percentages | 3%, not three percent, not 3 percent. |
| Range | $400K–$450K (en dash, no spaces). |

---

## 5. Microcopy Patterns

### 5.1 Buttons

- Verb-first. ≤3 words.
- Name the action. Never "Submit", "OK", "Click here", "Continue" (when something more specific applies).
- Sentence case for primary buttons in the platform UI; uppercase tracking-luxe is reserved for the brand label style on marketing pages.

| Context | Bad | Good |
|---|---|---|
| Signup form | Submit | Sign up |
| Inquiry form | Send | Send inquiry |
| Post editor | Publish post | Publish |
| Mod queue | Action | Approve / Remove / Defer |
| Vendor profile | Save | Save changes |
| AI tool | Run | Generate description |
| License flow | Continue | Verify license |
| Forum | Submit | Post reply |

### 5.2 Links

- Descriptive text. The link itself should make sense out of context.
- Same-tab by default.
- External links: open in new tab + add `aria-label="(opens in new tab)"`.
- Avoid "click here," "read more," "learn more" — use the destination as the label.

| Bad | Good |
|---|---|
| Click here for vendor details. | View vendor profile |
| Learn more. | How license verification works |
| Read more. | Read the full post |

### 5.3 Empty states

Three lines, max. Pattern: *what's missing → why it matters → CTA*.

**Empty leads list (vendor):**

> No leads yet.
> Buyers find vendors through the marketplace listing.
> Make sure your service description is current.
> [Edit service →]

**Empty saved searches (member):**

> Nothing saved yet.
> Save searches to get notified when new matches list.
> Search the marketplace and tap the bookmark.
> [Browse vendors →]

**Empty mod queue (mod):**

> Queue clear.
> New flagged items will appear here.
> Recent decisions in [Audit log].

**Empty comments (post):**

> First word is yours.
> [Sign in to comment]

### 5.4 Error states

Blameless, specific, actionable. Three rules:

1. The system, not the user, is the subject of failure.
2. State what happened in concrete terms.
3. Tell the reader the next action.

| Situation | Bad | Good |
|---|---|---|
| Email already in use | Error: invalid input | That email is already registered. [Sign in] or [reset password]. |
| ARELLO down | Verification failed | License check is unavailable right now. We'll retry automatically. You'll get an email when it's verified. |
| Wrong password | Authentication error | That password doesn't match. [Try again] or [reset password]. |
| Rate limited | Too many requests | You've hit the daily limit on this tool. Resets at midnight. |
| File too big | Upload failed | That file is over the 10 MB limit. Compress and re-upload. |
| Network drop on save | Network error | We couldn't save the change. Check your connection and [try again]. |
| AI tool output flagged | Content rejected | We couldn't generate that description — the input contained content our policy doesn't allow. Edit the prompt and try again. |

### 5.5 Success states

Confirmation. No celebration. No exclamation marks.

| Situation | Bad | Good |
|---|---|---|
| Post published | Awesome! Your post is live! | Published. [View post] |
| Lead sent | Great! We've sent your inquiry! | Inquiry sent. The vendor will reply by email. |
| Saved draft | Saved! | Draft saved. |
| Settings updated | Settings updated successfully! | Saved. |

### 5.6 Loading

Action-specific. The reader should know what is happening, not just that the app is alive.

| Bad | Good |
|---|---|
| Loading… | Verifying license… |
| Please wait | Drafting description… |
| Working on it | Sending inquiry… |
| Just a moment | Building your post preview… |

### 5.7 Confirmation dialogs

State the consequence. Use specific verbs in the buttons (avoid "OK"/"Cancel" as the only options).

> **Remove this comment?**
> The comment will be hidden from the public thread. The author will see a removal notice.
> [Remove] [Keep]

> **Delete this post?**
> This permanently removes the post and its comments. This cannot be undone.
> [Delete post] [Cancel]

> **Suspend vendor?**
> The vendor's services will be hidden from the marketplace. New leads will pause. Existing lead threads stay visible to both parties.
> [Suspend] [Cancel]

---

## 6. Form Labels & Helper Text

| Rule | Detail |
|---|---|
| Always label, never placeholder-only | Placeholders disappear on focus and fail accessibility. The label persists. |
| Helper text under input | Single line preferred. Constraints (length, format, allowed file types) belong here. |
| Error text between input and next field | Prefixed with an X icon (`role="alert"`). Replaces helper text on error. |
| Required fields marked with asterisk | An "All fields required unless noted" line at form top, or "Optional" suffix on optional labels. |
| Field name + question, not corporate jargon | "Your WA real estate license number" beats "License identifier (WA)". |

**Example — license field:**

```
WA real estate license number *
[___________________________]
14-digit ARELLO-issued ID. Find it on your DOL renewal letter.
```

**On error:**

```
WA real estate license number *
[___________________________]
✗ That doesn't match an active WA license. Check the digits and try again.
```

---

## 7. Accessibility Copy Patterns

| Pattern | Rule |
|---|---|
| Visually hidden context (`sr-only`) | Add when icons-only, or when visual context is implied. *"Sort by"* before a sort dropdown if the dropdown's selected value alone wouldn't make sense to a screen reader. |
| Status messages | `role="status" aria-live="polite"` for non-critical updates ("Saved", "Verifying…"). `role="alert" aria-live="assertive"` for errors that interrupt. |
| Form labels | Always paired via `for`/`id`. Never use the label as a button. |
| Link text | Descriptive — never "click here." |
| Image alt text | Specific. "Yakima Valley vineyards in late summer" beats "vineyard." Decorative images get `alt=""`. |
| Button vs link | Button = action. Link = navigation. Use the right semantic element. |
| Heading hierarchy | One `h1` per page. Don't skip levels (no `h2` then `h4`). |
| Language tag | `lang="en"` on `<html>`. Tag inline foreign-language phrases. |
| Keyboard | Every interactive element reachable by Tab. Visible focus ring. No "skip nav" hacks that break tab order. |
| ARIA | Use semantic HTML first. ARIA only when the platform doesn't provide the right element. |

---

## 8. Email Patterns

| Aspect | Rule |
|---|---|
| Subject | ≤50 characters. Action-clear. No clickbait. No emoji unless transactional context (e.g., a green check is acceptable in a confirmation). |
| Body opener | What happened, in one sentence. Then why we're emailing. |
| CTA | Single primary button. Verb-first. ("View inquiry", "Verify email", "Reset password.") |
| Footer | Plain-text reason for the email + opt-out (if applicable) + Yakima Web business address (CAN-SPAM). |
| From address | `hello@yakimaweb.com` for transactional + member-facing. `ops@yakimaweb.com` for system alerts to staff. `noreply@` is forbidden — replies go to a real inbox. |
| Reply behavior | Replies route to the right team based on `From`. |
| Plaintext fallback | Required. Should be readable, not just rendered HTML stripped. |

**Example — license verified:**

```
Subject: Your license is verified

Hi {first_name},

Your WA real estate license is verified. You can now publish posts on
Yakima Real Estate Hub.

[Start writing →]

This email was sent because you signed up for a realtor account at
yakimaweb.com. Manage email settings: yakimaweb.com/account/email/.

Yakima Web · 123 Yakima Ave · Yakima, WA 98901
```

**Example — lead received:**

```
Subject: New lead from {buyer_first_name}

{buyer_first_name} {buyer_last_initial}. asked about your "{service_name}" package.

[View inquiry →]

Reply through the platform or email {buyer_first_name} directly.
Lead-gen only — payments and contracts happen off-platform.

Yakima Web · 123 Yakima Ave · Yakima, WA 98901
```

---

## 9. Page-by-Page Copy Patterns

### 9.1 Home page hero

Pattern: **headline (5–8 words) → subhead (one sentence, claims a specific thing) → primary CTA + secondary link**.

> Yakima real estate, by the people who do it.
> Posts from local realtors. Tools that save listing time. A marketplace for the vendors agents already use.
> [Browse the marketplace] · [Sign up free]

Avoid: "Welcome to," "Discover," "The leading platform for…"

### 9.2 About page

Pattern: **what we do → who runs it → what we don't do → contact**.

- Lead paragraph: one sentence on what the platform is, one on who it serves.
- "Who runs it": names, brief credentials, location. People trust people.
- "What we don't do": *We don't broker. We don't take a cut of transactions. We don't run ad networks on user content.*
- Contact: an actual email and an actual phone, hours.

### 9.3 Blog post header / footer

**Header:**

- Title (Cormorant serif, large)
- Author byline + verified badge if realtor
- Date posted
- Reading time (computed)
- Tags (uppercase tracking-luxe, gold)

**Footer:**

- Author bio (one paragraph + link to profile)
- "Last updated" timestamp if edited post-publish
- Comment thread heading: "Discussion" (not "Comments")
- Sign-in prompt for anonymous readers: *"Member sign-in required to comment. [Sign in]"*

### 9.4 Marketplace category list

- H1: category name (sentence case). *"Real estate photographers in Yakima"*
- Lead paragraph: 2 sentences on what's in this category and how it works on the platform.
- Filter row: location, price range, package tier, response time. Labels not placeholders.
- Card content per vendor: name, package starting price, response-time average, verified badge, rating count if ≥3 reviews.
- Empty filter result: *"No vendors match those filters. [Clear filters]"*

### 9.5 Service detail page

Layout: hero block left (vendor name, title, summary, package list), sticky sidebar right (inquiry form). On mobile, sidebar collapses to bottom-anchored CTA.

**Sidebar inquiry form copy:**

> **Send an inquiry**
> The vendor will reply by email, usually within {avg_response} hours.
>
> Your message *
> [textarea — placeholder: "Property address, scope, timeline."]
>
> Move-in or shoot date (optional)
> [date picker]
>
> [Send inquiry]
>
> Lead-gen only — payments handled off-platform.

### 9.6 Forum thread

- Thread header: title, OP byline, posted timestamp, vote count, reply count, flair badge.
- Vote UI: up arrow, count, down arrow. ARIA labels: `aria-label="Upvote"`, `aria-label="Downvote"`. Not "Like" — this is Reddit-shaped and the audience knows what voting is.
- Reply form copy: *"Reply"* button, textarea with no placeholder (label above).
- Empty thread (no replies): *"No replies yet. Be the first."*
- Locked thread: *"Replies closed by a moderator. [See policy]."*
- Removed reply: *"Removed by moderation. [Why]"* — never delete the slot; transparency matters.

---

## 10. Banned Phrases

| Phrase | Why banned |
|---|---|
| "We're excited to announce" | Performative enthusiasm. The product itself should be the news. |
| "At Yakima Web, we believe…" | Self-referential and slow. Get to the point. |
| "Our mission is to…" | Tells, doesn't show. |
| "Don't hesitate to reach out" | Officious. Use "Email us at hello@yakimaweb.com." |
| "Please feel free to…" | Empty politeness padding. |
| "Best-in-class" | Empty marketing. |
| "World-class" | Yakima is not the world. |
| "Cutting-edge" | Cliche. Describe the actual feature. |
| "Streamlined" | Empty. Show the steps; let the reader decide. |
| "Frictionless" | Lying. There is always friction. |
| "Empowering realtors" | Condescending. Realtors don't need empowerment from us. |
| "Thank you for your patience" | If we mean it, we apologize specifically and explain. |
| "Sorry for the inconvenience" | Lazy. Name the inconvenience. |
| "Stay tuned!" | Cut. Tell them what's next or don't mention it. |
| "Click here" | Inaccessible and uninformative. |
| "Read more" | Use a verb + noun describing the destination. |
| "Synergy" | No. |
| "Pivot" (figurative business sense) | No. |
| "Game-changer" | No. |
| "Move the needle" | No. |
| "Drive results" | No. |
| "Holistic approach" | No. |
| "Solutions provider" | No. |
| "Best-of-breed" | No. |
| "Touch base" | Email or call. |

---

## 11. Examples — Before / After

| Before | After |
|---|---|
| "We're really excited to announce that our team has been working hard to deliver this game-changing new feature!" | "We just shipped the description writer." |
| "In order to use our marketplace, you'll first need to leverage our verification system." | "To list a service, get your account verified." |
| "Please don't hesitate to reach out with any questions you may have." | "Questions? Email hello@yakimaweb.com." |
| "Click submit to register for an account." | "Sign up." (button label) |
| "Our cutting-edge AI solution will help you unlock the full potential of your listings." | "The description writer drafts listing copy from your photos and notes. You edit before publishing." |
| "We are truly thrilled to welcome you to our world-class platform." | "Welcome." |
| "Utilize the search functionality to find vendors that align with your needs." | "Search the marketplace." |
| "Our robust moderation system ensures a frictionless experience for all users." | "We moderate every post and comment. Decisions are logged. [Read the policy.]" |
| "At this point in time, we are unable to process your request." | "We can't process this right now. [Try again]." |
| "Take your real estate journey to the next level!" | "Post your listing. Find a photographer. Read what local agents are writing." |
| "We're here to help every step of the way." | "Email hello@yakimaweb.com if you get stuck." |
| "Our state-of-the-art platform leverages cutting-edge AI to deliver actionable insights." | Cut entirely. Describe the actual feature. |

---

## 12. Copyediting Checklist — Seven Sweeps

Adapted from the `copy-editing` skill. Run on every page before merge.

| # | Sweep | Question | Action |
|---|---|---|---|
| 1 | **Lead** | Does the first sentence carry the page? | If you cut everything else, would the first sentence still tell the reader what this is? If not, rewrite it. |
| 2 | **Tighten** | What words do no work? | Cut adverbs. Cut *really*, *very*, *truly*. Cut throat-clearing. Cut everything in section 4.2. |
| 3 | **Verbs** | Where is the action hiding? | Make passive voice active where natural. Front-load verbs. *"It was decided that…"* → *"We decided…"* |
| 4 | **Specificity** | Is anything generic that could be concrete? | Replace nouns with names. Replace ranges with numbers. Replace "users" with "realtors" or "buyers." |
| 5 | **Voice** | Does this sound like Yakima Web? | Read it aloud. If it could be in any other company's copy, rewrite. |
| 6 | **Microcopy** | Every label, button, error, helper, empty state checked? | Walk every interactive element. Apply sections 5–7. |
| 7 | **Accessibility** | Does it work without sight or sound? | Read with a screen reader. Check link text out of context. Check headings hierarchy. Check alt text. |

---

## 13. Copy Review Process

| Surface | Reviewer | Gate |
|---|---|---|
| Marketing pages (home, about, lead-magnets) | Engineering lead + content reviewer | PR review |
| Blog post body (realtor authors) | Author signs; mod pipeline + spot-check by mod team | Mod queue + post-publish audit |
| Yakima Web posts (org authored) | Engineering lead | PR review |
| Microcopy (buttons, errors, empty states) | Engineering lead | PR review with this guide referenced |
| Email templates | Engineering lead + ops review | PR review + send-test before deploy |
| Mod canned responses | Ops + mod lead | Quarterly review |
| Forum policy pages | Ops + mod lead | Quarterly review |
| Legal copy (Privacy, Terms) | Attorney + ops | Annual review per RUNBOOK.md |

Process for new copy:

1. Author drafts.
2. Run sections 4 (word list) + 10 (banned) + 12 (Seven Sweeps).
3. Open PR. Reference this guide in description.
4. Reviewer applies the same checklist.
5. Reviewer leaves specific section citations on suggested changes (e.g., *"§5.4 — error needs an action"*).
6. Author revises.
7. Merge once both sign off.

Disputes go to engineering lead. Default position: cut more. The shorter version usually wins.

---

## 14. Accountability

Every public-facing string in the platform is governed by this guide. If you find copy that violates it, open a PR with the fix and cite the section. Do not file an issue and wait — fix it.

The guide itself is a living document. Propose changes through PR. Major changes (new principles, voice shifts) require ADR-level discussion.

— *Yakima Real Estate Hub Engineering, 2026-05-03*
