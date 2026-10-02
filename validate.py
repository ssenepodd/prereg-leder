#!/usr/bin/env python3
"""사전공개 회차 검증기 — 형식 설계의 결정을 약속이 아니라 기전으로 만든다.

  python3 validate.py entries/2026-09.md

ERROR 가 하나라도 있으면 종료코드 1. 커밋 훅에 걸어 두면 규칙 위반이 물리적으로 안 올라간다.
표준 라이브러리만 쓴다(PyYAML 불필요).
"""
import sys, re, datetime, pathlib

# 결정 3 — 금액을 싣지 않는다. 스키마에 존재하면 안 되는 키.
MONEY_KEYS = ("amount", "krw", "won", "nav", "balance", "value_krw",
              "평가금액", "매입금액", "잔고", "원화", "수익금")
# 어법 — 기록이지 조언이 아니다.
ADVICE_WORDS = ("추천", "유망", "강력매수", "매수의견", "적극", "필수", "확실",
                "목표주가", "급등", "수익 인증", "수익인증")
MIN_HORIZON_DAYS = 90
# 반증 불가능한 논지의 전형 (FALSIFIER-GUIDE.md 「논지 자체를 반증 가능하게 쓰기」)
VAGUE_CLAIM_WORDS = ("저평가", "고평가", "성장성", "매력적", "우수", "탄탄", "견조",
                     "기대된다", "전망된다", "수급이 좋", "턴어라운드가 기대",
                     "장기적으로", "저점", "바닥")


