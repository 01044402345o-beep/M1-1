"""대시보드의 순수 로직.

Streamlit 스크립트는 런타임에 묶여 있어 단위 테스트가 사실상 불가능하다.
그래서 파라미터 검증·구간 슬라이싱·분석 호출 오케스트레이션을 이 모듈로 분리하고,
`dashboard.py`는 위젯과 렌더링만 담당한다. 노트북 셀을 테스트할 수 없어
`btc_analysis.py`를 분리했던 것과 같은 이유다.

계산은 하지 않는다. 전부 `btc_analysis`에 위임한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import btc_analysis as ba


def load_prepared(csv_path: str | Path) -> pd.DataFrame:
    """CSV를 읽어 정제까지만 마친 프레임을 돌려준다.

    수익률은 여기서 계산하지 않는다. 구간이 바뀌면 누적 수익률도 달라져야 하므로
    슬라이싱 이후(`recompute_indicators`)에 계산한다.
    """
    df = ba.load_raw(csv_path)
    df = ba.drop_invalid_rows(df)
    df, _ = ba.reindex_daily(df)
    return ba.fill_prices(df)


def slice_period(df: pd.DataFrame, start, end) -> pd.DataFrame:
    """선택 구간을 양끝 포함해 잘라낸다."""
    return df.loc[pd.Timestamp(start):pd.Timestamp(end)]


def recompute_indicators(
    df: pd.DataFrame, ma_windows: tuple[int, ...], vol_window: int
) -> pd.DataFrame:
    """슬라이스 데이터만으로 지표를 다시 계산한다.

    전 구간에서 계산한 뒤 잘라 보여주지 않는 이유: 30일 이동평균을 전 구간에서
    계산한 뒤 2024년만 잘라 보면 그 값에는 2023년 데이터가 섞여 있다. 사용자가
    "2024년의 30일 이동평균"을 보고 있다고 믿는 것과 다르다.
    """
    out = ba.add_returns(df)
    out = ba.add_moving_averages(out, windows=tuple(ma_windows))
    return ba.add_volatility(out, window=vol_window)


MIN_TRAIN_DAYS = 2  # forecast_drift 의 기울기가 (마지막-첫값)/(길이-1) 이라 1일이면 0으로 나눈다


def summarize_period(df: pd.DataFrame, vol_window: int) -> dict:
    """선택 구간의 요약 통계를 돌려준다."""
    if df.empty:
        raise ValueError("빈 구간은 요약할 수 없다")

    outliers = ba.detect_return_outliers(df, z_threshold=3.0)
    drawdown = ba.max_drawdown(df["Close"])
    vol_col = f"vol_{vol_window}"

    return {
        "n_days": int(len(df)),
        "cum_return": float(df["cum_return"].iloc[-1]),
        "mdd": float(drawdown["mdd"]),
        "mdd_peak": drawdown["peak_date"],
        "mdd_trough": drawdown["trough_date"],
        "vol_mean": float(df[vol_col].mean()) if vol_col in df else float("nan"),
        "outlier_down": int((outliers["daily_return"] < 0).sum()),
        "outlier_up": int((outliers["daily_return"] > 0).sum()),
    }


def evaluate_holdout_window(
    close: pd.Series, holdout_start, horizon: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """임의 시작일의 홀드아웃으로 베이스라인 3종을 재평가한다.

    `run_baselines` 는 시리즈의 마지막 horizon 일을 홀드아웃으로 자른다. 따라서
    종가를 holdout_start + horizon - 1 까지 잘라서 넘기면 그 구간이 자동으로
    "마지막 horizon 일"이 된다. REPORT.md 7.4절의 반사실 검증과 같은 절차다.
    """
    holdout_start = pd.Timestamp(holdout_start)
    holdout_end = holdout_start + pd.Timedelta(days=horizon - 1)

    if holdout_end > close.index.max():
        raise ValueError(
            f"홀드아웃 종료일 {holdout_end.date()} 가 데이터 끝 {close.index.max().date()} 를 넘는다"
        )

    truncated = close.loc[:holdout_end]
    train_days = len(truncated) - horizon
    if train_days < MIN_TRAIN_DAYS:
        raise ValueError(
            f"학습 구간이 {train_days}일뿐이다. 최소 {MIN_TRAIN_DAYS}일이 필요하다"
        )

    return ba.run_baselines(truncated, horizon=horizon)


DEFAULT_MA_WINDOWS = (7, 30, 90)
DEFAULT_VOL_WINDOW = 30
DEFAULT_HORIZON = 30
MA_WINDOW_RANGE = (2, 200)
VOL_WINDOW_RANGE = (5, 120)
HORIZON_RANGE = (7, 90)


@dataclass(frozen=True)
class DashboardState:
    """화면이 그릴 내용을 결정하는 상태. 불변이다."""

    start: pd.Timestamp
    end: pd.Timestamp
    ma_windows: tuple[int, ...]
    vol_window: int
    holdout_start: pd.Timestamp
    horizon: int


def _as_date(value, fallback: pd.Timestamp) -> pd.Timestamp:
    """날짜로 못 읽으면 fallback 을 쓴다. 예외를 던지지 않는다."""
    if value is None:
        return fallback
    try:
        parsed = pd.Timestamp(value)
    except (ValueError, TypeError):
        return fallback
    return fallback if pd.isna(parsed) else parsed.normalize()


def _as_int(value, fallback: int, bounds: tuple[int, int]) -> int:
    """정수로 못 읽으면 fallback, 읽히면 범위로 자른다."""
    low, high = bounds
    try:
        number = int(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return fallback
    return max(low, min(high, number))


def parse_params(raw: dict, data_start, data_end) -> DashboardState:
    """URL 쿼리/위젯 입력을 검증·보정해 DashboardState 로 만든다.

    잘못된 입력에 예외를 던지지 않고 기본값으로 떨어진다. URL 은 사람이 손으로
    고칠 수 있고 캡처 스크립트가 만들기도 하므로, 오타 하나로 화면이 죽는 것보다
    안전한 값으로 보정되는 쪽이 낫다.
    """
    data_start = pd.Timestamp(data_start).normalize()
    data_end = pd.Timestamp(data_end).normalize()

    start = _as_date(raw.get("start"), data_start)
    end = _as_date(raw.get("end"), data_end)
    if start > end:
        start, end = end, start
    start = min(max(start, data_start), data_end)
    end = min(max(end, data_start), data_end)

    windows = tuple(
        _as_int(raw.get(key), default, MA_WINDOW_RANGE)
        for key, default in zip(("ma1", "ma2", "ma3"), DEFAULT_MA_WINDOWS)
    )
    ma_windows = tuple(sorted(set(windows)))

    vol_window = _as_int(raw.get("vol"), DEFAULT_VOL_WINDOW, VOL_WINDOW_RANGE)
    horizon = _as_int(raw.get("horizon"), DEFAULT_HORIZON, HORIZON_RANGE)

    latest_holdout = data_end - pd.Timedelta(days=horizon - 1)
    earliest_holdout = data_start + pd.Timedelta(days=MIN_TRAIN_DAYS)
    holdout_start = _as_date(raw.get("holdout"), latest_holdout)
    holdout_start = min(max(holdout_start, earliest_holdout), latest_holdout)

    return DashboardState(
        start=start,
        end=end,
        ma_windows=ma_windows,
        vol_window=vol_window,
        holdout_start=holdout_start,
        horizon=horizon,
    )
