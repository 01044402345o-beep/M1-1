"""분석 결과를 PNG로 저장하는 함수들.

계산 로직을 포함하지 않는다. btc_analysis가 만든 결과를 받아 그리기만 한다.

색상은 dataviz 스킬의 팔레트(docs/../.superpowers 참고)를 기반으로 하되,
matplotlib 정적 PNG 보고서에 맞게 다음 역할로 재배정했다:

- 범주형(계열 구분): blue #2a78d6 / orange #eb6834 / aqua #1baf7a
  (슬롯 1·2·3 — 전 슬롯 조합 검증 통과, blue/orange/red 조합은 색각 이상자
  기준 인접 대비가 부족해 red 대신 aqua를 사용)
- 발산형(수익률 양/음): blue #2a78d6 <-> red #e34948, 중립 회색 #f0efec
  (원안의 녹색/빨강 조합은 색각 이상 시뮬레이션에서 CVD 대비 4.1로 실패하여
  팔레트의 발산형 쌍으로 교체. 음수=red, 양수=blue로 통일해 수익률 막대
  그래프와 히트맵에서 같은 규칙을 쓴다)
- 중립 톤: muted #898781(보조 선/격자), primary ink #0b0b0b(기준선·실제값)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

import btc_analysis as ba

FIG_DPI = 150
KOREAN_FONT = "Malgun Gothic"  # Task 1에서 사용 불가로 확인되면 그 결과에 맞춰 교체한다

# dataviz 팔레트에서 가져온 색상 역할
_BLUE = "#2a78d6"
_ORANGE = "#eb6834"
_AQUA = "#1baf7a"
_RED = "#e34948"
_NEUTRAL_GRAY = "#f0efec"
_MUTED = "#898781"
_SECONDARY_INK = "#52514e"
_PRIMARY_INK = "#0b0b0b"
_GRIDLINE = "#e1e0d9"

# 수익률 발산형 컬러맵: 음수=red, 0=중립 회색, 양수=blue
_DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "btc_diverging", [_RED, _NEUTRAL_GRAY, _BLUE]
)


def setup_korean_font() -> None:
    """한글 레이블이 깨지지 않도록 폰트를 설정한다."""
    matplotlib.rcParams["font.family"] = KOREAN_FONT
    matplotlib.rcParams["axes.unicode_minus"] = False  # 음수 기호 깨짐 방지


# 모듈을 import하는 시점에 한 번 적용해 둔다. 이 모듈의 모든 그리기 함수는
# 한글 레이블을 쓰므로, 호출자가 setup_korean_font()를 직접 부르는 것을
# 잊어도(Step 5 생성 스크립트는 명시적으로 호출한다) 깨진 글자(□□□)가
# 나오지 않도록 안전장치로 둔다. 멱등이므로 다시 호출해도 무해하다.
setup_korean_font()


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
        ax.plot(df.index, df["Close"], color=_MUTED, linewidth=0.8, label="종가")
        ax.plot(df.index, df["ma_7"], color=_BLUE, linewidth=1.2, label="7일 이동평균")
        ax.plot(df.index, df["ma_30"], color=_ORANGE, linewidth=1.4, label="30일 이동평균")
        ax.plot(df.index, df["ma_90"], color=_AQUA, linewidth=1.8, label="90일 이동평균")
        ax.set_yscale(scale)
        ax.set_title(title)
        ax.set_ylabel("가격 (USD)")
        ax.legend(loc="upper left")
        ax.grid(alpha=0.6, color=_GRIDLINE, linewidth=0.8)

    axes[1].set_xlabel("날짜")
    return _save(fig, out_path)


def plot_returns_volatility(df: pd.DataFrame, out_path: str | Path) -> Path:
    """일별 수익률과 30일 롤링 변동성."""
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    returns_pct = df["daily_return"] * 100
    colors = np.where(returns_pct >= 0, _BLUE, _RED)
    axes[0].bar(df.index, returns_pct, color=colors, width=1.0)
    axes[0].axhline(0, color=_PRIMARY_INK, linewidth=0.6)
    axes[0].set_title("일별 수익률 (%)")
    axes[0].set_ylabel("수익률 (%)")
    axes[0].grid(alpha=0.6, color=_GRIDLINE, linewidth=0.8)

    axes[1].plot(df.index, df["vol_30"] * 100, color="#4a3aa7", linewidth=1.3)
    mean_vol = df["vol_30"].mean() * 100
    axes[1].axhline(mean_vol, color=_SECONDARY_INK, linestyle="--", linewidth=1.0,
                    label=f"평균 {mean_vol:.0f}%")
    axes[1].set_title("30일 롤링 변동성 (연율화, %)")
    axes[1].set_ylabel("변동성 (%)")
    axes[1].set_xlabel("날짜")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.6, color=_GRIDLINE, linewidth=0.8)

    return _save(fig, out_path)


def plot_monthly_heatmap(pivot: pd.DataFrame, out_path: str | Path) -> Path:
    """연도 x 월 월별 수익률 히트맵.

    0을 중립 회색으로 두는 발산형(blue<->red) 컬러맵을 쓴다. 양수/음수를
    즉시 구분하기 위함이며, 일별 수익률 막대 그래프와 동일한 색 규칙
    (음수=red, 양수=blue)을 사용해 보고서 전체에서 일관성을 유지한다.
    """
    values = pivot.to_numpy(dtype=float) * 100
    limit = float(np.nanmax(np.abs(values))) if np.isfinite(values).any() else 1.0

    fig, ax = plt.subplots(figsize=(12, 1.2 * len(pivot) + 2.5))
    mesh = ax.imshow(values, cmap=_DIVERGING_CMAP, vmin=-limit, vmax=limit, aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{m}월" for m in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(y) for y in pivot.index])
    ax.set_title("월별 수익률 히트맵 (%) — 같은 달이 연도별로 일관적인지 확인")

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            if np.isfinite(values[i, j]):
                # 채도가 짙은 칸은 흰 글자, 옅은 칸(0 근처)은 어두운 글자로
                # 대비를 유지한다 (칸 색은 데이터, 글자는 읽기용).
                text_color = "white" if abs(values[i, j]) / limit > 0.55 else _PRIMARY_INK
                ax.text(j, i, f"{values[i, j]:.1f}", ha="center", va="center",
                        fontsize=9, color=text_color)

    fig.colorbar(mesh, ax=ax, label="수익률 (%)")
    return _save(fig, out_path)


def plot_weekday_box(df: pd.DataFrame, out_path: str | Path) -> Path:
    """요일별 수익률 분포 박스플롯.

    평균만 보면 소수 극단값에 끌려가므로 분포 전체를 보여준다.
    """
    returns = df["daily_return"].dropna() * 100
    groups = [returns[returns.index.dayofweek == i].values for i in range(7)]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.boxplot(
        groups,
        tick_labels=ba.WEEKDAY_NAMES_KO,
        showmeans=True,
        boxprops=dict(color=_BLUE),
        whiskerprops=dict(color=_SECONDARY_INK),
        capprops=dict(color=_SECONDARY_INK),
        medianprops=dict(color=_ORANGE, linewidth=1.6),
        meanprops=dict(marker="D", markerfacecolor=_RED, markeredgecolor=_RED, markersize=5),
        flierprops=dict(markeredgecolor=_MUTED, markersize=4),
    )
    ax.axhline(0, color=_PRIMARY_INK, linewidth=0.6)
    ax.set_title("요일별 일간 수익률 분포 (%) — 비트코인은 주말에도 거래된다")
    ax.set_ylabel("수익률 (%)")
    ax.set_xlabel("요일")
    ax.grid(alpha=0.6, axis="y", color=_GRIDLINE, linewidth=0.8)

    return _save(fig, out_path)


def plot_baseline_forecast(predictions: pd.DataFrame, scores: pd.DataFrame,
                           out_path: str | Path) -> Path:
    """홀드아웃 구간의 실제값과 베이스라인 예측 비교."""
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(predictions.index, predictions["actual"], color=_PRIMARY_INK, linewidth=2.0,
            marker="o", markersize=5, label="실제")

    styles = {"Naive": ("--", _BLUE), "이동평균(7일)": ("-.", _ORANGE), "Drift": (":", _AQUA)}
    for name, (style, color) in styles.items():
        if name in predictions.columns:
            mape = scores.loc[name, "mape"]
            ax.plot(predictions.index, predictions[name], linestyle=style, linewidth=1.8,
                    color=color, label=f"{name} (MAPE {mape:.1f}%)")

    ax.set_title(f"베이스라인 예측 비교 — 홀드아웃 {len(predictions)}일")
    ax.set_ylabel("가격 (USD)")
    ax.set_xlabel("날짜")
    ax.legend(loc="best")
    ax.grid(alpha=0.6, color=_GRIDLINE, linewidth=0.8)

    return _save(fig, out_path)
