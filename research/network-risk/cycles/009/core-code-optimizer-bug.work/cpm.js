// Build src/PoolManager.sol as research/network-risk/tools/build/compile.js does, with an optional Yul step sequence and a chosen output selection.
// Usage: node cpm.js <solc dir> <repo root> <out.json> <steps|default> <comma separated outputs>
const fs=require('fs'),path=require('path');const [sp,root,out,steps,outs]=process.argv.slice(2);const solc=require(sp)
const remap=fs.readFileSync(path.join(root,'remappings.txt'),'utf8').split('\n').filter(Boolean).map(l=>l.split('='))
function resolve(p){for(const [f,t] of remap) if(p.startsWith(f)) return path.join(root,t,p.slice(f.length)); return path.join(root,p)}
const o={enabled:true,runs:44444444}; if(steps!=='default') o.details={yulDetails:{optimizerSteps:steps}}
const input={language:'Solidity',sources:{'src/PoolManager.sol':{content:fs.readFileSync(path.join(root,'src/PoolManager.sol'),'utf8')}},settings:{optimizer:o,viaIR:true,evmVersion:'cancun',metadata:{bytecodeHash:'none'},outputSelection:{'src/PoolManager.sol':{PoolManager:outs.split(',')}}}}
const t0=Date.now()
const r=JSON.parse(solc.compile(JSON.stringify(input),{import:p=>{try{return{contents:fs.readFileSync(resolve(p),'utf8')}}catch(e){return{error:String(e)}}}}))
const e=(r.errors||[]).filter(x=>x.severity==='error'); if(e.length){console.error(e.map(x=>x.formattedMessage).join('\n').slice(0,3000));process.exit(1)}
const c=r.contracts['src/PoolManager.sol'].PoolManager
fs.writeFileSync(out,JSON.stringify({compiler:solc.version(),settings:input.settings,ir:c.ir,irOptimized:c.irOptimized,creation:c.evm&&c.evm.bytecode&&c.evm.bytecode.object,runtime:c.evm&&c.evm.deployedBytecode&&c.evm.deployedBytecode.object},null,1))
console.log('done',Math.round((Date.now()-t0)/1000),'s',c.evm&&c.evm.deployedBytecode?c.evm.deployedBytecode.object.length/2:'')
