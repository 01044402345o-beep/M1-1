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


def test_add_returns_computes_pct_change():
    df = make_df(["2023-01-01", "2023-01-02", "2023-01-03"], [100.0, 110.0, 99.0])
    df = ba.fill_prices(df)

    out = ba.add_returns(df)

    assert np.isnan(out["daily_return"].iloc[0])  # 첫날은 직전값이 없다
    assert out["daily_return"].iloc[1] == pytest.approx(0.10)
    assert out["daily_return"].iloc[2] == pytest.approx(-0.10)


def test_add_returns_excludes_filled_days_and_next_day():
    # 01-02가 보간된 경우: 01-02와 01-03의 수익률은 모두 신뢰할 수 없다
    df = make_df(["2023-01-01", "2023-01-03"], [100.0, 120.0])
    df, _ = ba.reindex_daily(df)
    df = ba.fill_prices(df)

    out = ba.add_returns(df)

    assert np.isnan(out.loc["2023-01-02", "daily_return"])
    assert np.isnan(out.loc["2023-01-03", "daily_return"])


def test_add_returns_cumulative_is_monotonic_for_rising_prices():
    df = make_df(["2023-01-01", "2023-01-02", "2023-01-03"], [100.0, 110.0, 121.0])
    df = ba.fill_prices(df)

    out = ba.add_returns(df)

    assert out["cum_return"].iloc[0] == pytest.approx(0.0)
    assert out["cum_return"].iloc[2] == pytest.approx(0.21)


def test_add_moving_averages_creates_expected_columns():
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = ba.fill_prices(make_df(dates, np.arange(100, 200, dtype=float)))

    out = ba.add_moving_averages(df, windows=(7, 30, 90))

    assert {"ma_7", "ma_30", "ma_90"} <= set(out.columns)
    assert np.isnan(out["ma_7"].iloc[5])  # 윈도우가 안 찬 구간
    assert out["ma_7"].iloc[6] == pytest.approx(np.mean(np.arange(100, 107)))


def test_add_volatility_is_annualized_with_365():
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    rng = np.random.default_rng(0)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, 60))
    df = ba.add_returns(ba.fill_prices(make_df(dates, close)))

    out = ba.add_volatility(df, window=30)

    expected = out["daily_return"].rolling(30).std().iloc[-1] * np.sqrt(365)
    assert out["vol_30"].iloc[-1] == pytest.approx(expected)
    assert np.isnan(out["vol_30"].iloc[10])


def test_detect_return_outliers_finds_extreme_day():
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    close = np.full(60, 100.0)
    close[1:] = 100.0 * np.cumprod(np.full(59, 1.001))
    close[30] = close[29] * 1.30  # +30% 하루
    close[31:] = close[30] * np.cumprod(np.full(29, 1.001))
    df = ba.add_returns(ba.fill_prices(make_df(dates, close)))

    out = ba.detect_return_outliers(df, z_threshold=3.0)

    assert dates[30] in out.index


def test_detect_return_outliers_does_not_modify_input():
    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    df = ba.add_returns(ba.fill_prices(make_df(dates, np.linspace(100, 140, 40))))
    before = len(df)

    ba.detect_return_outliers(df)

    assert len(df) == before  # 탐지는 제거가 아니다


def test_max_drawdown_finds_largest_peak_to_trough():
    dates = pd.date_range("2023-01-01", periods=5, freq="D")
    close = [100.0, 150.0, 75.0, 120.0, 130.0]
    df = ba.fill_prices(make_df(dates, close))

    result = ba.max_drawdown(df["Close"])

    assert result["mdd"] == pytest.approx(-0.50)  # 150 -> 75
    assert result["peak_date"] == pd.Timestamp("2023-01-02")
    assert result["trough_date"] == pd.Timestamp("2023-01-03")


def test_monthly_return_pivot_compounds_within_month():
    # 1월에 +10%, +10% → 복리 21%
    dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
    df = ba.add_returns(ba.fill_prices(make_df(dates, [100.0, 110.0, 121.0])))

    pivot = ba.monthly_return_pivot(df)

    assert pivot.loc[2023, 1] == pytest.approx(0.21)


def test_monthly_return_pivot_separates_years_and_months():
    dates = ["2023-01-01", "2023-01-02", "2023-02-01", "2024-01-01", "2024-01-02"]
    close = [100.0, 110.0, 110.0, 110.0, 99.0]
    df = ba.add_returns(ba.fill_prices(make_df(dates, close)))

    pivot = ba.monthly_return_pivot(df)

    assert set(pivot.index) == {2023, 2024}
    assert pivot.loc[2023, 1] == pytest.approx(0.10)
    assert pivot.loc[2024, 1] == pytest.approx(-0.10)


def test_weekday_return_table_has_seven_rows_in_week_order():
    dates = pd.date_range("2023-01-02", periods=28, freq="D")  # 2023-01-02는 월요일
    rng = np.random.default_rng(1)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.01, 28))
    df = ba.add_returns(ba.fill_prices(make_df(dates, close)))

    table = ba.weekday_return_table(df)

    assert list(table.index) == ["월", "화", "수", "목", "금", "토", "일"]
    assert list(table.columns) == ["mean", "median", "std", "count"]


def test_weekday_return_table_aggregates_correct_weekday():
    # 2023-01-01은 일요일. 범위 01-01~01-15 안의 월요일은 01-02와 01-09 두 번뿐이고,
    # 그 두 날에만 +10% 수익률이 생기도록 구성한다.
    dates = pd.date_range("2023-01-01", periods=15, freq="D")
    close = np.full(15, 100.0)
    close[1:] = 110.0   # 01-02(월) +10%
    close[8:] = 121.0   # 01-09(월) +10%
    df = ba.add_returns(ba.fill_prices(make_df(dates, close)))

    table = ba.weekday_return_table(df)

    assert table.loc["월", "count"] == 2
    assert table.loc["월", "mean"] == pytest.approx(0.10)
    assert table.loc["화", "mean"] == pytest.approx(0.0)  # 다른 요일은 변화 없음
