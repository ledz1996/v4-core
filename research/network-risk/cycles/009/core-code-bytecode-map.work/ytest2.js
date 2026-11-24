const solc = require(process.argv[2])
for (const src of ['object "a" { code { sstore(0, 1) } }', 'object "a" { code { tstore(0, 1) } }']) {
const y = { language: 'Yul', sources: { 'pm.yul': { content: src } }, settings: { evmVersion: 'cancun', outputSelection: { '*': { '*': ['*'] } } } }
const r = JSON.parse(solc.compile(JSON.stringify(y)))
console.log(src, r.contracts ? Object.keys(r.contracts['pm.yul']) : null, (r.errors||[]).map(e=>e.severity))
}
