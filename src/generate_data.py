"""Generate a synthetic car dealer dataset: leads, sales funnel, market totals, stock.

All brands, models, channels and numbers are invented. Nothing here comes from a real company.
"""
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

SEED = 42
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

BRANDS = {
    "Brand A": ["A1 Sedan", "A3 SUV", "A5 EV"],
    "Brand B": ["B2 Hatch", "B4 SUV", "B6 EV"],
    "Brand C": ["C3 SUV", "C7 Pickup"],
}

# monthly base leads, then stage probabilities:
# contacted, visit | contacted, test drive | visit, sale | test drive, duplicate rate
CHANNELS = {
    "Instagram":    (260, 0.85, 0.22, 0.55, 0.35, 0.25),
    "Facebook":     (180, 0.85, 0.20, 0.50, 0.33, 0.22),
    "Classifieds":  (140, 0.80, 0.30, 0.50, 0.30, 0.20),
    "Call center":  (150, 1.00, 0.45, 0.65, 0.45, 0.08),
    "Google Ads":   (120, 0.90, 0.35, 0.60, 0.40, 0.12),
    "Website form": (90,  0.90, 0.40, 0.60, 0.42, 0.10),
    "Walk-in":      (40,  1.00, 1.00, 0.75, 0.50, 0.00),
    "Referral":     (25,  0.95, 0.60, 0.70, 0.55, 0.05),
}

MONTHS = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
SEASONALITY = [0.85, 0.90, 1.10, 1.15, 1.05, 0.95, 0.85, 0.90, 1.10, 1.15, 1.05, 1.00]


def make_leads(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    customer_seq = 0
    model_list = [(b, m) for b, models in BRANDS.items() for m in models]
    model_weights = np.array([0.16, 0.20, 0.08, 0.10, 0.16, 0.07, 0.15, 0.08])

    for month, season in zip(MONTHS, SEASONALITY):
        days_in_month = month.days_in_month
        for channel, (base, p_contact, p_visit, p_test, p_sale, p_dup) in CHANNELS.items():
            n = rng.poisson(base * season)
            for _ in range(n):
                customer_seq += 1
                brand, model = model_list[rng.choice(len(model_list), p=model_weights)]
                created = month + pd.Timedelta(days=int(rng.integers(0, days_in_month)))
                contacted = rng.random() < p_contact
                visited = contacted and rng.random() < p_visit
                test_drive = visited and rng.random() < p_test
                sold = test_drive and rng.random() < p_sale
                sale_date = created + pd.Timedelta(days=int(rng.integers(3, 25))) if sold else pd.NaT
                base_row = dict(
                    customer_id=f"C{customer_seq:06d}", created_at=created, channel=channel,
                    brand=brand, model=model, contacted=contacted, visited=visited,
                    test_drive=test_drive, sold=sold, sale_date=sale_date,
                )
                rows.append(base_row)
                # Duplicates: the same person writes again within a few days, no new outcome.
                if rng.random() < p_dup:
                    for _ in range(int(rng.integers(1, 3))):
                        dup = dict(base_row)
                        dup.update(
                            created_at=created + pd.Timedelta(days=int(rng.integers(0, 4))),
                            contacted=False, visited=False, test_drive=False, sold=False,
                            sale_date=pd.NaT,
                        )
                        rows.append(dup)

    leads = pd.DataFrame(rows).sort_values("created_at").reset_index(drop=True)
    leads.insert(0, "lead_id", [f"L{i:07d}" for i in range(1, len(leads) + 1)])
    return leads


def make_market(rng: np.random.Generator, leads: pd.DataFrame) -> pd.DataFrame:
    sold = leads[leads["sold"]].copy()
    sold["month"] = sold["sale_date"].dt.to_period("M").dt.to_timestamp()
    our = sold.groupby("month").size().reindex(MONTHS, fill_value=0)
    # The market grows faster than our sales in the second half of the year.
    growth = np.concatenate([np.linspace(1.00, 1.05, 6), np.linspace(1.08, 1.30, 6)])
    market = (our.mean() / 0.11) * np.array(SEASONALITY) * growth
    market = np.round(market * rng.normal(1, 0.02, len(MONTHS))).astype(int)
    return pd.DataFrame({"month": MONTHS.strftime("%Y-%m"), "market_units": market})


def make_stock() -> pd.DataFrame:
    targets = [45, 40, 35, 22, 42, 30, 32, 22]  # Q4 sales target per model
    stock = [25, 20, 40, 18, 20, 35, 22, 15]    # units in stock at the end of the year
    pairs = [(b, m) for b, models in BRANDS.items() for m in models]
    return pd.DataFrame(
        [dict(brand=b, model=m, q4_target=t, stock_units=s) for (b, m), t, s in zip(pairs, targets, stock)]
    )


def main() -> None:
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(exist_ok=True)

    leads = make_leads(rng)
    market = make_market(rng, leads)
    stock = make_stock()

    leads.to_csv(DATA_DIR / "leads.csv", index=False)
    market.to_csv(DATA_DIR / "market.csv", index=False)
    stock.to_csv(DATA_DIR / "stock.csv", index=False)

    db_path = DATA_DIR / "dealer.db"
    db_path.unlink(missing_ok=True)
    with sqlite3.connect(db_path) as con:
        leads.assign(
            created_at=leads["created_at"].dt.strftime("%Y-%m-%d"),
            sale_date=leads["sale_date"].dt.strftime("%Y-%m-%d"),
        ).to_sql("leads", con, index=False)
        market.to_sql("market", con, index=False)
        stock.to_sql("stock", con, index=False)

    print(f"leads: {len(leads):,} rows, unique customers: {leads['customer_id'].nunique():,}")
    print(f"sales: {int(leads['sold'].sum()):,}")


if __name__ == "__main__":
    main()
