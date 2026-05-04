"""Extended demo seed: more org posts, more realtor posts, more threads, comments, replies.

Idempotent — safe to re-run. Designed to ride on top of `seed_demo` to give every
public surface a generous spread of placeholder content. Sprint 1 deliverable.
"""
from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import LicenseType, RealtorProfile, VerificationStatus
from apps.content.models import Comment, Post, PostStatus, PostType
from apps.forum.models import Flair, ForumReply, ForumThread

User = get_user_model()

EXTRA_REALTORS = [
    ("eva-mendez@yakimaweb.local",   "Eva Mendez",       "Selah & Naches Realty",          "WA-EM-44021"),
    ("marcus-tate@yakimaweb.local",  "Marcus Tate",      "Yakima Valley Brokers",          "WA-MT-22118"),
    ("priya-shah@yakimaweb.local",   "Priya Shah",       "Northwest Heritage Realty",      "WA-PS-31077"),
    ("ron-bauer@yakimaweb.local",    "Ron Bauer",        "Lower Valley Land Co.",          "WA-RB-19883"),
    ("clara-jensen@yakimaweb.local", "Clara Jensen",     "Cascade Vista Realty",           "WA-CJ-50221"),
]

EXTRA_ORG_POSTS = [
    ("Yakima County school catchments — what changed for the 2026 school year",
     "Catchment lines were redrawn around three elementary feeders this summer. Here is what shifted, who is affected, and how it impacts comp pricing block-by-block.",
     "Three elementary catchments in Yakima County saw boundary adjustments this summer. The changes are small in geography but meaningful in pricing — buyers with school-age kids price catchment access into their offers, and a quiet boundary shift can move comps 1.5-3% in a tight block.\n\n"
     "## What changed\n\n"
     "- The eastern boundary of the Roosevelt feeder moved one block west.\n"
     "- The McKinley/Garfield split now runs along a slightly different arterial.\n"
     "- Selah's Lince Elementary picked up four blocks from the previous boundary.\n\n"
     "## What this means for pricing\n\n"
     "If you are listing in any of these zones, pull the new map before you set price. Buyers with kids are using the new boundaries already. Comps from twelve months ago may have priced in catchment access that no longer applies.\n\n"
     "## Where to verify\n\n"
     "The county GIS portal has the updated layer. Most listing platforms have not refreshed yet, so do not trust their school overlay until at least October.\n"),

    ("Why title insurance matters more in 2026 than it did five years ago",
     "Wire fraud cases tripled. Forgery is up. Tax-lien complications are surfacing in older Yakima parcels. Title insurance is doing more work than it used to, and buyers should understand what they are paying for.",
     "Title insurance feels like one of those line items you grumble about at closing. In 2026 it is doing more work than it used to.\n\n"
     "## What we are seeing locally\n\n"
     "Wire fraud against home buyers is up sharply across the Pacific Northwest, and Yakima is not exempt. We are also seeing more title disputes on older parcels — particularly homes that traded between family members in the 1990s without clean conveyance documentation, and properties with old tax-lien complications that nobody resolved.\n\n"
     "## What your policy actually covers\n\n"
     "Owner's title insurance covers losses from defects in title that existed before you bought, and were not surfaced during the title search. That includes forgery, unrecorded liens, fraudulent claims of ownership, and survey errors. It does not cover anything that happens after your closing.\n\n"
     "## Why we recommend the enhanced policy on every transaction\n\n"
     "The standard policy is fine for new construction. For anything older than 1990, the enhanced policy adds coverage for post-policy forgery, mechanic's liens, and adverse possession claims. The price difference is small. Skip it once and the savings disappear the first time you face a problem.\n"),

    ("How comps actually work — a primer for first-time sellers",
     "Five reasons your neighbor's sale price is not your sale price, and why that is good news.",
     "Every first-time seller asks the same question: my neighbor sold for $X, why isn't my house worth that? It is a fair question. The answer is more nuanced than 'because.'\n\n"
     "## Five things that make 'comparable' actually comparable\n\n"
     "1. Square footage within 10%.\n"
     "2. Same age bracket — pre-1950 to pre-1950, post-1990 to post-1990.\n"
     "3. Same condition tier — both renovated, or both original.\n"
     "4. Same lot characteristics — corner lot, view, frontage.\n"
     "5. Closed within the last 90 days.\n\n"
     "## Why your neighbor's sale might not count\n\n"
     "If your neighbor's house is 200 sqft larger, sold to a family member, or sold during a different rate environment six months ago, it is not actually a comp for your home. It is a data point — useful, but not pricing-definitive.\n\n"
     "## What the appraiser will do\n\n"
     "Take three to five comps from the same neighborhood. Adjust each one for differences (a finished basement, an extra bath, a smaller lot). Average the adjusted values. The result is the appraised value. The buyer's lender uses this number, not the sale price you negotiated, to underwrite the loan.\n"),

    ("The Yakima Valley orchard market — a niche worth understanding",
     "Cherry, apple, pear, hops. If you are listing or buying ag land, the dynamics are different in ways that surprise out-of-area buyers.",
     "The Yakima Valley produces a meaningful share of the world's cherries, apples, pears, and hops. If a buyer or seller you work with is touching ag land, the rules of the road are different from residential.\n\n"
     "## Water rights are everything\n\n"
     "An orchard parcel without senior water rights is a different asset from one with them. When you list ag land, lead with the water-rights summary. When you represent a buyer, ask for the water-rights documentation up front and have it reviewed by an ag attorney.\n\n"
     "## Tree age affects valuation more than acreage\n\n"
     "A 20-acre orchard with eight-year-old high-density apple trees is worth substantially more than a 30-acre orchard with thirty-year-old standards on the same soil. Buyers price the future revenue, not the lot lines.\n\n"
     "## The financing path is narrow\n\n"
     "Most residential lenders do not write ag loans. AgWest Farm Credit, Yakima Federal, and a few regional credit unions are the local options. The pre-approval process is longer and the documentation heavier. If you are working a deal, get the buyer in front of an ag lender weeks before you make an offer.\n"),

    ("ADUs in Yakima — what the city actually allows in 2026",
     "Detached versus attached, parking minimums, owner-occupancy, short-term rental restrictions. The current rules in plain English.",
     "ADU rules in the city of Yakima have been a moving target. As of 2026 the rules have settled enough to write down.\n\n"
     "## What you can build\n\n"
     "- Attached or detached ADU on most residential parcels.\n"
     "- Up to 1,000 sqft for detached, smaller cap for attached.\n"
     "- One off-street parking space required (waivable in some downtown overlays).\n"
     "- One ADU per lot.\n\n"
     "## Owner-occupancy and rental rules\n\n"
     "The city no longer requires owner-occupancy of either unit. You can rent both. Short-term rentals (under 30 days) are restricted in most residential zones — verify with planning before you list.\n\n"
     "## What this means for valuation\n\n"
     "A finished ADU adds real value. The market is pricing detached ADUs at roughly 60-70% of the price-per-square-foot of the main house. Attached ADUs trade at a small discount to that. If you are advising a client on whether to build, the numbers usually pencil only if they have flat lot, existing utilities, and a contractor relationship.\n"),

    ("Reading a Form 17 like a pro — the section sellers think doesn't matter",
     "Section 5 is about water. Section 6 is about heating systems. Section 7 is the one most buyers skip and most issues hide in.",
     "Washington's Form 17 seller disclosure has eight sections. Most buyers read the first four carefully and skim the rest. The hidden risk almost always lives in section 7.\n\n"
     "## What section 7 covers\n\n"
     "Section 7 is the catch-all 'general' disclosure. Lawsuits affecting the property. Unrecorded easements. Boundary disputes. Encroachments by neighboring structures. Special assessments. HOA conflicts. Anything the seller knows that does not fit cleanly into sections 1-6.\n\n"
     "## What to actually look for\n\n"
     "- Any answer of 'don't know' on a section 7 question — push for a written clarification.\n"
     "- Any reference to a prior insurance claim — request the CLUE report.\n"
     "- Any mention of a survey or boundary dispute — get the recorded survey before closing.\n"
     "- Any HOA or CC&R reference — request and read the full CC&Rs and the last twelve months of HOA minutes.\n\n"
     "## What we tell our buyers\n\n"
     "If your seller wrote 'don't know' three or more times in section 7, that is not laziness. It is risk. Either get answers or get out.\n"),

    ("How to actually use AI in your real estate practice without losing your license",
     "Description writing, image enhancement, lead intake. The current line between 'allowed' and 'unauthorized practice'.",
     "The Washington DOL's guidance on AI use in real estate is short. The actual lines you can and cannot cross are longer.\n\n"
     "## What is fine\n\n"
     "- AI-assisted property description writing, with your final review.\n"
     "- AI-enhanced photos that do not misrepresent material features.\n"
     "- AI-driven lead intake forms that route to a licensed human.\n"
     "- AI-assisted comp analysis where you, the licensed agent, sign the final price recommendation.\n\n"
     "## What crosses the line\n\n"
     "- AI-generated images that add features that don't exist (a fireplace, a deck, a finished basement) without prominent disclosure.\n"
     "- AI agents that quote price recommendations or negotiate terms without licensed human review.\n"
     "- AI systems that hold themselves out as licensed agents.\n\n"
     "## What our platform does\n\n"
     "Every AI tool on Yakima Web runs through a moderation pipeline before output reaches you. The descriptions and images come back tagged with a disclosure footer. You sign off, you publish. Your license, your responsibility, our guardrails.\n"),

    ("The 30-second test — how buyers actually decide on your listing",
     "Cover photo. Headline. First three lines of description. If those three things don't earn the click, the rest of your work doesn't get seen.",
     "Buyers spend a median of 30 seconds on a listing card before they decide whether to click in or scroll past. That window is shorter than most agents realize.\n\n"
     "## What buyers actually look at\n\n"
     "1. The cover photo. If it is dark, off-center, or has a car in the driveway, the click rate drops.\n"
     "2. The headline price. Round numbers signal motivation. Odd numbers signal precision.\n"
     "3. The first three lines of the description. If those lines are template marketing copy, the listing reads as average.\n\n"
     "## What we do\n\n"
     "Cover photo: highest-quality exterior shot, taken at golden hour, shot wide enough to show the lot. Headline: clean, accurate, no exclamation points. First three lines: lead with what is actually special about this house.\n\n"
     "## A quick exercise\n\n"
     "Write your description. Now delete the first sentence. The second sentence is almost certainly stronger as your opener. Repeat until the first sentence is the strongest.\n"),
]

