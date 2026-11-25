//   0x4ffc:
B4ffc:
cmp qword ptr [rsp+48], 8
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 23
jl Error
//       0x4ffd: DUP8
//       0x4ffe: DUP8
//       0x4fff: GT
mov r15, qword ptr [rbp-256]
mov r12, qword ptr [rbp-248]
mov r13, qword ptr [rbp-240]
mov r14, qword ptr [rbp-232]
cmp r15, qword ptr [rbp-224]
sbb r12, qword ptr [rbp-216]
sbb r13, qword ptr [rbp-208]
sbb r14, qword ptr [rbp-200]
//       0x5000: PUSH2 0x503a
//     0x5003: JumpI 784
jb B503a
//   0x5004:
cmp qword ptr [rsp+48], 1018
ja Error
sub qword ptr [rbx+16], 38
//       0x5004: PUSH2 0x5035
//       0x5007: PUSH2 0x5030
//       0x500a: PUSH2 0x5028
//       0x500d: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x501e: DUP5
//       0x501f: AND
vpcmpeqd xmm0, xmm0, xmm0
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0x5020: DUP11
//       0x5021: PUSH1 0x60
//       0x5023: SHL
mov r14, qword ptr [rbp-208]
mov r13, qword ptr [rbp-216]
mov r12, qword ptr [rbp-224]
xor r15d, r15d
shld r14, r13, 32
shld r13, r12, 32
shl r12, 32
//       0x5024: PUSH2 0x4922
//     0x5027: Jump
mov qword ptr [rbp+128], r15
mov qword ptr [rbp+136], r12
mov qword ptr [rbp+144], r13
mov qword ptr [rbp+152], r14
vmovaps qword ptr [rbp+96], ymm0
vmovd xmm0, dword ptr [ROD+5424]
vmovaps qword ptr [rbp+64], ymm0
vmovd xmm0, dword ptr [ROD+5428]
vmovaps qword ptr [rbp+32], ymm0
vmovd xmm0, dword ptr [ROD+5432]
vmovaps qword ptr [rbp], ymm0
add qword ptr [rsp+48], 5
add rbp, 160
jmp B4922
//   0x5028:
B5028:
cmp qword ptr [rsp+48], 11
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 21
jl Error
//       0x5029: DUP11
//       0x502a: DUP6
//       0x502b: AND
vmovaps ymm0, qword ptr [rbp-160]
vpand ymm1, ymm0, qword ptr [rbp-352]
//       0x502c: PUSH2 0x2ffa
//     0x502f: Jump
vmovaps qword ptr [rbp], ymm1
add qword ptr [rsp+48], 1
add rbp, 32
jmp B2ffa
//   0x5030:
B5030:
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 12
jl Error
//       0x5031: PUSH2 0x5d9b
//     0x5034: Jump
jmp B5d9b
//   0x5035:
B5035:
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 12
jl Error
//       0x5036: PUSH2 0x4ff0
//     0x5039: Jump
jmp B4ff0
//   0x503a:
B503a:
cmp qword ptr [rsp+48], 7
jb Error
cmp qword ptr [rsp+48], 1018
ja Error
sub qword ptr [rbx+16], 33
jl Error
//       0x503b: PUSH2 0x5035
//       0x503e: PUSH2 0x5030
//       0x5041: PUSH2 0x505c
//       0x5044: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x5055: DUP5
//       0x5056: AND
vpcmpeqd xmm0, xmm0, xmm0
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0x5057: DUP11
//       0x5058: PUSH2 0x588a
//     0x505b: Jump
vmovaps qword ptr [rbp+96], ymm0
vmovd xmm0, dword ptr [ROD+5436]
vmovaps qword ptr [rbp+64], ymm0
vmovd xmm0, dword ptr [ROD+5428]
vmovaps qword ptr [rbp+32], ymm0
vmovd xmm0, dword ptr [ROD+5432]
vmovaps qword ptr [rbp], ymm0
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp+128], ymm0
add qword ptr [rsp+48], 5
add rbp, 160
jmp B588a
//   0x505c:
B505c:
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 12
jl Error
//       0x505d: PUSH2 0x5028
//     0x5060: Jump
jmp B5028
//   0x510d:
sub qword ptr [rbx+16], 24
//       0x510d: POP
//       0x510e: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x5123: DUP6
//       0x5124: GT
mov r15, qword ptr [rbp-224]
mov r12, qword ptr [rbp-216]
mov r13, qword ptr [rbp-208]
mov r14, qword ptr [rbp-200]
cmp r13, qword ptr [ROD+5520]
sbb r14, 0
//       0x5125: PUSH2 0x519c
//     0x5128: JumpI 808
jb L1583
vmovaps qword ptr [rbp-128], ymm2
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], -2
add rbp, -64
jmp B519c
L1583:
//   0x5148:
B5148:
cmp qword ptr [rsp+48], 3
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 38
jl Error
//       0x5149: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x515e: DUP4
//       0x515f: AND
vmovaps ymm0, qword ptr [ROD+1152]
vpand ymm0, ymm0, qword ptr [rbp-96]
//       0x5160: SWAP3
//       0x5161: DUP2
//       0x5162: DUP5
//       0x5163: GT
mov r15, qword ptr [rbp-32]
mov r12, qword ptr [rbp-24]
mov r13, qword ptr [rbp-16]
mov r14, qword ptr [rbp-8]
vmovaps qword ptr [rbp], ymm0
cmp r15, qword ptr [rbp]
sbb r12, qword ptr [rbp+8]
sbb r13, qword ptr [rbp+16]
sbb r14, qword ptr [rbp+24]
//       0x5164: ISZERO
//       0x5165: PUSH2 0x518f
//     0x5168: JumpI 810
jb L1584
vmovaps ymm1, qword ptr [rbp-96]
vmovaps qword ptr [rbp], ymm1
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], 1
add rbp, 32
jmp B518f
L1584:
//   0x518f:
B518f:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 15
jl Error
//       0x5190: PUSH4 0x4323a555
//       0x5195: PUSH0
//       0x5196: MSTORE
cmp dword ptr [rbx+264], 32
jae L1585
mov rdi, 32
call qword ptr [ROD]
L1585:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+5536]
vmovups qword ptr [rax], ymm0
//       0x5197: PUSH1 0x4
//       0x5199: PUSH1 0x1c
//     0x519b: Revert
mov qword ptr [rbx+256], 1
vmovd xmm0, dword ptr [ROD+4492]
vmovups qword ptr [rbx+192], ymm0
vmovd xmm1, dword ptr [ROD+1540]
vmovups qword ptr [rbx+224], ymm1
jmp ContractEpilogue
//   0x519c:
B519c:
cmp qword ptr [rsp+48], 5
jb Error
cmp qword ptr [rsp+48], 1018
ja Error
sub qword ptr [rbx+16], 33
jl Error
//       0x519d: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x51ae: DUP5
//       0x51af: AND
vpcmpeqd xmm0, xmm0, xmm0
vpand ymm0, ymm0, qword ptr [rbp-128]
//       0x51b0: PUSH2 0x51c7
//       0x51b3: DUP2
//       0x51b4: PUSH13 0x1000000000000000000000000
//       0x51c2: DUP9
//       0x51c3: PUSH2 0x5943
//     0x51c6: Jump
vmovups xmm1, qword ptr [ROD+5568]
vmovaps qword ptr [rbp+96], ymm1
vmovd xmm1, dword ptr [ROD+5584]
vmovaps qword ptr [rbp+32], ymm1
vmovaps qword ptr [rbp], ymm0
vmovaps qword ptr [rbp+64], ymm0
vmovaps ymm0, qword ptr [rbp-160]
vmovaps qword ptr [rbp+128], ymm0
add qword ptr [rsp+48], 5
add rbp, 160
jmp B5943
//   0x51cf:
cmp qword ptr [rsp+48], 7
jb Error
sub qword ptr [rbx+16], 30
//       0x51cf: PUSH13 0x1000000000000000000000000
//       0x51dd: DUP8
//       0x51de: MULMOD
lea rsi, qword ptr [rbp-224]
lea rdx, qword ptr [ROD+5600]
lea rcx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp-64]
vzeroupper
call qword ptr [ROD+5592]
//       0x51df: ISZERO
mov r15, qword ptr [rbp-64]
mov r12, qword ptr [rbp-56]
mov r13, qword ptr [rbp-48]
mov r14, qword ptr [rbp-40]
or r15, r12
or r13, r14
or r15, r13
//       0x51e0: PUSH2 0x5148
//     0x51e3: JumpI 816
jne L1587
vmovaps ymm0, qword ptr [rbp-32]
vmovaps qword ptr [rbp-64], ymm0
add qword ptr [rsp+48], -1
add rbp, -32
jmp B5148
L1587:
//   0x51e4:
sub qword ptr [rbx+16], 22
//       0x51e4: PUSH1 0x1
//       0x51e6: ADD
mov r15, qword ptr [rbp-32]
mov r12, qword ptr [rbp-24]
mov r13, qword ptr [rbp-16]
mov r14, qword ptr [rbp-8]
add r15, 1
adc r12, 0
adc r13, 0
adc r14, 0
//       0x51e7: DUP1
//       0x51e8: PUSH2 0x5148
//     0x51eb: JumpI 817
mov rax, r15
or rax, r12
or rax, r13
or rax, r14
je L1588
mov qword ptr [rbp-64], r15
mov qword ptr [rbp-56], r12
mov qword ptr [rbp-48], r13
mov qword ptr [rbp-40], r14
add qword ptr [rsp+48], -1
add rbp, -32
jmp B5148
L1588:
