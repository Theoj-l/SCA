# MoveWell: model logic

How every number in the MoveWell app (`app/template.html` → `public/index.html`) and the submission notebook (`notebooks/MoveWell_Analysis.ipynb`) is produced. The two implement the same models; the notebook's last cell checks that they agree (`ALL MATCH`).

**Business question.** A new Singapore moving company has to buy trucks and hire crews before it knows how much work it will win. How many moves will there be to 2031, how big should the fleet be, how should it be built, and is the investment worth the risk?

**Latest changes (Nov 2026).** Added a sense check of the demand measure against outside figures (§2), monthly crew planning by dynamic programming (§8), and Singapore corporate tax on the cash flows (§9). Then added a fifth strategy, **broker first, then phased** (now the recommended plan), a make-or-buy test with leaner brokers, the value of the option to stop at the gate (§11), and the cost per job (§8). All results below are after tax with crews planned monthly; both can be switched off under *Adjust assumptions*, which reproduces the earlier model exactly (phased buying S$208,100 before tax with one crew per truck).

**Data cut-off.** Data pulled from data.gov.sg on 27 Oct 2026. Jan–Sep 2026 is a partial year; the forecast and the business plan cover 2027–2031 (60 months).

---

## 1. Data

| Data | Source | Used for |
|---|---|---|
| HDB resale transactions, Jan 1990 – Sep 2026 (5 files, 987,903 sales) | data.gov.sg | Resale moves, resale chance by flat age, season, market mood |
| HDB Property Information (blocks, units, completion year) | data.gov.sg | Flats completed per year (cohorts), BTO completions, MOP counts |
| HDB renting out of flats, monthly by town, 2021+ | data.gov.sg | Rental moves, rental seasonality |
| HDB rental approvals, quarterly, 2007-Q1 to 2021-Q3 | data.gov.sg | Rental moves before 2021 (spliced) |
| URA private residential transactions, quarterly, 2000+ | data.gov.sg | Condo and landed moves |
| Census 2020 households by planning area and dwelling type | SingStat via data.gov.sg | Splitting private moves across regions and planning areas |
| Real GDP growth 1985–2025 | SingStat via data.gov.sg | Recession flag |
| 16 dated rule changes, 1989–2026 | LKY School case study, cooling-measures timeline, HDB/MND releases | Policy impulse |
| Master Plan 2019 region and planning-area boundaries | URA via data.gov.sg | Map |
| OrangeTee HDB Market Outlook 2026 | Industry report | Validating MOP counts |
| ACRA Information on Corporate Entities (SSIC 49232) | data.gov.sg | Competitors: count, entry, survival, location |
| Mover price lists and guides (MoneySmart, Lalamove, Airtasker, Spaceship, Homejourney) | Published quotes | Competitor prices |
| Mover price quotes, lorry cost | Spaceship, DollarsAndSense | Business assumptions |

The notebook embeds an aggregated snapshot (gzip + base64) so it runs offline; `USE_LIVE_DATA = True` re-downloads and rebuilds it from source.

---

## 2. Estimated moves (the demand measure)

No public data counts moving jobs, so household moves are **estimated from housing records**. Each record type implies a number of households moving:

| Stream | Record | Moves per record | Why |
|---|---|---|---|
| HDB resale | Resale transaction | 2 | Seller moves out, buyer moves in |
| HDB rental | Approval to rent out a whole flat | 0.5 (slider `newTenancy`) | Some approvals are renewals with the same tenant (assumption) |
| New BTO | Flat completed that year | 1 | Owner moves in at completion |
| Condo and landed | URA resale / completed new sale | 2 per resale, 1 per completed new sale | Off-plan buyers cannot move in yet |

- Rental before 2021 comes from the quarterly file, scaled by the ratio of the two files over their overlap (Jan–Sep 2021).
- BTO completions are yearly (÷12 for monthly); private moves are quarterly (÷3).
- **Regions / planning areas:** HDB streams are assigned by town; private moves are only published nationally (by market segment), so they are split by each area's share of private households in Census 2020.
- 2025 total: **118,623 estimated moves** (HDB resale 50,168; rental 19,550; BTO 19,587; condo/landed 29,318).

