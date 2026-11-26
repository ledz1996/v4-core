// Compile src/DriverHx.sol with the solc-js 0.8.26 package used for research/network-risk/build.
// Usage: node compile_driver.js <node_modules/solc> <DriverHx.sol> <out.json>
const fs = require('fs')
const [solcPath, srcPath, out] = process.argv.slice(2)
const solc = require(solcPath)
const input = { language: 'Solidity', sources: { 'DriverHx.sol': { content: fs.readFileSync(srcPath, 'utf8') } },
  settings: { optimizer: { enabled: true, runs: 200 }, viaIR: true, evmVersion: 'cancun', metadata: { bytecodeHash: 'none' },
    outputSelection: { 'DriverHx.sol': { Driver: ['evm.deployedBytecode.object', 'evm.methodIdentifiers'], Tok: ['evm.deployedBytecode.object'] } } } }
const res = JSON.parse(solc.compile(JSON.stringify(input)))
const errs = (res.errors || []).filter(e => e.severity === 'error')
if (errs.length) { console.error(errs.map(e => e.formattedMessage).join('\n')); process.exit(1) }
const d = res.contracts['DriverHx.sol']
fs.writeFileSync(out, JSON.stringify({ compiler: solc.version(), settings: input.settings, driver: d.Driver.evm.deployedBytecode.object,
  tok: d.Tok.evm.deployedBytecode.object, methods: d.Driver.evm.methodIdentifiers }, null, 1))
console.log(solc.version(), 'driver', d.Driver.evm.deployedBytecode.object.length / 2, 'tok', d.Tok.evm.deployedBytecode.object.length / 2, 'warnings', (res.errors||[]).length)
