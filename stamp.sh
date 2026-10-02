#!/usr/bin/env bash
# 회차를 검증 → 커밋 → OTS 스탬프 → 스탬프까지 커밋.
# 검증 실패면 아무것도 커밋하지 않는다(규칙을 기전으로 만드는 자리).
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: ./stamp.sh entries/YYYY-MM.md"; exit 2; }
ENTRY="$1"
[ -f "$ENTRY" ] || { echo "없는 파일: $ENTRY"; exit 2; }

echo "▌ 1/4 형식 검증"
python3 validate.py "$ENTRY"

echo "▌ 2/4 회차 커밋"
git add "$ENTRY"
git commit -m "회차 $(basename "$ENTRY" .md)"

echo "▌ 3/4 OpenTimestamps 스탬프"
if command -v ots >/dev/null 2>&1; then
  ots stamp "$ENTRY"
  git add "$ENTRY.ots"
  git commit -m "회차 $(basename "$ENTRY" .md) — OTS 스탬프"
  echo "   비트코인 확인까지 몇 시간 걸린다. 나중에 'ots upgrade $ENTRY.ots' 후 재커밋."
else
  echo "   ⚠ ots 미설치 — 스탬프를 건너뛴다. 이게 없으면 커밋 날짜는 위조 가능해서"
  echo "     원장이 B등급이 되지 않는다. pip install opentimestamps-client"
  exit 1
fi

echo "▌ 4/4 완료 — git push 하면 시계가 시작된다"
