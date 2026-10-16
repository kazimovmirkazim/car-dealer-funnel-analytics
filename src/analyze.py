"""Run the SQL queries against data/dealer.db, save results to outputs/ and charts to images/."""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR, OUT_DIR, IMG_DIR = ROOT / "sql", ROOT / "outputs", ROOT / "images"

# Chart palette (light surface)
SURFACE = "#fcfcfb"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, NEUTRAL = "#2a78d6", "#eb6834", "#c3c2b7"
CRITICAL = "#d03b3b"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "Segoe UI", "font.size": 12, "text.color": INK,
    "axes.edgecolor": BASELINE, "axes.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def run_queries() -> dict[str, pd.DataFrame]:
    results = {}
    with sqlite3.connect(ROOT / "data" / "dealer.db") as con:
        for path in sorted(SQL_DIR.glob("*.sql")):
            query = path.read_text()
            if "CREATE VIEW" in query:
                con.executescript(query)
                continue
            results[path.stem] = pd.read_sql(query, con)
    OUT_DIR.mkdir(exist_ok=True)
    for name, df in results.items():
        df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return results


def headline(fig, title: str, subtitle: str) -> None:
    fig.text(0.04, 0.95, title, fontsize=18, fontweight="bold", va="top")
    fig.text(0.04, 0.885, subtitle, fontsize=12, color=INK_2, va="top")
    fig.text(0.04, 0.02, "Synthetic data. All brands, models and numbers are invented.",
             fontsize=9, color=MUTED)


def save(fig, name: str) -> None:
    IMG_DIR.mkdir(exist_ok=True)
    fig.savefig(IMG_DIR / name, dpi=100)
    plt.close(fig)


def chart_funnel(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.16, right=0.88, top=0.80, bottom=0.08)
    y = range(len(df))[::-1]
    ax.barh(list(y), df["customers"], color=BLUE, height=0.62)
    ax.set_yticks(list(y), df["stage"], fontsize=13)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    for yi, (_, row) in zip(y, df.iterrows()):
        label = f"{row.customers:,}"
        if pd.notna(row.pct_of_previous):
            label += f"   {row.pct_of_previous:.0f}% of previous step"
        ax.text(row.customers + 120, yi, label, va="center", fontsize=12, color=INK)
    worst = df.loc[df["pct_of_previous"].idxmin()]
    headline(fig, f"The biggest drop is before the showroom: only {worst.pct_of_previous:.0f}% of contacted customers visit",
             f"Lead-to-sale funnel, unique customers, 2025. Overall conversion: {df['pct_of_leads'].iloc[-1]:.1f}%")
    save(fig, "01_funnel.png")


def chart_channels(df: pd.DataFrame) -> None:
    df = df.sort_values("leads")
    top_leads = df.loc[df["leads"].idxmax(), "channel"]
    top_sales = df.loc[df["sales"].idxmax(), "channel"]
    colors = [BLUE if c == top_leads else ORANGE if c == top_sales else NEUTRAL for c in df["channel"]]

    fig, axes = plt.subplots(1, 3, figsize=(16, 9), sharey=True)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.78, bottom=0.08, wspace=0.25)
    panels = [("leads", "Leads", "{:,.0f}"), ("sales", "Sales", "{:,.0f}"),
              ("lead_to_sale_pct", "Lead-to-sale, %", "{:.1f}%")]
    for ax, (col, title, fmt) in zip(axes, panels):
        ax.barh(df["channel"], df[col], color=colors, height=0.62)
        ax.set_title(title, color=INK_2)
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        for yi, v in enumerate(df[col]):
            ax.text(v + df[col].max() * 0.02, yi, fmt.format(v), va="center", fontsize=11, color=INK_2)
        ax.set_xlim(0, df[col].max() * 1.25)
    axes[0].tick_params(axis="y", labelsize=12)
    headline(fig, f"{top_leads} brings the most leads. {top_sales} brings the most buyers.",
             "Volume and conversion are different questions. Unique customers by first channel, 2025.")
    save(fig, "02_channels.png")


