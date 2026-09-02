import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MapContainer, TileLayer, CircleMarker, Tooltip as MapTooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const C={bg:"#06090f",card:"#0c1220",card2:"#0f1628",border:"#172033",accent:"#06b6d4",amber:"#f59e0b",green:"#10b981",red:"#ef4444",purple:"#a78bfa",text:"#e2e8f0",muted:"#64748b",dim:"#334155",orange:"#f97316"};
const PAL=["#06b6d4","#f59e0b","#10b981","#ec4899","#a78bfa","#f97316","#14b8a6","#818cf8","#fb923c","#34d399"];
const MN=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const fmtK=n=>n>=1e6?`${(n/1e6).toFixed(1)}M`:n>=1e3?`${(n/1e3).toFixed(1)}K`:String(n);
function ciColor(ci){if(ci>=0.4)return C.red;if(ci>=0.25)return C.orange;if(ci>=0.15)return C.amber;return C.green;}
function ciLabel(ci){if(ci>=0.4)return"High";if(ci>=0.25)return"Elevated";if(ci>=0.15)return"Moderate";return"Low";}

const COORDS={
  "SAN ANTONIO":[-33.593,-71.621],"VALPARAÍSO":[-33.047,-71.613],"CORONEL":[-37.029,-73.153],
  "SAN VICENTE":[-36.743,-73.134],"LIRQUÉN":[-36.713,-72.981],"PUERTO ANGAMOS":[-23.100,-70.417],
  "ANTOFAGASTA":[-23.651,-70.398],"IQUIQUE":[-20.214,-70.152],"ARICA":[-18.475,-70.322],
  "COQUIMBO":[-29.953,-71.344],"CALDERA":[-27.065,-70.825],"MEJILLONES":[-23.099,-70.451],
  "PUNTA ARENAS":[-53.164,-70.917],"PUERTO MONTT":[-41.469,-72.942],"TALCAHUANO":[-36.725,-73.116],
  "QUINTERO":[-32.784,-71.535],"VENTANAS":[-32.743,-71.488],"PENCO":[-36.738,-72.993],
};

const CONGESTION_ALL={
  "SAN ANTONIO":{import:0.455,export:0.366},"VALPARAÍSO":{import:0.088,export:0.286},
  "SAN VICENTE":{import:0.019,export:0.480},"LIRQUÉN":{import:0.070,export:0.382},
  "CORONEL":{import:0.108,export:0.229},"PUERTO ANGAMOS":{import:0.168,export:0.176},
  "ANTOFAGASTA":{import:0.172,export:0.162},"IQUIQUE":{import:0.134,export:0.037},
  "ARICA":{import:0.039,export:0.140},"COQUIMBO":{import:0.094,export:0.148},
  "CALDERA":{import:0.053,export:0.508},"MEJILLONES":{import:0.135,export:0.172},
  "PUNTA ARENAS":{import:0.007,export:0.005},"PUERTO MONTT":{import:0.068,export:0.181},
  "TALCAHUANO":{import:0.075,export:0.059},"QUINTERO":{import:0.060,export:0.076},
  "VENTANAS":{import:0.489,export:0.158},"PENCO":{import:0.113,export:0.000},
};

const MONTHLY_CI={
  "SAN ANTONIO|import":[0.218,0.288,0.316,0.313,0.211,0.303,0.256,0.455,0.232,0.256,0.203,0.344],
  "VALPARAÍSO|import":[0.080,0.037,0.048,0.046,0.080,0.090,0.110,0.078,0.099,0.085,0.069,0.088],
  "SAN ANTONIO|export":[0.366,0.320,0.350,0.340,0.310,0.290,0.300,0.370,0.350,0.330,0.300,0.366],
  "VALPARAÍSO|export":[0.286,0.250,0.270,0.260,0.280,0.290,0.300,0.310,0.290,0.270,0.260,0.286],
  "CORONEL|export":[0.229,0.200,0.220,0.230,0.240,0.230,0.220,0.230,0.240,0.230,0.210,0.229],
  "SAN VICENTE|export":[0.480,0.420,0.450,0.460,0.470,0.440,0.460,0.490,0.480,0.450,0.420,0.480],
  "LIRQUÉN|export":[0.382,0.340,0.360,0.370,0.380,0.360,0.370,0.390,0.380,0.370,0.350,0.382],
};
function getMCI(port,dir){
  const k=`${port}|${dir}`;
  if(MONTHLY_CI[k])return MONTHLY_CI[k];
  const ci=CONGESTION_ALL[port]?.[dir]??0.1;
  return Array(12).fill(ci);
}

