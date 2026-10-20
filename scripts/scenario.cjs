const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),repo='ehsanisildur-ux/half-weir';
const cases={staircase:{claims:[2,4,6],endowment:24},lopsided:{claims:[1,3,7],endowment:22},review:{claims:[2,-1,6],endowment:24}};
const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const clone=x=>JSON.parse(JSON.stringify(x));
function assert(ok,message){if(!ok)throw Error(message);}
function descriptor(id,revision){return {url:`https://raw.githubusercontent.com/${repo}/${revision}/fixtures/${id}.json`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'fixtures',id+'.json'))).digest('hex')};}
function args(id,revision,accounts){const d=descriptor(id,revision);return [repo,'restitution-pool',['Aster','Briar','Cedar'],accounts.slice(1),d.url,d.sha256,cases[id].endowment];}
function configuration(a){return {repository:a[0],pool:a[1],labels:a[2],beneficiaries:a[3],url:a[4],sha256:a[5],endowment_ticks:a[6]};}
function initial(id,revision,accounts){return {configuration:configuration(args(id,revision,accounts)),sponsor:accounts[0],phase:'UNASSESSED',sponsor_balance:cases[id].endowment,pool_balance:0,funded_total:0,assessment:null,awarded:[0,0,0],credits:[0,0,0],fundings:[],rounds:[],transfers:[]};}
function tickAwards(caps,budget){
 // Independent one-tick priority queue: contract uses binary-search water levels.
 const x=caps.map(()=>0);
 for(let t=0;t<budget;t++){
  const eligible=x.map((value,index)=>({value,index})).filter(o=>o.value<caps[o.index]).sort((a,b)=>a.value-b.value||a.index-b.index);
  assert(eligible.length>0,'Feasible tick budget');x[eligible[0].index]++;
 }
 return x;
}
function oracle(claims,estate){
 const half=claims.reduce((a,b)=>a+b,0);
 if(estate<=half)return {regime:'AWARDS',target:tickAwards(claims,estate)};
 const loss=tickAwards(claims,2*half-estate);return {regime:'LOSSES',target:claims.map((c,i)=>2*c-loss[i])};
}
function check(s,id,revision,accounts){
 assert(Object.keys(s).sort().join(',')==='assessment,awarded,configuration,credits,funded_total,fundings,phase,pool_balance,rounds,sponsor,sponsor_balance,transfers','Exact full state schema');
 assert(equal(s.configuration,configuration(args(id,revision,accounts)))&&s.sponsor===accounts[0],'Immutable source, beneficiaries and sponsor');
 assert([s.credits,s.awarded].every(v=>Array.isArray(v)&&v.length===3)&&[...s.credits,...s.awarded,s.sponsor_balance,s.pool_balance,s.funded_total].every(x=>Number.isSafeInteger(x)&&x>=0),'Bounded native ledger');
 const total=x=>x.reduce((a,b)=>a+b,0);
 assert(s.sponsor_balance+s.pool_balance+total(s.credits)===cases[id].endowment&&total(s.credits)===total(s.awarded)&&s.funded_total===s.pool_balance+total(s.awarded),'All three conservation identities');
 assert(total(s.fundings)===s.funded_total&&s.fundings.length<=32&&s.rounds.length<=s.fundings.length&&s.transfers.length<=64,'Bounded linked tranche histories');
 if(s.assessment!==null){
  const a=s.assessment,source=JSON.parse(fs.readFileSync(path.join(root,'fixtures',id+'.json')));
  assert(Object.keys(a).sort().join(',')==='claims,source'&&equal(a.source,source)&&Object.keys(a.claims).sort().join(',')==='anchors,claims'&&equal(a.claims.claims,cases[id].claims),'Complete source and every current net claim');
  assert(Array.isArray(a.claims.anchors)&&a.claims.anchors.length===3&&a.claims.anchors.every((indices,i)=>Array.isArray(indices)&&indices.length<=4&&(cases[id].claims[i]===-1||indices.length>0)&&indices.every(j=>Number.isInteger(j)&&j>=0&&j<source.clauses.length)&&equal(indices,[...new Set(indices)].sort((a,b)=>a-b))),'All clause anchors');
 }
}
function plan(id){
 const p=[],add=(label,caller,method,args=[],error)=>p.push({label:id+'-'+label,caller,method,args,...(error?{error}:{})});
 add('assess',3,'assess');
 if(id==='review'){
  add('reject-unresolved-fund',0,'fund',[1],'[EXPECTED] Resolved active pool required');
  add('reject-unresolved-distribute',2,'distribute',[],'[EXPECTED] Unpaid funded tranche required');
 }else if(id==='staircase'){
  add('reject-nonsponsor',1,'fund',[1],'[EXPECTED] Sponsor only');
  add('fund-6',0,'fund',[6]);add('distribute-6',3,'distribute');
  add('transfer-before-topup',1,'transfer',[1,1]);
  add('reject-empty-distribute',2,'distribute',[],'[EXPECTED] Unpaid funded tranche required');
  for(const [index,total] of [12,18,24].entries()){add('fund-'+total,0,'fund',[6]);add('distribute-'+total,index+1,'distribute');}
 }else{
  add('fund-5',0,'fund',[5]);add('distribute-5',1,'distribute');
  add('fund-16',0,'fund',[11]);add('distribute-16',2,'distribute');
  add('fund-22',0,'fund',[6]);add('reject-overfund',0,'fund',[1],'[EXPECTED] Funding exceeds available capacity');add('distribute-22',3,'distribute');
 }
 return p;
}
function replay(before,item,after,id,revision,accounts){
 check(before,id,revision,accounts);check(after,id,revision,accounts);
 if(item.error){assert(equal(before,after),'Expected error changed any state');return;}
 const e=clone(before),claims=cases[id].claims;
 if(item.method==='assess'){
  assert(before.phase==='UNASSESSED','One fixed record assessment');e.assessment=clone(after.assessment);e.phase=claims.includes(-1)?'REVIEW':claims.every(c=>c===0)?'SATISFIED':'ACTIVE';
 }else if(item.method==='fund'){
  assert(item.caller===0&&before.phase==='ACTIVE','Signed sponsor funding');const amount=item.args[0];e.sponsor_balance-=amount;e.pool_balance+=amount;e.funded_total+=amount;e.fundings.push(amount);
 }else if(item.method==='distribute'){
  assert(before.phase==='ACTIVE'&&before.pool_balance>0,'Unpaid funded pool');const result=oracle(claims,before.funded_total),delta=result.target.map((x,i)=>x-before.awarded[i]);
  assert(delta.every(x=>x>=0)&&delta.reduce((a,b)=>a+b,0)===before.pool_balance,'Only newly owed ticks leave escrow');e.awarded=result.target;e.credits=e.credits.map((x,i)=>x+delta[i]);e.pool_balance=0;
  e.rounds.push({funded_total:before.funded_total,...result,delta});
  if(before.funded_total===2*claims.reduce((a,b)=>a+b,0))e.phase='SATISFIED';else if(before.sponsor_balance===0)e.phase='EXHAUSTED';
 }else if(item.method==='transfer'){
  const owner=item.caller-1,[recipient,amount]=item.args;assert(owner>=0&&owner!==recipient&&before.credits[owner]>=amount,'Actual signed beneficiary transfer');e.credits[owner]-=amount;e.credits[recipient]+=amount;e.transfers.push({sender:owner,recipient,amount});
 }else throw Error('Unknown scenario method');
 assert(equal(e,after),'Full independent state replay: '+item.label);
}
module.exports={cases,args,descriptor,initial,plan,replay,oracle,check};
