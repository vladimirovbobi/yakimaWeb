# Fiverr UX Teardown

**Purpose**: Extract structural patterns from Fiverr's marketplace for adaptation into a Django + HTMX + Tailwind-based real estate services marketplace (10K MAU, lead-gen model, local services focus).

---

## Sources Used

- [Fiverr Help Center - Creating a Gig](https://help.fiverr.com/hc/en-us/articles/360010451397-Creating-a-Gig)
- [Fiverr Help - Gig Images Guidelines](https://help.fiverr.com/hc/en-us/articles/15863342952977-Guidelines-for-selecting-Gig-images)
- [Codica - Marketplace Design Best Practices](https://www.codica.com/blog/best-practices-for-online-marketplace-design/)
- [QubStudio - Marketplace UX Design](https://qubstudio.com/blog/marketplace-ui-ux-design-best-practices-and-features/)
- [Stan.Vision - Card Design Patterns](https://www.stan.vision/journal/ui-card-design-examples-best-practices-and-common-patterns)
- [Eleken - Card UI Examples](https://www.eleken.co/blog-posts/card-ui-examples-and-best-practices-for-product-owners)
- [HireInSouth - Fiverr Pricing 2026](https://www.hireinsouth.com/post/fiverr-pricing)
- [EduEarnHub - Fiverr Pricing Strategy](https://eduearnhub.com/fiverr-gig-pricing-strategy/)
- [ZenLance - Fiverr Pricing Guide](https://zenlance.net/how-to-price-your-fiverr-gigs-2/)
- [Fiverr Tutorials - Best Profile Guide](https://fiverrtutorials.com/best-fiverr-profile)
- [Rahul Gautam - Level 2 Badge Guide](https://rahulgautam.in/blog/how-i-got-fiverrs-choice-badge-and-became-a-level-2-seller/)
- [HireEcomExperts - Fiverr Gig Levels](https://hireecomexperts.com/fiverr-gig-levels-explained/)
- [NN/G - Filter Categories Best Practices](https://www.nngroup.com/articles/filter-categories-values/)
- [Storylane - How to Find Gigs on Fiverr](https://www.storylane.io/tutorials/how-to-find-gigs-on-fiverr)
- [Fishtank - Facets Filters Sorting Guide](https://www.getfishtank.com/insights/understanding-facets-filters-and-sorting-for-search-and-listing-pages)

---

## Gig Card (Search Results / Category Landing)

### Card Anatomy

A Fiverr gig card is a compact information density design that functions as a **product card** for freelance services. It contains:

1. **Hero Image** (top, 100% width): 1280 × 769px recommended (72 DPI), minimum 712 × 430px. Clean, simple, 10 words max if text overlay. Fiverr automatically crops to aspect ratio.
2. **Seller Avatar & Name** (small circle 24–32px, left-aligned below image)
3. **Gig Title** (2–3 lines, medium weight, 14–16px on mobile)
4. **Seller Level Badge** (e.g., "Level 2" or "Top Rated")
5. **Star Rating + Review Count** (e.g., "4.9 ★ (247)")
6. **Price-from Label** (prominent, bold, 16–18px)
7. **Optional: Service Tags/Badges** (small pills): "Fast delivery", "Pro"

### Hierarchy & Visual Weight

- **Image dominates** (60–70% of card height)
- **Price is second-most-visible** after image
- **Seller info is subordinate** — small, left-positioned
- **Rating is tertiary** — muted color, smaller font

Nielsen research: over 60% of customers more likely to purchase when card is well-designed. Real case study: stripping 6 competing elements to 3 boosted click-through 34%.

### Hover Behavior (Desktop)

- **Image**: Subtle scale or brightness shift
- **Overall card**: Light shadow or elevation change
- **CTA button**: Becomes more prominent
- **No modal/popup** — hover is light, maintains scanning speed

### Mobile vs Desktop

| Aspect | Mobile | Desktop |
|--------|--------|---------|
| **Grid layout** | Single column | 2–4 columns (4 common at 1280px+) |
| **Card shape** | Square or 1:1 aspect | Rectangular |
| **Image height** | ~180px | ~200–240px |
| **Seller info** | Inline below image | Inline below image |
| **Price visibility** | Below fold | Often visible |
| **Touch targets** | Full card (min 48px) | Cursor-driven |
| **Sticky CTA** | Sticky bottom button | Hover reveals |

---

## Gig Detail Page

### Hero Gallery

- **Primary image** (left side desktop; full width mobile): Large, high-res
- **Thumbnail carousel** (below/side): 3–5 small thumbnails
- **Zoom capability**: Click to expand (lightbox)
- **Mobile**: Full-width swipeable gallery
- **Desktop**: Side-by-side with thumbnails

### Title + Tagline

```
[Back] [Share] [Save]
LARGE TITLE (32–48px, bold)
"I will create a professional logo for your brand"

Seller Avatar | Level 2 | 4.9★ (247 reviews) | From $49
[Tagline, 16px, lighter]
"Fast turnaround. Unlimited revisions. Pro quality."
```

### Three-Tier Package Table

Horizontal scrollable (mobile) or 3-column grid (desktop):

| Field | Shows |
|-------|-------|
| **Package Name** | "Basic", "Standard", "Premium" |
| **Price** | "$49", "$99", "$199" |
| **Delivery Time** | "3 days", "1 day" |
| **Features/Scope** | Bullet points |
| **Revisions** | "1 revision", "Unlimited" |
| **Additional Perks** | "Source files", "Commercial rights" |
| **CTA Button** | "Select" or "Continue" |

**Price anchoring**: Premium 3–4x Basic; Standard the "rational middle ground."

### FAQ Block

- **Below packages**, collapsible accordion
- **10–15 FAQs typical**; sorted by frequency
- **Expandable sections**: Click to reveal
- **Optional search**: For large lists
- **Styling**: Small, clean, muted colors

### Reviews Block

**Location**: Below FAQ or dedicated tab

**Components**:
1. **Rating summary** (top): Star count + breakdown chart
2. **Sort options**: "Most recent", "Highest rating", "Lowest rating"
3. **Review cards**: Buyer avatar + name, stars, date, title, text (truncated), photos, seller response
4. **Pagination** or "Load more"
5. **Empty state**: "This seller hasn't received reviews yet."

### Seller Profile Sidebar

**Desktop**: Fixed/sticky right card. **Mobile**: Collapsible section or top card.

**Components**:
- **Profile photo** (large circle, 80–100px)
- **Seller name** (bold, 16–18px)
- **Level badge** (e.g., "Level 2", "Top Rated")
- **Response time** (e.g., "Responds within 2 hours")
- **Completion rate** (e.g., "98% on-time")
- **Languages** (e.g., "English, Spanish")
- **Member since** (e.g., "Joined 2 years ago")
- **Contact CTA** (primary button: "Contact Seller" or "Message Now")
- **Optional: Service availability** ("Active" indicator)

### About This Gig / Scope

- **Below reviews** or collapsible section
- **Seller-written description** (400–800 words)
- **Bullets or short paragraphs** explaining scope, process, timeline
- **Links to portfolio** or examples

### Compare Packages

The 3-column package table itself functions as comparison. **Recommendation for Yakima**: Inline comparison table or side-by-side diff modal.

---

## Search + Filter UX

### Top-Level Category Nav

Fiverr uses **mega menu** or **horizontal pill navigation**:
- Main categories as **link buttons** in sticky header
- Hover (or tap on mobile) reveals **subcategories**
- No deep nesting; 1–2 levels max

**For Yakima**: 6–8 top-level service categories (Virtual Tours, Photography, Home Staging, Inspection Reports, Marketing, Appraisals, Consulting).

### Sidebar Filters (Left, Desktop)

Standard marketplace facets:

| Facet | Values | Type |
|-------|--------|------|
| **Price range** | Slider $0–$2000 | Range slider |
| **Delivery time** | "1 day", "3 days", "7 days", "14+ days" | Multi-select checkboxes |
| **Seller level** | "New", "Level 1", "Level 2", "Top Rated", "Pro" | Multi-select |
| **Service type** | "One-time", "Subscription", "Hourly" | Multi-select |
| **Language** | Dropdown or searchable | Multi-select |
| **Verification** | "Verified", "Pro verified" | Toggles |
| **Additional features** | "Rush delivery", "Includes consultation" | Multi-select |

**Mobile**: Bottom-sheet modal or slide-in panel. Applied filters as removable pills above results.

### Sort Options

- "Best selling" (default)
- "Newest"
- "Top rated"
- "Most reviewed"
- "Price: Low to High" / "High to Low"

Typically a **dropdown** near the top.

### Result Density

- **Desktop (1280px+)**: 4 columns
- **Tablet (768–1024px)**: 2–3 columns
- **Mobile (<768px)**: 1 column (full width, minus padding)
- **Spacing**: 16–24px gap; 24–32px outer padding

### Pagination vs Infinite Scroll

Fiverr uses **infinite scroll**. **Recommendation**: Start with pagination (simpler for Django + HTMX); migrate to infinite scroll if scale warrants.

### Empty State

- **Clear messaging**: "No results match your filters"
- **Suggest adjustments**: "Try widening your price range or removing a filter"
- **Link back to all listings** or show popular categories

---

## Trust Signals

### Verified Badges

- **Fiverr's Choice**: Algorithm selects top performers (badge on card/profile)
- **Pro Verified**: Manual vetting; premium tier
- **Skill Badges**: Seller passed skill assessment (small icon, clickable for percentile)
- **Responsive/Reliable**: Auto-awarded based on metrics

### Level System

| Level | Requirements | Visual Treatment |
|-------|--------------|------------------|
| **New Seller** | Just started | No special badge |
| **Level 1** | 50+ reviews, 90%+ on-time | Small "Level 1" badge, blue/green |
| **Level 2** | 100+ reviews, 95%+ on-time, $2000+ earned | "Level 2" badge, gold/green; prominent |
| **Top Rated** | Highest tier; consistent excellence | "Top Rated" badge, gold/star; appears first |

**Badges appear**:
- On gig cards (right side of seller name)
- On seller profile (sidebar, prominent)
- In search filters (users can filter by level)
- In reviews section (context for reviewer)

### Response Time Stat

- **Displayed on profile** and gig detail
- **e.g., "Responds within 2 hours"** or **"99% response rate"**
- **Visual**: Icon (speech bubble) + text, small, muted color
- **Reinforces reliability**

### Completion Rate / On-Time Delivery

- **On profile**: "98% on-time delivery"
- **Visual**: Icon (checkmark/clock) + percentage, small
- **Critical signal**: Buyers fixate on this when scanning

### "Recommended" Tags

- Fiverr algorithm marks certain gigs "Recommended for you"
- Tag appears on card as small pill: "Recommended"
- **Visual**: Muted color (not primary), optional

### Pro Badge

- Premium seller tier
- Appears on card and profile
- Indicates pre-vetted, premium scope/delivery

---

## Order Flow (Pre-Checkout Patterns)

Note: Yakima marketplace is **lead-gen only**, not transactional. Adapt for inquiry capture.

### "Continue" → Packet Selection

1. **User lands on gig detail**
2. **Clicks "Select"** on a package
3. **Form/modal appears**:
   - Selected package (highlighted)
   - Delivery date (auto-calculated or user-selectable)
   - Quantity/scope inputs (if applicable)
   - Checkbox for add-ons (optional)
   - Total price (if transactional)

**For lead-gen**: Replace with **custom inquiry form** asking for property address, service type, timeline, budget range, contact details.

### Custom Request Flow

- **Before placing order**: Buyer **"Message seller"** or **"Request custom offer"**
- **Opens chat/form**: Buyer describes specific needs
- **Seller responds** with custom offer or clarifications
- **Buyer then selects a package** or accepts custom offer

**For lead-gen**: This is your **primary flow**. Buyer fills inquiry form → seller receives lead → seller responds with quote/availability. No payment.

### Pre-Purchase Q&A

- Some gigs have a **"Contact seller before ordering"** requirement
- Buyer fills a form: "Do you work with X software?" "Can you do Y by Z date?"
- Seller responds (directly on gig page or in chat)
- Buyer then has confidence to place order

**For lead-gen**: Essential. Make Q&A asynchronous (buyer asks, service provider responds via email/dashboard) and visible on inquiry.

---

## Mobile-Specific Patterns

### Sticky CTA

- **"View Details"** or **"Message Now"** button remains **fixed at bottom**
- **Min height**: 48–56px; full width minus padding (~90%)
- **Color**: Primary brand color; high contrast
- **Prevents accidental taps**: Plenty of padding

### Bottom-Sheet Filters

- **Triggered by "Filter" button** in header
- **Slides up from bottom**, covering ~60–80% viewport
- **Shows all filter facets** stacked vertically
- **"Apply" button** at bottom (sticky/fixed)
- **"Clear filters"** secondary action
- **Smooth animation**: Slide-in from bottom

### Image Gallery Interaction

- **Full-width swipeable** carousel on mobile
- **Left/right swipe or chevron buttons** to navigate
- **Tap to expand**: Open lightbox or full-screen
- **Pinch to zoom**: Native browser support
- **Thumbnail indicators** (small dots) showing position

---

## What Translates to Yakima Real Estate Marketplace

### 5 Specific UX Details to Bake In

1. **Trust signals for service providers**: Implement a **level/badge system** (New Provider, Verified, Pro, Top Rated). Show response time, job completion rate, review count prominently. For Yakima: "Verified real estate professional" with local credentials, license linked to public database.

2. **Three-tier service packages**: Use **scope-based tiers** (e.g., photographer: "Single property", "Multi-property bundle", "Premium full-day shoot"). Display as side-by-side cards. Use price anchoring: make mid-tier the obvious choice.

3. **Sticky "Inquiry" CTA on mobile**: On `/marketplace/services/[slug]`, keep "Send Inquiry" or "Request Quote" button fixed at bottom viewport. Tapping opens **inline inquiry form**.

4. **Bottom-sheet filter panel on mobile**: On `/marketplace` listing, show "Filter" button that triggers bottom-sheet modal with facets (delivery time, service type, price range, location/radius). Apply filters, dismiss, see results update with HTMX.

5. **Seller profile sidebar with credibility stack**: On detail page, right sidebar (desktop) or top card (mobile) showing service provider avatar, name, verification badge, response time, completion rate, languages, "Message" / "Send Inquiry" CTA. Make this second most prominent thing after service image.

### 3 Things to Drop (Fiverr-isms)

1. **Subscription gigs and recurring revenue model**: Fiverr allows subscriptions. Yakima is lead-gen (one-time inquiry, seller quotes, buyer decides). Skip subscription package tier logic.

2. **Fiverr's resolution center and transaction disputes**: You're not processing payments or handling refunds. Drop order status tracking, resolution workflows, dispute panels. Flow ends at lead hand-off.

3. **"Top Rated" as an automatic algorithmic badge**: Fiverr auto-awards this. For 10K MAU local marketplace, manually vet and badge "Recommended" providers (your curation, not algorithm alone). Or let ratings/reviews speak.

---

## Concrete Component Sketches

### `/marketplace` Listing Card (Tailwind)

```html
<div class="group relative overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition hover:shadow-md">
  <div class="relative h-48 w-full overflow-hidden bg-gray-100">
    <img 
      src="/media/services/photo-1.jpg" 
      alt="Property photography service"
      class="h-full w-full object-cover transition group-hover:scale-105"
    />
    <div class="absolute right-3 top-3 inline-flex items-center rounded-full bg-green-600 px-2 py-1 text-xs font-semibold text-white">
      Verified
    </div>
  </div>

  <div class="p-4">
    <div class="mb-3 flex items-center gap-2">
      <img 
        src="/media/avatars/seller-123.jpg" 
        alt="Sarah Chen"
        class="h-6 w-6 rounded-full"
      />
      <span class="text-sm font-medium text-gray-900">Sarah Chen</span>
      <span class="text-xs text-gray-500">Level 2</span>
    </div>

    <h3 class="mb-2 line-clamp-2 text-base font-semibold text-gray-900">
      Professional property photos & virtual tour
    </h3>

    <div class="mb-3 flex items-center gap-1">
      <span class="text-sm font-semibold text-gray-900">4.9</span>
      <span class="text-sm text-yellow-400">★★★★★</span>
      <span class="text-xs text-gray-500">(47)</span>
    </div>

    <div class="flex items-baseline justify-between">
      <div>
        <span class="text-xs text-gray-500">From</span>
        <span class="text-lg font-bold text-gray-900">$149</span>
      </div>
      <button class="rounded-md bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700">
        View Details
      </button>
    </div>
  </div>
</div>
```

---

## Summary: Fiverr Patterns → Yakima

| Fiverr Element | Yakima Adaptation | Priority |
|---|---|---|
| Gig card | Service card (image, provider, rating, "from" price) | High |
| 3-tier packages | 3 service packages (scope-based) | High |
| Trust badges | Verified, Top Rated, Local Expert badges | High |
| Seller sidebar | Provider profile card | High |
| Search filters | Filters (price, timeline, service type, level, location) | High |
| Reviews + breakdown | Reviews + rating breakdown | High |
| Sticky mobile CTA | Sticky "Send Inquiry" button | High |
| Bottom-sheet filters | Bottom-sheet filter panel | Medium |
| Custom requests | Inquiry form | High |
| Pagination | Pagination or HTMX load-more | Low |
| Category nav | Horizontal pill nav | Medium |

---

## Conclusion

Fiverr's UX is battle-tested for lead-gen marketplaces: strong visual hierarchy (image first), trust signals (badges + metrics), and streamlined inquiry flow. The 3-tier package system drives conversion through price anchoring. Adapt patterns liberally, but drop transactional complexity and focus on **lead capture, provider curation, and buyer confidence**. For a 10K MAU local marketplace, manual verification and top-provider curation outperforms algorithmic badging.
