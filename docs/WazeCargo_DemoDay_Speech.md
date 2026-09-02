# WAZE CARGO — Demo Day Speech

## [SLIDE 1 — Title]

Good morning everyone. My name is David Vergara Fuentes, and together with my team — Michalis, Meliane, Artemiy, and Gerson — we built **Waze Cargo**: a predictive maritime analytics platform that forecasts port congestion before it happens.

Our tagline says it best: *"The ocean doesn't wait. Now you can move before it does."*

---

## [SLIDE 2 — Executive Summary]

Here's the picture in one sentence: Chile moves **223 billion dollars** in annual trade through its ports — and **no tool on the market** tells you whether that port will be congested when your cargo arrives.

Waze Cargo changes that. We're a freemium SaaS platform that predicts congestion across Chile's 31 ports up to **12 months ahead** — by combining 20 years of customs intelligence with seasonal ocean-weather forecasts. Our ML model runs at a **4.03% error rate**, and Dashboard 2.0 is already built and running.

We're here today asking for **€120,000 in seed funding for 15% equity** — to deploy, go to market, and plant our flag in Chile.

---

## [SLIDE 3 — Team]

Let me tell you why *this* team can pull this off.

Michalis is our ML engineer and tech lead — he built the entire pipeline, the AWS infrastructure, and the weather integration from scratch. Meliane designed our go-to-market strategy and funnel. Artemiy built our forecasting models. Gerson kept us on track as project lead.

And then there's me. I spent years working inside Chilean customs. That's not just domain expertise — that's **direct access to 20 years of trade records** that no outside team could get their hands on. That data is the foundation of everything you're about to see.

---

## [SLIDE 4 — The Problem]

Let me paint you a picture.

Chile's importers — 98.6% of them are SMEs — bring in **84 billion dollars** worth of machinery, electronics, vehicles, pharma. A five-day port delay means empty shelves, missed deadlines, and penalties. And here's the thing — insurance does **not** cover commercial losses from congestion.

On the export side, Chile is the world's number one copper exporter, plus fruit, salmon, wine, lithium — **139 billion dollars FOB**. When grape season hits in March or cherry season in December, a congested port means spoiled perishables and lost contracts worth millions.

Today's tools — MarineTraffic, VesselFinder — they tell you: *"Your vessel is 450 nautical miles from San Antonio, ETA March 15th."* Great. But they **cannot** tell you if that port will be jammed when you get there. They can't tell you if your grapes will compete with copper for berth space, or if ocean swells are about to shut down operations.

**Waze Cargo can.** We tell you: *"San Antonio will run 40% above normal on March 15th, swell risk is 3.2% — route through Valparaíso at 37%, or Coquimbo at just 7%, the calmest port in the country."*

That's the difference between reacting and **deciding**.

---

## [SLIDE 5 — Market & Users]

Our market breaks into three segments.

The **core** is small importers and exporters — highest volume of firms, smallest logistics teams, most vulnerable to delays. They currently rely on phone calls and gut feeling. Our free tier captures them.

The **growth** layer is medium-sized firms with structured operations, willing to pay for predictive tools. These are our Pro subscribers. One avoided delay per quarter more than pays for the subscription.

The **expansion** layer is B2B — freight forwarders, customs brokers, port authorities, mining companies. Enterprise and API licensing.

Think about Maria. She runs a mid-size fruit export company in Santiago. Every December she ships cherries to China through San Antonio. Last year? A six-day congestion delay. Cherries past their peak. **$180,000 rejected.** With Waze Cargo, she sees that December spike **three months out** and routes through Valparaíso instead. Problem solved.

---

## [SLIDE 6 — Business Model]

Our model is **freemium SaaS** — taste, then crave.

The **free tier** gives you congestion risk labels for one port, monthly view, no commodity detail. Enough to get hooked.

**Pro**, at €100 to €350 per month, unlocks all 31 ports, a 12-month forecast horizon, commodity breakdowns, weather-adjusted delay risk, cross-port comparison, and alternative port routing.

**Enterprise**, at €500 and up, adds multi-user dashboards, ERP integrations, dedicated support, and white-label options.

Our acquisition engine is smart: we publish a **public live dashboard** for San Antonio and Valparaíso — no signup needed. For cold outreach, we use customs data to show prospects **their own import history**. They see the value before we even ask for a meeting.

Conversion is built into the product: routing recommendations are visible but paywalled, commodity tables are blurred, swell alerts are locked. Users see exactly what they're missing.

---

## [SLIDE 7 — Product Demo]

Now — and I want to emphasize this — what I'm about to show you is **a running product**, not a mockup.

Dashboard 2.0 is live. You'll see an interactive map with all 31 Chilean ports color-coded by congestion risk. You can toggle between imports and exports — the profiles flip completely. Click into San Antonio and you get a 12-month forecast with best and worst months, plus swell and wind drivers. Switch view modes between congestion, weather, or combined. Drill into a commodity — say HS26, copper — and get cross-port comparison with a best-port recommendation.

The "aha" moment? When a user discovers a port they never considered is actually the best choice for their specific cargo.

One more thing on scientific integrity: during development, we found **two data-leakage bugs** that were inflating our accuracy. R-squared looked like 0.91 — but honestly it was 0.57. We caught them, fixed them, and we only report honest numbers. **4.03% weighted MAPE**, stress-tested across four temporal folds including the COVID break.

---

## [SLIDE 8 — Live 2026 Accuracy]

Here's the proof that matters: we forecast 2026 **before the year happened**. Five months in, we graded the model against actual customs data — January through May — fully out of sample.