const TREND_DATA=[
  {port:"SAN ANTONIO",d:"import",ci2024:0.261,ci2025:0.304,change:16.5},
  {port:"SAN ANTONIO",d:"export",ci2024:0.320,ci2025:0.311,change:-2.8},
  {port:"VALPARAÍSO",d:"import",ci2024:0.064,ci2025:0.088,change:37.3},
  {port:"VALPARAÍSO",d:"export",ci2024:0.271,ci2025:0.291,change:7.5},
  {port:"CORONEL",d:"import",ci2024:0.098,ci2025:0.090,change:-7.9},
  {port:"CORONEL",d:"export",ci2024:0.269,ci2025:0.242,change:-10.1},
  {port:"SAN VICENTE",d:"import",ci2024:0.030,ci2025:0.031,change:2.1},
  {port:"SAN VICENTE",d:"export",ci2024:0.272,ci2025:0.398,change:46.3},
  {port:"LIRQUÉN",d:"import",ci2024:0.059,ci2025:0.075,change:27.1},
  {port:"LIRQUÉN",d:"export",ci2024:0.367,ci2025:0.382,change:4.1},
  {port:"PUERTO ANGAMOS",d:"import",ci2024:0.148,ci2025:0.168,change:13.5},
  {port:"PUERTO ANGAMOS",d:"export",ci2024:0.160,ci2025:0.176,change:10.0},
  {port:"ANTOFAGASTA",d:"import",ci2024:0.150,ci2025:0.172,change:14.7},
  {port:"ANTOFAGASTA",d:"export",ci2024:0.144,ci2025:0.162,change:12.5},
  {port:"IQUIQUE",d:"import",ci2024:0.110,ci2025:0.134,change:21.8},
  {port:"IQUIQUE",d:"export",ci2024:0.030,ci2025:0.037,change:23.3},
];

const IMPORT_HS={
  "84":{name:"Machinery & valves",ports:{
    "SAN ANTONIO":[8919,7754,9070,9222,8512,8275,9230,9328,9402,10114,8289,9543],
    "VALPARAÍSO":[3262,2458,2846,2410,3780,3929,3998,3174,3361,3120,2803,2546],
    "PUERTO ANGAMOS":[458,408,459,447,431,407,453,460,445,437,408,413],
  }},
  "85":{name:"Electrical apparatus",ports:{
    "SAN ANTONIO":[4912,4275,5003,5087,4696,4565,5094,5148,5190,5583,4574,5274],
    "VALPARAÍSO":[1838,1385,1604,1358,2131,2214,2254,1789,1895,1759,1580,1435],
    "PUERTO ANGAMOS":[159,141,159,155,149,141,157,159,154,151,141,143],
  }},
  "87":{name:"Vehicles & parts",ports:{
    "SAN ANTONIO":[2968,2582,3020,3071,2834,2755,3073,3106,3130,3367,2758,3178],
    "VALPARAÍSO":[984,741,858,727,1140,1185,1206,958,1014,941,846,768],
  }},
  "39":{name:"Plastics & articles",ports:{
    "SAN ANTONIO":[3165,2754,3226,3280,3026,2942,3281,3315,3339,3593,2944,3393],
  }},
};

const EXPORT_HS={
  "08":{name:"Fresh Fruit",ports:{
    "VALPARAÍSO":[1888,2311,2546,2735,2668,2071,1927,1597,1544,1225,1017,1290],
    "SAN ANTONIO":[1119,1137,1425,1578,1558,1493,1435,1334,1188,942,874,897],
    "CORONEL":[147,152,188,228,264,274,244,152,163,128,92,78],
    "SAN VICENTE":[113,111,122,130,174,213,219,207,188,162,128,130],
    "LIRQUÉN":[55,55,61,71,74,56,66,52,46,49,51,58],
    "COQUIMBO":[134,143,118,60,21,0,0,0,0,0,0,0],
  }},
  "22":{name:"Wine",ports:{
    "SAN ANTONIO":[2201,1373,1679,2027,1928,1860,1859,1566,1724,1947,1661,1565],
    "VALPARAÍSO":[1195,1261,1539,1771,1622,1525,1755,1542,1477,1636,1566,1542],
  }},
  "44":{name:"Pine Sawnwood",ports:{
    "CORONEL":[464,476,378,395,418,377,421,411,376,395,342,394],
    "SAN VICENTE":[179,185,226,254,269,246,257,207,171,221,204,258],
    "LIRQUÉN":[165,157,156,167,169,168,161,166,166,173,174,166],
    "SAN ANTONIO":[116,116,116,116,116,116,116,116,116,116,116,116],
    "VALPARAÍSO":[50,45,50,52,55,51,55,50,53,51,44,43],
  }},
  "03":{name:"Frozen Salmon",ports:{
    "SAN VICENTE":[233,321,289,319,283,329,322,327,323,334,331,379],
    "CORONEL":[226,228,232,233,230,231,230,227,224,224,220,218],
    "LIRQUÉN":[148,151,163,194,189,158,153,146,157,175,190,177],
    "SAN ANTONIO":[119,90,86,102,106,91,102,78,88,74,87,105],
    "VALPARAÍSO":[58,61,66,66,67,66,65,60,54,53,51,50],
  }},
  "02":{name:"Frozen Meat",ports:{
    "SAN ANTONIO":[254,194,258,278,251,204,258,245,237,235,242,217],
    "VALPARAÍSO":[169,188,178,191,211,209,234,214,192,187,196,173],
    "LIRQUÉN":[52,39,28,40,53,44,56,59,44,29,22,32],
    "CORONEL":[28,36,29,21,29,43,17,24,34,29,13,46],
  }},
  "20":{name:"Fruit Preserves",ports:{
    "SAN ANTONIO":[277,231,254,284,259,286,329,330,345,317,315,241],
    "VALPARAÍSO":[149,137,181,199,215,208,261,220,213,231,193,158],
  }},
  "16":{name:"Mollusc Preparations",ports:{
    "SAN VICENTE":[76,99,104,112,122,109,117,100,83,89,85,94],
    "CORONEL":[97,98,101,96,102,103,104,98,96,81,77,76],
    "SAN ANTONIO":[22,28,24,20,25,20,20,20,20,24,20,22],
    "VALPARAÍSO":[12,13,18,13,17,14,20,18,16,13,17,17],
    "LIRQUÉN":[9,10,8,16,20,15,19,17,15,13,12,11],
  }},
  "47":{name:"Wood Pulp",ports:{
    "LIRQUÉN":[44,43,51,57,58,57,56,60,58,58,57,55],
    "SAN VICENTE":[52,50,49,47,48,47,48,47,47,48,48,49],
    "CORONEL":[40,28,48,27,30,27,28,15,35,40,29,37],
    "SAN ANTONIO":[19,19,19,20,20,20,21,21,20,20,20,20],
    "VALPARAÍSO":[14,14,13,14,13,14,14,14,15,15,15,15],
  }},
  "28":{name:"Lithium Carbonate",ports:{
    "PUERTO ANGAMOS":[41,43,44,46,44,44,44,44,44,45,42,42],
    "SAN ANTONIO":[39,36,56,42,38,30,43,33,48,47,40,37],
    "ARICA":[20,16,20,22,24,24,20,24,21,26,23,22],
    "IQUIQUE":[18,23,26,18,24,23,14,23,18,18,20,21],
    "VALPARAÍSO":[15,20,24,20,16,16,15,21,14,18,21,27],
    "ANTOFAGASTA":[10,9,11,10,10,9,9,10,10,9,9,10],
  }},
  "74":{name:"Copper",ports:{
    "SAN ANTONIO":[64,43,52,51,49,55,59,44,50,49,46,47],
    "PUERTO ANGAMOS":[31,30,37,28,40,32,42,38,39,46,36,28],
    "VALPARAÍSO":[15,23,18,23,24,13,26,21,18,13,18,23],
    "ANTOFAGASTA":[15,15,14,14,12,12,10,10,10,12,12,14],
    "IQUIQUE":[8,5,7,5,6,3,4,4,5,6,5,5],
  }},
};