EXTRA_REALTOR_POSTS = [
    ("Eva Mendez", "Naches: under-the-radar pocket worth knowing",
     "Why we keep recommending Naches to first-time buyers priced out of central Yakima.",
     "Naches sits about fifteen minutes north of Yakima and trades at meaningfully lower price-per-square-foot. The schools are well-rated, the river access is real, and the inventory turnover is slow enough that buyers who learn the streets get genuine buying power.\n\n"
     "If you are priced out of West Valley but want comparable lifestyle, Naches is worth a Saturday morning drive. Walk Naches Avenue. Drive the river loop. Talk to the neighbors at the coffee shop on the corner. The vibe sells the buyer; the data closes the deal.\n"),

    ("Eva Mendez", "Why I always recommend a sewer scope on Yakima homes pre-1980",
     "Three hundred dollars. One hour. Saves my buyers from a fifteen-thousand-dollar surprise on average.",
     "Most general inspections do not include sewer scopes. They are an upcharge. I recommend them on every Yakima home built before 1980, and I have never regretted it.\n\n"
     "Pre-1980 homes in central Yakima often have clay or Orangeburg sewer laterals. Both are at or past their service life. A scope catches collapses, root intrusion, and bellies before you close. The cheapest negotiation tool you have when something is wrong with the line is the scope report you produced before mutual acceptance.\n"),

    ("Marcus Tate", "Three things to ask before you co-sign a mortgage",
     "I have seen this go wrong more times than I can count. Read this before you say yes.",
     "Co-signing a mortgage means you are equally on the hook. Not 'a backup,' not 'just my name on the paper.' Equally. If the primary borrower stops paying, the lender comes for you.\n\n"
     "Three questions. First: what is the primary borrower's actual debt-to-income, including this loan? Second: what is your fallback plan if you have to take over the payments for six months? Third: what does this co-sign do to your own ability to qualify for credit in the next five years? If you cannot answer all three with confidence, do not sign.\n"),

    ("Marcus Tate", "FSBO in Yakima — when it works, when it doesn't",
     "Most for-sale-by-owner transactions leave money on the table. A few don't. Here is the difference.",
     "I represent buyers and sellers, so I have sat across the table from a lot of FSBO sellers. Some get it right. Most leave money on the table.\n\n"
     "FSBO works when the seller is patient, has a realistic price, knows their forms, and has a transactional attorney pre-engaged. FSBO does not work when the seller refuses to professionally photograph, prices off Zestimate, and tries to negotiate without understanding inspection-period dynamics. If you are going to FSBO, hire the photographer, hire the attorney, price into the comp band, and budget the time for showings.\n"),

    ("Priya Shah", "Buying in West Valley — what changed in the last 18 months",
     "Inventory shifted, the comp band tightened, and the buyer pool got pickier. Here is the read.",
     "West Valley comps shifted in 2025. Median sale prices held within a tight band, but days on market lengthened and the buyer pool got more selective.\n\n"
     "If you are buying in West Valley right now, you have more leverage than buyers had eighteen months ago. The 'every offer over ask' market is over. Sellers are accepting inspection contingencies again. Appraisal-protected offers are winning over straight-cash offers when the cash buyer is grinding on price.\n"),

    ("Priya Shah", "How to read a CMA — a buyer's perspective",
     "Your agent's CMA is a tool, not a verdict. Here is what to look for and what to push back on.",
     "When your agent hands you a CMA, treat it like a draft. The most useful CMAs include both the comps that support the listing price and the comps that don't. If your CMA only includes the supporting comps, ask for the others.\n\n"
     "Three pushbacks I make as a buyer's agent. Are the comps within 90 days? Are they within the same school catchment? Are they the same condition tier? If any answer is 'no,' the CMA is not telling the right story and the price recommendation needs to be adjusted.\n"),

    ("Ron Bauer", "Lower Valley land deals — what I look for",
     "Five things that turn a beautiful piece of acreage into a deal worth doing — or worth walking away from.",
     "I work the Lower Valley and have for fifteen years. Most acreage deals look beautiful on the drive-up and complicated by closing.\n\n"
     "Five things I check before I let a buyer fall in love. Water rights and well status. Septic capacity and primary and reserve drainfield siting. Road access and easement clarity. Power proximity. Zoning and conditional use overlays. If any of these are unresolved, you are buying a project, not a property.\n"),

    ("Ron Bauer", "Why I stopped recommending 'starter homes'",
     "The math doesn't work like it used to. Most of my buyers should buy what they actually want — and stretch.",
     "The starter home thesis was: buy a small house, build equity, trade up. The math worked when rates were 3% and home prices were rising 8% per year. The math is different now.\n\n"
     "If you are going to live in a house for less than five years in this rate environment, you almost certainly come out ahead by renting and investing the difference. If you are going to live in a house for ten years, buy what you actually want — buy enough house to grow into rather than out of. The transaction costs of a trade-up are real, and you absorb them again every time you move.\n"),

    ("Clara Jensen", "How to interview a buyer's agent",
     "Five questions that separate the agents who will work for you from the ones who will work for the easiest commission.",
     "Most buyers do not interview their agent. They sign with the first one they meet at an open house. The result is a transaction without a real advocate.\n\n"
     "Ask: how many transactions did you close last year, and what percentage were buyer-side? What is your protocol when an inspection finds a serious issue? When was the last time you walked away from a deal on behalf of a buyer? What is your communication cadence — daily, weekly, as-needed? Who else on your team will I be working with?\n"),

    ("Clara Jensen", "Why I push every buyer to walk a property twice",
     "First walkthrough is for the heart. Second walkthrough is for the head. Both matter.",
     "When a buyer falls for a house on the first walkthrough, the first walkthrough is doing exactly what it should — confirming the emotional fit. The second walkthrough is for the head.\n\n"
     "On the second visit, I make my buyers do specific things. Stand in each room with the listing agent absent if possible. Run every faucet for thirty seconds. Open every interior door. Stand in the basement and listen. Stand in the attic if accessible. The second walkthrough catches the things the first one missed because the heart was loud.\n"),

    ("Demo Realtor", "Twilight photography — the math on whether it's worth it",
     "An extra $150 to $300, a single hero shot, and the data on whether it actually moves listings.",
     "Twilight photography costs $150-300 on top of standard real estate photography. The output is one or two hero shots that lead the listing.\n\n"
     "Our internal data: listings with twilight photography on the cover image had 18% higher click-through rates and 11% lower median days on market in the last 200 transactions we tracked. The data is not perfectly clean — twilight photography correlates with higher overall photo quality — but the directional signal is consistent.\n"),

    ("Demo Realtor", "When a price reduction is the right move — and when it isn't",
     "If your showings are strong and your offers are zero, your price is the problem. If your showings are weak, your photos and description are the problem.",
     "Two failure modes get conflated. Strong showings, zero offers — the price is at or just above the band buyers are willing to pay. Weak showings, no offers — buyers are not even clicking in.\n\n"
     "The first one needs a price reduction. The second one needs a photography refresh, a description rewrite, and a cover-image change. Reducing price on a listing with weak photo flow does not fix the listing; it just makes you sad.\n"),

    ("Demo Realtor", "The case for hiring a professional stager",
     "A few hundred dollars worth of furniture rental returns multiples in faster sales and higher offers. Here is when it makes sense.",
     "Staging is not for every listing. Vacant homes benefit. Original-condition homes in newer neighborhoods benefit. Homes priced near the top of their comp band benefit. Lived-in homes that are already well-furnished often do not.\n\n"
     "The best stagers in the Lower Valley charge $1,500-3,500 for a full residence stage. The data on offer premiums and days-on-market is consistent enough that we recommend it on every vacant listing over $400K and most listings over $600K regardless of occupancy.\n"),

    ("Demo Realtor", "Why I always pull tax history before listing",
     "Three years of tax history tells me whether the assessed value matches the market reality and where the next reassessment will land.",
     "Before I write a CMA, I pull three years of property tax history from the county portal. The trajectory of the assessed value tells me where the county thinks the property sits, and a divergence from market reality is information I can use.\n\n"
     "If the assessed value is well below market, I prep the seller for a reassessment shock at the next cycle. If it is at or above market, I check whether the seller has been paying more than they should have been — sometimes there is a refund opportunity.\n"),

    ("Demo Realtor", "What 'as-is' actually means in a Washington contract",
     "It does not mean the buyer waives inspection. It does not mean the seller is off the hook for disclosure. It means something specific.",
     "'As-is' in Washington real estate contracts is a phrase with a narrower meaning than people assume. It means the seller will not make repairs in response to inspection findings. It does not waive the buyer's right to inspect. It does not waive the seller's Form 17 disclosure obligations. It does not waive the buyer's right to renegotiate or walk away during the inspection contingency window.\n\n"
     "If you list 'as-is,' price into it — buyers absorb the cost of likely repairs in their offer. If you offer 'as-is,' read your inspection report carefully and use the contingency to renegotiate or walk away.\n"),
]

