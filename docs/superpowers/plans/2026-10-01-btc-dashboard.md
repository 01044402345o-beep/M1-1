# 비트코인 분석 대시보드 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기간·이동평균·변동성 윈도·홀드아웃 구간을 바꿔가며 탐색할 수 있는 Streamlit 대시보드를 만들고, 스크린샷 5장과 시나리오 문서로 제출한다.

**Architecture:** 선행 프로젝트가 확립한 3계층을 따른다. 검증된 `btc_analysis.py`(수정 금지)를 `dashboard_core.py`(순수 함수, 테스트 대상)가 호출하고, `dashboard.py`(Streamlit 껍데기)는 위젯 배치와 렌더링만 한다. 계산 로직은 한 줄도 중복하지 않으므로 대시보드가 보여주는 수치는 리포트의 수치와 같은 테스트된 함수에서 나온다.

**Tech Stack:** Python 3.14.4, pandas 3.0.3, numpy 2.5.1, matplotlib 3.11.2, streamlit(신규), pytest 9.1.1, playwright(설치됨) + 시스템 Chrome

**Spec:** `docs/superpowers/specs/2026-10-01-btc-dashboard-design.md`

## Global Constraints

- Python 3.14.4, venv 없음. `python` 명령을 그대로 쓴다.
- 기존 산출물 **수정 금지**: `btc_analysis.py`, `plots.py`, `analysis.ipynb`, `REPORT.md`, `tests/test_btc_analysis.py`, `tests/test_plots.py`. 전부 리뷰를 통과해 `main`에 병합·푸시됐다. 버그를 발견하면 고치지 말고 보고한다.
- `README.md`와 `requirements.txt`는 수정 대상이다(Task 7, Task 1).
- 계산 로직은 `btc_analysis.py` 호출로만 수행한다. `dashboard_core.py`는 오케스트레이션·검증·슬라이싱을 하고, `dashboard.py`는 계산을 전혀 하지 않는다.
- 지표는 **선택 구간의 데이터만으로 재계산**한다. 전 구간에서 계산한 뒤 잘라 보여주지 않는다.
- 색상: **상승 = 빨강(`plots._RED`), 하락 = 파랑(`plots._BLUE`)** — 한국 금융 관행. 화면에 한 줄로 명시한다. 색상 상수는 `plots.py`에서 import하며 재정의하지 않는다.
- 한글 레이블, `Malgun Gothic`, `axes.unicode_minus = False`. 폰트는 `plots.setup_korean_font()`를 호출해 설정한다.
- 네트워크 접근 금지. `data/btc_usd_2023_2026.csv`만 읽는다.
- 학습 구간은 **최소 2일**을 보장한다. `forecast_drift`의 기울기가 `(마지막값 − 첫값) / (길이 − 1)`이라 1일이면 0으로 나눈다.
- 전체 테스트는 항상 통과해야 하고 `-W error`에서도 깨끔해야 한다. 기존 36개 + 이 계획이 추가하는 테스트.
- 교차 검증 고정점: 홀드아웃 `2026-06-01`, horizon `30`에서 MAE가 Naive **10,578.53** / Drift **11,287.03** / 이동평균 **11,526.55** 여야 한다 (`REPORT.md` 7.4절 기록값).
- 데이터 범위: `2023-01-01` ~ `2026-09-29`, 1,368행, 결측 없음.

---

## File Structure

| 파일 | 책임 |
| --- | --- |
| `dashboard_core.py` | 순수 함수. 파라미터 파싱·검증, 구간 슬라이싱, `btc_analysis` 호출 오케스트레이션, 구간 요약, 임의 홀드아웃 평가 |
| `dashboard.py` | Streamlit UI 껍데기. 위젯, 레이아웃, matplotlib Figure 생성, `st.pyplot` 렌더링 |
| `tests/test_dashboard_core.py` | `dashboard_core.py` 단위 테스트 |
| `capture_screenshots.py` | Playwright로 Streamlit 앱을 띄워 URL 쿼리를 바꿔가며 PNG 5장 캡처 |
| `docs/dashboard/README.md` | 시나리오 설명 (장면별 설정과 관찰) |
| `docs/dashboard/01~05_*.png` | 스크린샷 |
| `requirements.txt` | `streamlit` 추가 (수정) |
| `README.md` | 대시보드 실행 방법 섹션 추가 (수정) |

`dashboard_core.py`와 `dashboard.py`를 나누는 이유는 Streamlit 스크립트가 단위 테스트 불가능하기 때문이다. 노트북 셀을 테스트할 수 없어 `btc_analysis.py`를 분리했던 것과 같은 이유, 같은 해법이다.

---

## Task 1: streamlit 설치 및 의존성 고정

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: 기존 환경 (Python 3.14.4, pandas 3.0.3 등)
- Produces: 설치된 `streamlit`. Task 5~6이 의존한다.

- [ ] **Step 1: 설치 시도**

```bash
python -m pip install streamlit
```

- [ ] **Step 2: 설치 결과 확인**

Run:

```bash
python -c "import streamlit; print('streamlit', streamlit.__version__)"
```

Expected: 버전이 출력된다.

