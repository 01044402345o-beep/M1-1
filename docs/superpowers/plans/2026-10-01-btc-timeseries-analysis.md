# 비트코인 시계열 분석 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 비트코인(BTC-USD) 2023-01-01~2026-09-30 일봉 데이터를 수집·정제·분석하여, 시각화 5개와 인사이트 3개 이상을 담은 `REPORT.md`를 완성하고 GitHub에 업로드한다.

**Architecture:** 데이터 수집(`fetch_data.py`)과 분석 로직(`btc_analysis.py`)을 분리하고, 분석 로직은 DataFrame을 받아 DataFrame을 돌려주는 순수 함수로 구성해 pytest로 검증한다. `analysis.ipynb`는 이 모듈을 import하여 실행·시각화만 담당하고, 계산 로직을 직접 포함하지 않는다. 시각화는 `plots.py`에 분리하여 PNG 파일로 저장한다.

**Tech Stack:** Python 3.14 (실패 시 3.12 venv), pandas, numpy, matplotlib, yfinance, pytest, jupyter

**Spec:** `docs/superpowers/specs/2026-10-01-btc-timeseries-analysis-design.md`

## Global Constraints

- Python 3.10 이상 (현재 환경 3.14.4). 패키지 휠 미제공으로 설치 실패 시 Python 3.12 venv로 전환하고 그 사실과 이유를 README에 기록한다.
- 분석 대상: `BTC-USD`, 기간 `2023-01-01` ~ `2026-09-30`, 일(日) 주기.
- 데이터 출처: Yahoo Finance. **개인·비상업 용도 제한** 문구를 `README.md`와 `REPORT.md`에 모두 명시한다.
- `analysis.ipynb`는 네트워크에 접근하지 않는다. `data/btc_usd_2023_2026.csv`만 읽는다.
- 모든 그래프는 한글 레이블을 사용하고, matplotlib 폰트를 `Malgun Gothic`으로 설정하며 `axes.unicode_minus = False`를 지정한다 (음수 기호 깨짐 방지).
- 이상치는 **탐지하되 제거하지 않는다.** 예외: 가격 ≤ 0, 전일 대비 절대 변동률 > 50%, `High < Low` 인 행만 데이터 오류로 제거한다.
- 결측 보간은 가격에만 `ffill`을 적용하고, 보간된 날짜가 관여한 수익률은 `NaN`으로 둔다.
- 리포트의 모든 수치는 실제 실행 출력에서 가져온다. 추정값이나 예시값을 쓰지 않는다.
- 리포트는 관찰(Fact)과 해석(Why)을 분리해 서술한다. 특정 뉴스·사건과 연결한 서술은 가설로 표기하고 `(검증 필요)`를 붙인다.
- 리포트에 투자 권유가 아님을 명시한다.
- 변동성 연율화 계수는 `sqrt(365)`를 사용한다 (주식의 252가 아님 — 비트코인은 연중무휴 거래).

---

## File Structure

| 파일 | 책임 |
| --- | --- |
| `requirements.txt` | 의존성 버전 고정 |
| `fetch_data.py` | yfinance로 데이터 수집 → `data/btc_usd_2023_2026.csv` 저장. 단독 실행 전용 |
| `btc_analysis.py` | 정제·지표·집계·예측 순수 함수. 네트워크·파일 저장·그래프 없음 |
| `plots.py` | `btc_analysis.py` 결과를 받아 PNG 5개 생성. 계산 로직 없음 |
| `tests/test_btc_analysis.py` | `btc_analysis.py` 함수 단위 테스트 (합성 데이터 사용) |
| `tests/test_plots.py` | `plots.py` 스모크 테스트 (파일 생성 여부) |
| `analysis.ipynb` | 모듈 호출, 수치 출력, 그래프 저장. 계산 로직 없음 |
| `REPORT.md` | 분석 리포트 |
| `README.md` | 실행 방법, 재현 절차, 라이선스 주의 |

`btc_analysis.py`를 한 파일로 두는 이유: 함수 15개 내외의 소규모이고 전부 "하나의 DataFrame을 변환한다"는 단일 책임을 공유한다. 레이어별로 쪼개면 import만 늘고 응집도가 떨어진다.

---

## Task 1: 개발 환경 구성

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py` (빈 파일)
- Create: `check_env.py`

**Interfaces:**
- Consumes: 없음
- Produces: 설치된 pandas / numpy / matplotlib / yfinance / pytest / jupyter 환경. 이후 모든 태스크가 이에 의존한다.

- [ ] **Step 1: 패키지 설치**

```bash
python -m pip install --upgrade pip
python -m pip install pandas numpy matplotlib yfinance pytest jupyter
```

설치가 실패하면(휠 미제공 오류) 중단하고 Python 3.12로 가상환경을 만든 뒤 재시도한다:

```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install pandas numpy matplotlib yfinance pytest jupyter
```

3.12로 전환했다면 이후 모든 `python` 명령을 `.venv/Scripts/python.exe`로 바꿔 실행하고, 그 사실을 Task 10의 README에 기록한다.

- [ ] **Step 2: 환경 확인 스크립트 작성**

`check_env.py`:

```python
"""설치된 패키지 버전과 한글 폰트 사용 가능 여부를 확인한다."""

import sys

import matplotlib
import numpy
import pandas
import yfinance
from matplotlib import font_manager

print(f"python     {sys.version.split()[0]}")
print(f"pandas     {pandas.__version__}")
print(f"numpy      {numpy.__version__}")
print(f"matplotlib {matplotlib.__version__}")
print(f"yfinance   {yfinance.__version__}")

installed = {f.name for f in font_manager.fontManager.ttflist}
if "Malgun Gothic" in installed:
    print("font       Malgun Gothic 사용 가능")
else:
    candidates = sorted(n for n in installed if "Gothic" in n or "Gulim" in n or "Batang" in n)
    print(f"font       Malgun Gothic 없음. 대체 후보: {candidates}")
