import numpy as np
import pandas as pd
import pytest

import btc_analysis as ba
import dashboard_core as dc

CSV_PATH = "data/btc_usd_2023_2026.csv"


def make_prices(dates, close):
    """테스트용 최소 프레임.

    `ba.fill_prices` 를 거쳐 반환한다 — `recompute_indicators` 가 실제로 받는 것이
    `load_prepared`(= ... → fill_prices) 의 출력이므로, 픽스처도 같은 형태여야 한다.
    `is_filled` 를 손으로 적어 넣지 않고 함수를 통과시키는 이유는, fill_prices 가
    바뀌면 픽스처가 자동으로 따라가게 하기 위해서다.
    """
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="Date")
    close = np.asarray(close, dtype=float)
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.001,
            "Low": close * 0.999,
            "Close": close,
            "Volume": np.ones(len(close)) * 100.0,
        },
        index=idx,
    )
    return ba.fill_prices(frame)


def test_load_prepared_returns_cleaned_frame():
    df = dc.load_prepared(CSV_PATH)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    assert "is_filled" in df.columns
    assert "daily_return" not in df.columns  # 수익률은 구간 확정 후에 계산한다
    assert len(df) == 1368


def test_slice_period_includes_both_endpoints():
    df = make_prices(pd.date_range("2023-01-01", periods=10, freq="D"), np.arange(100, 110))

    out = dc.slice_period(df, "2023-01-03", "2023-01-05")

    assert len(out) == 3
    assert out.index.min() == pd.Timestamp("2023-01-03")
    assert out.index.max() == pd.Timestamp("2023-01-05")


def test_slice_period_accepts_timestamps_and_dates():
    df = make_prices(pd.date_range("2023-01-01", periods=5, freq="D"), np.arange(100, 105))

    a = dc.slice_period(df, pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-04"))
    b = dc.slice_period(df, "2023-01-02", "2023-01-04")

    assert len(a) == len(b) == 3


def test_recompute_indicators_is_local_to_the_slice():
    # 100일 선형 상승 뒤 슬라이스를 뒤쪽 40일만 잡는다.
    # 전 구간에서 계산한 뒤 잘랐다면 슬라이스 첫 행의 ma_7 이 값을 가지지만,
    # 슬라이스에서 재계산했다면 윈도가 차지 않아 NaN 이어야 한다.
    full = make_prices(pd.date_range("2023-01-01", periods=100, freq="D"),
                       np.arange(100.0, 200.0))
    sliced = dc.slice_period(full, "2023-02-25", "2023-04-05")

    out = dc.recompute_indicators(sliced, ma_windows=(7, 30, 90), vol_window=30)

    assert np.isnan(out["ma_7"].iloc[0])
    assert out["ma_7"].iloc[6] == pytest.approx(out["Close"].iloc[:7].mean())


def test_recompute_indicators_cum_return_starts_from_slice():
    full = make_prices(pd.date_range("2023-01-01", periods=5, freq="D"),
                       [100.0, 200.0, 220.0, 242.0, 266.2])
    sliced = dc.slice_period(full, "2023-01-02", "2023-01-05")

    out = dc.recompute_indicators(sliced, ma_windows=(2,), vol_window=5)

    # 200 -> 266.2 은 +33.1%. 100 에서부터 세면 +166% 가 되므로 구간 기준임을 확인한다.
    assert out["cum_return"].iloc[-1] == pytest.approx(0.331)


def test_recompute_indicators_adds_requested_columns():
    df = make_prices(pd.date_range("2023-01-01", periods=60, freq="D"),
                     np.linspace(100, 160, 60))

    out = dc.recompute_indicators(df, ma_windows=(5, 20), vol_window=10)

    assert {"daily_return", "cum_return", "ma_5", "ma_20", "vol_10"} <= set(out.columns)


def test_recompute_indicators_short_slice_leaves_indicators_empty():
    df = make_prices(pd.date_range("2023-01-01", periods=5, freq="D"),
                     [100.0, 101.0, 102.0, 103.0, 104.0])

    out = dc.recompute_indicators(df, ma_windows=(30,), vol_window=30)

    assert out["ma_30"].isna().all()
    assert out["vol_30"].isna().all()