**실패하면 여기서 멈추고 보고한다.** 다른 프레임워크로 바꾸지 않는다 — 접근 방식을 바꾸면 "검증된 모듈 직접 재사용"이라는 설계 근거가 무너지므로 그 판단은 사용자가 한다. 오류 메시지 전문을 보고에 싣는다.

- [ ] **Step 3: 기존 테스트가 여전히 통과하는지 확인**

Run: `python -m pytest tests/ -q`
Expected: 36 passed

streamlit 설치가 pandas/numpy를 다운그레이드했다면 여기서 드러난다. 버전이 바뀌었다면 보고한다.

- [ ] **Step 4: requirements.txt에 추가**

Step 2에서 출력된 **실제 버전**으로 아래 줄을 `requirements.txt` 끝에 추가한다. 추정값을 쓰지 않는다.

```
streamlit==X.Y.Z
```

- [ ] **Step 5: 커밋**

```bash
git add requirements.txt
git commit -m "chore: 대시보드용 streamlit 의존성 추가"
```

---

## Task 2: 데이터 준비와 구간 슬라이싱

**Files:**
- Create: `dashboard_core.py`
- Create: `tests/test_dashboard_core.py`

**Interfaces:**
- Consumes: `btc_analysis` (as `ba`) — `load_raw`, `drop_invalid_rows`, `reindex_daily`(2-튜플 반환), `fill_prices`, `add_returns`, `add_moving_averages(df, windows=tuple)`, `add_volatility(df, window=int)`
- Produces:
  - `load_prepared(csv_path: str | Path) -> pd.DataFrame` — 정제까지만. `daily_return`은 아직 없다
  - `slice_period(df, start, end) -> pd.DataFrame` — 양끝 포함
  - `recompute_indicators(df, ma_windows: tuple[int, ...], vol_window: int) -> pd.DataFrame` — 슬라이스에 `add_returns → add_moving_averages → add_volatility`를 순서대로 적용

**왜 `load_prepared`가 `add_returns`를 하지 않는가**: 수익률과 누적 수익률은 구간이 바뀌면 달라져야 한다. 전 구간에서 계산한 `cum_return`을 잘라 보여주면 "2024년 누적 수익률" 자리에 2023년부터의 누적이 표시된다. 그래서 수익률 계산은 슬라이싱 **이후**인 `recompute_indicators`에 둔다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_dashboard_core.py`:

```python
import numpy as np
import pandas as pd
import pytest

import btc_analysis as ba
import dashboard_core as dc

CSV_PATH = "data/btc_usd_2023_2026.csv"


def make_prices(dates, close):
    """테스트용 최소 OHLCV 프레임. is_filled 없이 원본 형태로 만든다."""
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="Date")
    close = np.asarray(close, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.001,
            "Low": close * 0.999,
            "Close": close,
            "Volume": np.ones(len(close)) * 100.0,
        },
        index=idx,
    )


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
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard_core'`

- [ ] **Step 3: 최소 구현 작성**

`dashboard_core.py`:

```python
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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: PASS — 7 passed

- [ ] **Step 5: 전체 테스트와 -W error 확인**

Run: `python -m pytest tests/ -q && python -m pytest tests/ -q -W error`
Expected: 43 passed (기존 36 + 신규 7), 둘 다 깨끔

- [ ] **Step 6: 커밋**

```bash
git add dashboard_core.py tests/test_dashboard_core.py
git commit -m "feat: 대시보드 데이터 준비 및 구간 재계산 함수 추가"
```

---

## Task 3: 구간 요약과 임의 홀드아웃 평가

**Files:**
- Modify: `dashboard_core.py` (append)
- Modify: `tests/test_dashboard_core.py` (append)

**Interfaces:**
- Consumes: Task 2의 `recompute_indicators` 출력, `ba.max_drawdown(close) -> dict{mdd, peak_date, trough_date}`, `ba.detect_return_outliers(df, z_threshold=3.0) -> DataFrame`, `ba.run_baselines(close, horizon=30) -> (predictions, scores)`
- Produces:
  - `MIN_TRAIN_DAYS = 2` (모듈 상수)
  - `summarize_period(df, vol_window: int) -> dict` — 키: `n_days`, `cum_return`, `mdd`, `mdd_peak`, `mdd_trough`, `vol_mean`, `outlier_down`, `outlier_up`
  - `evaluate_holdout_window(close, holdout_start, horizon) -> tuple[pd.DataFrame, pd.DataFrame]`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_dashboard_core.py` 끝에 추가:

```python
def test_summarize_period_reports_known_values():
    df = make_prices(pd.date_range("2023-01-01", periods=5, freq="D"),
                     [100.0, 150.0, 75.0, 120.0, 130.0])
    out = dc.recompute_indicators(df, ma_windows=(2,), vol_window=3)

    s = dc.summarize_period(out, vol_window=3)

    assert s["n_days"] == 5
    assert s["cum_return"] == pytest.approx(0.30)        # 100 -> 130
    assert s["mdd"] == pytest.approx(-0.50)              # 150 -> 75
    assert s["mdd_peak"] == pd.Timestamp("2023-01-02")
    assert s["mdd_trough"] == pd.Timestamp("2023-01-03")


def test_summarize_period_counts_outliers_by_direction():
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    close = 100.0 * np.cumprod(np.full(60, 1.001))
    close[30] = close[29] * 1.30   # 상승 이상치
    close[31:] = close[30] * np.cumprod(np.full(29, 1.001))
    close[45] = close[44] * 0.75   # 하락 이상치
    close[46:] = close[45] * np.cumprod(np.full(14, 1.001))
    out = dc.recompute_indicators(make_prices(dates, close), ma_windows=(5,), vol_window=10)

    s = dc.summarize_period(out, vol_window=10)

    assert s["outlier_up"] >= 1
    assert s["outlier_down"] >= 1
    assert s["outlier_up"] + s["outlier_down"] == len(
        ba.detect_return_outliers(out, z_threshold=3.0)
    )


def test_summarize_period_rejects_empty_frame():
    with pytest.raises(ValueError):
        dc.summarize_period(pd.DataFrame(), vol_window=2)


def test_evaluate_holdout_window_selects_the_requested_window():
    close = pd.Series(
        np.arange(100.0, 200.0),
        index=pd.date_range("2023-01-01", periods=100, freq="D"),
        name="Close",
    )

    preds, scores = dc.evaluate_holdout_window(close, "2023-03-01", horizon=10)

    assert preds.index.min() == pd.Timestamp("2023-03-01")
    assert preds.index.max() == pd.Timestamp("2023-03-10")
    assert len(preds) == 10
    assert list(scores.index) == ["Naive", "이동평균(7일)", "Drift"]


def test_evaluate_holdout_window_rejects_too_short_training():
    close = pd.Series(
        np.arange(100.0, 110.0),
        index=pd.date_range("2023-01-01", periods=10, freq="D"),
        name="Close",
    )

    # 홀드아웃이 2일차에 시작하면 학습 구간이 1일뿐 -> forecast_drift 가 0 으로 나눈다
    with pytest.raises(ValueError):
        dc.evaluate_holdout_window(close, "2023-01-02", horizon=5)


def test_evaluate_holdout_window_rejects_window_past_data_end():
    close = pd.Series(
        np.arange(100.0, 110.0),
        index=pd.date_range("2023-01-01", periods=10, freq="D"),
        name="Close",
    )

    with pytest.raises(ValueError):
        dc.evaluate_holdout_window(close, "2023-01-08", horizon=10)


def test_evaluate_holdout_window_reproduces_report_counterfactual():
    """REPORT.md 7.4절에 기록된 2026-06 반사실 수치를 독립 경로로 재현한다.

    대시보드가 리포트와 같은 계산을 하고 있다는 고정점이다.
    """
    df = dc.load_prepared(CSV_PATH)

    _, scores = dc.evaluate_holdout_window(df["Close"], "2026-06-01", horizon=30)

    assert scores.loc["Naive", "mae"] == pytest.approx(10578.53, abs=0.01)
    assert scores.loc["Drift", "mae"] == pytest.approx(11287.03, abs=0.01)
    assert scores.loc["이동평균(7일)", "mae"] == pytest.approx(11526.55, abs=0.01)
    assert scores["mae"].idxmin() == "Naive"
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: FAIL — `AttributeError: module 'dashboard_core' has no attribute 'summarize_period'`

- [ ] **Step 3: 최소 구현 작성**

`dashboard_core.py` 끝에 추가:

```python
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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: PASS — 14 passed

`test_evaluate_holdout_window_reproduces_report_counterfactual` 이 실패하면 **멈추고 보고한다.** 이는 대시보드의 계산이 리포트와 어긋난다는 뜻이며, 기대값을 바꿔 통과시키면 안 된다.

- [ ] **Step 5: 전체 테스트와 -W error 확인**

Run: `python -m pytest tests/ -q && python -m pytest tests/ -q -W error`
Expected: 50 passed, 둘 다 깨끔

- [ ] **Step 6: 커밋**

```bash
git add dashboard_core.py tests/test_dashboard_core.py
git commit -m "feat: 구간 요약 및 임의 홀드아웃 평가 함수 추가"
```

---

## Task 4: 파라미터 파싱과 검증

**Files:**
- Modify: `dashboard_core.py` (append)
- Modify: `tests/test_dashboard_core.py` (append)

**Interfaces:**
- Consumes: Task 3의 `MIN_TRAIN_DAYS`
- Produces:
  - `DashboardState` dataclass — 필드 `start`, `end`, `ma_windows`, `vol_window`, `holdout_start`, `horizon`
  - 범위 상수: `MA_WINDOW_RANGE = (2, 200)`, `VOL_WINDOW_RANGE = (5, 120)`, `HORIZON_RANGE = (7, 90)`, `DEFAULT_MA_WINDOWS = (7, 30, 90)`, `DEFAULT_VOL_WINDOW = 30`, `DEFAULT_HORIZON = 30`
  - `parse_params(raw: dict, data_start, data_end) -> DashboardState`

`parse_params`가 읽는 쿼리 키: `start`, `end`, `ma1`, `ma2`, `ma3`, `vol`, `holdout`, `horizon`. 모두 문자열이며 전부 선택 사항이다.

