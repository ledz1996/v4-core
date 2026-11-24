const solc = require(process.argv[2]); const fs=require('fs')
const ir = fs.readFileSync('yl.ir.yul','utf8')
for (const sel of [{ '*': { '*': ['*'] } }, { 'pm.yul': { '': ['*'], '*': ['*'] } }]) {
const y = { language: 'Yul', sources: { 'pm.yul': { content: ir } }, settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: 'cancun', outputSelection: sel } }
const r = JSON.parse(solc.compile(JSON.stringify(y)))
console.log(Object.keys(r), r.contracts ? Object.keys(r.contracts) : null, (r.errors||[]).map(e=>e.severity+':'+e.message.slice(0,80)))
}
