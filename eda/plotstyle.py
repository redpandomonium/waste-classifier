"""Shared look for the EDA figures, so every chart reads as one set."""

from pathlib import Path

import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).resolve().parent / "figures"

# Colour follows the thing, not the chart: a class or a split keeps its colour everywhere.
ORGANIC, RECYCLABLE = "#1baf7a", "#2a78d6"
CLASS_COLORS = {"Organic": ORGANIC, "Recyclable": RECYCLABLE}
TRAIN, VAL, TEST = "#8a8985", "#6250d6", "#eb6834"
SPLIT_COLORS = {"TRAIN": TRAIN, "VAL": VAL, "TEST": TEST}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.labelcolor": MUTED, "text.color": INK,
        "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False,
        "lines.linewidth": 2,
    })


def save(fig, name: str) -> None:
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / name)


def label_bars(ax, bars, fmt="{:,.0f}", horizontal=False, pad=3) -> None:
    for bar in bars:
        if horizontal:
            ax.annotate(fmt.format(bar.get_width()),
                        (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                        xytext=(pad, 0), textcoords="offset points",
                        va="center", ha="left", color=INK, fontsize=9)
        else:
            ax.annotate(fmt.format(bar.get_height()),
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, pad), textcoords="offset points",
                        va="bottom", ha="center", color=INK, fontsize=9)
