# MoveWell: planning a Singapore moving company from HDB data

OPIM348 Supply Chain Analytics term project (SMU). A new moving company has to buy fixed assets (trucks, crews) before it knows how much work it will win. Using 36 years of official housing data we forecast Singapore's household moves to 2031, size the fleet with the newsvendor model, test five ways of building the fleet for risk (NPV, chance of loss, CVaR) and return (IRR, payback), including recessions and rule changes for PRs, foreigners and loans, and test peak pricing as a way to manage the peak instead of buying for it.

## What's in the repo

```
SCA/
├── notebooks/
│   └── MoveWell_Analysis.ipynb   THE SUBMISSION: data (embedded), every model, every test,
│                                 results and explanations in one self-contained notebook
├── app/
│   ├── template.html             the interactive frontend; every model in commented JavaScript
│   ├── build.py                  embeds data/processed into the template
│   ├── MoveWell_HDB_Moving_Demand.html   the built app (open in a browser to present)
│   └── tools/make_reference.js   records the app's key numbers (for the notebook's check)
├── run.py                        one command to set up, run the notebook, build and open the app
├── public/index.html             copy of the built app; the only file the website serves
├── vercel.json                   Vercel settings (static site from public/, no build step)
├── data/
│   ├── processed/                aggregated data used to build the app (same as the notebook's snapshot)
│   ├── raw/                      raw downloads (git-ignored)
│   └── app_reference.json        output of make_reference.js
├── tools/
│   ├── fetch_acra_movers.py      downloads ACRA's company register (data.gov.sg API) and keeps moving firms (SSIC 49232)
│   └── build_competitors.py      summarises them into data/processed/competitors.json
├── docs/
│   └── MODEL_LOGIC.md            every model, formula and result, in one document
├── requirements.txt
└── README.md
```

**The notebook is self-contained.** The data (pulled from data.gov.sg on 27 Oct 2026) is embedded in §1 as a compressed snapshot, so it runs anywhere with no extra files or internet. The code that downloads and aggregates the official files is included too: set `USE_LIVE_DATA = True` to rebuild the data from source and compare it with the snapshot. Every random draw is seeded, so *Run All* reproduces every number.

**Testing in the notebook:** a monthly hold-out test against a fair baseline, a rolling-origin 1–5 year backtest, a prediction-interval coverage test (do the forecast bands contain reality as often as they claim?), leave-one-out robustness for the recession and policy effects, a seed-robustness check of the simulation, and a final check that the interactive app reproduces the notebook's numbers (`ALL MATCH`).

## How to run

**One command** (Windows, macOS or Linux; needs Python 3.10+ on PATH):

```powershell
python run.py              # first run sets up .venv and installs everything, then builds the app and opens it at http://localhost:8000
python run.py notebook     # runs the analysis notebook top to bottom and checks it reproduces (prints ALL MATCH)
python run.py all          # notebook, then the app
```