EXTRA_THREADS = [
    ("market", "Quarterly read on Selah inventory",
     "Anyone tracking the segmented Selah numbers? My anecdotal feel is that DOM is up about 15% YoY and inventory is up about 20%. Curious if that matches anyone else's data."),
    ("question", "Reliable mold remediation in central Yakima?",
     "Found mold in the basement of a 1962 home during inspection. Buyer wants quotes from two independent remediation companies. Recommendations welcome."),
    ("help", "VA appraisal repair list — pushing back",
     "VA appraisal flagged paint chips on a 1958 home as a repair item. Have any of you successfully pushed back on cosmetic-only repair calls?"),
    ("discussion", "Are listing love letters making a quiet comeback?",
     "I know the fair housing risks. But I am seeing buyer's agents include them again, redacted of demographic info. Curious where everyone lands."),
    ("market", "What is happening with conventional buyers under $400K?",
     "I am seeing fewer conventional buyers in the under-$400K bracket. FHA and VA seem to be carrying the segment. Anyone else seeing the same?"),
    ("show-tell", "Drone shot from a hilltop listing in West Valley",
     "Just got the drone footage back from a 2-acre listing on the West Valley ridge. The hero shot is unreal. Sharing for inspiration."),
    ("question", "Best septic inspector for Lower Valley orchards?",
     "Big property, big drainfield, old system. Looking for an inspector who actually understands ag-adjacent septic complexity."),
    ("local-news", "Yakima County permit fees rising in Q3",
     "Heads up — the building department announced a fee increase effective Q3. Anyone in active permit work should pull their estimates and re-budget."),
    ("help", "Buyer wants to write a contingent-on-sale offer",
     "First-time buyer wants to make a contingent-on-sale offer in a balanced market. What is the cleanest way to structure that without making it dead-on-arrival?"),
    ("discussion", "Has anyone had luck with iBuyer offers as a comp anchor?",
     "I have started using Opendoor and Offerpad estimates as a low-end comp anchor for sellers who think their house is worth more than the market believes. Anyone else?"),
    ("market", "West Valley DOM creeping up — what's driving it?",
     "West Valley DOM is up sharply Q-over-Q. Curious whether that is rate-driven, school-catchment-driven, or just supply normalizing."),
    ("question", "Recommendations for a closing attorney in Yakima?",
     "Complex transaction with a quitclaim from an estate. Need a closing attorney who knows their way around probate-adjacent title work."),
    ("show-tell", "Twilight photo of a 1920s craftsman in north Yakima",
     "Sharing a twilight shot from last week. The architecture is the whole story for this listing. Thoughts welcome."),
    ("help", "Buyer's lender keeps asking for the same documents",
     "Third request for the same paystubs in two weeks. Buyer is losing patience. Anyone been here? How did you handle the lender relationship?"),
    ("discussion", "Best tools for showings in 2026?",
     "I keep going back and forth on showing apps. Curious what is actually working for active agents — Showing Time, lockbox apps, or something else?"),
    ("local-news", "Yakima Avenue corridor revitalization — what realtors should know",
     "City announced funding for the Yakima Avenue corridor revitalization. Could meaningfully affect comps within a few blocks. Worth tracking."),
    ("market", "First-time buyer counts in Q1 — what your data shows",
     "My pipeline is showing more first-time buyers than this time last year. Curious if that is broadly true or just my book."),
    ("question", "Anyone use a flat-fee MLS service for FSBO listings?",
     "Have a seller who wants MLS exposure without full agent representation. Flat-fee MLS services I should look at?"),
    ("show-tell", "Before/after virtual staging on an empty 1950 ranch",
     "Sharing a staged-vs-empty comparison. The CTR delta was meaningful. Sharing for those debating whether virtual staging is worth it."),
    ("help", "Seller wants to time the market — convincing them to list now",
     "Seller is convinced rates will drop and is waiting. The math says they are wrong. How do you have that conversation?"),
    ("discussion", "What is the right photography budget for a $300K listing?",
     "I keep arguing with sellers about photography budget. What is the threshold below which you flat-out refuse to take a listing?"),
    ("market", "Naches turnover rate — quietly heating up?",
     "I am seeing inventory turn faster in Naches over the last six weeks. Curious if anyone else has data on that."),
    ("question", "Pet-related disclosures — what is required and what is best practice?",
     "Long-haired dogs lived in the home for ten years. The seller wants to disclose 'minor pet odor.' Is that enough? What do you advise?"),
    ("show-tell", "Mid-century kitchen restoration on a Yakima listing",
     "Owner kept the original 1962 cabinets, refinished them, replaced hardware. The result is gorgeous and it is doing the talking on showings."),
    ("local-news", "Yakima Federal posted a new realtor partner program",
     "Worth a look if you do a lot of Lower Valley deals — they posted a new co-marketing partner program last week."),
    ("help", "Inspection found a buried oil tank — now what?",
     "Buyer's inspector found evidence of an old fuel oil tank in the side yard. Seller did not disclose. How are you advising your buyer?"),
    ("market", "Spring inventory is ahead of last year — meaningful or noise?",
     "March listings are pacing about 12% above last March. Curious if you are seeing similar in your micro-market."),
    ("discussion", "Renting vs buying calculator — which one do you trust?",
     "Most rent-vs-buy calculators are too rosy on the buy side. What are you using with first-time buyers right now?"),
    ("question", "Real estate accountants who work with active agents in Yakima?",
     "I am looking for an accountant who actually understands schedule C realtor income, mileage, and home office. Recommendations welcome."),
    ("help", "Listing photos came back over-edited — what's the etiquette?",
     "Photographer over-edited the exteriors — sky replacement is too obvious. What is the cleanest way to ask for revisions without burning the relationship?"),
    ("show-tell", "Detached ADU walkthrough on a Yakima infill lot",
     "Owner finished a detached ADU last summer. Sharing the walkthrough for anyone weighing whether the math pencils."),
    ("market", "Out-of-area buyer share — pulling back?",
     "My anecdotal read is that out-of-area buyers (Seattle, California) are 30-40% less of the inquiry mix this spring vs last. Anyone else seeing this?"),
    ("question", "What's the right response time on inquiry messages?",
     "Lead intake from this platform — what response time are you targeting? I have been doing 1 hour during business hours but curious what the bar is."),
    ("discussion", "Do you offer to host the home inspection?",
     "I have started offering to host inspections for my listings. Buyers seem to like it. Curious if you do this and how it goes."),
    ("local-news", "Selah school bond on the November ballot",
     "Selah school bond is heading to the November ballot. Could meaningfully affect Selah catchment property tax forecasts."),
    ("help", "Buyer keeps backing out at week 2 of inspection contingency",
     "Same buyer twice has backed out at the inspection-period mark. Earnest money returned each time. Worth taking them on for round three?"),
    ("market", "Cherry land prices — quietly rising?",
     "I am seeing cherry orchard land trade harder this spring. Anyone with hard data on the Lower Valley ag market?"),
    ("question", "Best Spanish-bilingual transaction coordinator?",
     "Bilingual TC for a complex Lower Valley deal. Recommendations welcome — Spanish/English fluency is essential, not nice-to-have."),
    ("show-tell", "Side-by-side: AI furniture removal vs manual edit",
     "Did a side-by-side test of the platform's furniture removal tool against a manual photoshop edit. Sharing the results."),
    ("discussion", "Should buyer's agents stop attending the home inspection?",
     "I keep going back and forth. Some inspectors prefer no agent present. Others want the buyer's agent there. What's your protocol?"),
]

