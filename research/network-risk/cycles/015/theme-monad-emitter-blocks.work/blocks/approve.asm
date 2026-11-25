//   0x2518:
B2518:
cmp qword ptr [rsp+48], 4
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 2196
jl Error
//       0x2519: SWAP2
//       0x251a: SWAP3
//       0x251b: SWAP1
//       0x251c: SWAP3
//       0x251d: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x251e: PUSH0
//       0x251f: MSTORE
cmp dword ptr [rbx+264], 32
jae L1099
mov rdi, 32
call qword ptr [ROD]
L1099:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x2520: PUSH1 0x5
//       0x2522: PUSH1 0x20
//       0x2524: MSTORE
cmp dword ptr [rbx+264], 64
jae L1100
mov rdi, 64
call qword ptr [ROD]
L1100:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1408]
vmovups qword ptr [rax+32], ymm0
//       0x2525: PUSH1 0x40
//       0x2527: PUSH0
//       0x2528: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2529: DUP3
//       0x252a: DUP3
//       0x252b: AND
vmovaps ymm0, qword ptr [rbp-96]
vpand ymm1, ymm0, qword ptr [rbp-128]
//       0x252c: PUSH0
//       0x252d: MSTORE
cmp dword ptr [rbx+264], 32
jae L1101
mov rdi, 32
call qword ptr [ROD]
L1101:
mov rax, qword ptr [rbx+272]
vpermq ymm2, ymm1, 27
vpshufb ymm2, ymm2, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm2
//       0x252e: PUSH1 0x20
//       0x2530: MSTORE
cmp dword ptr [rbx+264], 64
jae L1102
mov rdi, 64
call qword ptr [ROD]
L1102:
mov rax, qword ptr [rbx+272]
vpermq ymm1, qword ptr [rbp], 27
vpshufb ymm1, ymm1, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm1
//       0x2531: PUSH1 0x40
//       0x2533: PUSH0
//       0x2534: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2535: DUP5
//       0x2536: PUSH0
//       0x2537: MSTORE
cmp dword ptr [rbx+264], 32
jae L1103
mov rdi, 32
call qword ptr [ROD]
L1103:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-64], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2538: PUSH1 0x20
//       0x253a: MSTORE
cmp dword ptr [rbx+264], 64
jae L1104
mov rdi, 64
call qword ptr [ROD]
L1104:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x253b: DUP3
//       0x253c: PUSH1 0x40
//       0x253e: PUSH0
//       0x253f: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp+32]
vzeroupper
call qword ptr [ROD+1192]
//       0x2540: SSTORE
lea rsi, qword ptr [rbp+32]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 1925
vzeroupper
call qword ptr [ROD+1344]
//       0x2541: PUSH1 0x40
//       0x2543: MLOAD
cmp dword ptr [rbx+264], 96
jae L1105
mov rdi, 96
call qword ptr [ROD]
L1105:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x2544: SWAP3
//       0x2545: DUP4
//       0x2546: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1106
call qword ptr [ROD]
L1106:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-32], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2547: AND
vmovaps ymm0, qword ptr [rbp-96]
vpand ymm0, ymm0, qword ptr [rbp-128]
//       0x2548: SWAP1
//       0x2549: PUSH32 0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7
//       0x256a: PUSH1 0x20
//       0x256c: CALLER
movbe r8d, dword ptr [rbx+60]
movbe r11, qword ptr [rbx+64]
movbe r10, qword ptr [rbx+72]
xor r9d, r9d
//       0x256d: SWAP3
//       0x256e: LOG4
mov qword ptr [rbp-128], r10
mov qword ptr [rbp-120], r11
mov qword ptr [rbp-112], r8
mov qword ptr [rbp-104], r9
vmovaps qword ptr [rbp-96], ymm0
mov qword ptr [rbp-32], r12
mov qword ptr [rbp-24], r13
mov qword ptr [rbp-16], r14
mov qword ptr [rbp-8], r15
lea rsi, qword ptr [rbp-32]
lea rdx, qword ptr [ROD+3072]
lea rcx, qword ptr [ROD+3328]
lea r8, qword ptr [rbp-128]
lea r9, qword ptr [rbp-96]
lea rax, qword ptr [rbp-64]
mov qword ptr [rsp], rax
mov rdi, rbx
vzeroupper
call qword ptr [ROD+1360]
//       0x256f: PUSH1 0x20
//       0x2571: PUSH1 0x40
//       0x2573: MLOAD
cmp dword ptr [rbx+264], 96
jae L1107
mov rdi, 96
call qword ptr [ROD]
L1107:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x2574: PUSH1 0x1
//       0x2576: DUP2
//       0x2577: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1108
call qword ptr [ROD]
L1108:
add rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1376]
vmovups qword ptr [rax], ymm0
//     0x2578: Return
mov qword ptr [rbx+256], 0
mov qword ptr [rbx+192], r12
mov qword ptr [rbx+200], r13
mov qword ptr [rbx+208], r14
mov qword ptr [rbx+216], r15
vmovd xmm0, dword ptr [ROD+1368]
vmovups qword ptr [rbx+224], ymm0
jmp ContractEpilogue
