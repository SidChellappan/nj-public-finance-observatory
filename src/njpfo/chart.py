"""Build the single public reported-net-debt chart."""

from __future__ import annotations

import math
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

from . import TARGET_MUNICIPALITIES, TARGET_YEARS

COLORS = {
    "1103": "#0f766e",
    "1107": "#c2410c",
    "1111": "#334155",
    "1113": "#7c3aed",
    "1114": "#b45309",
}
LINESTYLES = {
    "1103": "-",
    "1107": "--",
    "1111": "-.",
    "1113": ":",
    "1114": (0, (5, 2, 1, 2)),
}
MARKERS = {
    "1103": "o",
    "1107": "s",
    "1111": "^",
    "1113": "D",
    "1114": "P",
}


def publication_chart_data(panel: pd.DataFrame) -> pd.DataFrame:
    chart = panel.copy()
    chart.loc[~chart["publication_eligible_net_debt"], "net_debt"] = math.nan
    return chart


def build_chart(panel: pd.DataFrame, destination: Path) -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#94a3b8",
            "axes.labelcolor": "#334155",
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "svg.hashsalt": "njpfo-v0.1",
        }
    )
    chart = publication_chart_data(panel)
    figure, axis = plt.subplots(figsize=(11.4, 6.4), constrained_layout=True)
    figure.patch.set_facecolor("#fffdf8")
    axis.set_facecolor("#fffdf8")

    for code, name in TARGET_MUNICIPALITIES.items():
        group = (
            chart[chart["municipality_code"] == code]
            .set_index("budget_year")
            .reindex(TARGET_YEARS)
        )
        axis.plot(
            TARGET_YEARS,
            group["net_debt"] / 1_000_000,
            label=name,
            color=COLORS[code],
            linestyle=LINESTYLES[code],
            marker=MARKERS[code],
            markersize=5.5,
            markeredgecolor="#fffdf8",
            markeredgewidth=0.8,
            linewidth=2.2,
        )

    axis.set_title(
        "Reported municipal net debt, 2015-2025\n"
        "Nominal dollars · read each series within municipality",
        loc="left",
        fontsize=16,
        color="#172554",
        pad=16,
    )
    axis.set_xlabel("Budget year", labelpad=10)
    axis.set_ylabel("Reported net debt (nominal dollars, millions)", labelpad=12)
    axis.set_xticks(TARGET_YEARS)
    axis.tick_params(axis="x", rotation=45)
    axis.yaxis.set_major_locator(MultipleLocator(25))
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}M"))
    axis.grid(axis="y", color="#dbe4e8", linewidth=0.8)
    axis.grid(axis="x", visible=False)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(
        loc="upper left",
        frameon=False,
        ncol=3,
        borderaxespad=0,
        bbox_to_anchor=(0, 1.0),
    )
    axis.margins(x=0.02)

    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        destination,
        format="svg",
        facecolor=figure.get_facecolor(),
        metadata={
            "Title": (
                "Reported municipal net debt, 2015-2025 — nominal dollars"
            ),
            "Description": (
                "Line chart for Hamilton, Lawrence, Trenton, West Windsor, "
                "and Princeton. Nominal dollars as reported for each budget "
                "year; not adjusted for inflation or converted to a common-year "
                "dollar basis. Read each series as a within-municipality record "
                "over time. Differences in line height are not measures of "
                "relative debt burden or fiscal strength. Missing, source-flagged, "
                "and unreconciled observations appear as gaps."
            ),
            "Creator": "NJ Public Finance Observatory v0.1",
            "Date": None,
        },
    )
    plt.close(figure)

    text = destination.read_text(encoding="utf-8")
    title = (
        "<title id=\"chart-title\">Reported municipal net debt, "
        "2015-2025 — nominal dollars</title>"
    )
    description = (
        "<desc id=\"chart-desc\">Five municipal series. Nominal dollars as "
        "reported for each budget year; not adjusted for inflation or converted "
        "to a common-year dollar basis. Read each series as a within-municipality "
        "record over time. Differences in line height between municipalities are "
        "not measures of relative debt burden, fiscal strength, or a better or "
        "worse fiscal position. Missing, source-flagged, and unreconciled "
        "observations are shown as visible gaps; no values are interpolated.</desc>"
    )
    text = re.sub(
        r"(<svg\b[^>]*>)",
        r"\1\n " + title + "\n " + description,
        text,
        count=1,
    )
    text = text.replace(
        "<svg ",
        '<svg role="img" aria-labelledby="chart-title chart-desc" ',
        1,
    )
    destination.write_text(text, encoding="utf-8", newline="\n")
