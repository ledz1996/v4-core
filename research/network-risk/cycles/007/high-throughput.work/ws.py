# minimal WebSocket client through the HTTPS proxy (CONNECT), standard library only
import socket,ssl,os,base64,struct,json,time,sys
def connect(host,path,proxy=('127.0.0.1',33307)):
    s=socket.create_connection(proxy,timeout=30)
    s.sendall(f'CONNECT {host}:443 HTTP/1.1\r\nHost: {host}:443\r\n\r\n'.encode())
    buf=b''
    while b'\r\n\r\n' not in buf:
        d=s.recv(4096)
        if not d: raise Exception('proxy closed: '+buf.decode(errors='replace'))
        buf+=d
    if b' 200' not in buf.split(b'\r\n')[0]: raise Exception('CONNECT failed: '+buf.decode(errors='replace')[:300])
    ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
    ss=ctx.wrap_socket(s,server_hostname=host)
    key=base64.b64encode(os.urandom(16)).decode()
    ss.sendall(f'GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nUser-Agent: curl/8\r\n\r\n'.encode())
    buf=b''
    while b'\r\n\r\n' not in buf:
        d=ss.recv(4096)
        if not d: raise Exception('server closed during upgrade: '+buf.decode(errors='replace')[:300])
        buf+=d
    head,rest=buf.split(b'\r\n\r\n',1)
    if b' 101' not in head.split(b'\r\n')[0]: raise Exception('upgrade failed: '+head.decode(errors='replace')[:400])
    return ss,rest
def send(ss,text,opcode=1):
    p=text.encode() if isinstance(text,str) else text
    mask=os.urandom(4)
    hdr=bytes([0x80|opcode])
    n=len(p)
    if n<126: hdr+=bytes([0x80|n])
    elif n<65536: hdr+=bytes([0x80|126])+struct.pack('>H',n)
    else: hdr+=bytes([0x80|127])+struct.pack('>Q',n)
    ss.sendall(hdr+mask+bytes(b^mask[i%4] for i,b in enumerate(p)))
class Reader:
    def __init__(self,ss,rest=b''): self.ss=ss; self.buf=rest
    def need(self,n):
        while len(self.buf)<n:
            d=self.ss.recv(65536)
            if not d: raise EOFError
            self.buf+=d
        out=self.buf[:n]; self.buf=self.buf[n:]; return out
    def frame(self):
        msg=b''
        while True:
            b0,b1=self.need(2)
            fin=b0&0x80; op=b0&0x0f; n=b1&0x7f
            if n==126: n=struct.unpack('>H',self.need(2))[0]
            elif n==127: n=struct.unpack('>Q',self.need(8))[0]
            if b1&0x80: mask=self.need(4)
            p=self.need(n)
            if op==9: send(self.ss,p,opcode=10); continue
            if op==8: raise EOFError('close '+p.decode(errors='replace'))
            if op in (0,1,2): msg+=p
            if fin and op in (0,1,2): return msg
if __name__=='__main__':
    ss,rest=connect('mainnet.megaeth.com','/ws')
    rd=Reader(ss,rest)
    send(ss,json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}))
    print(rd.frame()[:200])