THREAD_REPLY_TEMPLATES = [
    "Agreed — seeing the same in my pipeline.",
    "Curious where you're getting your numbers. Mine are different.",
    "Solid analysis. Saving this for the next time it comes up with a client.",
    "We had a similar situation last quarter. Happy to walk you through what we did.",
    "Push back on this one. The data I'm seeing tells a different story.",
    "Worth running this past your broker before you act on it.",
    "I would loop in a transaction attorney before doing anything irreversible.",
    "Have you tried pulling the segmented data from the MLS? It often surfaces this kind of pattern.",
    "We solved this by changing photography vendors. Different problem, same shape.",
    "This is exactly the kind of thread I joined this platform for. Thanks for posting.",
]


def _ensure_user(email: str, full_name: str, *, is_realtor: bool = False, role: str = "member") -> User:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"full_name": full_name, "is_realtor": is_realtor, "role": role},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _ensure_extra_realtors(now) -> dict[str, User]:
    out: dict[str, User] = {}
    for email, name, brokerage, license_no in EXTRA_REALTORS:
        user = _ensure_user(email, name, is_realtor=True, role="realtor")
        out[name] = user
        RealtorProfile.objects.get_or_create(
            user=user,
            defaults={
                "license_number": license_no,
                "license_type": LicenseType.BROKER,
                "verification_status": VerificationStatus.VERIFIED,
                "verified_at": now,
                "brokerage": brokerage,
                "bio": f"Local broker with {brokerage}. Seeded demo realtor for content variety.",
            },
        )
    return out


