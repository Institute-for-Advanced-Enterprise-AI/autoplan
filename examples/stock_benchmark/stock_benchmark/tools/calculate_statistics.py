from pydantic import BaseModel
from stock_benchmark.tools.download_ticker import TickerData
from autoplan.tool import tool
import numpy as np
import pandas as pd
from autoplan.tool import tool


class Statistics(BaseModel):
    name: str
    one_month_return: float
    one_year_return: float
    five_year_return: float
    volatility: float
    sharpe_ratio: float | None


def sharpe_ratio(returns, N, rf=0):
    mean = returns.mean() * N - rf
    sigma = returns.std() * np.sqrt(N)
    return mean / sigma


@tool(can_use_prior_results=True)
async def calculate_statistics(data: TickerData) -> Statistics:
    """
    Calculate key performance metrics for a ticker or combined ticker data.

    This tool is used to analyze the performance of a stock ticker or custom benchmark by calculating
    returns over different time periods and volatility. It should be used after downloading ticker
    data or combining multiple tickers into a custom benchmark.

    The data parameter must be a PriorResult object that references the output of a previous 
    download_ticker or combine_ticker_data step. For example:
        data=PriorResult(index=x) where x is the index of the step that produced the data

    Args:
        data: TickerData from a prior step containing closing prices

    Returns:
        Statistics: Object containing calculated statistics including:
            - name: Name of the ticker/benchmark
            - one_month_return: Percentage return over last month
            - one_year_return: Percentage return over last year  
            - five_year_return: Percentage return over last 5 years
            - volatility: Standard deviation of monthly returns
    """
    # Calculate returns over different time periods
    prices = data.closes

    # Calculate period returns
    one_month_return = (prices[-1] / prices[-min(2, len(prices))] - 1) * 100
    one_year_return = (prices[-1] / prices[-min(12, len(prices))] - 1) * 100
    five_year_return = (prices[-1] / prices[-min(60, len(prices))] - 1) * 100

    # Calculate volatility using monthly returns
    volatility = 0

    for i in range(1, len(prices)):
        monthly_return = (prices[i] / prices[i - 1] - 1) * 100
        volatility += monthly_return**2

    volatility = (volatility / len(prices)) ** 0.5 * 100


    N = min(12, len(prices))
    df = pd.DataFrame(prices).tail(N).pct_change().dropna()
    rf = 0.01
    sharpes = df.apply(sharpe_ratio, args=(N, rf), axis=0)


    return Statistics(
        name=data.name,
        one_month_return=one_month_return,
        one_year_return=one_year_return,
        five_year_return=five_year_return,
        volatility=volatility,
        sharpe_ratio=sharpes.values[0],
    )

