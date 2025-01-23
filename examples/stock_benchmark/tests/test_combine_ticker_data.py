import pytest
from stock_benchmark.tools.combine_ticker_data import combine_ticker_data
from stock_benchmark.tools.download_ticker import TickerData


@pytest.mark.asyncio
async def test_combine_ticker_data():
    ticker1 = TickerData(closes=[1, 2, 3])
    ticker2 = TickerData(closes=[3, 2, 1])
    result = await combine_ticker_data(
        ticker1=ticker1,
        ticker1_weight=1,
        ticker2=ticker2,
        ticker2_weight=2,
    )()
    assert result.closes == [
        (1 * 1) + (3 * 2),
        (2 * 1) + (2 * 2),
        (3 * 1) + (1 * 2),
    ]
