//   0xde6:
cmp qword ptr [rsp+48], 1
jb Error
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 184
//       0xde6: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0xde7: PUSH0
//       0xde8: SWAP1
//       0xde9: DUP2
//       0xdea: MSTORE
cmp dword ptr [rbx+264], 32
jae L804
mov rdi, 32
call qword ptr [ROD]
L804:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0xdeb: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0xe00: DUP3
//       0xe01: AND
vmovaps ymm0, qword ptr [ROD+1152]
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0xe02: PUSH1 0x20
//       0xe04: MSTORE
cmp dword ptr [rbx+264], 64
jae L805
mov rdi, 64
call qword ptr [ROD]
L805:
mov rax, qword ptr [rbx+272]
vpermq ymm1, ymm0, 27
vpshufb ymm1, ymm1, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm1
//       0xe05: PUSH1 0x40
//       0xe07: SWAP1
//       0xe08: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0xe09: TLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1480]
//       0xe0a: PUSH2 0xe14
//       0xe0d: PUSH1 0x24
//       0xe0f: CALLDATALOAD
vpxor ymm0, ymm0, ymm0
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
add rdi, 36
sub rsi, 36
cmp rsi, 32
jl L807
vmovups ymm15, byte ptr [rdi]
L808:
vpermq ymm0, ymm15, 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
L806:
//       0xe10: PUSH2 0x30aa
//     0xe13: Jump
vmovaps qword ptr [rbp+64], ymm0
vmovd xmm0, dword ptr [ROD+2012]
vmovaps qword ptr [rbp+32], ymm0
add qword ptr [rsp+48], 3
add rbp, 96
jmp B30aa
//   0xe14:
Be14:
cmp qword ptr [rsp+48], 2
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 31
jl Error
//       0xe15: SWAP1
//       0xe16: DUP2
//       0xe17: PUSH1 0xf
//       0xe19: SIGNEXTEND
mov r12, qword ptr [rbp-32]
mov r13, qword ptr [rbp-24]
mov r14, r13
sar r14, 63
mov r15, r14
//       0xe1a: SUB
sub r12, qword ptr [rbp-64]
sbb r13, qword ptr [rbp-56]
sbb r14, qword ptr [rbp-48]
sbb r15, qword ptr [rbp-40]
//       0xe1b: PUSH2 0xe31
//     0xe1e: JumpI 156
or r13, r12
or r14, r15
or r13, r14
je L809
vmovaps ymm0, qword ptr [rbp-32]
vmovaps qword ptr [rbp-64], ymm0
add qword ptr [rsp+48], -1
add rbp, -32
jmp Be31
L809:
//   0xe1f:
cmp qword ptr [rsp+48], 3
jb Error
sub qword ptr [rbx+16], 38
//       0xe1f: PUSH2 0xe2f
//       0xe22: SWAP2
//       0xe23: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0xe24: SWAP2
//       0xe25: PUSH0
//       0xe26: SUB
xor r8d, r8d
xor r9d, r9d
xor r10d, r10d
xor r11d, r11d
sub r8, qword ptr [rbp-32]
sbb r9, qword ptr [rbp-24]
sbb r10, qword ptr [rbp-16]
sbb r11, qword ptr [rbp-8]
//       0xe27: PUSH1 0xf
//       0xe29: SIGNEXTEND
mov r10, r9
sar r10, 63
mov r11, r10
//       0xe2a: SWAP1
//       0xe2b: PUSH2 0x30f0
//     0xe2e: Jump
vmovaps ymm0, qword ptr [rbp-96]
vmovaps qword ptr [rbp], ymm0
vmovd xmm0, dword ptr [ROD+2016]
vmovaps qword ptr [rbp-96], ymm0
mov qword ptr [rbp-32], r8
mov qword ptr [rbp-24], r9
mov qword ptr [rbp-16], r10
mov qword ptr [rbp-8], r11
mov qword ptr [rbp-64], r12
mov qword ptr [rbp-56], r13
mov qword ptr [rbp-48], r14
mov qword ptr [rbp-40], r15
add qword ptr [rsp+48], 1
add rbp, 32
jmp B30f0
//   0xe2f:
Be2f:
sub qword ptr [rbx+16], 1
jl Error
//     0xe30: Stop
mov qword ptr [rbx+256], 0
jmp ContractEpilogue
//   0xe31:
Be31:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 14
jl Error
//       0xe32: PUSH32 0xbda73abf00000000000000000000000000000000000000000000000000000000
//       0xe53: PUSH0
//       0xe54: MSTORE
cmp dword ptr [rbx+264], 32
jae L810
mov rdi, 32
call qword ptr [ROD]
L810:
mov rax, qword ptr [rbx+272]
vmovd xmm0, dword ptr [ROD+2020]
vmovups qword ptr [rax], ymm0
//       0xe55: PUSH1 0x4
//       0xe57: PUSH0
//     0xe58: Revert
mov qword ptr [rbx+256], 1
vpxor ymm0, ymm0, ymm0
vmovups qword ptr [rbx+192], ymm0
vmovd xmm1, dword ptr [ROD+1540]
vmovups qword ptr [rbx+224], ymm1
jmp ContractEpilogue
