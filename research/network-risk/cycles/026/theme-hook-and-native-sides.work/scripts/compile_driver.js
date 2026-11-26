// Compile src/Driver26.sol with the solc-js 0.8.26 package used for research/network-risk/build.
// Usage: node compile_driver.js <node_modules/solc> <Driver26.sol> <out.json>
const fs = require('fs')
const [solcPath, srcPath, out] = process.argv.slice(2)
const solc = require(solcPath)
const input = { language: 'Solidity', sources: { 'Driver26.sol': { content: fs.readFileSync(srcPath, 'utf8') } },
  settings: { optimizer: { enabled: true, runs: 200 }, viaIR: true, evmVersion: 'cancun', metadata: { bytecodeHash: 'none' },
    outputSelection: { 'Driver26.sol': { Driver: ['evm.deployedBytecode.object', 'evm.methodIdentifiers'], Tok: ['evm.deployedBytecode.object'],
      Hk: ['evm.deployedBytecode.object', 'evm.methodIdentifiers'], IH: ['evm.methodIdentifiers'] } } } }
const res = JSON.parse(solc.compile(JSON.stringify(input)))
const errs = (res.errors || []).filter(e => e.severity === 'error')
if (errs.length) { console.error(errs.map(e => e.formattedMessage).join('\n')); process.exit(1) }
const d = res.contracts['Driver26.sol']
fs.writeFileSync(out, JSON.stringify({ compiler: solc.version(), settings: input.settings, driver: d.Driver.evm.deployedBytecode.object,
  tok: d.Tok.evm.deployedBytecode.object, hk: d.Hk.evm.deployedBytecode.object, methods: d.Driver.evm.methodIdentifiers,
  hkMethods: d.Hk.evm.methodIdentifiers, hooks: d.IH.evm.methodIdentifiers }, null, 1))
console.log(solc.version(), 'driver', d.Driver.evm.deployedBytecode.object.length / 2, 'hk', d.Hk.evm.deployedBytecode.object.length / 2, 'warnings', (res.errors||[]).length)
