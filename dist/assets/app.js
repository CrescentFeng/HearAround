const SCENES = [
  {id:'fire_alarm',icon:'🔥',name:'Fire or smoke alarm',hint:'Critical event',severity:'critical',score:.91,message:'Possible fire alarm — check your surroundings now',action:'Stay calm, leave the danger area, and follow official emergency guidance.',rule:'Critical event · immediate alert in 1/2 windows',vibration:[700,220,250,220,700],candidates:[['Fire alarm',.91],['Smoke detector',.78],['Alarm',.41]]},
  {id:'emergency_siren',icon:'🚨',name:'Emergency vehicle siren',hint:'Critical event',severity:'critical',score:.86,message:'A siren may be nearby — stay aware',action:'Check your surroundings and follow official emergency information.',rule:'Critical event · immediate alert in 1/2 windows',vibration:[700,240,700],candidates:[['Siren',.86],['Police car (siren)',.62],['Vehicle',.24]]},
  {id:'car_horn',icon:'🚗',name:'Car horn',hint:'Traffic warning',severity:'urgent',score:.79,message:'A car horn was detected — watch for vehicles',action:'Pause and check for nearby vehicles before moving.',rule:'Urgent event · confirmed in 2/3 windows',vibration:[220,140,220,140,220],candidates:[['Vehicle horn',.79],['Road traffic',.48],['Siren',.19]]},
  {id:'baby_crying',icon:'👶',name:'Baby crying',hint:'Check needed',severity:'urgent',score:.76,message:'A baby may be crying — please check',action:'Check the baby or caregiver when it is safe to do so.',rule:'Urgent event · confirmed in 2/3 windows',vibration:[220,140,600],candidates:[['Baby cry',.76],['Crying',.61],['Speech',.20]]},
  {id:'doorbell',icon:'🚪',name:'Doorbell',hint:'Door alert',severity:'attention',score:.82,message:'Someone may be at the door',action:'Check the door or a door camera when it is safe to do so.',rule:'Attention event · confirmed in 2/4 windows',vibration:[250,170,250],candidates:[['Doorbell',.82],['Ding-dong',.64],['Chime',.27]]},
  {id:'knocking',icon:'✊',name:'Knocking',hint:'Door alert',severity:'attention',score:.73,message:'Someone may be knocking',action:'Check the door or a door camera when it is safe to do so.',rule:'Attention event · confirmed in 2/4 windows',vibration:[180,220,180],candidates:[['Knock',.73],['Tap',.44],['Impact',.29]]}
];
const UI = {severity:{critical:'Critical',urgent:'Urgent',attention:'Attention'},colors:{critical:['#ff7474','#4b2227'],urgent:['#ffc45b','#45351d'],attention:['#72bcff','#142f45']},icons:Object.fromEntries(SCENES.map(scene=>[scene.id,scene.icon]))};
const LABEL_NAMES=Object.fromEntries(SCENES.map(scene=>[scene.id,scene.name]));
const fallbackUuid=()=>`session_${Date.now()}_${Math.random().toString(16).slice(2)}`;
const state={sessionId:sessionStorage.getItem('hearound-session')||(crypto.randomUUID?.()||fallbackUuid()),selectedFile:null,current:null,currentIsReal:false,events:[],lastPreview:{id:null,time:0},speech:false,demoAssets:[],live:{active:false,starting:false,stream:null,context:null,source:null,node:null,gain:null,timer:null,chunks:[],sampleCount:0,inflight:false,sequence:0}};
sessionStorage.setItem('hearound-session',state.sessionId);
const $=selector=>document.querySelector(selector);

