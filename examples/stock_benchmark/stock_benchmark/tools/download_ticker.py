import yfinance as yf
from pydantic import BaseModel

from autoplan.tool import tool


class TickerData(BaseModel):
    name: str
    closes: list[float]


@tool
async def download_ticker(ticker: str) -> TickerData:
    """
    Given a ticker, download the data from yfinance for the past 5 years in monthly frequency.
    """
    data = yf.download(ticker, period="5y", interval="1mo")
    return TickerData(
        name=ticker,
        closes=[cell[0] for cell in data["Close"].values.tolist()],
    )
