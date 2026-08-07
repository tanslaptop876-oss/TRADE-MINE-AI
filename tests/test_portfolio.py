import pytest

from app.services.portfolio import Portfolio


def test_buy_tracks_average_price_cash_and_journal():
    portfolio = Portfolio(100000, max_position_pct=0.50)
    portfolio.buy("TCS", 10, 1000)
    portfolio.buy("TCS", 10, 1200)

    position = portfolio.positions["TCS"]
    assert position.quantity == 20
    assert position.average_price == 1100
    assert portfolio.cash == 78000
    assert len(portfolio.journal) == 2


def test_sell_tracks_realized_pnl():
    portfolio = Portfolio(100000, max_position_pct=0.50)
    portfolio.buy("RELIANCE", 20, 1000)
    trade = portfolio.sell("RELIANCE", 5, 1100)

    assert trade.realized_pnl == 500
    assert portfolio.realized_pnl() == 500
    assert portfolio.positions["RELIANCE"].quantity == 15


def test_unrealized_pnl_and_equity():
    portfolio = Portfolio(100000, max_position_pct=0.50)
    portfolio.buy("TCS", 10, 1000)

    assert portfolio.unrealized_pnl({"TCS": 1100}) == 1000
    assert portfolio.equity({"TCS": 1100}) == 101000


def test_position_risk_limit_blocks_concentration():
    portfolio = Portfolio(100000, max_position_pct=0.20)
    portfolio.buy("TCS", 10, 1000)

    with pytest.raises(ValueError, match="risk limit"):
        portfolio.buy("TCS", 11, 1000)


def test_cannot_sell_more_than_position():
    portfolio = Portfolio(100000)
    portfolio.buy("TCS", 5, 1000)

    with pytest.raises(ValueError, match="cannot sell"):
        portfolio.sell("TCS", 6, 1100)


def test_summary_reports_portfolio_state():
    portfolio = Portfolio(100000, max_position_pct=0.50)
    portfolio.buy("TCS", 10, 1000)
    portfolio.sell("TCS", 2, 1200)

    summary = portfolio.summary({"TCS": 1100})
    assert summary["equity"] == 101200
    assert summary["realized_pnl"] == 400
    assert summary["unrealized_pnl"] == 800
    assert summary["open_positions"] == 1
    assert summary["trades"] == 2
