import re,sys,glob,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak256
def k(s): 
    r=keccak256(s.encode() if isinstance(s,str) else s)
    return r.hex() if isinstance(r,(bytes,bytearray)) else r
print('keccak empty', k(''))
# slots
for name,val in [("Unlocked","c090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23"),
                 ("NonzeroDeltaCount","7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b"),
                 ("ReservesOf","1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95"),
                 ("Currency","27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9")]:
    h=int(k(name),16)-1
    print(name, '%064x'%h==val)
def sel(s): return k(s)[:8]
print('transfer(address,uint256)', sel('transfer(address,uint256)'))
print('balanceOf(address)', sel('balanceOf(address)'))
print('unlockCallback(bytes)', sel('unlockCallback(bytes)'))
# ERC6909 interface id
sigs=['balanceOf(address,uint256)','allowance(address,address,uint256)','isOperator(address,address)','transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)']
x=0
for s in sigs: x^=int(sel(s),16)
print('erc6909 id %08x'%x, 'erc165 id', sel('supportsInterface(bytes4)'))
# errors
for e in ['CurrencyNotSettled()','AlreadyUnlocked()','ManagerLocked()','NonzeroNativeValue()','MustClearExactPositiveDelta()','InvalidCaller()','ProtocolFeeCurrencySynced()','WrappedError(address,bytes4,bytes,bytes)','NotApproved(address)']:
    print(e, sel(e))
# hex literal masks in src
for f in sorted(glob.glob('src/**/*.sol',recursive=True)):
    if '/test/' in f: continue
    for i,l in enumerate(open(f),1):
        for m in re.findall(r'0x[0-9a-fA-F]{9,}',l):
            body=m[2:]
            if set(body.lower())<=set('f0') :
                print(f,i,len(body),m)
