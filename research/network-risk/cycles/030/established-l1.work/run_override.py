"""Run a tools/opdiff script with a blockOverrides object on every eth_call (L-1191).
Usage: OV_NUMBER=98688601 python3 run_override.py <script.py> <args...>
evm.call_code is replaced before the script imports it, so every vector call carries
{"number": OV_NUMBER} as the fourth eth_call parameter. Read-only.
"""
import os, sys, time, runpy
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../tools/opdiff'))
sys.path.insert(0, TOOLS)
import evm  # noqa: E402

NUM = int(os.environ['OV_NUMBER'])


def call_code(url, code, data=b'', gas=None, block='latest', retries=3):
    tx = {'to': evm.STUB, 'data': '0x' + data.hex()}
    if gas: tx['gas'] = hex(gas)
    last = None
    for k in range(retries):
        try:
            return bytes.fromhex(evm.rpc(url, 'eth_call', [tx, block, {evm.STUB: {'code': '0x' + code.hex()}},
                                                           {'number': hex(NUM)}])[2:])
        except Exception as e:  # noqa
            last = e; time.sleep(1.5 * (k + 1))
    raise last


evm.call_code = call_code
script = os.path.join(TOOLS, sys.argv[1])
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name='__main__')
