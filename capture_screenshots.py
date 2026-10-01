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
            page.set_viewport_size({"width": 1600, "height": 1200})
            page.goto(f"{BASE}/{query}", wait_until="networkidle")
            # Streamlit 은 스크립트를 다시 돌리는 동안 "Running" 상태를 표시한다.
            page.wait_for_timeout(6000)
            # Streamlit의 실제 스크롤 컨테이너는 document.body 가 아니라
            # data-testid="stMain" 내부 div 다. full_page=True 는 document
            # 높이를 기준으로 하기 때문에 뷰포트를 콘텐츠 높이에 맞게 늘린 뒤
            # 다시 찍어야 아래쪽 섹션(예측 비교 등)이 잘리지 않는다.
            content_height = page.evaluate(
                "document.querySelector('[data-testid=\"stMain\"]').scrollHeight"
            )
            page.set_viewport_size({"width": 1600, "height": content_height + 50})
            page.wait_for_timeout(1000)
            path = OUT_DIR / f"{name}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"{path}  ({description})  {path.stat().st_size:,} bytes")

        browser.close()


if __name__ == "__main__":
    capture()
