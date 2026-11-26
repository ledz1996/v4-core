// Compile src/ProbeBytesAt.sol with the same solc-js 0.8.26 settings as the driver. Usage: node compile_probe.js <solc> <src> <out>
const fs = require('fs'); const [solcPath, srcPath, out] = process.argv.slice(2); const solc = require(solcPath)
const input = { language: 'Solidity', sources: { 'P.sol': { content: fs.readFileSync(srcPath, 'utf8') } },
  settings: { optimizer: { enabled: true, runs: 200 }, viaIR: true, evmVersion: 'cancun', metadata: { bytecodeHash: 'none' },
    outputSelection: { 'P.sol': { '*': ['evm.deployedBytecode.object', 'evm.methodIdentifiers'] } } } }
const res = JSON.parse(solc.compile(JSON.stringify(input)))
const errs = (res.errors || []).filter(e => e.severity === 'error'); if (errs.length) { console.error(errs.map(e => e.formattedMessage).join('\n')); process.exit(1) }
const c = res.contracts['P.sol'].ProbeBytesAt
fs.writeFileSync(out, JSON.stringify({ compiler: solc.version(), code: c.evm.deployedBytecode.object, methods: c.evm.methodIdentifiers }, null, 1))
console.log('ok', c.evm.deployedBytecode.object.length / 2)