```

- [ ] **Step 3: 실행하여 버전 확인**

Run: `python check_env.py`
Expected: 각 패키지 버전이 출력되고, 폰트 줄에 `Malgun Gothic 사용 가능`이 표시된다.

`Malgun Gothic 없음`이 출력되면 대체 후보 중 하나를 골라 Task 7의 폰트 설정값을 그 이름으로 바꾼다. 후보가 비어 있으면 Task 7에서 `matplotlib`의 기본 폰트를 쓰고 그래프 레이블을 영문으로 작성한다.

- [ ] **Step 4: requirements.txt 작성**

Step 3에서 출력된 **실제 버전**으로 아래 `X.Y.Z` 자리를 채운다. 추정값을 쓰지 않는다.

```
pandas==X.Y.Z
numpy==X.Y.Z
matplotlib==X.Y.Z
yfinance==X.Y.Z
pytest==X.Y.Z
jupyter==X.Y.Z
```

- [ ] **Step 5: tests 패키지 생성**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 6: pytest가 동작하는지 확인**

Run: `python -m pytest tests/ -q`
Expected: `no tests ran` (수집 오류 없이 정상 종료). 오류가 나면 pytest 설치를 재확인한다.

- [ ] **Step 7: 커밋**

```bash
git add requirements.txt check_env.py tests/__init__.py
git commit -m "chore: 개발 환경 구성 및 의존성 버전 고정"
```

---

## Task 2: 데이터 수집 스크립트

**Files:**
- Create: `fetch_data.py`
- Create (출력): `data/btc_usd_2023_2026.csv`

**Interfaces:**
- Consumes: Task 1의 yfinance
- Produces: `data/btc_usd_2023_2026.csv` — 첫 컬럼이 `Date`(YYYY-MM-DD), 이어서 `Open,High,Low,Close,Volume`. Task 3의 `load_raw()`가 이 형식을 읽는다.

- [ ] **Step 1: 수집 스크립트 작성**

`fetch_data.py`:

```python
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
    if isinstance(df.columns, type(df.columns)) and df.columns.nlevels > 1:
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
```

- [ ] **Step 2: 실행하여 데이터 수집**

Run: `python fetch_data.py`
Expected: `저장 완료`, 행 수가 **1,300 이상**(약 1,370), 기간이 `2023-01-01 ~ 2026-09-30` 근처로 출력된다.

행 수가 1,300 미만이거나 기간이 크게 다르면 멈추고 원인을 보고한다. 미션의 "100개 이상" 요건은 충족하지만 설계 가정이 깨진 것이므로 임의로 진행하지 않는다.

- [ ] **Step 3: CSV 앞부분을 눈으로 확인**

Run: `head -3 data/btc_usd_2023_2026.csv`
Expected: 첫 줄이 `Date,Open,High,Low,Close,Volume`, 둘째 줄이 `2023-01-01,...` 형태. 컬럼명이 비어 있거나 `Price`, `Ticker` 같은 줄이 섞여 있으면 MultiIndex 처리가 실패한 것이므로 Step 1의 컬럼 평탄화 코드를 수정한다.

- [ ] **Step 4: 커밋**

```bash
git add fetch_data.py data/btc_usd_2023_2026.csv
git commit -m "feat: BTC-USD 일봉 데이터 수집 스크립트 및 원본 데이터 추가"
```

---

## Task 3: 데이터 로드 및 정제 함수

**Files:**
- Create: `btc_analysis.py`
- Create: `tests/test_btc_analysis.py`

**Interfaces:**
- Consumes: Task 2의 CSV 형식 (`Date,Open,High,Low,Close,Volume`)
- Produces:
  - `load_raw(csv_path: str | Path) -> pd.DataFrame` — `DatetimeIndex`(name=`Date`), 컬럼 `Open/High/Low/Close/Volume`, 날짜 오름차순 정렬
  - `find_invalid_rows(df: pd.DataFrame) -> pd.DataFrame` — 데이터 오류 행만 담은 DataFrame
  - `drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame` — 오류 행 제거 결과
  - `reindex_daily(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DatetimeIndex]` — (전체 날짜로 재색인된 DataFrame, 누락 날짜 인덱스)
  - `fill_prices(df: pd.DataFrame) -> pd.DataFrame` — 가격 `ffill` 적용, `is_filled`(bool) 컬럼 추가

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_btc_analysis.py`:

```python
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
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'btc_analysis'`

- [ ] **Step 3: 최소 구현 작성**

`btc_analysis.py`:

```python
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
    jump = df["Close"].pct_change().abs() > MAX_PLAUSIBLE_DAILY_CHANGE

    return df[nonpositive | inverted | jump.fillna(False)]


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
    out = df.copy()
    out["is_filled"] = out["Close"].isna()
    out[PRICE_COLUMNS] = out[PRICE_COLUMNS].ffill()
    return out
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: PASS — 9 passed

- [ ] **Step 5: 실제 데이터에 적용하여 결측·오류 건수 확인**

Run:

```bash
python -c "import btc_analysis as ba; df=ba.load_raw('data/btc_usd_2023_2026.csv'); print('행수', len(df)); print('오류행', len(ba.find_invalid_rows(df))); d=ba.drop_invalid_rows(df); r,m=ba.reindex_daily(d); print('누락날짜', len(m), list(m[:10])); f=ba.fill_prices(r); print('보간건수', int(f[\"is_filled\"].sum()))"
```

Expected: 행수 1,300 이상. 출력된 **오류행 / 누락날짜 / 보간건수를 기록해 둔다** — Task 9의 리포트 "데이터 정제 과정" 절에 실제 수치로 들어간다.

오류행이 0이 아니면 해당 날짜와 값을 확인해 실제로 수집 오류인지 검토한 뒤 보고한다.

- [ ] **Step 6: 커밋**

```bash
git add btc_analysis.py tests/test_btc_analysis.py
git commit -m "feat: 데이터 로드 및 결측·오류 정제 함수 추가"
```

---

## Task 4: 수익률·이동평균·변동성 지표 함수

**Files:**
- Modify: `btc_analysis.py` (함수 추가)
- Modify: `tests/test_btc_analysis.py` (테스트 추가)

**Interfaces:**
- Consumes: Task 3의 `fill_prices()` 출력 (`Close`, `is_filled` 포함)
- Produces:
  - `add_returns(df) -> pd.DataFrame` — `daily_return`, `cum_return` 컬럼 추가
  - `add_moving_averages(df, windows=(7, 30, 90)) -> pd.DataFrame` — `ma_7`, `ma_30`, `ma_90` 추가
  - `add_volatility(df, window=30) -> pd.DataFrame` — `vol_30` 추가 (연율화)
  - `detect_return_outliers(df, z_threshold=3.0) -> pd.DataFrame` — 극단 수익률 일자 목록
  - `max_drawdown(close: pd.Series) -> dict` — `{"mdd": float, "peak_date": Timestamp, "trough_date": Timestamp}`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_btc_analysis.py` 끝에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: FAIL — `AttributeError: module 'btc_analysis' has no attribute 'add_returns'`

- [ ] **Step 3: 최소 구현 작성**

`btc_analysis.py` 끝에 추가:

```python
ANNUALIZATION_DAYS = 365  # 비트코인은 연중무휴 거래되므로 주식의 252가 아니다


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """일별 변화율과 누적 수익률을 추가한다.

    보간된 날짜(is_filled)와 그 다음 날의 수익률은 NaN으로 둔다.
    보간된 가격이 관여한 변화율은 실제 시장 움직임이 아니기 때문이다.
    """
    out = df.copy()
    returns = out["Close"].pct_change()

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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: PASS — 17 passed

- [ ] **Step 5: 실제 데이터로 주요 수치 산출**

Run:

```bash
python -c "
import btc_analysis as ba
df = ba.fill_prices(ba.reindex_daily(ba.drop_invalid_rows(ba.load_raw('data/btc_usd_2023_2026.csv')))[0])
df = ba.add_volatility(ba.add_moving_averages(ba.add_returns(df)))
print('기간', df.index.min().date(), '~', df.index.max().date(), '행수', len(df))
print('시작가 %.2f 종료가 %.2f' % (df['Close'].iloc[0], df['Close'].iloc[-1]))
print('전체 수익률 %.1f%%' % (df['cum_return'].iloc[-1]*100))
print('일평균 수익률 %.4f%% 일변동성 %.2f%%' % (df['daily_return'].mean()*100, df['daily_return'].std()*100))
print('연율 변동성 평균 %.1f%% 최대 %.1f%%' % (df['vol_30'].mean()*100, df['vol_30'].max()*100))
print('변동성 최고일', df['vol_30'].idxmax().date())
mdd = ba.max_drawdown(df['Close'])
print('MDD %.1f%% (%s -> %s)' % (mdd['mdd']*100, mdd['peak_date'].date(), mdd['trough_date'].date()))
o = ba.detect_return_outliers(df)
print('이상치(3시그마) %d일' % len(o))
print(o.sort_values('daily_return').head(5))
print(o.sort_values('daily_return').tail(5))
"
```

Expected: 모든 수치가 출력된다. **이 출력 전체를 보존한다** — Task 9의 인사이트 근거 수치가 여기서 나온다.

- [ ] **Step 6: 커밋**

```bash
git add btc_analysis.py tests/test_btc_analysis.py
git commit -m "feat: 수익률·이동평균·변동성·MDD 지표 함수 추가"
```

---

## Task 5: 월별·요일별 집계 함수

**Files:**
- Modify: `btc_analysis.py`
- Modify: `tests/test_btc_analysis.py`

**Interfaces:**
- Consumes: Task 4의 `add_returns()` 출력 (`daily_return` 포함)
- Produces:
  - `monthly_return_pivot(df) -> pd.DataFrame` — index=연도(int), columns=월(1~12 int), 값=해당 월 복리 수익률(소수)
  - `weekday_return_table(df) -> pd.DataFrame` — index=요일 한글명(월~일 순서), 컬럼 `mean`, `median`, `std`, `count`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_btc_analysis.py` 끝에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: FAIL — `AttributeError: module 'btc_analysis' has no attribute 'monthly_return_pivot'`

