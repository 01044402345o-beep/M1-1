"""Yahoo Finance에서 BTC-USD 일봉 데이터를 받아 CSV로 저장한다.

분석 노트북과 분리된 이유: 노트북 실행마다 네트워크에서 데이터를 받으면
실행 시점에 따라 결과가 달라져 재현이 불가능하다. 데이터를 한 번 고정한다.

실행: python fetch_data.py
"""

from pathlib import Path

import yfinance as yf

TICKER = "BTC-USD"
START = "2023-01-01"
END = "2026-10-01"  # yfinance의 end는 미포함이므로 2026-09-30까지 받으려면 10-01을 지정
OUT_PATH = Path("data/btc_usd_2023_2026.csv")


def fetch() -> None:
    df = yf.download(TICKER, start=START, end=END, interval="1d", auto_adjust=False, progress=False)

    if df.empty:
        raise RuntimeError("수집 결과가 비어 있다. 네트워크 상태와 티커를 확인하라.")

    # yfinance는 최근 버전에서 단일 티커에도 MultiIndex 컬럼을 반환한다.
    if df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.index.name = "Date"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, date_format="%Y-%m-%d")

    print(f"저장 완료: {OUT_PATH}")
    print(f"행 수: {len(df)}")
    print(f"기간: {df.index.min().date()} ~ {df.index.max().date()}")
    print(f"컬럼: {list(df.columns)}")


if __name__ == "__main__":
    fetch()
