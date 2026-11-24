{
let var_amountToProtocol_1 :=  0
var_amountToProtocol := var_amountToProtocol_1
let memPtr := mload(64)
finalize_allocation(memPtr, 96)
mstore(memPtr, 0)
let _1 := add(memPtr, 32)
mstore(_1, 0)
let _2 := add(memPtr, 64)
mstore(_2, 0)
let var_result_mpos := memPtr
var_result_4424_mpos := var_result_mpos
let _3 := sload( var_self_4410_slot)
let _4 := add(var_params_4413_mpos,  64)
let _5 := mload( _4)
let _6 := iszero(_5)
let expr :=  0
let expr_1 := expr
switch  iszero(_6)
case  0 {
let _7 := 0x0c
let _8 := 0xff
let value := and( _7,  _8)
let _9 := 184
let _10 := shr(_9,  _3)
let _11 := 16777215
let _12 := and(_11, _10)
let bits := and(value, _8)
let _13 := and(_12, _11)
let _14 := shr(bits, _13)
let result := and(_14, _11)
let _15 := 0xffff
let _16 := and(result, _11)
let converted := and(_16, _15)
let expr_2 := converted
expr_1 := expr_2
}
default {
let _17 := 0x0fff
let _18 := 0xffffff
let cleaned := and( _17,  _18)
let _19 := 184
let _20 := shr(_19,  _3)
let _21 := and(_18, _20)
let _22 := and( _21,  cleaned)
let _23 := 0xffff
let _24 := and(_22, _18)
let converted_1 := and(_24, _23)
let expr_3 := converted_1
expr_1 := expr_3
}
let expr_4 := expr_1
let _25 := mload( var_params_4413_mpos)
let var_amountSpecifiedRemaining := _25
let var_amountSpecifiedRemaining_1 := var_amountSpecifiedRemaining
let var_amountCalculated :=  0
let var_amountCalculated_1 := var_amountCalculated
mstore(memPtr, and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _26 := shr(160,  _3)
let expr_5 :=  signextend(2, _26)
let _27 := signextend( 2,  expr_5)
mstore(_1, _27)
let _28 := 3
let _29 := sload( add(var_self_4410_slot, _28))
let cleaned_1 := and(_29, 0xffffffffffffffffffffffffffffffff)
let _30 := and(cleaned_1, 0xffffffffffffffffffffffffffffffff)
mstore(_2, _30)
let _31 := mload( add(var_params_4413_mpos, 128))
let cleaned_2 := and(_31, 0xffffff)
let _32 := 0x400000
let _33 := and( _32,  0xffffff)
let expr_6 := and(cleaned_2,  _33)
let _34 := and(0, 0xffffff)
let _35 := and( expr_6,  0xffffff)
let _36 := eq( _35, _34)
let var :=  iszero(_36)
let expr_7 :=  0
let expr_8 := expr_7
switch var
case 0 {
let _37 := 208
let _38 := shr(_37,  _3)
let expr_9 :=  and( 0xffffff,  _38)
let expr_10 := expr_9
expr_8 := expr_10
}
default {
let _39 := mload( add(var_params_4413_mpos, 128))
let cleaned_3 := and(_39, 0xffffff)
let _40 := 0xbfffff
let ret :=  and( _40,  0xffffff)
let expr_11 :=  and( cleaned_3,  ret)
fun_validate(expr_11)
let expr_12 := expr_11
expr_8 := expr_12
}
let expr_13 := expr_8
let expr_14 := eq( and( expr_4,  0xffff), 0)
let expr_15 :=  0
let expr_16 := expr_15
switch expr_14
case 0 {
let _41 := and(and( expr_4,  0xffff), 0xffff)
let _42 := 0xfff
let var_self := and(_41, _42)
let var_lpFee := and(expr_13,  0xffffff)
let usr$numerator := mul(var_self, var_lpFee)
let _43 := 1000000
let _44 := div(usr$numerator, _43)
let _45 := add(var_self, var_lpFee)
let var_swapFee_1 := sub(_45, _44)
let expr_17 := var_swapFee_1
expr_16 := expr_17
}
default {
let expr_18 := expr_13
expr_16 := expr_18
}
let var_swapFee_2 := expr_16
var_swapFee := var_swapFee_2
let _46 := and( expr_16,  0xffffff)
let _47 := lt( _46,  0x0f4240)
let _48 := iszero(_47)
if  _48
{
let _49 := mload( var_params_4413_mpos)
let _50 := sgt(_49,  0)
if  _50
{
let _51 := 0x9620624600000000000000000000000000000000000000000000000000000000
mstore( 0,  _51)
let _52 := 0x04
revert( 0,  _52)
}
}
let _53 := mload( var_params_4413_mpos)
let _54 := eq(_53,  0)
if  _54
{
let var_swapDelta_1 :=  0
var_swapDelta := var_swapDelta_1
let var_amountToProtocol_2 :=  0
var_amountToProtocol := var_amountToProtocol_2
let var_swapFee_3 :=  expr_16
var_swapFee := var_swapFee_3
let var_result_mpos_1 := memPtr
var_result_4424_mpos := var_result_mpos_1
leave
}
switch  iszero(_6)
case  0 {
let _55 := mload( add(var_params_4413_mpos,  96))
let cleaned_4 := and(_55,  1461501637330902918203684832716283019655932542975)
let _56 := and( cleaned_4,  1461501637330902918203684832716283019655932542975)
let _57 := gt( _56, and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _58 := iszero(_57)
if  _58
{
let _59 := mload( add(var_params_4413_mpos,  96))
let cleaned_5 := and(_59,  1461501637330902918203684832716283019655932542975)
let _60 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
let usr$fmp := mload( 64)
mstore(usr$fmp,  _60)
let _61 := 0x04
let _62 := add(usr$fmp, _61)
mstore(_62,  and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _63 := and(cleaned_5,  1461501637330902918203684832716283019655932542975)
let _64 := 0x24
let _65 := add(usr$fmp, _64)
mstore(_65, _63)
let _66 := 0x44
revert(usr$fmp, _66)
}
let _67 := mload( add(var_params_4413_mpos,  96))
let cleaned_6 := and(_67,  1461501637330902918203684832716283019655932542975)
let _68 := 0xfffd8963efd1fc6a506488495d951d5263988d26
let _69 := and( _68,  1461501637330902918203684832716283019655932542975)
let _70 := and(_69,  1461501637330902918203684832716283019655932542975)
let _71 := and( cleaned_6,  1461501637330902918203684832716283019655932542975)
let _72 := lt( _71, _70)
let _73 := iszero(_72)
if  _73
{
let _74 := mload( add(var_params_4413_mpos,  96))
let cleaned_7 := and(_74,  1461501637330902918203684832716283019655932542975)
let _75 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
mstore( 0,  _75)
let _76 := and(cleaned_7,  1461501637330902918203684832716283019655932542975)
let _77 := 0x04
mstore(_77, _76)
let _78 := 0x24
revert( 0,  _78)
}
}
default
{
let _79 := mload( add(var_params_4413_mpos,  96))
let cleaned_8 := and(_79,  1461501637330902918203684832716283019655932542975)
let _80 := and( cleaned_8,  1461501637330902918203684832716283019655932542975)
let _81 := lt( _80, and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _82 := iszero(_81)
if  _82
{
let _83 := mload( add(var_params_4413_mpos,  96))
let cleaned_9 := and(_83,  1461501637330902918203684832716283019655932542975)
let _84 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
let usr$fmp_1 := mload( 64)
mstore(usr$fmp_1,  _84)
let _85 := 0x04
let _86 := add(usr$fmp_1, _85)
mstore(_86,  and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _87 := and(cleaned_9,  1461501637330902918203684832716283019655932542975)
let _88 := 0x24
let _89 := add(usr$fmp_1, _88)
mstore(_89, _87)
let _90 := 0x44
revert(usr$fmp_1, _90)
}
let _91 := mload( add(var_params_4413_mpos,  96))
let cleaned_10 := and(_91,  1461501637330902918203684832716283019655932542975)
let _92 := 0x01000276a3
let _93 := and( _92,  1461501637330902918203684832716283019655932542975)
let _94 := and(_93,  1461501637330902918203684832716283019655932542975)
let _95 := and( cleaned_10,  1461501637330902918203684832716283019655932542975)
let _96 := gt( _95, _94)
let _97 := iszero(_96)
if  _97
{
let _98 := mload( add(var_params_4413_mpos,  96))
let cleaned_11 := and(_98,  1461501637330902918203684832716283019655932542975)
let _99 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
mstore( 0,  _99)
let _100 := and(cleaned_11,  1461501637330902918203684832716283019655932542975)
let _101 := 0x04
mstore(_101, _100)
let _102 := 0x24
revert( 0,  _102)
}
}
let memPtr_1 := mload(64)
finalize_allocation(memPtr_1,  256)
mstore(memPtr_1,  0)
mstore(add(memPtr_1,  32), 0)
mstore(add(memPtr_1,  64), 0)
mstore(add(memPtr_1,  96), 0)
mstore(add(memPtr_1,  128),  0)
mstore(add(memPtr_1,  160),  0)
mstore(add(memPtr_1, 192),  0)
mstore(add(memPtr_1, 224),  0)
let expr_19 :=  0
let expr_20 := expr_19
switch  iszero(_6)
case  0 {
let _103 := add(var_self_4410_slot,  2)
let _104 := sload( _103)
let expr_21 := _104
expr_20 := expr_21
}
default {
let _105 := 1
let _106 := add(var_self_4410_slot, _105)
let _107 := sload( _106)
let expr_22 := _107
expr_20 := expr_22
}
let expr_23 := expr_20
mstore( add(memPtr_1, 224),  expr_23)
let _108 := 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618
let _109 := 0x0d89e8
for { }
0x1
{ }
{
let expr_24 := eq(var_amountSpecifiedRemaining_1,  0)
let expr_25 := expr_24
let expr_26 := expr_25
let _110 := iszero(expr_24)
if _110
{
let _111 := mload( var_result_4424_mpos)
let cleaned_12 := and(_111,  1461501637330902918203684832716283019655932542975)
let _112 := add(var_params_4413_mpos,  96)
let _113 := mload( _112)
let cleaned_13 := and(_113,  1461501637330902918203684832716283019655932542975)
let cleaned_14 := and(cleaned_13,  1461501637330902918203684832716283019655932542975)
let _114 := and( cleaned_12,  1461501637330902918203684832716283019655932542975)
let expr_27 :=  eq( _114,  cleaned_14)
let expr_28 := expr_27
expr_26 := expr_28
}
let expr_29 := expr_26
let _115 := iszero(expr_29)
let _116 := iszero( _115)
let _117 := iszero(_116)
let _118 := iszero( _117)
if _118 { break }
let _119 := mload( var_result_4424_mpos)
let cleaned_15 := and(_119,  1461501637330902918203684832716283019655932542975)
let _120 := and(cleaned_15,  1461501637330902918203684832716283019655932542975)
mstore(memPtr_1, _120)
let _121 := mload( add( var_result_4424_mpos,  32))
let cleaned_16 := signextend( 2,  _121)
let _122 := add(var_params_4413_mpos,  32)
let _123 := mload( _122)
let var_next :=  0
let var_next_1 := var_next
let var_initialized :=  0
let var_initialized_1 := var_initialized
let var_tick := signextend( 2,  cleaned_16)
let var_tickSpacing := signextend( 2,  signextend( 2,  _123))
let _124 := smod(var_tick, var_tickSpacing)
let _125 := slt(_124,  0)
let _126 := sdiv(var_tick, var_tickSpacing)
switch  iszero(_6)
case  0 {
let _127 := add( sub(_126, _125),  0x1)
let _128 := signextend( 2,  signextend( 2,  _127))
let _129 := 8
let bits_1 :=  and( and( signextend( 2,  _127),  0xff), 0xff)
let result_1 :=  shl( bits_1,  0x1)
let diff := sub(result_1,  0x1)
let _130 := not( diff)
let _131 := mapping_index_access_mapping_int16_uint256_of_int16( add(var_self_4410_slot, 5),  sar(_129, _128))
let _132 := sload(_131)
let _133 := eq( and( _132,  _130),  0)
let var_initialized_2 :=  iszero(_133)
var_initialized_1 := var_initialized_2
let expr_30 :=  0
let expr_31 := expr_30
switch  iszero(_133)
case  0 {
let _134 := sub( 0xff, and( signextend( 2,  _127),  0xff))
let _135 := and(_134,  0xff)
let _136 := and(_135,  0xff)
let _137 := and(_136, 0xffffff)
let _138 := and(_137, 0xffffff)
let _139 := signextend( 2,  _138)
let _140 := add(signextend( 2,  _127), _139)
let _141 := signextend( 2,  _140)
let _142 := mul(_141, signextend( 2,  _123))
let expr_32 :=  signextend( 2,  _142)
let expr_33 := expr_32
expr_31 := expr_33
}
default {
let _143 := gt( and( _132,  _130),  0)
let _144 := iszero(_143)
if _144 { revert(0, 0) }
let _145 := sub( 0,  and( _132,  _130))
let var_x := and( and( _132,  _130),  _145)
let _146 := 480
let _147 := 0x8040405543005266443200005020610674053026020000107506200176117077
let _148 := 252
let _149 := 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff
let _150 := mul(var_x, _149)
let _151 := 248
let _152 := shr(_151, _150)
let _153 := and(_152, _148)
let _154 := shl(_153, _147)
let _155 := 247
let _156 := shr(_155, _154)
let var_r := and(_156, _146)
let _157 := 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405
let _158 := 0x1f
let _159 := shr(var_r, var_x)
let _160 := 0xd76453e0
let _161 := div(_160, _159)
let _162 := and(_161, _158)
let _163 := byte(_162, _157)
let var_r_1 := or(var_r, _163)
let _164 := sub(var_r_1,  and( signextend( 2,  _127),  0xff))
let diff_1 := and(_164,  0xff)
let _165 := and(diff_1,  0xff)
let converted_2 := and(_165, 0xffffff)
let _166 := and(converted_2, 0xffffff)
let converted_3 := signextend( 2,  _166)
let _167 := add(signextend( 2,  _127), converted_3)
let sum := signextend( 2,  _167)
let _168 := mul(sum, signextend( 2,  _123))
let product := signextend( 2,  _168)
let expr_34 := product
expr_31 := expr_34
}
let expr_35 := expr_31
let var_next_2 := expr_35
var_next_1 := var_next_2
}
default
{
let _169 := signextend( 2,  sub(_126, _125))
let _170 := 8
let var_wordPos := sar(_170, _169)
let _171 := 0xff
let var_bitPos := and( sub(_126, _125),  _171)
let expr_36 :=  and(_171, _171)
let _172 := and( var_bitPos,  _171)
let _173 := sub( expr_36,  _172)
let _174 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
let result_2 :=  shr( _173,  _174)
let _175 := mapping_index_access_mapping_int16_uint256_of_int16( add(var_self_4410_slot, 5),  var_wordPos)
let _176 := sload(_175)
let expr_37 := and( _176,  result_2)
let _177 := eq(expr_37,  0)
let expr_38 := iszero(_177)
let var_initialized_3 := expr_38
var_initialized_1 := var_initialized_3
let expr_39 :=  0
let expr_40 := expr_39
switch expr_38
case 0 {
let _178 := and(_172, 0xffffff)
let _179 := and(_178, 0xffffff)
let _180 := signextend( 2,  _179)
let _181 := sub( sub(_126, _125),  _180)
let _182 := signextend( 2,  _181)
let _183 := mul(_182, signextend( 2,  _123))
let expr_41 :=  signextend( 2,  _183)
let expr_42 := expr_41
expr_40 := expr_42
}
default {
let _184 := fun_mostSignificantBit(expr_37)
let _185 := sub(var_bitPos, _184)
let diff_2 := and(_185, _171)
let _186 := and(diff_2, _171)
let converted_4 := and(_186, 0xffffff)
let _187 := and(converted_4, 0xffffff)
let converted_5 := signextend( 2,  _187)
let _188 := sub( sub(_126, _125),  converted_5)
let diff_3 :=  signextend( 2,  _188)
let _189 := mul(diff_3, signextend( 2,  _123))
let product_1 := signextend( 2,  _189)
let expr_43 := product_1
expr_40 := expr_43
}
let expr_44 := expr_40
let var_next_3 := expr_44
var_next_1 := var_next_3
}
let var_initialized_4 := var_initialized_1
let var_next_4 := var_next_1
let _190 := iszero(var_initialized_4)
let _191 := iszero(_190)
mstore( add(memPtr_1,  64), _191)
let _192 := signextend( 2,  var_next_4)
mstore( add(memPtr_1,  32), _192)
let _193 := mload( add(memPtr_1,  32))
let cleaned_17 := signextend( 2,  _193)
let cleaned_18 := signextend( 2,  cleaned_17)
let _194 := sgt(cleaned_18,  signextend( 2,  signextend( 2,  _108)))
let _195 := iszero(_194)
if  _195
{
mstore( add(memPtr_1,  32), signextend( 2,  signextend( 2,  _108)))
}
let _196 := mload( add(memPtr_1,  32))
let cleaned_19 := signextend( 2,  _196)
let cleaned_20 := signextend( 2,  cleaned_19)
let _197 := slt(cleaned_20,  signextend( 2,  signextend( 2,  _109)))
let _198 := iszero(_197)
if  _198
{
mstore( add(memPtr_1,  32), signextend( 2,  signextend( 2,  _109)))
}
let _199 := mload( add(memPtr_1,  32))
let cleaned_21 := signextend( 2,  _199)
let _200 := fun_getSqrtPriceAtTick( cleaned_21)
let _201 := and(_200,  1461501637330902918203684832716283019655932542975)
mstore( add(memPtr_1,  96), _201)
let _202 := mload( var_result_4424_mpos)
let _203 := mload( add(memPtr_1,  96))
let cleaned_22 := and(_203,  1461501637330902918203684832716283019655932542975)
let _204 := add(var_params_4413_mpos,  96)
let _205 := mload( _204)
let cleaned_23 := and(_205,  1461501637330902918203684832716283019655932542975)
let var_sqrtPriceNextX96 := and(cleaned_22,  1461501637330902918203684832716283019655932542975)
let var_sqrtPriceLimitX96 := and(cleaned_23,  1461501637330902918203684832716283019655932542975)
let _206 := lt(var_sqrtPriceNextX96, var_sqrtPriceLimitX96)
let _207 := xor(_206, and( iszero(_6),  0x1))
let _208 := xor(var_sqrtPriceNextX96, var_sqrtPriceLimitX96)
let _209 := mul(_208, _207)
let _210 := mload( add( var_result_4424_mpos,  64))
let var_sqrtPriceNextX96_1 :=  0
let var_sqrtPriceNextX96_2 := var_sqrtPriceNextX96_1
let var_amountIn :=  0
let var_amountIn_1 := var_amountIn
let var_amountOut :=  0
let var_amountOut_1 := var_amountOut
let var_feeAmount :=  0
let var_feeAmount_1 := var_feeAmount
let _211 := and( xor(var_sqrtPriceLimitX96, _209),  1461501637330902918203684832716283019655932542975)
let _212 := lt( and(and(_202,  1461501637330902918203684832716283019655932542975), 1461501637330902918203684832716283019655932542975),  _211)
let _213 := slt( var_amountSpecifiedRemaining_1,  0)
switch  _213
case  0 {
let expr_45 :=  0
let expr_46 := expr_45
switch  iszero(_212)
case  0 {
let expr_47 :=  fun_getAmount0Delta_7971( and(_202,  1461501637330902918203684832716283019655932542975),  xor(var_sqrtPriceLimitX96, _209),  and(_210, 0xffffffffffffffffffffffffffffffff), 0)
let expr_48 := expr_47
expr_46 := expr_48
}
default {
let expr_49 :=  fun_getAmount1Delta_8027( xor(var_sqrtPriceLimitX96, _209),  and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff), 0)
let expr_50 := expr_49
expr_46 := expr_50
}
let expr_51 := expr_46
let var_amountOut_2 := expr_51
var_amountOut_1 := var_amountOut_2
let _214 := lt( var_amountSpecifiedRemaining_1,  expr_51)
let _215 := iszero(_214)
switch  _215
case  0 {
let var_amountOut_3 :=  var_amountSpecifiedRemaining_1
var_amountOut_1 := var_amountOut_3
let _216 := and( and(_210, 0xffffffffffffffffffffffffffffffff), 0xffffffffffffffffffffffffffffffff)
let _217 := iszero(_216)
let _218 := iszero( and(and(_202,  1461501637330902918203684832716283019655932542975), 1461501637330902918203684832716283019655932542975))
let _219 := or(_218, _217)
if _219
{
let _220 := 0x4f2461b8
mstore( 0,  _220)
let _221 := 0x04
let _222 := 0x1c
revert(_222, _221)
}
let expr_52 :=  0
let expr_53 := expr_52
switch  iszero(_212)
case  0 {
let expr_54 :=  fun_getNextSqrtPriceFromAmount0RoundingUp( and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  var_amountSpecifiedRemaining_1,  0)
let expr_55 := expr_54
expr_53 := expr_55
}
default {
let expr_56 :=  fun_getNextSqrtPriceFromAmount1RoundingDown( and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  var_amountSpecifiedRemaining_1,  0)
let expr_57 := expr_56
expr_53 := expr_57
}
let expr_58 := expr_53
let var_sqrtPriceNextX96_3 := expr_58
var_sqrtPriceNextX96_2 := var_sqrtPriceNextX96_3
}
default
{
let var_sqrtPriceNextX96_4 :=  xor(var_sqrtPriceLimitX96, _209)
var_sqrtPriceNextX96_2 := var_sqrtPriceNextX96_4
}
let var_sqrtPriceNextX96_5 := var_sqrtPriceNextX96_2
let expr_59 :=  0
let expr_60 := expr_59
switch  iszero(_212)
case  0 {
let expr_61 :=  fun_getAmount1Delta_8027( and(_202,  1461501637330902918203684832716283019655932542975),  var_sqrtPriceNextX96_5,  and(_210, 0xffffffffffffffffffffffffffffffff),  0x1)
let expr_62 := expr_61
expr_60 := expr_62
}
default {
let expr_63 :=  fun_getAmount0Delta_7971(var_sqrtPriceNextX96_5,  and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  0x1)
let expr_64 := expr_63
expr_60 := expr_64
}
let expr_65 := expr_60
let var_amountIn_2 := expr_65
var_amountIn_1 := var_amountIn_2
let _223 := sub( 0x0f4240,  and( var_swapFee,  0xffffff))
let var_feeAmount_2 :=  fun_mulDivRoundingUp(expr_65,  and( var_swapFee,  0xffffff), _223)
let var_feeAmount_3 := var_feeAmount_2
var_feeAmount_1 := var_feeAmount_3
}
default
{
let expr_66 := fun_mulDiv( sub(0,  var_amountSpecifiedRemaining_1),  sub( 0x0f4240,  and( var_swapFee,  0xffffff)),  0x0f4240)
let expr_67 :=  0
let expr_68 := expr_67
switch  iszero(_212)
case  0 {
let expr_69 :=  fun_getAmount1Delta_8027( and(_202,  1461501637330902918203684832716283019655932542975),  xor(var_sqrtPriceLimitX96, _209),  and(_210, 0xffffffffffffffffffffffffffffffff),  0x1)
let expr_70 := expr_69
expr_68 := expr_70
}
default {
let expr_71 :=  fun_getAmount0Delta_7971( xor(var_sqrtPriceLimitX96, _209),  and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  0x1)
let expr_72 := expr_71
expr_68 := expr_72
}
let var_amountIn_3 := expr_68
var_amountIn_1 := var_amountIn_3
let _224 := lt(expr_66,  expr_68)
let _225 := iszero(_224)
switch  _225
case  0 {
let var_amountIn_4 := expr_66
var_amountIn_1 := var_amountIn_4
let _226 := and( and(_210, 0xffffffffffffffffffffffffffffffff), 0xffffffffffffffffffffffffffffffff)
let _227 := iszero(_226)
let _228 := iszero( and(and(_202,  1461501637330902918203684832716283019655932542975), 1461501637330902918203684832716283019655932542975))
let _229 := or(_228, _227)
if _229
{
let _230 := 0x4f2461b8
mstore( 0,  _230)
let _231 := 0x04
let _232 := 0x1c
revert(_232, _231)
}
let expr_73 :=  0
let expr_74 := expr_73
switch  iszero(_212)
case  0 {
let expr_75 :=  fun_getNextSqrtPriceFromAmount1RoundingDown( and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  expr_66,  0x1)
let expr_76 := expr_75
expr_74 := expr_76
}
default {
let expr_77 :=  fun_getNextSqrtPriceFromAmount0RoundingUp( and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff),  expr_66,  0x1)
let expr_78 := expr_77
expr_74 := expr_78
}
let expr_79 := expr_74
let var_sqrtPriceNextX96_6 := expr_79
var_sqrtPriceNextX96_2 := var_sqrtPriceNextX96_6
let var_feeAmount_4 :=  sub(sub(0,  var_amountSpecifiedRemaining_1),  expr_66)
let var_feeAmount_5 := var_feeAmount_4
var_feeAmount_1 := var_feeAmount_5
}
default
{
let var_amountIn_5 := var_amountIn_1
let var_sqrtPriceNextX96_7 :=  xor(var_sqrtPriceLimitX96, _209)
var_sqrtPriceNextX96_2 := var_sqrtPriceNextX96_7
let expr_80 := eq( and( var_swapFee,  0xffffff),  0x0f4240)
let expr_81 :=  0
let expr_82 := expr_81
switch expr_80
case 0 {
let expr_83 :=  fun_mulDivRoundingUp(var_amountIn_5,  and( var_swapFee,  0xffffff), sub( 0x0f4240,  and( var_swapFee,  0xffffff)))
let expr_84 := expr_83
expr_82 := expr_84
}
default {
let expr_85 := var_amountIn_5
expr_82 := expr_85
}
let expr_86 := expr_82
let var_feeAmount_6 := expr_86
var_feeAmount_1 := var_feeAmount_6
}
let var_sqrtPriceNextX96_8 := var_sqrtPriceNextX96_2
let expr_87 :=  0
let expr_88 := expr_87
switch  iszero(_212)
case  0 {
let expr_89 :=  fun_getAmount0Delta_7971( and(_202,  1461501637330902918203684832716283019655932542975),  var_sqrtPriceNextX96_8,  and(_210, 0xffffffffffffffffffffffffffffffff), 0)
let expr_90 := expr_89
expr_88 := expr_90
}
default {
let expr_91 :=  fun_getAmount1Delta_8027(var_sqrtPriceNextX96_8,  and(_202,  1461501637330902918203684832716283019655932542975),  and(_210, 0xffffffffffffffffffffffffffffffff), 0)
let expr_92 := expr_91
expr_88 := expr_92
}
let expr_93 := expr_88
let var_amountOut_4 := expr_93
var_amountOut_1 := var_amountOut_4
}
let var_amountOut_5 := var_amountOut_1
let var_sqrtPriceNextX96_9 := var_sqrtPriceNextX96_2
let var_amountIn_6 := var_amountIn_1
let var_feeAmount_7 := var_feeAmount_1
mstore( add(memPtr_1, 192),  var_feeAmount_7)
mstore( add(memPtr_1,  160),  var_amountOut_5)
mstore( add(memPtr_1,  128),  var_amountIn_6)
let _233 := and(var_sqrtPriceNextX96_9,  1461501637330902918203684832716283019655932542975)
mstore( var_result_4424_mpos,  _233)
let _234 := mload( var_params_4413_mpos)
let _235 := sgt(_234,  0)
switch  _235
case  0 {
let _236 := mload(add(memPtr_1,  128))
let _237 := mload(add(memPtr_1, 192))
let _238 := slt( add(_236, _237),  0)
if  _238
{
let _239 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
mstore( 0,  _239)
let _240 := 0x04
revert( 0,  _240)
}
let sum_1 := add( var_amountSpecifiedRemaining_1,  add(_236, _237))
let var_amountSpecifiedRemaining_2 := sum_1
var_amountSpecifiedRemaining_1 := var_amountSpecifiedRemaining_2
let _241 := mload(add(memPtr_1,  160))
let _242 := slt(_241,  0)
if  _242
{
let _243 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
mstore( 0,  _243)
let _244 := 0x04
revert( 0,  _244)
}
let var_amountCalculated_2 := checked_add_int256( var_amountCalculated_1,  _241)
let var_amountCalculated_3 := var_amountCalculated_2
var_amountCalculated_1 := var_amountCalculated_3
}
default
{
let _245 := mload(add(memPtr_1,  160))
let _246 := slt(_245,  0)
if  _246
{
let _247 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
mstore( 0,  _247)
let _248 := 0x04
revert( 0,  _248)
}
let diff_4 := sub( var_amountSpecifiedRemaining_1,  _245)
let var_amountSpecifiedRemaining_3 := diff_4
var_amountSpecifiedRemaining_1 := var_amountSpecifiedRemaining_3
let _249 := mload(add(memPtr_1,  128))
let _250 := mload(add(memPtr_1, 192))
let _251 := checked_add_uint256(_249,  _250)
if  slt(_251,  0)
{
let _252 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
mstore( 0,  _252)
let _253 := 0x04
revert( 0,  _253)
}
let _254 := slt(sub(var_amountCalculated_1, _251), var_amountCalculated_1)
let _255 := and( slt(_251,  0),  _254)
let _256 := sgt(sub(var_amountCalculated_1, _251), var_amountCalculated_1)
let _257 := iszero( slt(_251,  0))
let _258 := and(_257, _256)
let _259 := or(_258, _255)
if _259
{
let _260 := 35408467139433450592217433187231851964531694900788300625387963629091585785856
mstore(0, _260)
let _261 := 0x11
let _262 := 4
mstore(_262, _261)
let _263 := 0x24
revert(0, _263)
}
let var_amountCalculated_4 :=  sub(var_amountCalculated_1, _251)
var_amountCalculated_1 := var_amountCalculated_4
}
if  gt( and( expr_4,  0xffff), 0)
{
let expr_94 := eq( and( var_swapFee,  0xffffff), and( expr_4,  0xffff))
let expr_95 :=  0
let expr_96 := expr_95
switch expr_94
case 0 {
let _264 := mload(add(memPtr_1,  128))
let _265 := mload(add(memPtr_1, 192))
let sum_2 := add(_264, _265)
let _266 := iszero( 0x0f4240)
if _266
{
let _267 := 35408467139433450592217433187231851964531694900788300625387963629091585785856
mstore( 0,  _267)
let _268 := 0x12
let _269 := 4
mstore(_269, _268)
let _270 := 0x24
revert( 0,  _270)
}
let r := div( mul(sum_2, and( expr_4,  0xffff)),  0x0f4240)
let expr_97 := r
expr_96 := expr_97
}
default {
let _271 := mload(add(memPtr_1, 192))
let expr_98 := _271
expr_96 := expr_98
}
let expr_99 := expr_96
let _272 := mload(add(memPtr_1, 192))
let diff_5 := sub(_272, expr_99)
mstore( add(memPtr_1, 192),  diff_5)
let var_amountToProtocol_3 :=  add( var_amountToProtocol, expr_99)
let var_amountToProtocol_4 := var_amountToProtocol_3
var_amountToProtocol := var_amountToProtocol_4
}
let _273 := mload( add( var_result_4424_mpos,  64))
let cleaned_24 := and(_273, 0xffffffffffffffffffffffffffffffff)
let cleaned_25 := and(cleaned_24, 0xffffffffffffffffffffffffffffffff)
let _274 := gt(cleaned_25,  and(0, 0xffffffffffffffffffffffffffffffff))
if  _274
{
let _275 := mload(add(memPtr_1, 192))
let expr_100 :=  0x0100000000000000000000000000000000
let _276 := mload( add( var_result_4424_mpos,  64))
let cleaned_26 := and(_276, 0xffffffffffffffffffffffffffffffff)
let cleaned_27 := and(cleaned_26, 0xffffffffffffffffffffffffffffffff)
let _277 := mul(_275,  expr_100)
let var_result := div(_277, cleaned_27)
let _278 := mload(add(memPtr_1, 224))
let sum_3 := add(_278, var_result)
mstore( add(memPtr_1, 224),  sum_3)
}
let _279 := mload( var_result_4424_mpos)
let cleaned_28 := and(_279,  1461501637330902918203684832716283019655932542975)
let _280 := mload( add(memPtr_1,  96))
let cleaned_29 := and(_280,  1461501637330902918203684832716283019655932542975)
let cleaned_30 := and(cleaned_29,  1461501637330902918203684832716283019655932542975)
let _281 := and( cleaned_28,  1461501637330902918203684832716283019655932542975)
let _282 := eq( _281,  cleaned_30)
switch  _282
case  0 {
let _283 := mload( var_result_4424_mpos)
let cleaned_31 := and(_283,  1461501637330902918203684832716283019655932542975)
let _284 := mload( memPtr_1)
let cleaned_32 := and(_284,  1461501637330902918203684832716283019655932542975)
let cleaned_33 := and(cleaned_32,  1461501637330902918203684832716283019655932542975)
let _285 := and( cleaned_31,  1461501637330902918203684832716283019655932542975)
let _286 := eq( _285,  cleaned_33)
let _287 := iszero(_286)
if  _287
{
let _288 := mload( var_result_4424_mpos)
let cleaned_34 := and(_288,  1461501637330902918203684832716283019655932542975)
let _289 := fun_getTickAtSqrtPrice( cleaned_34)
let _290 := signextend( 2,  _289)
mstore( add( var_result_4424_mpos,  32), _290)
}
}
default
{
let _291 := mload( add(memPtr_1,  64))
let _292 := iszero(_291)
let cleaned_35 := iszero(_292)
if  cleaned_35
{
let expr_component :=  0
let expr_4864_component := expr_component
let expr_component_1 :=  0
let expr_4864_component_1 := expr_component_1
switch  iszero(_6)
case  0 {
let _293 := add(var_self_4410_slot,  0x1)
let _294 := sload( _293)
let _295 := mload(add(memPtr_1, 224))
let expr_component_2 := _294
expr_4864_component := expr_component_2
let expr_component_3 := _295
expr_4864_component_1 := expr_component_3
}
default {
let _296 := mload(add(memPtr_1, 224))
let _297 := add(var_self_4410_slot,  2)
let _298 := sload( _297)
let expr_component_4 := _296
expr_4864_component := expr_component_4
let expr_component_5 := _298
expr_4864_component_1 := expr_component_5
}
let expr_component_6 := expr_4864_component
let expr_component_7 := expr_4864_component_1
let _299 := mload( add(memPtr_1,  32))
let cleaned_36 := signextend( 2,  _299)
let _300 := 4
let _301 := add(var_self_4410_slot, _300)
let _302 := mapping_index_access_mapping_int24_struct_TickInfo_storage_of_int24( _301,  cleaned_36)
let _303 := add(_302,  0x1)
let _304 := sload( _303)
let diff_6 := sub(expr_component_6, _304)
sstore(_303, diff_6)
let _305 := add(_302,  2)
let _306 := sload( _305)
let diff_7 := sub(expr_component_7, _306)
sstore(_305, diff_7)
let _307 := sload( _302)
let _308 := shr( 128,  _307)
let _309 := 15
let value_1 := signextend(_309, _308)
let var_liquidityNet := value_1
let var_liquidityNet_1 := var_liquidityNet
if  iszero(_6)
{
let _310 := sub(0,  value_1)
let var_liquidityNet_2 :=  signextend(_309, _310)
let var_liquidityNet_3 := var_liquidityNet_2
var_liquidityNet_1 := var_liquidityNet_3
}
let var_liquidityNet_4 := var_liquidityNet_1
let _311 := mload( add( var_result_4424_mpos,  64))
let cleaned_37 := and(_311, 0xffffffffffffffffffffffffffffffff)
let _312 := fun_addDelta( cleaned_37,  var_liquidityNet_4)
let _313 := and(_312, 0xffffffffffffffffffffffffffffffff)
mstore( add( var_result_4424_mpos,  64), _313)
}
let expr_101 :=  0
let expr_102 := expr_101
switch  iszero(_6)
case  0 {
let _314 := mload( add(memPtr_1,  32))
let cleaned_38 := signextend( 2,  _314)
let expr_103 := cleaned_38
expr_102 := expr_103
}
default {
let _315 := mload( add(memPtr_1,  32))
let cleaned_39 := signextend( 2,  _315)
let _316 := signextend( 2,  0x1)
let _317 := sub( cleaned_39,  _316)
let expr_104 :=  signextend( 2,  _317)
let expr_105 := expr_104
expr_102 := expr_105
}
let expr_106 := expr_102
let _318 := signextend( 2,  expr_106)
mstore( add( var_result_4424_mpos,  32), _318)
}
}
let _319 := add( var_result_4424_mpos,  32)
let _320 := mload( _319)
let cleaned_40 := signextend( 2,  _320)
let _321 := 0xffffff0000000000000000000000000000000000000000
let _322 := shl( 160,  cleaned_40)
let _323 := and(_322, _321)
let _324 := 0xffffffffffffffffff000000ffffffffffffffffffffffffffffffffffffffff
let _325 := and(_324, _3)
let var_result_1 := or(_325, _323)
let _326 := mload( var_result_4424_mpos)
let cleaned_41 := and(_326,  1461501637330902918203684832716283019655932542975)
let _327 := and( 1461501637330902918203684832716283019655932542975,  cleaned_41)
let _328 := 0xffffffffffffffffffffffff0000000000000000000000000000000000000000
let _329 := and(_328, var_result_1)
let var_result_2 := or(_329, _327)
sstore(var_self_4410_slot, var_result_2)
let _330 := sload( add(var_self_4410_slot, _28))
let cleaned_42 := and(_330, 0xffffffffffffffffffffffffffffffff)
let _331 := add( var_result_4424_mpos,  64)
let _332 := mload( _331)
let cleaned_43 := and(_332, 0xffffffffffffffffffffffffffffffff)
let cleaned_44 := and(cleaned_43, 0xffffffffffffffffffffffffffffffff)
let _333 := and( cleaned_42,  0xffffffffffffffffffffffffffffffff)
let _334 := eq( _333,  cleaned_44)
let _335 := iszero(_334)
if  _335
{
let _336 := mload( _331)
let cleaned_45 := and(_336, 0xffffffffffffffffffffffffffffffff)
update_storage_value_offsett_uint128_to_uint128( add(var_self_4410_slot, _28),  cleaned_45)
}
let _337 := iszero( iszero(_6))
let _338 := iszero( _337)
let _339 := iszero(_338)
switch  _339
case  0 {
let _340 := mload(add(memPtr_1, 224))
let _341 := add(var_self_4410_slot,  0x1)
sstore(_341, _340)
}
default
{
let _342 := mload(add(memPtr_1, 224))
let _343 := add(var_self_4410_slot,  2)
sstore(_343, _342)
}
let _344 := mload( var_params_4413_mpos)
let _345 := slt(_344,  0)
let _346 := iszero(_345)
let cleaned_46 := iszero(_346)
let _347 := eq( _338,  cleaned_46)
let _348 := iszero(_347)
switch  _348
case  0 {
let _349 := mload( var_params_4413_mpos)
let diff_8 := sub(_349,  var_amountSpecifiedRemaining_1)
let expr_107 := fun_toInt128( diff_8)
let _350 := fun_toInt128( var_amountCalculated_1)
let _351 := and( 0xffffffffffffffffffffffffffffffff,  _350)
let _352 := shl( 128,  expr_107)
let var_balanceDelta := or(_352, _351)
let var_swapDelta_2 := var_balanceDelta
var_swapDelta := var_swapDelta_2
}
default
{
let expr_108 := fun_toInt128( var_amountCalculated_1)
let _353 := mload( var_params_4413_mpos)
let diff_9 := sub(_353,  var_amountSpecifiedRemaining_1)
let _354 := fun_toInt128( diff_9)
let _355 := and( 0xffffffffffffffffffffffffffffffff,  _354)
let _356 := shl( 128,  expr_108)
let var_balanceDelta_1 := or(_356, _355)
let var_swapDelta_3 := var_balanceDelta_1
var_swapDelta := var_swapDelta_3
}
}