- [ ] **Step 3: 최소 구현 작성**

`btc_analysis.py` 끝에 추가:

```python
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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: PASS — 21 passed

`test_weekday_return_table_aggregates_correct_weekday`의 `count == 3` 단정이 실패하면, 실제 월요일 개수를 세어 기대값을 맞춘 뒤 다시 실행한다 (테스트 데이터의 날짜 범위 계산 실수일 뿐 구현 문제가 아니다).

- [ ] **Step 5: 실제 데이터로 집계 결과 산출**

Run:

```bash
python -c "
import pandas as pd, btc_analysis as ba
pd.set_option('display.width', 200)
df = ba.fill_prices(ba.reindex_daily(ba.drop_invalid_rows(ba.load_raw('data/btc_usd_2023_2026.csv')))[0])
df = ba.add_returns(df)
p = ba.monthly_return_pivot(df)
print('=== 월별 수익률 (%) ===')
print((p*100).round(1))
print()
print('=== 월별 평균 (연도 평균, %) ===')
print((p.mean()*100).round(1))
print()
print('=== 월별 부호 일관성 (양수 연도 수 / 전체) ===')
print(p.apply(lambda c: f'{int((c>0).sum())}/{int(c.notna().sum())}'))
print()
print('=== 요일별 (%) ===')
w = ba.weekday_return_table(df)
print((w[['mean','median','std']]*100).round(3).join(w[['count']]))
"
```

Expected: 월별 표와 요일별 표가 출력된다. **출력을 보존한다.** Q3·Q4의 근거 수치다.

판단 지침: 월별 부호 일관성이 대부분 `2/4` 또는 `3/4` 수준이라면 **"월 효과는 확인되지 않았다"가 정직한 결론**이다. 억지로 패턴을 주장하지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add btc_analysis.py tests/test_btc_analysis.py
git commit -m "feat: 월별·요일별 수익률 집계 함수 추가"
```

---

## Task 6: 베이스라인 예측 및 평가 함수

**Files:**
- Modify: `btc_analysis.py`
- Modify: `tests/test_btc_analysis.py`

**Interfaces:**
- Consumes: Task 3의 `fill_prices()` 출력 (`Close` 포함)
- Produces:
  - `split_tail(close: pd.Series, horizon: int = 30) -> tuple[pd.Series, pd.Series]` — (train, test)
  - `forecast_naive(train: pd.Series, horizon: int) -> pd.Series`
  - `forecast_moving_average(train: pd.Series, horizon: int, window: int = 7) -> pd.Series`
  - `forecast_drift(train: pd.Series, horizon: int) -> pd.Series`
  - `evaluate_forecast(actual: pd.Series, predicted: pd.Series, origin_value: float) -> dict` — `{"mae", "mape", "direction_accuracy"}`
  - `run_baselines(close: pd.Series, horizon: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]` — (예측값 표, 평가 표)

예측 시리즈는 모두 test 구간과 동일한 `DatetimeIndex`를 가진다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_btc_analysis.py` 끝에 추가:

```python
def _close(n, start=100.0, step=1.0):
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.Series(start + step * np.arange(n), index=dates, name="Close")


def test_split_tail_separates_last_n_days():
    close = _close(100)

    train, test = ba.split_tail(close, horizon=30)

    assert len(train) == 70
    assert len(test) == 30
    assert train.index.max() < test.index.min()  # 미래 데이터 누수 없음


def test_split_tail_raises_when_horizon_too_large():
    close = _close(10)

    with pytest.raises(ValueError):
        ba.split_tail(close, horizon=10)


def test_forecast_naive_repeats_last_value():
    train = _close(50)  # 마지막 값 149.0

    pred = ba.forecast_naive(train, horizon=5)

    assert len(pred) == 5
    assert (pred == 149.0).all()
    assert pred.index[0] == train.index[-1] + pd.Timedelta(days=1)


def test_forecast_moving_average_repeats_window_mean():
    train = _close(50)

    pred = ba.forecast_moving_average(train, horizon=3, window=7)

    assert pred.iloc[0] == pytest.approx(train.iloc[-7:].mean())
    assert pred.nunique() == 1  # 상수 예측


def test_forecast_drift_extends_average_slope():
    train = _close(50, step=2.0)  # 하루 +2.0 추세

    pred = ba.forecast_drift(train, horizon=3)

    assert pred.iloc[0] == pytest.approx(train.iloc[-1] + 2.0)
    assert pred.iloc[2] == pytest.approx(train.iloc[-1] + 6.0)


def test_evaluate_forecast_computes_mae_and_mape():
    idx = pd.date_range("2023-01-01", periods=2, freq="D")
    actual = pd.Series([100.0, 200.0], index=idx)
    predicted = pd.Series([110.0, 180.0], index=idx)

    result = ba.evaluate_forecast(actual, predicted, origin_value=100.0)

    assert result["mae"] == pytest.approx(15.0)       # (10 + 20) / 2
    assert result["mape"] == pytest.approx(10.0)      # (10% + 10%) / 2


def test_evaluate_forecast_direction_accuracy_counts_matching_sign():
    idx = pd.date_range("2023-01-01", periods=2, freq="D")
    actual = pd.Series([110.0, 90.0], index=idx)      # 기준 100 대비 상승, 하락
    predicted = pd.Series([105.0, 95.0], index=idx)   # 상승, 하락 → 둘 다 맞음

    result = ba.evaluate_forecast(actual, predicted, origin_value=100.0)

    assert result["direction_accuracy"] == pytest.approx(100.0)


def test_evaluate_forecast_flat_prediction_has_zero_direction_accuracy():
    # 상수 예측은 방향을 주장하지 않으므로 구조적으로 0이 된다.
    # 이 성질 자체를 리포트에서 베이스라인의 한계로 서술한다.
    idx = pd.date_range("2023-01-01", periods=2, freq="D")
    actual = pd.Series([110.0, 90.0], index=idx)
    predicted = pd.Series([100.0, 100.0], index=idx)

    result = ba.evaluate_forecast(actual, predicted, origin_value=100.0)

    assert result["direction_accuracy"] == pytest.approx(0.0)


def test_run_baselines_returns_three_models():
    close = _close(120)

    preds, scores = ba.run_baselines(close, horizon=30)

    assert list(scores.index) == ["Naive", "이동평균(7일)", "Drift"]
    assert list(scores.columns) == ["mae", "mape", "direction_accuracy"]
    assert list(preds.columns) == ["actual", "Naive", "이동평균(7일)", "Drift"]
    assert len(preds) == 30
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_btc_analysis.py -q`
Expected: FAIL — `AttributeError: module 'btc_analysis' has no attribute 'split_tail'`

- [ ] **Step 3: 최소 구현 작성**

`btc_analysis.py` 끝에 추가:

```python
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
    """최근 추세의 평균 변화량을 선형 연장한다."""
    slope = (train.iloc[-1] - train.iloc[0]) / (len(train) - 1)
    steps = np.arange(1, horizon + 1)
    return pd.Series(train.iloc[-1] + slope * steps, index=_future_index(train, horizon), name="Drift")


