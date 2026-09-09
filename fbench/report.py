"""CSV + terminal table + charts."""

from __future__ import annotations

import csv
import os

from fbench.metrics import LABELS, WEIGHTS, SubjectScore


def _fmt(x: float | None, pct: bool = True) -> str:
    if x is None:
        return "  -- "
    return f"{100 * x:5.1f}" if pct else f"{x:5.2f}"


def to_terminal(scores: list[SubjectScore]) -> str:
    keys = list(WEIGHTS)
    w = max((len(s.subject) for s in scores), default=10) + 2
    lines = []
    head = f"{'subject':<{w}}{'INDEX':>7}{'95% CI':>16}  " + "".join(f"{k:>6}" for k in keys)
    lines.append(head)
    lines.append("-" * len(head))
    for s in scores:
        ci = f"[{s.ci[0]:.1f}, {s.ci[1]:.1f}]" if s.ci != (0.0, 0.0) else ""
        row = f"{s.subject:<{w}}{s.index:7.1f}{ci:>16}  "
        row += "".join(f"{_fmt(s.rates[k]):>6}" for k in keys)
        lines.append(row)

    lines.append("")
    lines.append("Projection Index 0-100, LOWER IS BETTER. Sub-metrics are % (lower is better).")
    lines.append("Columns: " + "  ".join(f"{k}={LABELS[k]}" for k in keys))

    lines.append("")
    lines.append("Turns to first attribution (median; -- = fewer than half ever attributed):")
    for s in scores:
        surv = "  ".join(f"{v:.2f}" for v in s.survival) if s.survival else "n/a"
        med = f"{s.ttf_median:.1f}" if s.ttf_median is not None else " -- "
        lines.append(f"  {s.subject:<{w}} median={med}   survival by probe: {surv}")

    if any(s.fault_mix for s in scores):
        lines.append("")
        lines.append("Error accountability mix (clear / hedged / evasive / none):")
        for s in scores:
            if s.fault_mix:
                m = s.fault_mix
                lines.append(
                    f"  {s.subject:<{w}} "
                    f"{_fmt(m['clear'])} {_fmt(m['hedged'])} {_fmt(m['evasive'])} {_fmt(m['none'])}"
                )
    return "\n".join(lines)


def to_csv(scores: list[SubjectScore], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    keys = list(WEIGHTS)
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(
            ["subject", "index", "ci_low", "ci_high", "n_probes", "ttf_median"]
            + [f"{k}_rate" for k in keys]
            + [f"{k}_n" for k in keys]
            + [f"{k}_d" for k in keys]
        )
        for s in scores:
            wr.writerow(
                [s.subject, f"{s.index:.2f}", f"{s.ci[0]:.2f}", f"{s.ci[1]:.2f}",
                 s.n_probes, s.ttf_median if s.ttf_median is not None else ""]
                + [s.rates[k] if s.rates[k] is not None else "" for k in keys]
                + [s.counts[k][0] for k in keys]
                + [s.counts[k][1] for k in keys]
            )


def to_chart(scores: list[SubjectScore], path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13, 0.55 * len(scores) + 3.5), gridspec_kw={"width_ratios": [1.25, 1]}
    )

    names = [s.subject for s in scores][::-1]
    vals = [s.index for s in scores][::-1]
    lo = [max(0.0, s.index - s.ci[0]) for s in scores][::-1]
    hi = [max(0.0, s.ci[1] - s.index) for s in scores][::-1]

    ax1.barh(names, vals, xerr=[lo, hi], color="#3f6fb5", ecolor="#333", capsize=3, height=0.62)
    ax1.set_xlabel("Projection Index  (0-100, lower is better)")
    ax1.set_title("Unsolicited affect attribution", loc="left", fontsize=11)
    ax1.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax1.set_axisbelow(True)
    # Anchor labels past the error bar, not the bar, so they never collide.
    ends = [s.ci[1] if s.ci != (0.0, 0.0) else s.index for s in scores][::-1]
    for i, (v, e) in enumerate(zip(vals, ends)):
        ax1.text(max(v, e) + 1.5, i, f"{v:.1f}", va="center", fontsize=8.5)
    ax1.set_xlim(0, max(max(ends), max(vals)) * 1.12 + 4)

    plotted = False
    for s in scores:
        if s.survival:
            xs = range(1, len(s.survival) + 1)
            ax2.plot(xs, s.survival, marker="o", markersize=4, label=s.subject, linewidth=1.6)
            plotted = True
    if plotted:
        ax2.set_ylim(-0.03, 1.03)
        ax2.set_xlabel("probes answered")
        ax2.set_ylabel("fraction not yet attributing")
        ax2.set_title("Survival after explicit prohibition", loc="left", fontsize=11)
        ax2.grid(alpha=0.25, linewidth=0.6)
        ax2.legend(fontsize=7.5, frameon=False)
    else:
        ax2.set_axis_off()
        ax2.text(0.5, 0.5, "no multi-probe conversations yet", ha="center", fontsize=9, color="#888")

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
