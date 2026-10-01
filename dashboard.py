"""비트코인 분석 대시보드 (Streamlit).

지표·메트릭·예측을 직접 계산하지 않는다. 그런 수치는 모두 dashboard_core 를
통해 검증된 btc_analysis 함수에서 나온다. 이 파일에 남아 있는 산술은 표시용
집계뿐이다(3σ 초과일 합계, 가장 긴 윈도 계산, MAE 최저 모델 선택 등).

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
st.caption(
    "본 저장소는 데이터 분석 학습 산출물이다. 투자 권유나 투자 조언이 아니다. "
    "Yahoo Finance 데이터는 **개인적·비상업적 용도**로만 사용이 허용된다."
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
        max_value=(data_end - pd.Timedelta(days=int(horizon) - 1)).date(),
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
c1.metric("기간 누적 수익률", f"{summary['cum_return'] * 100:,.1f}%", f"{summary['n_days']}일",
          delta_color="off")
c2.metric("최대 낙폭(MDD)", f"{summary['mdd'] * 100:,.1f}%",
          f"{summary['mdd_peak'].date()} → {summary['mdd_trough'].date()}", delta_color="off")
c3.metric(f"연율 변동성 평균({state.vol_window}일)",
          "계산 불가" if pd.isna(summary["vol_mean"])
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
    "이 예측은 위의 기간 선택과 무관하게 **전체 데이터셋**을 기준으로 계산됩니다. "
    "구간이 아니라 아래 사이드바의 '홀드아웃 시작일'과 '홀드아웃 길이'가 이 결과를 결정합니다."
)
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
    fig.autofmt_xdate()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(
        scores.round(2),
        column_config={
            "mae": st.column_config.NumberColumn("MAE", format="%.2f"),
            "mape": st.column_config.NumberColumn("MAPE", format="%.2f%%"),
            "direction_accuracy": st.column_config.NumberColumn("방향 정확도", format="%.0f%%"),
        },
    )