function escapeHtml(value){return String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));}
function percent(value){return `${Math.round(Number(value||0)*100)}%`;}
function showToast(message){const toast=$('#toast');toast.textContent=message;toast.classList.add('show');clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>toast.classList.remove('show'),2800);}
function setBusy(busy){$('#analysisState').classList.toggle('show',busy);$('#analyzeButton').disabled=busy||!state.selectedFile;$('#monitorState').textContent=busy?'Analyzing audio segment':'Waiting for sound input';}
function setLiveStatus(title,detail,mode='idle'){$('#liveTitle').textContent=title;$('#liveDetail').textContent=detail;$('#liveDot').className=`live-dot ${mode}`;}
function setCapability(name,available,availableText,fallbackText,required=false){const dot=$(`#${name}Dot`);const status=$(`#${name}Status`);dot.className=`compat-dot ${available?'ok':required?'blocked':'fallback'}`;status.textContent=available?availableText:fallbackText;}
function renderCompatibility(){
  const secure=window.isSecureContext;const microphone=secure&&Boolean(navigator.mediaDevices?.getUserMedia)&&Boolean(window.AudioWorkletNode);const vibration=Boolean(navigator.vibrate);const speech=Boolean(window.speechSynthesis&&window.SpeechSynthesisUtterance);
  setCapability('secure',secure,'Available','Requires HTTPS or localhost',true);setCapability('mic',microphone,'AudioWorklet available',secure?'Not supported':'Waiting for secure context',true);setCapability('vibration',vibration,'Available','Visual alert fallback');setCapability('speech',speech,'Available','Text and pictogram fallback');
  $('#compatNote').textContent=!secure?'This page is not in a secure context, so the browser will block microphone access. Use HTTPS.':microphone?'Microphone capture is available. Permission is requested only after you press “Start live monitoring.”':'This browser cannot capture live audio. Built-in samples and file upload still work.';
}
function renderScenarios(){
  $('#scenarios').innerHTML=SCENES.map(scene=>`<button class="scenario ${state.current?.label===scene.id&&!state.currentIsReal?'active':''}" data-scene="${scene.id}" aria-label="Preview ${scene.name} alert"><span class="sound-icon" aria-hidden="true">${scene.icon}</span><span><strong>${scene.name}</strong><small>${scene.hint}</small></span><i class="level-shape ${scene.severity}" aria-hidden="true"></i></button>`).join('');
  document.querySelectorAll('[data-scene]').forEach(button=>button.addEventListener('click',()=>runPreview(button.dataset.scene)));
}
function renderCandidates(candidates=[]){
  $('#candidates').innerHTML=candidates.slice(0,3).map(item=>{const label=item.label??item[0];const score=item.score??item[1];return `<div class="candidate"><span title="${escapeHtml(label)}">${escapeHtml(label)}</span><strong>${percent(score)}</strong><div class="meter"><b style="--w:${percent(score)}"></b></div></div>`}).join('');
}
function renderTrace(event,isReal){
  const top=event.evidence?.top_labels?.[0];
  const steps=[['Detection result',isReal?`${top?.label||event.display_name} · ${percent(top?.score??event.score)}`:`${event.display_name} · interaction preview`],['Rule evidence',event.decision?.reason||event.rule],['Recent state',event.decision?.suppressed?'A matching event is still in cooldown':'No matching alert needs suppression'],['Action taken',event.decision?.suppressed?'Keep the record without another alert':'Create pictogram, text, and optional vibration alert']];
  $('#trace').innerHTML=steps.map((step,index)=>`<div class="trace-step"><span class="trace-num">${index+1}</span><div><span>${step[0]}</span><strong>${escapeHtml(step[1])}</strong></div></div>`).join('');
}
function renderEvent(event,{real=false}={}){
  state.current=event;state.currentIsReal=real;$('#emptyState').hidden=true;$('#alertCard').hidden=false;$('#confirmRow').hidden=false;
  const severity=event.severity||'attention';const [color,bg]=UI.colors[severity]||UI.colors.attention;const card=$('#alertCard');card.dataset.severity=severity;card.style.setProperty('--alert',color);card.style.setProperty('--alert-soft',bg);
  $('#alertSymbol').textContent=UI.icons[event.label]||'👂';$('#severity').textContent=event.decision?.suppressed?'Duplicate alert avoided':UI.severity[severity];$('#sourceBadge').textContent=real?'Real model':'Interaction preview';$('#alertTitle').textContent=event.decision?.suppressed?`${event.display_name} was already reported`:event.user_message;$('#alertDesc').textContent=event.decision?.suppressed?'A matching event is still in cooldown. This occurrence is recorded only.':event.display_name;$('#actionText').textContent=event.decision?.suppressed?'No additional vibration or speech alert.':event.suggested_action;$('#confidence').textContent=percent(event.score);
  renderCandidates(event.evidence?.top_labels||event.candidates||[]);renderTrace(event,real);renderScenarios();
  if(!event.decision?.suppressed){if(state.speech)speakCurrent();if(navigator.vibrate)navigator.vibrate(event.vibration||[]);}
}
function addTimeline(event,real){state.events.unshift({time:new Date().toLocaleTimeString('en-GB',{hour12:false}),name:event.display_name,score:event.score,severity:event.severity,status:event.decision?.suppressed?'Suppressed':event.decision?.alert===false?'Recorded only':'Alerted',source:real?'Real model':'Interaction preview'});state.events=state.events.slice(0,12);renderTimeline();}
function renderTimeline(){$('#timeline').innerHTML=state.events.length?state.events.map(event=>`<div class="event"><time>${event.time}</time><div><span class="event-name">${escapeHtml(event.name)}</span><small>${event.source} · ${percent(event.score)}</small></div><span class="tag tag-${event.severity}">${UI.severity[event.severity]}</span><span class="outcome">${event.status}</span></div>`).join(''):'<div class="timeline-empty">No events in this session yet.</div>';}
function runPreview(id){
  const scene=SCENES.find(item=>item.id===id);const now=Date.now();const suppressed=state.lastPreview.id===id&&now-state.lastPreview.time<8000;
  const event={event_id:`preview_${Date.now()}`,label:scene.id,display_name:scene.name,severity:scene.severity,score:scene.score,user_message:scene.message,suggested_action:scene.action,vibration:scene.vibration,candidates:scene.candidates,decision:{alert:!suppressed,suppressed,reason:suppressed?'The same preview is still within its eight-second cooldown.':scene.rule}};
  setBusy(true);window.setTimeout(()=>{setBusy(false);renderEvent(event,{real:false});addTimeline(event,false);state.lastPreview={id,time:now};showToast(suppressed?'Duplicate alert avoided.':'This is an interaction preview, not a model result.');},420);
}
async function analyzeFile(){
  if(!state.selectedFile)return;setBusy(true);const data=new FormData();data.append('audio',state.selectedFile);data.append('session_id',state.sessionId);data.append('environment_mode',$('#environmentMode').value);
  try{const response=await fetch('/api/analyze',{method:'POST',body:data});const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.detail||`Recognition service returned ${response.status}`);state.sessionId=payload.session_id;sessionStorage.setItem('hearound-session',state.sessionId);
    if(payload.events.length){const event=payload.events.find(item=>item.decision.alert)||payload.events[0];renderEvent(event,{real:true});payload.events.forEach(item=>addTimeline(item,true));showToast(event.decision.suppressed?'Event recorded; duplicate alert suppressed.':'Real-model analysis complete.');}else{renderNoAlert(payload);showToast('No enabled important sound was confirmed.');}
    $('#monitorState').textContent=`Real analysis complete · ${payload.inference_ms} ms`;
  }catch(error){renderError(error.message);$('#monitorState').textContent='Recognition incomplete';}finally{setBusy(false);}
}
function renderNoAlert(payload){$('#emptyState').hidden=true;$('#alertCard').hidden=false;$('#confirmRow').hidden=true;const card=$('#alertCard');card.dataset.severity='attention';card.style.setProperty('--alert','#7de0a6');card.style.setProperty('--alert-soft','#173a2a');$('#alertSymbol').textContent='✓';$('#severity').textContent='No important alert';$('#sourceBadge').textContent='Real model';$('#alertTitle').textContent='No key sound confirmed';$('#alertDesc').textContent='This segment did not satisfy the repeated-window rule for any of the six events.';$('#actionText').textContent='No action is needed right now.';$('#confidence').textContent='-';renderCandidates(payload.top_candidates);renderTrace({display_name:'No confirmed event',score:0,decision:{reason:'No event reached its policy threshold.'}},true);}
function renderError(message){$('#emptyState').hidden=false;$('#alertCard').hidden=true;$('#confirmRow').hidden=true;$('#emptyState').innerHTML=`<div class="error-message"><strong>Recognition could not be completed</strong><br>${escapeHtml(message)}</div>`;showToast(message);}
async function sendFeedback(verdict){if(!state.current)return;if(!state.currentIsReal){showToast(verdict==='correct'?'Interaction preview confirmed.':'Preview corrections are not written to model data.');return;}try{const response=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId,event_id:state.current.event_id,verdict})});if(!response.ok)throw new Error('Feedback could not be saved');showToast(verdict==='correct'?'Confirmed — thank you for the feedback.':'Recognition error recorded. The model will not change automatically.');}catch(error){showToast(error.message);}}
function speakCurrent(){if(!state.current||!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(`${state.current.user_message}. ${state.current.suggested_action}`);utterance.lang='en-US';utterance.rate=.88;window.speechSynthesis.speak(utterance);}
async function checkHealth(){try{const response=await fetch('/api/health');if(!response.ok)throw new Error();const health=await response.json();$('#statusLight').className=`status-light ${health.model_ready?'ready':'pending'}`;$('#systemTitle').textContent=health.model_ready?'Real recognition service is ready':'Backend connected; model not loaded';$('#systemDetail').textContent=health.model_ready?'Live microphone and uploaded files will run YAMNet AudioSet 521.':'The first load downloads the model. Keep the network connection available.';$('#loadModelButton').hidden=health.model_ready;}catch{$('#statusLight').className='status-light error';$('#systemTitle').textContent='This page is a static preview';$('#systemDetail').textContent='Start the HearAround backend to use real microphone and file recognition.';$('#loadModelButton').hidden=true;}}
async function loadModel(){const button=$('#loadModelButton');button.disabled=true;button.textContent='Loading…';try{const response=await fetch('/api/model/load',{method:'POST'});if(!response.ok)throw new Error('Model loading failed. Check the network and dependencies.');await checkHealth();showToast('YAMNet is ready. You can now analyze a sound.');}catch(error){showToast(error.message);}finally{button.disabled=false;button.textContent='Load model';}}

function trimLiveBuffer(){
  const live=state.live;if(!live.context)return;const maxSamples=Math.ceil(live.context.sampleRate*5);
  while(live.sampleCount>maxSamples&&live.chunks.length){const excess=live.sampleCount-maxSamples;const first=live.chunks[0];if(first.length<=excess){live.chunks.shift();live.sampleCount-=first.length;}else{live.chunks[0]=first.slice(excess);live.sampleCount-=excess;}}
}
function liveWindow(seconds=3){
  const live=state.live;if(!live.context)return null;const wanted=Math.min(live.sampleCount,Math.floor(live.context.sampleRate*seconds));if(!wanted)return null;const output=new Float32Array(wanted);let offset=wanted;
  for(let index=live.chunks.length-1;index>=0&&offset>0;index-=1){const chunk=live.chunks[index];const count=Math.min(offset,chunk.length);offset-=count;output.set(chunk.subarray(chunk.length-count),offset);}return output;
}
function pcmWavBlob(samples,sampleRate){
  const buffer=new ArrayBuffer(44+samples.length*2);const view=new DataView(buffer);const write=(offset,text)=>{for(let index=0;index<text.length;index+=1)view.setUint8(offset+index,text.charCodeAt(index));};write(0,'RIFF');view.setUint32(4,36+samples.length*2,true);write(8,'WAVE');write(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,sampleRate,true);view.setUint32(28,sampleRate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);write(36,'data');view.setUint32(40,samples.length*2,true);
  for(let index=0;index<samples.length;index+=1){const value=Math.max(-1,Math.min(1,samples[index]));view.setInt16(44+index*2,value<0?value*32768:value*32767,true);}return new Blob([buffer],{type:'audio/wav'});
}
async function analyzeLiveWindow(){
  const live=state.live;if(!live.active||live.inflight||!live.context)return;const minimum=Math.floor(live.context.sampleRate*2.5);if(live.sampleCount<minimum){setLiveStatus('Building the audio buffer',`${(live.sampleCount/live.context.sampleRate).toFixed(1)} / 2.5 seconds`,'active');return;}const samples=liveWindow(3);if(!samples)return;live.inflight=true;live.sequence+=1;setLiveStatus('Analyzing surrounding sound',`Overlapping segment ${live.sequence} · raw audio is not saved`,'analyzing');$('#monitorState').textContent='Live monitoring · analyzing';
  const data=new FormData();data.append('audio',pcmWavBlob(samples,live.context.sampleRate),`live_${live.sequence}.wav`);data.append('session_id',state.sessionId);data.append('environment_mode',$('#environmentMode').value);
  try{const response=await fetch('/api/analyze',{method:'POST',body:data});const payload=await response.json().catch(()=>({}));if(!response.ok){if(response.status===422&&String(payload.detail||'').toLowerCase().includes('silent')){setLiveStatus('Live monitoring','The surroundings are quiet · no recording saved','active');return;}throw new Error(payload.detail||`Live recognition returned ${response.status}`);}state.sessionId=payload.session_id;sessionStorage.setItem('hearound-session',state.sessionId);renderCandidates(payload.top_candidates);
    if(payload.events.length){const event=payload.events.find(item=>item.decision.alert)||payload.events[0];renderEvent(event,{real:true});payload.events.forEach(item=>addTimeline(item,true));setLiveStatus(event.decision.suppressed?'Live monitoring':'Important sound detected',event.decision.suppressed?'Matching event is in cooldown; no repeated interruption':`${event.display_name} · ${percent(event.score)}`,'active');}else{setLiveStatus('Live monitoring',`No important sound confirmed · ${payload.inference_ms} ms`,'active');}
  }catch(error){setLiveStatus('Live recognition interrupted',error.message,'error');showToast(error.message);}finally{live.inflight=false;if(live.active)$('#monitorState').textContent='Live monitoring';}
}
async function startLiveMonitoring(){
  const live=state.live;if(live.active||live.starting)return;if(!window.isSecureContext){showToast('Microphone access requires HTTPS or localhost.');setLiveStatus('Live monitoring unavailable','This page is not in a secure context. Use HTTPS.','error');return;}if(!navigator.mediaDevices?.getUserMedia||!window.AudioWorkletNode){showToast('This browser does not support live audio capture.');setLiveStatus('Live monitoring unavailable','Built-in samples and file upload still work','error');return;}live.starting=true;$('#liveToggle').disabled=true;setLiveStatus('Waiting for microphone permission','Allow access in the browser prompt','analyzing');
  try{const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});const context=new AudioContext({latencyHint:'interactive'});await context.audioWorklet.addModule('/assets/pcm-capture-worklet.js');const source=context.createMediaStreamSource(stream);const node=new AudioWorkletNode(context,'hearound-pcm-capture');const gain=context.createGain();gain.gain.value=0;source.connect(node);node.connect(gain);gain.connect(context.destination);live.stream=stream;live.context=context;live.source=source;live.node=node;live.gain=gain;live.chunks=[];live.sampleCount=0;live.sequence=0;live.active=true;node.port.onmessage=event=>{if(!live.active||!event.data?.samples)return;const samples=event.data.samples instanceof Float32Array?event.data.samples:new Float32Array(event.data.samples);live.chunks.push(samples);live.sampleCount+=samples.length;trimLiveBuffer();};stream.getAudioTracks().forEach(track=>track.addEventListener('ended',()=>stopLiveMonitoring('Microphone disconnected')));live.timer=window.setInterval(analyzeLiveWindow,1500);$('#liveToggle').textContent='Pause live monitoring';$('#liveToggle').setAttribute('aria-pressed','true');$('#liveBox').classList.add('is-live');$('#monitorState').textContent='Live monitoring';setLiveStatus('Live monitoring',`Microphone ${context.sampleRate/1000} kHz · five-second memory buffer`,'active');showToast('Live monitoring started. Raw audio will not be saved.');
  }catch(error){const denied=error?.name==='NotAllowedError'||error?.name==='SecurityError';setLiveStatus('Live monitoring is off',denied?'Microphone permission was not granted; built-in samples still work':'Microphone startup failed; check the device','error');showToast(denied?'Microphone permission was not granted.':'The microphone could not be started.');
  }finally{live.starting=false;$('#liveToggle').disabled=false;}
}
async function stopLiveMonitoring(reason='Live monitoring paused'){
  const live=state.live;if(live.timer)window.clearInterval(live.timer);live.timer=null;live.active=false;if(live.node){live.node.port.onmessage=null;try{live.node.disconnect();}catch{}}if(live.source)try{live.source.disconnect();}catch{}if(live.gain)try{live.gain.disconnect();}catch{}if(live.stream)live.stream.getTracks().forEach(track=>track.stop());if(live.context)try{await live.context.close();}catch{}Object.assign(live,{stream:null,context:null,source:null,node:null,gain:null,chunks:[],sampleCount:0,inflight:false});$('#liveToggle').textContent='Start live monitoring';$('#liveToggle').setAttribute('aria-pressed','false');$('#liveBox').classList.remove('is-live');$('#monitorState').textContent='Waiting for sound input';setLiveStatus(reason,'Raw audio has been cleared from the memory buffer','idle');
}
function toggleLiveMonitoring(){return state.live.active?stopLiveMonitoring():startLiveMonitoring();}