National totals: imports forecast error **+7.7%**, exports **+4.5%**, total **+7.1%**.

Where it counts most — San Antonio imports, which represent **57% of all maritime imports** — our error is just **3.4%**. San Antonio exports: **1.2%**. Near-perfect on the highest-value flow.

Our biggest miss? Valparaíso imports, driven by a +91% spike in May — that's a known fix target and we're on it.

- 4.03% — the error rate (wMAPE) on the 2025 holdout data. This is data the model didn't train on, but it's still a controlled test within your historical dataset.
  - 8.5% — the error rate on live 2026 data. This is actual customs data from January–May 2026 that didn't exist when the model was built.

  "Honest degradation" means it's normal and expected for a model to perform slightly worse on truly future data versus a holdout test. The jump from 4% to 8.5% is
  modest and shows the model is robust — it's not overfitting.

  Think of it like a student who scores 96% on practice exams and 91.5% on the real exam. A small drop is natural, and 91.5% is still a strong result. The slide frames
  this as a positive: your forecasts hold up in the real world, especially on large ports (8.3% error) which handle 98% of trade volume.

The 4.03% wMAPE comes from your model's performance on the 2025 holdout test — a portion of historical data (2005–2025) that was deliberately excluded from training
  so the model could be evaluated on data it had never seen.

  Specifically, it was validated using walk-forward cross-validation across 4 temporal folds, including one that covers the COVID period (which was a major disruption
  to shipping patterns). This rigorous testing method is what gives that number credibility — it wasn't just tested on one convenient time window, it was stress-tested
  across different periods.
  
  So in short: you trained the model on historical customs data, held back 2025, asked the model to predict 2025, and it was off by only 4.03% on average (weighted by
  volume). That's where the number comes from.


Overall: **8.5% weighted MAPE** across 54 port-direction pairs. And large ports — which handle **98% of volume** — sit at just **8.3%**. The model is most accurate exactly where it matters most.

---

## [SLIDE 9 — Market Opportunity]

The maritime analytics market is **$1.8 billion today**, growing to **$5.6 billion by 2034** at roughly 12% CAGR. And 69% of ports globally remain untapped by predictive tools.

Now look at this competitive matrix. MarineTraffic, VesselFinder, Kpler, Vizion, Sinay — **none of them** combine congestion prediction, commodity-level data, weather risk, and 20 years of Chilean customs history.

That customs dataset is our moat. It's unreplicable from AIS data alone. Global platforms won't build Chile-specific models for a market they don't prioritize. **We're already there.**

---

## [SLIDE 10 — Key Metrics]

Our North Star metric is **Weekly Active Port Checks** — unique users checking at least one port forecast per week. It captures engagement and the habit that drives conversion.

Our targets: 40% activation rate — a forecast check within 3 minutes. 8 to 12% free-to-Pro conversion — well above the SaaS benchmark of 3 to 5%. Monthly churn below 5%. Day-30 retention at 60%. Customer lifetime value above €2,400, giving us a **3-to-1 LTV-to-CAC ratio**.

Year one target: **10 Pro users, €40K ARR.** We get there through the public free dashboard, cold outreach powered by customs intelligence, and trade association partnerships.

---

## [SLIDE 11 — Financial Projections]

Here's our path from **€40K to €1.2 million ARR** over five years.

Year one: 10 Pro users, MVP focused on San Antonio and Valparaíso — which together handle over 60% of container traffic. Year two: 55 Pro users, first Enterprise client, all 31 ports live. Year three: 150 Pro users, ARPU grows to €250 on commodity upsells, first API deals. Year four: 280 Pro users as we begin expanding into Peru and Colombia. Year five: 450 Pro users, white-label deals with port authorities, API licensing at scale.

And here's the key: our pipeline is **country-agnostic**. The same ML architecture we built for Chile can be deployed to any country with customs data.

---

## [SLIDE 12 — The Ask]

We're raising **€120,000 for 15% equity** — an implied valuation of €800K.

This is a **go-to-market bet on a working product**, not an R&D bet.

**40%** goes to product and infrastructure — deploying Dashboard 2.0, AWS scaling, the Enterprise API layer, and upgrading to live 7-day marine weather forecasts.

**30%** goes to sales and marketing — cold outreach tooling, trade events like SNA, ASOEX, and SOFOFA, content, SEO, and first case studies.

**30%** goes to team and operations — a part-time Chile market representative, legal compliance, and securing a formal data partnership with Chile's national customs service.

On returns: at a conservative 5x revenue multiple, Year 3 puts you at a **16x return**, and Year 5 at a **50x return** — in line with comparables like Windward and Kpler at 8 to 12x revenue multiples.

---

## [SLIDE 13 — Risks & Mitigation] *(if Q&A comes up)*

We've mapped our risks honestly. Low SaaS adoption among Chilean SMEs? The free tier removes the cost barrier, and WhatsApp alerts meet users where they already communicate. Competitors adding prediction? Our 20-year customs dataset at commodity-by-port granularity can't be replicated from ship tracking alone. ML accuracy degradation? We run walk-forward cross-validation, monthly auto-retraining, and alert if error crosses 8%. We've thought this through.

---

## [SLIDE 14 — Close]

I'll leave you with this:

*"The ocean doesn't wait. Now you can move before it does."*

The product is built. The data is ours. The market is blind and we have the lens.

**€120,000. 15% equity. Let's deploy.**

Thank you.

---

**Estimated delivery time:** 12–15 minutes. Trim Market Opportunity and Financial Projections sections to hit 10 minutes. The strongest sections to keep intact are the Problem, Product Demo, and Live 2026 Accuracy.
