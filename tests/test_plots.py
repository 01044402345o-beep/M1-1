"""그래프 함수의 스모크 테스트.

그래프의 '보기 좋음'은 자동 검증할 수 없다. 여기서 검증하는 것은
함수가 예외 없이 끝나고 실제로 비어 있지 않은 PNG를 만드는지다.
시각적 품질은 Task 8에서 사람이 직접 확인한다.
"""

import matplotlib

matplotlib.use("Agg")  # 창을 띄우지 않는 백엔드

import numpy as np
import pandas as pd

import btc_analysis as ba
import plots


def sample_df(n=400):
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    rng = np.random.default_rng(42)
    close = 20000 * np.cumprod(1 + rng.normal(0.001, 0.03, n))
    raw = pd.DataFrame(
        {"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close,
         "Volume": np.ones(n) * 1e9},
        index=pd.DatetimeIndex(dates, name="Date"),
    )
    df = ba.add_volatility(ba.add_moving_averages(ba.add_returns(ba.fill_prices(raw))))
    return df


def assert_png_created(path):
    assert path.exists(), f"{path} 가 생성되지 않았다"
    assert path.stat().st_size > 5000, f"{path} 가 너무 작다 (빈 그래프 의심)"


def test_plot_price_trend_creates_png(tmp_path):
    out = plots.plot_price_trend(sample_df(), tmp_path / "01.png")
    assert_png_created(out)


def test_plot_returns_volatility_creates_png(tmp_path):
    out = plots.plot_returns_volatility(sample_df(), tmp_path / "02.png")
    assert_png_created(out)


def test_plot_monthly_heatmap_creates_png(tmp_path):
    pivot = ba.monthly_return_pivot(sample_df())
    out = plots.plot_monthly_heatmap(pivot, tmp_path / "03.png")
    assert_png_created(out)


def test_plot_weekday_box_creates_png(tmp_path):
    out = plots.plot_weekday_box(sample_df(), tmp_path / "04.png")
    assert_png_created(out)


def test_plot_baseline_forecast_creates_png(tmp_path):
    preds, scores = ba.run_baselines(sample_df()["Close"], horizon=30)
    out = plots.plot_baseline_forecast(preds, scores, tmp_path / "05.png")
    assert_png_created(out)
