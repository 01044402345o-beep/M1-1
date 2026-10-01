"""BTC-USD 일봉 데이터의 정제·지표·집계·예측 함수.

모든 함수는 순수 함수다. 네트워크 접근, 파일 쓰기, 그래프 생성을 하지 않는다.
이유: 계산 로직을 노트북 셀에서 분리해 pytest로 검증 가능하게 만든다.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PRICE_COLUMNS = ["Open", "High", "Low", "Close"]
MAX_PLAUSIBLE_DAILY_CHANGE = 0.50  # 전일 대비 절대 변동률 상한. 초과 시 데이터 오류로 간주


def load_raw(csv_path: str | Path) -> pd.DataFrame:
    """CSV를 읽어 날짜 인덱스를 가진 DataFrame으로 돌려준다."""
    df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    df = df.sort_index()
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def find_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 오류로 판단되는 행을 찾는다.

    기준 (설계 문서 4.2절):
      1. 가격이 0 이하
      2. High < Low
      3. 전일 대비 절대 변동률이 50% 초과

    주의: 이것은 '이상치 제거'가 아니다. 비트코인의 -20% 급락 같은 극단값은
    분석 대상 신호이므로 보존한다. 여기서 걸러내는 것은 물리적으로 불가능하거나
    논리적으로 모순된 값, 즉 수집 오류다.
    """
    nonpositive = (df[PRICE_COLUMNS] <= 0).any(axis=1)
    inverted = df["High"] < df["Low"]
    # pandas 3.0: pct_change()의 fill_method 기본값이 None으로 바뀌어(과거 'pad'),
    # 결측을 자동으로 메우지 않는다. 결측 구간을 변동률로 오인하지 않으려면
    # fill_method=None을 명시해 결측은 그대로 NaN으로 남기고, 아래에서 fillna(False)로
    # '오류 아님'으로 처리한다 (결측은 find_invalid_rows의 책임이 아니라 reindex_daily의 몫).
    jump = df["Close"].pct_change(fill_method=None).abs() > MAX_PLAUSIBLE_DAILY_CHANGE

    # pandas 3.0 Copy-on-Write 환경에서 bool Series를 안전하게 결합하기 위해
    # fillna(False) 전에 dtype을 명시적으로 bool로 맞춘다 (object로 업캐스트되는 것을 방지).
    jump = jump.fillna(False).astype(bool)

    return df[nonpositive | inverted | jump]


def drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """find_invalid_rows가 찾은 행을 제거한다."""
    invalid = find_invalid_rows(df)
    return df.drop(index=invalid.index)


def reindex_daily(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """전체 날짜 범위로 재색인하고, 원본에 없던 날짜를 함께 돌려준다.

    결측을 조용히 넘기지 않고 명시적으로 드러내기 위한 단계다.
    """
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="D", name="Date")
    missing = full_index.difference(df.index)
    return df.reindex(full_index), missing


def fill_prices(df: pd.DataFrame) -> pd.DataFrame:
    """가격 컬럼을 ffill로 채우고 보간 여부를 is_filled에 기록한다.

    ffill을 쓰는 이유: 거래 기록이 없는 날은 '값이 없는' 것이 아니라
    '직전 가격이 유지된' 상태로 보는 것이 금융 시계열의 관례다.
    is_filled를 남기는 이유: 보간된 날의 수익률(0%)을 통계에서 제외해야
    변동성이 과소추정되지 않는다.
    """
    # pandas 3.0은 Copy-on-Write가 기본이라 df.copy() 없이 슬라이스를 직접
    # 수정하면 원본에 반영되지 않거나 경고가 날 수 있다. 명시적으로 복사해
    # out이 df와 독립된 객체임을 보장한다 (순수 함수 계약 유지).
    out = df.copy()
    out["is_filled"] = out["Close"].isna()
    out[PRICE_COLUMNS] = out[PRICE_COLUMNS].ffill()
    return out