**Manual setup** (if you prefer):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # the prompt should start with (.venv)
pip install -r requirements.txt
```

**Run the notebook.** Open the folder in VS Code (with the Python and Jupyter extensions), open `notebooks/MoveWell_Analysis.ipynb`, choose **Select Kernel → Python Environments → .venv**, then **Run All** (about a minute). The last cell should print `ALL MATCH`.

**Open the app.** Double-click `app/MoveWell_HDB_Moving_Demand.html`. After changing `template.html` or the data, rebuild with `python app/build.py`.

**If you change a model**, change it in both the notebook and `app/template.html`, rebuild the app, run `node app/tools/make_reference.js` (needs Node and Playwright), copy the new values into the `APP` dictionary in the notebook's last section, and re-run the notebook.

## Deploying the website (Vercel)

The app is a static file: all models and the simulation run in the visitor's browser, so no server or serverless function is needed.

1. Push this repo to GitHub (with `public/index.html` committed).
2. On vercel.com: **Add New → Project →** import the repo. `vercel.json` already sets the output directory to `public` and turns off the build step; leave everything else as default.
3. **Deploy.** Every later push to the main branch redeploys automatically.

To update the site: edit `app/template.html` (or refresh the data), run `python app/build.py`, commit, push.

The app and notebook are built around the 27 Oct 2026 data cut-off (Jan–Sep 2026 is treated as a partial year and the forecast covers 2027–2031). Adding newer months needs those dates updated in both, so refreshing the data is a deliberate step, not an automatic one.

## Method in one paragraph

No public data counts moving jobs, so moves are **estimated from housing records**: an HDB resale = 2 moves, a new tenancy = 1 (50% of rental approvals, an assumption), a completed BTO flat = 1, a private resale = 2 and a completed new private sale = 1. HDB resales are forecast as *flats of each age × the chance a flat that age is resold* (it jumps after the 5-year MOP), × a seasonal index, × a "market mood" that follows an AR(1). Resale chances are estimated separately before and after the 2010–13 cooling measures. Five years ahead the forecast errs by about 8% in a rolling backtest, against 22% for repeating last year. Recessions (GDP growth under 1%) raise resales by about 17%; a major rule change moves them about 7%. Both enter the simulation as random shocks at historical rates, or as forced stress tests. 2,000 simulated futures feed the fleet decision: trucks are capped by a newsvendor rule, and **crews are planned month by month by dynamic programming** (hire and release costs, never more crews than trucks), with trucks bought to match the plan. Cash flows are **after Singapore corporate tax** (17%, start-up and partial exemptions, 3-year capital allowances, loss carry-forward). Five strategies are compared on the same futures. **Broker first, then phased** (subcontract every job in 2027 while demand is uncertain, then buy trucks in phases) has the best mean NPV (S$421k ± S$34k; S$407k–430k across seeds) and the lowest chance of loss among the owning strategies (24%); phased buying from day one is second (S$358k, 26%), and a lean broker is the low-risk, low-return alternative. The verdict is **go, with conditions**: break-even needs about 2.2% market share, and trucks are bought only if MoveWell is placing at least about 84 jobs a month as a broker by December 2027; that option to stop is worth about S$95k. A peak rate card adds only about S$28k once crews are planned (the premium alone about S$166k) and depends on assumed price sensitivity. Market and competitor research uses ACRA's register (2,232 live moving firms, mostly one-person, with high churn) and published price lists (our S$900 is mid-market). A sense check bounds the demand measure between 5.3% and 8.0% of households a year. Full logic: [`docs/MODEL_LOGIC.md`](docs/MODEL_LOGIC.md).

## Data sources

| Data | Source |
|---|---|
| HDB resale flat prices, 1990–2026 | data.gov.sg [`d_ebc5ab87086db484f88045b47411ebc5`](https://data.gov.sg/datasets/d_ebc5ab87086db484f88045b47411ebc5/view), [`d_43f493c6c50d54243cc1eab0df142d6a`](https://data.gov.sg/datasets/d_43f493c6c50d54243cc1eab0df142d6a/view), [`d_2d5ff9ea31397b66239f245f57751537`](https://data.gov.sg/datasets/d_2d5ff9ea31397b66239f245f57751537/view), [`d_ea9ed51da2787afaf8e51f827c304208`](https://data.gov.sg/datasets/d_ea9ed51da2787afaf8e51f827c304208/view), [`d_8b84c4ee58e3cfc0ece0d773c8ca6abc`](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) |
| HDB Property Information | [`d_17f5382f26140b1fdae0ba2ef6239d2f`](https://data.gov.sg/datasets/d_17f5382f26140b1fdae0ba2ef6239d2f/view) |
| HDB renting out of flats (2021+) | [`d_c9f57187485a850908655db0e8cfe651`](https://data.gov.sg/datasets/d_c9f57187485a850908655db0e8cfe651/view) |
| HDB renting out of flat approvals, quarterly (2007–2021) | [`d_dad4567fc02596774010f765567780e3`](https://data.gov.sg/datasets/d_dad4567fc02596774010f765567780e3/view) |
| URA private residential transactions, quarterly | [`d_7c69c943d5f0d89d6a9a773d2b51f337`](https://data.gov.sg/datasets/d_7c69c943d5f0d89d6a9a773d2b51f337/view) |
| Census 2020 households by planning area and dwelling type | [`d_388f9c61f437a588b47b008a012d13fa`](https://data.gov.sg/datasets/d_388f9c61f437a588b47b008a012d13fa/view) |
| Real GDP growth (SingStat) | [`d_1f924c084e848ba3a27068d801c43f43`](https://data.gov.sg/datasets/d_1f924c084e848ba3a27068d801c43f43/view) |
| Public holidays | [`d_8ef23381f9417e4d4254ee8b4dcdb176`](https://data.gov.sg/datasets/d_8ef23381f9417e4d4254ee8b4dcdb176/view) |
| Master Plan 2019 region / planning-area boundaries | [`d_bf4d24df9129d5a8ff8cf82e20959ee0`](https://data.gov.sg/datasets/d_bf4d24df9129d5a8ff8cf82e20959ee0/view), [`d_4765db0e87b9c86336792efe8a1f7a66`](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) |
| Rule changes 1989–2026 | [LKY School, *Public Housing in Singapore*](https://lkyspp.nus.edu.sg/docs/default-source/case-studies/public-housing-in-singapore.pdf); [timeline of property cooling measures](https://propertyreviewsg.com/complete-timeline-of-singapores-property-cooling-measures/); [15-month wait-out removed, Jul 2026](https://sg.news.yahoo.com/government-removes-15-month-wait-031926809.html) |
| MOP validation | [OrangeTee, *HDB Market Outlook 2026*](https://www.orangetee.com/ResearchHubFiles/Items/582/20251120141338-7bea9593HDB%20Market%20Outlook%202026_final.pdf) |
| Move prices, truck cost | [Spaceship mover price comparison](https://blog.spaceship.com.sg/comparison-of-mover-price-and-service-in-singapore); [DollarsAndSense commercial vehicle cost guide](https://dollarsandsense.sg/business/cost-guide-to-buying-a-commercial-vehicle-in-singapore/) |

Business assumptions (market share, prices, wages, truck price, subcontractor rates, discount rate) are estimates, not data; every one has a slider in the app and appears in the tornado chart.
