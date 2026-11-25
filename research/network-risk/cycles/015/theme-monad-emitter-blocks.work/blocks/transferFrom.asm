//   0x1c5:
B1c5:
cmp qword ptr [rsp+48], 2
jb Error
cmp qword ptr [rsp+48], 1016
ja Error
sub qword ptr [rbx+16], 67
jl Error
//       0x1c6: SWAP1
//       0x1c7: PUSH1 0x44
//       0x1c9: CALLDATALOAD
vpxor ymm0, ymm0, ymm0
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
add rdi, 68
sub rsi, 68
cmp rsi, 32
jl L652
vmovups ymm15, byte ptr [rdi]
L653:
vpermq ymm0, ymm15, 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
L651:
//       0x1ca: SWAP2
//       0x1cb: PUSH32 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859
//       0x1ec: PUSH2 0x279
//       0x1ef: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x204: DUP1
//       0x205: PUSH1 0x64
//       0x207: CALLDATALOAD
vpxor ymm1, ymm1, ymm1
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
add rdi, 100
sub rsi, 100
cmp rsi, 32
jl L655
vmovups ymm15, byte ptr [rdi]
L656:
vpermq ymm1, ymm15, 27
vpshufb ymm1, ymm1, qword ptr [ROD+64]
L654:
//       0x208: SWAP6
//       0x209: AND
vmovaps ymm2, qword ptr [ROD+1152]
vpand ymm3, ymm2, qword ptr [rbp-64]
//       0x20a: SWAP4
//       0x20b: DUP5
//       0x20c: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x20d: EQ
vmovaps qword ptr [rbp], ymm3
xor r12, qword ptr [rbp]
xor r13, qword ptr [rbp+8]
xor r14, qword ptr [rbp+16]
xor r15, qword ptr [rbp+24]
or r12, r13
or r14, r15
or r12, r14
//       0x20e: ISZERO
//       0x20f: DUP1
//       0x210: PUSH2 0x30d
//     0x213: JumpI 41
setne al
movzx eax, al
vmovd xmm4, eax
vmovaps qword ptr [rbp+160], ymm4
vmovaps ymm4, qword ptr [rbp-32]
vmovaps qword ptr [rbp+128], ymm4
vmovaps qword ptr [rbp-32], ymm1
vmovaps qword ptr [rbp+96], ymm2
vmovd xmm2, dword ptr [ROD+1184]
vmovaps qword ptr [rbp+64], ymm2
vmovaps ymm2, qword ptr [ROD+1216]
vmovaps qword ptr [rbp+32], ymm2
vmovaps qword ptr [rbp-64], ymm0
mov rax, qword ptr [rsp+48]
lea rax, [rax+6]
lea rbp, [rbp+192]
mov qword ptr [rsp+48], rax
jne B30d
//   0x214:
B214:
cmp qword ptr [rsp+48], 1
jb Error
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 14
jl Error
//       0x215: PUSH2 0x287
//     0x218: JumpI 42
vmovaps ymm0, qword ptr [rbp-32]
vptest ymm0, ymm0
mov rax, qword ptr [rsp+48]
lea rax, [rax-1]
lea rbp, [rbp-32]
mov qword ptr [rsp+48], rax
jne B287
//   0x219:
B219:
cmp qword ptr [rsp+48], 7
jb Error
cmp qword ptr [rsp+48], 1019
ja Error
sub qword ptr [rbx+16], 222
jl Error
//       0x21a: DUP5
//       0x21b: PUSH0
//       0x21c: MSTORE
cmp dword ptr [rbx+264], 32
jae L657
mov rdi, 32
call qword ptr [ROD]
L657:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-160], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x21d: PUSH1 0x4
//       0x21f: PUSH1 0x20
//       0x221: MSTORE
cmp dword ptr [rbx+264], 64
jae L658
mov rdi, 64
call qword ptr [ROD]
L658:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1248]
vmovups qword ptr [rax+32], ymm0
//       0x222: PUSH1 0x40
//       0x224: PUSH0
//       0x225: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x226: DUP8
//       0x227: PUSH0
//       0x228: MSTORE
cmp dword ptr [rbx+264], 32
jae L659
mov rdi, 32
call qword ptr [ROD]
L659:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-224], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x229: PUSH1 0x20
//       0x22b: MSTORE
cmp dword ptr [rbx+264], 64
jae L660
mov rdi, 64
call qword ptr [ROD]
L660:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x22c: PUSH1 0x40
//       0x22e: PUSH0
//       0x22f: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x230: PUSH2 0x23a
//       0x233: DUP8
//       0x234: DUP3
//       0x235: SLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp+96]
vzeroupper
call qword ptr [ROD+1200]
//       0x236: PUSH2 0x2fed
//     0x239: Jump
vmovd xmm0, dword ptr [ROD+1208]
vmovaps qword ptr [rbp+32], ymm0
vmovaps ymm0, qword ptr [rbp-192]
vmovaps qword ptr [rbp+64], ymm0
add qword ptr [rsp+48], 4
add rbp, 128
jmp B2fed
//   0x23a:
B23a:
cmp qword ptr [rsp+48], 9
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 331
jl Error
//       0x23b: SWAP1
//       0x23c: SSTORE
lea rsi, qword ptr [rbp-64]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 227
vzeroupper
call qword ptr [ROD+1344]
//       0x23d: AND
vmovaps ymm0, qword ptr [rbp-96]
vpand ymm0, ymm0, qword ptr [rbp-128]
//       0x23e: SWAP4
//       0x23f: DUP5
//       0x240: PUSH0
//       0x241: MSTORE
cmp dword ptr [rbx+264], 32
jae L661
mov rdi, 32
call qword ptr [ROD]
L661:
mov rax, qword ptr [rbx+272]
vpermq ymm1, ymm0, 27
vpshufb ymm1, ymm1, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm1
//       0x242: PUSH1 0x4
//       0x244: PUSH1 0x20
//       0x246: MSTORE
cmp dword ptr [rbx+264], 64
jae L662
mov rdi, 64
call qword ptr [ROD]
L662:
mov rax, qword ptr [rbx+272]
vmovaps ymm1, qword ptr [ROD+1248]
vmovups qword ptr [rax+32], ymm1
//       0x247: PUSH1 0x40
//       0x249: PUSH0
//       0x24a: KECCAK256
vmovaps qword ptr [rbp-128], ymm0
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp-96]
vzeroupper
call qword ptr [ROD+1192]
//       0x24b: DUP7
//       0x24c: PUSH0
//       0x24d: MSTORE
cmp dword ptr [rbx+264], 32
jae L663
mov rdi, 32
call qword ptr [ROD]
L663:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-288], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x24e: PUSH1 0x20
//       0x250: MSTORE
cmp dword ptr [rbx+264], 64
jae L664
mov rdi, 64
call qword ptr [ROD]
L664:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-96], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x251: PUSH1 0x40
//       0x253: PUSH0
//       0x254: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp-96]
vzeroupper
call qword ptr [ROD+1192]
//       0x255: PUSH2 0x25f
//       0x258: DUP3
//       0x259: DUP3
//       0x25a: SLOAD
lea rdx, qword ptr [rbp-96]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x25b: PUSH2 0x2ffa
//     0x25e: Jump
vmovd xmm0, dword ptr [ROD+1352]
vmovaps qword ptr [rbp-64], ymm0
vmovaps ymm0, qword ptr [rbp-256]
vmovaps ymm1, qword ptr [rbp-128]
vmovaps qword ptr [rbp-128], ymm0
vmovaps qword ptr [rbp-32], ymm0
vmovaps qword ptr [rbp-256], ymm1
add qword ptr [rsp+48], 1
add rbp, 32
jmp B2ffa
//   0x25f:
B25f:
cmp qword ptr [rsp+48], 4
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 171
jl Error
//       0x260: SWAP1
//       0x261: SSTORE
lea rsi, qword ptr [rbp-64]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 67
vzeroupper
call qword ptr [ROD+1344]
//       0x262: PUSH1 0x40
//       0x264: DUP1
//       0x265: MLOAD
cmp dword ptr [rbx+264], 96
jae L665
mov rdi, 96
call qword ptr [ROD]
L665:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x266: CALLER
movbe r10d, dword ptr [rbx+60]
movbe r9, qword ptr [rbx+64]
movbe r8, qword ptr [rbx+72]
xor r11d, r11d
//       0x267: DUP2
//       0x268: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L666
call qword ptr [ROD]
L666:
add rax, qword ptr [rbx+272]
movbe qword ptr [rax], r11
movbe qword ptr [rax+8], r10
movbe qword ptr [rax+16], r9
movbe qword ptr [rax+24], r8
//       0x269: PUSH1 0x20
//       0x26b: DUP2
//       0x26c: ADD
mov r8, r12
mov r9, r13
mov r10, r14
mov r11, r15
add r12, 32
adc r13, 0
adc r14, 0
adc r15, 0
//       0x26d: SWAP3
//       0x26e: SWAP1
//       0x26f: SWAP3
//       0x270: MSTORE
mov rax, r12
and r12, -268435456
or r15, r14
or r13, r12
or r15, r13
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L667
call qword ptr [ROD]
L667:
add rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-96], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x271: SWAP1
//       0x272: SWAP2
//       0x273: DUP3
//       0x274: SWAP2
//       0x275: DUP3
//       0x276: ADD
mov r12, r8
mov r13, r9
mov r14, r10
mov r15, r11
add r8, 64
adc r9, 0
adc r10, 0
adc r11, 0
//       0x277: SWAP1
//     0x278: Jump
mov rcx, qword ptr [rbp-128]
mov rsi, qword ptr [rbp-120]
mov rdx, qword ptr [rbp-112]
mov rdi, qword ptr [rbp-104]
mov qword ptr [rbp-64], r8
mov qword ptr [rbp-56], r9
mov qword ptr [rbp-48], r10
mov qword ptr [rbp-40], r11
vmovq xmm0, r12
vmovq xmm1, r14
vpinsrq xmm0, xmm0, r13, 1
vpinsrq xmm1, xmm1, r15, 1
vinserti128 ymm0, ymm0, xmm1, 1
vmovaps qword ptr [rbp-128], ymm0
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], -1
add rbp, -32
cmp rcx, 24009
jnb Error
or rsi, rdx
or rsi, rdi
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+rcx*4]
add rax, rcx
jmp rax
//   0x279:
B279:
cmp qword ptr [rsp+48], 7
jb Error
sub qword ptr [rbx+16], 1900
jl Error
//       0x27a: SUB
mov r12, qword ptr [rbp-32]
mov r13, qword ptr [rbp-24]
mov r14, qword ptr [rbp-16]
mov r15, qword ptr [rbp-8]
sub r12, qword ptr [rbp-64]
sbb r13, qword ptr [rbp-56]
sbb r14, qword ptr [rbp-48]
sbb r15, qword ptr [rbp-40]
//       0x27b: SWAP1
//       0x27c: LOG4
mov qword ptr [rbp-64], r12
mov qword ptr [rbp-56], r13
mov qword ptr [rbp-48], r14
mov qword ptr [rbp-40], r15
lea rsi, qword ptr [rbp-96]
lea rdx, qword ptr [rbp-64]
lea rcx, qword ptr [rbp-128]
lea r8, qword ptr [rbp-160]
lea r9, qword ptr [rbp-192]
lea rax, qword ptr [rbp-224]
mov qword ptr [rsp], rax
mov rdi, rbx
vzeroupper
call qword ptr [ROD+1360]
//       0x27d: PUSH1 0x20
//       0x27f: PUSH1 0x40
//       0x281: MLOAD
cmp dword ptr [rbx+264], 96
jae L669
mov rdi, 96
call qword ptr [ROD]
L669:
mov rax, qword ptr [rbx+272]
movbe r15, qword ptr [rax+64]
movbe r14, qword ptr [rax+72]
movbe r13, qword ptr [rax+80]
movbe r12, qword ptr [rax+88]
//       0x282: PUSH1 0x1
//       0x284: DUP2
//       0x285: MSTORE
mov rax, r12
and rax, -268435456
or rax, r13
or rax, r14
or rax, r15
jnz Error
mov rax, r12
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L670
call qword ptr [ROD]
L670:
add rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1376]
vmovups qword ptr [rax], ymm0
//     0x286: Return
mov qword ptr [rbx+256], 0
mov qword ptr [rbx+192], r12
mov qword ptr [rbx+200], r13
mov qword ptr [rbx+208], r14
mov qword ptr [rbx+216], r15
vmovd xmm0, dword ptr [ROD+1368]
vmovups qword ptr [rbx+224], ymm0
jmp ContractEpilogue
//   0x287:
B287:
cmp qword ptr [rsp+48], 7
jb Error
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 281
jl Error
//       0x288: DUP5
//       0x289: PUSH0
//       0x28a: MSTORE
cmp dword ptr [rbx+264], 32
jae L671
mov rdi, 32
call qword ptr [ROD]
L671:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-160], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x28b: PUSH1 0x5
//       0x28d: PUSH1 0x20
//       0x28f: MSTORE
cmp dword ptr [rbx+264], 64
jae L672
mov rdi, 64
call qword ptr [ROD]
L672:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1408]
vmovups qword ptr [rax+32], ymm0
//       0x290: PUSH1 0x40
//       0x292: PUSH0
//       0x293: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x294: DUP3
//       0x295: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x296: AND
and r12, qword ptr [rbp-64]
and r13, qword ptr [rbp-56]
and r14, qword ptr [rbp-48]
and r15, qword ptr [rbp-40]
//       0x297: PUSH0
//       0x298: MSTORE
cmp dword ptr [rbx+264], 32
jae L673
mov rdi, 32
call qword ptr [ROD]
L673:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x299: PUSH1 0x20
//       0x29b: MSTORE
cmp dword ptr [rbx+264], 64
jae L674
mov rdi, 64
call qword ptr [ROD]
L674:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x29c: PUSH1 0x40
//       0x29e: PUSH0
//       0x29f: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2a0: DUP8
//       0x2a1: PUSH0
//       0x2a2: MSTORE
cmp dword ptr [rbx+264], 32
jae L675
mov rdi, 32
call qword ptr [ROD]
L675:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-224], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2a3: PUSH1 0x20
//       0x2a5: MSTORE
cmp dword ptr [rbx+264], 64
jae L676
mov rdi, 64
call qword ptr [ROD]
L676:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x2a6: PUSH1 0x40
//       0x2a8: PUSH0
//       0x2a9: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2aa: SLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x2ab: DUP7
//       0x2ac: PUSH32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
//       0x2cd: DUP3
//       0x2ce: SUB
mov r12, qword ptr [rbp]
mov r13, qword ptr [rbp+8]
mov r14, qword ptr [rbp+16]
mov r15, qword ptr [rbp+24]
sub r12, -1
sbb r13, -1
sbb r14, -1
sbb r15, -1
//       0x2cf: PUSH2 0x2da
//     0x2d2: JumpI 47
or r13, r12
or r14, r15
or r13, r14
vmovaps ymm0, qword ptr [rbp-192]
vmovaps qword ptr [rbp+32], ymm0
mov rax, qword ptr [rsp+48]
lea rax, [rax+2]
lea rbp, [rbp+64]
mov qword ptr [rsp+48], rax
jne B2da
//   0x2d3:
B2d3:
cmp qword ptr [rsp+48], 2
jb Error
sub qword ptr [rbx+16], 16
jl Error
//       0x2d4: POP
//       0x2d5: POP
//       0x2d6: PUSH2 0x219
//     0x2d9: Jump
add qword ptr [rsp+48], -2
add rbp, -64
jmp B219
//   0x2da:
B2da:
cmp qword ptr [rsp+48], 2
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 18
jl Error
//       0x2db: PUSH2 0x2e3
//       0x2de: SWAP2
//       0x2df: PUSH2 0x2fed
//     0x2e2: Jump
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp], ymm0
vmovd xmm0, dword ptr [ROD+1372]
vmovaps qword ptr [rbp-64], ymm0
add qword ptr [rsp+48], 1
add rbp, 32
jmp B2fed
//   0x2e3:
B2e3:
cmp qword ptr [rsp+48], 8
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 272
jl Error
//       0x2e4: DUP6
//       0x2e5: PUSH0
//       0x2e6: MSTORE
cmp dword ptr [rbx+264], 32
jae L677
mov rdi, 32
call qword ptr [ROD]
L677:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-192], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2e7: PUSH1 0x5
//       0x2e9: PUSH1 0x20
//       0x2eb: MSTORE
cmp dword ptr [rbx+264], 64
jae L678
mov rdi, 64
call qword ptr [ROD]
L678:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1408]
vmovups qword ptr [rax+32], ymm0
//       0x2ec: PUSH1 0x40
//       0x2ee: PUSH0
//       0x2ef: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2f0: DUP4
//       0x2f1: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x2f2: AND
and r12, qword ptr [rbp-96]
and r13, qword ptr [rbp-88]
and r14, qword ptr [rbp-80]
and r15, qword ptr [rbp-72]
//       0x2f3: PUSH0
//       0x2f4: MSTORE
cmp dword ptr [rbx+264], 32
jae L679
mov rdi, 32
call qword ptr [ROD]
L679:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x2f5: PUSH1 0x20
//       0x2f7: MSTORE
cmp dword ptr [rbx+264], 64
jae L680
mov rdi, 64
call qword ptr [ROD]
L680:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x2f8: PUSH1 0x40
//       0x2fa: PUSH0
//       0x2fb: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x2fc: DUP9
//       0x2fd: PUSH0
//       0x2fe: MSTORE
cmp dword ptr [rbx+264], 32
jae L681
mov rdi, 32
call qword ptr [ROD]
L681:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-256], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x2ff: PUSH1 0x20
//       0x301: MSTORE
cmp dword ptr [rbx+264], 64
jae L682
mov rdi, 64
call qword ptr [ROD]
L682:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x302: PUSH1 0x40
//       0x304: PUSH0
//       0x305: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x306: SSTORE
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 16
vzeroupper
call qword ptr [ROD+1344]
//       0x307: PUSH0
//       0x308: DUP7
//       0x309: PUSH2 0x2d3
//     0x30c: Jump
vpxor ymm0, ymm0, ymm0
vmovaps qword ptr [rbp-32], ymm0
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp], ymm0
add qword ptr [rsp+48], 1
add rbp, 32
jmp B2d3
//   0x30d:
B30d:
cmp qword ptr [rsp+48], 6
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 229
jl Error
//       0x30e: POP
//       0x30f: DUP5
//       0x310: PUSH0
//       0x311: MSTORE
cmp dword ptr [rbx+264], 32
jae L683
mov rdi, 32
call qword ptr [ROD]
L683:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-192], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax], ymm0
//       0x312: PUSH1 0x3
//       0x314: PUSH1 0x20
//       0x316: MSTORE
cmp dword ptr [rbx+264], 64
jae L684
mov rdi, 64
call qword ptr [ROD]
L684:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+1440]
vmovups qword ptr [rax+32], ymm0
//       0x317: PUSH1 0x40
//       0x319: PUSH0
//       0x31a: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+1192]
//       0x31b: DUP3
//       0x31c: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x31d: AND
and r12, qword ptr [rbp-96]
and r13, qword ptr [rbp-88]
and r14, qword ptr [rbp-80]
and r15, qword ptr [rbp-72]
//       0x31e: PUSH0
//       0x31f: MSTORE
cmp dword ptr [rbx+264], 32
jae L685
mov rdi, 32
call qword ptr [ROD]
L685:
mov rax, qword ptr [rbx+272]
movbe qword ptr [rax], r15
movbe qword ptr [rax+8], r14
movbe qword ptr [rax+16], r13
movbe qword ptr [rax+24], r12
//       0x320: PUSH1 0x20
//       0x322: MSTORE
cmp dword ptr [rbx+264], 64
jae L686
mov rdi, 64
call qword ptr [ROD]
L686:
mov rax, qword ptr [rbx+272]
vpermq ymm0, qword ptr [rbp-32], 27
vpshufb ymm0, ymm0, qword ptr [ROD+64]
vmovups qword ptr [rax+32], ymm0
//       0x323: PUSH1 0xff
//       0x325: PUSH1 0x40
//       0x327: PUSH0
//       0x328: KECCAK256
lea rdx, qword ptr [ROD+1280]
lea rcx, qword ptr [ROD+1312]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1192]
//       0x329: SLOAD
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x32a: AND
vmovd xmm0, dword ptr [ROD+1472]
vpand ymm0, ymm0, qword ptr [rbp]
//       0x32b: ISZERO
vptest ymm0, ymm0
//       0x32c: PUSH2 0x214
//     0x32f: Jump
sete al
movzx eax, al
vmovd xmm0, eax
vmovaps qword ptr [rbp-32], ymm0
jmp B214
