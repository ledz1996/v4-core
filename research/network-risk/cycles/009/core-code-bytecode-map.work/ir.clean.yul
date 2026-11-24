object "PoolManager_1216" {
 code {
 {
 let _1 := memoryguard(0xa0)
 if callvalue() { revert(0, 0) }
 let programSize := datasize("PoolManager_1216")
 let argSize := sub(codesize(), programSize)
 let newFreePtr := add(_1, and(add(argSize, 31), not(31)))
 if or(gt(newFreePtr, sub(shl(64, 1), 1)), lt(newFreePtr, _1))
 {
 mstore( 0, shl(224, 0x4e487b71))
 mstore(4, 0x41)
 revert( 0, 0x24)
 }
 mstore(64, newFreePtr)
 codecopy(_1, programSize, argSize)
 if slt(sub(add(_1, argSize), _1), 32)
 {
 revert( 0, 0)
 }
 let value := mload(_1)
 let _2 := and(value, sub(shl(160, 1), 1))
 if iszero(eq(value, _2))
 {
 revert( 0, 0)
 }
 sstore( 0, or(and(sload( 0), not(sub(shl(160, 1), 1))), _2))
 let _3 := mload(64)
 log3( 0, 0, 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0, 0, _2)
 mstore(128, address())
 let _4 := datasize("PoolManager_1216_deployed")
 codecopy(_3, dataoffset("PoolManager_1216_deployed"), _4)
 setimmutable(_3, "1375", mload( 128))
 return(_3, _4)
 }
 }
 object "PoolManager_1216_deployed" {
 code {
 {
 let _1 := memoryguard(0xa0)
 mstore(64, _1)
 if iszero(lt(calldatasize(), 4))
 {
 switch shr(224, calldataload(0))
 case 0x00fdd58e {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
 mstore(0, and(abi_decode_address(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, 4)
 let dataSlot := keccak256(0, 64)
 mstore(0, calldataload(36))
 mstore(32, dataSlot)
 mstore(_1, sload(keccak256(0, 64)))
 return(_1, 32)
 }
 case 0x01ffc9a7 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let value := calldataload(4)
 let _2 := and(value, 0xffffffff00000000000000000000000000000000000000000000000000000000)
 if iszero(eq(value, _2)) { revert(0, 0) }
 let expr := eq(_2, 0x01ffc9a700000000000000000000000000000000000000000000000000000000)
 if iszero(expr)
 {
 expr := eq(_2, 0x0f632fb300000000000000000000000000000000000000000000000000000000)
 }
 let memPos := mload(64)
 mstore(memPos, iszero(iszero(expr)))
 return(memPos, 32)
 }
 case 0x095bcdb6 {
 if callvalue() { revert(0, 0) }
 let param, param_1, param_2 := abi_decode_addresst_uint256t_uint256(calldatasize())
 mstore(0, caller())
 mstore(0x20, 4)
 let dataSlot_1 := keccak256(0, 64)
 mstore(0, param_1)
 mstore(0x20, dataSlot_1)
 let dataSlot_2 := keccak256(0, 64)
 sstore(dataSlot_2, checked_sub_uint256( sload( dataSlot_2), param_2))
 let _3 := and(param, 0xffffffffffffffffffffffffffffffffffffffff)
 mstore(0, _3)
 mstore(0x20, 4)
 let dataSlot_3 := keccak256(0, 64)
 mstore(0, param_1)
 mstore(0x20, dataSlot_3)
 let dataSlot_4 := keccak256(0, 64)
 sstore(dataSlot_4, checked_add_uint256( sload( dataSlot_4), param_2))
 let _4 := mload(64)
 log4(_4, sub(abi_encode_address_uint256(_4, caller(), param_2), _4), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, caller(), _3, param_1)
 let memPos_1 := mload(64)
 mstore(memPos_1, 0x01)
 return(memPos_1, 0x20)
 }
 case 0x0b0d9c09 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
 let value0 := abi_decode_address()
 let value1 := abi_decode_address_40210()
 let value_1 := calldataload(68)
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let ret := signextend(15, sub(0, fun_toInt128_5750(value_1)))
 fun_accountDelta(value0, ret, caller())
 fun_transfer(value0, value1, value_1)
 return(0, 0)
 }
 case 0x11da60b4 {
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0) }
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let var := fun_settle( caller())
 let memPos_2 := mload(64)
 mstore(memPos_2, var)
 return(memPos_2, 32)
 }
 case 0x156e29f6 {
 if callvalue() { revert(0, 0) }
 let param_3, param_4, param_5 := abi_decode_addresst_uint256t_uint256(calldatasize())
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let cleaned := and(param_4, 0xffffffffffffffffffffffffffffffffffffffff)
 let ret_1 := signextend(15, sub(0, fun_toInt128_5750(param_5)))
 fun_accountDelta(cleaned, ret_1, caller())
 let _5 := and(param_3, 0xffffffffffffffffffffffffffffffffffffffff)
 mstore(0, _5)
 mstore(0x20, 4)
 let dataSlot_5 := keccak256(0, 64)
 mstore(0, cleaned)
 mstore(0x20, dataSlot_5)
 let dataSlot_6 := keccak256(0, 64)
 sstore(dataSlot_6, checked_add_uint256( sload( dataSlot_6), param_5))
 let _6 := mload(64)
 log4(_6, sub(abi_encode_address_uint256(_6, caller(), param_5), _6), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, 0, _5, cleaned)
 return(0, 0)
 }
 case 0x1e2eaeaf {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 mstore( 0, sload( calldataload(4)))
 return( 0, 32)
 }
 case 0x234266d7 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 256) { revert(0, 0) }
 let value0_1 := abi_decode_struct_PoolKey(calldatasize())
 let value_2 := calldataload(164)
 let value_3 := calldataload(196)
 let offset := calldataload(228)
 if gt(offset, 0xffffffffffffffff) { revert(0, 0) }
 let value3, value4 := abi_decode_bytes_calldata(add(4, offset), calldatasize())
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 fun_checkNotDelegateCall()
 let expr_1 := keccak256( value0_1, 160)
 mstore(0, expr_1)
 mstore(0x20, 0x06)
 let dataSlot_7 := keccak256(0, 64)
 fun_checkPoolInitialized(dataSlot_7)
 let _7 := add(value0_1, 128)
 let _8 := mload( _7)
 let cleaned_1 := and(_8, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( caller(), cleaned_1))
 {
 let var_1 := 0
 var_1 := iszero(iszero( and( _8, 0x20)))
 if var_1
 {
 let expr_mpos := mload(64)
 mstore(add(expr_mpos, 0x20), 0xb6a8b0fa00000000000000000000000000000000000000000000000000000000)
 let _9 := sub(abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(add(expr_mpos, 36), caller(), value0_1, value_2, value_3, value3, value4), expr_mpos)
 mstore(expr_mpos, add(_9, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_mpos, _9)
 pop(fun_callHook(cleaned_1, expr_mpos))
 }
 }
 let cleaned_2 := and(sload( add(dataSlot_7, 3)), 0xffffffffffffffffffffffffffffffff)
 if iszero( cleaned_2)
 {
 mstore( 0, 0xa74f97ab00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let _10 := sub(0, fun_toInt128_5750(value_2))
 let var_balanceDelta := or(shl( 128, _10), and( 0xffffffffffffffffffffffffffffffff, sub(0, fun_toInt128_5750(value_3))))
 if iszero(iszero(value_2))
 {
 let _11 := add(dataSlot_7, 1)
 sstore(_11, add( sload( _11), div(shl( 128, value_2), cleaned_2)))
 }
 if iszero(iszero(value_3))
 {
 let _12 := add(dataSlot_7, 2)
 sstore(_12, add( sload( _12), div(shl( 128, value_3), cleaned_2)))
 }
 fun_accountPoolBalanceDelta(value0_1, var_balanceDelta, caller())
 let _13 := mload(64)
 mstore(_13, value_2)
 mstore(add(_13, 0x20), value_3)
 log3(_13, 64, 0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb, expr_1, caller())
 let _14 := mload( _7)
 let cleaned_3 := and(_14, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( caller(), cleaned_3))
 {
 let var_2 := 0
 var_2 := iszero(iszero( and( _14, 16)))
 if var_2
 {
 let expr_mpos_1 := mload(64)
 mstore(add(expr_mpos_1, 0x20), 0xe1b4af6900000000000000000000000000000000000000000000000000000000)
 let _15 := sub(abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(add(expr_mpos_1, 36), caller(), value0_1, value_2, value_3, value3, value4), expr_mpos_1)
 mstore(expr_mpos_1, add(_15, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_mpos_1, _15)
 pop(fun_callHook(cleaned_3, expr_mpos_1))
 }
 }
 let memPos_3 := mload(64)
 mstore(memPos_3, var_balanceDelta)
 return(memPos_3, 0x20)
 }
 case 0x2d771389 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let value0_2 := abi_decode_address()
 require_helper_stringliteral_269d( eq( caller(), and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)))
 let _16 := and(value0_2, 0xffffffffffffffffffffffffffffffffffffffff)
 sstore( 0x02, or(and(sload( 0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), _16))
 log2( 0, 0, 0xb4bd8ef53df690b9943d3318996006dbb82a25f54719d8c8035b516a2a5b8acc, _16)
 return(0, 0)
 }
 case 0x35fd631a {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
 let value_4 := calldataload(36)
 let /// @ast-id 1319
 var_startSlot := calldataload(4)
 let usr$memptr := mload( 64)
 let usr$memptr_1 := usr$memptr
 mstore(usr$memptr, 32)
 mstore(add(usr$memptr, 32), value_4)
 usr$memptr := add(usr$memptr, 64)
 let _17 := add(usr$memptr_1, shl(5, value_4))
 let usr$end := add(_17, 64)
 for { }
 1
 { }
 {
 mstore(usr$memptr, sload(var_startSlot))
 usr$memptr := add(usr$memptr, 32)
 var_startSlot := add(var_startSlot, 1)
 if iszero(lt(usr$memptr, usr$end)) { break }
 }
 return(usr$memptr_1, add(sub(_17, usr$memptr_1), 64))
 }
 case 0x3dd45adb {
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let value0_3 := abi_decode_address()
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let _18 := fun_settle( value0_3)
 let memPos_4 := mload(64)
 mstore(memPos_4, _18)
 return(memPos_4, 32)
 }
 case 0x426a8493 {
 if callvalue() { revert(0, 0) }
 let param_6, param_7, param_8 := abi_decode_addresst_uint256t_uint256(calldatasize())
 mstore(0, caller())
 mstore(0x20, 0x05)
 let dataSlot_8 := keccak256(0, 64)
 let dataSlot_9 := 0
 mstore( 0, and( param_6, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_8)
 dataSlot_9 := keccak256( 0, 0x40)
 mstore(0, param_7)
 mstore(0x20, dataSlot_9)
 sstore(keccak256(0, 64), param_8)
 let _19 := mload(64)
 mstore(_19, param_8)
 log4(_19, 0x20, 0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7, caller(), and( param_6, 0xffffffffffffffffffffffffffffffffffffffff), param_7)
 let memPos_5 := mload(64)
 mstore(memPos_5, 0x01)
 return(memPos_5, 0x20)
 }
 case 0x48c89491 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let offset_1 := calldataload(4)
 if gt(offset_1, 0xffffffffffffffff) { revert(0, 0) }
 let value0_4, value1_1 := abi_decode_bytes_calldata(add(4, offset_1), calldatasize())
 if tload(87100234046427240614499661373387320107015461065347489303548037305558901893923)
 {
 mstore( 0, 0x5090d6c600000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 tstore( 87100234046427240614499661373387320107015461065347489303548037305558901893923, true)
 let _20 := mload(64)
 mstore(_20, 0x91dd734600000000000000000000000000000000000000000000000000000000)
 mstore( add(_20, 4), 32)
 let _21 := call(gas(), caller(), 0, _20, sub( abi_encode_bytes_calldata(value0_4, value1_1, add( _20, 36)), _20), _20, 0)
 if iszero(_21)
 {
 let pos := mload(64)
 returndatacopy(pos, 0, returndatasize())
 revert(pos, returndatasize())
 }
 let expr_mpos_2 := 0
 if _21
 {
 let _22 := returndatasize()
 returndatacopy(_20, 0, _22)
 finalize_allocation(_20, _22)
 let _23 := add(_20, _22)
 if slt(sub(_23, _20), 32) { revert(0, 0) }
 let offset_2 := mload(_20)
 if gt(offset_2, 0xffffffffffffffff) { revert(0, 0) }
 let _24 := add(_20, offset_2)
 if iszero(slt(add(_24, 0x1f), _23)) { revert(0, 0) }
 let length := mload(_24)
 if gt(length, 0xffffffffffffffff)
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert(0, 36)
 }
 let memPtr := mload(64)
 finalize_allocation(memPtr, add(and(add(length, 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), 32))
 mstore(memPtr, length)
 if gt(add(add(_24, length), 32), _23) { revert(0, 0) }
 mcopy(add(memPtr, 32), add(_24, 32), length)
 mstore(add(add(memPtr, length), 32), 0)
 expr_mpos_2 := memPtr
 }
 if iszero(iszero( tload(56671960505278111519104690822132496699113179860588238901689140059013086026251)))
 {
 mstore( 0, 0x5212cba100000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 tstore( 87100234046427240614499661373387320107015461065347489303548037305558901893923, false)
 let memPos_6 := mload(64)
 mstore(memPos_6, 32)
 let length_1 := mload(expr_mpos_2)
 mstore(add(memPos_6, 32), length_1)
 mcopy(add(memPos_6, 64), add(expr_mpos_2, 32), length_1)
 mstore(add(add(memPos_6, length_1), 64), 0)
 return(memPos_6, add(sub(add(memPos_6, and(add(length_1, 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), memPos_6), 64))
 }
 case 0x52759651 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 192) { revert(0, 0) }
 let value0_5 := abi_decode_struct_PoolKey(calldatasize())
 let value1_2 := abi_decode_uint24()
 let var_3 := eq( and(mload( add(value0_5, 64)), 0xffffff), 0x800000)
 let expr_2 := iszero( var_3)
 if var_3
 {
 expr_2 := iszero(eq( caller(), and(mload( add(value0_5, 128)), 0xffffffffffffffffffffffffffffffffffffffff)))
 }
 if expr_2
 {
 mstore( 0, 0x30d2164100000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 fun_validate(value1_2)
 mstore(0, keccak256( value0_5, 160))
 mstore(0x20, 0x06)
 let dataSlot_10 := keccak256(0, 64)
 fun_checkPoolInitialized(dataSlot_10)
 let _25 := sload( dataSlot_10)
 sstore(dataSlot_10, or(and(0xffffff000000ffffffffffffffffffffffffffffffffffffffffffffffffffff, _25), and(shl(208, value1_2), 0xffffff0000000000000000000000000000000000000000000000000000)))
 return(0, 0)
 }
 case 0x558a7297 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
 let value0_6 := abi_decode_address()
 let value_5 := 0
 value_5 := calldataload(36)
 let _26 := iszero(iszero(value_5))
 if iszero(eq(value_5, _26)) { revert(0, 0) }
 mstore(0, caller())
 mstore(32, 0x03)
 let dataSlot_11 := keccak256(0, 64)
 let dataSlot_12 := 0
 mstore( 0, and( value0_6, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_11)
 dataSlot_12 := keccak256( 0, 0x40)
 let value_6 := and(sload( dataSlot_12), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)
 sstore( dataSlot_12, or(value_6, and(_26, 255)))
 let _27 := mload(64)
 mstore(_27, _26)
 log3(_27, 32, 0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267, caller(), and( value0_6, 0xffffffffffffffffffffffffffffffffffffffff))
 let memPos_7 := mload(64)
 mstore(memPos_7, 0x01)
 return(memPos_7, 32)
 }
 case 0x598af9e7 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
 let value0_7 := abi_decode_address()
 let value1_3 := abi_decode_address_40210()
 mstore(0, and(value0_7, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, 5)
 let dataSlot_13 := keccak256(0, 64)
 let dataSlot_14 := 0
 mstore( 0, and( value1_3, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_13)
 dataSlot_14 := keccak256( 0, 0x40)
 mstore(0, calldataload(68))
 mstore(32, dataSlot_14)
 let _28 := sload(keccak256(0, 64))
 let memPos_8 := mload(64)
 mstore(memPos_8, _28)
 return(memPos_8, 32)
 }
 case 0x5a6bcfda {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 320) { revert(0, 0) }
 let value0_8 := abi_decode_struct_PoolKey(calldatasize())
 if slt(add(calldatasize(), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5c), 0x80) { revert(0, 0) }
 let memPtr_1 := mload(64)
 finalize_allocation_40225(memPtr_1)
 let value_7 := 0
 value_7 := calldataload(164)
 if iszero(eq(value_7, signextend(2, value_7))) { revert(0, 0) }
 mstore(memPtr_1, value_7)
 let value_8 := 0
 value_8 := calldataload(196)
 if iszero(eq(value_8, signextend(2, value_8))) { revert(0, 0) }
 mstore(add(memPtr_1, 32), value_8)
 mstore(add(memPtr_1, 64), calldataload(228))
 mstore(add(memPtr_1, 96), calldataload(260))
 let offset_3 := calldataload(292)
 if gt(offset_3, 0xffffffffffffffff) { revert(0, 0) }
 let value2, value3_1 := abi_decode_bytes_calldata(add(4, offset_3), calldatasize())
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 fun_checkNotDelegateCall()
 let expr_3 := keccak256( value0_8, 160)
 mstore(0, expr_3)
 mstore(32, 0x06)
 mstore(0x80, keccak256(0, 64))
 fun_checkPoolInitialized(mload(0x80))
 let _29 := mload( add(value0_8, 0x80))
 let cleaned_4 := and(_29, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( caller(), cleaned_4))
 {
 let expr_4 := sgt( mload(add(memPtr_1, 64)), 0)
 let expr_5 := expr_4
 if expr_4
 {
 let var_4 := 0
 var_4 := iszero(iszero( and( _29, 2048)))
 expr_4 := var_4
 }
 switch expr_4
 case 0 {
 let expr_6 := iszero(expr_5)
 if expr_6
 {
 let var_5 := 0
 var_5 := iszero(iszero( and( _29, 512)))
 expr_6 := var_5
 }
 if expr_6
 {
 let expr_mpos_3 := mload(64)
 mstore(add(expr_mpos_3, 32), 0x21d0ee7000000000000000000000000000000000000000000000000000000000)
 let _30 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(add(expr_mpos_3, 36), caller(), value0_8, memPtr_1, value2, value3_1), expr_mpos_3)
 mstore(expr_mpos_3, add(_30, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_mpos_3, _30)
 pop(fun_callHook(cleaned_4, expr_mpos_3))
 }
 }
 default /// @src 23:9959:10368 "if (params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)) {..."
 {
 let expr_mpos_4 := mload(64)
 mstore(add(expr_mpos_4, 32), 0x259982e500000000000000000000000000000000000000000000000000000000)
 let _31 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(add(expr_mpos_4, 36), caller(), value0_8, memPtr_1, value2, value3_1), expr_mpos_4)
 mstore(expr_mpos_4, add(_31, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_mpos_4, _31)
 pop(fun_callHook(cleaned_4, expr_mpos_4))
 }
 }
 let cleaned_5 := signextend(2, mload( memPtr_1))
 let cleaned_6 := signextend(2, mload(add(memPtr_1, 32)))
 let expr_7 := fun_toInt128( mload(add(memPtr_1, 64)))
 let cleaned_7 := signextend(2, mload( add(value0_8, 96)))
 let _32 := mload(add(memPtr_1, 96))
 let memPtr_2 := mload(64)
 let newFreePtr := add(memPtr_2, 192)
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr_2))
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert(0, 0x24)
 }
 mstore(64, newFreePtr)
 mstore(memPtr_2, caller())
 mstore( add(memPtr_2, 32), cleaned_5)
 mstore( add(memPtr_2, 64), cleaned_6)
 mstore( add(memPtr_2, 96), signextend(15, expr_7))
 mstore( add(memPtr_2, 0x80), cleaned_7)
 mstore( add(memPtr_2, 160), _32)
 let var_delta := 0
 var_delta := 0
 if iszero(slt(cleaned_5, cleaned_6))
 {
 let usr$fmp := mload( 64)
 mstore(usr$fmp, 0xc4433ed500000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp, 4), cleaned_5)
 mstore(add(usr$fmp, 0x24), cleaned_6)
 revert(usr$fmp, 0x44)
 }
 if slt(cleaned_5, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618)
 {
 mstore( 0, 0xd5e2f7ab00000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_5)
 revert( 0, 0x24)
 }
 if sgt(cleaned_6, 0x0d89e8)
 {
 mstore( 0, 0x1ad777f800000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_6)
 revert( 0, 0x24)
 }
 let memPtr_3 := mload(64)
 finalize_allocation_40225(memPtr_3)
 mstore(memPtr_3, 0)
 mstore(add(memPtr_3, 32), 0)
 mstore(add(memPtr_3, 64), 0)
 mstore(add(memPtr_3, 96), 0)
 if iszero(iszero( signextend(15, expr_7)))
 {
 let var_flipped := 0
 let var_liquidityGrossAfter := 0
 let var_upper := 0
 let _33 := add(mload(0x80), 4)
 let dataSlot_15 := 0
 mstore(0, signextend(2, cleaned_5))
 mstore(0x20, _33)
 dataSlot_15 := keccak256(0, 0x40)
 let _34 := sload( dataSlot_15)
 let cleaned_8 := and(_34, 0xffffffffffffffffffffffffffffffff)
 var_liquidityGrossAfter := fun_addDelta(cleaned_8, signextend(15, expr_7))
 let _35 := and( var_liquidityGrossAfter, 0xffffffffffffffffffffffffffffffff)
 let expr_8 := iszero( cleaned_8)
 var_flipped := iszero(eq( iszero( _35), expr_8))
 if expr_8
 {
 if iszero(sgt( cleaned_5, signextend( 2, shr( 160, sload( mload(0x80))))))
 {
 sstore( add( dataSlot_15, 1), sload( add(mload(0x80), 1)))
 sstore( add( dataSlot_15, 2), sload( add(mload(0x80), 2)))
 }
 }
 let expr_9 := 0
 var_upper := 0
 expr_9 := checked_add_int128( sar(0x80, _34), signextend(15, expr_7))
 sstore( dataSlot_15, or(_35, shl( 0x80, expr_9)))
 mstore(add(memPtr_3, 32), _35)
 mstore(memPtr_3, var_flipped)
 let var_flipped_1 := 0
 let var_liquidityGrossAfter_1 := 0
 let dataSlot_16 := 0
 mstore(0, signextend(2, cleaned_6))
 mstore(0x20, _33)
 dataSlot_16 := keccak256(0, 0x40)
 let _36 := sload( dataSlot_16)
 let cleaned_9 := and(_36, 0xffffffffffffffffffffffffffffffff)
 var_liquidityGrossAfter_1 := fun_addDelta(cleaned_9, signextend(15, expr_7))
 let expr_10 := iszero( cleaned_9)
 var_flipped_1 := iszero(eq( iszero( and( var_liquidityGrossAfter_1, 0xffffffffffffffffffffffffffffffff)), expr_10))
 if expr_10
 {
 if iszero(sgt( cleaned_6, signextend( 2, shr( 160, sload( mload(0x80))))))
 {
 sstore( add( dataSlot_16, 1), sload( add(mload(0x80), 1)))
 sstore( add( dataSlot_16, 2), sload( add(mload(0x80), 2)))
 }
 }
 let expr_11 := 0
 let diff := sub(signextend(15, sar(0x80, _36)), signextend(15, expr_7))
 if or(slt(diff, 0xffffffffffffffffffffffffffffffff80000000000000000000000000000000), sgt(diff, 0x7fffffffffffffffffffffffffffffff))
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert(0, 0x24)
 }
 expr_11 := diff
 sstore( dataSlot_16, or( and( var_liquidityGrossAfter_1, 0xffffffffffffffffffffffffffffffff), shl( 0x80, diff)))
 mstore(add(memPtr_3, 96), and( var_liquidityGrossAfter_1, 0xffffffffffffffffffffffffffffffff))
 mstore(add(memPtr_3, 64), var_flipped_1)
 if iszero(slt( signextend(15, expr_7), 0))
 {
 let cleaned_10 := signextend(2, mload( add(memPtr_2, 0x80)))
 let cleaned_11 := and(mload(add(memPtr_3, 32)), 0xffffffffffffffffffffffffffffffff)
 let _37 := and( div( 0xffffffffffffffffffffffffffffffff, add(sub(sdiv( 0x0d89e8, cleaned_10), sub(sdiv( 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618, cleaned_10), slt(smod( 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618, cleaned_10), 0))), 1)), 0xffffffffffffffffffffffffffffffff)
 if gt( cleaned_11, _37)
 {
 mstore( 0, 0xb8e3c38500000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_5)
 revert( 0, 0x24)
 }
 if gt( and(mload(add(memPtr_3, 96)), 0xffffffffffffffffffffffffffffffff), _37)
 {
 mstore( 0, 0xb8e3c38500000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_6)
 revert( 0, 0x24)
 }
 }
 if iszero(iszero(mload( memPtr_3)))
 {
 fun_flipTick( add(mload(0x80), 5), cleaned_5, signextend(2, mload( add(memPtr_2, 0x80))))
 }
 if iszero(iszero(mload(add(memPtr_3, 64))))
 {
 fun_flipTick( add(mload(0x80), 5), cleaned_6, signextend(2, mload( add(memPtr_2, 0x80))))
 }
 }
 let var_feeGrowthInside0X128 := 0
 let var_feeGrowthInside1X128 := 0
 let _38 := add(mload(0x80), 4)
 let dataSlot_17 := 0
 mstore(0, signextend(2, cleaned_5))
 mstore(0x20, _38)
 dataSlot_17 := keccak256(0, 0x40)
 let dataSlot_18 := 0
 mstore(0, signextend(2, cleaned_6))
 mstore(0x20, _38)
 dataSlot_18 := keccak256(0, 0x40)
 let var_tick := signextend( 2, shr( 160, sload( mload(0x80))))
 switch slt(var_tick, cleaned_5)
 case 0 {
 switch iszero(slt(var_tick, cleaned_6))
 case 0 {
 let _39 := sload( add(mload(0x80), 1))
 let diff_1 := sub(_39, sload( add(dataSlot_17, 1)))
 var_feeGrowthInside0X128 := sub(diff_1, sload( add(dataSlot_18, 1)))
 let _40 := sload( add(mload(0x80), 2))
 let diff_2 := sub(_40, sload( add(dataSlot_17, 2)))
 var_feeGrowthInside1X128 := sub(diff_2, sload( add(dataSlot_18, 2)))
 }
 default /// @src 29:23933:24487 "if (tickCurrent >= tickUpper) {..."
 {
 let _41 := sload( add(dataSlot_18, 1))
 var_feeGrowthInside0X128 := sub(_41, sload( add(dataSlot_17, 1)))
 let _42 := sload( add(dataSlot_18, 2))
 var_feeGrowthInside1X128 := sub(_42, sload( add(dataSlot_17, 2)))
 }
 }
 default /// @src 29:23687:24487 "if (tickCurrent < tickLower) {..."
 {
 let _43 := sload( add(dataSlot_17, 1))
 var_feeGrowthInside0X128 := sub(_43, sload( add(dataSlot_18, 1)))
 let _44 := sload( add(dataSlot_17, 2))
 var_feeGrowthInside1X128 := sub(_44, sload( add(dataSlot_18, 2)))
 }
 let cleaned_12 := and( mload( memPtr_2), 0xffffffffffffffffffffffffffffffffffffffff)
 let _45 := mload( add(memPtr_2, 160))
 let usr$fmp_1 := mload( 64)
 mstore(add(usr$fmp_1, 0x26), _45)
 mstore(add(usr$fmp_1, 0x06), cleaned_6)
 mstore(add(usr$fmp_1, 0x03), cleaned_5)
 mstore(usr$fmp_1, cleaned_12)
 let var_positionKey := keccak256(add(usr$fmp_1, 0x0c), 0x3a)
 mstore(add(usr$fmp_1, 64), 0)
 mstore(add(usr$fmp_1, 32), 0)
 mstore(usr$fmp_1, 0)
 mstore(0, var_positionKey)
 mstore(32, add(mload(0x80), 0x06))
 let dataSlot_19 := keccak256(0, 64)
 let cleaned_13 := and(sload( dataSlot_19), 0xffffffffffffffffffffffffffffffff)
 switch iszero( signextend(15, expr_7))
 case 0 {
 sstore( dataSlot_19, or(and(sload( dataSlot_19), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and( fun_addDelta(cleaned_13, signextend(15, expr_7)), 0xffffffffffffffffffffffffffffffff)))
 }
 default /// @src 30:3970:4240 "if (liquidityDelta == 0) {..."
 {
 if iszero( cleaned_13)
 {
 mstore( 0, 0xaefeb92400000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 }
 let _46 := add(dataSlot_19, 1)
 let var_feesOwed0 := fun_mulDiv_40234( sub(var_feeGrowthInside0X128, sload( _46)), cleaned_13)
 let _47 := add(dataSlot_19, 2)
 let var_feesOwed1 := fun_mulDiv_40234( sub(var_feeGrowthInside1X128, sload( _47)), cleaned_13)
 sstore(_46, var_feeGrowthInside0X128)
 sstore(_47, var_feeGrowthInside1X128)
 let expr_12 := fun_toInt128_5750(var_feesOwed0)
 let var_balanceDelta_1 := or(shl( 0x80, expr_12), and( 0xffffffffffffffffffffffffffffffff, fun_toInt128_5750(var_feesOwed1)))
 if slt( signextend(15, expr_7), 0)
 {
 if iszero(iszero(mload( memPtr_3)))
 {
 fun_clearTick(mload(0x80), cleaned_5)
 }
 if iszero(iszero(mload(add(memPtr_3, 64))))
 {
 fun_clearTick(mload(0x80), cleaned_6)
 }
 }
 if iszero(iszero( signextend(15, expr_7)))
 {
 let _48 := sload( mload(0x80))
 let expr_13 := signextend( 2, shr( 160, _48))
 let expr_14 := and( 0xffffffffffffffffffffffffffffffffffffffff, _48)
 switch slt(expr_13, cleaned_5)
 case 0 {
 switch slt(expr_13, cleaned_6)
 case 0 {
 let expr_15 := fun_getSqrtPriceAtTick(cleaned_5)
 var_delta := and( 0xffffffffffffffffffffffffffffffff, fun_toInt128( fun_getAmount1Delta(expr_15, fun_getSqrtPriceAtTick(cleaned_6), signextend(15, expr_7))))
 }
 default /// @src 29:9757:10794 "if (tick < tickUpper) {..."
 {
 let expr_16 := fun_toInt128( fun_getAmount0Delta(expr_14, fun_getSqrtPriceAtTick(cleaned_6), signextend(15, expr_7)))
 var_delta := or(shl( 0x80, expr_16), and( 0xffffffffffffffffffffffffffffffff, fun_toInt128( fun_getAmount1Delta( fun_getSqrtPriceAtTick(cleaned_5), expr_14, signextend(15, expr_7)))))
 let _49 := add(mload(0x80), 0x03)
 sstore( _49, or(and(sload( _49), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and( fun_addDelta( and(sload( _49), 0xffffffffffffffffffffffffffffffff), signextend(15, expr_7)), 0xffffffffffffffffffffffffffffffff)))
 }
 }
 default /// @src 29:9197:10794 "if (tick < tickLower) {..."
 {
 let expr_17 := fun_getSqrtPriceAtTick(cleaned_5)
 var_delta := shl( 0x80, fun_toInt128( fun_getAmount0Delta(expr_17, fun_getSqrtPriceAtTick(cleaned_6), signextend(15, expr_7))))
 }
 }
 let expr_18 := fun_toInt128( add(sar( 0x80, var_delta), sar( 0x80, var_balanceDelta_1)))
 let var_balanceDelta_2 := or(shl( 0x80, expr_18), and( 0xffffffffffffffffffffffffffffffff, fun_toInt128( add(signextend( 15, var_delta), signextend( 15, var_balanceDelta_1)))))
 let cleaned_14 := signextend(2, mload( memPtr_1))
 let cleaned_15 := signextend(2, mload(add(memPtr_1, 32)))
 let _50 := mload(add(memPtr_1, 64))
 let _51 := mload(add(memPtr_1, 96))
 let _52 := mload(64)
 mstore(_52, cleaned_14)
 mstore(add(_52, 32), cleaned_15)
 mstore(add(_52, 64), _50)
 mstore(add(_52, 96), _51)
 log3(_52, 0x80, 0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec, expr_3, caller())
 let expr_component, expr_component_1 := fun_afterModifyLiquidity( and(mload( add(value0_8, 0x80)), 0xffffffffffffffffffffffffffffffffffffffff), value0_8, memPtr_1, var_balanceDelta_2, var_balanceDelta_1, value2, value3_1)
 if iszero(iszero(expr_component_1))
 {
 fun_accountPoolBalanceDelta(value0_8, expr_component_1, and(mload( add(value0_8, 0x80)), 0xffffffffffffffffffffffffffffffffffffffff))
 }
 fun_accountPoolBalanceDelta(value0_8, expr_component, caller())
 let memPos_9 := mload(64)
 mstore(memPos_9, expr_component)
 mstore(add(memPos_9, 32), var_balanceDelta_1)
 return(memPos_9, 64)
 }
 case 0x6276cbbe {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 192) { revert(0, 0) }
 let value0_9 := abi_decode_struct_PoolKey(calldatasize())
 let value_9 := 0
 value_9 := calldataload(164)
 let _53 := and(value_9, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq(value_9, _53)) { revert(0, 0) }
 fun_checkNotDelegateCall()
 let _54 := add(value0_9, 96)
 let cleaned_16 := signextend(2, mload( _54))
 if sgt( cleaned_16, 32767)
 {
 mstore( 0, 0xb70024f800000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_16)
 revert( 0, 0x24)
 }
 let cleaned_17 := signextend(2, mload( _54))
 if slt( cleaned_17, 1)
 {
 mstore( 0, 0xe9e9058800000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_17)
 revert( 0, 0x24)
 }
 let cleaned_18 := and( mload( value0_9), 0xffffffffffffffffffffffffffffffffffffffff)
 let _55 := add(value0_9, 32)
 let cleaned_19 := and( mload( _55), 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(lt( cleaned_18, cleaned_19))
 {
 let usr$fmp_2 := mload( 64)
 mstore(usr$fmp_2, 0x6e6c983000000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp_2, 4), cleaned_18)
 mstore(add(usr$fmp_2, 0x24), cleaned_19)
 revert(usr$fmp_2, 0x44)
 }
 let _56 := add(value0_9, 128)
 let cleaned_20 := and(mload( _56), 0xffffffffffffffffffffffffffffffffffffffff)
 let _57 := add(value0_9, 64)
 if iszero( fun_isValidHookAddress(cleaned_20, and(mload( _57), 0xffffff)))
 {
 mstore( 0, 0xe65af6a000000000000000000000000000000000000000000000000000000000)
 mstore( 4, cleaned_20)
 revert( 0, 0x24)
 }
 let expr_19 := fun_getInitialLPFee( and(mload( _57), 0xffffff))
 let _58 := mload( _56)
 let cleaned_21 := and(_58, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( caller(), cleaned_21))
 {
 let var_6 := 0
 var_6 := iszero(iszero( and( _58, 8192)))
 if var_6
 {
 let expr_mpos_5 := mload(64)
 mstore(add(expr_mpos_5, 32), 0xdc98354e00000000000000000000000000000000000000000000000000000000)
 mstore( add(expr_mpos_5, 36), caller())
 abi_encode_struct_PoolKey(value0_9, add( expr_mpos_5, 68))
 mstore( add( expr_mpos_5, 228), _53)
 mstore(expr_mpos_5, 228)
 finalize_allocation(expr_mpos_5, 260)
 pop(fun_callHook(cleaned_21, expr_mpos_5))
 }
 }
 let expr_20 := keccak256( value0_9, 160)
 mstore(0, expr_20)
 mstore( 32, 0x06)
 let dataSlot_20 := keccak256(0, 64)
 if iszero(iszero( and( 0xffffffffffffffffffffffffffffffffffffffff, sload( dataSlot_20))))
 {
 mstore( 0, 0x7983c05100000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let expr_21 := fun_getTickAtSqrtPrice(value_9)
 sstore(dataSlot_20, or(or( and(shl( 160, expr_21), 0xffffff0000000000000000000000000000000000000000), _53), and(shl(208, expr_19), 0xffffff0000000000000000000000000000000000000000000000000000)))
 let cleaned_22 := and( mload( value0_9), 0xffffffffffffffffffffffffffffffffffffffff)
 let cleaned_23 := and( mload( _55), 0xffffffffffffffffffffffffffffffffffffffff)
 let cleaned_24 := and(mload( _57), 0xffffff)
 let cleaned_25 := signextend(2, mload( _54))
 let cleaned_26 := and(mload( _56), 0xffffffffffffffffffffffffffffffffffffffff)
 let _59 := mload(64)
 mstore(_59, cleaned_24)
 mstore( add(_59, 32), cleaned_25)
 mstore(add(_59, 64), cleaned_26)
 mstore( add(_59, 96), _53)
 let _60 := signextend(2, expr_21)
 mstore( add(_59, 128), _60)
 log4(_59, 160, 0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438, expr_20, cleaned_22, cleaned_23)
 let _61 := mload( _56)
 let cleaned_27 := and(_61, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( caller(), cleaned_27))
 {
 let var_7 := 0
 var_7 := iszero(iszero( and( _61, 4096)))
 if var_7
 {
 let expr_mpos_6 := mload(64)
 mstore(add(expr_mpos_6, 32), 0x6fe7e6eb00000000000000000000000000000000000000000000000000000000)
 mstore( add(expr_mpos_6, 36), caller())
 abi_encode_struct_PoolKey(value0_9, add( expr_mpos_6, 68))
 mstore( add( expr_mpos_6, 228), _53)
 mstore( add( expr_mpos_6, 260), _60)
 mstore(expr_mpos_6, 260)
 finalize_allocation(expr_mpos_6, 292)
 pop(fun_callHook(cleaned_27, expr_mpos_6))
 }
 }
 let memPos_10 := mload(64)
 mstore(memPos_10, _60)
 return(memPos_10, 32)
 }
 case 0x7e87ce7d {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 192) { revert(0, 0) }
 let value0_10 := abi_decode_struct_PoolKey(calldatasize())
 let value1_4 := abi_decode_uint24()
 if iszero(eq( caller(), and(sload( 0x02), 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 mstore( 0, 0x48f5c3ed00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 if iszero( and(lt(and(value1_4, 0xfff), 1001), lt(and(value1_4, 0xfff000), 4100096)))
 {
 mstore( 0, 0xa7abe2f700000000000000000000000000000000000000000000000000000000)
 mstore( 4, and( value1_4, 0xffffff))
 revert( 0, 0x24)
 }
 let expr_22 := keccak256( value0_10, 160)
 mstore(0, expr_22)
 mstore(0x20, 0x06)
 let dataSlot_21 := keccak256(0, 64)
 fun_checkPoolInitialized(dataSlot_21)
 let _62 := sload( dataSlot_21)
 sstore(dataSlot_21, or(and(0xffffffffffff000000ffffffffffffffffffffffffffffffffffffffffffffff, _62), and(shl(184, value1_4), 0xffffff0000000000000000000000000000000000000000000000)))
 let _63 := mload(64)
 mstore(_63, and( value1_4, 0xffffff))
 log2(_63, 0x20, 0xe9c42593e71f84403b84352cd168d693e2c9fcd1fdbcc3feb21d92b43e6696f9, expr_22)
 return(0, 0)
 }
 case 0x80f0b44c {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
 let value0_11 := abi_decode_address()
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let expr_23 := tload( fun_computeSlot( caller(), value0_11))
 let expr_24 := fun_toInt128_5750( calldataload(36))
 if iszero(eq( signextend(15, expr_24), expr_23))
 {
 mstore( 0, 0xbda73abf00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 fun_accountDelta(value0_11, signextend(15, sub(0, expr_24)), caller())
 return(0, 0)
 }
 case 0x8161b874 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
 let value0_12 := abi_decode_address()
 let value1_5 := abi_decode_address_40210()
 let value_10 := calldataload(68)
 if iszero(eq( caller(), and(sload( 0x02), 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 mstore( 0, 0x48f5c3ed00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let var_8 := 0
 let _64 := and( value1_5, 0xffffffffffffffffffffffffffffffffffffffff)
 var_8 := iszero( _64)
 let expr_25 := iszero( var_8)
 if expr_25
 {
 expr_25 := eq( and( tload(18037029214425852597980496522548842536420057720408124260691716999909707453369), 0xffffffffffffffffffffffffffffffffffffffff), _64)
 }
 if expr_25
 {
 mstore( 0, 0xc79e594800000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let expr_26 := 0
 switch iszero(value_10)
 case 0 { expr_26 := value_10 }
 default {
 mstore(0, _64)
 mstore(32, 1)
 expr_26 := sload(keccak256(0, 64))
 }
 mstore(0, _64)
 mstore(32, 1)
 let dataSlot_22 := keccak256(0, 64)
 sstore(dataSlot_22, checked_sub_uint256( sload( dataSlot_22), expr_26))
 fun_transfer(value1_5, value0_12, expr_26)
 let memPos_11 := mload(64)
 mstore(memPos_11, expr_26)
 return(memPos_11, 32)
 }
 case 0x8da5cb5b {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0) }
 let value_11 := and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)
 let memPos_12 := mload(64)
 mstore(memPos_12, value_11)
 return(memPos_12, 32)
 }
 case 0x97e8cd4e {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 mstore(0, and(abi_decode_address(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, 1)
 let _65 := sload(keccak256(0, 64))
 let memPos_13 := mload(64)
 mstore(memPos_13, _65)
 return(memPos_13, 32)
 }
 case 0x9bf6645f {
 if callvalue() { revert(0, 0) }
 let param_9, param_10 := abi_decode_array_bytes32_dyn_calldata(calldatasize())
 let usr$memptr_2 := mload( 64)
 let usr$memptr_3 := usr$memptr_2
 mstore(usr$memptr_2, 0x20)
 mstore(add(usr$memptr_2, 0x20), param_10)
 usr$memptr_2 := add(usr$memptr_2, 64)
 let _66 := add(usr$memptr_3, shl(5, param_10))
 let usr$end_1 := add(_66, 64)
 let usr$calldataptr := param_9
 for { } 1 { }
 {
 mstore(usr$memptr_2, tload(calldataload(usr$calldataptr)))
 usr$memptr_2 := add(usr$memptr_2, 0x20)
 usr$calldataptr := add(usr$calldataptr, 0x20)
 if iszero(lt(usr$memptr_2, usr$end_1)) { break }
 }
 return(usr$memptr_3, add(sub(_66, usr$memptr_3), 64))
 }
 case 0xa5841194 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let value0_13 := abi_decode_address()
 let var_9 := 0
 let _67 := and( value0_13, 0xffffffffffffffffffffffffffffffffffffffff)
 var_9 := iszero( _67)
 switch var_9
 case 0 {
 let _68 := fun_balanceOfSelf(value0_13)
 tstore(18037029214425852597980496522548842536420057720408124260691716999909707453369, _67)
 tstore(13582234132832961652756477188584847927179359657859594952372729441197434191253, _68)
 }
 default /// @src 6:12902:13243 "if (currency.isAddressZero()) {..."
 {
 tstore(18037029214425852597980496522548842536420057720408124260691716999909707453369, 0)
 }
 return(0, 0)
 }
 case 0xb6363cf2 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
 let value0_14 := abi_decode_address()
 let value1_6 := abi_decode_address_40210()
 mstore(0, and(value0_14, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, 3)
 let dataSlot_23 := keccak256(0, 64)
 let dataSlot_24 := 0
 mstore( 0, and( value1_6, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_23)
 dataSlot_24 := keccak256( 0, 0x40)
 let value_12 := and(sload( dataSlot_24), 0xff)
 let memPos_14 := mload(64)
 mstore(memPos_14, iszero(iszero(value_12)))
 return(memPos_14, 32)
 }
 case 0xdbd035ff {
 if callvalue() { revert(0, 0) }
 let param_11, param_12 := abi_decode_array_bytes32_dyn_calldata(calldatasize())
 let usr$memptr_4 := mload( 64)
 let usr$memptr_5 := usr$memptr_4
 mstore(usr$memptr_4, 0x20)
 mstore(add(usr$memptr_4, 0x20), param_12)
 usr$memptr_4 := add(usr$memptr_4, 64)
 let _69 := add(usr$memptr_5, shl(5, param_12))
 let usr$end_2 := add(_69, 64)
 let usr$calldataptr_1 := param_11
 for { } 1 { }
 {
 mstore(usr$memptr_4, sload(calldataload(usr$calldataptr_1)))
 usr$memptr_4 := add(usr$memptr_4, 0x20)
 usr$calldataptr_1 := add(usr$calldataptr_1, 0x20)
 if iszero(lt(usr$memptr_4, usr$end_2)) { break }
 }
 return(usr$memptr_5, add(sub(_69, usr$memptr_5), 64))
 }
 case 0xf02de3b2 {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0) }
 let value_13 := and(sload( 2), 0xffffffffffffffffffffffffffffffffffffffff)
 let memPos_15 := mload(64)
 mstore(memPos_15, value_13)
 return(memPos_15, 32)
 }
 case 0xf135baaa {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 mstore( 0, tload( calldataload(4)))
 return( 0, 32)
 }
 case 0xf2fde38b {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let value0_15 := abi_decode_address()
 let _70 := sload(0)
 require_helper_stringliteral_269d( eq( caller(), and(_70, 0xffffffffffffffffffffffffffffffffffffffff)))
 let _71 := and(value0_15, 0xffffffffffffffffffffffffffffffffffffffff)
 sstore(0, or(and(_70, 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), _71))
 log3( 0, 0, 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0, caller(), _71)
 return(0, 0)
 }
 case 0xf3cd914c {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 288) { revert(0, 0) }
 let value0_16 := abi_decode_struct_PoolKey(calldatasize())
 if slt(add(calldatasize(), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5c), 0x60) { revert(0, 0) }
 let memPtr_4 := mload(64)
 finalize_allocation_40253(memPtr_4)
 let value_14 := 0
 value_14 := calldataload(164)
 if iszero(eq(value_14, iszero(iszero(value_14)))) { revert(0, 0) }
 mstore(memPtr_4, value_14)
 let _72 := add(memPtr_4, 32)
 mstore(_72, calldataload(196))
 let value_15 := 0
 value_15 := calldataload(228)
 if iszero(eq(value_15, and(value_15, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
 let _73 := add(memPtr_4, 64)
 mstore(_73, value_15)
 let offset_4 := calldataload(260)
 if gt(offset_4, 0xffffffffffffffff) { revert(0, 0) }
 let value2_1, value3_2 := abi_decode_bytes_calldata(add(4, offset_4), calldatasize())
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 fun_checkNotDelegateCall()
 if iszero( mload( _72))
 {
 mstore( 0, 0xbe8b850700000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let expr_27 := keccak256( value0_16, 160)
 mstore(0, expr_27)
 mstore(32, 0x06)
 let dataSlot_25 := keccak256(0, 64)
 fun_checkPoolInitialized(dataSlot_25)
 let _74 := add(value0_16, 128)
 let expr_component_2, expr_component_3, expr_component_4 := fun_beforeSwap( and(mload( _74), 0xffffffffffffffffffffffffffffffffffffffff), value0_16, memPtr_4, value2_1, value3_2)
 let cleaned_28 := signextend(2, mload( add(value0_16, 0x60)))
 let cleaned_29 := iszero(iszero(mload( memPtr_4)))
 let cleaned_30 := and(mload( _73), 0xffffffffffffffffffffffffffffffffffffffff)
 let memPtr_5 := mload(64)
 finalize_allocation_40256(memPtr_5)
 mstore(memPtr_5, expr_component_2)
 mstore( add(memPtr_5, 32), cleaned_28)
 mstore( add(memPtr_5, 64), cleaned_29)
 mstore( add(memPtr_5, 0x60), cleaned_30)
 mstore( add(memPtr_5, 128), and(expr_component_4, 0xffffff))
 let cleaned_31 := iszero(iszero(mload( memPtr_4)))
 let expr_28 := 0
 switch cleaned_31
 case 0 {
 expr_28 := and( mload( add(value0_16, 32)), 0xffffffffffffffffffffffffffffffffffffffff)
 }
 default /// @src 6:10554:10603 "params.zeroForOne ? key.currency0 : key.currency1"
 {
 expr_28 := and( mload( value0_16), 0xffffffffffffffffffffffffffffffffffffffff)
 }
 let expr_component_5, expr_component_6, expr_component_7, expr_component_mpos := fun_swap(dataSlot_25, memPtr_5)
 if iszero(iszero(expr_component_6))
 {
 mstore(0, and(expr_28, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, 1)
 let dataSlot_26 := keccak256(0, 64)
 sstore(dataSlot_26, add( sload( dataSlot_26), expr_component_6))
 }
 let cleaned_32 := and(mload( expr_component_mpos), 0xffffffffffffffffffffffffffffffffffffffff)
 let cleaned_33 := and(mload( add(expr_component_mpos, 64)), 0xffffffffffffffffffffffffffffffff)
 let cleaned_34 := signextend(2, mload( add(expr_component_mpos, 32)))
 let _75 := mload(64)
 mstore(_75, signextend( 15, sar( 128, expr_component_5)))
 mstore(add(_75, 32), signextend(15, expr_component_5))
 mstore(add(_75, 64), cleaned_32)
 mstore(add(_75, 0x60), cleaned_33)
 mstore(add(_75, 128), cleaned_34)
 mstore( add(_75, 160), and( expr_component_7, 0xffffff))
 log3(_75, 192, 0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f, expr_27, caller())
 let expr_component_8, expr_component_9 := fun_afterSwap( and(mload( _74), 0xffffffffffffffffffffffffffffffffffffffff), value0_16, memPtr_4, expr_component_5, value2_1, value3_2, expr_component_3)
 if iszero(iszero(expr_component_9))
 {
 fun_accountPoolBalanceDelta(value0_16, expr_component_9, and(mload( _74), 0xffffffffffffffffffffffffffffffffffffffff))
 }
 fun_accountPoolBalanceDelta(value0_16, expr_component_8, caller())
 let memPos_16 := mload(64)
 mstore(memPos_16, expr_component_8)
 return(memPos_16, 32)
 }
 case 0xf5298aca {
 if callvalue() { revert(0, 0) }
 let param_13, param_14, param_15 := abi_decode_addresst_uint256t_uint256(calldatasize())
 if iszero( tload(87100234046427240614499661373387320107015461065347489303548037305558901893923))
 {
 mstore( 0, 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 4)
 }
 let cleaned_35 := and(param_14, 0xffffffffffffffffffffffffffffffffffffffff)
 let expr_29 := fun_toInt128_5750(param_15)
 fun_accountDelta(cleaned_35, expr_29, caller())
 let _76 := and( param_13, 0xffffffffffffffffffffffffffffffffffffffff)
 let expr_30 := iszero(eq( _76, caller()))
 if expr_30
 {
 mstore(0, _76)
 mstore(0x20, 0x03)
 let dataSlot_27 := keccak256(0, 64)
 let dataSlot_28 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_27)
 dataSlot_28 := keccak256( 0, 0x40)
 expr_30 := iszero( and(sload( dataSlot_28), 0xff))
 }
 if expr_30
 {
 mstore(0, _76)
 mstore(0x20, 0x05)
 let dataSlot_29 := keccak256(0, 64)
 let dataSlot_30 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_29)
 dataSlot_30 := keccak256( 0, 0x40)
 mstore(0, cleaned_35)
 mstore(0x20, dataSlot_30)
 let _77 := sload(keccak256(0, 64))
 if iszero(eq(_77, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
 {
 let expr_31 := checked_sub_uint256(_77, param_15)
 mstore(0, _76)
 mstore(0x20, 0x05)
 let dataSlot_31 := keccak256(0, 64)
 let dataSlot_32 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_31)
 dataSlot_32 := keccak256( 0, 0x40)
 mstore(0, cleaned_35)
 mstore(0x20, dataSlot_32)
 sstore(keccak256(0, 64), expr_31)
 }
 }
 mstore(0, _76)
 mstore(0x20, 4)
 let dataSlot_33 := keccak256(0, 64)
 mstore(0, cleaned_35)
 mstore(0x20, dataSlot_33)
 let dataSlot_34 := keccak256(0, 64)
 sstore(dataSlot_34, checked_sub_uint256( sload( dataSlot_34), param_15))
 let _78 := mload(64)
 log4(_78, sub(abi_encode_address_uint256(_78, caller(), param_15), _78), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, _76, 0, cleaned_35)
 return(0, 0)
 }
 case 0xfe99049a {
 if callvalue() { revert(0, 0) }
 if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 128) { revert(0, 0) }
 let value0_17 := abi_decode_address()
 let value1_7 := abi_decode_address_40210()
 let value_16 := calldataload(68)
 let value_17 := calldataload(100)
 let _79 := and( value0_17, 0xffffffffffffffffffffffffffffffffffffffff)
 let expr_32 := iszero(eq( caller(), _79))
 if expr_32
 {
 mstore(0, _79)
 mstore(32, 0x03)
 let dataSlot_35 := keccak256(0, 64)
 let dataSlot_36 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_35)
 dataSlot_36 := keccak256( 0, 0x40)
 expr_32 := iszero( and(sload( dataSlot_36), 0xff))
 }
 if expr_32
 {
 mstore(0, _79)
 mstore(32, 0x05)
 let dataSlot_37 := keccak256(0, 64)
 let dataSlot_38 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_37)
 dataSlot_38 := keccak256( 0, 0x40)
 mstore(0, value_16)
 mstore(32, dataSlot_38)
 let _80 := sload(keccak256(0, 64))
 if iszero(eq(_80, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
 {
 let expr_33 := checked_sub_uint256(_80, value_17)
 mstore(0, _79)
 mstore(32, 0x05)
 let dataSlot_39 := keccak256(0, 64)
 let dataSlot_40 := 0
 mstore( 0, and( caller(), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(0x20, dataSlot_39)
 dataSlot_40 := keccak256( 0, 0x40)
 mstore(0, value_16)
 mstore(32, dataSlot_40)
 sstore(keccak256(0, 64), expr_33)
 }
 }
 mstore(0, _79)
 mstore(32, 4)
 let dataSlot_41 := keccak256(0, 64)
 mstore(0, value_16)
 mstore(32, dataSlot_41)
 let dataSlot_42 := keccak256(0, 64)
 sstore(dataSlot_42, checked_sub_uint256( sload( dataSlot_42), value_17))
 let _81 := and(value1_7, 0xffffffffffffffffffffffffffffffffffffffff)
 mstore(0, _81)
 mstore(32, 4)
 let dataSlot_43 := keccak256(0, 64)
 mstore(0, value_16)
 mstore(32, dataSlot_43)
 let dataSlot_44 := keccak256(0, 64)
 sstore(dataSlot_44, checked_add_uint256( sload( dataSlot_44), value_17))
 let _82 := mload(64)
 log4(_82, sub(abi_encode_address_uint256(_82, caller(), value_17), _82), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, _79, _81, value_16)
 let memPos_17 := mload(64)
 mstore(memPos_17, 1)
 return(memPos_17, 32)
 }
 }
 revert(0, 0)
 }
 function abi_decode_address() -> value
 {
 value := calldataload(4)
 if iszero(eq(value, and(value, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
 }
 function abi_decode_address_40210() -> value
 {
 value := calldataload(36)
 if iszero(eq(value, and(value, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
 }
 function abi_decode_addresst_uint256t_uint256(dataEnd) -> value0, value1, value2
 {
 if slt(add(dataEnd, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
 let value := 0
 value := calldataload(4)
 if iszero(eq(value, and(value, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
 value0 := value
 value1 := calldataload(36)
 value2 := calldataload(68)
 }
 function finalize_allocation_40225(memPtr)
 {
 let newFreePtr := add(memPtr, 0x80)
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert( 0, 0x24)
 }
 mstore(64, newFreePtr)
 }
 function finalize_allocation_40253(memPtr)
 {
 let newFreePtr := add(memPtr, 0x60)
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert( 0, 0x24)
 }
 mstore(64, newFreePtr)
 }
 function finalize_allocation_40256(memPtr)
 {
 let newFreePtr := add(memPtr, 160)
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert( 0, 0x24)
 }
 mstore(64, newFreePtr)
 }
 function finalize_allocation(memPtr, size)
 {
 let newFreePtr := add(memPtr, and(add(size, 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert( 0, 0x24)
 }
 mstore(64, newFreePtr)
 }
 function abi_decode_uint24() -> value
 {
 value := calldataload(164)
 if iszero(eq(value, and(value, 0xffffff))) { revert(0, 0) }
 }
 function abi_decode_struct_PoolKey(end) -> value
 {
 if slt(add(end, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0xa0) { revert(0, 0) }
 let memPtr := mload(64)
 finalize_allocation_40256(memPtr)
 value := memPtr
 let value_1 := 0
 value_1 := calldataload(4)
 if iszero(eq(value_1, and(value_1, 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 revert( 0, 0)
 }
 mstore(memPtr, value_1)
 let value_2 := 0
 value_2 := calldataload(36)
 if iszero(eq(value_2, and(value_2, 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 revert( 0, 0)
 }
 mstore(add(memPtr, 32), value_2)
 let value_3 := 0
 value_3 := calldataload(68)
 if iszero(eq(value_3, and(value_3, 0xffffff)))
 {
 revert( 0, 0)
 }
 mstore(add(memPtr, 64), value_3)
 let value_4 := 0
 value_4 := calldataload(100)
 if iszero(eq(value_4, signextend(2, value_4)))
 {
 revert( 0, 0)
 }
 mstore(add(memPtr, 96), value_4)
 let value_5 := calldataload(132)
 if iszero(eq(value_5, and(value_5, 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 revert( 0, 0)
 }
 mstore(add(memPtr, 128), value_5)
 }
 function abi_decode_bytes_calldata(offset, end) -> arrayPos, length
 {
 if iszero(slt(add(offset, 0x1f), end)) { revert(0, 0) }
 length := calldataload(offset)
 if gt(length, 0xffffffffffffffff) { revert(0, 0) }
 arrayPos := add(offset, 0x20)
 if gt(add(add(offset, length), 0x20), end) { revert(0, 0) }
 }
 function abi_decode_array_bytes32_dyn_calldata(dataEnd) -> value0, value1
 {
 if slt(add(dataEnd, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
 let offset := calldataload(4)
 if gt(offset, 0xffffffffffffffff) { revert(0, 0) }
 if iszero(slt(add(offset, 35), dataEnd))
 {
 revert( 0, 0)
 }
 let length := calldataload(add(4, offset))
 if gt(length, 0xffffffffffffffff)
 {
 revert( 0, 0)
 }
 if gt(add(add(offset, shl(5, length)), 36), dataEnd)
 {
 revert( 0, 0)
 }
 value0 := add(offset, 36)
 value1 := length
 }
 function checked_sub_uint256(x, y) -> diff
 {
 diff := sub(x, y)
 if gt(diff, x)
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert(0, 0x24)
 }
 }
 function checked_add_uint256(x, y) -> sum
 {
 sum := add(x, y)
 if gt(x, sum)
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert(0, 0x24)
 }
 }
 function abi_encode_address_uint256(headStart, value0, value1) -> tail
 {
 tail := add(headStart, 64)
 mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(add(headStart, 32), value1)
 }
 function require_helper_stringliteral_269d(condition)
 {
 if iszero(condition)
 {
 let memPtr := mload(64)
 mstore(memPtr, 0x08c379a000000000000000000000000000000000000000000000000000000000)
 mstore(add(memPtr, 4), 32)
 mstore(add(memPtr, 36), 12)
 mstore(add(memPtr, 68), "UNAUTHORIZED")
 revert(memPtr, 100)
 }
 }
 function abi_encode_bytes_calldata(start, length, pos) -> end
 {
 mstore(pos, length)
 calldatacopy(add(pos, 0x20), start, length)
 mstore(add(add(pos, length), 0x20), 0)
 end := add(add(pos, and(add(length, 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), 0x20)
 }
 function fun_toInt128_5750(var_x) -> var
 {
 if iszero(lt(var_x, 0x80000000000000000000000000000000))
 {
 mstore(0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert(0, 0x04)
 }
 var := signextend(15, var_x)
 }
 function fun_accountDelta(var_currency, var_delta, var_target)
 {
 let _1 := signextend(15, var_delta)
 if iszero( _1)
 {
 leave
 }
 let expr := fun_computeSlot(var_target, var_currency)
 let var_previous := tload(expr)
 let expr_1 := checked_add_int256(var_previous, _1)
 tstore(expr, expr_1)
 switch iszero(expr_1)
 case 0 {
 if iszero(var_previous)
 {
 tstore(56671960505278111519104690822132496699113179860588238901689140059013086026251, add(tload(56671960505278111519104690822132496699113179860588238901689140059013086026251), 1))
 }
 }
 default /// @src 6:16754:16902 "if (next == 0) {..."
 {
 tstore(56671960505278111519104690822132496699113179860588238901689140059013086026251, add(tload(56671960505278111519104690822132496699113179860588238901689140059013086026251), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
 }
 }
 function fun_transfer(var_currency, var_to, var_amount)
 {
 let var := 0
 let _1 := and( var_currency, 0xffffffffffffffffffffffffffffffffffffffff)
 var := iszero( _1)
 switch var
 case 0 {
 let usr$fmp := mload(0x40)
 mstore(usr$fmp, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp, 4), and(var_to, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(add(usr$fmp, 36), var_amount)
 let var_success := and(or(and(eq(mload( 0), 1), gt(returndatasize(), 31)), iszero(returndatasize())), call(gas(), var_currency, 0, usr$fmp, 68, 0, 32))
 mstore(usr$fmp, 0)
 mstore(add(usr$fmp, 32), 0)
 mstore(add(usr$fmp, 0x40), 0)
 if iszero(var_success)
 {
 let usr$encodedDataSize := and(add(returndatasize(), 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
 let usr$fmp_1 := mload( 0x40)
 mstore(usr$fmp_1, 0x90bfb86500000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp_1, 4), _1)
 mstore(add(usr$fmp_1, 36), 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp_1, 68), 0x80)
 mstore(add(usr$fmp_1, 0x64), add(0xa0, usr$encodedDataSize))
 mstore(add(usr$fmp_1, 0x84), returndatasize())
 returndatacopy(add(usr$fmp_1, 0xa4), 0, returndatasize())
 let _2 := add(usr$fmp_1, usr$encodedDataSize)
 mstore(add(_2, 0xa4), 4)
 mstore(add(_2, 0xc4), 0xf27f64e400000000000000000000000000000000000000000000000000000000)
 revert(usr$fmp_1, add(0xe4, usr$encodedDataSize))
 }
 }
 default /// @src 40:1765:4339 "if (currency.isAddressZero()) {..."
 {
 if iszero( call(gas(), var_to, var_amount, 0, 0, 0, 0))
 {
 let usr$encodedDataSize_1 := and(add(returndatasize(), 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
 let usr$fmp_2 := mload(0x40)
 mstore(usr$fmp_2, 0x90bfb86500000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp_2, 0x04), and(var_to, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(add(usr$fmp_2, 0x24), 0)
 mstore(add(usr$fmp_2, 0x44), 0x80)
 mstore(add(usr$fmp_2, 0x64), add(0xa0, usr$encodedDataSize_1))
 mstore(add(usr$fmp_2, 0x84), returndatasize())
 returndatacopy(add(usr$fmp_2, 0xa4), 0, returndatasize())
 let _3 := add(usr$fmp_2, usr$encodedDataSize_1)
 mstore(add(_3, 0xa4), 0x04)
 mstore(add(_3, 0xc4), 0xf4b3b1bc00000000000000000000000000000000000000000000000000000000)
 revert(usr$fmp_2, add(0xe4, usr$encodedDataSize_1))
 }
 }
 }
 function fun_settle(var_recipient) -> var_paid
 {
 var_paid := 0
 let expr := tload(18037029214425852597980496522548842536420057720408124260691716999909707453369)
 let var := 0
 var := iszero( and( expr, 0xffffffffffffffffffffffffffffffffffffffff))
 switch var
 case 0 {
 if iszero(iszero( callvalue()))
 {
 mstore( 0, 0xb0ec849e00000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 var_paid := checked_sub_uint256( fun_balanceOfSelf(expr), tload(13582234132832961652756477188584847927179359657859594952372729441197434191253))
 tstore( 18037029214425852597980496522548842536420057720408124260691716999909707453369, 0)
 }
 default /// @src 6:15912:16406 "if (currency.isAddressZero()) {..."
 {
 var_paid := callvalue()
 }
 fun_accountDelta(expr, fun_toInt128_5750(var_paid), var_recipient)
 }
 function fun_checkNotDelegateCall()
 {
 if iszero(eq( address(), and( loadimmutable("1375"), 0xffffffffffffffffffffffffffffffffffffffff)))
 {
 mstore(0, 0x0d89438e00000000000000000000000000000000000000000000000000000000)
 revert(0, 0x04)
 }
 }
 function fun_checkPoolInitialized(var_self_5326_slot)
 {
 if iszero( and(1461501637330902918203684832716283019655932542975, sload( var_self_5326_slot)))
 {
 mstore( 0, 0x486aa30700000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 }
 function abi_encode_struct_PoolKey(value, pos)
 {
 mstore(pos, and( mload(value), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore( add(pos, 0x20), and( mload(add(value, 0x20)), 0xffffffffffffffffffffffffffffffffffffffff))
 mstore( add(pos, 0x40), and( mload(add(value, 0x40)), 0xffffff))
 mstore( add(pos, 0x60), signextend(2, mload(add(value, 0x60))))
 mstore( add(pos, 0x80), and( mload(add(value, 0x80)), 0xffffffffffffffffffffffffffffffffffffffff))
 }
 function abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(headStart, value0, value1, value2, value3, value4, value5) -> tail
 {
 mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
 abi_encode_struct_PoolKey(value1, add(headStart, 32))
 mstore( add(headStart, 192), value2)
 mstore( add(headStart, 224), value3)
 mstore(add(headStart, 256), 288)
 tail := abi_encode_bytes_calldata(value4, value5, add(headStart, 288))
 }
 function fun_accountPoolBalanceDelta(var_key_mpos, var_delta, var_target)
 {
 let cleaned := and( mload( var_key_mpos), 0xffffffffffffffffffffffffffffffffffffffff)
 fun_accountDelta(cleaned, sar(128, var_delta), var_target)
 let cleaned_1 := and( mload( add(var_key_mpos, 32)), 0xffffffffffffffffffffffffffffffffffffffff)
 fun_accountDelta(cleaned_1, signextend(15, var_delta), var_target)
 }
 function fun_validate(var_self)
 {
 let cleaned := and(var_self, 0xffffff)
 if gt(cleaned, 0x0f4240)
 {
 mstore( 0, 0x1400211300000000000000000000000000000000000000000000000000000000)
 mstore(0x04, cleaned)
 revert( 0, 0x24)
 }
 }
 function abi_encode_struct_ModifyLiquidityParams(value, pos)
 {
 mstore(pos, signextend(2, mload(value)))
 mstore( add(pos, 0x20), signextend(2, mload(add(value, 0x20))))
 mstore( add(pos, 0x40), mload(add(value, 0x40)))
 mstore( add(pos, 0x60), mload(add(value, 0x60)))
 }
 function abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(headStart, value0, value1, value2, value3, value4) -> tail
 {
 mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
 abi_encode_struct_PoolKey(value1, add(headStart, 32))
 abi_encode_struct_ModifyLiquidityParams(value2, add(headStart, 192))
 mstore(add(headStart, 320), 352)
 tail := abi_encode_bytes_calldata(value3, value4, add(headStart, 352))
 }
 function fun_toInt128(var_x) -> var_y
 {
 var_y := signextend(15, var_x)
 if iszero(eq( var_y, var_x))
 {
 mstore(0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert(0, 0x04)
 }
 }
 function abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(headStart, value0, value1, value2, value3, value4, value5, value6) -> tail
 {
 mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
 abi_encode_struct_PoolKey(value1, add(headStart, 32))
 abi_encode_struct_ModifyLiquidityParams(value2, add(headStart, 192))
 mstore( add(headStart, 320), value3)
 mstore( add(headStart, 352), value4)
 mstore(add(headStart, 384), 416)
 tail := abi_encode_bytes_calldata(value5, value6, add(headStart, 416))
 }
 function fun_afterModifyLiquidity(var_self_3029_address, var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length) -> var_callerDelta, var_hookDelta
 {
 var_hookDelta := 0
 if eq( caller(), and( var_self_3029_address, 0xffffffffffffffffffffffffffffffffffffffff))
 {
 var_callerDelta := var_delta
 var_hookDelta := 0
 leave
 }
 var_callerDelta := var_delta
 switch sgt( mload( add(var_params_3035_mpos, 64)), 0)
 case 0 {
 let var := 0
 var := iszero(iszero( and( var_self_3029_address, 256)))
 if var
 {
 let expr_3133_mpos := mload( 64)
 mstore(add(expr_3133_mpos, 0x20), 0x6c2bbe7e00000000000000000000000000000000000000000000000000000000)
 let _1 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(add(expr_3133_mpos, 36), caller(), var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length), expr_3133_mpos)
 mstore(expr_3133_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_3133_mpos, _1)
 let var_1 := 0
 var_1 := iszero(iszero( and( var_self_3029_address, 1)))
 var_hookDelta := fun_callHookWithReturnDelta(var_self_3029_address, expr_3133_mpos, var_1)
 var_callerDelta := fun_sub(var_delta, var_hookDelta)
 }
 }
 default /// @src 23:10893:12023 "if (params.liquidityDelta > 0) {..."
 {
 let var_2 := 0
 var_2 := iszero(iszero( and( var_self_3029_address, 1024)))
 if var_2
 {
 let expr_3094_mpos := mload( 64)
 mstore(add(expr_3094_mpos, 0x20), 0x9f063efc00000000000000000000000000000000000000000000000000000000)
 let _2 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(add(expr_3094_mpos, 36), caller(), var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length), expr_3094_mpos)
 mstore(expr_3094_mpos, add(_2, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_3094_mpos, _2)
 let var_3 := 0
 var_3 := iszero(iszero( and( var_self_3029_address, 2)))
 var_hookDelta := fun_callHookWithReturnDelta(var_self_3029_address, expr_3094_mpos, var_3)
 var_callerDelta := fun_sub(var_callerDelta, var_hookDelta)
 }
 }
 }
 function fun_isValidHookAddress(var_self_2668_address, var_fee) -> var_
 {
 var_ := 0
 let var := 0
 var := iszero(iszero( and( var_self_2668_address, 128)))
 let expr := iszero( var)
 if expr
 {
 let var_1 := 0
 var_1 := iszero(iszero( and( var_self_2668_address, 8)))
 expr := var_1
 }
 if expr
 {
 var_ := 0
 leave
 }
 let var_2 := 0
 var_2 := iszero(iszero( and( var_self_2668_address, 64)))
 let expr_1 := iszero( var_2)
 if expr_1
 {
 let var_3 := 0
 var_3 := iszero(iszero( and( var_self_2668_address, 4)))
 expr_1 := var_3
 }
 if expr_1
 {
 var_ := 0
 leave
 }
 let var_4 := 0
 var_4 := iszero(iszero( and( var_self_2668_address, 1024)))
 let expr_2 := iszero( var_4)
 if expr_2
 {
 let var_5 := 0
 var_5 := iszero(iszero( and( var_self_2668_address, 2)))
 expr_2 := var_5
 }
 if expr_2
 {
 var_ := 0
 leave
 }
 let var_6 := 0
 var_6 := iszero(iszero( and( var_self_2668_address, 256)))
 let expr_3 := iszero( var_6)
 if expr_3
 {
 let var_7 := 0
 var_7 := iszero(iszero( and( var_self_2668_address, 1)))
 expr_3 := var_7
 }
 if expr_3
 {
 var_ := 0
 leave
 }
 let expr_4 := 0
 switch iszero( and( var_self_2668_address, 0xffffffffffffffffffffffffffffffffffffffff))
 case 0 {
 let _1 := iszero( and( var_self_2668_address, 0x3fff))
 let expr_5 := iszero(_1)
 if _1
 {
 expr_5 := eq( and( var_fee, 0xffffff), 0x800000)
 }
 expr_4 := expr_5
 }
 default {
 expr_4 := iszero( eq( and( var_fee, 0xffffff), 0x800000))
 }
 var_ := expr_4
 }
 function fun_getInitialLPFee(var_self) -> var
 {
 var := 0
 if eq( and( var_self, 0xffffff), 0x800000)
 {
 var := 0
 leave
 }
 fun_validate(var_self)
 var := var_self
 }
 function fun_balanceOfSelf(var_currency) -> var
 {
 var := 0
 let var_1 := 0
 let _1 := and( var_currency, 0xffffffffffffffffffffffffffffffffffffffff)
 var_1 := iszero( _1)
 switch var_1
 case 0 {
 let _2 := mload(64)
 mstore(_2, 0x70a0823100000000000000000000000000000000000000000000000000000000)
 mstore( add(_2, 4), address())
 let _3 := staticcall(gas(), _1, _2, 36, _2, 32)
 if iszero(_3)
 {
 let pos := mload(64)
 returndatacopy(pos, 0, returndatasize())
 revert(pos, returndatasize())
 }
 let expr := 0
 if _3
 {
 let _4 := 32
 if gt( 32, returndatasize()) { _4 := returndatasize() }
 finalize_allocation(_2, _4)
 if slt(sub( add(_2, _4), _2), 32) { revert(0, 0) }
 expr := mload(_2)
 }
 var := expr
 leave
 }
 default /// @src 40:4435:4621 "if (currency.isAddressZero()) {..."
 {
 var := selfbalance()
 leave
 }
 }
 function abi_encode_struct_SwapParams(value, pos)
 {
 mstore(pos, iszero(iszero( mload(value))))
 mstore( add(pos, 0x20), mload(add(value, 0x20)))
 mstore( add(pos, 0x40), and( mload(add(value, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
 }
 function checked_add_int256(x, y) -> sum
 {
 sum := add(x, y)
 let _1 := slt(sum, y)
 let _2 := slt(x, 0)
 if or(and(iszero(_2), _1), and(_2, iszero(_1)))
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert( 0, 0x24)
 }
 }
 function fun_beforeSwap(var_self_3157_address, var_key_3160_mpos, var_params_3163_mpos, var_hookData_3165_offset, var_hookData_3165_length) -> var_amountToSwap, var_hookReturn, var_lpFeeOverride
 {
 var_hookReturn := 0
 var_lpFeeOverride := 0
 var_amountToSwap := mload( add(var_params_3163_mpos, 32))
 if eq( caller(), and( var_self_3157_address, 0xffffffffffffffffffffffffffffffffffffffff))
 {
 var_amountToSwap := var_amountToSwap
 var_hookReturn := 0
 var_lpFeeOverride := 0
 leave
 }
 let var := 0
 var := iszero(iszero( and( var_self_3157_address, 128)))
 if var
 {
 let expr_3212_mpos := mload(64)
 mstore(add(expr_3212_mpos, 32), 0x575e24b400000000000000000000000000000000000000000000000000000000)
 mstore( add(expr_3212_mpos, 36), caller())
 abi_encode_struct_PoolKey(var_key_3160_mpos, add( expr_3212_mpos, 68))
 abi_encode_struct_SwapParams(var_params_3163_mpos, add( expr_3212_mpos, 228))
 mstore(add( expr_3212_mpos, 324), 320)
 let _1 := sub( abi_encode_bytes_calldata(var_hookData_3165_offset, var_hookData_3165_length, add( expr_3212_mpos, 356)), expr_3212_mpos)
 mstore(expr_3212_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_3212_mpos, _1)
 let expr_3213_mpos := fun_callHook(var_self_3157_address, expr_3212_mpos)
 if iszero(eq( mload( expr_3213_mpos), 0x60))
 {
 mstore( 0, 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 if eq( and(mload( add(var_key_3160_mpos, 64)), 0xffffff), 0x800000)
 {
 var_lpFeeOverride := mload(add( expr_3213_mpos, 0x60))
 }
 let var_1 := 0
 var_1 := iszero(iszero( and( var_self_3157_address, 8)))
 if var_1
 {
 var_hookReturn := mload(add( expr_3213_mpos, 64))
 let _2 := signextend(15, sar( 0x80, var_hookReturn))
 if iszero(iszero( _2))
 {
 let expr := slt(var_amountToSwap, 0)
 var_amountToSwap := checked_add_int256(var_amountToSwap, _2)
 let expr_1 := 0
 switch expr
 case 0 {
 expr_1 := slt(var_amountToSwap, 0)
 }
 default /// @src 23:13888:13936 "exactInput ? amountToSwap > 0 : amountToSwap < 0"
 {
 expr_1 := sgt(var_amountToSwap, 0)
 }
 if expr_1
 {
 mstore( 0, 0xfa0b71d600000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 }
 }
 }
 }
 function checked_add_int128(x, y) -> sum
 {
 sum := add(signextend(15, x), signextend(15, y))
 if or(sgt(sum, 0x7fffffffffffffffffffffffffffffff), slt(sum, 0xffffffffffffffffffffffffffffffff80000000000000000000000000000000))
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert(0, 0x24)
 }
 }
 function fun_afterSwap(var_self_address, var_key_3301_mpos, var_params_mpos, var_swapDelta, var_hookData_3309_offset, var_hookData_3309_length, var_beforeSwapHookReturn) -> var, var_1
 {
 if eq( caller(), and( var_self_address, 0xffffffffffffffffffffffffffffffffffffffff))
 {
 var := var_swapDelta
 var_1 := 0
 leave
 }
 let expr := sar(128, var_beforeSwapHookReturn)
 let var_hookDeltaUnspecified := signextend(15, var_beforeSwapHookReturn)
 let var_2 := 0
 var_2 := iszero(iszero( and( var_self_address, 64)))
 if var_2
 {
 let expr_mpos := mload( 0x40)
 mstore(add(expr_mpos, 0x20), 0xb47b2fb100000000000000000000000000000000000000000000000000000000)
 mstore( add(expr_mpos, 36), caller())
 abi_encode_struct_PoolKey(var_key_3301_mpos, add( expr_mpos, 68))
 abi_encode_struct_SwapParams(var_params_mpos, add( expr_mpos, 228))
 mstore(add( expr_mpos, 324), var_swapDelta)
 mstore(add( expr_mpos, 356), 352)
 let _1 := sub( abi_encode_bytes_calldata(var_hookData_3309_offset, var_hookData_3309_length, add( expr_mpos, 388)), expr_mpos)
 mstore(expr_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
 finalize_allocation(expr_mpos, _1)
 let var_3 := 0
 var_3 := iszero(iszero( and( var_self_address, 4)))
 var_hookDeltaUnspecified := checked_add_int128(var_hookDeltaUnspecified, fun_toInt128( fun_callHookWithReturnDelta(var_self_address, expr_mpos, var_3)))
 }
 let var_hookDelta := 0
 var_hookDelta := 0
 let _2 := iszero( signextend( 15, var_hookDeltaUnspecified))
 let expr_1 := iszero(_2)
 if _2
 {
 expr_1 := iszero(iszero( signextend( 15, expr)))
 }
 if expr_1
 {
 let expr_2 := slt( mload( add(var_params_mpos, 32)), 0)
 let expr_3 := eq( expr_2, iszero(iszero(mload( var_params_mpos))))
 let expr_4 := 0
 switch expr_3
 case 0 {
 expr_4 := or(shl( 128, var_hookDeltaUnspecified), and(0xffffffffffffffffffffffffffffffff, expr))
 }
 default /// @src 23:15133:15332 "(params.amountSpecified < 0 == params.zeroForOne)..."
 {
 expr_4 := or(shl( 128, expr), and(0xffffffffffffffffffffffffffffffff, var_hookDeltaUnspecified))
 }
 var_hookDelta := expr_4
 var_swapDelta := fun_sub(var_swapDelta, expr_4)
 }
 var := var_swapDelta
 var_1 := var_hookDelta
 }
 function fun_callHook(var_self_2764_address, var_data_mpos) -> var_result_mpos
 {
 let _1 := mload(var_data_mpos)
 let _2 := add(var_data_mpos, 0x20)
 if iszero( call(gas(), var_self_2764_address, 0, _2, _1, 0, 0))
 {
 let value := 0
 let length := mload(var_data_mpos)
 let _3 := mload(_2)
 value := and(_3, 0xffffffff00000000000000000000000000000000000000000000000000000000)
 if lt(length, 4)
 {
 value := and(and(_3, shl(shl(3, sub(4, length)), 0xffffffff00000000000000000000000000000000000000000000000000000000)), 0xffffffff00000000000000000000000000000000000000000000000000000000)
 }
 let usr$encodedDataSize := and(add(returndatasize(), 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
 let usr$fmp := mload(0x40)
 mstore(usr$fmp, 0x90bfb86500000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp, 4), and( var_self_2764_address, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(add(usr$fmp, 0x24), and(value, 0xffffffff00000000000000000000000000000000000000000000000000000000))
 mstore(add(usr$fmp, 0x44), 0x80)
 mstore(add(usr$fmp, 0x64), add(0xa0, usr$encodedDataSize))
 mstore(add(usr$fmp, 0x84), returndatasize())
 returndatacopy(add(usr$fmp, 0xa4), 0, returndatasize())
 let _4 := add(usr$fmp, usr$encodedDataSize)
 mstore(add(_4, 0xa4), 4)
 mstore(add(_4, 0xc4), 0xa9e35b2f00000000000000000000000000000000000000000000000000000000)
 revert(usr$fmp, add(0xe4, usr$encodedDataSize))
 }
 var_result_mpos := mload(0x40)
 mstore(0x40, add(var_result_mpos, and(add(returndatasize(), 0x3f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)))
 mstore(var_result_mpos, returndatasize())
 let _5 := returndatasize()
 let _6 := add(var_result_mpos, 0x20)
 returndatacopy(_6, 0, _5)
 let expr := lt( mload( var_result_mpos), 0x20)
 if iszero(expr)
 {
 let expr_1 := mload(_6)
 expr := iszero(eq( and( expr_1, 0xffffffff00000000000000000000000000000000000000000000000000000000), and( mload(_2), 0xffffffff00000000000000000000000000000000000000000000000000000000)))
 }
 if expr
 {
 mstore( 0, 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 }
 function fun_flipTick(var_self_8407_slot, var_tick, var_tickSpacing)
 {
 let var_tick_1 := signextend(2, var_tick)
 let var_tickSpacing_1 := signextend(2, var_tickSpacing)
 if smod(var_tick_1, var_tickSpacing_1)
 {
 let usr$fmp := mload(0x40)
 mstore(usr$fmp, 0xd4d8f3e6)
 mstore(add(usr$fmp, 0x20), var_tick_1)
 mstore(add(usr$fmp, 0x40), var_tickSpacing_1)
 revert(add(usr$fmp, 0x1c), 0x44)
 }
 let var_tick_2 := sdiv(var_tick_1, var_tickSpacing_1)
 mstore(0, sar(8, var_tick_2))
 mstore(0x20, var_self_8407_slot)
 let usr$slot := keccak256(0, 0x40)
 sstore(usr$slot, xor(sload(usr$slot), shl(and(var_tick_2, 0xff), 1)))
 }
 function fun_clearTick(var_self_5348_slot, var_tick)
 {
 let dataSlot := 0
 mstore( 0, signextend(2, var_tick))
 mstore(0x20, add(var_self_5348_slot, 4))
 dataSlot := keccak256( 0, 0x40)
 sstore( dataSlot, 0)
 sstore(add( dataSlot, 1), 0)
 sstore(add( dataSlot, 2), 0)
 }
 function fun_getSqrtPriceAtTick(var_tick) -> var_sqrtPriceX96
 {
 let var_tick_1 := signextend(2, var_tick)
 let usr$mask := sar(255, var_tick_1)
 let var_absTick := xor(usr$mask, add(usr$mask, var_tick_1))
 if gt(var_absTick, 0x0d89e8)
 {
 mstore(0, 0x8b86327a00000000000000000000000000000000000000000000000000000000)
 mstore(0x04, var_tick_1)
 revert(0, 0x24)
 }
 let var_price := 0
 var_price := xor(0x0100000000000000000000000000000000, mul(0x01fffcb933bd6fad37aa2d162d1a594001, and(var_absTick, 0x1)))
 if iszero(iszero( and(var_absTick, 2)))
 {
 var_price := shr( 128, mul( var_price, 0xfff97272373d413259a46990580e213a))
 }
 if iszero(iszero( and(var_absTick, 0x04)))
 {
 var_price := shr( 128, mul( var_price, 0xfff2e50f5f656932ef12357cf3c7fdcc))
 }
 if iszero(iszero( and(var_absTick, 0x08)))
 {
 var_price := shr( 128, mul( var_price, 0xffe5caca7e10e4e61c3624eaa0941cd0))
 }
 if iszero(iszero( and(var_absTick, 0x10)))
 {
 var_price := shr( 128, mul( var_price, 0xffcb9843d60f6159c9db58835c926644))
 }
 if iszero(iszero( and(var_absTick, 0x20)))
 {
 var_price := shr( 128, mul( var_price, 0xff973b41fa98c081472e6896dfb254c0))
 }
 if iszero(iszero( and(var_absTick, 0x40)))
 {
 var_price := shr( 128, mul( var_price, 0xff2ea16466c96a3843ec78b326b52861))
 }
 if iszero(iszero( and(var_absTick, 128)))
 {
 var_price := shr( 128, mul( var_price, 0xfe5dee046a99a2a811c461f1969c3053))
 }
 if iszero(iszero( and(var_absTick, 0x0100)))
 {
 var_price := shr( 128, mul( var_price, 0xfcbe86c7900a88aedcffc83b479aa3a4))
 }
 if iszero(iszero( and(var_absTick, 0x0200)))
 {
 var_price := shr( 128, mul( var_price, 0xf987a7253ac413176f2b074cf7815e54))
 }
 if iszero(iszero( and(var_absTick, 0x0400)))
 {
 var_price := shr( 128, mul( var_price, 0xf3392b0822b70005940c7a398e4b70f3))
 }
 if iszero(iszero( and(var_absTick, 0x0800)))
 {
 var_price := shr( 128, mul( var_price, 0xe7159475a2c29b7443b29c7fa6e889d9))
 }
 if iszero(iszero( and(var_absTick, 0x1000)))
 {
 var_price := shr( 128, mul( var_price, 0xd097f3bdfd2022b8845ad8f792aa5825))
 }
 if iszero(iszero( and(var_absTick, 0x2000)))
 {
 var_price := shr( 128, mul( var_price, 0xa9f746462d870fdf8a65dc1f90e061e5))
 }
 if iszero(iszero( and(var_absTick, 0x4000)))
 {
 var_price := shr( 128, mul( var_price, 0x70d869a156d2a1b890bb3df62baf32f7))
 }
 if iszero(iszero( and(var_absTick, 0x8000)))
 {
 var_price := shr( 128, mul( var_price, 0x31be135f97d08fd981231505542fcfa6))
 }
 if iszero(iszero( and(var_absTick, 0x010000)))
 {
 var_price := shr( 128, mul( var_price, 0x09aa508b5b7a84e1c677de54f3e99bc9))
 }
 if iszero(iszero( and(var_absTick, 0x020000)))
 {
 var_price := shr( 128, mul( var_price, 0x5d6af8dedb81196699c329225ee604))
 }
 if iszero(iszero( and(var_absTick, 0x040000)))
 {
 var_price := shr( 128, mul( var_price, 0x2216e584f5fa1ea926041bedfe98))
 }
 if iszero(iszero( and(var_absTick, 0x080000)))
 {
 var_price := shr( 128, mul( var_price, 0x048a170391f7dc42444e8fa2))
 }
 if sgt(var_tick_1, 0)
 {
 var_price := div(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, var_price)
 }
 var_sqrtPriceX96 := shr( 0x20, add(var_price, 0xffffffff))
 }
 function fun_getAmount1Delta(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
 {
 let expr := 0x00
 switch slt( signextend(15, var_liquidity), 0x00)
 case 0 {
 let _1 := fun_getAmount1Delta_40416(var_sqrtPriceAX96, var_sqrtPriceBX96, and(0xffffffffffffffffffffffffffffffff, var_liquidity))
 if slt(_1, 0x00)
 {
 mstore( 0x00, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0x00, 0x04)
 }
 expr := sub( 0x00, _1)
 }
 default /// @src 33:13838:14056 "liquidity < 0..."
 {
 let _2 := fun_getAmount1Delta_40417(var_sqrtPriceAX96, var_sqrtPriceBX96, and(0xffffffffffffffffffffffffffffffff, sub( 0x00, var_liquidity)))
 if slt(_2, 0x00)
 {
 mstore( 0x00, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0x00, 0x04)
 }
 expr := _2
 }
 var := expr
 }
 function fun_getAmount0Delta(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
 {
 let expr := 0x00
 switch slt( signextend(15, var_liquidity), 0x00)
 case 0 {
 let _1 := fun_getAmount0Delta_40418(var_sqrtPriceAX96, var_sqrtPriceBX96, and(0xffffffffffffffffffffffffffffffff, var_liquidity))
 if slt(_1, 0x00)
 {
 mstore( 0x00, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0x00, 0x04)
 }
 expr := sub( 0x00, _1)
 }
 default /// @src 33:13065:13283 "liquidity < 0..."
 {
 let _2 := fun_getAmount0Delta_40419(var_sqrtPriceAX96, var_sqrtPriceBX96, and(0xffffffffffffffffffffffffffffffff, sub( 0x00, var_liquidity)))
 if slt(_2, 0x00)
 {
 mstore( 0x00, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0x00, 0x04)
 }
 expr := _2
 }
 var := expr
 }
 function fun_addDelta(var_x, var_y) -> var_z
 {
 var_z := add(and(var_x, 0xffffffffffffffffffffffffffffffff), signextend(15, var_y))
 if shr(128, var_z)
 {
 mstore(0, 0x93dafdf1)
 revert(0x1c, 0x04)
 }
 }
 function fun_callHookWithReturnDelta(var_self_2820_address, var_data_2822_mpos, var_parseReturn) -> var
 {
 var := 0
 let expr_2834_mpos := fun_callHook(var_self_2820_address, var_data_2822_mpos)
 if iszero(var_parseReturn)
 {
 var := 0
 leave
 }
 if iszero(eq( mload( expr_2834_mpos), 0x40))
 {
 mstore( 0, 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 var := mload(add( expr_2834_mpos, 0x40))
 }
 function fun_sub(var_a, var_b) -> var
 {
 let expr := fun_toInt128( sub(sar(128, var_a), sar(128, var_b)))
 var := or(shl( 128, expr), and(0xffffffffffffffffffffffffffffffff, fun_toInt128( sub(signextend(15, var_a), signextend(15, var_b)))))
 }
 function fun_getTickAtSqrtPrice(var_sqrtPriceX96) -> var_tick
 {
 if gt( and( add( var_sqrtPriceX96, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffd895d), 0xffffffffffffffffffffffffffffffffffffffff), 0xfffd8963efd1fc6a506488495d951d5163961682)
 {
 mstore(0, 0x6148752400000000000000000000000000000000000000000000000000000000)
 mstore(0x04, and(var_sqrtPriceX96, 0xffffffffffffffffffffffffffffffffffffffff))
 revert(0, 0x24)
 }
 let var_r := and(shl( 0x20, var_sqrtPriceX96), 0xffffffffffffffffffffffffffffffffffffffff00000000)
 let result := var_r
 let value := and( fun_mostSignificantBit(var_r), 0xff)
 switch iszero(lt(value, 0x80))
 case 0 {
 var_r := shl(sub( 0x7f, value), var_r)
 }
 default /// @src 36:8507:8590 "if (msb >= 128) r = price >> (msb - 127);..."
 {
 var_r := shr(add( value, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81), result)
 }
 let _1 := mul(var_r, var_r)
 let var_r_1 := shr(shr( 0xff, _1), shr(127, _1))
 let _2 := mul(var_r_1, var_r_1)
 let var_r_2 := shr(shr( 0xff, _2), shr( 127, _2))
 let _3 := mul(var_r_2, var_r_2)
 let var_r_3 := shr(shr( 0xff, _3), shr( 127, _3))
 let _4 := mul(var_r_3, var_r_3)
 let var_r_4 := shr(shr( 0xff, _4), shr( 127, _4))
 let _5 := mul(var_r_4, var_r_4)
 let var_r_5 := shr(shr( 0xff, _5), shr( 127, _5))
 let _6 := mul(var_r_5, var_r_5)
 let var_r_6 := shr(shr( 0xff, _6), shr( 127, _6))
 let _7 := mul(var_r_6, var_r_6)
 let var_r_7 := shr(shr( 0xff, _7), shr( 127, _7))
 let _8 := mul(var_r_7, var_r_7)
 let var_r_8 := shr(shr( 0xff, _8), shr( 127, _8))
 let _9 := mul(var_r_8, var_r_8)
 let var_r_9 := shr(shr( 0xff, _9), shr( 127, _9))
 let _10 := mul(var_r_9, var_r_9)
 let var_r_10 := shr(shr( 0xff, _10), shr( 127, _10))
 let _11 := mul(var_r_10, var_r_10)
 let var_r_11 := shr(shr( 0xff, _11), shr( 127, _11))
 let _12 := mul(var_r_11, var_r_11)
 let var_r_12 := shr(shr( 0xff, _12), shr( 127, _12))
 let _13 := mul(var_r_12, var_r_12)
 let var_r_13 := shr(shr( 0xff, _13), shr( 127, _13))
 let expr := mul( or( or( or( or( or( or( or( or( or( or( or( or( or( or( shl( 0x40, add( value, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff80)), and(shr(192, _1), 0x8000000000000000)), and(shr(193, _2), 0x4000000000000000)), and(shr(194, _3), 0x2000000000000000)), and(shr(195, _4), 0x1000000000000000)), and(shr(196, _5), 0x0800000000000000)), and(shr(197, _6), 0x0400000000000000)), and(shr(198, _7), 0x0200000000000000)), and(shr(199, _8), 0x0100000000000000)), and(shr(200, _9), 0x80000000000000)), and(shr(201, _10), 0x40000000000000)), and(shr(202, _11), 0x20000000000000)), and(shr(203, _12), 0x10000000000000)), and(shr(204, _13), 0x08000000000000)), and(shr(205, mul(var_r_13, var_r_13)), 0x04000000000000)), 0x3627a301d71055774c85)
 let cleaned := signextend(2, sar( 0x80, add( expr, 0xfffffffffffffffffffffffffffffffffd709b7e5480fba5a50fed5e62ffc556)))
 let cleaned_1 := signextend(2, sar( 0x80, add( expr, 0xdb2df09e81959a81455e260799a0632f)))
 let expr_1 := 0
 switch eq( cleaned, cleaned_1)
 case 0 {
 let expr_2 := iszero(gt( and( fun_getSqrtPriceAtTick(cleaned_1), 0xffffffffffffffffffffffffffffffffffffffff), and( var_sqrtPriceX96, 0xffffffffffffffffffffffffffffffffffffffff)))
 let expr_3 := 0
 switch expr_2
 case 0 { expr_3 := cleaned }
 default { expr_3 := cleaned_1 }
 expr_1 := expr_3
 }
 default { expr_1 := cleaned }
 var_tick := expr_1
 }
 function fun_computeSlot(var_target, var_currency) -> var_hashSlot
 {
 mstore(0, and(var_target, 0xffffffffffffffffffffffffffffffffffffffff))
 mstore(32, and(var_currency, 0xffffffffffffffffffffffffffffffffffffffff))
 var_hashSlot := keccak256(0, 64)
 }
 function wrapping_div_uint256(x, y) -> r
 {
 if iszero(y)
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x12)
 revert(0, 0x24)
 }
 r := div(x, y)
 }
 function fun_swap(var_self_slot, var_params_4413_mpos) -> var_swapDelta, var_amountToProtocol, var_swapFee, var_result_4424_mpos
 {
 var_amountToProtocol := 0
 let memPtr := mload(64)
 finalize_allocation_40253(memPtr)
 mstore(memPtr, 0)
 let _1 := add(memPtr, 32)
 mstore(_1, 0)
 let _2 := add(memPtr, 64)
 mstore(_2, 0)
 var_result_4424_mpos := memPtr
 let _3 := sload( var_self_slot)
 let _4 := iszero(mload( add(var_params_4413_mpos, 64)))
 let expr := 0
 switch iszero(_4)
 case 0 {
 expr := and(shr(196, _3), 4095)
 }
 default /// @src 29:12550:12652 "zeroForOne ? slot0Start.protocolFee().getZeroForOneFee() : slot0Start.protocolFee().getOneForZeroFee()"
 {
 expr := and( shr(184, _3), 0x0fff)
 }
 let var_amountSpecifiedRemaining := mload( var_params_4413_mpos)
 let var_amountCalculated := 0
 let expr_1 := and(1461501637330902918203684832716283019655932542975, _3)
 mstore(memPtr, expr_1)
 mstore(_1, signextend(2, shr(160, _3)))
 mstore(_2, and(sload( add(var_self_slot, 3)), 0xffffffffffffffffffffffffffffffff))
 let _5 := mload( add(var_params_4413_mpos, 128))
 let expr_2 := 0
 switch iszero(iszero( and( _5, 0x400000)))
 case 0 {
 expr_2 := and( 0xffffff, shr(208, _3))
 }
 default /// @src 29:13451:13592 "params.lpFeeOverride.isOverride()..."
 {
 let expr_3 := and( _5, 0xbfffff)
 fun_validate(expr_3)
 expr_2 := expr_3
 }
 let expr_4 := 0
 switch iszero( and( expr, 0xffff))
 case 0 {
 let var_self := and( expr, 0xfff)
 let var_lpFee := and(expr_2, 0xffffff)
 expr_4 := sub(add(var_self, var_lpFee), div(mul(var_self, var_lpFee), 1000000))
 }
 default /// @src 29:13617:13687 "protocolFee == 0 ? lpFee : uint16(protocolFee).calculateSwapFee(lpFee)"
 { expr_4 := expr_2 }
 var_swapFee := expr_4
 if iszero(lt( and( expr_4, 0xffffff), 0x0f4240))
 {
 if sgt( mload( var_params_4413_mpos), 0)
 {
 mstore( 0, 0x9620624600000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 }
 if iszero( mload( var_params_4413_mpos))
 {
 var_swapDelta := 0
 var_amountToProtocol := 0
 var_swapFee := expr_4
 var_result_4424_mpos := memPtr
 leave
 }
 switch iszero(_4)
 case 0 {
 let _6 := add(var_params_4413_mpos, 96)
 let cleaned := and(mload( _6), 1461501637330902918203684832716283019655932542975)
 if iszero(gt( cleaned, expr_1))
 {
 let usr$fmp := mload( 64)
 mstore(usr$fmp, 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp, 0x04), expr_1)
 mstore(add(usr$fmp, 0x24), cleaned)
 revert(usr$fmp, 0x44)
 }
 let cleaned_1 := and(mload( _6), 1461501637330902918203684832716283019655932542975)
 if iszero(lt( cleaned_1, 0xfffd8963efd1fc6a506488495d951d5263988d26))
 {
 mstore( 0, 0x9e4d7cc700000000000000000000000000000000000000000000000000000000)
 mstore(0x04, cleaned_1)
 revert( 0, 0x24)
 }
 }
 default /// @src 29:14350:15371 "if (zeroForOne) {..."
 {
 let _7 := add(var_params_4413_mpos, 96)
 let cleaned_2 := and(mload( _7), 1461501637330902918203684832716283019655932542975)
 if iszero(lt( cleaned_2, expr_1))
 {
 let usr$fmp_1 := mload( 64)
 mstore(usr$fmp_1, 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000)
 mstore(add(usr$fmp_1, 0x04), expr_1)
 mstore(add(usr$fmp_1, 0x24), cleaned_2)
 revert(usr$fmp_1, 0x44)
 }
 let cleaned_3 := and(mload( _7), 1461501637330902918203684832716283019655932542975)
 if iszero(gt( cleaned_3, 0x01000276a3))
 {
 mstore( 0, 0x9e4d7cc700000000000000000000000000000000000000000000000000000000)
 mstore(0x04, cleaned_3)
 revert( 0, 0x24)
 }
 }
 let memPtr_1 := mload(64)
 let newFreePtr := add(memPtr_1, 256)
 if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr_1))
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x41)
 revert(0, 0x24)
 }
 mstore(64, newFreePtr)
 mstore(memPtr_1, 0)
 mstore(add(memPtr_1, 32), 0)
 mstore(add(memPtr_1, 64), 0)
 mstore(add(memPtr_1, 96), 0)
 mstore(add(memPtr_1, 128), 0)
 mstore(add(memPtr_1, 160), 0)
 mstore(add(memPtr_1, 192), 0)
 let expr_5 := 0
 switch iszero(_4)
 case 0 {
 expr_5 := sload( add(var_self_slot, 2))
 }
 default /// @src 29:15446:15512 "zeroForOne ? self.feeGrowthGlobal0X128 : self.feeGrowthGlobal1X128"
 {
 expr_5 := sload( add(var_self_slot, 1))
 }
 mstore( add(memPtr_1, 224), expr_5)
 for { }
 0x1
 { }
 {
 let expr_6 := iszero(var_amountSpecifiedRemaining)
 if iszero(expr_6)
 {
 let cleaned_4 := and(mload( var_result_4424_mpos), 1461501637330902918203684832716283019655932542975)
 expr_6 := eq( cleaned_4, and(mload( add(var_params_4413_mpos, 96)), 1461501637330902918203684832716283019655932542975))
 }
 if iszero( iszero(expr_6)) { break }
 mstore(memPtr_1, and(mload( var_result_4424_mpos), 1461501637330902918203684832716283019655932542975))
 let cleaned_5 := signextend( 2, mload( add(var_result_4424_mpos, 32)))
 let cleaned_6 := signextend( 2, mload( add(var_params_4413_mpos, 32)))
 let var_next := 0
 let var_initialized := 0
 let var_compressed := sub(sdiv(cleaned_5, cleaned_6), slt(smod(cleaned_5, cleaned_6), 0))
 switch iszero(_4)
 case 0 {
 let _8 := add( var_compressed, 0x1)
 let dataSlot := 0
 mstore(0, signextend(1, sar(8, signextend( 2, _8))))
 mstore(0x20, add(var_self_slot, 5))
 dataSlot := keccak256(0, 0x40)
 let expr_7 := and( sload( dataSlot), not( add(shl(and(_8, 0xff), 0x1), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)))
 let _9 := iszero(expr_7)
 var_initialized := iszero(_9)
 let expr_8 := 0
 switch var_initialized
 case 0 {
 expr_8 := signextend( 2, mul(signextend( 2, add(signextend( 2, _8), signextend( 2, and(sub( 0xff, and(0xff, _8)), 0xff)))), cleaned_6))
 }
 default /// @src 35:6019:6232 "initialized..."
 {
 if _9 { revert(0, 0) }
 let var_x := and(expr_7, sub( 0, expr_7))
 let var_r := and(shr(247, shl(and(shr(248, mul(var_x, 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff)), 252), 0x8040405543005266443200005020610674053026020000107506200176117077)), 480)
 expr_8 := signextend( 2, mul(signextend( 2, add(signextend( 2, _8), signextend( 2, and(sub( or(var_r, byte(and(div(0xd76453e0, shr(var_r, var_x)), 31), 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405)), and(0xff, _8)), 0xff)))), cleaned_6))
 }
 var_next := expr_8
 }
 default /// @src 35:4565:6247 "if (lte) {..."
 {
 let var_bitPos := and(var_compressed, 0xff)
 let dataSlot_1 := 0
 mstore( 0, signextend(1, sar(8, signextend( 2, var_compressed))))
 mstore(0x20, add(var_self_slot, 5))
 dataSlot_1 := keccak256( 0, 0x40)
 let expr_9 := and( sload( dataSlot_1), shr(sub( 0xff, var_bitPos), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
 var_initialized := iszero(iszero(expr_9))
 let expr_10 := 0
 switch var_initialized
 case 0 {
 expr_10 := signextend( 2, mul(signextend( 2, sub( var_compressed, signextend( 2, var_bitPos))), cleaned_6))
 }
 default /// @src 35:5164:5358 "initialized..."
 {
 expr_10 := signextend( 2, mul(signextend( 2, sub(var_compressed, signextend( 2, and(sub(var_bitPos, fun_mostSignificantBit(expr_9)), 0xff)))), cleaned_6))
 }
 var_next := expr_10
 }
 mstore( add(memPtr_1, 64), iszero(iszero(var_initialized)))
 let _10 := signextend( 2, var_next)
 mstore( add(memPtr_1, 32), _10)
 if iszero(sgt(_10, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618))
 {
 mstore( add(memPtr_1, 32), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618)
 }
 if iszero(slt( signextend( 2, mload( add(memPtr_1, 32))), 0x0d89e8))
 {
 mstore( add(memPtr_1, 32), 0x0d89e8)
 }
 let _11 := and( fun_getSqrtPriceAtTick( signextend( 2, mload( add(memPtr_1, 32)))), 1461501637330902918203684832716283019655932542975)
 mstore( add(memPtr_1, 96), _11)
 let cleaned_7 := and(mload( var_result_4424_mpos), 1461501637330902918203684832716283019655932542975)
 let cleaned_8 := and(mload( add(var_params_4413_mpos, 96)), 1461501637330902918203684832716283019655932542975)
 let var_sqrtPriceTargetX96 := xor(cleaned_8, mul(xor(_11, cleaned_8), xor(lt(_11, cleaned_8), and( iszero(_4), 0x1))))
 let cleaned_9 := and(mload( add(var_result_4424_mpos, 64)), 0xffffffffffffffffffffffffffffffff)
 let var_sqrtPriceNextX96 := 0
 let var_amountIn := 0
 let var_amountOut := 0
 let var_feeAmount := 0
 let expr_11 := iszero(lt( cleaned_7, and( var_sqrtPriceTargetX96, 1461501637330902918203684832716283019655932542975)))
 switch slt(var_amountSpecifiedRemaining, 0)
 case 0 {
 let expr_12 := 0
 switch expr_11
 case 0 {
 expr_12 := fun_getAmount0Delta_40419(cleaned_7, var_sqrtPriceTargetX96, cleaned_9)
 }
 default /// @src 34:5746:5978 "zeroForOne..."
 {
 expr_12 := fun_getAmount1Delta_40417(var_sqrtPriceTargetX96, cleaned_7, cleaned_9)
 }
 var_amountOut := expr_12
 switch iszero(lt(var_amountSpecifiedRemaining, expr_12))
 case 0 {
 var_amountOut := var_amountSpecifiedRemaining
 if or(iszero(cleaned_7), iszero(cleaned_9))
 {
 mstore( 0, 0x4f2461b8)
 revert(0x1c, 0x04)
 }
 let expr_13 := 0
 switch expr_11
 case 0 {
 expr_13 := fun_getNextSqrtPriceFromAmount0RoundingUp_40426(cleaned_7, cleaned_9, var_amountSpecifiedRemaining)
 }
 default /// @src 33:8646:8840 "zeroForOne..."
 {
 let var := 0
 let var_add := 0
 var := 0
 var_add := 0
 let expr_14 := 0
 switch iszero(gt(var_amountSpecifiedRemaining, 0xffffffffffffffffffffffffffffffffffffffff))
 case 0 {
 let _12 := and( cleaned_9, 0xffffffffffffffffffffffffffffffff)
 let var_result := 0
 var_result := fun_mulDiv(var_amountSpecifiedRemaining, 0x01000000000000000000000000, _12)
 if iszero(_12)
 {
 mstore( 0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x12)
 revert( 0, 0x24)
 }
 if iszero(iszero( mulmod(var_amountSpecifiedRemaining, 0x01000000000000000000000000, _12)))
 {
 var_result := add( var_result, 1)
 if iszero(var_result)
 { revert(0, 0) }
 }
 expr_14 := var_result
 }
 default {
 let result := shl( 0x60, var_amountSpecifiedRemaining)
 let _13 := and( cleaned_9, 0xffffffffffffffffffffffffffffffff)
 expr_14 := add(div(result, _13), iszero(iszero(mod(result, _13))))
 }
 let _14 := and( cleaned_7, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(gt(_14, expr_14))
 {
 mstore( 0, 0x4323a555)
 revert(0x1c, 0x04)
 }
 var := and(sub(_14, expr_14), 0xffffffffffffffffffffffffffffffffffffffff)
 expr_13 := var
 }
 var_sqrtPriceNextX96 := expr_13
 }
 default /// @src 34:5996:6512 "if (uint256(amountRemaining) >= amountOut) {..."
 {
 var_sqrtPriceNextX96 := var_sqrtPriceTargetX96
 }
 let expr_15 := 0
 switch expr_11
 case 0 {
 expr_15 := fun_getAmount1Delta_40416(cleaned_7, var_sqrtPriceNextX96, cleaned_9)
 }
 default /// @src 34:6540:6766 "zeroForOne..."
 {
 expr_15 := fun_getAmount0Delta_40418(var_sqrtPriceNextX96, cleaned_7, cleaned_9)
 }
 var_amountIn := expr_15
 var_feeAmount := fun_mulDivRoundingUp(expr_15, and( var_swapFee, 0xffffff), sub( 0x0f4240, and( var_swapFee, 0xffffff)))
 }
 default /// @src 34:4027:6949 "if (exactIn) {..."
 {
 let expr_16 := sub( 0x0f4240, and( var_swapFee, 0xffffff))
 let expr_17 := fun_mulDiv_40430( sub(0, var_amountSpecifiedRemaining), expr_16)
 let expr_18 := 0
 switch expr_11
 case 0 {
 expr_18 := fun_getAmount1Delta_40416(cleaned_7, var_sqrtPriceTargetX96, cleaned_9)
 }
 default /// @src 34:4221:4451 "zeroForOne..."
 {
 expr_18 := fun_getAmount0Delta_40418(var_sqrtPriceTargetX96, cleaned_7, cleaned_9)
 }
 var_amountIn := expr_18
 switch iszero(lt(expr_17, expr_18))
 case 0 {
 var_amountIn := expr_17
 if or(iszero(cleaned_7), iszero(cleaned_9))
 {
 mstore( 0, 0x4f2461b8)
 revert(0x1c, 0x04)
 }
 let expr_19 := 0
 switch expr_11
 case 0 {
 let var_1 := 0
 var_1 := 0
 let expr_20 := 0
 switch iszero(gt(expr_17, 0xffffffffffffffffffffffffffffffffffffffff))
 case 0 {
 expr_20 := fun_mulDiv_40456(expr_17, and( cleaned_9, 0xffffffffffffffffffffffffffffffff))
 }
 default /// @src 33:4834:5006 "amount <= type(uint160).max..."
 {
 expr_20 := wrapping_div_uint256( shl( 0x60, expr_17), and( cleaned_9, 0xffffffffffffffffffffffffffffffff))
 }
 var_1 := fun_toUint160( checked_add_uint256( and( cleaned_7, 0xffffffffffffffffffffffffffffffffffffffff), expr_20))
 expr_19 := var_1
 }
 default {
 expr_19 := fun_getNextSqrtPriceFromAmount0RoundingUp(cleaned_7, cleaned_9, expr_17)
 }
 var_sqrtPriceNextX96 := expr_19
 var_feeAmount := sub(0, add( var_amountSpecifiedRemaining, expr_17))
 }
 default /// @src 34:4469:5438 "if (amountRemainingLessFee >= amountIn) {..."
 {
 var_sqrtPriceNextX96 := var_sqrtPriceTargetX96
 let expr_21 := 0
 switch eq( and( var_swapFee, 0xffffff), 0x0f4240)
 case 0 {
 expr_21 := fun_mulDivRoundingUp(var_amountIn, and( var_swapFee, 0xffffff), expr_16)
 }
 default /// @src 34:4666:4922 "_feePips == MAX_SWAP_FEE..."
 { expr_21 := var_amountIn }
 var_feeAmount := expr_21
 }
 let expr_22 := 0
 switch expr_11
 case 0 {
 expr_22 := fun_getAmount0Delta_40419(cleaned_7, var_sqrtPriceNextX96, cleaned_9)
 }
 default /// @src 34:5467:5695 "zeroForOne..."
 {
 expr_22 := fun_getAmount1Delta_40417(var_sqrtPriceNextX96, cleaned_7, cleaned_9)
 }
 var_amountOut := expr_22
 }
 mstore( add(memPtr_1, 192), var_feeAmount)
 mstore( add(memPtr_1, 160), var_amountOut)
 mstore( add(memPtr_1, 128), var_amountIn)
 mstore(var_result_4424_mpos, and(var_sqrtPriceNextX96, 1461501637330902918203684832716283019655932542975))
 switch sgt( mload( var_params_4413_mpos), 0)
 case 0 {
 let _15 := mload(add(memPtr_1, 128))
 let sum := add(_15, mload(add(memPtr_1, 192)))
 if slt(sum, 0)
 {
 mstore( 0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 var_amountSpecifiedRemaining := add(var_amountSpecifiedRemaining, sum)
 let _16 := mload(add(memPtr_1, 160))
 if slt(_16, 0)
 {
 mstore( 0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 var_amountCalculated := checked_add_int256(var_amountCalculated, _16)
 }
 default /// @src 29:16961:17529 "if (params.amountSpecified > 0) {..."
 {
 let _17 := mload(add(memPtr_1, 160))
 if slt(_17, 0)
 {
 mstore( 0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 var_amountSpecifiedRemaining := sub(var_amountSpecifiedRemaining, _17)
 let _18 := mload(add(memPtr_1, 128))
 let _19 := checked_add_uint256(_18, mload(add(memPtr_1, 192)))
 if slt(_19, 0)
 {
 mstore( 0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert( 0, 0x04)
 }
 let diff := sub(var_amountCalculated, _19)
 if and( 0x1, sgt(diff, var_amountCalculated))
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x11)
 revert(0, 0x24)
 }
 var_amountCalculated := diff
 }
 if iszero( iszero( and( expr, 0xffff)))
 {
 let expr_23 := 0
 switch eq( and( var_swapFee, 0xffffff), and( expr, 0xffff))
 case 0 {
 let _20 := mload(add(memPtr_1, 128))
 expr_23 := div( mul( add(_20, mload(add(memPtr_1, 192))), and( expr, 0xffff)), 0x0f4240)
 }
 default /// @src 29:18159:18401 "(swapFee == protocolFee)..."
 {
 expr_23 := mload(add(memPtr_1, 192))
 }
 mstore( add(memPtr_1, 192), sub( mload(add(memPtr_1, 192)), expr_23))
 var_amountToProtocol := add( var_amountToProtocol, expr_23)
 }
 let cleaned_10 := and(mload( add(var_result_4424_mpos, 64)), 0xffffffffffffffffffffffffffffffff)
 if iszero(iszero(cleaned_10))
 {
 mstore( add(memPtr_1, 224), add( mload(add(memPtr_1, 224)), div(shl( 128, mload(add(memPtr_1, 192))), cleaned_10)))
 }
 let cleaned_11 := and(mload( var_result_4424_mpos), 1461501637330902918203684832716283019655932542975)
 switch eq( cleaned_11, and(mload( add(memPtr_1, 96)), 1461501637330902918203684832716283019655932542975))
 case 0 {
 if iszero(eq( cleaned_11, and(mload( memPtr_1), 1461501637330902918203684832716283019655932542975)))
 {
 mstore( add(var_result_4424_mpos, 32), signextend( 2, fun_getTickAtSqrtPrice( cleaned_11)))
 }
 }
 default /// @src 29:19484:20873 "if (result.sqrtPriceX96 == step.sqrtPriceNextX96) {..."
 {
 if iszero(iszero(mload( add(memPtr_1, 64))))
 {
 let expr_4864_component := 0
 let expr_component := 0
 switch iszero(_4)
 case 0 {
 let _21 := sload( add(var_self_slot, 0x1))
 let _22 := mload(add(memPtr_1, 224))
 expr_4864_component := _21
 expr_component := _22
 }
 default {
 let _23 := mload(add(memPtr_1, 224))
 let _24 := sload( add(var_self_slot, 2))
 expr_4864_component := _23
 expr_component := _24
 }
 let cleaned_12 := signextend( 2, mload( add(memPtr_1, 32)))
 let dataSlot_2 := 0
 mstore( 0, signextend(2, cleaned_12))
 mstore(0x20, add(var_self_slot, 4))
 dataSlot_2 := keccak256( 0, 0x40)
 let _25 := add(dataSlot_2, 0x1)
 sstore(_25, sub(expr_4864_component, sload( _25)))
 let _26 := add(dataSlot_2, 2)
 sstore(_26, sub(expr_component, sload( _26)))
 let var_liquidityNet := sar( 128, sload( dataSlot_2))
 if iszero(_4)
 {
 var_liquidityNet := signextend(15, sub(0, var_liquidityNet))
 }
 mstore( add(var_result_4424_mpos, 64), and( fun_addDelta( and(mload( add(var_result_4424_mpos, 64)), 0xffffffffffffffffffffffffffffffff), var_liquidityNet), 0xffffffffffffffffffffffffffffffff))
 }
 let expr_24 := 0
 switch iszero(_4)
 case 0 {
 expr_24 := signextend( 2, mload( add(memPtr_1, 32)))
 }
 default /// @src 29:20522:20568 "zeroForOne ? step.tickNext - 1 : step.tickNext"
 {
 expr_24 := signextend( 2, add( signextend( 2, mload( add(memPtr_1, 32))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
 }
 mstore( add(var_result_4424_mpos, 32), signextend( 2, expr_24))
 }
 }
 let _27 := and(0xffffff0000000000000000000000000000000000000000, shl( 160, mload( add(var_result_4424_mpos, 32))))
 sstore(var_self_slot, or(or(_27, and( _3, 0xffffffffffffffffff0000000000000000000000000000000000000000000000)), and(mload( var_result_4424_mpos), 1461501637330902918203684832716283019655932542975)))
 let cleaned_13 := and(sload( add(var_self_slot, 3)), 0xffffffffffffffffffffffffffffffff)
 let cleaned_14 := and(mload( add(var_result_4424_mpos, 64)), 0xffffffffffffffffffffffffffffffff)
 if iszero(eq( cleaned_13, cleaned_14))
 {
 sstore( add(var_self_slot, 3), or(and(sload( add(var_self_slot, 3)), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(cleaned_14, 0xffffffffffffffffffffffffffffffff)))
 }
 switch _4
 case 0 {
 sstore( add(var_self_slot, 0x1), mload(add(memPtr_1, 224)))
 }
 default /// @src 29:21147:21324 "if (!zeroForOne) {..."
 {
 sstore( add(var_self_slot, 2), mload(add(memPtr_1, 224)))
 }
 let _28 := mload( var_params_4413_mpos)
 switch iszero(eq( iszero(_4), slt(_28, 0)))
 case 0 {
 let expr_25 := fun_toInt128( sub(_28, var_amountSpecifiedRemaining))
 var_swapDelta := or(shl( 128, expr_25), and( 0xffffffffffffffffffffffffffffffff, fun_toInt128(var_amountCalculated)))
 }
 default /// @src 29:21401:21835 "if (zeroForOne != (params.amountSpecified < 0)) {..."
 {
 let expr_26 := fun_toInt128(var_amountCalculated)
 var_swapDelta := or(shl( 128, expr_26), and( 0xffffffffffffffffffffffffffffffff, fun_toInt128( sub(mload( var_params_4413_mpos), var_amountSpecifiedRemaining))))
 }
 }
 function fun_mulDiv_40234(var_a, var_b) -> var_result
 {
 var_result := 0
 let expr := mul( var_a, var_b)
 let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
 let _1 := lt(usr$mm, expr)
 let _2 := sub(usr$mm, expr)
 let var_prod1 := sub(_2, _1)
 if iszero( gt( 0x0100000000000000000000000000000000, var_prod1))
 { revert(0, 0) }
 if eq( _2, _1)
 {
 var_result := shr(128, expr)
 leave
 }
 let var_remainder := mulmod(var_a, var_b, 0x0100000000000000000000000000000000)
 var_result := or( shr(128, sub(expr, var_remainder)), shl( 128, sub(var_prod1, gt(var_remainder, expr))))
 }
 function fun_mulDiv_40430(var_a, var_b) -> var_result
 {
 var_result := 0
 let expr := mul( var_a, var_b)
 let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
 let _1 := lt(usr$mm, expr)
 let _2 := sub(usr$mm, expr)
 let var_prod1 := sub(_2, _1)
 if iszero( gt( 0x0f4240, var_prod1))
 { revert(0, 0) }
 if eq( _2, _1)
 {
 var_result := div(expr, 0x0f4240)
 leave
 }
 let var_remainder := mulmod(var_a, var_b, 0x0f4240)
 var_result := mul( or( shr(6, sub(expr, var_remainder)), shl(250, sub(var_prod1, gt(var_remainder, expr)))), 0xde8f6cefed634549b62c77574f722e1ac57e23f24d8fd5cb790fb65668c26139)
 }
 function fun_mulDiv_40437(var_a, var_b) -> var_result
 {
 var_result := 0
 let expr := mul( var_a, var_b)
 let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
 let _1 := lt(usr$mm, expr)
 let _2 := sub(usr$mm, expr)
 let var_prod1 := sub(_2, _1)
 if iszero( gt( 0x01000000000000000000000000, var_prod1))
 { revert(0, 0) }
 if eq( _2, _1)
 {
 var_result := shr(96, expr)
 leave
 }
 let var_remainder := mulmod(var_a, var_b, 0x01000000000000000000000000)
 var_result := or( shr(96, sub(expr, var_remainder)), shl(160, sub(var_prod1, gt(var_remainder, expr))))
 }
 function fun_mulDiv_40456(var_a, var_denominator) -> var_result
 {
 var_result := 0
 let expr := shl(96, var_a)
 let usr$mm := mulmod(var_a, 0x01000000000000000000000000, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
 let _1 := lt(usr$mm, expr)
 let _2 := sub(usr$mm, expr)
 let var_prod1 := sub(_2, _1)
 if iszero( gt(var_denominator, var_prod1))
 { revert(0, 0) }
 if eq( _2, _1)
 {
 var_result := div(expr, var_denominator)
 leave
 }
 let var_remainder := mulmod(var_a, 0x01000000000000000000000000, var_denominator)
 let expr_1 := and( sub(0, var_denominator), var_denominator)
 let var_denominator_1 := div(var_denominator, expr_1)
 let expr_2 := xor( mul( 0x03, var_denominator_1), 0x02)
 let expr_3 := mul( expr_2, sub( 0x02, mul( var_denominator_1, expr_2)))
 let expr_4 := mul( expr_3, sub( 0x02, mul( var_denominator_1, expr_3)))
 let expr_5 := mul( expr_4, sub( 0x02, mul( var_denominator_1, expr_4)))
 let expr_6 := mul( expr_5, sub( 0x02, mul( var_denominator_1, expr_5)))
 let expr_7 := mul( expr_6, sub( 0x02, mul( var_denominator_1, expr_6)))
 var_result := mul( or( div( sub(expr, var_remainder), expr_1), mul( sub(var_prod1, gt(var_remainder, expr)), add(div(sub( 0, expr_1), expr_1), 1))), mul( expr_7, sub( 0x02, mul( var_denominator_1, expr_7))))
 }
 function fun_mulDiv(var_a, var_b, var_denominator) -> var_result
 {
 var_result := 0
 let expr := mul( var_a, var_b)
 let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
 let _1 := lt(usr$mm, expr)
 let _2 := sub(usr$mm, expr)
 let var_prod1 := sub(_2, _1)
 if iszero( gt(var_denominator, var_prod1))
 { revert(0, 0) }
 if eq( _2, _1)
 {
 var_result := div(expr, var_denominator)
 leave
 }
 let var_remainder := mulmod(var_a, var_b, var_denominator)
 let expr_1 := and( sub(0, var_denominator), var_denominator)
 let var_denominator_1 := div(var_denominator, expr_1)
 let expr_2 := xor( mul( 0x03, var_denominator_1), 0x02)
 let expr_3 := mul( expr_2, sub( 0x02, mul( var_denominator_1, expr_2)))
 let expr_4 := mul( expr_3, sub( 0x02, mul( var_denominator_1, expr_3)))
 let expr_5 := mul( expr_4, sub( 0x02, mul( var_denominator_1, expr_4)))
 let expr_6 := mul( expr_5, sub( 0x02, mul( var_denominator_1, expr_5)))
 let expr_7 := mul( expr_6, sub( 0x02, mul( var_denominator_1, expr_6)))
 var_result := mul( or( div( sub(expr, var_remainder), expr_1), mul( sub(var_prod1, gt(var_remainder, expr)), add(div(sub( 0, expr_1), expr_1), 1))), mul( expr_7, sub( 0x02, mul( var_denominator_1, expr_7))))
 }
 function fun_getAmount1Delta_40416(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var_amount1
 {
 let usr$diff := sub(and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and(var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
 let usr$mask := sar(255, usr$diff)
 let var_res := xor(usr$mask, add(usr$mask, usr$diff))
 let expr := and( var_liquidity, 0xffffffffffffffffffffffffffffffff)
 let expr_1 := fun_mulDiv_40437(expr, var_res)
 var_amount1 := add(expr_1, and(iszero(iszero(mulmod(expr, var_res, 0x01000000000000000000000000))), 0x01))
 }
 function fun_getAmount1Delta_40417(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var_amount1
 {
 let usr$diff := sub(and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and(var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
 let usr$mask := sar(255, usr$diff)
 var_amount1 := fun_mulDiv_40437( and( var_liquidity, 0xffffffffffffffffffffffffffffffff), xor(usr$mask, add(usr$mask, usr$diff)))
 }
 function fun_getAmount0Delta_40418(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
 {
 if gt( and( var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and( var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
 {
 let expr_component := var_sqrtPriceBX96
 var_sqrtPriceBX96 := var_sqrtPriceAX96
 var_sqrtPriceAX96 := expr_component
 }
 let _1 := and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(_1)
 {
 mstore(0, 0x00bfc921)
 revert(0x1c, 0x04)
 }
 let expr := 0
 let expr_1 := fun_mulDivRoundingUp( and(shl( 0x60, var_liquidity), 0xffffffffffffffffffffffffffffffff000000000000000000000000), and( sub( var_sqrtPriceBX96, var_sqrtPriceAX96), 0xffffffffffffffffffffffffffffffffffffffff), and( var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
 expr := add(div(expr_1, _1), iszero(iszero(mod(expr_1, _1))))
 var := expr
 }
 function fun_getAmount0Delta_40419(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
 {
 let var_roundUp := 0x00
 if gt( and( var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and( var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
 {
 let expr_component := var_sqrtPriceBX96
 var_sqrtPriceBX96 := var_sqrtPriceAX96
 var_sqrtPriceAX96 := expr_component
 }
 let _1 := and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(_1)
 {
 mstore( 0x00, 0x00bfc921)
 revert(0x1c, 0x04)
 }
 let expr := 0x00
 var_roundUp := 0x00
 expr := wrapping_div_uint256( fun_mulDiv( and(shl( 0x60, var_liquidity), 0xffffffffffffffffffffffffffffffff000000000000000000000000), and( sub( var_sqrtPriceBX96, var_sqrtPriceAX96), 0xffffffffffffffffffffffffffffffffffffffff), and( var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff)), _1)
 var := expr
 }
 function fun_mostSignificantBit(var_x) -> var_r
 {
 if iszero(var_x)
 {
 revert( 0x00, 0x00)
 }
 let var_r_1 := shl(7, lt(0xffffffffffffffffffffffffffffffff, var_x))
 let var_r_2 := or(var_r_1, shl(6, lt(0xffffffffffffffff, shr(var_r_1, var_x))))
 let var_r_3 := or(var_r_2, shl(5, lt(0xffffffff, shr(var_r_2, var_x))))
 let var_r_4 := or(var_r_3, shl(4, lt(0xffff, shr(var_r_3, var_x))))
 let var_r_5 := or(var_r_4, shl(3, lt(0xff, shr(var_r_4, var_x))))
 var_r := or(var_r_5, byte(and(0x1f, shr(shr(var_r_5, var_x), 0x8421084210842108cc6318c6db6d54be)), 0x0706060506020500060203020504000106050205030304010505030400000000))
 }
 function fun_mulDivRoundingUp(var_a, var_b, var_denominator) -> var_result
 {
 var_result := fun_mulDiv(var_a, var_b, var_denominator)
 if iszero(var_denominator)
 {
 mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
 mstore(4, 0x12)
 revert(0, 0x24)
 }
 if iszero(iszero( mulmod(var_a, var_b, var_denominator)))
 {
 var_result := add( var_result, 1)
 if iszero(var_result)
 {
 revert( 0x00, 0x00)
 }
 }
 }
 function fun_getNextSqrtPriceFromAmount0RoundingUp_40426(var_sqrtPX96, var_liquidity, var_amount) -> var
 {
 let var_add := 0
 var := 0
 if iszero(var_amount)
 {
 var := var_sqrtPX96
 leave
 }
 let result := and(shl( 0x60, var_liquidity), 0xffffffffffffffffffffffffffffffff000000000000000000000000)
 var_add := 0
 let _1 := and( var_sqrtPX96, 0xffffffffffffffffffffffffffffffffffffffff)
 let expr := mul( var_amount, _1)
 if iszero(and(eq(div(expr, var_amount), _1), gt(result, expr)))
 {
 mstore( 0, 0xf5c787f1)
 revert(0x1c, 0x04)
 }
 var := fun_toUint160( fun_mulDivRoundingUp(result, _1, sub( result, expr)))
 }
 function fun_getNextSqrtPriceFromAmount0RoundingUp(var_sqrtPX96, var_liquidity, var_amount) -> var
 {
 var := 0
 if iszero(var_amount)
 {
 var := var_sqrtPX96
 leave
 }
 let result := and(shl( 0x60, var_liquidity), 0xffffffffffffffffffffffffffffffff000000000000000000000000)
 let _1 := and( var_sqrtPX96, 0xffffffffffffffffffffffffffffffffffffffff)
 let expr := mul( var_amount, _1)
 if eq( wrapping_div_uint256(expr, var_amount), _1)
 {
 let expr_1 := add( result, expr)
 if iszero(lt(expr_1, result))
 {
 var := and( fun_mulDivRoundingUp(result, _1, expr_1), 0xffffffffffffffffffffffffffffffffffffffff)
 leave
 }
 }
 let _2 := checked_add_uint256( wrapping_div_uint256(result, _1), var_amount)
 var := and( add(div(result, _2), iszero(iszero(mod(result, _2)))), 0xffffffffffffffffffffffffffffffffffffffff)
 }
 function fun_toUint160(var_x) -> var_y
 {
 var_y := and( var_x, 0xffffffffffffffffffffffffffffffffffffffff)
 if iszero(eq( var_y, var_x))
 {
 mstore(0, 0x93dafdf100000000000000000000000000000000000000000000000000000000)
 revert(0, 0x04)
 }
 }
 }
 data ".metadata" hex"a164736f6c634300081a000a"
 }
}