def evaluate_forecast(actual: pd.Series, predicted: pd.Series, origin_value: float) -> dict:
    """MAE, MAPE, 방향 정확도를 계산한다.

    방향 정확도는 예측 시작 시점(origin_value) 대비 상승/하락 부호가
    실제와 일치한 비율이다. 상수 예측(Naive, 이동평균)은 부호가 0이 되어
    구조적으로 0%가 나온다. 이는 버그가 아니라 '단순 베이스라인은 방향을
    주장하지 않는다'는 사실을 드러내는 결과이며, 리포트에 그렇게 서술한다.
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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/ -q`
Expected: PASS — 30 passed

- [ ] **Step 5: 실제 데이터로 예측 결과 산출**

Run:

```bash
python -c "
import btc_analysis as ba
df = ba.fill_prices(ba.reindex_daily(ba.drop_invalid_rows(ba.load_raw('data/btc_usd_2023_2026.csv')))[0])
preds, scores = ba.run_baselines(df['Close'], horizon=30)
print('홀드아웃 구간', preds.index.min().date(), '~', preds.index.max().date())
print('실제 시작 %.0f 종료 %.0f (%.1f%%)' % (preds['actual'].iloc[0], preds['actual'].iloc[-1], (preds['actual'].iloc[-1]/preds['actual'].iloc[0]-1)*100))
print()
print(scores.round(2))
print()
print('MAE 최저 모델:', scores['mae'].idxmin())
"
```

Expected: 평가 표가 출력된다. **출력을 보존한다.** Q5와 보너스 절의 근거다.

판단 지침: Naive가 MAE 최저로 나와도 그것이 정상적인 결과다. 더 좋아 보이는 숫자를 만들기 위해 holdout 길이나 window를 바꿔 끼우지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add btc_analysis.py tests/test_btc_analysis.py
git commit -m "feat: 베이스라인 예측 3종 및 평가 지표 함수 추가"
```

---

## Task 7: 시각화 모듈

**Files:**
- Create: `plots.py`
- Create: `tests/test_plots.py`
- Create (출력): `images/01_price_trend_ma.png` ~ `images/05_baseline_forecast.png`

**Interfaces:**
- Consumes: Task 4·5·6의 출력 (`ma_7/ma_30/ma_90`, `daily_return`, `vol_30`, `monthly_return_pivot()`, `weekday_return_table()`, `run_baselines()`)
- Produces:
  - `setup_korean_font() -> None`
  - `plot_price_trend(df, out_path) -> Path`
  - `plot_returns_volatility(df, out_path) -> Path`
  - `plot_monthly_heatmap(pivot, out_path) -> Path`
  - `plot_weekday_box(df, out_path) -> Path`
  - `plot_baseline_forecast(predictions, scores, out_path) -> Path`

- [ ] **Step 1: 실패하는 스모크 테스트 작성**

`tests/test_plots.py`:

```python
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
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_plots.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'plots'`

- [ ] **Step 3: 구현 작성**

`plots.py`:

```python
"""분석 결과를 PNG로 저장하는 함수들.

계산 로직을 포함하지 않는다. btc_analysis가 만든 결과를 받아 그리기만 한다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import btc_analysis as ba

FIG_DPI = 150
KOREAN_FONT = "Malgun Gothic"  # Task 1에서 사용 불가로 확인되면 그 결과에 맞춰 교체한다


def setup_korean_font() -> None:
    """한글 레이블이 깨지지 않도록 폰트를 설정한다."""
    matplotlib.rcParams["font.family"] = KOREAN_FONT
    matplotlib.rcParams["axes.unicode_minus"] = False  # 음수 기호 깨짐 방지


