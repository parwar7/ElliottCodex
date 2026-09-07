/* Offline browser QA. Uses an already installed Playwright and Edge only. */
'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const target=path.resolve(process.argv[2]||'');
if(!target.startsWith(root+path.sep)||!fs.existsSync(target))throw Error('Chart must exist beneath Runtime');
const scratch=fs.mkdtempSync(path.join(root,'chart-browser-qa-'));
process.env.TEMP=scratch;process.env.TMP=scratch;
(async()=>{
 let context;
 try{
  context=await chromium.launchPersistentContext(path.join(scratch,'profile'),{
   executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
   headless:true,viewport:{width:1280,height:900},args:['--disable-background-networking','--no-first-run']});
  const requests=[],errors=[];await context.route('**/*',route=>{const url=route.request().url();if(/^https?:/.test(url)){requests.push(url);return route.abort();}return route.continue();});
  const page=context.pages()[0];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(target).href);await page.waitForSelector('#detail .proposed');
  const input=JSON.parse(fs.readFileSync(path.join(path.dirname(target),'canonical.json'),'utf8'));
  assert.deepEqual(await page.evaluate(()=>JSON.parse(document.getElementById('canonical').textContent)),input);
  const ids=input.hypotheses.map(h=>h.hypothesis_id);let checked=0;
  for(const h of input.hypotheses){
   if(h.path==='parent')await page.selectOption('#parentSelect',h.hypothesis_id);
   else{
    await page.selectOption('#parentSelect',h.parent_family_hypothesis_id);
    await page.locator('[data-child-id]').filter({hasText:h.display_ref.replace('H','Scenario ')}).click();
   }
   const state=await page.evaluate(()=>({id:document.querySelector('#detail .proposed').dataset.hypothesisId,
     lines:document.querySelectorAll('#detail .proposed').length,
     labels:[...document.querySelectorAll('#detail .rolelabel')].map(x=>x.textContent),
     rows:[...document.querySelectorAll('#roles tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent)),
     childIds:[...document.querySelectorAll('[data-child-id]')].map(x=>x.dataset.childId),
     status:document.getElementById('status').textContent,position:document.getElementById('reachStatus').textContent}));
   assert.equal(state.id,h.hypothesis_id);assert.equal(state.lines,1);
   assert.deepEqual(state.labels,h.endpoints.filter(e=>e.edge==='end').map(e=>e.role));
   assert.equal(state.rows.length,h.endpoints.length/2);
   for(let i=0;i<state.rows.length;i++){
    assert.equal(state.rows[i][3],`${h.endpoints[i*2].represented_price_text} / ${h.endpoints[i*2].price_field}`);
    assert.equal(state.rows[i][4],`${h.endpoints[i*2+1].represented_price_text} / ${h.endpoints[i*2+1].price_field}`);
    for(const j of [0,1])assert.equal(state.rows[i][j+1],new Date(h.endpoints[i*2+j].timestamp_utc).toISOString().replace('T',' ').replace('.000Z',' UTC'));
   }
   assert.deepEqual(state.childIds,input.hypotheses.filter(x=>x.parent_family_hypothesis_id===h.hypothesis_id).map(x=>x.hypothesis_id));
   if(h.p004?.fatal)assert.ok(state.status.includes('P004-REJECTED'));
   assert.equal(state.position,'CURRENT_WAVE_POSITION_UNRESOLVED');checked++;
   if(h.path==='child'){await page.click('#backParent');assert.equal(await page.locator('#detail .proposed').getAttribute('data-hypothesis-id'),h.parent_family_hypothesis_id);}
  }
  // Genuine menu, child links and return flow above, then responsive/system-theme checks.
  for(const colorScheme of ['light','dark'])for(const width of [1280,390]){
   await page.emulateMedia({colorScheme});await page.setViewportSize({width,height:900});
   await page.selectOption('#parentSelect',ids[0]);
   assert.deepEqual(await page.evaluate(()=>[...document.querySelectorAll('main, section, select, .badge, p')].filter(n=>n.getBoundingClientRect().right>innerWidth+1).map(n=>({tag:n.tagName,id:n.id,right:n.getBoundingClientRect().right}))),[]);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   assert.ok(await page.locator('#overview').isVisible());
  }
  await page.setViewportSize({width:1280,height:900});await page.emulateMedia({colorScheme:'light'});
  await page.screenshot({path:path.join(scratch,'preview.png'),fullPage:true});
  const downloadPromise=page.waitForEvent('download');await page.click('#download');const download=await downloadPromise;
  const downloadPath=path.join(scratch,'download.json');await download.saveAs(downloadPath);
  assert.deepEqual(JSON.parse(fs.readFileSync(downloadPath,'utf8')),input);
  assert.deepEqual(requests,[]);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',browser:await context.browser().version(),hypotheses_checked:checked,
    exact_labels_prices_timestamps_links:true,alternative_isolation:true,back_navigation:true,json_download:true,
    desktop_mobile_light_dark:true,external_page_requests:requests.length,page_errors:errors.length,
    screenshot:path.join(scratch,'preview.png')}));
 }finally{if(context)await context.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