def _seed_org_posts(org_author: User, now) -> int:
    created = 0
    for title, excerpt, body in EXTRA_ORG_POSTS:
        slug = slugify(title)[:240]
        if Post.objects.filter(slug=slug).exists():
            continue
        Post.objects.create(
            author=org_author,
            post_type=PostType.ORG,
            status=PostStatus.PUBLISHED,
            title=title,
            slug=slug,
            excerpt=excerpt,
            body=body,
            moderation_status="approved",
            moderated_at=now,
            published_at=now,
        )
        created += 1
    return created


def _seed_realtor_posts(extra_realtors: dict[str, User], now) -> int:
    created = 0
    base = User.objects.filter(email="demo-realtor@yakimaweb.local").first()
    for author_name, title, excerpt, body in EXTRA_REALTOR_POSTS:
        author = extra_realtors.get(author_name) or base
        if author is None:
            continue
        slug = slugify(title)[:240]
        if Post.objects.filter(slug=slug).exists():
            continue
        Post.objects.create(
            author=author,
            post_type=PostType.BLOG,
            status=PostStatus.PUBLISHED,
            title=title,
            slug=slug,
            excerpt=excerpt,
            body=body,
            moderation_status="approved",
            moderated_at=now,
            published_at=now,
        )
        created += 1
    return created