function setSelectedFile(file,{audioUrl=null,status=null}={}){
  state.selectedFile=file||null;$('#analyzeButton').disabled=!file;
  $('#fileStatus').textContent=status||(file?`${file.name} · ${(file.size/1024/1024).toFixed(2)} MB`:'No file selected');
  const audio=$('#audioPreview');
  if(file){if(audio.dataset.objectUrl==='true'&&audio.src)URL.revokeObjectURL(audio.src);audio.src=audioUrl||URL.createObjectURL(file);audio.dataset.objectUrl=String(!audioUrl);audio.hidden=false;}else{audio.hidden=true;audio.removeAttribute('src');}
}
function demoOptionLabel(asset){
  if(asset.kind==='negative')return `Hard negative · ${asset.clip_id.replaceAll('_',' ')}`;
  if(asset.kind==='mixed')return `Mixed scene · ${asset.expected_labels.map(label=>LABEL_NAMES[label]||label).join(' + ')}`;
  return `${asset.expected_labels.map(label=>LABEL_NAMES[label]||label).join(' / ')} · ${asset.clip_id}`;
}
async function loadDemoAssets(){
  const select=$('#demoAssetSelect');const button=$('#loadDemoAsset');
  try{const response=await fetch('/api/demo-assets');if(!response.ok)throw new Error();const payload=await response.json();state.demoAssets=payload.assets||[];
    const groups=[['target','Target sounds'],['negative','Hard negatives'],['mixed','Mixed sound scenes']];
    select.innerHTML=groups.map(([kind,label])=>{const items=state.demoAssets.filter(asset=>asset.kind===kind);return items.length?`<optgroup label="${label}">${items.map(asset=>`<option value="${escapeHtml(asset.clip_id)}">${escapeHtml(demoOptionLabel(asset))}</option>`).join('')}</optgroup>`:''}).join('');
    select.disabled=!state.demoAssets.length;button.disabled=!state.demoAssets.length;$('#demoCount').textContent=`${state.demoAssets.length} clips`;
  }catch{select.innerHTML='<option>Sample catalog unavailable</option>';select.disabled=true;button.disabled=true;}
}
async function loadEvaluation(){
  try{const response=await fetch('/api/evaluation');if(!response.ok)throw new Error();const payload=await response.json();if(!payload.ready||!payload.holdout)return;const holdout=payload.holdout;const stress=payload.stress;
    $('#holdoutCount').textContent=`${holdout.clips} clips`;$('#holdoutF1').textContent=percent(holdout.per_class?.macro_f1);$('#falseAlertCount').textContent=`${holdout.negative_false_alerts}/${holdout.negative_clips}`;$('#stressCount').textContent=stress?.passed?`${stress.total_inferences} runs ✓`:'Pending';
    $('#evaluationNote').textContent=`Frozen-policy independent evaluation: ${percent(holdout.exact_match)} exact match and ${holdout.critical_misses}/${holdout.critical_clips} critical-event misses. Doorbell and other failures are disclosed; these results are not medical evidence or safety certification.`;
  }catch{$('#evaluationNote').textContent='The independent evaluation summary is temporarily unavailable; product functionality is unaffected.';}
}
async function loadSelectedDemo(){
  const asset=state.demoAssets.find(item=>item.clip_id===$('#demoAssetSelect').value);if(!asset)return;
  const button=$('#loadDemoAsset');button.disabled=true;button.textContent='Loading…';
  try{const response=await fetch(asset.audio_url);if(!response.ok)throw new Error('Sample loading failed.');const blob=await response.blob();const file=new File([blob],`${asset.clip_id}.wav`,{type:'audio/wav'});setSelectedFile(file,{audioUrl:asset.audio_url,status:`${demoOptionLabel(asset)} · ${asset.duration_s.toFixed(1)} seconds`});
    const source=asset.source_url.split(' | ')[0];$('#sampleAttribution').hidden=false;$('#sampleAttribution').innerHTML=`${escapeHtml(asset.creator)} · ${escapeHtml(asset.license)} · <a href="${escapeHtml(source)}" target="_blank" rel="noreferrer">View source</a>`;showToast('Licensed sample loaded. You can preview it before running recognition.');
  }catch(error){showToast(error.message);}finally{button.disabled=false;button.textContent='Load this sample';}
}

