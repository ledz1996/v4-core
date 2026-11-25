//   0x3bb:
B3bb:
cmp qword ptr [rsp+48], 5
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 34
jl Error
//       0x3bc: AND
vmovaps ymm0, qword ptr [rbp-32]
vpand ymm0, ymm0, qword ptr [rbp-64]
//       0x3bd: SWAP3
//       0x3be: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x3bf: DUP5
//       0x3c0: EQ
vmovaps qword ptr [rbp-64], ymm0
xor r12, qword ptr [rbp-64]
xor r13, qword ptr [rbp-56]
xor r14, qword ptr [rbp-48]
xor r15, qword ptr [rbp-40]
or r12, r13
or r14, r15
or r12, r14
//       0x3c1: ISZERO
//       0x3c2: DUP1
//       0x3c3: PUSH2 0x4a0
//     0x3c6: JumpI 58
setne al
movzx eax, al
vmovd xmm1, eax
vmovaps qword ptr [rbp-32], ymm1
vmovaps ymm1, qword ptr [rbp-160]
vmovaps qword ptr [rbp-64], ymm1
vmovaps qword ptr [rbp-160], ymm0
jne B4a0
//   0x3c7:
B3c7:
cmp qword ptr [rsp+48], 1
jb Error
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 14
jl Error
//       0x3c8: PUSH2 0x3f2
//     0x3cb: JumpI 59
vmovaps ymm0, qword ptr [rbp-32]
vptest ymm0, ymm0
mov rax, qword ptr [rsp+48]
lea rax, [rax-1]
lea rbp, [rbp-32]
mov qword ptr [rsp+48], rax
jne B3f2
//   0x3f2:
B3f2:
cmp qword ptr [rsp+48], 6
jb Error
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 287
jl Error
//       0x3f3: DUP4
//       0x3f4: DUP6
//       0x3f5: MSTORE
mov rax, qword ptr [rbp-152]
or rax, qword ptr [rbp-144]
or rax, qword ptr [rbp-136]
jnz Error
mov rax, qword ptr [rbp-160]
test rax, -268435456
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L690
call qword ptr [ROD]
L690:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-128], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x3f6: PUSH1 0x5
//       0x3f8: PUSH1 0x20
//       0x3fa: MSTORE
cmp dword ptr [rbx+264], 64
jae L691
mov rdi, 64
call qword ptr [ROD]
L691:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1408]
vmovups qword ptr [rax+32], ymm0
//       0x3fb: PUSH1 0x40
//       0x3fd: DUP6
//       0x3fe: KECCAK256
lea rdx, qword ptr [rbp-160]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x3ff: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x414: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x415: AND
and r14, qword ptr [ROD+1168]
and r15, 0
//       0x416: DUP7
//       0x417: MSTORE
mov rax, qword ptr [rbp-160]
add rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x418: PUSH1 0x20
//       0x41a: MSTORE
cmp dword ptr [rbx+264], 64
jae L692
mov rdi, 64
call qword ptr [ROD]
L692:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x41b: PUSH1 0x40
//       0x41d: DUP6
//       0x41e: KECCAK256
lea rdx, qword ptr [rbp-160]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x41f: DUP7
//       0x420: DUP7
//       0x421: MSTORE
mov rax, qword ptr [rbp-160]
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-192], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x422: PUSH1 0x20
//       0x424: MSTORE
cmp dword ptr [rbx+264], 64
jae L693
mov rdi, 64
call qword ptr [ROD]
L693:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x425: PUSH1 0x40
//       0x427: DUP6
//       0x428: KECCAK256
lea rdx, qword ptr [rbp-160]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x429: SLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x42a: DUP2
//       0x42b: PUSH32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
//       0x44c: DUP3
//       0x44d: SUB
mov r12, qword ptr [rbp]
mov r13, qword ptr [rbp+8]
mov r14, qword ptr [rbp+16]
mov r15, qword ptr [rbp+24]
sub r12, -1
sbb r13, -1
sbb r14, -1
sbb r15, -1
//       0x44e: PUSH2 0x459
//     0x451: JumpI 62
or r13, r12
or r14, r15
or r13, r14
vmovaps ymm0, qword ptr [rbp-32]
vmovaps qword ptr [rbp+32], ymm0
mov rax, qword ptr [rsp+48]
lea rax, [rax+2]
lea rbp, [rbp+64]
mov qword ptr [rsp+48], rax
jne B459
//   0x452:
B452:
cmp qword ptr [rsp+48], 2
jb Error
sub qword ptr [rbx+16], 16
jl Error
//       0x453: POP
//       0x454: POP
//       0x455: PUSH2 0x3cc
//     0x458: Jump
add qword ptr [rsp+48], -2
add rbp, -64
jmp B3cc
//   0x459:
B459:
cmp qword ptr [rsp+48], 2
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 18
jl Error
//       0x45a: PUSH2 0x462
//       0x45d: SWAP2
//       0x45e: PUSH2 0x2fed
//     0x461: Jump
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp], ymm0
vmovd xmm0, dword ptr [ROD+1500]
vmovaps qword ptr [rbp-64], ymm0
add qword ptr [rsp+48], 1
add rbp, 32
jmp B2fed
//   0x462:
B462:
cmp qword ptr [rsp+48], 8
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 279
jl Error
//       0x463: DUP5
//       0x464: DUP7
//       0x465: MSTORE
mov rax, qword ptr [rbp-184]
or rax, qword ptr [rbp-176]
or rax, qword ptr [rbp-168]
jnz Error
mov rax, qword ptr [rbp-192]
test rax, -268435456
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L694
call qword ptr [ROD]
L694:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-160], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x466: PUSH1 0x5
//       0x468: PUSH1 0x20
//       0x46a: MSTORE
cmp dword ptr [rbx+264], 64
jae L695
mov rdi, 64
call qword ptr [ROD]
L695:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1408]
vmovups qword ptr [rax+32], ymm0
//       0x46b: PUSH1 0x40
//       0x46d: DUP7
//       0x46e: KECCAK256
lea rdx, qword ptr [rbp-192]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x46f: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x484: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x485: AND
and r14, qword ptr [ROD+1168]
and r15, 0
//       0x486: DUP8
//       0x487: MSTORE
mov rax, qword ptr [rbp-192]
add rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x488: PUSH1 0x20
//       0x48a: MSTORE
cmp dword ptr [rbx+264], 64
jae L696
mov rdi, 64
call qword ptr [ROD]
L696:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x48b: PUSH1 0x40
//       0x48d: DUP7
//       0x48e: KECCAK256
lea rdx, qword ptr [rbp-192]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x48f: DUP8
//       0x490: DUP8
//       0x491: MSTORE
mov rax, qword ptr [rbp-192]
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-224], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x492: PUSH1 0x20
//       0x494: MSTORE
cmp dword ptr [rbx+264], 64
jae L697
mov rdi, 64
call qword ptr [ROD]
L697:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x495: PUSH1 0x40
//       0x497: DUP7
//       0x498: KECCAK256
lea rdx, qword ptr [rbp-192]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x499: SSTORE
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 17
vzeroupper
call qword ptr [ROD+1344]
//       0x49a: DUP7
//       0x49b: DUP2
//       0x49c: PUSH2 0x452
//     0x49f: Jump
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp], ymm0
vmovaps ymm0, qword ptr [rbp-256]
vmovaps qword ptr [rbp-32], ymm0
add qword ptr [rsp+48], 1
add rbp, 32
jmp B452
//   0x4a0:
B4a0:
cmp qword ptr [rsp+48], 6
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 233
jl Error
//       0x4a1: POP
//       0x4a2: DUP4
//       0x4a3: DUP6
//       0x4a4: MSTORE
mov rax, qword ptr [rbp-184]
or rax, qword ptr [rbp-176]
or rax, qword ptr [rbp-168]
jnz Error
mov rax, qword ptr [rbp-192]
test rax, -268435456
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L698
call qword ptr [ROD]
L698:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-160], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x4a5: PUSH1 0x3
//       0x4a7: PUSH1 0x20
//       0x4a9: MSTORE
cmp dword ptr [rbx+264], 64
jae L699
mov rdi, 64
call qword ptr [ROD]
L699:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1440]
vmovups qword ptr [rax+32], ymm0
//       0x4aa: PUSH1 0x40
//       0x4ac: DUP6
//       0x4ad: KECCAK256
lea rdx, qword ptr [rbp-192]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+1192]
//       0x4ae: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x4c3: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x4c4: AND
and r14, qword ptr [ROD+1168]
and r15, 0
//       0x4c5: DUP7
//       0x4c6: MSTORE
mov rax, qword ptr [rbp-192]
add rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x4c7: PUSH1 0x20
//       0x4c9: MSTORE
cmp dword ptr [rbx+264], 64
jae L700
mov rdi, 64
call qword ptr [ROD]
L700:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-32], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x4ca: PUSH1 0xff
//       0x4cc: PUSH1 0x40
//       0x4ce: DUP7
//       0x4cf: KECCAK256
lea rdx, qword ptr [rbp-192]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x4d0: SLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x4d1: AND
vmovd xmm0, dword ptr [ROD+1472]
vpand ymm0, ymm0, qword ptr [rbp]
//       0x4d2: ISZERO
vptest ymm0, ymm0
//       0x4d3: PUSH2 0x3c7
//     0x4d6: Jump
sete al
movzx eax, al
vmovd xmm0, eax
vmovaps qword ptr [rbp-32], ymm0
jmp B3c7
