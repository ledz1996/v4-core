// Compile src/Seq.sol with solc-js 0.8.26 (same settings as the cycle 25 driver).
// Usage: node compile_seq.js <node_modules/solc> <Seq.sol> <out.json>
const fs = require('fs')
const [solcPath, srcPath, out] = process.argv.slice(2)
const solc = require(solcPath)
const names = ["Seq", "Tok", "Hk", "Hk2", "HkA", "HkB", "Meta"]
const sel = {}; for (const n of names) sel[n] = ['evm.deployedBytecode.object', 'evm.bytecode.object', 'evm.methodIdentifiers']
const input = { language: 'Solidity', sources: { 'Seq.sol': { content: fs.readFileSync(srcPath, 'utf8') } },
  settings: { optimizer: { enabled: true, runs: 200 }, viaIR: true, evmVersion: 'cancun', metadata: { bytecodeHash: 'none' },
    outputSelection: { 'Seq.sol': sel } } }
const res = JSON.parse(solc.compile(JSON.stringify(input)))
const errs = (res.errors || []).filter(e => e.severity === 'error')
if (errs.length) { console.error(errs.map(e => e.formattedMessage).join('\n')); process.exit(1) }
const d = res.contracts['Seq.sol']; const o = { compiler: solc.version(), settings: input.settings }
for (const n of names) o[n] = { runtime: d[n].evm.deployedBytecode.object, init: d[n].evm.bytecode.object, methods: d[n].evm.methodIdentifiers }
fs.writeFileSync(out, JSON.stringify(o, null, 1))
console.log(solc.version(), names.map(n => n + ' ' + d[n].evm.deployedBytecode.object.length / 2).join(', '), 'warnings', (res.errors || []).length)