**검증 원칙**: 잘못된 입력에 예외를 던지지 않고 **기본값으로 보정**한다. URL은 사용자가 손으로 고칠 수 있고 캡처 스크립트가 만들기도 하므로, 오타 하나로 화면이 죽는 것보다 안전한 값으로 떨어지는 쪽이 낫다. 다만 보정 사실을 알 수 있도록 `dashboard.py`가 상태를 위젯에 반영한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_dashboard_core.py` 끝에 추가:

```python
DATA_START = pd.Timestamp("2023-01-01")
DATA_END = pd.Timestamp("2026-09-29")


def test_parse_params_defaults_when_empty():
    s = dc.parse_params({}, DATA_START, DATA_END)

    assert s.start == DATA_START
    assert s.end == DATA_END
    assert s.ma_windows == (7, 30, 90)
    assert s.vol_window == 30
    assert s.horizon == 30
    assert s.holdout_start == DATA_END - pd.Timedelta(days=29)  # 마지막 30일


def test_parse_params_reads_valid_values():
    s = dc.parse_params(
        {"start": "2024-01-01", "end": "2024-12-31", "ma1": "5", "ma2": "20",
         "ma3": "60", "vol": "14", "holdout": "2024-12-01", "horizon": "15"},
        DATA_START, DATA_END,
    )

    assert s.start == pd.Timestamp("2024-01-01")
    assert s.end == pd.Timestamp("2024-12-31")
    assert s.ma_windows == (5, 20, 60)
    assert s.vol_window == 14
    assert s.holdout_start == pd.Timestamp("2024-12-01")
    assert s.horizon == 15


def test_parse_params_clamps_dates_into_data_range():
    s = dc.parse_params({"start": "2020-01-01", "end": "2099-12-31"}, DATA_START, DATA_END)

    assert s.start == DATA_START
    assert s.end == DATA_END


def test_parse_params_swaps_reversed_dates():
    s = dc.parse_params({"start": "2025-06-01", "end": "2024-06-01"}, DATA_START, DATA_END)

    assert s.start == pd.Timestamp("2024-06-01")
    assert s.end == pd.Timestamp("2025-06-01")


def test_parse_params_falls_back_on_garbage_dates():
    s = dc.parse_params({"start": "어제", "end": "2024-13-45"}, DATA_START, DATA_END)

    assert s.start == DATA_START
    assert s.end == DATA_END


def test_parse_params_clamps_window_values():
    s = dc.parse_params({"ma1": "1", "ma2": "999", "vol": "0", "horizon": "500"},
                        DATA_START, DATA_END)

    assert s.ma_windows[0] == 2      # MA_WINDOW_RANGE 하한
    assert s.ma_windows[1] == 200    # MA_WINDOW_RANGE 상한
    assert s.vol_window == 5         # VOL_WINDOW_RANGE 하한
    assert s.horizon == 90           # HORIZON_RANGE 상한


def test_parse_params_falls_back_on_non_numeric_windows():
    s = dc.parse_params({"ma1": "일곱", "vol": "", "horizon": "삼십"},
                        DATA_START, DATA_END)

    assert s.ma_windows == (7, 30, 90)
    assert s.vol_window == 30
    assert s.horizon == 30


def test_parse_params_keeps_ma_windows_sorted_and_unique():
    s = dc.parse_params({"ma1": "60", "ma2": "5", "ma3": "5"}, DATA_START, DATA_END)

    assert s.ma_windows == tuple(sorted(set(s.ma_windows)))
    assert len(s.ma_windows) >= 1


def test_parse_params_pushes_holdout_back_when_window_would_overrun():
    s = dc.parse_params({"holdout": "2026-09-25", "horizon": "30"}, DATA_START, DATA_END)

    assert s.holdout_start + pd.Timedelta(days=s.horizon - 1) <= DATA_END


def test_parse_params_keeps_minimum_training_days():
    s = dc.parse_params({"holdout": "2023-01-01", "horizon": "30"}, DATA_START, DATA_END)

    train_days = (s.holdout_start - DATA_START).days
    assert train_days >= dc.MIN_TRAIN_DAYS


def test_dashboard_state_is_immutable():
    import dataclasses

    s = dc.parse_params({}, DATA_START, DATA_END)

    with pytest.raises(dataclasses.FrozenInstanceError):
        s.vol_window = 99
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: FAIL — `AttributeError: module 'dashboard_core' has no attribute 'parse_params'`

- [ ] **Step 3: 최소 구현 작성**

`dashboard_core.py` 상단 import에 다음을 추가한다:

```python
from dataclasses import dataclass
```

그리고 파일 끝에 추가:

```python
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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `python -m pytest tests/test_dashboard_core.py -q`
Expected: PASS — 25 passed

- [ ] **Step 5: 전체 테스트와 -W error 확인**

Run: `python -m pytest tests/ -q && python -m pytest tests/ -q -W error`
Expected: 61 passed, 둘 다 깨끔

- [ ] **Step 6: 커밋**

```bash
git add dashboard_core.py tests/test_dashboard_core.py
git commit -m "feat: 대시보드 파라미터 파싱 및 범위 검증 추가"
```

---

## Task 5: Streamlit UI

**Files:**
- Create: `dashboard.py`

**Interfaces:**
- Consumes: `dashboard_core` 전체 (`load_prepared`, `parse_params`, `slice_period`, `recompute_indicators`, `summarize_period`, `evaluate_holdout_window`, `DashboardState`, 범위 상수), `plots.setup_korean_font`, `plots._RED`, `plots._BLUE`, `plots._ORANGE`, `plots._AQUA`
- Produces: `streamlit run dashboard.py` 로 뜨는 앱. Task 6이 캡처한다.

이 파일은 **계산을 하지 않는다.** 모든 수치는 `dashboard_core` 호출에서 나온다.

- [ ] **Step 1: 앱 작성**

`dashboard.py`:

```python
"""비트코인 분석 대시보드 (Streamlit).

계산 로직이 없는 껍데기다. 모든 수치는 dashboard_core 를 통해
검증된 btc_analysis 함수에서 나온다.

실행: streamlit run dashboard.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import dashboard_core as dc
import plots

CSV_PATH = "data/btc_usd_2023_2026.csv"

st.set_page_config(page_title="비트코인 시계열 분석 대시보드", layout="wide")
plots.setup_korean_font()


@st.cache_data
def _load():
    return dc.load_prepared(CSV_PATH)


full = _load()
data_start, data_end = full.index.min(), full.index.max()

# URL 쿼리를 초기값으로 읽는다. 위젯 조작과 자동 캡처가 같은 경로를 쓴다.
state = dc.parse_params(dict(st.query_params), data_start, data_end)

st.title("비트코인(BTC-USD) 시계열 분석 대시보드")
st.caption(
    f"데이터 {data_start.date()} ~ {data_end.date()} · "
    "색상은 한국 금융 관행을 따릅니다 — **상승 = 빨강, 하락 = 파랑** (미국 관행과 반대). "
    "모든 수치는 리포트와 동일한 `btc_analysis.py` 함수에서 계산됩니다."
)

with st.sidebar:
    st.header("조건")
    period = st.date_input(
        "분석 기간",
        value=(state.start.date(), state.end.date()),
        min_value=data_start.date(),
        max_value=data_end.date(),
    )
    ma1 = st.number_input("이동평균 1", *dc.MA_WINDOW_RANGE, state.ma_windows[0])
    ma2 = st.number_input(
        "이동평균 2", *dc.MA_WINDOW_RANGE,
        state.ma_windows[1] if len(state.ma_windows) > 1 else dc.DEFAULT_MA_WINDOWS[1],
    )
    ma3 = st.number_input(
        "이동평균 3", *dc.MA_WINDOW_RANGE,
        state.ma_windows[2] if len(state.ma_windows) > 2 else dc.DEFAULT_MA_WINDOWS[2],
    )
    vol_window = st.number_input("변동성 윈도", *dc.VOL_WINDOW_RANGE, state.vol_window)
    log_scale = st.checkbox("가격 축을 로그로", value=False)

    st.divider()
    st.subheader("예측")
    horizon = st.number_input("홀드아웃 길이(일)", *dc.HORIZON_RANGE, state.horizon)
    holdout_start = st.date_input(
        "홀드아웃 시작일",
        value=state.holdout_start.date(),
        min_value=(data_start + pd.Timedelta(days=dc.MIN_TRAIN_DAYS)).date(),
        max_value=data_end.date(),
    )

# 위젯 값을 다시 parse_params 에 통과시켜 검증을 한 곳에만 둔다.
start, end = (period if isinstance(period, tuple) and len(period) == 2
              else (state.start.date(), state.end.date()))
state = dc.parse_params(
    {
        "start": str(start), "end": str(end),
        "ma1": str(ma1), "ma2": str(ma2), "ma3": str(ma3),
        "vol": str(vol_window), "holdout": str(holdout_start), "horizon": str(horizon),
    },
    data_start, data_end,
)

window = dc.recompute_indicators(
    dc.slice_period(full, state.start, state.end), state.ma_windows, state.vol_window
)

if window.empty:
    st.error("선택한 구간에 데이터가 없습니다. 기간을 넓혀 주세요.")
    st.stop()

# --- 1. 구간 요약 ---
st.subheader("1. 구간 요약")
summary = dc.summarize_period(window, state.vol_window)
c1, c2, c3, c4 = st.columns(4)
c1.metric("기간 누적 수익률", f"{summary['cum_return'] * 100:,.1f}%", f"{summary['n_days']}일")
c2.metric("최대 낙폭(MDD)", f"{summary['mdd'] * 100:,.1f}%",
          f"{summary['mdd_peak'].date()} → {summary['mdd_trough'].date()}", delta_color="off")
c3.metric(f"연율 변동성 평균({state.vol_window}일)",
          "계산 불가" if summary["vol_mean"] != summary["vol_mean"]
          else f"{summary['vol_mean'] * 100:,.1f}%")
c4.metric("3σ 초과일", f"{summary['outlier_up'] + summary['outlier_down']}일",
          f"상승 {summary['outlier_up']} / 하락 {summary['outlier_down']}", delta_color="off")

longest = max(state.ma_windows + (state.vol_window,))
if summary["n_days"] < longest:
    st.warning(
        f"선택 구간이 {summary['n_days']}일인데 가장 긴 윈도는 {longest}일입니다. "
        "윈도가 채워지지 않아 해당 지표는 비어 있습니다 — 기간을 넓히거나 윈도를 줄이세요."
    )

# --- 2. 가격과 이동평균 ---
st.subheader("2. 가격과 이동평균")
fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(window.index, window["Close"], color="#999999", linewidth=0.9, label="종가")
for w, color in zip(state.ma_windows, (plots._BLUE, plots._ORANGE, plots._AQUA)):
    ax.plot(window.index, window[f"ma_{w}"], color=color, linewidth=1.4, label=f"{w}일 이동평균")
if log_scale:
    ax.set_yscale("log")
ax.set_ylabel("가격 (USD)")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)
st.pyplot(fig)
plt.close(fig)

# --- 3. 수익률과 변동성 ---
st.subheader("3. 일별 수익률과 롤링 변동성")
fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
returns_pct = window["daily_return"] * 100
axes[0].bar(window.index, returns_pct,
            color=[plots._RED if v >= 0 else plots._BLUE for v in returns_pct.fillna(0)], width=1.0)
axes[0].axhline(0, color="black", linewidth=0.6)
axes[0].set_ylabel("수익률 (%)")
axes[0].grid(alpha=0.3)
axes[1].plot(window.index, window[f"vol_{state.vol_window}"] * 100,
             color="#9467bd", linewidth=1.3)
axes[1].set_ylabel("변동성 (%)")
axes[1].grid(alpha=0.3)
st.pyplot(fig)
plt.close(fig)

# --- 4. 베이스라인 예측 ---
st.subheader("4. 베이스라인 예측 비교")
st.caption(
    "방향 정확도는 예측 구간 전체에 대한 **단 한 번의 방향 베팅**이 맞았는지를 잴 뿐이며, "
    "일별 방향 예측 능력이 아닙니다. 모델 순위는 MAE·MAPE로 판단하세요."
)
try:
    preds, scores = dc.evaluate_holdout_window(full["Close"], state.holdout_start, state.horizon)
except ValueError as exc:
    st.error(f"예측을 계산할 수 없습니다: {exc}")
else:
    best = scores["mae"].idxmin()
    st.success(f"MAE 최저 모델: **{best}** (MAE {scores.loc[best, 'mae']:,.2f})")
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(preds.index, preds["actual"], color="black", linewidth=2.0, marker="o",
            markersize=3, label="실제")
    for name, style, color in (
        ("Naive", "--", plots._BLUE),
        ("이동평균(7일)", "-.", plots._ORANGE),
        ("Drift", ":", plots._AQUA),
    ):
        ax.plot(preds.index, preds[name], linestyle=style, color=color, linewidth=1.8,
                label=f"{name} (MAPE {scores.loc[name, 'mape']:.2f}%)")
    ax.set_ylabel("가격 (USD)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(scores.round(2), use_container_width=True)
```

- [ ] **Step 2: 앱이 오류 없이 뜨는지 확인**

Run:

```bash
python -m streamlit run dashboard.py --server.headless true --server.port 8501 &
sleep 12
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8501
```

Expected: `HTTP 200`

- [ ] **Step 3: 앱 로그에 예외가 없는지 확인**

Streamlit 출력에 `Traceback` 이나 `Error` 가 없어야 한다. 있으면 고치고 다시 띄운다.

- [ ] **Step 4: 쿼리 파라미터가 먹히는지 확인**

Run:

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://localhost:8501/?start=2024-01-01&end=2024-12-31&ma1=5&ma2=20&ma3=60&vol=14&holdout=2026-06-01&horizon=30"
```

Expected: `HTTP 200`

(실제 반영 여부는 Task 6의 스크린샷에서 눈으로 확인한다.)

- [ ] **Step 5: 앱 종료 후 전체 테스트**

Run: `python -m pytest tests/ -q`
Expected: 61 passed

- [ ] **Step 6: 커밋**

```bash
git add dashboard.py
git commit -m "feat: Streamlit 대시보드 UI 추가"
```

---

## Task 6: 스크린샷 자동 캡처

**Files:**
- Create: `capture_screenshots.py`
- Create (출력): `docs/dashboard/01_overview.png` ~ `05_holdout_june.png`

**Interfaces:**
- Consumes: Task 5의 `dashboard.py` (쿼리 파라미터 지원)
- Produces: PNG 5장. Task 7의 시나리오 문서가 참조한다.

**Playwright 사용 조건 (사전 검증 완료)**: `pw.chromium.launch(channel="chrome")` 로 시스템 Chrome을 쓴다. 번들 chromium은 설치돼 있지 않으므로 `channel` 없이 호출하면 실패한다.

- [ ] **Step 1: 캡처 스크립트 작성**

`capture_screenshots.py`:

```python
"""대시보드 스크린샷을 자동 캡처한다.