def _seed_threads(authors: list[User], now) -> int:
    created = 0
    for flair_slug, title, body in EXTRA_THREADS:
        flair = Flair.objects.filter(slug=flair_slug).first()
        if flair is None:
            continue
        if ForumThread.objects.filter(title=title).exists():
            continue
        author = random.choice(authors)
        ForumThread.objects.create(
            author=author,
            flair=flair,
            title=title,
            body=body,
            score=random.randint(0, 28),
            reply_count=0,
            moderation_status="approved",
            moderated_at=now,
        )
        created += 1
    return created


def _seed_replies(authors: list[User], now) -> int:
    created = 0
    threads = list(ForumThread.objects.all())
    for thread in threads:
        if thread.replies.exists():
            continue
        n_replies = random.randint(2, 7)
        chosen_authors = random.sample(authors, k=min(n_replies, len(authors)))
        for author in chosen_authors:
            body = random.choice(THREAD_REPLY_TEMPLATES)
            ForumReply.objects.create(
                thread=thread,
                author=author,
                body=body,
                score=random.randint(-1, 12),
                moderation_status="approved",
                moderated_at=now - timedelta(hours=random.randint(0, 96)),
            )
            created += 1
        thread.reply_count = n_replies
        thread.save(update_fields=["reply_count"])
    return created


