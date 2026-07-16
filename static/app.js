let currentLang="ru",currentAnalysis=null,googlePayClient=null;

document.addEventListener("DOMContentLoaded",()=>{
    setupLang();
    checkApiKey();
    loadHistory();
});

function setupLang(){document.querySelectorAll(".lang-btn").forEach(b=>{b.addEventListener("click",()=>{document.querySelectorAll(".lang-btn").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentLang=b.dataset.lang;applyLang()})})}
function applyLang(){document.querySelectorAll("[data-ru][data-en]").forEach(el=>{el.textContent=el.getAttribute("data-"+currentLang)})}

// API Key Management
function getApiKey(){return localStorage.getItem("lpcritic_api_key")||""}
function saveApiKey(){
    const key=document.getElementById("api-key-input").value.trim();
    if(!key){showApiStatus("Enter a valid key","err");return}
    localStorage.setItem("lpcritic_api_key",key);
    showApiStatus("Key saved!","ok");
    setTimeout(()=>checkApiKey(),500);
}
function checkApiKey(){
    const key=getApiKey();
    if(key){
        document.getElementById("api-section").hidden=true;
        document.getElementById("main-input").hidden=false;
        updateUsageDisplay();
        setupForm();
    }
}
function showApiStatus(msg,type){
    const s=document.getElementById("api-status");
    s.textContent=msg;
    s.className="api-status "+type;
}

// Usage Tracking (client-side for free tier)
function getUsage(){
    const data=JSON.parse(localStorage.getItem("lpcritic_usage")||"{}");
    const now=Date.now();
    const hourAgo=now-3600000;
    const recent=(data.timestamps||[]).filter(t=>t>hourAgo);
    return{count:recent.length,timestamps:recent};
}
function trackUsage(){
    const usage=getUsage();
    usage.timestamps.push(Date.now());
    localStorage.setItem("lpcritic_usage",JSON.stringify({timestamps:usage.timestamps}));
}
function updateUsageDisplay(){
    const usage=getUsage();
    const remaining=Math.max(0,3-usage.count);
    document.getElementById("usage-count").textContent=remaining+" / 3";
}

// Form
function setupForm(){
    document.getElementById("analyze-form").addEventListener("submit",async e=>{
        e.preventDefault();
        const url=document.getElementById("url-input").value.trim();
        if(!url)return;
        const usage=getUsage();
        if(usage.count>=3){showError("Free limit: 3 per hour. Upgrade to Pro for unlimited.");return}
        setLoading(true);hide("error-section");hide("results");
        try{
            const r=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,api_key:getApiKey()})});
            if(!r.ok){const err=await r.json();throw new Error(err.detail||"Failed")}
            const d=await r.json();
            trackUsage();
            updateUsageDisplay();
            renderResults(d);loadHistory();
        }catch(e){showError(e.message)}finally{setLoading(false)}
    });
}

function setLoading(v){const b=document.getElementById("analyze-btn"),sp=b.querySelector(".btn-spinner"),tx=b.querySelector(".btn-text"),ld=document.getElementById("loading");b.disabled=v;sp.hidden=!v;tx.hidden=v;ld.hidden=!v}
function hide(id){document.getElementById(id).hidden=true}
function showError(msg){const s=document.getElementById("error-section");document.getElementById("error-message").textContent=msg;s.hidden=false}

function renderResults(data){
currentAnalysis=data;
const s=document.getElementById("results");s.hidden=false;
const score=data.result.overall_score;
const circ=2*Math.PI*85;
setTimeout(()=>{document.getElementById("score-ring").style.strokeDashoffset=circ-(score/100)*circ;document.getElementById("score-number").textContent=score},100);
document.getElementById("score-summary").textContent=data.result.summary;
if(data.screenshot){document.getElementById("screenshot-block").hidden=false;document.getElementById("screenshot-img").src="/api/screenshot/"+data.screenshot.split("/").pop()}
document.getElementById("quick-wins-list").innerHTML=data.result.quick_wins.map((w,i)=>'<div class="win-card"><div class="win-num">'+(i+1)+'</div><div class="win-text">'+w.description+'</div></div>').join("");
document.getElementById("categories-list").innerHTML=data.result.categories.map(cat=>'<div class="cat-card" onclick="toggleCat(this)"><div class="cat-head"><div class="cat-left"><span class="cat-dot '+cat.status+'"></span><span class="cat-name">'+cat.name+'</span></div><div class="cat-right"><div class="cat-bar"><div class="cat-bar-fill '+cat.status+'" style="width:'+cat.score*10+'%"></div></div><span class="cat-score">'+cat.score+'/10</span><span class="cat-chevron">&#9662;</span></div></div><div class="cat-body"><div class="cat-cols"><div class="cat-col col-issues"><h4>Issues</h4><ul>'+cat.issues.map(i=>'<li>'+i+'</li>').join("")+'</ul></div><div class="cat-col col-fixes"><h4>Fixes</h4><ul>'+cat.fixes.map(f=>'<li>'+f+'</li>').join("")+'</ul></div></div></div></div>').join("");
s.scrollIntoView({behavior:"smooth",block:"start"})
}
function toggleCat(c){c.classList.toggle("open")}

