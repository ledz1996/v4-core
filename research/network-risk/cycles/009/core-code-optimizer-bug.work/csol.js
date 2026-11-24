// Compile one Solidity file with solc-js and given settings. Usage: node csol.js <solc> <file> <out.json> <steps|default|noLE> <viaIR 0|1> <opt 0|1>
const fs=require('fs');const [sp,file,out,steps,via,opt]=process.argv.slice(2);const solc=require(sp)
const o={enabled:opt==='1',runs:44444444}
if(steps!=='default'&&opt==='1')o.details={yulDetails:{optimizerSteps:steps}}
const input={language:'Solidity',sources:{[file]:{content:fs.readFileSync(file,'utf8')}},settings:{optimizer:o,viaIR:via==='1',evmVersion:'cancun',metadata:{bytecodeHash:'none'},outputSelection:{'*':{'*':['evm.deployedBytecode.object','irOptimized','evm.methodIdentifiers']}}}}
const r=JSON.parse(solc.compile(JSON.stringify(input)));const e=(r.errors||[]).filter(x=>x.severity==='error');if(e.length){console.error(e.map(x=>x.formattedMessage).join('\n'));process.exit(1)}
const res={};for(const [n,c] of Object.entries(r.contracts[file]))res[n]={runtime:c.evm.deployedBytecode.object,ir:c.irOptimized,ids:c.evm.methodIdentifiers}
fs.writeFileSync(out,JSON.stringify({compiler:solc.version(),settings:input.settings,contracts:res},null,1));console.log(solc.version(),Object.keys(res))
