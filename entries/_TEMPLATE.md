---
id: YYYY-MM
cut: YYYY-MM-DD              # 포지션 기준일 (월말)
published: YYYY-MM-DD        # 공개일 = 평가 시작점 (cut + 3~7영업일)
level: L1                    # L1 논지만 / L2 +포지션 / L3 +성과
benchmark: KOSPI

# ── L2 이상에서만 채운다. L1이면 통째로 비워 둔다 ──
positions: []
# - ticker: "000000"
#   name: 종목명
#   weight: 0.0              # 위험자산 대비 %. ★금액 금지
#   first_cut: YYYY-MM-DD    # 이 종목이 처음 등재된 회차
#   thesis: T-YYYY-MM-NN
cash_weight: null

# ── L1부터 필수. 이게 원장의 본체다 ──
theses:
  - id: T-YYYY-MM-01
    claim: >
      (반증 가능한 형태로. "저평가" "성장성" 같은 말은 시험을 통과하지 못한다.
       FALSIFIER-GUIDE.md 참조)
    falsifier: >
      ([관측치] + [임계값] + [기한] 세 조각이 다 있어야 한다.
       주가만 쓰면 손절 규칙이지 반증조건이 아니다)
    evaluate_on: YYYY-MM-DD  # ★등록 시점에 박는다. 나중에 못 옮긴다
    horizon_days: 0

# ── L2 이상. 월말 스냅샷이 못 잡는 월중 매매를 메운다 ──
turnover: null
# monthly_turnover_pct: 0.0
# avg_holding_days: 0.0
# round_trips: 0
---

## 이번 회차

(판단, 지난 회차 대비 변경과 그 이유. 추천이 아니라 기록의 어법으로.)

## 지난 회차 대비

(신규 등록 논지 / 기한 도래 예정 논지. 결과는 여기 쓰지 않는다 — outcomes/ 에 잡이 쓴다.)