async function loadHistory(){try{const r=await fetch("/api/history");const recs=await r.json();const l=document.getElementById("history-list");if(!recs.length){l.innerHTML='<div class="hist-empty">'+(currentLang==="ru"?"Пока нет анализов":"No analyses yet")+"</div>";return}l.innerHTML=recs.map(r=>'<div class="hist-card" onclick="loadAnalysis(\''+r.id+'\')"><span class="hist-url">'+r.url+'</span><div class="hist-meta"><span class="hist-score">'+r.result.overall_score+'/100</span><span>'+new Date(r.timestamp).toLocaleDateString()+'</span></div></div>').join("")}catch(e){console.error(e)}}
async function loadAnalysis(id){try{const r=await fetch("/api/history/"+id);const d=await r.json();renderResults(d);window.scrollTo({top:0,behavior:"smooth"})}catch(e){console.error(e)}}

function downloadReport(type){
if(!currentAnalysis)return;
const d=currentAnalysis,result=d.result;
if(type==="html"){
const catHTML=result.categories.map(c=>{const clr=c.status==="good"?"#22c55e":c.status==="warning"?"#eab308":"#ef4444";return'<div style="background:#f9fafb;border-radius:12px;padding:20px;margin-bottom:12px;border-left:4px solid '+clr+'"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h3 style="margin:0;font-size:16px;color:#18181b">'+c.name+'</h3><span style="background:'+clr+';color:#fff;padding:3px 10px;border-radius:20px;font-size:13px;font-weight:700">'+c.score+'/10</span></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><h4 style="margin:0 0 6px;color:#71717a;font-size:11px;text-transform:uppercase;letter-spacing:1px">Issues</h4><ul style="list-style:none;padding:0;margin:0">'+c.issues.map(i=>'<li style="padding:3px 0;font-size:13px;color:#333">&#10060; '+i+'</li>').join("")+'</ul></div><div><h4 style="margin:0 0 6px;color:#71717a;font-size:11px;text-transform:uppercase;letter-spacing:1px">Fixes</h4><ul style="list-style:none;padding:0;margin:0">'+c.fixes.map(f=>'<li style="padding:3px 0;font-size:13px;color:#333">&#9989; '+f+'</li>').join("")+'</ul></div></div></div>'}).join("");
const winsHTML=result.quick_wins.map((w,i)=>'<div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #e5e7eb"><div style="width:24px;height:24px;background:#dcfce7;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#16a34a">'+(i+1)+'</div><div style="font-size:13px;color:#333">'+w.description+'</div></div>').join("");
const html='<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Report - '+d.url+'</title></head><body style="font-family:Inter,system-ui,sans-serif;max-width:700px;margin:0 auto;padding:40px 24px;background:#fff;color:#18181b"><div style="text-align:center;margin-bottom:36px"><h1 style="font-size:24px;margin-bottom:6px">Landing Page Critic Report</h1><p style="color:#71717a;font-size:13px">'+d.url+'</p><p style="color:#a1a1aa;font-size:11px">'+new Date(d.timestamp).toLocaleString()+'</p></div><div style="text-align:center;background:linear-gradient(135deg,#a855f7,#6366f1);color:#fff;border-radius:16px;padding:28px;margin-bottom:32px"><div style="font-size:56px;font-weight:900">'+result.overall_score+'</div><div style="font-size:13px;opacity:0.8">Overall Score</div></div><div style="background:#fefce8;border:1px solid #fde047;border-radius:12px;padding:20px;margin-bottom:28px"><h2 style="margin:0 0 10px;font-size:16px;color:#854d0e">&#9889; Quick Wins</h2>'+winsHTML+'</div><h2 style="font-size:18px;margin-bottom:16px">Detailed Analysis</h2>'+catHTML+'<div style="margin-top:36px;text-align:center;padding:16px;background:#f9fafb;border-radius:8px"><p style="color:#a1a1aa;font-size:11px">Generated by Landing Page Critic</p></div></body></html>';
const blob=new Blob([html],{type:"text/html"});const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download="report-"+d.id+".html";document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(u);
}else if(type==="pdf"){
html2pdf().set({margin:10,filename:"report-"+d.id+".pdf",html2canvas:{scale:2},jsPDF:{unit:"mm",format:"a4",orientation:"portrait"}}).from(document.getElementById("report-content")).save();
}}

// Google Pay
function onGooglePayLoaded(){
    googlePayClient=new google.payments.api.PaymentsClient({environment:"TEST"});
    const button=googlePayClient.createButton({onClick:onGooglePayClick,buttonColor:"black",buttonType:"subscribe"});
    document.getElementById("google-pay-button-container").appendChild(button);
}
function onGooglePayClick(){
    const paymentDataRequest={apiVersion:2,apiVersionMinor:0,allowedPaymentMethods:[{type:"CARD",parameters:{allowedAuthMethods:["PAN_ONLY","CRYPTOGRAM_3DS"],allowedCardNetworks:["MASTERCARD","VISA","AMEX"]},tokenizationSpecification:{type:"PAYMENT_GATEWAY",parameters:{gateway:"example",gatewayMerchantId:"example"}}}],transactionInfo:{totalPriceStatus:"FINAL",totalPrice:"5.00",currencyCode:"USD",countryCode:"US"},merchantInfo:{merchantName:"Landing Page Critic"}};
    googlePayClient.loadPaymentData(paymentDataRequest).then(paymentData=>{
        alert("Payment successful! Pro activated.");
        localStorage.setItem("lpcritic_pro","true");
    }).catch(err=>{
        if(err.statusCode!=="CANCELED")console.error(err);
    });
}