Streamlit 위젯을 클릭하는 대신 URL 쿼리 파라미터로 상태를 지정한다.
위젯 클릭은 Streamlit 내부 DOM 구조에 의존해 버전이 바뀌면 깨지지만,
주소를 바꾸는 방식은 그 취약점이 없다.

실행: python capture_screenshots.py   (앱이 8501 포트에 떠 있어야 한다)
"""

from __future__ import annotations

import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT_DIR = pathlib.Path("docs/dashboard")

SCENES = [
    ("01_overview", "", "기본값 — 전체 기간"),
    ("02_period_2023", "?start=2023-01-01&end=2023-12-31", "기간을 2023년으로 좁힘"),
    ("03_ma_5_20_60", "?ma1=5&ma2=20&ma3=60", "이동평균을 5/20/60으로 변경"),
    ("04_holdout_aug", "?holdout=2026-08-31&horizon=30", "홀드아웃 2026-08-31 (리포트 본 분석)"),
    ("05_holdout_june", "?holdout=2026-06-01&horizon=30", "홀드아웃 2026-06-01 (하락 구간)"),
]


def capture() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 1200})

        for name, query, description in SCENES:
            page.goto(f"{BASE}/{query}", wait_until="networkidle")
            # Streamlit 은 스크립트를 다시 돌리는 동안 "Running" 상태를 표시한다.
            page.wait_for_timeout(6000)
            path = OUT_DIR / f"{name}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"{path}  ({description})  {path.stat().st_size:,} bytes")

        browser.close()


if __name__ == "__main__":
    capture()
```

- [ ] **Step 2: 앱을 띄운 상태에서 캡처 실행**

Run:

```bash
python -m streamlit run dashboard.py --server.headless true --server.port 8501 &
sleep 12
python capture_screenshots.py
```

Expected: PNG 5개 경로와 크기가 출력된다. 각 파일이 50KB 이상이어야 한다.

- [ ] **Step 3: 5장을 모두 눈으로 확인**

Read 도구로 `docs/dashboard/01_overview.png` ~ `05_holdout_june.png` 를 **전부 직접 열어본다.** 확인 항목:

- 한글이 `□□□` 로 깨지지 않았는가
- 음수 기호가 정상인가
- **장면 2**: 기간이 2023년으로 좁혀졌고 지표가 재계산되었는가
- **장면 3**: 이동평균 범례가 5/20/60으로 바뀌었는가
- **장면 4와 5**: MAE 최저 모델이 서로 다른가. 4는 Drift, 5는 Naive 여야 한다 — **이것이 이 스크린샷 세트의 핵심이다**
- 그래프가 잘리거나 겹치지 않았는가

장면 4와 5의 MAE 최저 모델이 같다면 쿼리 파라미터가 반영되지 않은 것이다. 고치고 다시 캡처한다. **5장을 보지 않고 다음 단계로 넘어가지 않는다.**

- [ ] **Step 4: 앱 종료**

Git Bash에 `pkill`이 없을 수 있으므로 Windows 명령을 쓴다:

```bash
powershell -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -like '*streamlit*run*dashboard.py*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
```

종료 확인: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501` 가 200을 반환하지 않으면 종료된 것이다.

- [ ] **Step 5: 커밋**

```bash
git add capture_screenshots.py docs/dashboard/
git commit -m "feat: 대시보드 스크린샷 자동 캡처 스크립트 및 결과 추가"
```

---

## Task 7: 시나리오 문서와 README 갱신

**Files:**
- Create: `docs/dashboard/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 6의 스크린샷 5장과 그때 관찰한 실제 수치
- Produces: 제출 가능한 상태의 보너스 과제 산출물

- [ ] **Step 1: 시나리오 문서 작성**

`docs/dashboard/README.md` 를 아래 구조로 작성한다. **수치는 Task 6에서 실제로 본 화면에서 가져온다 — 추정하지 않는다.**

```markdown
# 비트코인 분석 대시보드 — 시나리오 설명

## 무엇인가

`REPORT.md` 의 분석을 기간·조건을 바꿔가며 탐색할 수 있게 만든 Streamlit 대시보드다.
계산은 전부 `btc_analysis.py` 의 검증된 함수가 수행하므로, 화면의 수치와 리포트의
수치는 같은 코드에서 나온다.

## 실행

(README.md 의 실행 방법과 동일한 명령을 적는다)

## 조작할 수 있는 것

(사이드바 컨트롤 목록과 각각의 범위를 표로)

## 장면별 시나리오

각 장면마다: 이미지, 설정한 조건, **관찰한 것**(실제 수치), 그리고 왜 이 장면이 의미 있는지.

### 1. 기본값 — 전체 기간
### 2. 기간을 2023년으로 좁히면
### 3. 이동평균을 5/20/60으로 바꾸면
### 4. 홀드아웃 2026-08-31 — 리포트 본 분석
### 5. 홀드아웃 2026-06-01 — 순위가 뒤집힌다

## 이 대시보드가 보여주는 것

장면 4와 5를 나란히 두는 이유를 서술한다: 같은 모델, 같은 코드, 홀드아웃 구간만
바꿨는데 MAE 최저 모델이 Drift 에서 Naive 로 뒤집힌다. `REPORT.md` 7.4절이 글로
주장한 "Drift 의 승리는 구간 운에 가깝다"를 독자가 손으로 확인할 수 있다.
```

- [ ] **Step 2: 문서의 수치가 스크린샷과 일치하는지 확인**

스크린샷을 다시 열어 문서에 적은 수치와 대조한다. 하나라도 어긋나면 문서를 고친다.

- [ ] **Step 3: README.md에 대시보드 섹션 추가**

`README.md` 의 실행 방법 섹션 뒤에 추가한다:

```markdown
## 대시보드 (보너스 과제)

기간·이동평균·변동성 윈도·예측 홀드아웃 구간을 바꿔가며 분석을 탐색할 수 있다.

```bash
streamlit run dashboard.py
```

브라우저가 자동으로 열린다(기본 http://localhost:8501). URL 쿼리로 상태를 지정할 수도 있다:

```
http://localhost:8501/?start=2024-01-01&end=2024-12-31&ma1=5&ma2=20&ma3=60&holdout=2026-06-01
```

스크린샷과 시나리오 설명: [docs/dashboard/README.md](docs/dashboard/README.md)

계산은 전부 `btc_analysis.py` 의 검증된 함수가 수행한다. `dashboard.py` 는 위젯과
렌더링만 담당하고, 파라미터 검증·구간 슬라이싱은 테스트된 `dashboard_core.py` 에 있다.
```

- [ ] **Step 4: 링크와 파일 존재 확인**

Run:

```bash
ls docs/dashboard/
grep -c '!\[' docs/dashboard/README.md
grep -n 'TBD\|TODO\|XXX' docs/dashboard/README.md README.md || echo "플레이스홀더 없음"
```

Expected: PNG 5개 존재, 이미지 링크 5개, 플레이스홀더 없음

- [ ] **Step 5: 전체 테스트 재확인**

Run: `python -m pytest tests/ -q && python -m pytest tests/ -q -W error`
Expected: 61 passed, 둘 다 깨끔

- [ ] **Step 6: 커밋**

```bash
git add docs/dashboard/README.md README.md
git commit -m "docs: 대시보드 시나리오 설명 및 실행 방법 추가"
```

---

## Self-Review

**1. 스펙 커버리지**

| 스펙 요구사항 | 담당 태스크 |
| --- | --- |
| Streamlit이 `btc_analysis` 직접 import | Task 2~5 (`dashboard_core` 가 `ba.*` 만 호출) |
| 3계층 구조 | Task 2~5 |
| `load_prepared` / `slice_period` / `recompute_indicators` | Task 2 |
| `summarize_period` / `evaluate_holdout_window` | Task 3 |
| `parse_params` / `DashboardState` | Task 4 |
| 기간 선택 | Task 5 사이드바 |
| 이동평균 구간 선택 | Task 5 사이드바 |
| 변동성 윈도 + 구간 요약 | Task 5 섹션 1·3 |
| 홀드아웃 시작일 선택 | Task 5 사이드바 + 섹션 4 |
| 지표를 구간에서 재계산 | Task 2 (`recompute_indicators`), 테스트로 고정 |
| 윈도 미충족 시 경고 | Task 5 (`st.warning`) |
| 최소 학습 2일 강제 | Task 3 (`MIN_TRAIN_DAYS`), Task 4 (파싱 시 보정) |
| 교차 검증 고정점 (2026-06 반사실) | Task 3 테스트 |
| 상승=빨강 / 하락=파랑 | Task 5 (`plots._RED`/`_BLUE` import), 화면 캡션 |
| 한글·폰트·음수기호 | Task 5 (`plots.setup_korean_font()`) |
| 방향 정확도 설명 한 줄 | Task 5 섹션 4 캡션 |
| URL 쿼리 파라미터 | Task 4 (파싱), Task 5 (`st.query_params`), Task 6 (활용) |
| 스크린샷 5장 | Task 6 |
| 시나리오 문서 | Task 7 |
| README 실행 방법 | Task 7 |
| requirements 갱신 | Task 1 |
| `plots.py` 재사용은 색상 상수만 | Task 5 |
| 기존 산출물 수정 금지 | Global Constraints |

누락 없음.

**2. 플레이스홀더 점검**

실행 시점에 채우도록 남긴 자리는 2곳이며 모두 "실제 출력에서 가져오라"는 지시가 붙어 있다: Task 1의 streamlit 버전, Task 7의 시나리오 문서 수치. 추정값 사용을 명시적으로 금지했다.

**3. 타입·이름 일관성**

- `load_prepared` 가 `add_returns` 를 하지 않고 `recompute_indicators` 가 한다 — Task 2 구현·테스트·docstring이 일치
- `summarize_period(df, vol_window)` 의 2번째 인자를 Task 5가 `state.vol_window` 로 전달 — 일치
- `evaluate_holdout_window(close, holdout_start, horizon)` 를 Task 5가 `full["Close"]`(전 구간 종가)로 호출 — 의도적이다. 예측은 선택 기간이 아니라 전체 데이터 기준으로 평가해야 리포트와 비교 가능하다
- `DashboardState.ma_windows` 가 중복 제거 후 1~3개일 수 있으므로 Task 5가 `zip` 으로 색상과 짝지어 개수에 안전하게 대응 — 일치
- `MIN_TRAIN_DAYS` 를 Task 3이 정의하고 Task 4·Task 5가 소비 — 정의가 소비보다 앞선다
- `MA_WINDOW_RANGE` 등 범위 상수를 Task 4가 정의하고 Task 5의 `st.number_input` 이 언패킹해 사용 — 일치
- 테스트 누적 개수 7 → 14 → 25, 전체 36 + 25 = 61 — Task 5·7의 기대값과 합산 일치
