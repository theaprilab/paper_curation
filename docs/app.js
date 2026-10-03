'use strict';
const el = (tag, text, cls) => { const n = document.createElement(tag); if(text !== undefined) n.textContent = text; if(cls) n.className = cls; return n; };
function link(text, url) { const a = el('a', text); try { const parsed = new URL(url); if (parsed.protocol !== 'https:') return el('span', text); a.href=parsed.href; a.target='_blank'; a.rel='noopener noreferrer'; } catch { return el('span',text); } return a; }
const labels = {selected:'자동 후보 · 검토 필요',no_match:'적합 논문 미발견',source_error:'수집 실패'};
function card(slot) {
 const c=el('article',undefined,'card '+slot.guru_type), top=el('div',undefined,'card-top');
 top.append(el('span',slot.guru_type==='main'?'MAIN GURU':'APPLICATION GURU','role'));
 const p=slot.paper, reviewed=p?.review_status==='reviewed';
 top.append(el('span',slot.status==='selected' && reviewed?'검토 완료':labels[slot.status], 'status'+(reviewed?' reviewed':'')));
 c.append(top,el('p',slot.guru,'guru'),el('p',slot.group,'group'));
 if(slot.status==='source_error') c.append(el('p',slot.retained_previous?'새 논문 수집에 실패하여 이전 결과를 표시합니다.':'소스 접속 실패로 이번 수집을 완료하지 못했습니다.','warning'));
 if(p){
  const body=el('div',undefined,'paper');
  const age=(Date.now()-Date.parse(p.date))/86400000;
  body.append(el('span',`${p.date} · arXiv 최초 제출${age>730?' · 2년 이상 경과':''}`,'date'+(age>730?' old':'')));
  const h=el('h3');h.append(link(p.title,p.link));body.append(h,el('p',p.summary,'abstract'));
  body.append(el('span',p.summary_method==='assistant_abstract_summary'?'AI 정리 · 초록 기반 · 원문 검토 필요':p.summary_method==='human'?'검토자 요약':'초록 발췌 · 원문 영어','date'));
  const why=el('div',undefined,'why'), note=p.reading_note;
  why.append(el('b',note?.method==='extractive_abstract'?'초록의 제안 방법 · 자동 발췌':'어디에 활용할 수 있나'),el('p',note?.application || p.why_it_matters));

  body.append(why);
  const detail=el('details');detail.append(el('summary','저자 · 로봇 관련성 · 선정 근거'));
  detail.append(el('p',p.authors.join(', ')),el('p',`연구자 연결: ${p.attribution==='guru_author'?'구루 본인이 저자로 참여':'근거가 등록된 그룹 구성원 참여'}`));
  const list=el('ul');for(const evidence of p.robotics_relevance.evidence)list.append(el('li',evidence));detail.append(list);
  detail.append(el('p',`분야 키워드: ${p.topic_evidence.join(', ') || '검토자 확인'}`),el('p',`판정: ${p.robotics_relevance.method} · 마지막 수집 ${p.verified_at.slice(0,10)}`));body.append(detail);c.append(body);
 } else {const e=el('div',undefined,'empty');e.append(el('strong','기준에 맞는 논문을 기다립니다.'),el('p','검색 범위에서 관심 분야와 로봇 적용 조건을 동시에 충족하는 논문을 찾지 못했습니다.'));c.append(e);}
 if(slot.coverage)c.append(el('p',`arXiv ${slot.coverage.scanned} / ${slot.coverage.total}편 확인${slot.coverage.truncated?' · 검색 상한 도달':''}`,'date'));
 const links=el('div',undefined,'links');if(p)links.append(link('논문 읽기 ↗',p.link));links.append(link('공식 연구 페이지 ↗',slot.publication_url));c.append(links);return c;
}
let data;
let selectedTopic="all", selectedView="current";
function render(topic=selectedTopic){
 selectedTopic=topic;
 const root=document.querySelector('#results');root.replaceChildren();
 if(selectedView==='history'){
  const records=(data.history || []).filter(r=>r.archived_at && (topic==='all'||r.paper.topic===topic)).sort((a,b)=>b.archived_at.localeCompare(a.archived_at));
  root.append(el('p',`지난 선정 논문 ${records.length}편 · 교체되거나 선정에서 제외된 논문입니다. 현재 추천 여부와는 다릅니다.`,'muted'));
  if(!records.length)root.append(el('p','아직 지난 논문이 없습니다. 현재 논문이 교체되면 이곳에 자동으로 쌓입니다.','message'));
  const grid=el('div',undefined,'grid');
  for(const r of records){const p=r.paper;const c=card({...p,id:r.guru_id,paper:p,status:'selected',publication_url:r.publication_url});c.prepend(el('p',`${p.topic} · 최초 선정 ${r.first_selected_at.slice(0,10)} · 보관 ${r.archived_at.slice(0,10)}`,'date'));grid.append(c);}
  root.append(grid);return;
 }
 const topics=[...new Set(data.slots.map(s=>s.topic))];
 topics.filter(t=>topic==='all'||t===topic).forEach((t)=>{const s=el('section',undefined,'topic'),head=el('div',undefined,'topic-head');head.append(el('h2',t),el('span','MAIN + APPLICATION / 각 1편'));const grid=el('div',undefined,'grid');data.slots.filter(x=>x.topic===t).forEach(x=>grid.append(card(x)));s.append(head,grid);root.append(s);});
}
async function start(){try{const r=await fetch('data/papers.json');if(!r.ok)throw Error(r.status);data=await r.json();if(!Array.isArray(data.slots))throw Error('invalid data');document.querySelector('#count').textContent=data.slots.filter(s=>s.paper).length;document.querySelector('#update').textContent=`생성 ${data.generated_at.slice(0,10)}${data.mode==='offline'?' · 저장 데이터':''}`;document.querySelector('#review-count').textContent=`검토 완료 ${data.slots.filter(s=>s.paper?.review_status==='reviewed').length}편`;document.querySelector('#scope').textContent=data.latest_scope;render();}catch(e){document.querySelector('#results').replaceChildren(el('p','데이터를 불러오지 못했습니다. 웹 서버로 열었는지 확인하고 새로고침해 주세요.','message'));document.querySelector('#update').textContent='데이터 로드 실패';}}
for(const b of document.querySelectorAll('#filters button'))b.addEventListener('click',()=>{if(!data)return;document.querySelectorAll('#filters button').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render(b.dataset.topic);});
for(const b of document.querySelectorAll('#views button'))b.addEventListener('click',()=>{if(!data)return;selectedView=b.dataset.view;document.querySelectorAll('#views button').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render();});
start();
