"""keccak256 via build/kec (C reference from cycle 22)."""
import subprocess, os
K = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'kec')
def keccak(b: bytes) -> bytes:
    if not b: return bytes.fromhex('c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
    return subprocess.run([K, str(len(b))], input=b, capture_output=True).stdout
def c2(deployer, salt, init):
    return '0x' + keccak(b'\xff' + bytes.fromhex(deployer[2:]) + salt + keccak(init))[12:].hex()
if __name__ == '__main__':
    assert keccak(b'abc').hex() == '4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45'; print('kec ok')
def rlp_create(sender, nonce):
    a = bytes.fromhex(sender[2:])
    if nonce == 0: n = b'\x80'
    elif nonce < 0x80: n = bytes([nonce])
    else:
        nb = nonce.to_bytes((nonce.bit_length() + 7) // 8, 'big'); n = bytes([0x80 + len(nb)]) + nb
    body = bytes([0x94]) + a + n
    return '0x' + keccak(bytes([0xc0 + len(body)]) + body)[12:].hex()
