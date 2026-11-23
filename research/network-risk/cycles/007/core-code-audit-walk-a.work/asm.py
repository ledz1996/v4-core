# minimal EVM assembler: list of tokens; ints/hex strings pushed with minimal PUSH; ('label',name), ('ref',name) -> PUSH2
OPS=dict(STOP=0x00,ADD=0x01,MUL=0x02,SUB=0x03,DIV=0x04,LT=0x10,GT=0x11,EQ=0x14,ISZERO=0x15,AND=0x16,OR=0x17,NOT=0x19,BYTE=0x1a,SHL=0x1b,SHR=0x1c,KECCAK256=0x20,
ADDRESS=0x30,BALANCE=0x31,ORIGIN=0x32,CALLER=0x33,CALLVALUE=0x34,CALLDATALOAD=0x35,CALLDATASIZE=0x36,CALLDATACOPY=0x37,CODESIZE=0x38,CODECOPY=0x39,GASPRICE=0x3a,EXTCODESIZE=0x3b,EXTCODECOPY=0x3c,RETURNDATASIZE=0x3d,RETURNDATACOPY=0x3e,EXTCODEHASH=0x3f,
BLOCKHASH=0x40,COINBASE=0x41,TIMESTAMP=0x42,NUMBER=0x43,PREVRANDAO=0x44,GASLIMIT=0x45,CHAINID=0x46,SELFBALANCE=0x47,BASEFEE=0x48,BLOBHASH=0x49,BLOBBASEFEE=0x4a,
POP=0x50,MLOAD=0x51,MSTORE=0x52,MSTORE8=0x53,SLOAD=0x54,SSTORE=0x55,JUMP=0x56,JUMPI=0x57,PC=0x58,MSIZE=0x59,GAS=0x5a,JUMPDEST=0x5b,TLOAD=0x5c,TSTORE=0x5d,MCOPY=0x5e,PUSH0=0x5f,
DUP1=0x80,DUP2=0x81,DUP3=0x82,DUP4=0x83,DUP5=0x84,DUP6=0x85,DUP7=0x86,DUP8=0x87,SWAP1=0x90,SWAP2=0x91,SWAP3=0x92,SWAP4=0x93,
LOG0=0xa0,LOG1=0xa1,LOG2=0xa2,CREATE=0xf0,CALL=0xf1,CALLCODE=0xf2,RETURN=0xf3,DELEGATECALL=0xf4,CREATE2=0xf5,STATICCALL=0xfa,REVERT=0xfd,INVALID=0xfe,SELFDESTRUCT=0xff)
def asm(toks):
    out=bytearray(); labels={}; refs=[]
    for t in toks:
        if isinstance(t,tuple):
            if t[0]=='label': labels[t[1]]=len(out); out.append(0x5b)
            elif t[0]=='ref': out.append(0x61); refs.append((len(out),t[1])); out+=b'\0\0'
            elif t[0]=='raw': out+=bytes.fromhex(t[1])
        elif isinstance(t,int):
            if t==0: out.append(0x5f)
            else:
                b=t.to_bytes((t.bit_length()+7)//8,'big'); out.append(0x5f+len(b)); out+=b
        elif t.startswith('0x'):
            b=bytes.fromhex(t[2:]); out.append(0x5f+len(b)); out+=b
        else: out.append(OPS[t])
    for pos,name in refs: out[pos:pos+2]=labels[name].to_bytes(2,'big')
    return '0x'+out.hex()