const pad12=a=>a.length>=12?a:[...a,...Array(12-a.length).fill(0)];

const IMPORT_BY_PORT={};
Object.entries(IMPORT_HS).forEach(([hs,{name,ports}])=>{
  Object.entries(ports).forEach(([port,fc])=>{
    if(!IMPORT_BY_PORT[port])IMPORT_BY_PORT[port]=[];
    IMPORT_BY_PORT[port].push({hs,name:`HS${hs} — ${name}`,fc});
  });
});
Object.values(IMPORT_BY_PORT).forEach(a=>a.sort((x,y)=>y.fc.reduce((s,v)=>s+v,0)-x.fc.reduce((s,v)=>s+v,0)));

const EXPORT_BY_PORT={};
Object.entries(EXPORT_HS).forEach(([hs,{name,ports}])=>{
  Object.entries(ports).forEach(([port,fc])=>{
    if(!EXPORT_BY_PORT[port])EXPORT_BY_PORT[port]=[];
    EXPORT_BY_PORT[port].push({hs,name:`HS${hs} — ${name}`,fc:pad12(fc)});
  });
});
Object.values(EXPORT_BY_PORT).forEach(a=>a.sort((x,y)=>y.fc.reduce((s,v)=>s+v,0)-x.fc.reduce((s,v)=>s+v,0)));

const TT=({active,payload,label})=>{
  if(!active||!payload?.length)return null;
  return <div style={{background:"#1e293b",border:"1px solid #334155",borderRadius:8,padding:"8px 12px",fontSize:12,color:C.text,boxShadow:"0 8px 32px rgba(0,0,0,0.6)"}}>
    <div style={{fontWeight:700,marginBottom:4,color:C.accent}}>{label}</div>
    {payload.map((p,i)=><div key={i} style={{display:"flex",gap:8,alignItems:"center",marginBottom:2}}>
      <span style={{width:8,height:8,borderRadius:2,background:p.color,display:"inline-block"}}/>
      <span style={{color:C.muted}}>{p.name}:</span>
      <span style={{fontWeight:600}}>{typeof p.value==="number"?(p.value<1?(p.value*100).toFixed(0)+"%":p.value>999?fmtK(p.value):p.value):p.value}</span>
    </div>)}
  </div>;
};

function FlyTo({center,zoom}){const map=useMap();useEffect(()=>{map.flyTo(center,zoom,{duration:0.8});},[center,zoom,map]);return null;}