def _save(fig, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_price_trend(df: pd.DataFrame, out_path: str | Path) -> Path:
    """종가와 이동평균. 선형축과 로그축을 2단으로 함께 보여준다.

    로그축을 같이 두는 이유: 기간 중 가격이 수 배 변하면 선형축에서는
    초기 구간의 변화가 눌려 '평평하게' 보인다.
    """
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

    for ax, scale, title in (
        (axes[0], "linear", "BTC-USD 종가와 이동평균 (선형 스케일)"),
        (axes[1], "log", "같은 데이터 (로그 스케일) — 초기 구간 변화율 비교용"),
    ):
        ax.plot(df.index, df["Close"], color="#999999", linewidth=0.8, label="종가")
        ax.plot(df.index, df["ma_7"], color="#1f77b4", linewidth=1.2, label="7일 이동평균")
        ax.plot(df.index, df["ma_30"], color="#ff7f0e", linewidth=1.4, label="30일 이동평균")
        ax.plot(df.index, df["ma_90"], color="#d62728", linewidth=1.6, label="90일 이동평균")
        ax.set_yscale(scale)
        ax.set_title(title)
        ax.set_ylabel("가격 (USD)")
        ax.legend(loc="upper left")
        ax.grid(alpha=0.3)

    axes[1].set_xlabel("날짜")
    return _save(fig, out_path)


def plot_returns_volatility(df: pd.DataFrame, out_path: str | Path) -> Path:
    """일별 수익률과 30일 롤링 변동성."""
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    returns_pct = df["daily_return"] * 100
    colors = np.where(returns_pct >= 0, "#2ca02c", "#d62728")
    axes[0].bar(df.index, returns_pct, color=colors, width=1.0)
    axes[0].axhline(0, color="black", linewidth=0.6)
    axes[0].set_title("일별 수익률 (%)")
    axes[0].set_ylabel("수익률 (%)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(df.index, df["vol_30"] * 100, color="#9467bd", linewidth=1.3)
    mean_vol = df["vol_30"].mean() * 100
    axes[1].axhline(mean_vol, color="gray", linestyle="--", linewidth=1.0,
                    label=f"평균 {mean_vol:.0f}%")
    axes[1].set_title("30일 롤링 변동성 (연율화, %)")
    axes[1].set_ylabel("변동성 (%)")
    axes[1].set_xlabel("날짜")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.3)

    return _save(fig, out_path)


def plot_monthly_heatmap(pivot: pd.DataFrame, out_path: str | Path) -> Path:
    """연도 x 월 월별 수익률 히트맵.

    0을 흰색으로 두는 발산형 컬러맵을 쓴다. 양수/음수를 즉시 구분하기 위함이다.
    """
    values = pivot.to_numpy(dtype=float) * 100
    limit = float(np.nanmax(np.abs(values))) if np.isfinite(values).any() else 1.0

    fig, ax = plt.subplots(figsize=(12, 1.2 * len(pivot) + 2.5))
    mesh = ax.imshow(values, cmap="RdYlGn", vmin=-limit, vmax=limit, aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{m}월" for m in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(y) for y in pivot.index])
    ax.set_title("월별 수익률 히트맵 (%) — 같은 달이 연도별로 일관적인지 확인")

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            if np.isfinite(values[i, j]):
                ax.text(j, i, f"{values[i, j]:.1f}", ha="center", va="center", fontsize=9)

    fig.colorbar(mesh, ax=ax, label="수익률 (%)")
    return _save(fig, out_path)


def plot_weekday_box(df: pd.DataFrame, out_path: str | Path) -> Path:
    """요일별 수익률 분포 박스플롯.

    평균만 보면 소수 극단값에 끌려가므로 분포 전체를 보여준다.
    """
    returns = df["daily_return"].dropna() * 100
    groups = [returns[returns.index.dayofweek == i].values for i in range(7)]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.boxplot(groups, tick_labels=ba.WEEKDAY_NAMES_KO, showmeans=True)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title("요일별 일간 수익률 분포 (%) — 비트코인은 주말에도 거래된다")
    ax.set_ylabel("수익률 (%)")
    ax.set_xlabel("요일")
    ax.grid(alpha=0.3, axis="y")

    return _save(fig, out_path)


def plot_baseline_forecast(predictions: pd.DataFrame, scores: pd.DataFrame,
                           out_path: str | Path) -> Path:
    """홀드아웃 구간의 실제값과 베이스라인 예측 비교."""
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(predictions.index, predictions["actual"], color="black", linewidth=2.0,
            marker="o", markersize=3, label="실제")

    styles = {"Naive": "--", "이동평균(7일)": "-.", "Drift": ":"}
    for name, style in styles.items():
        if name in predictions.columns:
            mape = scores.loc[name, "mape"]
            ax.plot(predictions.index, predictions[name], linestyle=style, linewidth=1.8,
                    label=f"{name} (MAPE {mape:.1f}%)")

    ax.set_title(f"베이스라인 예측 비교 — 홀드아웃 {len(predictions)}일")
    ax.set_ylabel("가격 (USD)")
    ax.set_xlabel("날짜")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)

    return _save(fig, out_path)
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_plots.py -q`
Expected: PASS — 5 passed

`boxplot`의 `tick_labels` 인자에서 `TypeError`가 나면 설치된 matplotlib이 3.9 미만이다. `labels=`로 바꿔 실행한다.

- [ ] **Step 5: 실제 데이터로 PNG 5개 생성**

Run:

```bash
python -c "
import matplotlib; matplotlib.use('Agg')
import btc_analysis as ba, plots
plots.setup_korean_font()
df = ba.fill_prices(ba.reindex_daily(ba.drop_invalid_rows(ba.load_raw('data/btc_usd_2023_2026.csv')))[0])
df = ba.add_volatility(ba.add_moving_averages(ba.add_returns(df)))
plots.plot_price_trend(df, 'images/01_price_trend_ma.png')
plots.plot_returns_volatility(df, 'images/02_returns_volatility.png')
plots.plot_monthly_heatmap(ba.monthly_return_pivot(df), 'images/03_monthly_heatmap.png')
plots.plot_weekday_box(df, 'images/04_weekday_boxplot.png')
preds, scores = ba.run_baselines(df['Close'], horizon=30)
plots.plot_baseline_forecast(preds, scores, 'images/05_baseline_forecast.png')
print('생성 완료')
"
ls -la images/
```

Expected: PNG 5개가 생성되고 각 파일 크기가 50KB 이상.

- [ ] **Step 6: 그래프 5개를 눈으로 확인**

Read 도구로 `images/01_price_trend_ma.png` ~ `images/05_baseline_forecast.png`를 **모두 직접 열어 본다.** 확인 항목:

- 한글 레이블이 `□□□`로 깨지지 않았는가 (깨졌다면 `KOREAN_FONT` 값 수정)
- 음수 기호가 정상 표시되는가
- 범례가 데이터를 가리지 않는가
- 히트맵 셀의 숫자가 읽히는가
- 로그축 패널에서 초기 구간이 눌려 보이지 않는가

문제가 있으면 수정하고 Step 5를 다시 실행한다. **그래프를 보지 않고 다음 태스크로 넘어가지 않는다.**

- [ ] **Step 7: 커밋**

```bash
git add plots.py tests/test_plots.py images/
git commit -m "feat: 시각화 5종 생성 모듈 추가 및 이미지 산출"
```

---

## Task 8: 분석 노트북 작성 및 실행

**Files:**
- Create: `analysis.ipynb`

**Interfaces:**
- Consumes: `btc_analysis.py`, `plots.py`, `data/btc_usd_2023_2026.csv`
- Produces: 실행된 노트북 (출력 포함) + `images/` 재생성. Task 9 리포트의 **모든 수치가 이 노트북 출력에서 나온다.**

- [ ] **Step 1: 노트북 셀 구성 결정**

아래 12개 셀로 구성한다. 계산식을 셀 안에 직접 쓰지 않고 `btc_analysis` 함수를 호출만 한다 (검증된 코드만 쓰기 위함).

| 셀 | 종류 | 내용 |
| --- | --- | --- |
| 1 | md | 제목, 분석 목적, 실행 전 준비(`python fetch_data.py` 선행 안내) |
| 2 | code | import, `plots.setup_korean_font()` |
| 3 | md | 1. 데이터 로드 및 기본 정보 |
| 4 | code | `load_raw`, `df.info()`, `df.head()`, `df.describe()`, 기간·행수 출력 |
| 5 | md | 2. 결측치·이상치 점검 및 처리 기준 |
| 6 | code | `find_invalid_rows`, `drop_invalid_rows`, `reindex_daily`, `fill_prices`, 각 건수 출력 |
| 7 | md | 3. 지표 계산 (이동평균·수익률·변동성·MDD) |
| 8 | code | `add_returns`→`add_moving_averages`→`add_volatility`, 요약 통계·MDD·이상치 목록 출력 |
| 9 | md | 4. 패턴 탐색 (월별·요일별) |
| 10 | code | `monthly_return_pivot`, `weekday_return_table` 출력 + 월별 부호 일관성 |
| 11 | md | 5. 베이스라인 예측 |
| 12 | code | `run_baselines` 평가표 출력 + 그래프 5개 저장 |

- [ ] **Step 2: 노트북 파일 생성**

`analysis.ipynb`를 위 구성대로 작성한다. `nbformat`으로 생성하는 것이 수동 JSON 작성보다 안전하다:

```bash
python - <<'PY'
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []

C.append(nbf.v4.new_markdown_cell("""# 비트코인(BTC-USD) 시계열 분석

**기간**: 2023-01-01 ~ 2026-09-30 (일 단위)
**출처**: Yahoo Finance (`yfinance`) — 개인·비상업 용도 제한

## 실행 순서

1. `pip install -r requirements.txt`
2. `python fetch_data.py` — 데이터를 `data/`에 받는다 (이미 CSV가 있으면 생략 가능)
3. 이 노트북을 위에서 아래로 순서대로 실행

계산 로직은 모두 `btc_analysis.py`에 있고 `tests/`에서 검증된다.
이 노트북은 호출과 출력만 담당한다 — 노트북 셀 안의 계산식은 테스트할 수 없기 때문이다."""))

C.append(nbf.v4.new_code_cell("""import matplotlib
import pandas as pd

import btc_analysis as ba
import plots

plots.setup_korean_font()
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

CSV_PATH = "data/btc_usd_2023_2026.csv"
print("준비 완료")"""))

C.append(nbf.v4.new_markdown_cell("""## 1. 데이터 로드 및 기본 정보

기간, 컬럼, 자료형, 기술통계를 먼저 확인한다."""))

C.append(nbf.v4.new_code_cell("""raw = ba.load_raw(CSV_PATH)

print(f"기간: {raw.index.min().date()} ~ {raw.index.max().date()}")
print(f"행 수: {len(raw)}")
print(f"컬럼: {list(raw.columns)}")
print()
raw.info()
print()
display(raw.head())
display(raw.describe().round(2))"""))

C.append(nbf.v4.new_markdown_cell("""## 2. 결측치 / 이상치 점검

**처리 기준**

- **데이터 오류는 제거한다**: 가격 0 이하, `High < Low`, 전일 대비 ±50% 초과
- **결측 날짜는 ffill로 채운다**: 거래 기록이 없는 날은 직전 가격이 유지된 것으로 본다
- **보간된 날이 관여한 수익률은 제외한다**: 가짜 0% 수익률이 섞이면 변동성이 과소추정된다
- **극단 수익률은 제거하지 않는다**: 비트코인의 하루 ±10% 변동은 측정 오류가 아니라 분석 대상 신호다"""))

C.append(nbf.v4.new_code_cell("""invalid = ba.find_invalid_rows(raw)
print(f"데이터 오류 행: {len(invalid)}건")
if len(invalid):
    display(invalid)

clean = ba.drop_invalid_rows(raw)
reindexed, missing = ba.reindex_daily(clean)
print(f"전체 날짜 재색인 후 행 수: {len(reindexed)}")
print(f"원본에 없던 날짜: {len(missing)}건")
if len(missing):
    print(list(missing[:20]))

df = ba.fill_prices(reindexed)
print(f"ffill로 보간한 날짜: {int(df['is_filled'].sum())}건")
print(f"보간 후 종가 결측: {int(df['Close'].isna().sum())}건")"""))

C.append(nbf.v4.new_markdown_cell("""## 3. 시계열 지표 계산

- **이동평균 7/30/90일** — 단기 노이즈를 걷어내 추세를 분리한다
- **일별·누적 변화율** — 가격 레벨이 다른 구간을 공정하게 비교한다
- **30일 롤링 변동성(연율화)** — 변동성의 시간 변화를 측정한다. 연중무휴 거래이므로 `sqrt(365)`로 연율화한다
- **최대 낙폭(MDD)** — 하락 리스크 규모를 단일 수치로 요약한다"""))

C.append(nbf.v4.new_code_cell("""df = ba.add_returns(df)
df = ba.add_moving_averages(df, windows=(7, 30, 90))
df = ba.add_volatility(df, window=30)

print(f"시작가 ${df['Close'].iloc[0]:,.0f}  종료가 ${df['Close'].iloc[-1]:,.0f}")
print(f"전체 누적 수익률: {df['cum_return'].iloc[-1]*100:,.1f}%")
print(f"최고가 ${df['Close'].max():,.0f} ({df['Close'].idxmax().date()})")
print(f"최저가 ${df['Close'].min():,.0f} ({df['Close'].idxmin().date()})")
print()
print(f"일평균 수익률: {df['daily_return'].mean()*100:.4f}%")
print(f"일간 표준편차: {df['daily_return'].std()*100:.2f}%")
print(f"연율 변동성 — 평균 {df['vol_30'].mean()*100:.1f}%  최대 {df['vol_30'].max()*100:.1f}% ({df['vol_30'].idxmax().date()})  최소 {df['vol_30'].min()*100:.1f}% ({df['vol_30'].idxmin().date()})")
print()

mdd = ba.max_drawdown(df["Close"])
print(f"최대 낙폭: {mdd['mdd']*100:.1f}%  ({mdd['peak_date'].date()} 고점 → {mdd['trough_date'].date()} 저점)")
print()

outliers = ba.detect_return_outliers(df, z_threshold=3.0)
print(f"3시그마 초과 일자: {len(outliers)}일 (전체의 {len(outliers)/df['daily_return'].notna().sum()*100:.1f}%)")
print("--- 하락 상위 5일 ---")
display(outliers.nsmallest(5, "daily_return"))
print("--- 상승 상위 5일 ---")
display(outliers.nlargest(5, "daily_return"))"""))

C.append(nbf.v4.new_markdown_cell("""## 4. 패턴 탐색: 월별 / 요일별

집계 단위를 바꾸는 이유: 일 단위에서는 노이즈가 커서 반복 패턴이 보이지 않는다.
월·요일로 묶어 같은 구간이 연도를 건너도 일관된지 확인한다."""))

C.append(nbf.v4.new_code_cell("""pivot = ba.monthly_return_pivot(df)
print("=== 월별 수익률 (%) ===")
display((pivot * 100).round(1))

print("=== 월별 평균 (%) ===")
display((pivot.mean() * 100).round(1).to_frame("평균 수익률(%)").T)

print("=== 월별 부호 일관성 (양수였던 연도 수 / 데이터가 있는 연도 수) ===")
consistency = pivot.apply(lambda c: f"{int((c > 0).sum())}/{int(c.notna().sum())}")
display(consistency.to_frame("양수 연도").T)

print("=== 요일별 수익률 ===")
weekday = ba.weekday_return_table(df)
display((weekday[["mean", "median", "std"]] * 100).round(3).join(weekday[["count"]]))"""))

C.append(nbf.v4.new_markdown_cell("""## 5. 베이스라인 예측 (보너스)

마지막 30일을 홀드아웃으로 두고, 그 이전 데이터만으로 3개 베이스라인을 비교한다.

**방향 정확도 주의**: Naive와 이동평균은 상수를 예측하므로 방향 부호가 0이 되어
구조적으로 0%가 나온다. 버그가 아니라 "단순 베이스라인은 방향을 주장하지 않는다"는
사실이다. 이 지표는 Drift 모델 평가에만 의미가 있다."""))

C.append(nbf.v4.new_code_cell("""predictions, scores = ba.run_baselines(df["Close"], horizon=30)

print(f"홀드아웃: {predictions.index.min().date()} ~ {predictions.index.max().date()} ({len(predictions)}일)")
actual_change = predictions["actual"].iloc[-1] / predictions["actual"].iloc[0] - 1
print(f"홀드아웃 구간 실제 변화: {actual_change*100:+.1f}%")
print()
display(scores.round(2))
print(f"MAE 최저 모델: {scores['mae'].idxmin()}")
print()

plots.plot_price_trend(df, "images/01_price_trend_ma.png")
plots.plot_returns_volatility(df, "images/02_returns_volatility.png")
plots.plot_monthly_heatmap(pivot, "images/03_monthly_heatmap.png")
plots.plot_weekday_box(df, "images/04_weekday_boxplot.png")
plots.plot_baseline_forecast(predictions, scores, "images/05_baseline_forecast.png")
print("그래프 5개 저장 완료 → images/")"""))

nb.cells = C
nbf.write(nb, "analysis.ipynb")
print("analysis.ipynb 생성 완료")
PY
```

- [ ] **Step 3: 노트북을 처음부터 끝까지 실행**

Run: `python -m jupyter nbconvert --to notebook --execute --inplace analysis.ipynb`
Expected: 오류 없이 완료. 모든 셀에 출력이 저장된다.

실패하면 오류 메시지의 셀을 수정하고 다시 실행한다. **일부 셀만 돌린 상태로 두지 않는다** — 재현성이 깨진다.

- [ ] **Step 4: 노트북 출력 전체를 확인하고 수치를 기록**

Run: `python -m jupyter nbconvert --to markdown --stdout analysis.ipynb`

출력된 모든 수치를 읽고 기록한다. Task 9에서 리포트를 쓸 때 **이 출력만을 근거로** 사용한다. 출력에 없는 수치를 리포트에 쓰지 않는다.

- [ ] **Step 5: 전체 테스트 재실행**

Run: `python -m pytest tests/ -q`
Expected: PASS — 35 passed

- [ ] **Step 6: 커밋**

```bash
git add analysis.ipynb images/
git commit -m "feat: 분석 노트북 작성 및 전체 실행 결과 반영"
```

---

## Task 9: 분석 리포트 작성

**Files:**
- Create: `REPORT.md`

**Interfaces:**
- Consumes: Task 8 노트북의 실행 출력 (모든 수치), `images/*.png` 5개
- Produces: 미션 요구사항을 충족하는 최종 리포트

- [ ] **Step 1: 리포트 골격 작성**

`REPORT.md`에 아래 9개 절을 만든다. 각 절 제목은 그대로 쓴다.

```markdown
# 비트코인(BTC-USD) 시계열 분석 리포트

> 본 문서는 데이터 분석 학습 산출물이며, 투자 권유나 투자 조언이 아니다.

## 1. 분석 주제 및 선정 이유
## 2. 분석 질문
## 3. 데이터 설명
## 4. 데이터 정제 과정
## 5. 분석 결과 및 시각화
## 6. 인사이트
## 7. 보너스: 베이스라인 예측
## 8. 결론 및 한계점
## 9. AI 사용 로그
```

- [ ] **Step 2: 1~4절 작성 (주제·질문·데이터·정제)**

- **1절**: 비트코인을 고른 이유 3가지를 쓴다 — ① 연중무휴 거래라 요일 분석이 가능하다(주식으로는 불가능) ② 변동성이 커서 분석 기법의 효과가 뚜렷하다 ③ 추세 전환 구간이 여러 번 있어 관찰과 해석을 분리해 서술할 소재가 많다. 기간 선정 근거(연도 3개 이상 확보로 월별 교차 비교 가능)도 쓴다.
- **2절**: 설계 문서의 Q1~Q5를 표로 옮기고 각 질문이 "그래프로 확인 가능" / "추가 해석 필요" 중 어느 쪽인지 표시한다.
- **3절**: 출처(Yahoo Finance / yfinance), 기간, **실제 행 수**, 컬럼 목록, 데이터 수집 방법(`python fetch_data.py`), 라이선스 주의 문구(개인·비상업 용도 제한)를 쓴다.
- **4절**: Task 3·Task 8 Step 6에서 얻은 **실제 건수**를 넣는다 — 데이터 오류 N건, 누락 날짜 N건, ffill 보간 N건, 3시그마 초과 N일. 그리고 각 처리의 **근거**를 쓴다. 특히 "극단 수익률을 제거하지 않은 이유"를 한 단락으로 설명한다 (제거하면 변동성 분석의 목적 자체가 훼손된다).

- [ ] **Step 3: 5절 작성 (시각화 + 관찰)**

그래프 5개를 순서대로 삽입하고, **각 그래프 아래에 관찰 내용을 3줄 이상** 쓴다. 이미지 링크는 상대 경로로 쓴다:

```markdown
### 5.1 가격 추이와 이동평균

![가격 추이와 이동평균](images/01_price_trend_ma.png)

**관찰**: (노트북 출력의 실제 수치로 작성)

**로그축을 함께 둔 이유**: 기간 중 가격이 수 배 변해 선형축만으로는 초기 구간의 변화율이 눌려 보인다.
```

같은 형식으로 5.2(수익률·변동성), 5.3(월별 히트맵), 5.4(요일별 박스플롯), 5.5(예측)까지 작성한다.

**금지**: 그래프만 나열하고 설명을 생략하는 것. 미션의 명시적 금지 사항이다.

- [ ] **Step 4: 6절 작성 (인사이트 3개 이상)**

각 인사이트를 아래 형식으로 쓴다. **관찰에는 반드시 노트북 출력의 실제 수치가 들어가야 한다.**

```markdown
### 인사이트 1: [제목]

- **관찰(Fact)**: [수치와 구간. 노트북 출력에서 가져온 값만 쓴다]
- **해석(Why)**: [원인 가설 1~2개]
- **행동(Action)**: [다음 분석 과제 또는 의사결정 제안]
```

작성 지침:

- 인사이트 소재: ① 추세 전환 구간과 이동평균 교차 ② 변동성 집중 현상 ③ 월별 패턴의 존재/부재 ④ 요일 효과의 존재/부재 ⑤ MDD로 본 하락 리스크 중 **3개 이상**을 고른다.
- **패턴이 없다는 결론도 유효한 인사이트다.** 월별 부호 일관성이 `2/4`, `3/4` 수준이라면 "월 효과는 확인되지 않았다 — 표본이 4년치뿐이라 우연과 구분할 수 없다"가 정직한 서술이다. 없는 패턴을 있다고 쓰지 않는다.
- 특정 뉴스·사건과 연결한 문장에는 반드시 `(검증 필요)`를 붙인다. AI의 지식 기준일이 2026년 5월이므로 그 이후 구간의 사건 연결은 사실이 아닐 수 있다.

- [ ] **Step 5: 7~8절 작성 (예측 결과, 결론·한계)**

- **7절**: Task 8의 평가표를 그대로 싣고, MAE 최저 모델이 무엇인지 쓴다. Naive가 이겼다면 **그것을 그대로 쓰고 이유를 설명한다** — 가격 시계열이 랜덤워크에 가까워 과거 추세의 연장이 미래를 예측하지 못한다. 방향 정확도가 상수 예측에서 구조적으로 0%가 되는 이유도 명시한다. 가정과 한계 3가지(과거 패턴 반복 가정 / 외부 변수 미반영 / 단일 홀드아웃 구간)를 쓴다.
- **8절**: 결론은 Q1~Q5에 대한 답을 각 한 줄로 정리한다. 한계점은 최소 4개 — 외부 변수(규제·거시경제·뉴스) 미반영, 단일 자산 단일 지표, 4년이라는 짧은 표본, 상관을 인과로 해석할 수 없음.

- [ ] **Step 6: 9절 작성 (AI 사용 로그)**

미션의 의무 항목이다. 3가지를 모두 쓴다.

| 항목 | 내용 |
| --- | --- |
| **사용 작업** | 데이터 수집 스크립트 작성, 정제·지표·집계·예측 함수 구현, 단위 테스트 작성, 시각화 코드 작성, 리포트 문장 다듬기 |
| **사용 이유** | 반복적인 pandas 코드 작성 시간 절감, 정제 기준의 대안 탐색(ffill vs 제거 vs 보간), 계산 로직의 검증 방법 설계 |
| **검증 방법** | ① 모든 분석 함수에 pytest 단위 테스트를 작성해 합성 데이터로 기대값 검증 (예: +10%, −10% 입력에 대한 수익률 계산) ② 생성된 그래프 5개를 직접 열어 한글 깨짐·범례 가림·축 스케일 확인 ③ 리포트의 모든 수치를 노트북 실행 출력과 대조 ④ AI가 제시한 사건 연결 가설은 사실 확인 전까지 `(검증 필요)`로 표기 |

**추가로 쓸 것**: AI 지식 기준일이 2026년 5월이라는 한계, 그리고 그 이후 구간의 사건 해석은 본인이 검증해야 한다는 점.

- [ ] **Step 7: 리포트 자체 점검**

다음을 하나씩 확인한다.

```bash
grep -c '!\[' REPORT.md          # 이미지 링크 5개 이상인지
grep -n '관찰' REPORT.md | wc -l  # 관찰 서술이 충분한지
grep -n 'TBD\|TODO\|XXX\|예시값' REPORT.md   # 플레이스홀더가 남았는지 (결과 없어야 함)
ls images/                        # 참조된 파일이 실제로 존재하는지
```

체크리스트:

- [ ] 시각화 3개 이상 포함 (실제 5개)
- [ ] 인사이트 3개 이상, 각각 실제 수치 포함
- [ ] 관찰과 해석이 분리되어 있음
- [ ] 분석 질문 3개 이상
- [ ] 결측치·이상치 처리 기준과 근거 서술
- [ ] 분석 기법 2개 이상 명시
- [ ] AI 사용 로그 3항목 모두 작성
- [ ] 데이터 출처·기간·라이선스 명시
- [ ] 이미지 링크가 모두 실제 파일을 가리킴
- [ ] 플레이스홀더·추정값 없음

- [ ] **Step 8: 커밋**

```bash
git add REPORT.md
git commit -m "docs: 비트코인 시계열 분석 리포트 작성"
```

---

## Task 10: README 작성 및 GitHub 업로드

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: 앞선 모든 태스크의 산출물
- Produces: GitHub에 공개된 저장소

- [ ] **Step 1: README 작성**

`README.md`에 아래를 포함한다.

````markdown
# 비트코인(BTC-USD) 시계열 분석

2023-01-01 ~ 2026-09-30 비트코인 일봉 데이터를 분석해 추세·변동성·반복 패턴을 확인하고,
베이스라인 예측의 한계를 검증한 프로젝트.

**분석 결과: [REPORT.md](REPORT.md)**

## 프로젝트 구조

(실제 파일 구조를 트리로 적는다)

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 데이터 수집 (data/ 에 CSV가 이미 있으면 생략 가능)
python fetch_data.py

# 3. 테스트 실행 (계산 로직 검증)
python -m pytest tests/ -q

# 4. 분석 노트북 실행
jupyter notebook analysis.ipynb
# 또는 전체 자동 실행:
python -m jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

노트북은 위에서 아래로 순서대로 실행한다. 네트워크에 접근하지 않고 `data/`의 CSV만 읽으므로
언제 실행해도 같은 결과가 나온다.

## 설계 원칙

- **수집과 분석 분리**: 노트북이 매번 데이터를 받으면 실행 시점에 따라 결과가 달라진다.
  `fetch_data.py`로 한 번 받아 CSV로 고정한다.
- **계산 로직은 테스트된 모듈에만**: 노트북 셀의 계산식은 검증할 수 없으므로
  모든 계산을 `btc_analysis.py`에 두고 `tests/`에서 검증한다.

## 데이터 출처 및 라이선스 주의

- 출처: Yahoo Finance (`yfinance` 라이브러리)
- 기간: 2023-01-01 ~ 2026-09-30, 일(日) 단위
- Yahoo Finance 데이터는 **개인적·비상업적 용도**로만 사용이 허용된다.
  본 저장소의 `data/` CSV는 분석 재현 목적으로만 포함되었으며 상업적 재배포를 허용하지 않는다.

## 면책

본 저장소는 데이터 분석 학습 산출물이다. 투자 권유나 투자 조언이 아니다.

## 개발 환경

(Task 1 Step 3에서 확인한 실제 Python 및 패키지 버전을 적는다.
Python 3.12 venv로 전환했다면 그 사실과 이유도 함께 적는다.)
````

- [ ] **Step 2: 커밋**

```bash
git add README.md
git commit -m "docs: README에 실행 방법 및 데이터 라이선스 안내 추가"
```

- [ ] **Step 3: 최종 상태 점검**

```bash
python -m pytest tests/ -q
git status --short
git log --oneline
ls -R
```

Expected: 테스트 전체 통과, 커밋되지 않은 파일 없음, 커밋 7개 이상, `data/` CSV와 `images/` PNG 5개 존재.

- [ ] **Step 4: 사용자에게 GitHub 저장소 생성 요청**

`gh` CLI가 없으므로 사용자가 직접 생성해야 한다. 다음을 안내한다.

> github.com에서 새 저장소를 만들어 주세요.
> - 이름: `btc-timeseries-analysis`
> - 공개/비공개: 자유
> - **"Add a README file" 체크는 해제**해 주세요 (이미 로컬에 있어 충돌이 납니다)
>
> 만든 뒤 저장소 URL을 알려주세요.

**사용자가 URL을 주기 전까지 다음 단계로 넘어가지 않는다.**

- [ ] **Step 5: 원격 연결 및 푸시**

사용자가 준 URL로 실행한다:

```bash
git remote add origin <사용자가 제공한 URL>
git branch -M main
git push -u origin main
```

인증 창이 뜨면 사용자가 직접 처리한다. 푸시가 인증 실패로 막히면, 사용자에게 위 명령을 터미널에서 `!` 접두사로 직접 실행하도록 안내한다.

- [ ] **Step 6: 업로드 결과 확인**

```bash
git remote -v
git log --oneline origin/main -1
```

Expected: origin이 연결되고 로컬 최신 커밋이 `origin/main`에 반영되어 있다.

GitHub 웹에서 다음을 확인하도록 사용자에게 안내한다:

- `REPORT.md`의 이미지 5개가 **모두 정상 렌더링**되는지 (상대 경로가 깨지면 이미지가 안 보인다)
- `analysis.ipynb`가 출력과 함께 미리보기되는지

---

## Self-Review

**1. 스펙 커버리지**

| 스펙 요구사항 | 담당 태스크 |
| --- | --- |
| 데이터 100개 이상 | Task 2 (약 1,370행, Step 2에서 검증) |
| 출처·기간 명시 | Task 9 Step 2 (3절), Task 10 Step 1 |
| 분석 질문 3개 이상 | Task 9 Step 2 (2절, Q1~Q5) |
| 기본 정보 확인 | Task 8 셀 4 |
| 결측·이상치 처리 | Task 3, Task 8 셀 6, Task 9 Step 2 (4절) |
| 분석 기법 2개 이상 | Task 4 (이동평균/변화율/변동성/MDD), Task 5 (월별·요일별) — 5개 |
| 시각화 2개 이상 | Task 7 (5개) |
| 인사이트 3개 이상 | Task 9 Step 4 |
| REPORT.md | Task 9 |
| Python 코드 | Task 2, 3, 4, 5, 6, 7, 8 |
| requirements.txt | Task 1 Step 4 |
| 실행 방법 문서화 | Task 10 Step 1 |
| 라이선스 주의 | Task 9 Step 2, Task 10 Step 1 |
| 관찰/해석 분리 | Task 9 Step 3, Step 4 |
| AI 사용 로그 3항목 | Task 9 Step 6 |
| GitHub 저장소 | Task 10 |
| 보너스 (B) 예측 | Task 6, Task 7 (그래프 5), Task 9 Step 5 |
| 집계 단위 근거 | Task 8 셀 9 마크다운, Task 9 Step 3 |
| 스케일 점검(로그축) | Task 7 `plot_price_trend` |
| 시간축 정렬·누락 확인 | Task 3 `reindex_daily`, Task 8 셀 6 |

누락 없음.

**2. 플레이스홀더 점검**

의도적으로 실행 시점에 채우도록 남긴 자리는 3곳이며, 모두 "실제 출력에서 가져오라"는 지시와 함께 있다: Task 1 Step 4의 버전 번호, Task 9의 실제 수치, Task 10의 환경 정보. 추정값으로 채우는 것을 명시적으로 금지했다.

**3. 타입·이름 일관성**

- `fill_prices()`가 만드는 `is_filled`를 `add_returns()`가 소비 — 일치
- `add_volatility(window=30)`이 만드는 `vol_30`을 `plot_returns_volatility()`가 소비 — 일치
- `add_moving_averages(windows=(7,30,90))`이 만드는 `ma_7/ma_30/ma_90`을 `plot_price_trend()`가 소비 — 일치
- `run_baselines()`가 돌려주는 `scores.index` = `["Naive", "이동평균(7일)", "Drift"]`와 `plot_baseline_forecast()`의 `styles` 키 — 일치
- `forecast_moving_average(window=7)`의 `name=f"이동평균({window}일)"` → `window=7`일 때 `"이동평균(7일)"` — 일치
- `WEEKDAY_NAMES_KO`를 `weekday_return_table()`과 `plot_weekday_box()`가 공유 — 일치
- `reindex_daily()`는 `(DataFrame, DatetimeIndex)` 튜플 반환. Task 3~8의 모든 호출부에서 `[0]` 또는 언패킹으로 처리 — 일치
