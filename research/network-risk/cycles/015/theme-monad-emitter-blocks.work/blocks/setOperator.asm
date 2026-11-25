//   0x20c1:
cmp qword ptr [rsp+48], 1018
ja Error
sub qword ptr [rbx+16], 1886
jl Error
//       0x20c1: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x20d6: SWAP1
//       0x20d7: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x20d8: PUSH0
//       0x20d9: MSTORE
cmp dword ptr [rbx+264], 32
jae L1058
mov rdi, 32
call qword ptr [ROD]
L1058:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x20da: PUSH1 0x3
//       0x20dc: PUSH1 0x20
//       0x20de: MSTORE
cmp dword ptr [rbx+264], 64
jae L1059
mov rdi, 64
call qword ptr [ROD]
L1059:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1440]
vmovups qword ptr [rax+32], ymm0
//       0x20df: PUSH1 0x40
//       0x20e1: PUSH0
//       0x20e2: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp+64]
vzeroupper
call qword ptr [ROD+1192]
//       0x20e3: DUP3
//       0x20e4: DUP3
//       0x20e5: AND
vmovaps ymm0, qword ptr [ROD+1152]
vpand ymm1, ymm0, qword ptr [rbp-32]
//       0x20e6: PUSH0
//       0x20e7: MSTORE
cmp dword ptr [rbx+264], 32
jae L1060
mov rdi, 32
call qword ptr [ROD]
L1060:
mov rax, qword ptr [rbx+272]
vpermq ymm2, ymm1, 27
vpshufb ymm2, ymm2, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm2
//       0x20e8: PUSH1 0x20
//       0x20ea: MSTORE
cmp dword ptr [rbx+264], 64
jae L1061
mov rdi, 64
call qword ptr [ROD]
L1061:
mov rax, qword ptr [rbx+272]
vpermq ymm1, qword ptr [rbp+64], 27
vpshufb ymm1, ymm1, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm1
//       0x20eb: PUSH1 0x40
//       0x20ed: PUSH0
//       0x20ee: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp+64]
vzeroupper
call qword ptr [ROD+1192]
//       0x20ef: PUSH32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00
//       0x2110: DUP2
//       0x2111: SLOAD
lea rdx, qword ptr [rbp+64]
mov rdi, rbx
lea rsi, qword ptr [rbp+128]
vzeroupper
call qword ptr [ROD+1200]
//       0x2112: AND
vmovaps ymm0, qword ptr [ROD+3040]
vpand ymm0, ymm0, qword ptr [rbp+128]
//       0x2113: PUSH1 0xff
//       0x2115: DUP6
//       0x2116: AND
vmovd xmm1, dword ptr [ROD+1472]
vpand ymm1, ymm1, qword ptr [rbp+32]
//       0x2117: OR
vpor ymm1, ymm1, ymm0
//       0x2118: SWAP1
//       0x2119: SSTORE
vmovaps qword ptr [rbp], ymm1
lea rsi, qword ptr [rbp+64]
lea rdx, qword ptr [rbp]
mov rdi, rbx
mov rcx, 1550
vzeroupper
call qword ptr [ROD+1344]
//       0x211a: PUSH1 0x40
//       0x211c: MLOAD
cmp dword ptr [rbx+264], 96
jae L1062
mov rdi, 96
call qword ptr [ROD]
L1062:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x211d: SWAP3
//       0x211e: DUP4
//       0x211f: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1063
call qword ptr [ROD]
L1063:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp+32], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2120: AND
vmovaps ymm0, qword ptr [ROD+1152]
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0x2121: SWAP1
//       0x2122: PUSH32 0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267
//       0x2143: PUSH1 0x20
//       0x2145: CALLER
movbe r8d, dword ptr [rbx+60]
movbe r11, qword ptr [rbx+64]
movbe r10, qword ptr [rbx+72]
xor r9d, r9d
//       0x2146: SWAP3
//       0x2147: LOG3
mov qword ptr [rbp], r10
mov qword ptr [rbp+8], r11
mov qword ptr [rbp+16], r8
mov qword ptr [rbp+24], r9
vmovaps qword ptr [rbp-32], ymm0
mov qword ptr [rbp+32], r12
mov qword ptr [rbp+40], r13
mov qword ptr [rbp+48], r14
mov qword ptr [rbp+56], r15
lea rsi, qword ptr [rbp+32]
lea rdx, qword ptr [ROD+3072]
lea rcx, qword ptr [ROD+3104]
lea r8, qword ptr [rbp]
lea r9, qword ptr [rbp-32]
mov rdi, rbx
vzeroupper
call qword ptr [ROD+1656]
//       0x2148: PUSH1 0x20
//       0x214a: PUSH1 0x40
//       0x214c: MLOAD
cmp dword ptr [rbx+264], 96
jae L1064
mov rdi, 96
call qword ptr [ROD]
L1064:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x214d: PUSH1 0x1
//       0x214f: DUP2
//       0x2150: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1065
call qword ptr [ROD]
L1065:
add rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1376]
vmovups qword ptr [rax], ymm0
//     0x2151: Return
mov qword ptr [rbx+256], 0
mov qword ptr [rbx+192], r12
mov qword ptr [rbx+200], r13
mov qword ptr [rbx+208], r14
mov qword ptr [rbx+216], r15
vmovd xmm0, dword ptr [ROD+1368]
vmovups qword ptr [rbx+224], ymm0
jmp ContractEpilogue
