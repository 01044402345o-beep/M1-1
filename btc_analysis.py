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


ANNUALIZATION_DAYS = 365  # 비트코인은 연중무휴 거래되므로 주식의 252가 아니다


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """일별 변화율과 누적 수익률을 추가한다.

    보간된 날짜(is_filled)와 그 다음 날의 수익률은 NaN으로 둔다.
    보간된 가격이 관여한 변화율은 실제 시장 움직임이 아니기 때문이다.
    """
    out = df.copy()
    returns = out["Close"].pct_change(fill_method=None)

    # is_filled.shift(1)은 첫 행에 NaN을 만들어 object dtype이 될 수 있지만,
    # bool 컬럼인 is_filled와 `|` 연산을 거치면 다시 bool dtype으로 수렴한다
    # (pandas 3.0.3에서 확인함). 따라서 별도의 .astype(bool) 가드는 불필요하다.
    unreliable = out["is_filled"] | out["is_filled"].shift(1).fillna(False)
    returns[unreliable] = np.nan
    out["daily_return"] = returns

    # 누적 계산에서는 결측을 '변화 없음'으로 간주해 구간을 이어붙인다.
    out["cum_return"] = (1.0 + returns.fillna(0.0)).cumprod() - 1.0
    return out


def add_moving_averages(df: pd.DataFrame, windows: tuple[int, ...] = (7, 30, 90)) -> pd.DataFrame:
    """종가 이동평균을 추가한다. 단기 노이즈를 걷어내 추세를 분리하기 위한 것이다."""
    out = df.copy()
    for window in windows:
        out[f"ma_{window}"] = out["Close"].rolling(window).mean()
    return out