def _seed_comments(authors: list[User], now) -> int:
    created = 0
    posts = list(Post.objects.filter(status=PostStatus.PUBLISHED))
    snippets = [
        "Saved this. Sharing with my buyers tomorrow.",
        "Useful framing. The third point especially.",
        "Curious how this plays out in Selah specifically.",
        "Pushing back on point two — my data is different.",
        "Bookmarking. This is the kind of post I joined for.",
        "Have a client this is going to help. Thanks.",
        "Strong piece. Looking forward to the follow-up.",
    ]
    for post in posts:
        if post.comments.exists():
            continue
        n = random.randint(1, 4)
        for _ in range(n):
            author = random.choice(authors)
            Comment.objects.create(
                post=post,
                author=author,
                body=random.choice(snippets),
                moderation_status="approved",
                moderated_at=now - timedelta(hours=random.randint(0, 240)),
            )
            created += 1
    return created


class Command(BaseCommand):
    help = "Extended demo seed: more org posts, realtor posts, threads, comments, replies."

    def handle(self, *args, **opts):
        org_author = (
            User.objects.filter(is_superuser=True).first()
            or User.objects.filter(is_staff=True).first()
            or User.objects.first()
        )
        if org_author is None:
            self.stdout.write(self.style.ERROR(
                "No users in DB — create a superuser before running seed_demo_extras."
            ))
            return

        now = timezone.now()
        random.seed(20260504)

        extra_realtors = _ensure_extra_realtors(now)
        commenter_pool = list(User.objects.all()[:30])
        if len(commenter_pool) < 4:
            self.stdout.write(self.style.WARNING(
                "Fewer than 4 users in DB — comments/replies will be sparse."
            ))

        org_created = _seed_org_posts(org_author, now)
        blog_created = _seed_realtor_posts(extra_realtors, now)
        thread_created = _seed_threads(commenter_pool or [org_author], now)
        reply_created = _seed_replies(commenter_pool or [org_author], now)
        comment_created = _seed_comments(commenter_pool or [org_author], now)

        self.stdout.write(self.style.SUCCESS(
            f"Extras seeded: org_posts={org_created}, realtor_posts={blog_created}, "
            f"threads={thread_created}, replies={reply_created}, comments={comment_created}."
        ))
