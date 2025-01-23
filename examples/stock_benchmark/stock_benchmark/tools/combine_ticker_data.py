from stock_benchmark.tools.download_ticker import TickerData

from autoplan.tool import tool


@tool(can_use_prior_results=True)
async def combine_ticker_data(
    ticker1: TickerData | None = None,
    ticker1_weight: float | None = None,
    ticker2: TickerData | None = None,
    ticker2_weight: float | None = None,
    ticker3: TickerData | None = None,
    ticker3_weight: float | None = None,
    ticker4: TickerData | None = None,
    ticker4_weight: float | None = None,
    ticker5: TickerData | None = None,
    ticker5_weight: float | None = None,
) -> TickerData:
    tickers_to_weights = {}

    tickers = [ticker1, ticker2, ticker3, ticker4, ticker5]
    weights = [
        ticker1_weight,
        ticker2_weight,
        ticker3_weight,
        ticker4_weight,
        ticker5_weight,
    ]

    for index, (ticker, weight) in enumerate(zip(tickers, weights)):
        if ticker is not None:
            tickers_to_weights[index] = weight

    data: list[list[(float, weight)]] = []

    for ticker_index, weight in tickers_to_weights.items():
        ticker = tickers[ticker_index]
        for i in range(len(ticker.closes)):
            try:
                data[i]
            except IndexError:
                data.append([])

            data[i].append((ticker.closes[i], weight))
    closes = []
    for i in range(len(data)):
        closes.append(sum([item[0] * item[1] for item in data[i]]))

    return TickerData(name="combined", closes=closes)
