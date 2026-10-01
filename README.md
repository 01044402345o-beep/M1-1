# 비트코인(BTC-USD) 시계열 분석

2023-01-01 ~ 2026-09-29 비트코인 일봉 데이터를 분석해 추세·변동성·반복 패턴을 확인하고,
베이스라인 예측의 한계를 검증한 프로젝트.

**분석 결과: [REPORT.md](REPORT.md)**

## 프로젝트 구조

```
.
├── README.md                  # 이 문서
├── REPORT.md                  # 분석 리포트 (핵심 산출물)
├── requirements.txt           # 패키지 버전 고정
├── check_env.py               # 설치 패키지 버전·한글 폰트 확인용 스크립트
├── fetch_data.py               # 데이터 수집 스크립트 (1회 실행, 노트북과 분리)
├── btc_analysis.py            # 계산 로직 (18개 공개 함수)
├── plots.py                   # 시각화 함수 5개 + 한글 폰트 설정
├── analysis.ipynb             # 분석 노트북 (12개 셀, 실행 결과 저장됨)
├── data/
│   └── btc_usd_2023_2026.csv  # 수집된 일봉 데이터 (1,368행)
├── images/                    # 노트북에서 생성한 차트 PNG 5개
│   ├── 01_price_trend_ma.png
│   ├── 02_returns_volatility.png
│   ├── 03_monthly_heatmap.png
│   ├── 04_weekday_boxplot.png
│   └── 05_baseline_forecast.png
├── tests/                     # btc_analysis.py / plots.py 검증 테스트 35개
│   ├── test_btc_analysis.py
│   └── test_plots.py
└── docs/superpowers/           # 코딩 전에 작성한 설계 스펙·구현 계획 문서
    ├── specs/
    └── plans/
```

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 데이터 수집 (data/ 에 CSV가 이미 있으므로 생략 가능)
python fetch_data.py

# 3. 테스트 실행 (계산 로직 검증, 35개)
python -m pytest tests/ -q

# 4. 분석 노트북 실행
jupyter notebook analysis.ipynb
# 또는 전체 자동 실행:
python -m jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

노트북은 위에서 아래로 순서대로 실행한다. 네트워크에 접근하지 않고 `data/`의 CSV만 읽으므로
언제 실행해도 같은 결과가 나온다.

## 설계 원칙

- **수집과 분석 분리**: 노트북이 매번 데이터를 새로 받으면 실행 시점에 따라 결과가 달라진다.
  `fetch_data.py`로 한 번만 받아 CSV로 고정해 두었기 때문에, 노트북은 언제 실행해도 같은 결과를 낸다.
- **계산 로직은 테스트된 모듈에만**: 노트북 셀 안의 계산식은 단위 테스트를 할 수 없다.
  그래서 모든 계산을 `btc_analysis.py`에 순수 함수로 두고, `tests/`의 35개 테스트로 검증했다.

## 데이터 출처 및 라이선스 주의

- 출처: Yahoo Finance (`yfinance` 라이브러리)
- 기간: 2023-01-01 ~ 2026-09-29, 일(日) 단위 (1,368행).
  수집 목표는 2026-09-30까지였으나, 수집 시점에 Yahoo Finance가 해당 일봉을 아직 확정하지 않아
  실제 데이터는 09-29까지만 포함되었다.
- Yahoo Finance 데이터는 **개인적·비상업적 용도**로만 사용이 허용된다.
  본 저장소의 `data/` CSV는 분석 재현 목적으로만 포함되었으며 상업적 재배포를 허용하지 않는다.

## 면책

본 저장소는 데이터 분석 학습 산출물이다. 투자 권유나 투자 조언이 아니다.

## 개발 환경

- Python **3.14.4** (시스템 Python). 모든 패키지가 3.14에서 문제없이 설치되어
  별도의 가상환경(venv)을 만들지 않았다.
- 주요 패키지 버전 (`requirements.txt`): pandas 3.0.3, numpy 2.5.1, matplotlib 3.11.2,
  yfinance 1.7.0, pytest 9.1.1, jupyter 1.1.1
- 차트의 한글 라벨은 `Malgun Gothic` 폰트를 사용한다. 이 저장소는 해당 폰트가 설치된
  Windows 환경에서 작업했으며, 다른 OS에서 재현할 경우 한글을 지원하는 대체 폰트를
  `plots.py`의 `setup_korean_font()`에 지정해야 한다.
- 차트의 상승/하락 색상은 **한국 금융 관행**(상승 = 빨강, 하락 = 파랑)을 따른다.
  미국식 관행(상승 = 초록, 하락 = 빨강)과 반대이므로 그래프를 볼 때 유의한다.
