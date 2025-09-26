# LS Position Monitor (Simple, Raspberry Pi + GitHub Pages)

- **백엔드 없음**: 라즈베리파이에서 파이썬 스크립트가 네이버금융 실시간가를 긁어와 `web/live.json`을 갱신하고 커밋/푸시.
- **프론트**: GitHub Pages(정적)에서 `live.json`을 읽어 KPI/테이블 렌더.

## 빠른 시작 (Raspberry Pi)

```bash
sudo apt-get update
sudo apt-get install -y git python3-pip
git clone <YOUR_REPO_URL> ls-position-simple
cd ls-position-simple
pip3 install -r requirements.txt
