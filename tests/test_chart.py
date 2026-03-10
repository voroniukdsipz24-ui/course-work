import pytest
from matplotlib.figure import Figure

from model import PaymentSchedule, Payment
from chart_generator import ChartGenerator

# ═══════════════════════════════════════════════════════════════════════════════
# CHART GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestChartGenerator:

    def test_render_returns_figure(self, chart_generator, small_schedule):
        from matplotlib.figure import Figure
        fig = chart_generator.render(small_schedule)
        assert isinstance(fig, Figure)

    def test_cache_hit_returns_same_object(self, chart_generator, small_schedule):
        fig1 = chart_generator.render(small_schedule, fig_w=6.8, fig_h=4.6)
        fig2 = chart_generator.render(small_schedule, fig_w=6.8, fig_h=4.6)
        assert fig1 is fig2

    def test_different_size_produces_different_figure(
            self, chart_generator, small_schedule):
        fig1 = chart_generator.render(small_schedule, fig_w=6.8, fig_h=4.6)
        fig2 = chart_generator.render(small_schedule, fig_w=8.0, fig_h=5.0)
        assert fig1 is not fig2

    def test_invalidate_cache_resets_state(self, chart_generator, small_schedule):
        chart_generator.render(small_schedule)
        chart_generator.invalidate_cache()
        assert chart_generator._cache_key is None
        assert chart_generator._cached_figure is None

    def test_after_invalidate_new_figure_created(self, chart_generator, small_schedule):
        fig1 = chart_generator.render(small_schedule)
        chart_generator.invalidate_cache()
        fig2 = chart_generator.render(small_schedule)
        assert fig1 is not fig2

    def test_figure_to_bytes_returns_png(self, chart_generator, small_schedule):
        fig = chart_generator.render(small_schedule)
        data = ChartGenerator.figure_to_bytes(fig)
        assert isinstance(data, bytes)
        # PNG сигнатури
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

    def test_render_single_payment_schedule(self, chart_generator):
        s = PaymentSchedule()
        s.append(Payment(1, 5000.0, 100.0, 5100.0, 0.0))
        from matplotlib.figure import Figure
        fig = chart_generator.render(s)
        assert isinstance(fig, Figure)

    def test_render_large_schedule(self, chart_generator):
        """Швидкий тест для графіка на 360 місяців (30-річна іпотека)"""
        s = PaymentSchedule()
        balance = 500_000.0
        for i in range(1, 361):
            s.append(Payment(i, 800.0, 300.0, 1100.0, max(balance - 800.0 * i, 0.0)))
        from matplotlib.figure import Figure
        fig = chart_generator.render(s)
        assert isinstance(fig, Figure)