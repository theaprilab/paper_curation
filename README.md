# Research Radar — 연구실 논문 큐레이션 V1

4개 분야 × Main / Application Guru = 8개 슬롯. Python 표준 라이브러리만으로 arXiv를 수집하고, JSON을 읽는 정적 사이트를 GitHub Pages로 배포합니다. `sources/`의 참조 파일은 변경하지 않았습니다.

## 실행

프로젝트 폴더에서 Python 3.10 이상으로 실행하세요. 별도 패키지와 API 키는 필요 없습니다.

```sh
python3 -m curator.pipeline
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
```

브라우저에서 http://127.0.0.1:8765 를 엽니다. HTML 파일을 직접 더블클릭하면 JSON 로딩이 차단될 수 있습니다.

저장된 수집 결과로 재선정하거나 테스트하려면:

```sh
python3 -m curator.pipeline --offline
python3 -m unittest discover -s tests -v
```

`--max-results 600`으로 연구자별 검색 상한(기본 300편)을 늘릴 수 있습니다. 페이지당 최대 100편, 요청 사이 최소 3.2초, 실패 시 최대 3회 시도합니다.

## V1의 정확한 범위

- 자동 소스: **arXiv API 저자 검색**. 공식 publication page는 교차 확인 링크입니다. OpenAlex/Semantic Scholar 및 공식 페이지 자동 파서는 아직 구현하지 않았습니다. Google Scholar scraping은 없습니다.
- Guru 본인이 저자에 포함된 논문을 기본 대상으로 합니다. 그룹 전체나 회사 전체 논문을 해당 Guru의 성과로 자동 간주하지 않습니다.
- 분야 키워드와 로봇·자율시스템 키워드가 제목/초록에 모두 있는 후보를 선택합니다. Information Space에는 belief-space/POMDP/information gathering을 포함합니다. Active Learning에는 Bayesian optimization/active exploration/preference learning을 포함합니다.
- **규칙 기반 후보 선별이며 의미 이해 모델이나 논문 품질 평가가 아닙니다.** 단순 언급에 의한 오탐과 표현 차이에 의한 누락이 가능합니다. 모든 자동 후보는 `needs_review`입니다.
- 최신성은 **스캔한 arXiv 결과 안에서 최초 제출일이 가장 최근**이라는 뜻입니다. 수정일은 별도 저장하고 순위에 사용하지 않습니다. 학회 게재일과 혼동하지 않습니다. 상한 도달 여부, 조회 URL, 조회 시각을 기록합니다.
- 같은 논문이 두 Guru의 저자 논문이라면 각 슬롯에 나올 수 있습니다. 슬롯 간 중복 금지보다 각 Guru의 최신 적합 논문을 우선합니다.
- arXiv에 없는 논문, 저자명이 다르게 등록된 논문, 소속 근거가 등록되지 않은 그룹원 논문은 누락될 수 있습니다. 철자 일치는 ORCID 수준의 신원 확인이 아닙니다.
- 최초 7개 후보에는 초록을 읽고 작성한 한국어 AI 요약과 읽을 이유를 포함했습니다. 이후 새 후보는 자동 초록 발췌(영어)와 초록의 방법·검증 문장로 표시됩니다. 한국어 생성 모델 API는 연결하지 않았습니다.

## 초기 수집 결과 (2026-09-28)

855개 연구자별 검색 결과를 검사해 7개 후보를 선정했습니다(연구자 간 중복 가능). Krause는 320편 중 최신 300편을 확인했습니다.

| 분야 | Main | Application |
|---|---|---|
| Active Learning | Krause · 2025-10-31 | Yue · 2024-06-20 |
| Active Inference | Friston · 2026-06-22 | Murata · 2025-12-01 |
| Information Space | LaValle · 2025-04-25 | Kaelbling · 2025-05-04 |
| HDC | Rahimi · 적합 후보 미발견 | Neubert · 2024-03-15 |

Rahimi의 arXiv 결과 54편에서 두 조건을 동시에 충족하는 후보를 찾지 못했습니다. 8편을 채우려고 로봇 관련성이 없는 논문을 넣지 않습니다. 이는 관련 논문이 존재하지 않는다는 결론이 아닙니다.

