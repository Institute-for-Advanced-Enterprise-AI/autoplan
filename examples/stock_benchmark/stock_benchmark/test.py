import pandas as pd
import yfinance as yf
from pydantic import BaseModel


def download_ticker(ticker: str) -> pd.DataFrame:
    return yf.download(ticker, period="5y", interval="1mo")


def combine_ticker_data(
    ticker1: pd.DataFrame | None,
    ticker1_weight: float,
    ticker2: pd.DataFrame | None,
    ticker2_weight: float,
    ticker3: pd.DataFrame | None,
    ticker3_weight: float,
    ticker4: pd.DataFrame | None,
    ticker4_weight: float,
    ticker5: pd.DataFrame | None,
    ticker5_weight: float,
) -> pd.DataFrame:
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

    reduced_data = pd.DataFrame()
    for ticker_index, weight in tickers_to_weights.items():
        ticker = tickers[ticker_index]
        if isinstance(ticker.columns, pd.MultiIndex):
            ticker.columns = ticker.columns.get_level_values(0)

        for column in ticker.columns:
            if column in reduced_data.columns:
                reduced_data[column] = reduced_data[column] + (ticker[column] * weight)
            else:
                reduced_data[column] = ticker[column] * weight
    return reduced_data


class Statistics(BaseModel):
    one_month_return: float
    one_year_return: float
    five_year_return: float
    volatility: float


def calculate_statistics(data: pd.DataFrame) -> Statistics:
    # Calculate returns over different time periods
    prices = data["Close"]

    # Calculate period returns
    one_month_return = (prices.iloc[-1] / prices.iloc[-2] - 1) * 100
    one_year_return = (prices.iloc[-1] / prices.iloc[-12] - 1) * 100
    five_year_return = (prices.iloc[-1] / prices.iloc[-60] - 1) * 100

    # Calculate volatility using monthly returns
    monthly_returns = prices.pct_change()
    volatility = monthly_returns.std() * (12**0.5) * 100  # Annualized volatility

    return Statistics(
        one_month_return=one_month_return,
        one_year_return=one_year_return,
        five_year_return=five_year_return,
        volatility=volatility,
    )