def add_volatility(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """롤링 표준편차를 연율화해 변동성 컬럼을 추가한다."""
    out = df.copy()
    out[f"vol_{window}"] = out["daily_return"].rolling(window).std() * np.sqrt(ANNUALIZATION_DAYS)
    return out


def detect_return_outliers(df: pd.DataFrame, z_threshold: float = 3.0) -> pd.DataFrame:
    """일별 수익률이 ±z_threshold 표준편차를 벗어난 날을 찾는다.

    탐지만 한다. 제거하지 않는다. 비트코인의 급변동은 측정 오류가 아니라
    분석 대상 신호이므로, 제거하면 변동성 분석의 목적 자체가 훼손된다.
    """
    returns = df["daily_return"]
    z_score = (returns - returns.mean()) / returns.std()
    mask = z_score.abs() > z_threshold

    result = df.loc[mask.fillna(False), ["Close", "daily_return"]].copy()
    result["z_score"] = z_score[mask.fillna(False)]
    return result


def max_drawdown(close: pd.Series) -> dict:
    """최대 낙폭과 그 고점·저점 날짜를 돌려준다.

    하락 리스크의 규모를 단일 수치로 요약하기 위한 지표다.
    """
    running_max = close.cummax()
    drawdown = close / running_max - 1.0

    trough_date = drawdown.idxmin()
    peak_date = close.loc[:trough_date].idxmax()

    return {
        "mdd": float(drawdown.min()),
        "peak_date": peak_date,
        "trough_date": trough_date,
    }


WEEKDAY_NAMES_KO = ["월", "화", "수", "목", "금", "토", "일"]


def monthly_return_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """연도 x 월 형태의 월별 복리 수익률 표를 만든다.

    단순 평균이 아니라 복리로 묶는 이유: 월 수익률은 일별 수익률의 곱으로
    정의되며, 평균을 쓰면 실제 월간 변화와 값이 달라진다.
    """
    returns = df["daily_return"].dropna()
    monthly = returns.groupby([returns.index.year, returns.index.month]).apply(
        lambda s: (1.0 + s).prod() - 1.0
    )
    monthly.index.names = ["year", "month"]
    return monthly.unstack("month")


def weekday_return_table(df: pd.DataFrame) -> pd.DataFrame:
    """요일별 수익률 통계표를 만든다.

    평균만 보면 소수의 극단값에 끌려가므로 중앙값과 표준편차를 함께 낸다.
    비트코인은 연중무휴 거래되므로 주말 행이 비지 않는다 — 주식으로는
    불가능한 분석이다.
    """
    returns = df["daily_return"].dropna()
    grouped = returns.groupby(returns.index.dayofweek).agg(["mean", "median", "std", "count"])
    grouped.index = [WEEKDAY_NAMES_KO[i] for i in grouped.index]
    return grouped.reindex(WEEKDAY_NAMES_KO)


def split_tail(close: pd.Series, horizon: int = 30) -> tuple[pd.Series, pd.Series]:
    """마지막 horizon일을 홀드아웃으로 분리한다.

    학습 구간에 미래 데이터가 섞이지 않도록 시간 순서대로만 자른다.
    """
    if horizon >= len(close):
        raise ValueError(f"horizon({horizon})이 데이터 길이({len(close)}) 이상이다")
    return close.iloc[:-horizon], close.iloc[-horizon:]


def _future_index(train: pd.Series, horizon: int) -> pd.DatetimeIndex:
    start = train.index[-1] + pd.Timedelta(days=1)
    return pd.date_range(start, periods=horizon, freq="D", name="Date")


def forecast_naive(train: pd.Series, horizon: int) -> pd.Series:
    """마지막 관측값을 그대로 유지한다. 가장 단순한 기준선이다."""
    return pd.Series(train.iloc[-1], index=_future_index(train, horizon), name="Naive")


def forecast_moving_average(train: pd.Series, horizon: int, window: int = 7) -> pd.Series:
    """최근 window일 평균값을 유지한다."""
    value = train.iloc[-window:].mean()
    return pd.Series(value, index=_future_index(train, horizon), name=f"이동평균({window}일)")


def forecast_drift(train: pd.Series, horizon: int) -> pd.Series:
    """학습 구간 전체의 평균 일간 변화량을 선형으로 연장한다.

    (마지막값 - 첫값) / (길이 - 1)로 구한 평균 변화량을 그대로 외삽하므로,
    최근 구간의 추세만 보는 것이 아니라 학습 구간 전체 평균 추세를 쓴다.
    """
    slope = (train.iloc[-1] - train.iloc[0]) / (len(train) - 1)
    steps = np.arange(1, horizon + 1)
    return pd.Series(train.iloc[-1] + slope * steps, index=_future_index(train, horizon), name="Drift")


def evaluate_forecast(actual: pd.Series, predicted: pd.Series, origin_value: float) -> dict:
    """MAE, MAPE, 방향 정확도를 계산한다.

    방향 정확도는 예측 시작 시점(origin_value) 대비 상승/하락 부호가
    실제와 일치한 비율이다.

    Naive만 구조적으로 0%가 나온다: Naive의 예측값은 origin_value와 정확히
    같으므로 부호가 항상 0이고, 실제 부호는 +1 또는 -1이므로 둘이 일치할
    수 없다. 반면 이동평균과 Drift는 origin_value와 다른 수준을 예측하므로
    부호가 +1 또는 -1 중 하나로 전체 구간에서 고정된다. 그 결과 이 지표는
    예측 기간 전체에 대해 '단 한 번의 방향 베팅'이 맞았는지를 측정할 뿐,
    일별 방향 예측 능력을 측정하지 않는다 — 따라서 이 지표만으로 모델 간
    우열을 주장해서는 안 된다. 이는 버그가 아니라 지표가 정의대로 작동한
    결과이며, 리포트에 그렇게 서술한다.
    """
    error = (actual - predicted).abs()
    mae = float(error.mean())
    mape = float((error / actual.abs()).mean() * 100)

    actual_direction = np.sign(actual - origin_value)
    predicted_direction = np.sign(predicted - origin_value)
    direction_accuracy = float((actual_direction == predicted_direction).mean() * 100)

    return {"mae": mae, "mape": mape, "direction_accuracy": direction_accuracy}


def run_baselines(close: pd.Series, horizon: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """3개 베이스라인을 학습·예측·평가해 (예측값 표, 평가 표)를 돌려준다."""
    train, test = split_tail(close, horizon)
    origin = float(train.iloc[-1])

    forecasts = [
        forecast_naive(train, horizon),
        forecast_moving_average(train, horizon, window=7),
        forecast_drift(train, horizon),
    ]

    predictions = pd.DataFrame({"actual": test.values}, index=test.index)
    scores = {}
    for forecast in forecasts:
        aligned = pd.Series(forecast.values, index=test.index, name=forecast.name)
        predictions[forecast.name] = aligned
        scores[forecast.name] = evaluate_forecast(test, aligned, origin)

    score_table = pd.DataFrame(scores).T[["mae", "mape", "direction_accuracy"]]
    return predictions, score_table