def chart_duplicates(df: pd.DataFrame) -> None:
    df = df.sort_values("duplicate_pct")
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.13, right=0.80, top=0.80, bottom=0.10)
    y = range(len(df))
    for yi, (_, row) in zip(y, df.iterrows()):
        ax.plot([row.conversion_raw_pct, row.conversion_dedup_pct], [yi, yi], color=BASELINE, lw=2, zorder=1)
    ax.scatter(df["conversion_raw_pct"], list(y), s=110, color=NEUTRAL, zorder=2, label="Raw rows",
               edgecolor=SURFACE, linewidth=2)
    ax.scatter(df["conversion_dedup_pct"], list(y), s=110, color=BLUE, zorder=3, label="Unique customers",
               edgecolor=SURFACE, linewidth=2)
    ax.set_xscale("log")
    ax.set_xticks([2, 5, 10, 20, 40], ["2%", "5%", "10%", "20%", "40%"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(axis="x", color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.set_yticks(list(y), df["channel"], fontsize=12)
    for yi, (_, row) in zip(y, df.iterrows()):
        ax.text(48, yi, f"{row.duplicate_pct:.0f}% duplicates", va="center", fontsize=11, color=INK_2)
    ax.set_xlim(1.5, 45)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=11)
    ax.set_xlabel("Lead-to-sale conversion (log scale)")
    worst = df.iloc[-1]
    headline(fig, f"Duplicates make {worst.channel} look worse than it is",
             f"Same sales, two denominators: {worst.channel} converts {worst.conversion_raw_pct:.1f}% on raw rows "
             f"and {worst.conversion_dedup_pct:.1f}% on unique customers.")
    save(fig, "03_duplicates.png")


def chart_market_share(df: pd.DataFrame) -> None:
    df = df.copy()
    peak = df.loc[df["share_pct"].idxmax()]
    last = df.iloc[-1]
    pp = last.share_pct - peak.share_pct
    pct = 100 * (last.share_pct / peak.share_pct - 1)
    df["our_index"] = 100 * df["our_units"] / df["our_units"].iloc[0]
    df["market_index"] = 100 * df["market_units"] / df["market_units"].iloc[0]
    months = pd.to_datetime(df["month"]).dt.strftime("%b")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
    fig.subplots_adjust(left=0.06, right=0.95, top=0.76, bottom=0.10, wspace=0.22)

    ax1.plot(months, df["share_pct"], color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    ax1.set_title("Our market share, %", color=INK_2)
    ax1.set_ylim(0, df["share_pct"].max() * 1.3)
    ax1.grid(axis="y", color=GRID, lw=1)
    ax1.set_axisbelow(True)
    for row, va in ((peak, "bottom"), (last, "top")):
        i = df.index[df["month"] == row.month][0] - df.index[0]
        ax1.annotate(f"{row.share_pct:.1f}%", (i, row.share_pct), xytext=(0, 12 if va == "bottom" else -16),
                     textcoords="offset points", ha="center", fontsize=12, fontweight="bold")

    ax2.plot(months, df["market_index"], color=NEUTRAL, lw=2, label="Market")
    ax2.plot(months, df["our_index"], color=BLUE, lw=2, label="Our sales")
    ax2.axhline(100, color=BASELINE, lw=1)
    ax2.set_title(f"Units, index ({months.iloc[0]} = 100)", color=INK_2)
    ax2.grid(axis="y", color=GRID, lw=1)
    ax2.set_axisbelow(True)
    ax2.text(len(df) - 1 + 0.2, df["market_index"].iloc[-1], "Market", va="center", color=INK_2)
    ax2.text(len(df) - 1 + 0.2, df["our_index"].iloc[-1], "Our sales", va="center", color=INK_2)

    headline(fig, f"Share fell {abs(pp):.1f} percentage points, which is a {abs(pct):.0f}% drop",
             f"{peak.share_pct:.1f}% in {pd.to_datetime(peak.month):%B} to {last.share_pct:.1f}% in "
             f"{pd.to_datetime(last.month):%B}. Our sales held up; the market grew faster.")
    save(fig, "04_market_share.png")


def chart_stock(df: pd.DataFrame) -> None:
    df = df.sort_values("target_pct", ascending=False).reset_index(drop=True)
    total_pct = 100 * df["sold_q4"].sum() / df["q4_target"].sum()
    colors = [CRITICAL if f == "behind target, high stock" else BLUE for f in df["flag"]]
    labels = [f"{m}  ({b})" for m, b in zip(df["model"], df["brand"])]

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.17, right=0.80, top=0.80, bottom=0.10)
    y = range(len(df))[::-1]
    ax.barh(list(y), df["target_pct"], color=colors, height=0.62)
    ax.axvline(100, color=INK_2, lw=1, ls="--")
    ax.text(100, len(df) - 0.3, "Target", ha="center", color=INK_2, fontsize=11)
    ax.set_yticks(list(y), labels, fontsize=12)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, 135)
    for yi, (_, row) in zip(y, df.iterrows()):
        ax.text(row.target_pct + 2, yi, f"{row.target_pct:.0f}%  ({row.sold_q4}/{row.q4_target})",
                va="center", fontsize=11, color=INK)
        ax.text(140, yi, f"stock {row.stock_units}", va="center", fontsize=11,
                color=CRITICAL if row.flag == "behind target, high stock" else INK_2,
                fontweight="bold" if row.flag == "behind target, high stock" else "normal")
    n_red = (df["flag"] == "behind target, high stock").sum()
    headline(fig, f"Total plan: {total_pct:.0f}%. But {n_red} models are near half of target with the highest stock",
             "Q4 2025 sales vs target by model. Red: below 70% of target and 30+ units in stock.")
    save(fig, "05_stock_vs_target.png")


def main() -> None:
    r = run_queries()
    chart_funnel(r["02_funnel"])
    chart_channels(r["03_channel_performance"])
    chart_duplicates(r["04_duplicate_effect"])
    chart_market_share(r["05_market_share"])
    chart_stock(r["06_stock_vs_target"])
    print("Saved:", ", ".join(p.name for p in sorted(IMG_DIR.glob("*.png"))))


if __name__ == "__main__":
    main()
