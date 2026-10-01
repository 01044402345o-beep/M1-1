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
