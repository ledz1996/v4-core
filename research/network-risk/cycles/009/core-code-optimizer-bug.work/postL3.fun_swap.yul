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
let _31 := add(var_params_4413_mpos, 128)
let _32 := mload( _31)
let cleaned_2 := and(_32, 0xffffff)
let _33 := 0x400000
let _34 := and( _33,  0xffffff)
let expr_6 := and(cleaned_2,  _34)
let _35 := and(0, 0xffffff)
let _36 := and( expr_6,  0xffffff)
let _37 := eq( _36, _35)
let var :=  iszero(_37)
let expr_7 :=  0
let expr_8 := expr_7
switch var
case 0 {
let _38 := 208
let _39 := shr(_38,  _3)
let expr_9 :=  and( 0xffffff,  _39)
let expr_10 := expr_9
expr_8 := expr_10
}
default {
let _40 := _32
let cleaned_3 := and(_40, 0xffffff)
let _41 := 0xbfffff
let ret :=  and( _41,  0xffffff)
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
let _42 := and(and( expr_4,  0xffff), 0xffff)
let _43 := 0xfff
let var_self := and(_42, _43)
let var_lpFee := and(expr_13,  0xffffff)
let usr$numerator := mul(var_self, var_lpFee)
let _44 := 1000000
let _45 := div(usr$numerator, _44)
let _46 := add(var_self, var_lpFee)
let var_swapFee_1 := sub(_46, _45)
let expr_17 := var_swapFee_1
expr_16 := expr_17
}
default {
let expr_18 := expr_13
expr_16 := expr_18
}
let var_swapFee_2 := expr_16
var_swapFee := var_swapFee_2
let _47 := and( expr_16,  0xffffff)
let _48 := lt( _47,  0x0f4240)
let _49 := iszero(_48)
if  _49
{
let _50 := mload( var_params_4413_mpos)
let _51 := sgt(_50,  0)
if  _51
{
let _52 := 0x9620624600000000000000000000000000000000000000000000000000000000
mstore( 0,  _52)
let _53 := 0x04
revert( 0,  _53)
}
}
let _54 := mload( var_params_4413_mpos)
let _55 := eq(_54,  0)
if  _55
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
let _56 := mload( add(var_params_4413_mpos,  96))
let cleaned_4 := and(_56,  1461501637330902918203684832716283019655932542975)
let _57 := and( cleaned_4,  1461501637330902918203684832716283019655932542975)
let _58 := gt( _57, and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _59 := iszero(_58)
if  _59
{
let _60 := _56
let cleaned_5 := and(_60,  1461501637330902918203684832716283019655932542975)
let _61 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
let usr$fmp := mload( 64)
mstore(usr$fmp,  _61)
let _62 := 0x04
let _63 := add(usr$fmp, _62)
mstore(_63,  and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _64 := and(cleaned_5,  1461501637330902918203684832716283019655932542975)
let _65 := 0x24
let _66 := add(usr$fmp, _65)
mstore(_66, _64)
let _67 := 0x44
revert(usr$fmp, _67)
}
let _68 := mload( add(var_params_4413_mpos,  96))
let cleaned_6 := and(_68,  1461501637330902918203684832716283019655932542975)
let _69 := 0xfffd8963efd1fc6a506488495d951d5263988d26
let _70 := and( _69,  1461501637330902918203684832716283019655932542975)
let _71 := and(_70,  1461501637330902918203684832716283019655932542975)
let _72 := and( cleaned_6,  1461501637330902918203684832716283019655932542975)
let _73 := lt( _72, _71)
let _74 := iszero(_73)
if  _74
{
let _75 := _68
let cleaned_7 := and(_75,  1461501637330902918203684832716283019655932542975)
let _76 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
mstore( 0,  _76)
let _77 := and(cleaned_7,  1461501637330902918203684832716283019655932542975)
let _78 := 0x04
mstore(_78, _77)
let _79 := 0x24
revert( 0,  _79)
}
}
default
{
let _80 := mload( add(var_params_4413_mpos,  96))
let cleaned_8 := and(_80,  1461501637330902918203684832716283019655932542975)
let _81 := and( cleaned_8,  1461501637330902918203684832716283019655932542975)
let _82 := lt( _81, and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _83 := iszero(_82)
if  _83
{
let _84 := _80
let cleaned_9 := and(_84,  1461501637330902918203684832716283019655932542975)
let _85 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
let usr$fmp_1 := mload( 64)
mstore(usr$fmp_1,  _85)
let _86 := 0x04
let _87 := add(usr$fmp_1, _86)
mstore(_87,  and( and(1461501637330902918203684832716283019655932542975,  _3),  1461501637330902918203684832716283019655932542975))
let _88 := and(cleaned_9,  1461501637330902918203684832716283019655932542975)
let _89 := 0x24
let _90 := add(usr$fmp_1, _89)
mstore(_90, _88)
let _91 := 0x44
revert(usr$fmp_1, _91)
}
let _92 := mload( add(var_params_4413_mpos,  96))
let cleaned_10 := and(_92,  1461501637330902918203684832716283019655932542975)
let _93 := 0x01000276a3
let _94 := and( _93,  1461501637330902918203684832716283019655932542975)
let _95 := and(_94,  1461501637330902918203684832716283019655932542975)
let _96 := and( cleaned_10,  1461501637330902918203684832716283019655932542975)
let _97 := gt( _96, _95)
let _98 := iszero(_97)
if  _98
{
let _99 := _92
let cleaned_11 := and(_99,  1461501637330902918203684832716283019655932542975)
let _100 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
mstore( 0,  _100)
let _101 := and(cleaned_11,  1461501637330902918203684832716283019655932542975)
let _102 := 0x04
mstore(_102, _101)
let _103 := 0x24
revert( 0,  _103)
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
let _104 := add(var_self_4410_slot,  2)
let _105 := sload( _104)
let expr_21 := _105
expr_20 := expr_21
}
default {
let _106 := 1
let _107 := add(var_self_4410_slot, _106)
let _108 := sload( _107)
let expr_22 := _108
expr_20 := expr_22
}
let expr_23 := expr_20
mstore( add(memPtr_1, 224),  expr_23)
let _109 := 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618
let _110 := 0x0d89e8
for { }
0x1
{ }
{
let expr_24 := eq(var_amountSpecifiedRemaining_1,  0)
let expr_25 := expr_24
let expr_26 := expr_25
let _111 := iszero(expr_24)
if _111
{
let _112 := mload( var_result_4424_mpos)
let cleaned_12 := and(_112,  1461501637330902918203684832716283019655932542975)
let _113 := add(var_params_4413_mpos,  96)
let _114 := mload( _113)
let cleaned_13 := and(_114,  1461501637330902918203684832716283019655932542975)
let cleaned_14 := and(cleaned_13,  1461501637330902918203684832716283019655932542975)
let _115 := and( cleaned_12,  1461501637330902918203684832716283019655932542975)
let expr_27 :=  eq( _115,  cleaned_14)
let expr_28 := expr_27
expr_26 := expr_28
}
let expr_29 := expr_26
let _116 := iszero(expr_29)
let _117 := iszero( _116)
let _118 := iszero(_117)
let _119 := iszero( _118)
if _119 { break }
let _120 := mload( var_result_4424_mpos)
let cleaned_15 := and(_120,  1461501637330902918203684832716283019655932542975)
let _121 := and(cleaned_15,  1461501637330902918203684832716283019655932542975)
mstore(memPtr_1, _121)
let _122 := mload( add( var_result_4424_mpos,  32))
let cleaned_16 := signextend( 2,  _122)
let _123 := add(var_params_4413_mpos,  32)
let _124 := mload( _123)
let var_next :=  0
let var_next_1 := var_next
let var_initialized :=  0
let var_initialized_1 := var_initialized
let var_tick := signextend( 2,  cleaned_16)
let var_tickSpacing := signextend( 2,  signextend( 2,  _124))
let _125 := smod(var_tick, var_tickSpacing)
let _126 := slt(_125,  0)
let _127 := sdiv(var_tick, var_tickSpacing)
switch  iszero(_6)
case  0 {
let _128 := add( sub(_127, _126),  0x1)
let _129 := signextend( 2,  signextend( 2,  _128))
let _130 := 8
let bits_1 :=  and( and( signextend( 2,  _128),  0xff), 0xff)
let result_1 :=  shl( bits_1,  0x1)
let diff := sub(result_1,  0x1)
let _131 := not( diff)
let _132 := mapping_index_access_mapping_int16_uint256_of_int16( add(var_self_4410_slot, 5),  sar(_130, _129))
let _133 := sload(_132)
let _134 := eq( and( _133,  _131),  0)
let var_initialized_2 :=  iszero(_134)
var_initialized_1 := var_initialized_2
let expr_30 :=  0
let expr_31 := expr_30
switch  iszero(_134)
case  0 {
let _135 := sub( 0xff, and( signextend( 2,  _128),  0xff))
let _136 := and(_135,  0xff)
let _137 := and(_136,  0xff)
let _138 := and(_137, 0xffffff)
let _139 := and(_138, 0xffffff)
let _140 := signextend( 2,  _139)
let _141 := add(signextend( 2,  _128), _140)
let _142 := signextend( 2,  _141)
let _143 := mul(_142, signextend( 2,  _124))
let expr_32 :=  signextend( 2,  _143)
let expr_33 := expr_32
expr_31 := expr_33
}
default {
let _144 := gt( and( _133,  _131),  0)
let _145 := iszero(_144)
if _145 { revert(0, 0) }
let _146 := sub( 0,  and( _133,  _131))
let var_x := and( and( _133,  _131),  _146)
let _147 := 480
let _148 := 0x8040405543005266443200005020610674053026020000107506200176117077
let _149 := 252
let _150 := 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff
let _151 := mul(var_x, _150)
let _152 := 248
let _153 := shr(_152, _151)
let _154 := and(_153, _149)
let _155 := shl(_154, _148)
let _156 := 247
let _157 := shr(_156, _155)
let var_r := and(_157, _147)
let _158 := 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405
let _159 := 0x1f
let _160 := shr(var_r, var_x)
let _161 := 0xd76453e0
let _162 := div(_161, _160)
let _163 := and(_162, _159)
let _164 := byte(_163, _158)
let var_r_1 := or(var_r, _164)
let _165 := sub(var_r_1,  and( signextend( 2,  _128),  0xff))
let diff_1 := and(_165,  0xff)
let _166 := and(diff_1,  0xff)
let converted_2 := and(_166, 0xffffff)
let _167 := and(converted_2, 0xffffff)
let converted_3 := signextend( 2,  _167)
let _168 := add(signextend( 2,  _128), converted_3)
let sum := signextend( 2,  _168)
let _169 := mul(sum, signextend( 2,  _124))
let product := signextend( 2,  _169)
let expr_34 := product
expr_31 := expr_34
}
let expr_35 := expr_31
let var_next_2 := expr_35
var_next_1 := var_next_2
}
default
{
let _170 := signextend( 2,  sub(_127, _126))
let _171 := 8
let var_wordPos := sar(_171, _170)
let _172 := 0xff
let var_bitPos := and( sub(_127, _126),  _172)
let expr_36 :=  and(_172, _172)
let _173 := and( var_bitPos,  _172)
let _174 := sub( expr_36,  _173)
let _175 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
let result_2 :=  shr( _174,  _175)
let _176 := mapping_index_access_mapping_int16_uint256_of_int16( add(var_self_4410_slot, 5),  var_wordPos)
let _177 := sload(_176)
let expr_37 := and( _177,  result_2)
let _178 := eq(expr_37,  0)
let expr_38 := iszero(_178)
let var_initialized_3 := expr_38
var_initialized_1 := var_initialized_3
let expr_39 :=  0
let expr_40 := expr_39
switch expr_38
case 0 {
let _179 := and(_173, 0xffffff)
let _180 := and(_179, 0xffffff)
let _181 := signextend( 2,  _180)
let _182 := sub( sub(_127, _126),  _181)
let _183 := signextend( 2,  _182)
let _184 := mul(_183, signextend( 2,  _124))
let expr_41 :=  signextend( 2,  _184)
let expr_42 := expr_41
expr_40 := expr_42
}
default {
let _185 := fun_mostSignificantBit(expr_37)
let _186 := sub(var_bitPos, _185)
let diff_2 := and(_186, _172)
let _187 := and(diff_2, _172)
let converted_4 := and(_187, 0xffffff)
let _188 := and(converted_4, 0xffffff)
let converted_5 := signextend( 2,  _188)
let _189 := sub( sub(_127, _126),  converted_5)
let diff_3 :=  signextend( 2,  _189)
let _190 := mul(diff_3, signextend( 2,  _124))
let product_1 := signextend( 2,  _190)
let expr_43 := product_1
expr_40 := expr_43
}
let expr_44 := expr_40
let var_next_3 := expr_44
var_next_1 := var_next_3
}
let var_initialized_4 := var_initialized_1
let var_next_4 := var_next_1
let _191 := iszero(var_initialized_4)
let _192 := iszero(_191)
mstore( add(memPtr_1,  64), _192)
let _193 := signextend( 2,  var_next_4)
mstore( add(memPtr_1,  32), _193)
let _194 := _193
let cleaned_17 := signextend( 2,  _194)
let cleaned_18 := signextend( 2,  cleaned_17)
let _195 := sgt(cleaned_18,  signextend( 2,  signextend( 2,  _109)))
let _196 := iszero(_195)
if  _196
{
mstore( add(memPtr_1,  32), signextend( 2,  signextend( 2,  _109)))
}
let _197 := mload( add(memPtr_1,  32))
let cleaned_19 := signextend( 2,  _197)
let cleaned_20 := signextend( 2,  cleaned_19)
let _198 := slt(cleaned_20,  signextend( 2,  signextend( 2,  _110)))
let _199 := iszero(_198)
if  _199
{
mstore( add(memPtr_1,  32), signextend( 2,  signextend( 2,  _110)))
}
let _200 := mload( add(memPtr_1,  32))
let cleaned_21 := signextend( 2,  _200)
let _201 := fun_getSqrtPriceAtTick( cleaned_21)
mstore( add(memPtr_1,  96), and(_201,  1461501637330902918203684832716283019655932542975))
let _202 := mload( var_result_4424_mpos)
let _203 := and(_201,  1461501637330902918203684832716283019655932542975)
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
let _276 := _273
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
let _283 := _279
let cleaned_31 := and(_283,  1461501637330902918203684832716283019655932542975)
let _284 := mload( memPtr_1)
let cleaned_32 := and(_284,  1461501637330902918203684832716283019655932542975)
let cleaned_33 := and(cleaned_32,  1461501637330902918203684832716283019655932542975)
let _285 := and( cleaned_31,  1461501637330902918203684832716283019655932542975)
let _286 := eq( _285,  cleaned_33)
let _287 := iszero(_286)
if  _287
{
let _288 := _279
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
let _336 := _332
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
let _349 := _344
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