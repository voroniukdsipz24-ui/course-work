"""
chart_generator.py
ChartGenerator перетворює PaymentSchedule на фігуру Matplotlib.
Не має залежностей від Qt; результат передається у view як об’єкт Figure.
Кешує останній згенерований результат, щоб уникнути зайвого перемальовування.
"""

from __future__ import annotations
import io
import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.figure import Figure

try:
    import seaborn as sns
    _HAS_SNS = True
except ImportError:
    _HAS_SNS = False

from model import PaymentSchedule

logger = logging.getLogger(__name__)

# ── кольорова палітра графіка ──────────────────────────────────────────────────────
_CHART_BG   = "#080d24"
_CHART_GRID = "#152040"
_C_BALANCE  = "#00e5a0"
_SANS       = "Segoe UI"


def _fmt_dollars(x: float, _) -> str:
    if abs(x) >= 1_000_000:
        return f"{x / 1_000_000:.1f}M"
    if abs(x) >= 10_000:
        return f"{x / 1_000:.0f}K"
    return f"{x:.0f}"


def _style_axes(ax) -> None:
    ax.set_facecolor(_CHART_BG)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(_CHART_GRID)
        ax.spines[spine].set_linewidth(0.8)
    ax.tick_params(colors="#6a90c0", labelsize=8, length=3, width=0.8)
    ax.xaxis.label.set_color("#6a90c0")
    ax.yaxis.label.set_color("#6a90c0")
    ax.grid(axis="y", color=_CHART_GRID, linewidth=0.6, alpha=0.8, zorder=0)
    ax.grid(axis="x", color=_CHART_GRID, linewidth=0.3, alpha=0.4, zorder=0)
    ax.set_axisbelow(True)


class ChartGenerator:
    """
    Створює графік залишку боргу за кредитом для PaymentSchedule.
    Кешує останній результат (schedule_id, fig_w, fig_h) → Figure, щоб уникнути повторного рендерингу.
    """

    def __init__(self) -> None:
        self._cache_key: tuple | None = None
        self._cached_figure: Figure | None = None

    def render(self, schedule: PaymentSchedule,
               fig_w: float = 6.8, fig_h: float = 4.6) -> Figure:
        """
        Повертає фігуру Matplotlib для графіка платежів.
        Повертає кешовану фігуру, якщо ідентичність графіка та розмір не змінилися.
        """
        cache_key = (id(schedule), round(fig_w, 2), round(fig_h, 2))
        if cache_key == self._cache_key and self._cached_figure is not None:
            logger.debug("ChartGenerator: cache hit")
            return self._cached_figure

        logger.debug("ChartGenerator: rendering fig %.2f×%.2f", fig_w, fig_h)
        fig = self._build_figure(schedule, fig_w, fig_h)
        self._cache_key     = cache_key
        self._cached_figure = fig
        return fig

    def invalidate_cache(self) -> None:
        if self._cached_figure is not None:
            try:
                plt.close(self._cached_figure)
            except Exception:
                pass
        self._cache_key     = None
        self._cached_figure = None

    @staticmethod
    def _build_figure(schedule: PaymentSchedule,
                      fig_w: float, fig_h: float) -> Figure:

        months  = [p.month             for p in schedule]
        balance = [p.remaining_balance for p in schedule]
        n       = len(months)

        principal_start = max(
            (balance[0] + schedule.payments[0].principal_part) if n > 0 else 1.0,
            1.0,
        )
        
        months.insert(0, 0)
        balance.insert(0, principal_start)

        # Дублюємо графіки з однією точкою, щоб matplotlib міг намалювати лінію
        if n == 1:
            months  = [0, months[0]]
            balance = [principal_start, balance[0]]

        if _HAS_SNS:
            sns.set_style("darkgrid", {
                "axes.facecolor":   _CHART_BG,
                "figure.facecolor": _CHART_BG,
                "grid.color":       _CHART_GRID,
            })

        fig, ax = plt.subplots(1, 1, figsize=(max(fig_w, 3.0), max(fig_h, 2.5)))
        fig.patch.set_facecolor(_CHART_BG)
        _style_axes(ax)

        ax.fill_between(months, balance, alpha=0.18, color=_C_BALANCE, zorder=2)
        ax.fill_between(months, balance, alpha=0.06, color=_C_BALANCE, zorder=1)
        ax.plot(months, balance, color=_C_BALANCE, linewidth=2.2,
                zorder=4, solid_capstyle="round")

        if len(months) >= 3:
            mid_i   = len(months) // 2
            y_range = max(balance) - min(balance)
            offset  = max(y_range * 0.10, principal_start * 0.06)
            ax.annotate(
                f"  {_fmt_dollars(balance[mid_i], None)}",
                xy=(months[mid_i], balance[mid_i]),
                xytext=(months[mid_i], balance[mid_i] + offset),
                color="#a0e8c8", fontsize=8, fontfamily=_SANS,
                arrowprops=dict(arrowstyle="-", color="#3a7a60", lw=0.8),
                zorder=5,
            )

        ax.scatter([months[0], months[-1]], [balance[0], balance[-1]],
                   color=_C_BALANCE, s=50, zorder=5, linewidths=0)

        ax.set_xlabel("Місяць", fontsize=9, labelpad=8)
        ax.set_ylabel("Залишок боргу", fontsize=9, labelpad=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_dollars))

        y_min, y_max = ax.get_ylim()
        if abs(y_max - y_min) < 1.0:
            ax.set_ylim(0, max(principal_start * 1.1, 1.0))

        x_min, x_max = ax.get_xlim()
        if abs(x_max - x_min) < 0.5:
            ax.set_xlim(months[0] - 0.5, months[-1] + 0.5)

        if len(months) > 60:
            step = max(1, len(months) // 10)
            ax.set_xticks(months[::step])
        ax.tick_params(axis="both", labelsize=8.5)

        ax.set_title("Залишок кредиту", color="#a0c4ff",
                     fontsize=9.5, fontweight="bold",
                     fontfamily=_SANS, pad=7, loc="left")
        ax.axhline(0, color=_CHART_GRID, linewidth=0.8, zorder=0)

        fig.tight_layout(pad=2.4)
        return fig

    @staticmethod
    def figure_to_bytes(fig: Figure, dpi: int = 120) -> bytes:
        """Рендерить фігуру у PNG-байти для експорту або відображення."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf.seek(0)
        return buf.read()
