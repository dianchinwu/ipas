(function(root,factory){root.IPASProgressCore=factory();}(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const VERSION=2,KEY="ipas-learning-progress-v2",LEGACY_KEY="ipas-learning-progress-v1";
const STATUSES=["NOT_STARTED","IN_PROGRESS","COMPLETED"],RATINGS=["correct","partial","wrong"];
function localDate(date){const v=date||new Date(),p=n=>String(n).padStart(2,"0");return `${v.getFullYear()}-${p(v.getMonth()+1)}-${p(v.getDate())}`;}
function validDate(x){if(!/^\d{4}-\d{2}-\d{2}$/.test(x||""))return false;const[y,m,d]=x.split("-").map(Number),v=new Date(y,m-1,d);return v.getFullYear()===y&&v.getMonth()===m-1&&v.getDate()===d;}
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x),timestamp=x=>typeof x==="string"&&!Number.isNaN(Date.parse(x));
function empty(){return {status:"NOT_STARTED",completed_at:null,recall:{},skipped_recall:false};}
function blank(ids){return Object.fromEntries(ids.map(id=>[id,empty()]));}
function normalizeRecord(record,version,allowedPrompts){
 if(!object(record)||!STATUSES.includes(record.status))throw new Error("包含非法學習狀態。");let done=null;
 if(record.status==="COMPLETED"){done=typeof record.completed_at==="string"&&version===1?{date:record.completed_at,timestamp:`${record.completed_at}T00:00:00`}:record.completed_at;if(!object(done)||!validDate(done.date)||!timestamp(done.timestamp))throw new Error("完成日期或時間不合法。");done={date:done.date,timestamp:done.timestamp};}else if(record.completed_at!=null)throw new Error("未完成狀態不得含完成日期。");
 const recall={};if(version===2){if(!object(record.recall)||typeof record.skipped_recall!=="boolean")throw new Error("自評或略過欄位不合法。");for(const[id,r]of Object.entries(record.recall)){if(!/^(R|E)\d+$/.test(id)||(allowedPrompts&&!allowedPrompts.includes(id))||!object(r)||!RATINGS.includes(r.rating)||!timestamp(r.rated_at))throw new Error("題目、自評或時間不合法。");recall[id]={rating:r.rating,rated_at:r.rated_at};}}
 return {status:record.status,completed_at:done,recall,skipped_recall:version===2?record.skipped_recall:false};
}
function needsReview(state){return Object.keys(state).filter(id=>Object.values(state[id].recall).some(r=>r.rating==="partial"||r.rating==="wrong"));}
function validate(payload,ids,catalog){if(!object(payload)||![1,2].includes(payload.version)||!object(payload.units))throw new Error("進度檔版本或結構不正確。");const allowed=new Set(ids),units={};for(const[id,record]of Object.entries(payload.units)){if(!allowed.has(id))throw new Error(`不存在的 Learning Unit：${id}`);units[id]=normalizeRecord(record,payload.version,catalog&&catalog[id]);}return {version:VERSION,updated_at:payload.updated_at||null,units,needs_review:needsReview(units)};}
function hydrate(payload,ids,catalog){return Object.assign(blank(ids),payload?validate(payload,ids,catalog).units:{});}
function merge(current,incoming,ids,catalog){const next=hydrate({version:VERSION,units:current},ids,catalog),imported=validate(incoming,ids,catalog).units;for(const[id,value]of Object.entries(imported)){const old=next[id],recall={...old.recall};for(const[prompt,r]of Object.entries(value.recall))if(!recall[prompt]||Date.parse(r.rated_at)>Date.parse(recall[prompt].rated_at))recall[prompt]=r;let picked=old;if(value.status==="COMPLETED"&&(old.status!=="COMPLETED"||value.completed_at.date>old.completed_at.date||(value.completed_at.date===old.completed_at.date&&Date.parse(value.completed_at.timestamp)>Date.parse(old.completed_at.timestamp))))picked=value;else if(old.status!=="COMPLETED"&&value.status==="IN_PROGRESS")picked=value;next[id]={...picked,recall};}return next;}
function inProgress(state,id){return {...state,[id]:{...state[id],status:state[id].status==="COMPLETED"?"COMPLETED":"IN_PROGRESS"}};}
function rate(state,id,prompt,rating,now){if(!RATINGS.includes(rating))throw new Error("非法自評。");const next=inProgress(state,id);next[id]={...next[id],recall:{...next[id].recall,[prompt]:{rating,rated_at:(now||new Date()).toISOString()}}};return next;}
function complete(state,id,now,skipped=false){const v=now||new Date();return {...state,[id]:{...state[id],status:"COMPLETED",completed_at:{date:localDate(v),timestamp:v.toISOString()},skipped_recall:skipped}};}
function cancel(state,id){return {...state,[id]:{...state[id],status:Object.keys(state[id].recall).length?"IN_PROGRESS":"NOT_STARTED",completed_at:null,skipped_recall:false}};}
function nextId(state,ids){return ids.find(id=>state[id].status!=="COMPLETED")||null;}
function stats(state,units,today){const completed=units.filter(u=>state[u.id].status==="COMPLETED"),subjects={};for(const u of units){subjects[u.subject]||={completed:0,total:0};subjects[u.subject].total++;if(state[u.id].status==="COMPLETED")subjects[u.subject].completed++;}return {completed:completed.length,total:units.length,subjects,today:completed.filter(u=>state[u.id].completed_at.date===today)};}
function exportPayload(state,now){return {version:VERSION,updated_at:(now||new Date()).toISOString(),units:state,needs_review:needsReview(state)};}
// Schedule is only a hint. It never orders or mutates the canonical ids.
function scheduleHints(state,units,today){const open=units.filter(u=>state[u.id].status!=="COMPLETED"),ordinal=s=>{const[y,m,d]=s.split("-").map(Number);return Date.UTC(y,m-1,d)/86400000;};return {today:units.filter(u=>u.dates.includes(today)),overdue:open.filter(u=>u.dates.some(d=>d<today)).length,remaining:open.length,days:Math.max(0,ordinal("2026-10-31")-ordinal(today))};}
return {VERSION,KEY,LEGACY_KEY,STATUSES,RATINGS,localDate,validDate,blank,validate,hydrate,merge,inProgress,rate,complete,cancel,nextId,stats,exportPayload,needsReview,scheduleHints};
}));