Peer Neubert의 현재 그룹은 [University of Koblenz INTAS](https://www.uni-koblenz.de/de/informatik/icv/neubert)로 공식 페이지에서 확인해 설정을 갱신했습니다. 초기 요청의 TU Chemnitz는 `previous_group`에 보존했습니다. 표시 소속은 현재 추적 그룹이며 각 논문의 발표 당시 소속을 뜻하지 않습니다.

## 구조

- `config/gurus.json`: 8명, 별칭, 공식 페이지, 그룹 구성원 설정
- `config/reviews.json`: 논문별 포함/제외 판단 및 요약 보정
- `curator/pipeline.py`: 수집·판정·최신 후보 선택·원자적 JSON 저장
- `data/raw/*.json`: 수집 메타데이터와 원본 초록 스냅샷
- `data/audit.json`: 포함/제외 근거, 키워드 및 근거 문장
- `docs/data/papers.json`: 배포되는 8개 슬롯과 구조화된 논문
- `docs/`: HTML/CSS/JS 정적 화면
- `.github/workflows/update.yml`: 매주 월요일 08:17 KST 업데이트 및 Pages 배포(실제 실행은 GitHub 대기열에 따라 지연 가능)

논문 필드는 `title`, `authors`, `date`, `date_type`, `updated`, `link`, `source`, `topic`, `guru`, `group`, `guru_type`, `robotics_relevance`, `summary`, `summary_method`, `why_it_matters`, `review_status`, `verified_at` 등을 포함합니다. 빈 슬롯은 `paper: null`입니다.

## 검토 및 그룹 추적 확장

`config/reviews.json` 키는 `guru_id:arxiv_id`입니다. 새 논문의 자동 요약을 덮어쓰려면 `summary`, `why_it_matters`, `source_url`, `note_method`를 추가하세요. `decision`을 생략하면 후보 상태를 유지합니다.

```json
{
  "murata:2512.01924": {
    "decision": "include",
    "evidence": "검토자가 원문에서 확인한 로봇 실험 및 분야 적합성 근거",
    "source_url": "https://arxiv.org/abs/2512.01924",
    "summary": "검토한 요약",
    "why_it_matters": "연구실에서 읽어야 하는 구체적인 이유"
  }
}
```

`decision: exclude`는 최신 후보도 제외하고 그다음 논문을 선택합니다. `include`는 근거와 출처가 있을 때만 키워드 누락을 보완하며 저자 불일치·미래 날짜·철회 논문은 통과시키지 않습니다. 그룹원을 추가할 때는 Guru 설정의 `members`에 `name`, `evidence_url`, `from`, `to`를 넣습니다. 날짜는 `YYYY-MM-DD`이며 소속 유효 기간 내 발표 논문만 인정합니다. `evidence_url`은 관리자가 확인한 공식 명단이어야 합니다. 현재 members는 비어 있고 Guru 본인 논문만 수집합니다.

## GitHub Pages 배포

현재 폴더에는 Git 저장소/remote가 없으므로 원격 배포는 수행하지 않았습니다.

1. 이 프로젝트를 GitHub 저장소의 `main` 브랜치에 올립니다. `sources/`와 로컬 `AGENTS.md`는 배포에 필요하지 않습니다.
2. 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다.
3. **Actions → Curate and publish research radar → Run workflow**를 실행합니다.
4. 성공하면 실행 결과의 `github-pages` 환경에 사이트 주소가 표시됩니다.

워크플로는 `docs/`만 공개합니다. 매 실행 결과와 누적 이력을 `docs/data/papers.json`에 함께 저장하고 **main 브랜치에 자동 커밋**한 뒤 배포합니다. 캐시 만료와 무관하게 다음 실행에서 기록을 이어받습니다. 감사 artifact는 별도로 90일 보관합니다. 일부 소스 실패 시 기존 논문과 확인 시각을 유지하며, 전체 실패 시 기존 배포를 유지합니다.

저장소의 Actions에 contents 쓰기 권한이 필요합니다. 브랜치 보호 규칙으로 봇의 main 직접 커밋이 차단되면 기록 저장 단계가 실패하고 배포하지 않습니다. 실행 중 main에 다른 커밋이 추가돼도 강제 push하지 않고 실패하므로, 변경사항을 확인한 후 워크플로를 다시 실행하세요.

## 지난 논문 보관

화면의 **지난 논문**에서 이전 선정 논문을 확인할 수 있습니다. 분야 필터도 그대로 적용되며 최근 보관 순으로 표시합니다. 제목·저자·요약·선정 근거·원문 링크와 최초 선정일·보관일이 남습니다.

- 기록 대상은 한 번이라도 선정된 논문입니다. 수집 과정에서 탈락한 모든 논문 목록은 별도 `data/audit.json`에 있습니다.
- Guru + arXiv ID 조합으로 중복 저장을 방지합니다. 현재 선정 논문은 지난 목록에서 제외합니다.
- 다시 선정된 논문은 최신 목록으로 돌아가고 최초 선정일은 보존합니다. 모든 교체 이벤트를 별도 로그로 나열하지는 않습니다.
- 수집 실패로 이전 논문을 유지하는 경우 보관 상태로 넘기지 않습니다.
- 수동 제외되거나 더 이상 적합하지 않은 논문도 과거 기록으로 남습니다. 과거 선정은 현재 추천을 의미하지 않습니다.
- 기능 추가 전 사라진 기록은 복원할 수 없습니다. 기존 최신 JSON의 7편을 시작 기록으로 등록했으며, 아직 교체 이력이 없어 지난 목록은 비어 있습니다.


## 검증

저자 불일치, 분야/로봇 조건, 최신 부적합 논문 건너뛰기, 수정일과 제출일 구분, 미래 날짜, 수동 제외, 그룹 소속 기간, API 오류, 장애 시 이전 결과 유지에 대한 단위 테스트가 포함됩니다. 실제 arXiv 수집 및 브라우저 렌더링은 이 초기 데이터로 확인했습니다.

API 기준: [arXiv API 안내](https://info.arxiv.org/help/api/user-manual.html), [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## 초록 기반 활용 설명

현재 7편의 `reading_note`는 실제 수집 초록을 바탕으로 작성한 한국어 AI 해석입니다. 활용할 문제와 구체적인 방법(`application`), 실험 범위·해석상 한계(`validation_scope`), 초록 원문 근거(`evidence`)를 분리해 표시합니다. 원문 전체를 검토했다는 의미는 아닙니다. 성능 수치는 초록에서 저자가 보고한 내용으로 표시합니다.

이후 신규 논문에는 생성 모델 없이 초록에서 방법 및 평가 문장을 추출해 영어로 보여줍니다. 자동 발췌를 한국어 활용 해석처럼 표시하지 않습니다. 한국어 설명을 추가하려면 `config/reviews.json`의 `reading_note`를 보완하세요. 저장된 근거가 갱신된 초록에 없으면 자동 발췌로 전환합니다.