**Known gaps:** moves with no record (moving in with family, emigration, private-home tenancies) are missed; not every move hires a mover. Market share is defined as a share of estimated moves, so it absorbs both.

**Sense check (floor 1, notebook §2b).** Singapore publishes no annual moving rate, so the estimate is bounded with outside figures:
- 118,623 moves ÷ 1,487,100 resident households (SingStat, 2025) = **8.0% of households a year**.
- **Arrivals only** (resale buyer 1, new tenancy, BTO owner, private resale buyer, completed new private sale) removes double counting of a household that sells one home and buys another: **78,916 = 5.3%**. This is the lower bound; the true number of relocations lies between ~79k and ~119k.
- Floor: household growth of 23,700 in 2025 (each new household is at least one move). Ceiling benchmark: 11.8% of Americans moved in 2024, a record low (US Census Bureau data via GlobeSt).
- Both counts sit between floor and benchmark, as expected for a high-ownership market with a 5-year MOP. Because market share is defined on the upper count, the 3% assumption (3,559 jobs a year) equals a 4.5% share of actual relocations.

**Market and competitors (floor 2, notebook §2c).**
- *Competitors:* ACRA's register of every Singapore business (Information on Corporate Entities, data.gov.sg, pulled 3 Nov 2026), filtered to SSIC 49232 "Moving services" as primary or secondary activity by `tools/fetch_acra_movers.py`, summarised by `tools/build_competitors.py` into `data/processed/competitors.json`.
- 12,154 entities ever registered; **2,232 live** (1,250 with moving as the main activity); 50% sole proprietors or partnerships; median 1 officer; median age 6 years. Only 304 live firms use "mover/moving/removal/relocation" in their name or description (many do deliveries or general lorry work under the same code).
- *Entry and survival:* about 167 new main-activity firms a year (2022–25; a spike in 2020–21). Share of each registration year still live in 2026: 30% of 2021's firms, 22% of 2016's (a survival snapshot by age, since the register has no closure dates).
- *Market size:* estimated moves × average price for 2025's mix (S$882) = **S$70M (arrivals only) to S$105M** a year; split evenly across main-activity firms, S$84k each. Our 3% share is S$3.1M a year, about 38× an average firm.
- *Where competitors are:* by registered postal sector (approximate). Against the share of moves, the East (1.7×) and North-East (1.3×) have the most moves per competitor, the Central region the fewest.
- *Prices* (published quotes): budget lorry trips S$149–300; GoGoX 14ft lorry S$380+, Lalamove helpers +S$40; Airtasker 4-/5-room average S$700/900; established movers' 4-room quotes S$883–980 (2020); 2026 guide 4–5 room S$800–1,500 (standard 1,000–1,200); month-end surcharge +10–20%. Our S$900 is mid-market.
- *Five forces:* rivalry high, entry high, substitutes high, buyer power medium–high, supplier power medium; each mapped to a model assumption (uncertain share and break-even share; price drift; elasticity above 1 and the broker's share penalty; price as top NPV driver; crew and truck costs as sliders).

---

## 3. Why moves happen: the MOP wave

- Owners must live in a new HDB flat for 5 years (Minimum Occupation Period). After that a wave of them sells.
- **Resale chance by age** `h(age)` = resales of each completion cohort ÷ flats completed that year, median across cohorts with ≥3,000 flats. Ages 20–35 share a pooled tail rate.
- **Two eras:** 1990–2010 (`h1`, older flats resold ~3.9%/yr) and 2011–2026 (`hNow`, ~3.1%/yr) after the 2010–13 cooling measures. Everything the forecast uses comes from 2011 onwards.
- MOP counts (flats completed 5 years earlier) are checked against OrangeTee's published forecast (e.g. 2027: 20,064 vs 18,939).

---

## 4. Demand model

```
resales(year y, month m) = E(y) / 12 × S[m] × M[y] × noise
E(y)  = Σ over completion years c of  flats(c) × h(y − c)       (structural resales)
S[m]  = seasonal index (12 values, mean-scaled), fitted 2011–2023, Covid circuit breaker (Apr–May 2020) excluded
M[y]  = market mood: actual ÷ (structural × season), one value per year
```

- Future completions: actual up to 2025, max(actual, slider) for 2026, slider `btoFuture` (20,000/yr) afterwards.
- **Market mood dynamics** (AR(1) on log M, 2012–2026), after removing recession and policy effects (§6):
  `log M[y] = c + φ·log M[y−1] + bRec·recession[y] + bPol·policyImpulse[y] + ε`
- Monthly noise: lognormal, sd = residual sd of the fitted monthly model (`epsSd`).
- **Rental:** average monthly approvals 2021–2026 × rental seasonality `Sr` × new-tenancy share, ±6% monthly noise.
- **Private:** average of the last 15 quarters, ±13% (their coefficient of variation), moves with market mood (excluding the recession boost).
- **BTO:** slider ÷ 12, ±15% per year.

---

## 5. Forecast checks

1. **Monthly hold-out:** fit on 2011–2023, forecast Jan 2024 – Sep 2026 (33 months) standing at end-2023, mood carried at its 2023 level.
   - Our model MAPE 11.8% vs "2023 repeated" (fair baseline) 12.9%. "Same month last year" (11.1%) peeks at newer data and is shown for reference only.
2. **Rolling 1–5 year backtest:** for each origin year 2013–2021, refit `h` and the mood AR(1) on 2011..origin only, forecast annual totals 1–5 years ahead.
   - 5 years ahead: **8.3% error vs 22.1%** for repeating the last year.
3. **Prediction-interval coverage** (notebook §5b): about 89% of outcomes fall inside the 80% band and 61% inside the 50% band, so the bands are slightly wide (conservative).

---

## 6. Recessions and rule changes

- **Recession flag:** real GDP growth < 1% (1998, 2001, 2009, 2020).
- **Policy impulse:** each of 16 dated rule changes is +1 (opens demand: e.g. 1989 resale opened to PRs and private owners, 2026 wait-out removal) or −1 (restricts: ABSD, LTV/TDSR, PR wait), 1 = major, 0.5 = minor or mostly private. A change in month m counts (12 − m + 1)/12 in its year and the rest the next year.
- **Regression 1991–2025:** `log M[y] = a + b·era2011 + φ·log M[y−1] + bRec·rec[y] + bPol·impulse[y]`, where M is mood under each era's own resale chances.
  - **Recession year: +16.6% resales** (`bRec`); **major rule change: ±6.5%** (`bPol`), fading through the lag.
  - Year-to-year mood explained: 65% without indicators → 69% with.
  - Robustness: dropping each recession (and the year after) keeps the effect positive (7% to 24%); rule changes always push the expected way.
- **In the simulation:** recessions arrive with the historical frequency (~1 in 9 years); rule changes arrive at 16/38 per year, and are more likely to be tightenings after a hot year (8 of 8 historically) than after a quiet one (Laplace-smoothed). The July 2026 loosening carries half into 2027.
- **Scenarios:** random (default), none / frozen, or forced (recession in a chosen year; loosening or tightening in July of a chosen year). In forced scenarios the fleet is planned from the normal forecast, so the shock arrives unannounced.
- **Stress table:** six scenarios × the same 600 futures × one fleet plan.

---

## 7. Monte Carlo of the future (2027–2031)

`genScenarios(a, nsim = 2000, seed = 2027)` produces 2,000 futures × 60 months. Random generator: mulberry32 + polar Box–Muller, replicated exactly in Python (`Rng` class), so app and notebook draw identical numbers. Every draw happens in every future whatever the scenario (**common random numbers**), so strategies and scenarios are compared on the same futures.

Per future:
- market mood path (AR(1) with recession and policy shocks, §6)
- monthly HDB resale moves = 2 × E(y)/12 × S[m] × M[y] × lognormal noise
- rental, BTO and private moves (§4)
- **our market share:** S-curve from 0.5% in month 1 to a target drawn triangular(0.5×, 1×, 1.3× of `shareTarget` = 3%), reaching it over `rampMonths` = 24 months
- **price drift:** random walk, 3% a year; × (1 − 10%) in recession years
- **capacity noise:** ±3% a month (on top of 5% downtime)

---

## 8. Fleet and crews: newsvendor ceiling + monthly crew plan

**Costs per job-slot.** Underage (a job we cannot do ourselves) `Cu = subcontractor 80% × S$900 − own variable cost S$90 = S$630`. An idle **truck** slot costs `(S$125,000/10/12 + S$1,500) / 30 = S$85`; an idle **crew** slot costs `S$11,000 / 30 = S$367`.

**Trucks (capital, yearly).** The newsvendor fleet with the truck-only overage cost (`CR = 630/(630+85) = 0.88`) is a **ceiling**: ⌈ 0.88-quantile of all simulated monthly jobs in year k ÷ (30 × 95%) ⌉.

**Crews (labour, monthly): aggregate planning by dynamic programming.** Each month t choose W_t crews, 0 ≤ W_t ≤ trucks that month, starting from none:
```
maximise  Σ_t δ_t [ g_t(W_t) − h·(W_t − W_{t−1})⁺ − r·(W_{t−1} − W_t)⁺ ]
g_t(W)  = mean over the futures of (revenue − own variable cost − subcontract cost − marketing) with W crews
          − W × crew cost             (rounded to the cent so app and notebook break ties identically)
h = r   = S$3,000 to hire or release one crew (assumption);  δ_t = monthly discount factor
DP:       best[t][W] = g_t(W) + max_W' ( best[t−1][W'] − change cost(W'→W)·δ_t ),  backtrack from the best final W
```
One schedule for all futures, decided in advance like the fleet (60 numbers fitted on 2,000 futures, so overfitting is negligible). **Trucks then follow the plan:** each year's busiest planned month (buy: the busiest month of all five years; lease: each year; phased: running maximum, never sell), so no truck is bought that no crew will drive.

**Result:** for phased buying from day one, crews grow from 2 to 10 over 2027–28 with market share; for the recommended plan (broker first) there are no crews in 2027, then 5 in January 2028 growing to 10 (10 hires, 0 releases), with trucks 0 → 9 → 10 → 10 → 10. Once the share settles, seasons (±10%) are too mild for hiring and releasing at S$3,000 to pay, so crews stay flat and peaks go to subcontractors. One crew per truck (the earlier model) gave a single ratio `CR = 630/(630+451) = 0.58`.

**What one job earns (2029, floor 6):** average price S$884 (market mix) − materials S$90 − marketing S$53 − crew time S$415 (S$11,000 ÷ 26.5 jobs at 93% utilisation) − truck S$96 = **S$230 per job done in-house**, against **S$124 per job passed to a subcontractor**. Covering S$360,000 a year of overhead takes about 1,560 in-house jobs a year. Crew time costs four times the truck per job, which is why crews are planned monthly and trucks yearly.

---

## 9. Five strategies, cash flows and tax

| Strategy | Trucks |
|---|---|
| Buy fleet upfront | Year-3 ceiling, then the plan's busiest month of all five years, bought in month 1 |
| Lease and resize yearly | Each year's busiest planned month, leased at S$2,900/truck/month |
| **Phased buying** | Each year's busiest planned month, never sell (running max) |
| Asset-light broker | No trucks or crews; 30% less share won; pays subcontractors 85%; can place at most 85% of jobs; S$18,000/month overhead |
| **Broker first, then phased** (recommended) | Broker in 2027 (no trucks or crews, broker terms), then phased buying with planned crews from January 2028 |

Each month in each future:
```
demand   d = share × (resale + rental + BTO + private moves)          (× 0.7 for the broker)
price    p = blended price (HDB S$900, rental 0.55×, private 1.22×) × drift
capacity  = crews W_t × 30 × 95% × capacity noise
own       = min(d, capacity);  overflow = d − own
sub       = min(overflow, 25% × d)          (subcontractors absorb at most 25% of demand; broker 85%)
lost      = overflow − sub
revenue   = (own + sub) × p
cost      = own × S$90 + sub × p × 80% + W_t × S$11,000 + trucks × S$1,500 running + overhead S$30,000 (broker 60%)
            + marketing 6% of revenue (+ lease) + S$3,000 per crew hired or released
cash flow = revenue − cost − truck purchases − corporate tax;  final month + book value of owned trucks (straight line, 10 years)
```
**Corporate tax (Singapore, IRAS rules).** Per future and calendar year: chargeable income = operating profit − capital allowances (each truck written off over 3 years, Section 19A(1); commercial vehicles qualify) + balancing charge on the trucks' 2031 sale at book value, less losses brought forward (no time limit; shareholding test assumed met). Start-up exemption in the first 3 years (75% of the first S$100k, 50% of the next S$100k), partial exemption after (75% of the first S$10k, 50% of the next S$190k). Tax = 17% of the rest, paid at the end of the year (in practice a year later, so slightly conservative). Temporary CIT rebates are left out.

- **NPV** at 10% a year (monthly discounting), after tax. Optional terminal value: 3× final-year operating cash flow × (1 − 17%) (off by default).
- **Metrics:** mean NPV, chance of loss (NPV < 0), CVaR (mean of worst 5%), cash needed (5th percentile of the deepest cumulative cash hole), IRR on the mean cash flows (bisection), median payback, crew utilisation, jobs turned away, tax a year, NPV before tax.

**Base results (seed 2027, after tax, crews planned monthly):**

| Strategy | Mean NPV | Chance of loss | Worst 5% avg | Cash needed | IRR | Trucks 2027→2031 |
|---|---|---|---|---|---|---|
| Buy upfront | S$156k | 33% | −S$1.93M | S$2.10M | 13.4% | 10→10 |
| Lease yearly | −S$11k | 40% | −S$2.16M | S$2.30M | 8.7% | 5→10 |
| Phased buying | S$358k | 26% | −S$1.71M | S$2.00M | 19.8% | 5→10 |
| Broker | −S$339k | 100% | −S$523k | S$614k | n/a | 0 |
| **Broker first, then phased** | **S$421k** | **24%** | −S$1.58M | S$1.98M | 24.2% | 0→10 |

**What crew planning and tax do (phased buying from day one, same futures):**

| Model | Trucks | Mean NPV | Chance of loss | Cash needed | Tax a year |
|---|---|---|---|---|---|
| One crew per truck, before tax (earlier model) | 3·10·11·11·11 | S$208k | 37.3% | S$2.83M | – |
| One crew per truck, after tax | 3·10·11·11·11 | S$101k | 38.8% | S$2.83M | S$34k |
| Crews planned monthly, before tax | 5·9·10·10·10 | S$480k | 24.9% | S$2.00M | – |
| **Crews planned monthly, after tax (base)** | 5·9·10·10·10 | **S$358k** | **26.0%** | S$2.00M | S$38k |

- Precision: ±S$34k (95%) within the seed for the recommended plan; five seeds give **S$407k–430k** (23–24% chance of loss), best under every seed; phased buying from day one S$344k–368k. Monthly crew planning made results far less seed-sensitive than one crew per truck (S$95k–208k).
- **Make or buy (floor 7):** a lean broker (S$8,000/month overhead) earns S$127k with a 9% chance of loss; with no share penalty S$334k and 0%. Outsourcing everything is the low-risk, low-return option; owning earns more per job (S$230 vs S$124) but can lose heavily. Broker first, then phased combines them.
- **Stress test** (recommended plan, 600 futures, one plan made in advance): calm S$475k, history repeats S$415k, recession 2028 S$460k, tightening 2028 S$393k, loosening 2028 S$553k, recession then tightening S$396k.
- **Tornado:** each assumption ±20%, 600 futures. Move price and jobs per crew matter most.

---

## 10. Peak pricing (rate card)

- **Tiers by calendar month:** peak = 3 highest months of S (Apr, Jul, Aug) at +15%; off-peak = 3 lowest (Dec, Jan, Feb) at −10%; normal = list price.
- **Customer response** applied to our monthly jobs before the fleet is sized:
  1. elasticity: jobs × (price multiplier)^(−1.2)
  2. date shifts: 20% of peak-month customers move to off-peak months of the same year at the off-peak price, but only into the gap below an average month (capacity control, so quiet months never become the new peak)
- The newsvendor then re-sizes the fleet on the reshaped demand; the critical ratio keeps the list price (conservative).
- **Result (recommended plan, crews planned monthly, after tax):** +S$28k mean NPV (premium alone +S$166k, discount alone −S$121k); chance of loss 24% → 21%; one truck fewer in 2029. Crew planning already matches capacity to demand, so less is left for pricing; a premium-only rate card is the better version. (Before crew planning and tax the rate card added S$68k.)
- **Sensitivity grid** (elasticity 0.3–2.0 × flexible share 0–30%, 600 futures); **break-even elasticity ≈ 1.5** (bisection): the rate card pays while a 10% price rise loses fewer than ~13% of jobs. The grid is not perfectly smooth because small demand changes tip whole crews or trucks in or out.

---

## 11. Go / no-go and the stage gate

All for the recommended plan (broker first, then phased):
- **Break-even market share:** bisection on `shareTarget` until mean NPV = 0 (600 futures) → **2.2%** (we assume 3.0%).
- **Chance of reaching it:** from the triangular(0.5×, 1×, 1.3×) share distribution → **87%**.
- **Stage gate:** on the break-even path, the share after 12 months of the 24-month ramp (1.21%) × the broker's 70% × simulated market in Dec 2027 (~9,900 moves) → **~84 jobs a month as a broker**. Below it, do not buy trucks.
- **Value of the option to stop (abandonment option):** in each future, if its own December 2027 jobs are below the gate, close the business at the end of 2027 (NPV = its 2027 cash flows only; no trucks to sell, no crews to release). This stops **16%** of launches; they lose about **S$166k** on average instead of **S$761k** if they had carried on. Mean NPV rises **S$421k → S$516k (+S$95k)**; the chance of loss rises slightly (24% → 27%) because every stopped future books its year-1 loss, including a few that would have recovered. Stopping cuts the size of losses, not their number.
- **Value per risk:** about S$21 of expected NPV per S$100 of cash buffer; IRR 24.2% vs a 10% hurdle.
- **Verdict rule:** no-go if mean NPV ≤ 0; go if chance of loss < 20%; otherwise **go, with conditions**.

---

## 12. Town clusters and depots

- **k-means** on 26 HDB towns, 5 standardised features: resold per year, resale growth (2023–26 vs 2017–19), share reaching MOP by 2031, share rented out, share of 4-room+ resales. k-means++ start, Lloyd iterations.
- **k = 4** chosen by the elbow and silhouette (0.33): family-size flats, rental hotspots, fast-growing, MOP wave coming.
- **Depots:** a second k-means on town coordinates, weighted by estimated moves (longitude scaled by cos(latitude)).

---

## 13. The app

- **Map layer:** region bars of estimated moves by type and year (2021–2026), planning-area drill-down, "change vs previous year / vs 2021" views, region side panel.
- **Analysis building, floors G–10 and the rooftop:** opening and answer (G), MOP wave and the sense check (1), market and competitors (2), forecast check (3), outlook (4), shocks and policy (5), fleet sizing, the monthly crew plan and cost per job (6), risk and the make-or-buy test (7), return, tax and tornado (8), town clusters and depots (9), go/no-go with the value of stopping at the gate, recommendation, limitations and sources (10), and on the rooftop (R) peak pricing: one more lever applied to the recommended plan.
- Every slider re-runs the 2,000 futures; changed numbers animate. The main results update first (about 1 s); the stress table, pricing, go/no-go and tornado (about 40 more simulation runs) follow in small steps so the page stays responsive.
- *Adjust assumptions* also has switches for corporate tax and monthly crew planning (both on by default).
- `python run.py` builds and serves the app; `python run.py notebook` runs the notebook and checks `ALL MATCH`; the site is a static file on Vercel.

## 14. Limitations

Demand is a proxy, bounded but not validated (§2); business numbers, including the S$3,000 hire and release costs, are assumptions with sliders; tax is simplified (no temporary rebates, paid at year end, no working capital); simulation noise (§9); customer price response is assumed (§10); simplified operations (crews planned on average demand as one schedule, no overtime or re-planning within a future; depots from k-means rather than travel times; 2020 Census shares; rule changes dated from secondary sources).