document.querySelectorAll('[data-view-option]').forEach(button=>button.addEventListener('click',()=>{document.body.dataset.view=button.dataset.viewOption;document.querySelectorAll('[data-view-option]').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});}));
$('#audioUpload').addEventListener('change',event=>{const file=event.target.files[0];$('#sampleAttribution').hidden=true;setSelectedFile(file||null);});
$('#loadDemoAsset').addEventListener('click',loadSelectedDemo);
$('#liveToggle').addEventListener('click',toggleLiveMonitoring);
$('#analyzeButton').addEventListener('click',analyzeFile);$('#confirmButton').addEventListener('click',()=>sendFeedback('correct'));$('#incorrectButton').addEventListener('click',()=>sendFeedback('incorrect'));$('#speakButton').addEventListener('click',speakCurrent);$('#loadModelButton').addEventListener('click',loadModel);
$('#speechToggle').addEventListener('click',()=>{state.speech=!state.speech;$('#speechToggle').textContent=`Speech: ${state.speech?'on':'off'}`;$('#speechToggle').setAttribute('aria-pressed',String(state.speech));showToast(state.speech?'Spoken alerts enabled.':'Spoken alerts disabled.');});
$('#contrastToggle').addEventListener('click',()=>{document.body.classList.toggle('contrast');const on=document.body.classList.contains('contrast');$('#contrastToggle').setAttribute('aria-pressed',String(on));showToast(on?'High contrast enabled.':'Standard contrast restored.');});
$('#clearEvents').addEventListener('click',async()=>{state.events=[];renderTimeline();try{await fetch(`/api/events/${encodeURIComponent(state.sessionId)}`,{method:'DELETE'});}catch{}showToast('This session’s event history has been cleared.');});
document.addEventListener('visibilitychange',()=>{if(state.live.active&&document.visibilityState==='visible'&&state.live.context?.state==='suspended')state.live.context.resume().catch(()=>{});});
window.addEventListener('beforeunload',()=>{if(state.live.stream)state.live.stream.getTracks().forEach(track=>track.stop());});
setInterval(()=>$('#clock').textContent=new Date().toLocaleTimeString('en-GB',{hour12:false}),1000);
const heights=[18,32,51,28,68,42,23,79,46,30,58,91,55,34,72,44,88,35,63,29,49,75,38,61,25,84,47,31,57,69,40,54,27,76,43,20,64,36,52,30,81,46,26,70,39,59,24,67];$('#wave').innerHTML=heights.map((height,index)=>`<i style="--h:${height}px;--d:-${(index%9)*.11}s"></i>`).join('');
renderScenarios();renderTimeline();renderCompatibility();checkHealth();loadDemoAssets();loadEvaluation();
