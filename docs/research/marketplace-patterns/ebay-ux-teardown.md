# eBay UX Teardown

## Sources Used

- [eBay Playbook: Layout in Product](https://playbook.ebay.com/foundations/layout-in-product) — official responsive grid system
- [eBay Developers: Item Specifics Guide](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/item-specifics.html)
- [eBay Help: How to Use Search](https://www.ebay.com/help/buying/search-tips/use-search?id=4006)
- [eBay Feedback Score & Trust Signals](https://www.frooition.com/blog/ebay-feedback-examples-and-templates-for-sellers-2026-guide/)
- [eBay Item Specifics for SEO](https://www.3dsellers.com/blog/ebay-item-specifics)
- [eBay Advanced Search Filters](https://www.ebay.com/help/buying/search-tips/advanced-search?id=4049)
- eBay UX analysis from multiple seller education platforms

---

## Listing Card (Search Results)

### Anatomy

eBay search results display items in a dense grid format with the following components per card:

1. **Product Image** (primary, ~220px square for desktop)
2. **Title** (truncated at ~2 lines, 14–16px weight-500)
3. **Price** (prominent, bold, red or green depending on context; 16–18px)
4. **Shipping Info** (e.g., "Free shipping" or shipping cost; 12px gray)
5. **Seller Name + Feedback Star** (compact row; seller avatar optional)
6. **Item Condition** (e.g., "New", "Used - Like New"; 11px)
7. **Time Remaining** (for auctions; 11px; grayed if >1 week)
8. **Save/Watch Icon** (heart outline; top-right corner)

### Density at Breakpoints

eBay uses **8 responsive breakpoints** (320, 512, 768, 1024, 1280, 1440, 1680, 1920px):

- **Mobile (320–511px)**: 1 card per row, full bleed
- **Tablet (512–767px)**: 2 cards per row
- **Small Desktop (768–1023px)**: 3 cards per row
- **Desktop (1024–1279px)**: 4 cards per row
- **Large Desktop (1280px+)**: 5–6 cards per row (depending on sidebar width)

This density is **aggressive**—much tighter than modern "clean" marketplaces (Etsy, Shopify, Airbnb). It maximizes results-per-scroll, encouraging volume browsing.

### Hover State / Quick View

- **Desktop hover**: Card background lightens slightly; image opacity shifts; title underline appears
- **No dedicated "quick view" modal** (unlike Shopify or Etsy)—hover effect nudges toward click-through to detail page
- **Mobile**: No hover state; tap leads directly to detail page

### Compare Mode

- **Checkbox overlay** (top-left corner, appears on hover/focus)
- Buyers can select up to ~10 items and compare side-by-side
- Comparison shows: price, condition, shipping, seller, feedback
- **Not prominent** in the default view—secondary feature

---

## Listing Detail Page

### Image Gallery

- **Primary image**: Large (600–800px square, responsive)
- **Thumbnails**: 5–10 smaller images below or to the left (responsive grid)
- **Hover behavior**: Hovering a thumbnail swaps the primary image (no load delay)
- **Full-screen mode**: Click primary image to expand to lightbox with arrow navigation
- **Zoom on hover**: Optional pinch-zoom for mobile; desktop hover shows magnified crop
- **No video gallery** (historically; videos now embedded in description or as carousel)

### Title + Condition + Price Hierarchy

```
┌─────────────────────────────────────────┐
│ [Title in 20px bold, up to 80 chars]   │
│                                         │
│ Condition: NEW (or Used - Like New)    │
│                                         │
│ $149.99  [red/green depending on type] │
│ or $5.00 Starting bid + Shipping $12   │
│                                         │
│ Seller info row (feedback, location)   │
└─────────────────────────────────────────┘
```

- **Title**: Always at the top; wraps to 2–3 lines max
- **Condition badge**: Right-aligned, small caps, 11px
- **Price**: Largest, most prominent text after title (18–24px bold)
- **Seller row**: Compact; feedback score (e.g., "4,523 feedback") + % positive (e.g., "99.2%")

### "Buy It Now" vs "Place Bid" CTA Treatment

- **Buy It Now listings**:
  - Large orange button: "Buy It Now" (eBay brand orange, ~48px tall)
  - Price shown above button
  - Button sticky on scroll (mobile)

- **Auction listings**:
  - Red button: "Place Bid" (eBay red, ~48px tall)
  - Current bid shown; next bid increment displayed
  - Button text updates in real-time if auction is about to close

- **Buy It Now + Auction hybrid**:
  - Two side-by-side CTAs (orange "Buy It Now" + red "Place Bid")
  - Price duality (immediate buy price vs starting bid)

### Item Specifics Table

**The most critical component for your use case:**

Item Specifics are structured name-value pairs that buyers use to filter search results. On the detail page, they appear as a scrollable table:

```
┌─────────────────────┬──────────────────────┐
│ Brand               │ Sony                 │
├─────────────────────┼──────────────────────┤
│ Model               │ A7RIII               │
├─────────────────────┼──────────────────────┤
│ Type                │ Digital Camera       │
├─────────────────────┼──────────────────────┤
│ Megapixels          │ 42.4 MP              │
├─────────────────────┼──────────────────────┤
│ Storage Type        │ SD, Secure Digital   │
├─────────────────────┼──────────────────────┤
│ Focus Type          │ Autofocus            │
├─────────────────────┼──────────────────────┤
│ Color               │ Black                │
├─────────────────────┼──────────────────────┤
│ Lens Included?      │ No                   │
└─────────────────────┴──────────────────────┘
```

**Key patterns**:
- Left column (label): 40% width, bold 13px, right-aligned
- Right column (value): 60% width, regular 13px, left-aligned
- Row height: ~28px; padding: 8px vertical
- Background: White with alternating light gray (#f9f9f9) rows for readability
- Each row is a separate `<div>` or `<tr>` with no visible borders (light divider lines instead)
- **Scrollable horizontally on mobile** if values are long
- **Clickable**: Some values are links (e.g., clicking "Sony" filters all Sony cameras)

**Category-specific tiers** (required, required-soon, recommended, additional):
- eBay requires certain specifics to go live (e.g., Condition, Brand, Model for electronics)
- Missing required specifics → listing not visible in filtered search results
- Recommended specifics improve Cassini ranking (eBay's search algorithm)

### Description Block

- **HTML-embedded content** (sellers upload custom HTML)
- Typically: product narrative + bullet points + additional images + seller logo
- **Pros**: Maximum flexibility; sellers can create rich, branded experiences
- **Cons**: Dated HTML (tables, inline styles); security risks (frames, scripts); mobile rendering issues; slow load times
- Rendered below Item Specifics; collapsible/expandable on mobile

### Shipping Calculator

- **Integrated widget** (not separate page)
- Inputs: buyer location (zip code or country), shipping method (Standard, Priority, etc.)
- Outputs: estimated delivery date + shipping cost
- **Conditional display**: Some sellers hide shipping cost until buyer enters location (lead-gen signal)
- Tax included for eligible categories (US only)

### Returns Policy

- **Standardized section** (not customizable HTML)
- Displays: accepts returns (yes/no), window (30/60/90 days), condition (new/refurbished), shipping (paid/seller-paid)
- Color-coded: Green (30 days, seller-paid) = trust signal; Red (no returns) = risk signal
- **Impact on conversion**: Buyers heavily weight return policy; listings with generous returns rank higher

### Seller Info Card

Compact box, typically right-aligned or in a sidebar (responsive stack on mobile):

```
┌─────────────────────────────────┐
│ ⭐ Seller: TechStore123        │
│                                 │
│ Feedback: 4,523 (99.2% positive)│
│ Member since: January 2015      │
│ Location: Los Angeles, CA, USA  │
│                                 │
│ [Top Rated Seller] [eBay Auth]  │
│                                 │
│ [Contact Seller] [Ask Question] │
│ [View All Items] [More from ...] │
└─────────────────────────────────┘
```

- **Feedback score + percentage**: Clickable; opens seller review feed
- **Badges**: Top Rated Seller (gold), Authenticity Guarantee (luxury), eBay Money Back Guarantee
- **Member since**: Trust signal; older members = higher perceived reliability
- **Location**: Buyer preference (local pickup, shipping speed perception)
- **CTAs**: Contact Seller (email form), Ask Question (Q&A), View All Items (seller browse)

### Similar Items / Sponsored

- **"Similar Items"** section: Below description; 4–6 cards of algorithmically matched listings (often from competitors)
- **"Sponsored"** tag: Light label; minimal visual hierarchy (barely noticeable)
- Placement: After description, before reviews

### Watch + Add to List

- **Watch button**: Heart outline (top-right of title); turns solid on click
- **Add to custom list**: Dropdown (e.g., "Add to 'For Later'", "Add to 'Gifts'")
- Watched items trigger notifications if price drops or auction ends soon
- Wishlist syncs across devices

---

## Search + Filter UX

### Category Browse (Left Sidebar Tree)

- **Collapsible tree** (not flat list); major categories expand to subcategories
- Example: Electronics → Cameras & Photo → Digital Cameras → Camera Lenses
- **Breadcrumb navigation** at top (above search box): "Home > Electronics > Cameras"
- Mobile: Collapses to dropdown or modal
- **Visual hierarchy**: Bold parent, indented children; active category highlighted

### Filter Facets (Left Sidebar)

**Primary filters** (always visible):

- **Condition**: New, Used, Refurbished, For Parts or Not Working (checkboxes)
- **Price**: Slider or input range (e.g., "$10–$500")
- **Location**: "US Only", "Local Pickup Only", "Ships from US", "Ships from [country]"
- **Buying Format**: "Buy It Now", "Auction", "Accepts Offers"
- **Shipping**: "Free Shipping", "Local Pickup", "Expedited Shipping Available"

**Secondary filters** (category-dependent; expand/collapse):

- **Brand**: Checkboxes; sorted by frequency (most listings first)
- **Seller Type**: "Top Rated Sellers Only", "Authorized Sellers"
- **Returns**: "Accepts Returns", "Free Returns"
- **Item Specifics**: Dynamic based on category (e.g., for cameras: Megapixels, Brand, Type, Color)

**Filter behavior**:
- Changes apply instantly (no "Apply" button; AJAX updates results in real-time)
- Selected filters show with `X` to remove; count displayed (e.g., "Condition: New (1,234)")
- "Clear All" link resets filters
- **Result count** displayed in real-time below each filter option (e.g., "New (5,234)")

### Sort Options

Dropdown at top-right of results:

1. **Best Match** (default; uses Cassini ranking: relevance + feedback + price + shipping)
2. **Price: Low to High**
3. **Price: High to Low**
4. **Newly Listed** (freshness signal)
5. **Time: Ending Soonest** (for auctions)
6. **Distance: Nearest First** (if location filter applied)
7. **Authenticity Guarantee** (luxury categories only)

### Saved Searches + Alerts

- **Saved searches**: Users can save a filtered search and revisit later
- **Email alerts**: Checkbox to notify when new items match saved search (daily or weekly digest)
- Alerts include: new listings, price drops, auction activity
- **Mobile**: Accessible via account menu (not always visible in search UI)

### Result Density

- eBay is **noticeably dense** vs. competitors (Fiverr, Etsy, Shopify)
  - Fewer product images per card
  - Minimal whitespace
  - More cards per row
- **Trade-off**: High volume discovery (good for browsers) vs. decision friction (overwhelming)
- Fiverr/Etsy/Shopify use ~40% more vertical space per card; larger images; more whitespace

### Pagination

- **Traditional numeric pagination**: 1 2 3 4 5 ... 50 [Next >]
- Or **"Show More" button** on some result sets (infinite scroll on mobile)
- Results-per-page: 60 items (default); 120 available
- **No "Jump to page" input** (less common on modern platforms)

---

## Trust Signals

### Feedback Score (Number + Percentage)

- **Format**: "4,523 feedback" + "99.2% positive"
- **Displayed on**:
  - Search result card (seller row)
  - Listing detail page (seller card + title area)
  - Seller profile page
- **Visual treatment**: Subtle color coding (green for 99%+ positive; yellow for 95–99%; red for <95%)
- **Clickable**: Opens seller feedback feed (last 25 reviews visible; can scroll to older reviews)

### Top Rated Seller Badge

- **Gold or blue badge** with checkmark
- Requires: Min. 98% positive feedback + low defect rate + fast shipping + accept returns
- **Displayed**: Next to seller name on all listings; also in search results
- High conversion impact; eBay prioritizes Top Rated listings in search

### eBay Money Back Guarantee

- **Default trust mechanism** (all listings covered unless seller opts out)
- Guarantees: Item as described, timely delivery, resolved disputes
- **Display**: Fine print in policy section; rarely prominent

### Authenticity Guarantee (Luxury Categories)

- For high-value items (jewelry, handbags, watches, etc.)
- Item is inspected by eBay-certified authenticator before delivery
- **Displayed prominently** in title or badge area
- **Increases price** (sellers pay ~3–5% fee); strong conversion booster for luxury buyers

### Member Since Date

- "Member since January 2015" displayed in seller card
- Older members perceived as more reliable
- **No formal "years in business" badge**; implicit trust signal

### Location of Seller

- Country/state displayed (e.g., "Los Angeles, CA")
- Buyer preference varies: US-only buyers filter for domestic sellers; international buyers check shipping time/cost
- **Impact**: Domestic sellers rank higher in their home country

---

## Watchlist + Saved Searches

### How Items Are Added

1. **Watch button**: Heart outline (top-right of listing title)
   - Click → turns solid; notification settings dialog appears
2. **Add to List**: Dropdown (next to Watch button)
   - Creates custom list (e.g., "Photography Gear", "Gifts for Mom")
   - Multi-select: Add multiple items to list at once from search results

### Notifications Model

- **Real-time notifications** (email + app push):
  - Price drop (user-set threshold, e.g., "below $100")
  - Auction ending soon (24 hours, 1 hour)
  - Seller restock (if multiple variations)
  - New reviews posted (if user subscribed)
- **Notification frequency**: User-configurable (daily digest, instant, weekly summary)
- **Reminders**: 24h before auction ends; email includes updated price, competing bids

---

## What Translates to Yakima Real Estate (Lead-Gen Scope)

### 5 Patterns to Adopt

1. **Density + Grid Responsiveness**: 8 breakpoints like eBay ensures listings look sharp on mobile (your primary traffic). Aggressive cards-per-row maximizes discovery without scrolling fatigue.

2. **Item Specifics as Structured Key-Value Table**: Your service listings (e.g., "Real Estate Photography", "Junk Removal") need filterable attributes. eBay's table format is battle-tested for scanning and comparison.

3. **Trust Signals (Compact Format)**:
   - Service provider feedback score (e.g., "4.8★ · 127 reviews")
   - Response time (e.g., "Replies within 2 hours")
   - Years in business (e.g., "Operating since 2018")
   - License/certification badges (local real estate license, bonded junk removal, etc.)
   These appear inline with listing cards and in detail pages.

4. **Seller Info Card (Right Sidebar or Sticky)**:
   - Provider name + rating
   - Contact options: WhatsApp, Email, Phone (lead capture)
   - "View All Services" (cross-sell)
   - Service area (ZIP code or radius from location)
   - Badges (verified, top-rated, licensed)

5. **Filter Facets (Sidebar)**:
   - Service category (Photography, Cleaning, Junk Removal, etc.)
   - Service area (Yakima, nearby towns, radius slider)
   - Price range (consultation fee or hourly rate)
   - Provider rating (4★+, 5★ only, etc.)
   - Availability (same-day, weekends, etc.)

### 3 Patterns to Drop

1. **Auction Mechanics**: No bidding, time-left countdowns, or bid history. Not relevant for lead-gen marketplace; use fixed pricing or consultation quotes.

2. **Shipping/Delivery Complexity**: eBay's shipping calculator, carrier selection, international shipping options = noise for local services. Instead: simple service area (ZIP codes, map radius) + provider availability (calendar).

3. **Returns Policy Complexity**: eBay's 30/60/90-day return windows, seller-paid shipping, refund timelines don't apply. For real estate services, replace with: satisfaction guarantee (brief), dispute resolution (link to help), and maybe a "guarantee your quote or it's free" signal.

---

## Concrete Component Sketches

### Real Estate Photography Service Listing Card

```
┌────────────────────────────────────┐
│ [Portfolio image: kitchen photo] ♡ │
│                                    │
│ Professional Real Estate Photos    │
│ (title: 16px bold)                 │
│                                    │
│ $299–$599 per shoot                │
│ (price: 18px, bold)                │
│                                    │
│ Service Area: Yakima, WA & 25 mi   │
│ (condition equivalent; 12px gray)  │
│                                    │
│ John's Photography ⭐ 4.9/5 (64)   │
│ Responds in < 2 hours             │
│ (seller row: 12px)                 │
└────────────────────────────────────┘
```

**Item Specifics Table (Expanded Detail Page)**:

```
┌──────────────────────┬──────────────────────┐
│ Service Type         │ Real Estate Photos   │
├──────────────────────┼──────────────────────┤
│ Photos Included      │ 40–60 digital photos │
├──────────────────────┼──────────────────────┤
│ Video Walkthrough    │ Yes (1–3 min)        │
├──────────────────────┼──────────────────────┤
│ Drone Photos         │ Additional $150      │
├──────────────────────┼──────────────────────┤
│ Turnaround Time      │ 2–3 business days    │
├──────────────────────┼──────────────────────┤
│ Service Area         │ Yakima + 25 mi       │
├──────────────────────┼──────────────────────┤
│ Availability         │ Weekdays & Weekends  │
├──────────────────────┼──────────────────────┤
│ Equipment            │ Canon R5, DJI Avata2 │
└──────────────────────┴──────────────────────┘
```

### Junk Removal Service Listing Card

```
┌────────────────────────────────────┐
│ [Before/after cleanup photo]    ♡  │
│                                    │
│ Full House Junk & Debris Removal   │
│ (title: 16px bold)                 │
│                                    │
│ FREE quote (price: 18px, green)    │
│ ~$150–$800 typical range           │
│                                    │
│ Service: All of Yakima             │
│ (12px gray)                        │
│                                    │
│ GreenClean Removal ⭐ 4.7/5 (89)  │
│ Responds in < 4 hours             │
│ (seller row: 12px)                 │
└────────────────────────────────────┘
```

**Item Specifics Table**:

```
┌──────────────────────┬──────────────────────┐
│ Service Type         │ Junk Removal         │
├──────────────────────┼──────────────────────┤
│ What We Take         │ Furniture, appliances│
│                      │ electronics, debris  │
├──────────────────────┼──────────────────────┤
│ Recycling Policy     │ 75% diverted to      │
│                      │ reuse/recycle        │
├──────────────────────┼──────────────────────┤
│ Pricing              │ Free estimate;       │
│                      │ by volume/weight     │
├──────────────────────┼──────────────────────┤
│ Turnaround           │ Same-day (24h notice)│
├──────────────────────┼──────────────────────┤
│ Service Area         │ All of Yakima        │
├──────────────────────┼──────────────────────┤
│ Equipment            │ 2 trucks, 2-person   │
│                      │ crew                 │
├──────────────────────┼──────────────────────┤
│ Insured/Bonded       │ Yes, $1M coverage    │
└──────────────────────┴──────────────────────┘
```

### Django + HTMX + Tailwind Implementation Notes

**Listing Card Component** (`components/listing_card.html`):

```html
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
  <!-- Card container: matches eBay density at 8 breakpoints via Tailwind -->
  <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow group">
    <!-- Image container -->
    <div class="relative h-48 bg-gray-200 overflow-hidden">
      <img src="{{ service.image_url }}" alt="{{ service.title }}" 
           class="w-full h-full object-cover group-hover:opacity-90">
      <!-- Watch/favorite button (top-right) -->
      <button hx-post="/api/watchlist/add" hx-vals='{"service_id": "{{ service.id }}"}' 
              class="absolute top-2 right-2 p-2 bg-white rounded-full shadow hover:bg-gray-100">
        <svg class="w-5 h-5 text-gray-400 group-hover:text-red-500"><!-- heart icon --></svg>
      </button>
    </div>
    
    <!-- Content container -->
    <div class="p-3 space-y-2">
      <h3 class="font-bold text-sm line-clamp-2">{{ service.title }}</h3>
      <p class="text-red-600 font-bold text-lg">{{ service.price_display }}</p>
      <p class="text-gray-600 text-xs">{{ service.location_display }}</p>
      
      <!-- Seller row: feedback + name -->
      <div class="flex items-center gap-2 text-xs">
        <span class="font-semibold">{{ service.provider.name }}</span>
        <span class="text-yellow-500">★{{ service.provider.rating }}</span>
        <span class="text-gray-500">({{ service.provider.review_count }})</span>
      </div>
      
      <!-- CTA -->
      <a href="{{ service.detail_url }}" class="block w-full text-center bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 text-sm">
        View Details
      </a>
    </div>
  </div>
</div>
```

**Item Specifics Table** (`components/item_specifics.html`):

```html
<div class="mt-6 bg-white rounded-lg p-4">
  <h2 class="font-bold text-lg mb-4">Service Details</h2>
  <div class="space-y-0 divide-y divide-gray-200">
    {% for key, value in service.specifics.items %}
    <div class="py-3 grid grid-cols-2 gap-4">
      <div class="text-sm font-semibold text-gray-700 text-right">{{ key }}</div>
      <div class="text-sm text-gray-900">{{ value }}</div>
    </div>
    {% endfor %}
  </div>
</div>
```

**Sidebar Filters** (`components/filter_sidebar.html`):

```html
<aside class="w-full md:w-64 flex-shrink-0 space-y-4">
  <!-- Category filter -->
  <div class="bg-white rounded-lg p-4">
    <h3 class="font-bold text-sm mb-2">Service Category</h3>
    <div class="space-y-2">
      {% for category in categories %}
      <label class="flex items-center text-sm">
        <input type="checkbox" name="category" value="{{ category.id }}" 
               hx-get="/marketplace/listings" hx-target="#results" 
               class="mr-2">
        {{ category.name }} <span class="ml-auto text-gray-500">({{ category.count }})</span>
      </label>
      {% endfor %}
    </div>
  </div>
  
  <!-- Service area filter (replace eBay location) -->
  <div class="bg-white rounded-lg p-4">
    <h3 class="font-bold text-sm mb-2">Service Area</h3>
    <input type="text" placeholder="Zip code or city" 
           hx-get="/marketplace/listings" hx-trigger="change" hx-target="#results"
           class="w-full px-3 py-2 border rounded text-sm">
  </div>
  
  <!-- Price range -->
  <div class="bg-white rounded-lg p-4">
    <h3 class="font-bold text-sm mb-2">Price Range</h3>
    <input type="range" min="0" max="2000" name="price_max" 
           hx-get="/marketplace/listings" hx-target="#results"
           class="w-full">
  </div>
  
  <!-- Rating filter -->
  <div class="bg-white rounded-lg p-4">
    <h3 class="font-bold text-sm mb-2">Rating</h3>
    <div class="space-y-2">
      {% for rating_threshold in [5, 4.5, 4, 3] %}
      <label class="flex items-center text-sm">
        <input type="radio" name="min_rating" value="{{ rating_threshold }}" 
               hx-get="/marketplace/listings" hx-target="#results"
               class="mr-2">
        {{ rating_threshold }}★ & up
      </label>
      {% endfor %}
    </div>
  </div>
</aside>
```

**Seller Info Card** (sticky, right sidebar on detail page):

```html
<div class="sticky top-4 bg-white rounded-lg shadow p-4 space-y-3">
  <!-- Provider header -->
  <div>
    <p class="font-bold text-lg">{{ provider.name }}</p>
    <div class="flex items-center gap-1 text-sm">
      <span class="text-yellow-500">★{{ provider.rating }}</span>
      <span class="text-gray-600">({{ provider.review_count }} reviews)</span>
    </div>
    <p class="text-xs text-gray-600 mt-1">Operating since {{ provider.established_year }}</p>
  </div>
  
  <!-- Response time + location -->
  <div class="text-sm text-gray-700 border-t pt-3">
    <p>Response time: < {{ provider.avg_response_minutes }} minutes</p>
    <p>Service area: {{ provider.service_area }}</p>
  </div>
  
  <!-- Trust badges -->
  <div class="flex gap-2 border-t pt-3">
    {% if provider.verified %}<span class="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">Verified</span>{% endif %}
    {% if provider.licensed %}<span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">Licensed</span>{% endif %}
  </div>
  
  <!-- CTAs -->
  <div class="space-y-2 pt-3 border-t">
    <button hx-get="/services/{{ service.id }}/request-quote" hx-target="#quoteModal" 
            class="w-full bg-orange-600 text-white py-2 rounded font-semibold hover:bg-orange-700">
      Get Quote
    </button>
    <button hx-get="/contact/{{ provider.id }}" hx-target="#contactModal"
            class="w-full border border-gray-300 text-gray-700 py-2 rounded font-semibold hover:bg-gray-50">
      Contact Provider
    </button>
  </div>
</div>
```

---

## Anti-Patterns to Avoid

### 1. **Cluttered Description HTML**

eBay allows sellers to embed raw HTML in descriptions, leading to:
- Nested tables, inline styles, fonts that don't scale
- Security risks (iframes, external scripts)
- Mobile rendering disasters (horizontal scrolling, overlapping text)

**For Yakima marketplace**: Enforce a **structured description template** (Django form) instead of free HTML. Offer pre-built sections: "What's Included", "Turnaround Time", "Guarantees". Render server-side as clean HTML/Tailwind.

### 2. **Feedback as Single Number**

eBay displays "4,523 feedback" as a number, but this conflates volume with quality. A seller with 10,000 neutral feedbacks looks as credible as one with 4,523 positive.

**For your platform**: Use a **5-star rating + review count** (e.g., "4.8★ · 127 reviews"), weighted by recency. Also surface "% responded to negative reviews" as a trust signal.

### 3. **Dense, Dated Pagination**

eBay's numeric pagination (1 2 3 4 ... 50 [Next]) works, but newer UX patterns (infinite scroll, load-more button) feel less jarring.

**For Yakima**: Use **"Load More" button** over infinite scroll (better for lead-gen CTAs—force a pause, show provider info). Or stick with pagination but make it sticky at bottom so users don't lose context.

### 4. **Time-Left Countdown (Auction Mechanic)**

eBay displays "5 days 12 hours" for auctions, creating urgency and FOMO. For lead-gen, this is manipulative and unnecessary.

**For your platform**: Don't use artificial scarcity. Instead, use **soft signals**: "Popular service" (if many bookings) or "Only 2 slots available this week" (if truly limited).

### 5. **Shipping Complexity**

eBay's shipping calculator, carrier selection, and international routing are necessary for physical goods but unnecessary overhead for local services.

**For your platform**: Keep it simple: "Service Area: Yakima, WA & 25 mi" (one-liner). For consultation lead-gen, "Virtual consultation available" is enough.

### 6. **Lack of Mobile-First Density**

eBay cards shrink on mobile but still display a lot of info (title, price, seller, feedback). On narrow screens, this becomes unreadable.

**For your platform**: Be more aggressive about hiding secondary info on mobile. Show: image, title, price, provider name, rating. Hide specifics (move to detail page). Use Tailwind's `hidden md:block` liberally.

### 7. **Watchlist as Secondary Feature**

eBay buries the watch button in the top-right corner, and notifications are opt-in. Lead-gen marketplaces should make follow-up easier.

**For your platform**: Promote "Save to Wishlist" more prominently. Send a **default** email when a provider becomes available (opt-out, not opt-in). Offer SMS notifications as well.

---

## Summary: Density vs. Trust vs. Conversion

eBay balances **discovery (dense cards)**, **trust (feedback + badges)**, and **conversion (large CTA buttons)**. For your Yakima marketplace:

1. **Adopt eBay's grid density** (responsive breakpoints, cards per row) to maximize results-per-scroll without overwhelming.
2. **Reframe item specifics** as service attributes (photos included, turnaround time, equipment, insurance). Use the table layout; it's proven to aid comparison.
3. **Lean on trust signals** (rating, response time, years in business, badges) more than eBay does. Real estate buyers are risk-averse; make trust visible.
4. **Simplify CTAs**. Replace "Buy It Now" + "Place Bid" complexity with single "Get Quote" button (lead-gen).
5. **Drop auction mechanics** and shipping complexity. Keep the interface tight: browse, filter, compare, contact.
6. **Use HTMX for form filters** (sidebar checkboxes, price range slider) to update results in-place without page reload. This feels snappier than eBay's traditional pagination.

The teardown shows that eBay prioritizes **volume discovery** over **careful browsing**. For real estate services in a small market like Yakima, you may want the opposite: **high-quality provider cards** with **prominent trust signals** and **easy lead capture**. Use eBay's structure as a foundation, but bias toward conversion over browse depth.
