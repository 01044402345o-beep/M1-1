"""대시보드의 순수 로직.

Streamlit 스크립트는 런타임에 묶여 있어 단위 테스트가 사실상 불가능하다.
그래서 파라미터 검증·구간 슬라이싱·분석 호출 오케스트레이션을 이 모듈로 분리하고,
`dashboard.py`는 위젯과 렌더링만 담당한다. 노트북 셀을 테스트할 수 없어
`btc_analysis.py`를 분리했던 것과 같은 이유다.

계산은 하지 않는다. 전부 `btc_analysis`에 위임한다.
"""

from __future__ import annotations

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