def parse_front_matter(text):
    """--- 로 감싼 앞머리를 아주 얕게 파싱한다. 중첩 리스트/스칼라만 다룬다."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, "앞머리(--- ... ---)를 찾지 못했다"
    return m.group(1), None


def blocks(fm, key):
    """theses / positions 같은 리스트 항목을 '- ' 단위 덩어리로 자른다."""
    m = re.search(rf"^{key}:\s*(.*?)(?=^\w|\Z)", fm, re.S | re.M)
    if not m:
        return []
    body = m.group(1)
    if body.strip() in ("[]", "null", ""):
        return []
    out, cur = [], None
    for line in body.split("\n"):
        if re.match(r"^\s*-\s", line):
            if cur is not None:
                out.append("\n".join(cur))
            cur = [re.sub(r"^\s*-\s", "  ", line)]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        out.append("\n".join(cur))
    return [b for b in out if b.strip() and not b.strip().startswith("#")]


def field(block, name):
    m = re.search(rf"^\s*{name}:\s*(?:>|\|)?\s*(.*?)(?=^\s*\w+:|\Z)", block, re.S | re.M)
    if not m:
        return None
    return " ".join(m.group(1).split()).strip() or None


def main(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    fm, err = parse_front_matter(text)
    errs, warns = ([err] if err else []), []
    if err:
        report(path, errs, warns); return 1

    is_example = "EXAMPLE" in (field(fm, "id") or "")
    level = (field(fm, "level") or "L1").upper()

    # ── 결정 3: 금액 금지 (전 수준 공통) ──
    for k in MONEY_KEYS:
        if re.search(rf"^\s*{re.escape(k)}\s*:", fm, re.M | re.I):
            errs.append(f"결정 3 위반 — 금액성 필드 '{k}' 가 있다. 비중 %만 싣는다")

    # ── 날짜 ──
    cut, pub = field(fm, "cut"), field(fm, "published")
    try:
        d_cut = datetime.date.fromisoformat(cut)
        d_pub = datetime.date.fromisoformat(pub)
        if d_pub < d_cut:
            errs.append("published 가 cut 보다 이르다 — 공개일은 기준일 이후여야 한다")
        if (d_pub - d_cut).days > 45:
            warns.append(f"공개 지연이 {(d_pub-d_cut).days}일이다. 길수록 기록의 신선도가 떨어진다")
    except (TypeError, ValueError):
        errs.append("cut / published 가 YYYY-MM-DD 형식이 아니다")
        d_pub = None

    # ── 논지: L1부터 필수 ──
    ths = blocks(fm, "theses")
    if not ths:
        errs.append("논지가 0건이다 — L1에서도 논지는 원장의 본체다")

    seen = set()
    for i, b in enumerate(ths, 1):
        tid = field(b, "id") or f"#{i}"
        if tid in seen:
            errs.append(f"[{tid}] 논지 id 가 중복이다")
        seen.add(tid)

        claim, fals, ev = field(b, "claim"), field(b, "falsifier"), field(b, "evaluate_on")
        if not claim:
            errs.append(f"[{tid}] claim 이 없다")
        else:
            vague = [w for w in VAGUE_CLAIM_WORDS if w in claim]
            if vague and not re.search(r"\d", claim):
                warns.append(f"[{tid}] 논지가 반증 불가능해 보인다 — {'/'.join(vague)} 는 "
                             f"관측치가 아니다. 숫자가 붙은 주장으로 다시 쓸 것")
        if not fals:
            errs.append(f"[{tid}] falsifier 가 없다 — 없으면 일기장이 된다")
        if not ev:
            errs.append(f"[{tid}] evaluate_on 이 없다 — 없으면 영원히 미판정으로 남는다")

        # 반증조건 품질 — 시험 1·2·3 (FALSIFIER-GUIDE.md)
        if fals:
            has_num = bool(re.search(r"\d", fals))
            has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{4}년|\d+분기|\d+Q", fals))
            price_only = (re.search(r"주가|주가가|가격", fals)
                          and not re.search(r"매출|이익|점유율|비중|가동률|출하|수주|금리|"
                                            r"YoY|컨센서스|지분율|잔고|생산|capa|CAPA", fals))
            if not has_num:
                errs.append(f"[{tid}] 반증조건에 임계값(숫자)이 없다 — 관측 불가라 판정불가가 된다")
            if not has_date:
                warns.append(f"[{tid}] 반증조건 안에 기한이 안 보인다 — evaluate_on 과 별개로 명시할 것")
            if price_only:
                warns.append(f"[{tid}] 반증조건이 주가로만 돼 있다 — 이건 손절 규칙이지 반증조건이 아닐 수 있다")

        # 기간
        if ev and d_pub:
            try:
                days = (datetime.date.fromisoformat(ev) - d_pub).days
                if days <= 0:
                    errs.append(f"[{tid}] evaluate_on 이 공개일보다 이르거나 같다")
                elif days < MIN_HORIZON_DAYS:
                    warns.append(f"[{tid}] 검증 기간이 {days}일이다 — {MIN_HORIZON_DAYS}일 미만은 "
                                 f"대개 논지가 아니라 트레이딩이다")
            except ValueError:
                errs.append(f"[{tid}] evaluate_on 이 YYYY-MM-DD 형식이 아니다")

    # ── L2 이상: 포지션 ──
    pos = blocks(fm, "positions")
    if level in ("L2", "L3"):
        if not pos:
            errs.append(f"{level} 인데 포지션이 0건이다 — 수준을 골랐으면 그 안에서는 전량이다(결정 1)")
        tot = 0.0
        for i, b in enumerate(pos, 1):
            nm = field(b, "name") or field(b, "ticker") or f"#{i}"
            th = field(b, "thesis")
            if not th:
                errs.append(f"[{nm}] thesis 가 없다 — 논지 없는 포지션은 실을 수 없다(결정 1)")
            elif th not in seen:
                errs.append(f"[{nm}] thesis '{th}' 가 theses 에 없다")
            if not field(b, "first_cut"):
                errs.append(f"[{nm}] first_cut 이 없다 — 보유기간이 검증 불가해진다")
            w = field(b, "weight")
            try:
                w = float(w); tot += w
                if w > 100 or w <= 0:
                    errs.append(f"[{nm}] weight {w} 가 비중(%)으로 보이지 않는다")
                if w > 1000:
                    errs.append(f"[{nm}] weight 가 금액으로 보인다(결정 3)")
            except (TypeError, ValueError):
                errs.append(f"[{nm}] weight 가 숫자가 아니다")
        if tot > 100.5:
            errs.append(f"비중 합이 {tot:.1f}% 다 — 100% 를 넘는다")
        if re.search(r"^turnover:\s*null", fm, re.M) or not re.search(r"^turnover:", fm, re.M):
            errs.append(f"{level} 인데 turnover 집계가 없다 — 월말 스냅샷은 월중 매매를 못 잡는다")
    elif pos:
        warns.append("level 이 L1 인데 positions 가 채워져 있다 — 의도한 수준인지 확인할 것")

    # ── 어법 ──
    body = text[len(fm) + 8:] if fm else text
    for w in ADVICE_WORDS:
        if w in body or w in fm:
            warns.append(f"어법 — '{w}' 가 있다. 기록이지 조언이 아니다(결정 3의 취지)")

    if is_example:
        warns.append("EXAMPLE 파일이다 — 공개 리포로 옮기기 전에 삭제할 것")

    report(path, errs, warns)
    return 1 if errs else 0


def report(path, errs, warns):
    print(f"\n▌ {path}")
    for e in errs:
        print(f"  ERROR  {e}")
    for w in warns:
        print(f"  WARN   {w}")
    if not errs and not warns:
        print("  OK — 형식 통과")
    elif not errs:
        print(f"  통과 (경고 {len(warns)}건 — 확인 권고)")
    else:
        print(f"  실패 — ERROR {len(errs)}건")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: validate.py <entry.md> [entry.md ...]"); sys.exit(2)
    sys.exit(max(main(p) for p in sys.argv[1:]))
