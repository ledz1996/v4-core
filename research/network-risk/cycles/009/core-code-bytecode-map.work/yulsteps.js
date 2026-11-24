// Run the Yul optimizer of solc 0.8.26 on the unoptimized IR of PoolManager with a given step sequence.
// Usage: node yulsteps.js <solc dir> <repo root> <out prefix> <steps> [<steps> ...]
const fs = require('fs'), path = require('path')
const [solcPath, root, out, ...seqs] = process.argv.slice(2)
const solc = require(solcPath)
const remap = fs.readFileSync(path.join(root, 'remappings.txt'), 'utf8').split('\n').filter(Boolean).map(l => l.split('='))
function resolve(p) { for (const [from, to] of remap) if (p.startsWith(from)) return path.join(root, to, p.slice(from.length)); return path.join(root, p) }
const imp = { import: p => { try { return { contents: fs.readFileSync(resolve(p), 'utf8') } } catch (e) { return { error: String(e) } } } }
let ir
if (fs.existsSync(out + '.sub.yul')) ir = fs.readFileSync(out + '.sub.yul', 'utf8')
else {
  const input = { language: 'Solidity', sources: { 'src/PoolManager.sol': { content: fs.readFileSync(path.join(root, 'src/PoolManager.sol'), 'utf8') } },
    settings: { optimizer: { enabled: true, runs: 44444444 }, viaIR: true, evmVersion: 'cancun', metadata: { bytecodeHash: 'none' }, outputSelection: { 'src/PoolManager.sol': { PoolManager: ['ir'] } } } }
  const res = JSON.parse(solc.compile(JSON.stringify(input), imp))
  ir = res.contracts['src/PoolManager.sol'].PoolManager.ir; fs.writeFileSync(out + '.ir.yul', ir)
}
seqs.forEach((steps, i) => {
  const y = { language: 'Yul', sources: { 'pm.yul': { content: ir } },
    settings: { optimizer: { enabled: true, runs: 44444444, details: { yul: true, yulDetails: { optimizerSteps: steps } } }, evmVersion: 'cancun', outputSelection: { 'pm.yul': { '*': ['irOptimized', 'evm.bytecode.object'] } } } }
  const r = JSON.parse(solc.compile(JSON.stringify(y))); if (!r.contracts) { console.error(JSON.stringify(r).slice(0, 1500)); return }
  const errs = (r.errors || []).filter(e => e.severity === 'error')
  if (errs.length) { console.error(i, errs.map(e => e.formattedMessage).join('\n').slice(0, 2000)); return }
  const c = Object.values(r.contracts['pm.yul'])[0]
  fs.writeFileSync(out + '.' + i + '.yul', c.irOptimized)
  console.log(i, 'ok', c.irOptimized.length, 'chars, runtime', (c.evm.bytecode.object || '').length / 2)
})