export default function Dashboard(){
  const [dir,setDir]=useState("import");
  const [selPort,setSelPort]=useState(null);
  const [selHS,setSelHS]=useState(null);

  const hsData=dir==="import"?IMPORT_HS:EXPORT_HS;
  const byPort=dir==="import"?IMPORT_BY_PORT:EXPORT_BY_PORT;

  const availComms=selPort&&byPort[selPort]
    ?byPort[selPort]
    :Object.entries(hsData).map(([hs,{name}])=>({hs,name:`HS${hs} — ${name}`}));

  const ports=Object.entries(CONGESTION_ALL).map(([name,ci])=>{
    const c=COORDS[name];
    return c?{name,ci:ci[dir]??0,lat:c[0],lng:c[1]}:null;
  }).filter(Boolean).sort((a,b)=>b.ci-a.ci);

  const portCI=selPort?getMCI(selPort,dir):null;
  const trend=selPort?TREND_DATA.find(t=>t.port===selPort&&t.d===dir):null;
  const portComms=selPort?byPort[selPort]||[]:[];

  const commData=selHS?hsData[selHS]:null;
  const commFC=selHS&&selPort&&commData?.ports?.[selPort]?pad12(commData.ports[selPort]):null;

  const commPorts=selHS&&commData?Object.entries(commData.ports).map(([port,fc])=>{
    const pfc=pad12(fc);
    const total=pfc.reduce((a,b)=>a+b,0);
    const mci=getMCI(port,dir);
    const avgCI=mci.reduce((a,b)=>a+b,0)/12;
    return {port,fc:pfc,total,avgCI,score:Math.round(total*(1-avgCI)),ci:mci};
  }).sort((a,b)=>b.score-a.score):[];

  const mapCenter=selPort&&COORDS[selPort]?COORDS[selPort]:[-33.5,-71.0];
  const mapZoom=selPort?7:4;

  const handleDir=d=>{setDir(d);setSelPort(null);setSelHS(null);};
  const handlePort=name=>{
    if(selPort===name){setSelPort(null);setSelHS(null);}
    else setSelPort(name);
  };

  return (
    <div style={{background:C.bg,height:"100vh",fontFamily:"'DM Sans',system-ui,sans-serif",color:C.text,display:"flex",flexDirection:"column"}}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
      <style>{`
        .leaflet-tooltip{background:#1e293b!important;border:1px solid #334155!important;color:#e2e8f0!important;
          font-family:'DM Sans',system-ui,sans-serif!important;border-radius:8px!important;padding:6px 10px!important;
          box-shadow:0 4px 20px rgba(0,0,0,0.6)!important;font-size:12px!important}
        .leaflet-tooltip-top:before{border-top-color:#334155!important}
        .leaflet-tooltip-bottom:before{border-bottom-color:#334155!important}
        select option{background:#0f1628;color:#e2e8f0}
        ::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#0c1220}
        ::-webkit-scrollbar-thumb{background:#334155;border-radius:3px}
      `}</style>

      {/* Header */}
      <div style={{padding:"12px 24px",borderBottom:`1px solid ${C.border}`,display:"flex",alignItems:"center",justifyContent:"space-between",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:32,height:32,borderRadius:8,background:`linear-gradient(135deg,${C.accent},${C.purple})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:16}}>&#9875;</div>
          <div>
            <h1 style={{margin:0,fontSize:18,fontWeight:800,letterSpacing:"-0.03em"}}>WazeCargo <span style={{color:C.accent}}>Port Intelligence</span></h1>
            <p style={{margin:0,fontSize:10,color:C.muted}}>Congestion Forecast & Commodity Predictions &middot; 2026</p>
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div style={{padding:"10px 24px",borderBottom:`1px solid ${C.border}`,display:"flex",alignItems:"center",gap:24,flexShrink:0,flexWrap:"wrap"}}>
        <div style={{display:"flex",gap:0}}>
          {["import","export"].map(d=>(
            <button key={d} onClick={()=>handleDir(d)}
              style={{padding:"6px 20px",fontSize:11,fontWeight:dir===d?700:500,cursor:"pointer",
                textTransform:"uppercase",letterSpacing:1,
                border:`1px solid ${dir===d?C.accent:C.border}`,
                borderRadius:d==="import"?"6px 0 0 6px":"0 6px 6px 0",
                background:dir===d?`${C.accent}20`:"transparent",
                color:dir===d?C.accent:C.muted}}>
              {d}
            </button>
          ))}
        </div>

        <div style={{display:"flex",alignItems:"center",gap:6}}>
          <span style={{fontSize:11,color:C.muted,fontWeight:600}}>Port:</span>
          {selPort
            ?<div style={{display:"flex",alignItems:"center",gap:6}}>
              <span style={{width:8,height:8,borderRadius:"50%",background:ciColor(CONGESTION_ALL[selPort]?.[dir]??0)}}/>
              <span style={{fontSize:12,fontWeight:700,color:C.text}}>{selPort}</span>
              <button onClick={()=>{setSelPort(null);setSelHS(null);}}
                style={{width:18,height:18,borderRadius:4,border:`1px solid ${C.border}`,background:"transparent",
                  color:C.muted,cursor:"pointer",fontSize:12,lineHeight:1,display:"flex",alignItems:"center",justifyContent:"center"}}>×</button>
            </div>
            :<span style={{fontSize:11,color:C.dim,fontStyle:"italic"}}>Click map to select</span>
          }
        </div>

        <div style={{display:"flex",alignItems:"center",gap:6}}>
          <span style={{fontSize:11,color:C.muted,fontWeight:600}}>Commodity:</span>
          <select value={selHS||""} onChange={e=>setSelHS(e.target.value||null)}
            style={{padding:"5px 10px",paddingRight:28,borderRadius:6,border:`1px solid ${C.border}`,
              background:C.card2,color:C.text,fontSize:11,minWidth:240,cursor:"pointer",outline:"none",
              appearance:"auto"}}>
            <option value="">— All commodities —</option>
            {availComms.map(c=><option key={c.hs} value={c.hs}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {/* Main: Map + Panel */}
      <div style={{display:"grid",gridTemplateColumns:"1.4fr 1fr",flex:1,overflow:"hidden"}}>
        {/* Map */}
        <div style={{position:"relative",borderRight:`1px solid ${C.border}`}}>
          <MapContainer center={[-33.5,-71.0]} zoom={4} style={{height:"100%",width:"100%"}}
            scrollWheelZoom={true} zoomControl={true}>
            <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'/>
            <FlyTo center={mapCenter} zoom={mapZoom}/>
            {ports.map(p=>(
              <CircleMarker key={p.name} center={[p.lat,p.lng]}
                radius={selPort===p.name?14:p.ci>0.3?10:p.ci>0.15?7:5}
                pathOptions={{
                  color:selPort===p.name?"#fff":ciColor(p.ci),
                  fillColor:ciColor(p.ci),fillOpacity:selPort===p.name?0.9:0.65,
                  weight:selPort===p.name?3:1.5}}
                eventHandlers={{click:()=>handlePort(p.name)}}>
                <MapTooltip direction="top" offset={[0,-8]} opacity={0.95}>
                  <div style={{fontWeight:700}}>{p.name}</div>
                  <div style={{fontSize:11}}>CI: {(p.ci*100).toFixed(0)}% &middot; {ciLabel(p.ci)}</div>
                </MapTooltip>
              </CircleMarker>
            ))}
          </MapContainer>

          {/* Legend */}
          <div style={{position:"absolute",bottom:24,left:16,zIndex:1000,background:"rgba(12,18,32,0.92)",
            borderRadius:10,padding:"10px 14px",border:`1px solid ${C.border}`,fontSize:10}}>
            <div style={{fontWeight:700,color:C.text,marginBottom:6,textTransform:"uppercase",letterSpacing:1}}>
              {dir} congestion
            </div>
            {[{l:"Low (<15%)",c:C.green},{l:"Moderate (15-25%)",c:C.amber},{l:"Elevated (25-40%)",c:C.orange},{l:"High (>40%)",c:C.red}].map(x=>(
              <div key={x.l} style={{display:"flex",alignItems:"center",gap:6,marginBottom:3}}>
                <span style={{width:8,height:8,borderRadius:"50%",background:x.c,display:"inline-block"}}/>
                <span style={{color:C.muted}}>{x.l}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        <div style={{overflowY:"auto",padding:"16px 20px",display:"flex",flexDirection:"column",gap:12}}>
          {!selPort&&!selHS&&<OverviewPanel ports={ports} dir={dir} onSelect={handlePort}/>}
          {!selPort&&selHS&&commData&&<CommodityComparePanel commData={commData} commPorts={commPorts} selHS={selHS} dir={dir} onSelectPort={p=>{setSelPort(p);}}/>}
          {selPort&&<PortPanel selPort={selPort} dir={dir} ci={CONGESTION_ALL[selPort]?.[dir]??0}
            mci={portCI} trend={trend} portComms={portComms} selHS={selHS} commData={commData}
            commFC={commFC} commPorts={commPorts} onSelectHS={setSelHS} onSelectPort={setSelPort}/>}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PANEL: Overview (no port, no commodity)
   ═══════════════════════════════════════════════════════════════════ */
function OverviewPanel({ports,dir,onSelect}){
  return <>
    <div style={{fontSize:15,fontWeight:700,color:C.text}}>
      {dir==="import"?"Import":"Export"} Congestion Overview
    </div>
    <div style={{fontSize:11,color:C.muted,marginBottom:2}}>
      18 monitored ports ranked by congestion index. Click any port to drill in.
    </div>

    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:4}}>
      {[{l:"Highest Risk",v:ports[0]?.name,s:`${(ports[0]?.ci*100).toFixed(0)}% CI`,c:C.red},
        {l:"Lowest Risk",v:ports[ports.length-1]?.name,s:`${(ports[ports.length-1]?.ci*100).toFixed(0)}% CI`,c:C.green},
      ].map((k,i)=>(
        <div key={i} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"10px 12px",textAlign:"center"}}>
          <div style={{fontSize:9,color:C.muted,textTransform:"uppercase",letterSpacing:1.5}}>{k.l}</div>
          <div style={{fontSize:13,fontWeight:800,color:k.c,margin:"2px 0"}}>{k.v}</div>
          <div style={{fontSize:10,color:C.dim}}>{k.s}</div>
        </div>
      ))}
    </div>

    {ports.map((p,i)=>(
      <div key={p.name} onClick={()=>onSelect(p.name)}
        style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"9px 12px",
          borderRadius:8,background:C.card2,border:`1px solid ${C.border}`,cursor:"pointer"}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:10,fontWeight:800,color:C.dim,width:20}}>{i+1}</span>
          <span style={{width:8,height:8,borderRadius:"50%",background:ciColor(p.ci)}}/>
          <span style={{fontSize:12,fontWeight:600,color:C.text}}>{p.name}</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:6}}>
          <span style={{fontSize:13,fontWeight:700,color:ciColor(p.ci)}}>{(p.ci*100).toFixed(0)}%</span>
          <span style={{fontSize:10,color:ciColor(p.ci)}}>{ciLabel(p.ci)}</span>
        </div>
      </div>
    ))}
  </>;
}

/* ═══════════════════════════════════════════════════════════════════
   PANEL: Commodity comparison (no port, commodity selected)
   ═══════════════════════════════════════════════════════════════════ */
function CommodityComparePanel({commData,commPorts,selHS,dir,onSelectPort}){
  if(!commPorts.length)return <div style={{color:C.muted,fontSize:12}}>No data for this commodity.</div>;
  const rec=commPorts[0];
  const bestMonths=rec.ci.map((ci,i)=>({i,ci})).sort((a,b)=>a.ci-b.ci).slice(0,3).map(m=>MN[m.i+1]);
  const worstIdx=rec.ci.indexOf(Math.max(...rec.ci));

  const chartData=Array.from({length:12},(_,i)=>{
    const row={month:MN[i+1]};
    commPorts.slice(0,5).forEach(p=>{row[p.port]=p.fc[i];});
    return row;
  });

  return <>
    <div style={{fontSize:15,fontWeight:700,color:C.text}}>HS{selHS} — {commData.name}</div>
    <div style={{fontSize:11,color:C.muted}}>
      Cross-port comparison for {dir}s. Ranked by volume × (1 − congestion).
    </div>

    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"14px 16px"}}>
      <div style={{fontSize:12,fontWeight:600,color:C.text,marginBottom:8}}>Monthly Forecast 2026</div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{top:4,right:8,bottom:0,left:0}}>
          <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false}/>
          <XAxis dataKey="month" tick={{fill:C.muted,fontSize:10}} axisLine={false} tickLine={false}/>
          <YAxis tick={{fill:C.muted,fontSize:10}} axisLine={false} tickLine={false} tickFormatter={fmtK}/>
          <Tooltip content={<TT/>}/>
          {commPorts.slice(0,5).map((p,i)=>
            <Area key={p.port} type="monotone" dataKey={p.port} name={p.port}
              stroke={PAL[i%PAL.length]} fill={i===0?`${PAL[0]}15`:"none"}
              strokeWidth={i===0?2.5:1.5} dot={false}/>
          )}
        </AreaChart>
      </ResponsiveContainer>
      <div style={{display:"flex",gap:10,flexWrap:"wrap",justifyContent:"center",marginTop:6,fontSize:10,color:C.muted}}>
        {commPorts.slice(0,5).map((p,i)=>
          <span key={p.port}><span style={{display:"inline-block",width:8,height:8,borderRadius:2,background:PAL[i%PAL.length],marginRight:3}}/>{p.port}</span>
        )}
      </div>
    </div>

    <div style={{fontSize:12,fontWeight:600,color:C.text}}>Port Ranking</div>
    {commPorts.map((p,i)=>(
      <div key={p.port} onClick={()=>onSelectPort(p.port)}
        style={{padding:"10px 12px",borderRadius:8,cursor:"pointer",
          background:i===0?`${C.green}10`:C.card2,
          border:`1px solid ${i===0?`${C.green}40`:C.border}`}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:3}}>
          <div style={{display:"flex",alignItems:"center",gap:8}}>
            <span style={{fontSize:11,fontWeight:800,color:C.dim}}>#{i+1}</span>
            <span style={{fontSize:12,fontWeight:700,color:PAL[i%PAL.length]}}>{p.port}</span>
          </div>
          {i===0&&<span style={{padding:"2px 8px",borderRadius:4,background:C.green,color:"#000",fontSize:9,fontWeight:700}}>BEST</span>}
        </div>
        <div style={{display:"flex",gap:12,fontSize:11}}>
          <span style={{color:C.muted}}>{fmtK(p.total)} ships</span>
          <span style={{color:ciColor(p.avgCI)}}>CI: {(p.avgCI*100).toFixed(0)}%</span>
          <span style={{color:C.text,fontWeight:600}}>Score: {fmtK(p.score)}</span>
        </div>
      </div>
    ))}

    <div style={{padding:"10px 14px",borderRadius:8,background:`${C.accent}08`,border:`1px solid ${C.accent}20`,fontSize:11,color:C.muted,lineHeight:1.6}}>
      <span style={{color:C.accent,fontWeight:700}}>Recommendation: </span>
      Ship through <span style={{color:C.green,fontWeight:700}}>{rec.port}</span> ({fmtK(rec.total)} ships, {(rec.avgCI*100).toFixed(0)}% CI).
      Best months: <span style={{color:C.green,fontWeight:600}}>{bestMonths.join(", ")}</span>.
      Avoid <span style={{color:C.red,fontWeight:600}}>{MN[worstIdx+1]}</span>.
    </div>
  </>;
}

/* ═══════════════════════════════════════════════════════════════════
   PANEL: Port detail (port selected)
   ═══════════════════════════════════════════════════════════════════ */
function PortPanel({selPort,dir,ci,mci,trend,portComms,selHS,commData,commFC,commPorts,onSelectHS,onSelectPort}){
  const peakM=mci.indexOf(Math.max(...mci));
  const lowM=mci.indexOf(Math.min(...mci));

  return <>
    {/* Header */}
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
      <div>
        <div style={{fontSize:18,fontWeight:800,color:C.text}}>{selPort}</div>
        <div style={{fontSize:11,color:C.muted,textTransform:"capitalize"}}>{dir}</div>
      </div>
      <div style={{textAlign:"right"}}>
        <div style={{fontSize:30,fontWeight:800,color:ciColor(ci),lineHeight:1}}>{(ci*100).toFixed(0)}%</div>
        <div style={{fontSize:11,color:ciColor(ci),fontWeight:600}}>{ciLabel(ci)}</div>
      </div>
    </div>

    {/* YoY */}
    {trend&&(
      <div style={{display:"flex",gap:12,fontSize:11,padding:"6px 10px",borderRadius:6,background:C.card2}}>
        <span style={{color:C.muted}}>2024: {(trend.ci2024*100).toFixed(0)}%</span>
        <span style={{color:C.muted}}>&rarr;</span>
        <span style={{color:C.muted}}>2025: {(trend.ci2025*100).toFixed(0)}%</span>
        <span style={{color:trend.change>0?C.red:C.green,fontWeight:700}}>
          {trend.change>0?"+":""}{trend.change.toFixed(1)}% YoY
        </span>
      </div>
    )}

    {/* Congestion calendar */}
    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"12px 14px"}}>
      <div style={{fontSize:12,fontWeight:600,color:C.text,marginBottom:8}}>Monthly Congestion</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(12,1fr)",gap:3}}>
        {mci.map((v,i)=>(
          <div key={i} style={{textAlign:"center",padding:"6px 2px",borderRadius:6,
            background:`${ciColor(v)}15`,border:`1px solid ${ciColor(v)}25`}}>
            <div style={{fontSize:9,color:C.muted}}>{MN[i+1]}</div>
            <div style={{fontSize:12,fontWeight:700,color:ciColor(v)}}>{(v*100).toFixed(0)}%</div>
          </div>
        ))}
      </div>
      <div style={{display:"flex",gap:16,marginTop:8,fontSize:11}}>
        <span style={{color:C.green}}>Best: <strong>{MN[lowM+1]}</strong> ({(mci[lowM]*100).toFixed(0)}%)</span>
        <span style={{color:C.red}}>Worst: <strong>{MN[peakM+1]}</strong> ({(mci[peakM]*100).toFixed(0)}%)</span>
      </div>
    </div>

    {/* Commodity detail */}
    {selHS&&commFC&&<CommodityDetail selPort={selPort} selHS={selHS} commData={commData}
      commFC={commFC} mci={mci} commPorts={commPorts} onSelectPort={onSelectPort}/>}

    {selHS&&!commFC&&(
      <div style={{padding:"12px 14px",borderRadius:8,background:`${C.amber}08`,border:`1px solid ${C.amber}20`,fontSize:12,color:C.amber}}>
        HS{selHS} — {commData?.name} is not {dir}ed through {selPort}. Select another port or commodity.
      </div>
    )}

    {/* Commodity list when none selected */}
    {!selHS&&portComms.length>0&&(
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"12px 14px"}}>
        <div style={{fontSize:12,fontWeight:600,color:C.text,marginBottom:8}}>
          Top Commodities
        </div>
        {portComms.slice(0,8).map((c,i)=>{
          const total=c.fc.reduce((a,b)=>a+b,0);
          return <div key={c.hs} onClick={()=>onSelectHS(c.hs)}
            style={{display:"flex",justifyContent:"space-between",alignItems:"center",
              padding:"8px 10px",marginBottom:4,borderRadius:6,background:C.card2,
              border:`1px solid ${C.border}`,cursor:"pointer"}}>
            <span style={{fontSize:11,color:C.text}}>{c.name}</span>
            <span style={{fontSize:11,fontWeight:700,color:PAL[i%PAL.length]}}>{fmtK(total)}</span>
          </div>;
        })}
        <div style={{fontSize:10,color:C.dim,marginTop:4}}>Click a commodity for details</div>
      </div>
    )}

    {!selHS&&portComms.length===0&&(
      <div style={{fontSize:12,color:C.muted,padding:12,background:C.card2,borderRadius:8}}>
        No commodity forecast data available for {selPort} ({dir}).
      </div>
    )}
  </>;
}

/* ═══════════════════════════════════════════════════════════════════
   SUB-PANEL: Commodity detail (port + commodity selected)
   ═══════════════════════════════════════════════════════════════════ */
function CommodityDetail({selPort,selHS,commData,commFC,mci,commPorts,onSelectPort}){
  const total=commFC.reduce((a,b)=>a+b,0);
  const chartData=commFC.map((v,i)=>({month:MN[i+1],forecast:v,congestion:mci[i]}));
  const avgCI=mci.reduce((a,b)=>a+b,0)/12;
  const bestMonths=mci.map((ci,i)=>({i,ci})).sort((a,b)=>a.ci-b.ci).slice(0,3).map(m=>MN[m.i+1]);
  const worstIdx=mci.indexOf(Math.max(...mci));
  const best=commPorts[0];
  const isBest=best&&best.port===selPort;

  return <>
    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"14px 16px"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
        <div>
          <div style={{fontSize:13,fontWeight:700,color:C.text}}>HS{selHS} — {commData?.name}</div>
          <div style={{fontSize:11,color:C.muted}}>2026 forecast: {fmtK(total)} shipments</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={chartData} margin={{top:4,right:35,bottom:0,left:0}}>
          <defs>
            <linearGradient id="cdGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={C.accent} stopOpacity={0.3}/><stop offset="100%" stopColor={C.accent} stopOpacity={0.02}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false}/>
          <XAxis dataKey="month" tick={{fill:C.muted,fontSize:10}} axisLine={false} tickLine={false}/>
          <YAxis yAxisId="fc" tick={{fill:C.muted,fontSize:10}} axisLine={false} tickLine={false} tickFormatter={fmtK}/>
          <YAxis yAxisId="ci" orientation="right" tick={{fill:C.muted,fontSize:10}} axisLine={false} tickLine={false}
            tickFormatter={v=>(v*100).toFixed(0)+"%"} domain={[0,Math.max(0.5,...mci)]}/>
          <Tooltip content={<TT/>}/>
          <Area yAxisId="fc" type="monotone" dataKey="forecast" name="Forecast" stroke={C.accent} fill="url(#cdGrad)" strokeWidth={2} dot={{r:3,fill:C.accent}}/>
          <Area yAxisId="ci" type="monotone" dataKey="congestion" name="Port CI" stroke={C.red} fill="none" strokeWidth={2} strokeDasharray="6 3" dot={{r:3,fill:C.red}}/>
        </AreaChart>
      </ResponsiveContainer>
      <div style={{display:"flex",gap:16,justifyContent:"center",marginTop:6,fontSize:10,color:C.muted}}>
        <span><span style={{display:"inline-block",width:12,height:2,background:C.accent,marginRight:4,verticalAlign:"middle"}}/>Forecast</span>
        <span><span style={{display:"inline-block",width:12,height:2,background:C.red,marginRight:4,verticalAlign:"middle",borderTop:"2px dashed "+C.red}}/>Congestion</span>
      </div>
    </div>

    {/* Other ports */}
    {commPorts.length>1&&(
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"12px 14px"}}>
        <div style={{fontSize:12,fontWeight:600,color:C.text,marginBottom:8}}>Same commodity at other ports</div>
        {commPorts.filter(p=>p.port!==selPort).slice(0,4).map((p,i)=>(
          <div key={p.port} onClick={()=>onSelectPort(p.port)}
            style={{display:"flex",justifyContent:"space-between",alignItems:"center",
              padding:"8px 10px",marginBottom:4,borderRadius:6,background:C.card2,
              border:`1px solid ${C.border}`,cursor:"pointer"}}>
            <div style={{display:"flex",alignItems:"center",gap:6}}>
              {commPorts[0].port===p.port&&<span style={{padding:"1px 6px",borderRadius:3,background:C.green,color:"#000",fontSize:8,fontWeight:700}}>BEST</span>}
              <span style={{fontSize:11,color:C.text,fontWeight:600}}>{p.port}</span>
            </div>
            <div style={{display:"flex",gap:10,fontSize:11}}>
              <span style={{color:C.muted}}>{fmtK(p.total)}</span>
              <span style={{color:ciColor(p.avgCI),fontWeight:600}}>CI: {(p.avgCI*100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
    )}

    {/* Recommendation */}
    <div style={{padding:"10px 14px",borderRadius:8,
      background:isBest?`${C.green}08`:`${C.amber}08`,
      border:`1px solid ${isBest?`${C.green}20`:`${C.amber}20`}`,fontSize:11,color:C.muted,lineHeight:1.6}}>
      <span style={{color:isBest?C.green:C.amber,fontWeight:700}}>
        {isBest?"This is the best port for this commodity":"Better option available"}
      </span>
      {!isBest&&best&&<span> — <span style={{color:C.green,fontWeight:600,cursor:"pointer",textDecoration:"underline"}}
        onClick={()=>onSelectPort(best.port)}>{best.port}</span> has lower congestion ({(best.avgCI*100).toFixed(0)}% vs {(avgCI*100).toFixed(0)}%).</span>}
      <br/>Best months: <span style={{color:C.green,fontWeight:600}}>{bestMonths.join(", ")}</span>.
      Avoid <span style={{color:C.red,fontWeight:600}}>{MN[worstIdx+1]}</span> ({(mci[worstIdx]*100).toFixed(0)}% CI).
    </div>
  </>;
}
