"""Render the public 32K-only reference comparison; no API calls or secrets."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from verify_result_artifacts import ROOT, load, verify_all


def main():
    verify_all()
    data = load(ROOT / "assets/factcon_32k_comparison.json")
    result = load(ROOT / data["continuum_summary"])["results"]["continuum"]
    rows = [{"name": "Continuum", "sh": result["single_hop"]["accuracy"] * 100,
             "mh": result["multi_hop"]["accuracy"] * 100}, *data["baselines"]]
    for filename in ("segoeui.ttf", "segoeuib.ttf"):
        font = Path("C:/Windows/Fonts") / filename
        if font.exists():
            font_manager.fontManager.addfont(str(font))
    family = "Segoe UI" if Path("C:/Windows/Fonts/segoeui.ttf").exists() else "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "font.size": 12, "axes.unicode_minus": False})
    bg, ink, muted, orange = "#F7F6F2", "#252923", "#63706B", "#C44920"
    fig = plt.figure(figsize=(16, 10), facecolor=bg)
    fig.text(.055, .948, "CONTINUUM  /  FACTCONSOLIDATION", fontsize=13, color=orange, weight="bold")
    fig.text(.055, .887, "Memory that keeps up with changing facts.", fontsize=29, color=ink, weight="bold")
    fig.text(.055, .846, "32K context • 200 official questions • SubEM scoring • Replication: September 28, 2026",
             fontsize=13, color=muted)
    for x, key, title in ((.055, "single_hop", "SINGLE-HOP"), (.36, "multi_hop", "MULTI-HOP"), (.665, "overall", "OVERALL")):
        score = result[key]
        fig.text(x, .751, f"{score['accuracy'] * 100:.0f}%", fontsize=41, weight="bold", color=orange)
        fig.text(x + .095, .767, title, fontsize=12, weight="bold", color=ink)
        fig.text(x + .095, .741, f"{score['correct']} / {score['total']} correct", fontsize=12, color=muted)
    for panel, (key, title, subtitle) in enumerate((
            ("sh", "Single-hop", "Find the current fact after updates"),
            ("mh", "Multi-hop", "Connect facts across an updated chain"))):
        ax = fig.add_axes([.205 + panel * .425, .18, .31, .47], facecolor=bg)
        values = [r[key] for r in rows]
        ax.barh(range(len(rows)), values, height=.58,
                color=[orange] + ["#8A9690"] * (len(rows) - 1), zorder=3)
        ax.set_yticks(range(len(rows)), [r["name"] for r in rows] if panel == 0 else [])
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100%"])
        ax.tick_params(axis="both", length=0, colors=muted, labelsize=11, pad=10)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="x", color="#DDDCD5", linewidth=.7, zorder=0)
        ax.set_axisbelow(True)
        ax.text(0, 1.13, title, transform=ax.transAxes, fontsize=19, weight="bold", color=ink)
        ax.text(0, 1.07, subtitle, transform=ax.transAxes, fontsize=11, color=muted)
        for i, value in enumerate(values):
            ax.text(value + 1.6, i, f"{value:g}%", va="center", fontsize=12,
                    color=orange if i == 0 else ink, weight="bold" if i == 0 else "normal")
        if panel == 0:
            ax.get_yticklabels()[0].set_color(orange)
            ax.get_yticklabels()[0].set_weight("bold")
    fig.text(.055, .095, "Orange: Continuum replication   •   Grey: published paper reference results",
             fontsize=12, color=ink)
    fig.text(.055, .064, "Different models / protocols; not a same-run A/B. Continuum: GLM 5.3, retained-corpus API replay.",
             fontsize=11, color=muted)
    fig.text(.055, .035, "Sources: MemoryAgentBench v3, Tables 5 & 10  •  Full methodology: github.com/syntarus12/evals",
             fontsize=11, color=muted)
    output = ROOT / "assets/continuum-factcon-32k.png"
    fig.savefig(output, dpi=180, facecolor=bg)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
