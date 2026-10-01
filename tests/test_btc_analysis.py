import numpy as np
import pandas as pd
import pytest

import btc_analysis as ba


def make_df(dates, close, open_=None, high=None, low=None, volume=None):
    """테스트용 최소 DataFrame. 지정하지 않은 컬럼은 close에서 파생한다."""
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="Date")
    close = np.asarray(close, dtype=float)
    return pd.DataFrame(
        {
            "Open": close if open_ is None else open_,
            "High": close if high is None else high,
            "Low": close if low is None else low,
            "Close": close,
            "Volume": np.ones(len(close)) * 100 if volume is None else volume,
        },
        index=idx,
    )


def test_load_raw_parses_dates_and_sorts(tmp_path):
    csv = tmp_path / "x.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume\n"
        "2023-01-03,3,3,3,3,10\n"
        "2023-01-01,1,1,1,1,10\n"
        "2023-01-02,2,2,2,2,10\n",
        encoding="utf-8",
    )

    df = ba.load_raw(csv)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.name == "Date"
    assert list(df["Close"]) == [1.0, 2.0, 3.0]  # 정렬됨
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_find_invalid_rows_flags_nonpositive_price():
    df = make_df(["2023-01-01", "2023-01-02"], [100.0, 0.0])

    invalid = ba.find_invalid_rows(df)

    assert len(invalid) == 1
    assert invalid.index[0] == pd.Timestamp("2023-01-02")


def test_find_invalid_rows_flags_high_below_low():
    df = make_df(["2023-01-01"], [100.0], high=[90.0], low=[110.0])

    invalid = ba.find_invalid_rows(df)

    assert len(invalid) == 1


def test_find_invalid_rows_flags_extreme_jump_over_50pct():
    # 100 -> 200 은 +100% 이므로 오류로 간주한다
    df = make_df(["2023-01-01", "2023-01-02"], [100.0, 200.0])

    invalid = ba.find_invalid_rows(df)

    assert pd.Timestamp("2023-01-02") in invalid.index


def test_find_invalid_rows_keeps_large_but_plausible_move():
    # -20% 는 비트코인에서 실제로 발생하는 값이므로 오류가 아니다
    df = make_df(["2023-01-01", "2023-01-02"], [100.0, 80.0])

    invalid = ba.find_invalid_rows(df)

    assert len(invalid) == 0


def test_drop_invalid_rows_removes_only_invalid():
    # 가운데 행만 High < Low 로 모순. 가격 자체는 연속적이라 변동률 검사가
    # 인접 행으로 번지지 않는다 (0 이나 결측을 쓰면 다음 행까지 같이 걸린다).
    df = make_df(
        ["2023-01-01", "2023-01-02", "2023-01-03"],
        [100.0, 102.0, 105.0],
        high=[101.0, 95.0, 106.0],
        low=[99.0, 103.0, 104.0],
    )

    clean = ba.drop_invalid_rows(df)

    assert len(clean) == 2
    assert pd.Timestamp("2023-01-02") not in clean.index


def test_reindex_daily_reports_missing_dates():
    df = make_df(["2023-01-01", "2023-01-02", "2023-01-05"], [100.0, 101.0, 104.0])

    filled, missing = ba.reindex_daily(df)

    assert len(filled) == 5  # 01-01 ~ 01-05
    assert list(missing) == [pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
    assert filled.loc["2023-01-03", "Close"] != filled.loc["2023-01-03", "Close"]  # NaN


def test_reindex_daily_with_no_gaps_reports_empty():
    df = make_df(["2023-01-01", "2023-01-02"], [100.0, 101.0])

    filled, missing = ba.reindex_daily(df)

    assert len(filled) == 2
    assert len(missing) == 0


def test_fill_prices_forward_fills_and_marks():
    df = make_df(["2023-01-01", "2023-01-02", "2023-01-03"], [100.0, 101.0, 102.0])
    df, _ = ba.reindex_daily(df.drop(index=pd.Timestamp("2023-01-02")))

    out = ba.fill_prices(df)

    assert out.loc["2023-01-02", "Close"] == 100.0  # 직전 종가 유지
    assert bool(out.loc["2023-01-02", "is_filled"]) is True
    assert bool(out.loc["2023-01-01", "is_filled"]) is False
    assert out["Close"].isna().sum() == 0
