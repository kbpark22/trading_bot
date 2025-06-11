# Trading Bot 사용설명서 (README)

## 개요
이 봇은 Upbit 거래소의 API를 이용하여 지정한 코인에 대해 자동으로 매수/매도 주문을 실행하는 Python 기반 트레이딩 봇입니다. 

## 주요 기능
- 지정한 CSV 파일(`symbols.csv`)에 따라 여러 코인 자동 매매
- 포트폴리오 전체 평가금액 기록(`portfolio_valuation.csv`)
- 모든 자산 일괄 매도 기능 (`--sell-all` 옵션)
- 거래 내역 및 로그 파일 기록

## 준비사항
1. **Python 3.x** 설치
2. **필수 라이브러리 설치**
   ```bash
   pip install ccxt
   ```
3. **API 키 준비**
   - `apikeys.py` 파일에 `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY` 변수로 API 키를 입력

4. **심볼 및 매매 파라미터 파일 준비**
   - `symbols.csv` 파일 예시:
     | symbol      | avg_days | target_ratio | buy_ratio |
     |-------------|----------|--------------|-----------|
     | BTC/KRW    | 5        | 1.02         | 0.3       |
     | ETH/KRW    | 7        | 1.01         | 0.2       |

## 실행 방법

이 트레이딩 봇은 단순히 한 번 실행하는 것이 아니라, crontab(스케줄러)을 이용해 매일 정해진 시간(UTC 23:55, KST 08:55)에 자동으로 주기적으로 실행하는 것이 기본 사용 방식입니다.

### crontab을 이용한 자동 실행 (리눅스 기준)
1. 터미널에서 crontab 편집:
   ```bash
   crontab -e
   ```
2. 아래와 같이 등록 (UTC 기준 23:55, 즉 KST 08:55에 백그라운드로 실행)
   ```bash
   55 23 * * * nohup /usr/bin/python3 /경로/트레이딩봇/trading_bot.py &
   ```
   - `nohup`과 `&`를 사용하면 세션이 끊겨도 백그라운드에서 계속 실행됩니다.
   - `/usr/bin/python3` 경로와 파일 경로는 환경에 맞게 수정하세요.

> 윈도우 환경에서는 작업 스케줄러(Task Scheduler)에서 같은 시간에 자동 실행하도록 등록하세요.

### 참고: 수동 실행(테스트용)
테스트 목적으로 한 번만 실행하려면 아래와 같이 입력할 수 있습니다.
```bash
python trading_bot.py
```
- 지정한 심볼에 대해 자동으로 매수/매도 로직 실행

### 2. 모든 자산 일괄 매도
```bash
python trading_bot.py --sell-all
```
- KRW, BTC를 제외한 모든 자산을 시장가로 즉시 매도

## 주요 파일 설명
- `trading_bot.py` : 메인 트레이딩 봇 코드
- `apikeys.py` : Upbit API 키 보관 파일
- `symbols.csv` : 매매 대상 심볼 및 파라미터 목록
- `portfolio_valuation.csv` : 일별 전체 평가금액 기록
- `trade_logs.log` : 거래 및 시스템 로그

## 참고 및 주의사항
- Upbit API 키는 반드시 안전하게 관리하세요.
- 거래소 수수료, 가격 변동, 주문 최소 단위 등으로 인해 일부 잔고가 남을 수 있습니다.
- 실제 투자 전, 소액으로 충분히 테스트하세요.
- 본 코드는 투자 손실에 대해 책임지지 않습니다.

---
문의: [YOUR_EMAIL@domain.com]
