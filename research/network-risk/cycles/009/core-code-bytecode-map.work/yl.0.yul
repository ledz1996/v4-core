/// @use-src 0:"solmate/src/auth/Owned.sol", 1:"src/ERC6909.sol", 2:"src/ERC6909Claims.sol", 3:"src/Extsload.sol", 4:"src/Exttload.sol", 5:"src/NoDelegateCall.sol", 6:"src/PoolManager.sol", 7:"src/ProtocolFees.sol", 8:"src/interfaces/IExtsload.sol", 9:"src/interfaces/IExttload.sol", 11:"src/interfaces/IPoolManager.sol", 12:"src/interfaces/IProtocolFees.sol", 15:"src/interfaces/external/IERC6909Claims.sol"
object "PoolManager_1216" {
    code {
        {
            /// @src 6:4791:17612
            let _1 := memoryguard(0xa0)
            if callvalue() { revert(0, 0) }
            let programSize := datasize("PoolManager_1216")
            let argSize := sub(codesize(), programSize)
            let newFreePtr := add(_1, and(add(argSize, 31), not(31)))
            if or(gt(newFreePtr, sub(shl(64, 1), 1)), lt(newFreePtr, _1))
            {
                mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ shl(224, 0x4e487b71))
                mstore(4, 0x41)
                revert(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x24)
            }
            mstore(64, newFreePtr)
            codecopy(_1, programSize, argSize)
            if slt(sub(add(_1, argSize), _1), 32)
            {
                revert(/** @src -1:-1:-1 */ 0, 0)
            }
            /// @src 6:4791:17612
            let value := mload(_1)
            let _2 := and(value, sub(shl(160, 1), 1))
            if iszero(eq(value, _2))
            {
                revert(/** @src -1:-1:-1 */ 0, 0)
            }
            /// @src 6:4791:17612
            sstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ or(and(sload(/** @src -1:-1:-1 */ 0), /** @src 6:4791:17612 */ not(sub(shl(160, 1), 1))), _2))
            /// @src 0:1075:1115
            let _3 := /** @src 6:4791:17612 */ mload(64)
            /// @src 0:1075:1115
            log3(/** @src -1:-1:-1 */ 0, 0, /** @src 0:1075:1115 */ 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0, /** @src -1:-1:-1 */ 0, /** @src 0:1075:1115 */ _2)
            /// @src 5:700:724
            mstore(128, /** @src 5:719:723 */ address())
            /// @src 6:4791:17612
            let _4 := datasize("PoolManager_1216_deployed")
            codecopy(_3, dataoffset("PoolManager_1216_deployed"), _4)
            setimmutable(_3, "1375", mload(/** @src 5:700:724 */ 128))
            /// @src 6:4791:17612
            return(_3, _4)
        }
    }
    /// @use-src 0:"solmate/src/auth/Owned.sol", 1:"src/ERC6909.sol", 2:"src/ERC6909Claims.sol", 3:"src/Extsload.sol", 4:"src/Exttload.sol", 5:"src/NoDelegateCall.sol", 6:"src/PoolManager.sol", 7:"src/ProtocolFees.sol", 16:"src/libraries/BitMath.sol", 17:"src/libraries/CurrencyDelta.sol", 18:"src/libraries/CurrencyReserves.sol", 19:"src/libraries/CustomRevert.sol", 20:"src/libraries/FixedPoint128.sol", 21:"src/libraries/FixedPoint96.sol", 22:"src/libraries/FullMath.sol", 23:"src/libraries/Hooks.sol", 24:"src/libraries/LPFeeLibrary.sol", 25:"src/libraries/LiquidityMath.sol", 26:"src/libraries/Lock.sol", 27:"src/libraries/NonzeroDeltaCount.sol", 28:"src/libraries/ParseBytes.sol", 29:"src/libraries/Pool.sol", 30:"src/libraries/Position.sol", 31:"src/libraries/ProtocolFeeLibrary.sol", 32:"src/libraries/SafeCast.sol", 33:"src/libraries/SqrtPriceMath.sol", 34:"src/libraries/SwapMath.sol", 35:"src/libraries/TickBitmap.sol", 36:"src/libraries/TickMath.sol", 37:"src/libraries/UnsafeMath.sol", 38:"src/types/BalanceDelta.sol", 39:"src/types/BeforeSwapDelta.sol", 40:"src/types/Currency.sol", 41:"src/types/PoolId.sol", 44:"src/types/Slot0.sol"
    object "PoolManager_1216_deployed" {
        code {
            {
                /// @src 6:4791:17612
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
                        /// @src 1:2762:2862
                        let expr := /** @src 1:2762:2787 */ eq(_2, /** @src 6:4791:17612 */ 0x01ffc9a700000000000000000000000000000000000000000000000000000000)
                        /// @src 1:2762:2862
                        if iszero(expr)
                        {
                            expr := /** @src 1:2837:2862 */ eq(_2, /** @src 6:4791:17612 */ 0x0f632fb300000000000000000000000000000000000000000000000000000000)
                        }
                        let memPos := mload(64)
                        mstore(memPos, iszero(iszero(expr)))
                        return(memPos, 32)
                    }
                    case 0x095bcdb6 {
                        if callvalue() { revert(0, 0) }
                        let param, param_1, param_2 := abi_decode_addresst_uint256t_uint256(calldatasize())
                        mstore(0, /** @src 1:1292:1302 */ caller())
                        /// @src 6:4791:17612
                        mstore(0x20, 4)
                        let dataSlot_1 := keccak256(0, 64)
                        mstore(0, param_1)
                        mstore(0x20, dataSlot_1)
                        let dataSlot_2 := keccak256(0, 64)
                        sstore(dataSlot_2, /** @src 1:1282:1317 */ checked_sub_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:1282:1317 */ dataSlot_2), param_2))
                        /// @src 6:4791:17612
                        let _3 := and(param, 0xffffffffffffffffffffffffffffffffffffffff)
                        mstore(0, _3)
                        mstore(0x20, 4)
                        let dataSlot_3 := keccak256(0, 64)
                        mstore(0, param_1)
                        mstore(0x20, dataSlot_3)
                        let dataSlot_4 := keccak256(0, 64)
                        sstore(dataSlot_4, /** @src 1:1328:1361 */ checked_add_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:1328:1361 */ dataSlot_4), param_2))
                        /// @src 1:1377:1431
                        let _4 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 1:1377:1431
                        log4(_4, sub(abi_encode_address_uint256(_4, /** @src 1:1292:1302 */ caller(), /** @src 1:1377:1431 */ param_2), _4), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, /** @src 1:1292:1302 */ caller(), /** @src 1:1377:1431 */ _3, param_1)
                        /// @src 6:4791:17612
                        let memPos_1 := mload(64)
                        mstore(memPos_1, /** @src 1:1449:1453 */ 0x01)
                        /// @src 6:4791:17612
                        return(memPos_1, 0x20)
                    }
                    case 0x0b0d9c09 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
                        let value0 := abi_decode_address()
                        let value1 := abi_decode_address_40277()
                        let value_1 := calldataload(68)
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        let ret := signextend(15, sub(0, /** @src 6:13498:13515 */ fun_toInt128_5750(value_1)))
                        /// @src 6:13518:13528
                        fun_accountDelta(value0, ret, caller())
                        /// @src 6:13565:13571
                        fun_transfer(value0, value1, value_1)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0x11da60b4 {
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0) }
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:13708:13734
                        let var := /** @src 6:13715:13734 */ fun_settle(/** @src 6:13723:13733 */ caller())
                        /// @src 6:4791:17612
                        let memPos_2 := mload(64)
                        mstore(memPos_2, var)
                        return(memPos_2, 32)
                    }
                    case 0x156e29f6 {
                        if callvalue() { revert(0, 0) }
                        let param_3, param_4, param_5 := abi_decode_addresst_uint256t_uint256(calldatasize())
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        let cleaned := and(param_4, 0xffffffffffffffffffffffffffffffffffffffff)
                        let ret_1 := signextend(15, sub(0, /** @src 6:14759:14776 */ fun_toInt128_5750(param_5)))
                        /// @src 6:14779:14789
                        fun_accountDelta(cleaned, ret_1, caller())
                        /// @src 6:4791:17612
                        let _5 := and(param_3, 0xffffffffffffffffffffffffffffffffffffffff)
                        mstore(0, _5)
                        mstore(0x20, 4)
                        let dataSlot_5 := keccak256(0, 64)
                        mstore(0, cleaned)
                        mstore(0x20, dataSlot_5)
                        let dataSlot_6 := keccak256(0, 64)
                        sstore(dataSlot_6, /** @src 1:3186:3219 */ checked_add_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:3186:3219 */ dataSlot_6), param_5))
                        /// @src 1:3235:3289
                        let _6 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 1:3235:3289
                        log4(_6, sub(abi_encode_address_uint256(_6, /** @src 6:14779:14789 */ caller(), /** @src 1:3235:3289 */ param_5), _6), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, /** @src 6:4791:17612 */ 0, /** @src 1:3235:3289 */ _5, cleaned)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0x1e2eaeaf {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        /// @src 3:411:510
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 3:411:510 */ sload(/** @src 6:4791:17612 */ calldataload(4)))
                        /// @src 3:411:510
                        return(/** @src 6:4791:17612 */ 0, 32)
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
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 5:1169:1245
                        fun_checkNotDelegateCall()
                        /// @src 6:12252:12262
                        let expr_1 := /** @src 41:357:530 */ keccak256(/** @src 6:12252:12262 */ value0_1, /** @src 6:4791:17612 */ 160)
                        mstore(0, expr_1)
                        mstore(0x20, /** @src 6:17402:17408 */ 0x06)
                        /// @src 6:4791:17612
                        let dataSlot_7 := keccak256(0, 64)
                        /// @src 6:12324:12349
                        fun_checkPoolInitialized(dataSlot_7)
                        /// @src 6:12362:12371
                        let _7 := add(value0_1, 128)
                        /// @src 6:4791:17612
                        let _8 := mload(/** @src 6:12362:12371 */ _7)
                        /// @src 6:4791:17612
                        let cleaned_1 := and(_8, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 23:8810:8869
                        if /** @src 23:8814:8841 */ iszero(eq(/** @src 23:8814:8824 */ caller(), /** @src 6:4791:17612 */ cleaned_1))
                        /// @src 23:8810:8869
                        {
                            /// @src 23:15770:15808
                            let var_1 := /** @src 6:4791:17612 */ 0
                            /// @src 23:16460:16501
                            var_1 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _8, 0x20)))
                            /// @src 23:15766:15932
                            if /** @src 23:15770:15808 */ var_1
                            /// @src 23:15766:15932
                            {
                                /// @src 23:15838:15920
                                let expr_mpos := /** @src 6:4791:17612 */ mload(64)
                                /// @src 23:15838:15920
                                mstore(add(expr_mpos, /** @src 6:4791:17612 */ 0x20), /** @src 23:15838:15920 */ 0xb6a8b0fa00000000000000000000000000000000000000000000000000000000)
                                let _9 := sub(abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(add(expr_mpos, 36), /** @src 23:8814:8824 */ caller(), /** @src 23:15838:15920 */ value0_1, value_2, value_3, value3, value4), expr_mpos)
                                mstore(expr_mpos, add(_9, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                finalize_allocation(expr_mpos, _9)
                                /// @src 23:15824:15921
                                pop(fun_callHook(cleaned_1, expr_mpos))
                            }
                        }
                        /// @src 6:4791:17612
                        let cleaned_2 := and(sload(/** @src 29:22076:22091 */ add(dataSlot_7, 3)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                        /// @src 29:22101:22167
                        if /** @src 29:22105:22119 */ iszero(/** @src 6:4791:17612 */ cleaned_2)
                        /// @src 29:22101:22167
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 29:22121:22154 */ 0xa74f97ab00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        let _10 := sub(0, /** @src 29:22298:22316 */ fun_toInt128_5750(value_2))
                        /// @src 38:553:668
                        let var_balanceDelta := or(shl(/** @src 6:12362:12371 */ 128, /** @src 6:4791:17612 */ _10), /** @src 38:553:668 */ and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, sub(0, /** @src 29:22321:22339 */ fun_toInt128_5750(value_3))))
                        /// @src 29:22499:22642
                        if /** @src 29:22503:22514 */ iszero(iszero(value_2))
                        /// @src 29:22499:22642
                        {
                            /// @src 29:22534:22560
                            let _11 := add(dataSlot_7, /** @src 6:4791:17612 */ 1)
                            sstore(_11, /** @src 20:258:293 */ add(/** @src 6:4791:17612 */ sload(/** @src 29:22534:22627 */ _11), /** @src 37:1070:1156 */ div(shl(/** @src 6:12362:12371 */ 128, /** @src 29:22564:22627 */ value_2), /** @src 6:4791:17612 */ cleaned_2)))
                        }
                        /// @src 29:22655:22798
                        if /** @src 29:22659:22670 */ iszero(iszero(value_3))
                        /// @src 29:22655:22798
                        {
                            /// @src 29:22690:22716
                            let _12 := add(dataSlot_7, 2)
                            /// @src 6:4791:17612
                            sstore(_12, /** @src 20:258:293 */ add(/** @src 6:4791:17612 */ sload(/** @src 29:22690:22783 */ _12), /** @src 37:1070:1156 */ div(shl(/** @src 6:12362:12371 */ 128, /** @src 29:22720:22783 */ value_3), /** @src 6:4791:17612 */ cleaned_2)))
                        }
                        /// @src 6:12513:12523
                        fun_accountPoolBalanceDelta(value0_1, var_balanceDelta, /** @src 23:8814:8824 */ caller())
                        /// @src 6:12641:12685
                        let _13 := /** @src 6:4791:17612 */ mload(64)
                        mstore(_13, value_2)
                        mstore(add(_13, 0x20), value_3)
                        /// @src 6:12641:12685
                        log3(_13, /** @src 6:4791:17612 */ 64, /** @src 6:12641:12685 */ 0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb, expr_1, /** @src 23:8814:8824 */ caller())
                        /// @src 6:4791:17612
                        let _14 := mload(/** @src 6:12696:12705 */ _7)
                        /// @src 6:4791:17612
                        let cleaned_3 := and(_14, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 23:8810:8869
                        if /** @src 23:8814:8841 */ iszero(eq(/** @src 23:8814:8824 */ caller(), /** @src 6:4791:17612 */ cleaned_3))
                        /// @src 23:8810:8869
                        {
                            /// @src 23:16199:16236
                            let var_2 := /** @src 6:4791:17612 */ 0
                            /// @src 23:16460:16501
                            var_2 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _14, 16)))
                            /// @src 23:16195:16359
                            if /** @src 23:16199:16236 */ var_2
                            /// @src 23:16195:16359
                            {
                                /// @src 23:16266:16347
                                let expr_mpos_1 := /** @src 6:4791:17612 */ mload(64)
                                /// @src 23:16266:16347
                                mstore(add(expr_mpos_1, /** @src 6:4791:17612 */ 0x20), /** @src 23:16266:16347 */ 0xe1b4af6900000000000000000000000000000000000000000000000000000000)
                                let _15 := sub(abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(add(expr_mpos_1, 36), /** @src 23:8814:8824 */ caller(), /** @src 23:16266:16347 */ value0_1, value_2, value_3, value3, value4), expr_mpos_1)
                                mstore(expr_mpos_1, add(_15, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                finalize_allocation(expr_mpos_1, _15)
                                /// @src 23:16252:16348
                                pop(fun_callHook(cleaned_3, expr_mpos_1))
                            }
                        }
                        /// @src 6:4791:17612
                        let memPos_3 := mload(64)
                        mstore(memPos_3, var_balanceDelta)
                        return(memPos_3, 0x20)
                    }
                    case 0x2d771389 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        let value0_2 := abi_decode_address()
                        /// @src 0:756:800
                        require_helper_stringliteral_269d(/** @src 0:764:783 */ eq(/** @src 0:764:774 */ caller(), /** @src 6:4791:17612 */ and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)))
                        let _16 := and(value0_2, 0xffffffffffffffffffffffffffffffffffffffff)
                        sstore(/** @src 7:1153:1187 */ 0x02, /** @src 6:4791:17612 */ or(and(sload(/** @src 7:1153:1187 */ 0x02), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), _16))
                        /// @src 7:1202:1242
                        log2(/** @src 6:4791:17612 */ 0, 0, /** @src 7:1202:1242 */ 0xb4bd8ef53df690b9943d3318996006dbb82a25f54719d8c8035b516a2a5b8acc, _16)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0x35fd631a {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
                        let value_4 := calldataload(36)
                        /// @ast-id 1319 @src 3:552:1533
                        let /// @ast-id 1319
                        var_startSlot := /** @src 6:4791:17612 */ calldataload(4)
                        /// @src 3:656:1527
                        let usr$memptr := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 3:656:1527
                        let usr$memptr_1 := usr$memptr
                        mstore(usr$memptr, /** @src 6:4791:17612 */ 32)
                        /// @src 3:656:1527
                        mstore(add(usr$memptr, /** @src 6:4791:17612 */ 32), /** @src 3:656:1527 */ value_4)
                        usr$memptr := add(usr$memptr, /** @src 6:4791:17612 */ 64)
                        /// @src 3:656:1527
                        let _17 := add(usr$memptr_1, shl(5, value_4))
                        let usr$end := add(_17, /** @src 6:4791:17612 */ 64)
                        /// @src 3:656:1527
                        for { }
                        /** @src 6:4791:17612 */ 1
                        /// @src 3:656:1527
                        { }
                        {
                            mstore(usr$memptr, sload(var_startSlot))
                            usr$memptr := add(usr$memptr, /** @src 6:4791:17612 */ 32)
                            /// @src 3:656:1527
                            var_startSlot := add(var_startSlot, /** @src 6:4791:17612 */ 1)
                            /// @src 3:656:1527
                            if iszero(lt(usr$memptr, usr$end)) { break }
                        }
                        return(usr$memptr_1, add(sub(_17, usr$memptr_1), /** @src 6:4791:17612 */ 64))
                    }
                    case 0x3dd45adb {
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        let value0_3 := abi_decode_address()
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:5494:5495
                        let _18 := /** @src 6:13887:13905 */ fun_settle(/** @src 6:5494:5495 */ value0_3)
                        /// @src 6:4791:17612
                        let memPos_4 := mload(64)
                        mstore(memPos_4, _18)
                        return(memPos_4, 32)
                    }
                    case 0x426a8493 {
                        if callvalue() { revert(0, 0) }
                        let param_6, param_7, param_8 := abi_decode_addresst_uint256t_uint256(calldatasize())
                        mstore(0, /** @src 1:2125:2135 */ caller())
                        /// @src 6:4791:17612
                        mstore(0x20, /** @src 1:2115:2124 */ 0x05)
                        /// @src 6:4791:17612
                        let dataSlot_8 := keccak256(0, 64)
                        /// @src 1:2115:2145
                        let dataSlot_9 := /** @src -1:-1:-1 */ 0
                        /// @src 6:4791:17612
                        mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:2115:2145 */ param_6, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0x20, /** @src 1:2115:2136 */ dataSlot_8)
                        /// @src 6:4791:17612
                        dataSlot_9 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                        mstore(0, param_7)
                        mstore(0x20, /** @src 1:2115:2145 */ dataSlot_9)
                        /// @src 6:4791:17612
                        sstore(keccak256(0, 64), param_8)
                        /// @src 1:2174:2215
                        let _19 := /** @src 6:4791:17612 */ mload(64)
                        mstore(_19, param_8)
                        /// @src 1:2174:2215
                        log4(_19, /** @src 6:4791:17612 */ 0x20, /** @src 1:2174:2215 */ 0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7, /** @src 1:2125:2135 */ caller(), /** @src 6:4791:17612 */ and(/** @src 1:2174:2215 */ param_6, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), /** @src 1:2174:2215 */ param_7)
                        /// @src 6:4791:17612
                        let memPos_5 := mload(64)
                        mstore(memPos_5, /** @src 1:2233:2237 */ 0x01)
                        /// @src 6:4791:17612
                        return(memPos_5, 0x20)
                    }
                    case 0x48c89491 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        let offset_1 := calldataload(4)
                        if gt(offset_1, 0xffffffffffffffff) { revert(0, 0) }
                        let value0_4, value1_1 := abi_decode_bytes_calldata(add(4, offset_1), calldatasize())
                        /// @src 6:5705:5765
                        if /** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923)
                        /// @src 6:5705:5765
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5728:5752 */ 0x5090d6c600000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 26:527:628
                        log2(/** @src 6:4791:17612 */ 0, 0, /** @src 26:837:921 */ 87100234046427240614499661373387320107015461065347489303548037305558901893923, /** @src 26:527:628 */ true)
                        /// @src 6:5916:5964
                        let _20 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 6:5916:5964
                        mstore(_20, /** @src 6:4791:17612 */ 0x91dd734600000000000000000000000000000000000000000000000000000000)
                        mstore(/** @src 6:5916:5964 */ add(_20, /** @src 6:4791:17612 */ 4), 32)
                        /// @src 6:5916:5964
                        let _21 := call(gas(), /** @src 6:5932:5942 */ caller(), /** @src 6:4791:17612 */ 0, /** @src 6:5916:5964 */ _20, sub(/** @src 6:4791:17612 */ abi_encode_bytes_calldata(value0_4, value1_1, add(/** @src 6:5916:5964 */ _20, /** @src 6:4791:17612 */ 36)), /** @src 6:5916:5964 */ _20), _20, /** @src 6:4791:17612 */ 0)
                        /// @src 6:5916:5964
                        if iszero(_21)
                        {
                            /// @src 6:4791:17612
                            let pos := mload(64)
                            returndatacopy(pos, 0, returndatasize())
                            revert(pos, returndatasize())
                        }
                        /// @src 6:5916:5964
                        let expr_mpos_2 := /** @src 6:4791:17612 */ 0
                        /// @src 6:5916:5964
                        if _21
                        {
                            let _22 := returndatasize()
                            returndatacopy(_20, /** @src 6:4791:17612 */ 0, /** @src 6:5916:5964 */ _22)
                            finalize_allocation(_20, _22)
                            let _23 := add(_20, _22)
                            /// @src 6:4791:17612
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
                            /// @src 6:5916:5964
                            expr_mpos_2 := memPtr
                        }
                        /// @src 6:5975:6050
                        if /** @src 6:5979:6008 */ iszero(iszero(/** @src 27:622:711 */ extcodehash(56671960505278111519104690822132496699113179860588238901689140059013086026251)))
                        /// @src 6:5975:6050
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:6010:6037 */ 0x5212cba100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 26:675:755
                        log2(/** @src 6:4791:17612 */ 0, 0, /** @src 26:837:921 */ 87100234046427240614499661373387320107015461065347489303548037305558901893923, /** @src 26:675:755 */ false)
                        /// @src 6:4791:17612
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
                        /// @src 24:1372:1403
                        let var_3 := /** @src 24:1379:1403 */ eq(/** @src 6:4791:17612 */ and(mload(/** @src 6:15288:15295 */ add(value0_5, /** @src 6:4791:17612 */ 64)), 0xffffff), /** @src 24:552:560 */ 0x800000)
                        /// @src 6:15287:15346
                        let expr_2 := /** @src 6:15287:15310 */ iszero(/** @src 6:15288:15310 */ var_3)
                        /// @src 6:15287:15346
                        if var_3
                        {
                            expr_2 := /** @src 6:15314:15346 */ iszero(eq(/** @src 6:15314:15324 */ caller(), /** @src 6:4791:17612 */ and(mload(/** @src 6:15336:15345 */ add(value0_5, 128)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)))
                        }
                        /// @src 6:15283:15425
                        if expr_2
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:15362:15401 */ 0x30d2164100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:15434:15458
                        fun_validate(value1_2)
                        /// @src 6:4791:17612
                        mstore(0, /** @src 41:357:530 */ keccak256(/** @src 6:15482:15492 */ value0_5, /** @src 6:4791:17612 */ 160))
                        mstore(0x20, /** @src 6:15502:15508 */ 0x06)
                        /// @src 6:4791:17612
                        let dataSlot_10 := keccak256(0, 64)
                        /// @src 29:5306:5331
                        fun_checkPoolInitialized(dataSlot_10)
                        /// @src 6:4791:17612
                        let _25 := sload(/** @src 29:5356:5366 */ dataSlot_10)
                        /// @src 6:4791:17612
                        sstore(dataSlot_10, /** @src 44:3217:3395 */ or(and(0xffffff000000ffffffffffffffffffffffffffffffffffffffffffffffffffff, _25), and(shl(208, value1_2), 0xffffff0000000000000000000000000000000000000000000000000000)))
                        /// @src 6:4791:17612
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
                        mstore(0, /** @src 1:2355:2365 */ caller())
                        /// @src 6:4791:17612
                        mstore(32, /** @src 1:2344:2354 */ 0x03)
                        /// @src 6:4791:17612
                        let dataSlot_11 := keccak256(0, 64)
                        /// @src 1:2344:2376
                        let dataSlot_12 := /** @src -1:-1:-1 */ 0
                        /// @src 6:4791:17612
                        mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:2344:2376 */ value0_6, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0x20, /** @src 1:2344:2366 */ dataSlot_11)
                        /// @src 6:4791:17612
                        dataSlot_12 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                        let value_6 := and(sload(/** @src 1:2344:2376 */ dataSlot_12), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)
                        sstore(/** @src 1:2344:2376 */ dataSlot_12, /** @src 6:4791:17612 */ or(value_6, and(_26, 255)))
                        /// @src 1:2403:2446
                        let _27 := /** @src 6:4791:17612 */ mload(64)
                        mstore(_27, _26)
                        /// @src 1:2403:2446
                        log3(_27, /** @src 6:4791:17612 */ 32, /** @src 1:2403:2446 */ 0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267, /** @src 1:2355:2365 */ caller(), /** @src 6:4791:17612 */ and(/** @src 1:2403:2446 */ value0_6, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        let memPos_7 := mload(64)
                        mstore(memPos_7, /** @src 1:2464:2468 */ 0x01)
                        /// @src 6:4791:17612
                        return(memPos_7, 32)
                    }
                    case 0x598af9e7 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
                        let value0_7 := abi_decode_address()
                        let value1_3 := abi_decode_address_40277()
                        mstore(0, and(value0_7, 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(32, /** @src 1:880:988 */ 5)
                        /// @src 6:4791:17612
                        let dataSlot_13 := keccak256(0, 64)
                        /// @src 1:880:988
                        let dataSlot_14 := /** @src -1:-1:-1 */ 0
                        /// @src 6:4791:17612
                        mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:880:988 */ value1_3, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0x20, /** @src 1:880:988 */ dataSlot_13)
                        /// @src 6:4791:17612
                        dataSlot_14 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                        mstore(0, calldataload(68))
                        mstore(32, /** @src 1:880:988 */ dataSlot_14)
                        /// @src 6:4791:17612
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
                        finalize_allocation_40292(memPtr_1)
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
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 5:1169:1245
                        fun_checkNotDelegateCall()
                        /// @src 6:7868:7878
                        let expr_3 := /** @src 41:357:530 */ keccak256(/** @src 6:7868:7878 */ value0_8, /** @src 6:4791:17612 */ 160)
                        mstore(0, expr_3)
                        mstore(32, /** @src 6:17402:17408 */ 0x06)
                        /// @src 6:4791:17612
                        mstore(0x80, keccak256(0, 64))
                        /// @src 6:7954:7979
                        fun_checkPoolInitialized(mload(0x80))
                        /// @src 6:4791:17612
                        let _29 := mload(/** @src 6:7996:8005 */ add(value0_8, /** @src 6:4791:17612 */ 0x80))
                        let cleaned_4 := and(_29, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 23:8810:8869
                        if /** @src 23:8814:8841 */ iszero(eq(/** @src 23:8814:8824 */ caller(), /** @src 6:4791:17612 */ cleaned_4))
                        /// @src 23:8810:8869
                        {
                            /// @src 23:9963:10037
                            let expr_4 := /** @src 23:9963:9988 */ sgt(/** @src 6:4791:17612 */ mload(add(memPtr_1, 64)), 0)
                            /// @src 23:9963:9988
                            let expr_5 := /** @src 23:9963:10037 */ expr_4
                            if expr_4
                            {
                                /// @src 23:9992:10037
                                let var_4 := /** @src 6:4791:17612 */ 0
                                /// @src 23:16460:16501
                                var_4 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _29, 2048)))
                                /// @src 23:9963:10037
                                expr_4 := var_4
                            }
                            /// @src 23:9959:10368
                            switch expr_4
                            case 0 {
                                /// @src 23:10167:10245
                                let expr_6 := /** @src 23:10167:10193 */ iszero(expr_5)
                                /// @src 23:10167:10245
                                if expr_6
                                {
                                    /// @src 23:10197:10245
                                    let var_5 := /** @src 6:4791:17612 */ 0
                                    /// @src 23:16460:16501
                                    var_5 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _29, 512)))
                                    /// @src 23:10167:10245
                                    expr_6 := var_5
                                }
                                /// @src 23:10163:10368
                                if expr_6
                                {
                                    /// @src 23:10275:10356
                                    let expr_mpos_3 := /** @src 6:4791:17612 */ mload(64)
                                    /// @src 23:10275:10356
                                    mstore(add(expr_mpos_3, /** @src 6:4791:17612 */ 32), /** @src 23:10275:10356 */ 0x21d0ee7000000000000000000000000000000000000000000000000000000000)
                                    let _30 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(add(expr_mpos_3, 36), /** @src 23:8814:8824 */ caller(), /** @src 23:10275:10356 */ value0_8, memPtr_1, value2, value3_1), expr_mpos_3)
                                    mstore(expr_mpos_3, add(_30, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                    finalize_allocation(expr_mpos_3, _30)
                                    /// @src 23:10261:10357
                                    pop(fun_callHook(cleaned_4, expr_mpos_3))
                                }
                            }
                            default /// @src 23:9959:10368
                            {
                                /// @src 23:10067:10145
                                let expr_mpos_4 := /** @src 6:4791:17612 */ mload(64)
                                /// @src 23:10067:10145
                                mstore(add(expr_mpos_4, /** @src 6:4791:17612 */ 32), /** @src 23:10067:10145 */ 0x259982e500000000000000000000000000000000000000000000000000000000)
                                let _31 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(add(expr_mpos_4, 36), /** @src 23:8814:8824 */ caller(), /** @src 23:10067:10145 */ value0_8, memPtr_1, value2, value3_1), expr_mpos_4)
                                mstore(expr_mpos_4, add(_31, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                finalize_allocation(expr_mpos_4, _31)
                                /// @src 23:10053:10146
                                pop(fun_callHook(cleaned_4, expr_mpos_4))
                            }
                        }
                        /// @src 6:4791:17612
                        let cleaned_5 := signextend(2, mload(/** @src 6:8275:8291 */ memPtr_1))
                        /// @src 6:4791:17612
                        let cleaned_6 := signextend(2, mload(add(memPtr_1, 32)))
                        /// @src 6:8378:8410
                        let expr_7 := fun_toInt128(/** @src 6:4791:17612 */ mload(add(memPtr_1, 64)))
                        let cleaned_7 := signextend(2, mload(/** @src 6:8445:8460 */ add(value0_8, /** @src 6:4791:17612 */ 96)))
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
                        mstore(memPtr_2, /** @src 23:8814:8824 */ caller())
                        /// @src 6:4791:17612
                        mstore(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 32), cleaned_5)
                        mstore(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 64), cleaned_6)
                        mstore(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 96), signextend(15, expr_7))
                        mstore(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 0x80), cleaned_7)
                        mstore(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 160), _32)
                        /// @src 6:8138:8532
                        let var_delta := /** @src 6:4791:17612 */ 0
                        /// @src 29:6526:6544
                        var_delta := /** @src 6:4791:17612 */ 0
                        /// @src 29:4259:4344
                        if /** @src 29:4263:4285 */ iszero(slt(cleaned_5, cleaned_6))
                        /// @src 29:4259:4344
                        {
                            /// @src 19:2092:2343
                            let usr$fmp := mload(/** @src 6:4791:17612 */ 64)
                            /// @src 19:2092:2343
                            mstore(usr$fmp, /** @src 29:4287:4311 */ 0xc4433ed500000000000000000000000000000000000000000000000000000000)
                            /// @src 19:2092:2343
                            mstore(add(usr$fmp, /** @src 6:4791:17612 */ 4), /** @src 19:2092:2343 */ cleaned_5)
                            mstore(add(usr$fmp, 0x24), cleaned_6)
                            revert(usr$fmp, 0x44)
                        }
                        /// @src 29:4354:4440
                        if /** @src 29:4358:4387 */ slt(cleaned_5, /** @src 36:1032:1039 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618)
                        /// @src 29:4354:4440
                        {
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 29:4389:4418 */ 0xd5e2f7ab00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_5)
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                        }
                        /// @src 29:4450:4536
                        if /** @src 29:4454:4483 */ sgt(cleaned_6, /** @src 36:1317:1323 */ 0x0d89e8)
                        /// @src 29:4450:4536
                        {
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 29:4485:4514 */ 0x1ad777f800000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_6)
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                        }
                        /// @src 6:4791:17612
                        let memPtr_3 := mload(64)
                        finalize_allocation_40292(memPtr_3)
                        mstore(memPtr_3, 0)
                        mstore(add(memPtr_3, 32), 0)
                        mstore(add(memPtr_3, 64), 0)
                        mstore(add(memPtr_3, 96), 0)
                        /// @src 29:6884:8072
                        if /** @src 29:6888:6907 */ iszero(iszero(/** @src 6:4791:17612 */ signextend(15, expr_7)))
                        /// @src 29:6884:8072
                        {
                            /// @src 29:7002:7052
                            let var_flipped := /** @src 6:4791:17612 */ 0
                            /// @src 29:7002:7052
                            let var_liquidityGrossAfter := /** @src 6:4791:17612 */ 0
                            /// @ast-id 5302 @src 29:25241:27171
                            let var_upper := /** @src 6:4791:17612 */ 0
                            /// @src 29:25443:25453
                            let _33 := add(mload(0x80), /** @src 6:4791:17612 */ 4)
                            /// @src 29:25443:25459
                            let dataSlot_15 := /** @src 6:4791:17612 */ 0
                            mstore(0, signextend(2, /** @src 29:25443:25459 */ cleaned_5))
                            /// @src 6:4791:17612
                            mstore(0x20, /** @src 29:25443:25453 */ _33)
                            /// @src 6:4791:17612
                            dataSlot_15 := keccak256(0, 0x40)
                            let _34 := sload(/** @src 29:25443:25459 */ dataSlot_15)
                            /// @src 6:4791:17612
                            let cleaned_8 := and(_34, 0xffffffffffffffffffffffffffffffff)
                            /// @src 29:25586:25668
                            var_liquidityGrossAfter := /** @src 29:25608:25668 */ fun_addDelta(cleaned_8, /** @src 6:4791:17612 */ signextend(15, expr_7))
                            let _35 := and(/** @src 29:25690:25714 */ var_liquidityGrossAfter, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                            /// @src 29:25720:25745
                            let expr_8 := iszero(/** @src 6:4791:17612 */ cleaned_8)
                            /// @src 29:25679:25746
                            var_flipped := /** @src 29:25689:25746 */ iszero(eq(/** @src 29:25690:25714 */ iszero(/** @src 6:4791:17612 */ _35), expr_8))
                            /// @src 29:25757:26114
                            if expr_8
                            {
                                /// @src 29:25914:26104
                                if /** @src 29:25918:25943 */ iszero(sgt(/** @src 6:4791:17612 */ cleaned_5, /** @src 44:1682:1780 */ signextend(/** @src 6:4791:17612 */ 2, /** @src 44:1682:1780 */ shr(/** @src 6:4791:17612 */ 160, sload(/** @src 29:25926:25936 */ mload(0x80))))))
                                /// @src 29:25914:26104
                                {
                                    /// @src 6:4791:17612
                                    sstore(/** @src 29:25963:25989 */ add(/** @src 29:25443:25459 */ dataSlot_15, /** @src 6:4791:17612 */ 1), sload(/** @src 29:25992:26017 */ add(mload(0x80), /** @src 6:4791:17612 */ 1)))
                                    sstore(/** @src 29:26035:26061 */ add(/** @src 29:25443:25459 */ dataSlot_15, /** @src 6:4791:17612 */ 2), sload(/** @src 29:26064:26089 */ add(mload(0x80), /** @src 6:4791:17612 */ 2)))
                                }
                            }
                            /// @src 29:26344:26425
                            let expr_9 := /** @src 6:4791:17612 */ 0
                            /// @src 29:26344:26425
                            var_upper := /** @src 6:4791:17612 */ 0
                            /// @src 29:26344:26425
                            expr_9 := /** @src 29:26390:26425 */ checked_add_int128(/** @src 6:4791:17612 */ sar(0x80, _34), signextend(15, expr_7))
                            /// @src 29:26435:27165
                            sstore(/** @src 29:25443:25459 */ dataSlot_15, /** @src 29:26435:27165 */ or(_35, shl(/** @src 6:4791:17612 */ 0x80, /** @src 29:26435:27165 */ expr_9)))
                            /// @src 6:4791:17612
                            mstore(add(memPtr_3, 32), _35)
                            mstore(memPtr_3, var_flipped)
                            /// @src 29:7125:7174
                            let var_flipped_1 := /** @src 6:4791:17612 */ 0
                            /// @src 29:7125:7174
                            let var_liquidityGrossAfter_1 := /** @src 6:4791:17612 */ 0
                            /// @src 29:25443:25459
                            let dataSlot_16 := /** @src 6:4791:17612 */ 0
                            mstore(0, signextend(2, /** @src 29:25443:25459 */ cleaned_6))
                            /// @src 6:4791:17612
                            mstore(0x20, /** @src 29:25443:25453 */ _33)
                            /// @src 6:4791:17612
                            dataSlot_16 := keccak256(0, 0x40)
                            let _36 := sload(/** @src 29:25443:25459 */ dataSlot_16)
                            /// @src 6:4791:17612
                            let cleaned_9 := and(_36, 0xffffffffffffffffffffffffffffffff)
                            /// @src 29:25586:25668
                            var_liquidityGrossAfter_1 := /** @src 29:25608:25668 */ fun_addDelta(cleaned_9, /** @src 6:4791:17612 */ signextend(15, expr_7))
                            /// @src 29:25720:25745
                            let expr_10 := iszero(/** @src 6:4791:17612 */ cleaned_9)
                            /// @src 29:25679:25746
                            var_flipped_1 := /** @src 29:25689:25746 */ iszero(eq(/** @src 29:25690:25714 */ iszero(/** @src 6:4791:17612 */ and(/** @src 29:25690:25714 */ var_liquidityGrossAfter_1, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)), expr_10))
                            /// @src 29:25757:26114
                            if expr_10
                            {
                                /// @src 29:25914:26104
                                if /** @src 29:25918:25943 */ iszero(sgt(/** @src 6:4791:17612 */ cleaned_6, /** @src 44:1682:1780 */ signextend(/** @src 6:4791:17612 */ 2, /** @src 44:1682:1780 */ shr(/** @src 6:4791:17612 */ 160, sload(/** @src 29:25926:25936 */ mload(0x80))))))
                                /// @src 29:25914:26104
                                {
                                    /// @src 6:4791:17612
                                    sstore(/** @src 29:25963:25989 */ add(/** @src 29:25443:25459 */ dataSlot_16, /** @src 6:4791:17612 */ 1), sload(/** @src 29:25992:26017 */ add(mload(0x80), /** @src 6:4791:17612 */ 1)))
                                    sstore(/** @src 29:26035:26061 */ add(/** @src 29:25443:25459 */ dataSlot_16, /** @src 6:4791:17612 */ 2), sload(/** @src 29:26064:26089 */ add(mload(0x80), /** @src 6:4791:17612 */ 2)))
                                }
                            }
                            /// @src 29:26344:26425
                            let expr_11 := /** @src 6:4791:17612 */ 0
                            let diff := sub(signextend(15, sar(0x80, _36)), signextend(15, expr_7))
                            if or(slt(diff, 0xffffffffffffffffffffffffffffffff80000000000000000000000000000000), sgt(diff, 0x7fffffffffffffffffffffffffffffff))
                            {
                                mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                                mstore(4, 0x11)
                                revert(0, 0x24)
                            }
                            /// @src 29:26344:26425
                            expr_11 := diff
                            /// @src 29:26435:27165
                            sstore(/** @src 29:25443:25459 */ dataSlot_16, /** @src 29:26435:27165 */ or(/** @src 6:4791:17612 */ and(/** @src 29:25690:25714 */ var_liquidityGrossAfter_1, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff), /** @src 29:26435:27165 */ shl(/** @src 6:4791:17612 */ 0x80, /** @src 29:26435:27165 */ diff)))
                            /// @src 6:4791:17612
                            mstore(add(memPtr_3, 96), and(/** @src 29:25690:25714 */ var_liquidityGrossAfter_1, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff))
                            mstore(add(memPtr_3, 64), var_flipped_1)
                            /// @src 29:7275:7783
                            if /** @src 29:7279:7298 */ iszero(slt(/** @src 6:4791:17612 */ signextend(15, expr_7), 0))
                            /// @src 29:7275:7783
                            {
                                /// @src 6:4791:17612
                                let cleaned_10 := signextend(2, mload(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 0x80)))
                                let cleaned_11 := and(mload(add(memPtr_3, 32)), 0xffffffffffffffffffffffffffffffff)
                                /// @src 29:7430:7482
                                let _37 := /** @src 6:4791:17612 */ and(/** @src 29:28155:28512 */ div(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:28155:28512 */ add(sub(sdiv(/** @src 36:1317:1323 */ 0x0d89e8, /** @src 29:28155:28512 */ cleaned_10), sub(sdiv(/** @src 36:1032:1039 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618, /** @src 29:28155:28512 */ cleaned_10), slt(smod(/** @src 36:1032:1039 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618, /** @src 29:28155:28512 */ cleaned_10), /** @src 6:4791:17612 */ 0))), 1)), 0xffffffffffffffffffffffffffffffff)
                                /// @src 29:7426:7585
                                if /** @src 29:7430:7482 */ gt(/** @src 6:4791:17612 */ cleaned_11, /** @src 29:7430:7482 */ _37)
                                /// @src 29:7426:7585
                                {
                                    /// @src 19:1431:1574
                                    mstore(/** @src 6:4791:17612 */ 0, /** @src 29:7510:7540 */ 0xb8e3c38500000000000000000000000000000000000000000000000000000000)
                                    /// @src 19:1431:1574
                                    mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_5)
                                    revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                                }
                                /// @src 29:7606:7765
                                if /** @src 29:7610:7662 */ gt(/** @src 6:4791:17612 */ and(mload(add(memPtr_3, 96)), 0xffffffffffffffffffffffffffffffff), /** @src 29:7610:7662 */ _37)
                                /// @src 29:7606:7765
                                {
                                    /// @src 19:1431:1574
                                    mstore(/** @src 6:4791:17612 */ 0, /** @src 29:7690:7720 */ 0xb8e3c38500000000000000000000000000000000000000000000000000000000)
                                    /// @src 19:1431:1574
                                    mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_6)
                                    revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                                }
                            }
                            /// @src 29:7801:7921
                            if /** @src 6:4791:17612 */ iszero(iszero(mload(/** @src 29:7805:7823 */ memPtr_3)))
                            /// @src 29:7801:7921
                            {
                                /// @src 29:7883:7901
                                fun_flipTick(/** @src 29:7847:7862 */ add(mload(0x80), 5), /** @src 29:7883:7901 */ cleaned_5, /** @src 6:4791:17612 */ signextend(2, mload(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 0x80))))
                            }
                            /// @src 29:7938:8058
                            if /** @src 6:4791:17612 */ iszero(iszero(mload(add(memPtr_3, 64))))
                            /// @src 29:7938:8058
                            {
                                /// @src 29:8020:8038
                                fun_flipTick(/** @src 29:7984:7999 */ add(mload(0x80), 5), /** @src 29:8020:8038 */ cleaned_6, /** @src 6:4791:17612 */ signextend(2, mload(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 0x80))))
                            }
                        }
                        /// @src 29:8187:8233
                        let var_feeGrowthInside0X128 := /** @src 6:4791:17612 */ 0
                        /// @src 29:8187:8233
                        let var_feeGrowthInside1X128 := /** @src 6:4791:17612 */ 0
                        /// @src 29:23528:23538
                        let _38 := add(mload(0x80), /** @src 6:4791:17612 */ 4)
                        /// @src 29:23528:23549
                        let dataSlot_17 := /** @src 6:4791:17612 */ 0
                        mstore(0, signextend(2, /** @src 29:23528:23549 */ cleaned_5))
                        /// @src 6:4791:17612
                        mstore(0x20, /** @src 29:23528:23549 */ _38)
                        /// @src 6:4791:17612
                        dataSlot_17 := keccak256(0, 0x40)
                        /// @src 29:23584:23605
                        let dataSlot_18 := /** @src 6:4791:17612 */ 0
                        mstore(0, signextend(2, /** @src 29:23584:23605 */ cleaned_6))
                        /// @src 6:4791:17612
                        mstore(0x20, /** @src 29:23584:23605 */ _38)
                        /// @src 6:4791:17612
                        dataSlot_18 := keccak256(0, 0x40)
                        /// @src 44:1682:1780
                        let var_tick := signextend(/** @src 6:4791:17612 */ 2, /** @src 44:1682:1780 */ shr(/** @src 6:4791:17612 */ 160, sload(/** @src 29:23635:23645 */ mload(0x80))))
                        /// @src 29:23687:24487
                        switch /** @src 29:23691:23714 */ slt(var_tick, cleaned_5)
                        case /** @src 29:23687:24487 */ 0 {
                            /// @src 29:23933:24487
                            switch /** @src 29:23937:23961 */ iszero(slt(var_tick, /** @src 6:4791:17612 */ cleaned_6))
                            case /** @src 29:23933:24487 */ 0 {
                                /// @src 6:4791:17612
                                let _39 := sload(/** @src 29:24241:24266 */ add(mload(0x80), /** @src 6:4791:17612 */ 1))
                                let diff_1 := sub(_39, sload(/** @src 29:24269:24296 */ add(dataSlot_17, /** @src 6:4791:17612 */ 1)))
                                /// @src 29:24198:24326
                                var_feeGrowthInside0X128 := /** @src 6:4791:17612 */ sub(diff_1, sload(/** @src 29:24299:24326 */ add(dataSlot_18, /** @src 6:4791:17612 */ 1)))
                                let _40 := sload(/** @src 29:24387:24412 */ add(mload(0x80), /** @src 6:4791:17612 */ 2))
                                let diff_2 := sub(_40, sload(/** @src 29:24415:24442 */ add(dataSlot_17, /** @src 6:4791:17612 */ 2)))
                                /// @src 29:24344:24472
                                var_feeGrowthInside1X128 := /** @src 6:4791:17612 */ sub(diff_2, sload(/** @src 29:24445:24472 */ add(dataSlot_18, /** @src 6:4791:17612 */ 2)))
                            }
                            default /// @src 29:23933:24487
                            {
                                /// @src 6:4791:17612
                                let _41 := sload(/** @src 29:24004:24031 */ add(dataSlot_18, /** @src 6:4791:17612 */ 1))
                                /// @src 29:23981:24061
                                var_feeGrowthInside0X128 := /** @src 6:4791:17612 */ sub(_41, sload(/** @src 29:24034:24061 */ add(dataSlot_17, /** @src 6:4791:17612 */ 1)))
                                let _42 := sload(/** @src 29:24102:24129 */ add(dataSlot_18, /** @src 6:4791:17612 */ 2))
                                /// @src 29:24079:24159
                                var_feeGrowthInside1X128 := /** @src 6:4791:17612 */ sub(_42, sload(/** @src 29:24132:24159 */ add(dataSlot_17, /** @src 6:4791:17612 */ 2)))
                            }
                        }
                        default /// @src 29:23687:24487
                        {
                            /// @src 6:4791:17612
                            let _43 := sload(/** @src 29:23757:23784 */ add(dataSlot_17, /** @src 6:4791:17612 */ 1))
                            /// @src 29:23734:23814
                            var_feeGrowthInside0X128 := /** @src 6:4791:17612 */ sub(_43, sload(/** @src 29:23787:23814 */ add(dataSlot_18, /** @src 6:4791:17612 */ 1)))
                            let _44 := sload(/** @src 29:23855:23882 */ add(dataSlot_17, /** @src 6:4791:17612 */ 2))
                            /// @src 29:23832:23912
                            var_feeGrowthInside1X128 := /** @src 6:4791:17612 */ sub(_44, sload(/** @src 29:23885:23912 */ add(dataSlot_18, /** @src 6:4791:17612 */ 2)))
                        }
                        let cleaned_12 := and(/** @src 6:5241:5266 */ mload(/** @src 29:8305:8317 */ memPtr_2), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let _45 := mload(/** @src 6:8176:8518 */ add(memPtr_2, /** @src 6:4791:17612 */ 160))
                        /// @src 30:2447:3056
                        let usr$fmp_1 := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 30:2447:3056
                        mstore(add(usr$fmp_1, 0x26), _45)
                        mstore(add(usr$fmp_1, /** @src 6:17402:17408 */ 0x06), /** @src 30:2447:3056 */ cleaned_6)
                        mstore(add(usr$fmp_1, 0x03), cleaned_5)
                        mstore(usr$fmp_1, cleaned_12)
                        let var_positionKey := keccak256(add(usr$fmp_1, 0x0c), 0x3a)
                        mstore(add(usr$fmp_1, /** @src 6:4791:17612 */ 64), 0)
                        /// @src 30:2447:3056
                        mstore(add(usr$fmp_1, /** @src 6:4791:17612 */ 32), 0)
                        /// @src 30:2447:3056
                        mstore(usr$fmp_1, /** @src 6:4791:17612 */ 0)
                        mstore(0, var_positionKey)
                        mstore(32, /** @src 29:8286:8300 */ add(mload(0x80), /** @src 6:17402:17408 */ 0x06))
                        /// @src 6:4791:17612
                        let dataSlot_19 := keccak256(0, 64)
                        let cleaned_13 := and(sload(/** @src 30:3945:3959 */ dataSlot_19), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                        /// @src 30:3970:4240
                        switch /** @src 29:6888:6907 */ iszero(/** @src 6:4791:17612 */ signextend(15, expr_7))
                        case /** @src 30:3970:4240 */ 0 {
                            /// @src 6:4791:17612
                            sstore(/** @src 30:4163:4229 */ dataSlot_19, /** @src 6:4791:17612 */ or(and(sload(/** @src 30:4163:4229 */ dataSlot_19), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(/** @src 30:4180:4229 */ fun_addDelta(cleaned_13, /** @src 6:4791:17612 */ signextend(15, expr_7)), 0xffffffffffffffffffffffffffffffff)))
                        }
                        default /// @src 30:3970:4240
                        {
                            /// @src 30:4065:4132
                            if /** @src 30:4069:4083 */ iszero(/** @src 6:4791:17612 */ cleaned_13)
                            /// @src 30:4065:4132
                            {
                                /// @src 19:814:910
                                mstore(/** @src 6:4791:17612 */ 0, /** @src 30:4085:4119 */ 0xaefeb92400000000000000000000000000000000000000000000000000000000)
                                /// @src 19:814:910
                                revert(/** @src 6:4791:17612 */ 0, 4)
                            }
                        }
                        /// @src 30:4434:4463
                        let _46 := add(dataSlot_19, /** @src 6:4791:17612 */ 1)
                        /// @src 30:4367:4495
                        let var_feesOwed0 := /** @src 30:4395:4495 */ fun_mulDiv_40301(/** @src 6:4791:17612 */ sub(var_feeGrowthInside0X128, sload(/** @src 30:4434:4463 */ _46)), /** @src 30:4395:4495 */ cleaned_13)
                        /// @src 30:4576:4605
                        let _47 := add(dataSlot_19, /** @src 6:4791:17612 */ 2)
                        /// @src 30:4509:4637
                        let var_feesOwed1 := /** @src 30:4537:4637 */ fun_mulDiv_40301(/** @src 6:4791:17612 */ sub(var_feeGrowthInside1X128, sload(/** @src 30:4576:4605 */ _47)), /** @src 30:4537:4637 */ cleaned_13)
                        /// @src 6:4791:17612
                        sstore(_46, var_feeGrowthInside0X128)
                        sstore(_47, var_feeGrowthInside1X128)
                        /// @src 29:8623:8643
                        let expr_12 := fun_toInt128_5750(var_feesOwed0)
                        /// @src 38:553:668
                        let var_balanceDelta_1 := or(shl(/** @src 6:4791:17612 */ 0x80, /** @src 38:553:668 */ expr_12), and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:8645:8665 */ fun_toInt128_5750(var_feesOwed1)))
                        /// @src 29:8755:9010
                        if /** @src 29:8759:8777 */ slt(/** @src 6:4791:17612 */ signextend(15, expr_7), 0)
                        /// @src 29:8755:9010
                        {
                            /// @src 29:8797:8888
                            if /** @src 6:4791:17612 */ iszero(iszero(mload(/** @src 29:8801:8819 */ memPtr_3)))
                            /// @src 29:8797:8888
                            {
                                /// @src 29:8859:8868
                                fun_clearTick(mload(0x80), cleaned_5)
                            }
                            /// @src 29:8905:8996
                            if /** @src 6:4791:17612 */ iszero(iszero(mload(add(memPtr_3, 64))))
                            /// @src 29:8905:8996
                            {
                                /// @src 29:8967:8976
                                fun_clearTick(mload(0x80), cleaned_6)
                            }
                        }
                        /// @src 29:9030:10804
                        if /** @src 29:6888:6907 */ iszero(iszero(/** @src 6:4791:17612 */ signextend(15, expr_7)))
                        /// @src 29:9030:10804
                        {
                            /// @src 6:4791:17612
                            let _48 := sload(/** @src 29:9084:9094 */ mload(0x80))
                            /// @src 29:9146:9159
                            let expr_13 := /** @src 44:1682:1780 */ signextend(/** @src 6:4791:17612 */ 2, /** @src 44:1682:1780 */ shr(/** @src 6:4791:17612 */ 160, /** @src 29:9146:9159 */ _48))
                            /// @src 29:9161:9182
                            let expr_14 := /** @src 44:1502:1595 */ and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff, /** @src 29:9161:9182 */ _48)
                            /// @src 29:9197:10794
                            switch /** @src 29:9201:9217 */ slt(expr_13, cleaned_5)
                            case /** @src 29:9197:10794 */ 0 {
                                /// @src 29:9757:10794
                                switch /** @src 29:9761:9777 */ slt(expr_13, /** @src 6:4791:17612 */ cleaned_6)
                                case /** @src 29:9757:10794 */ 0 {
                                    /// @src 29:10634:10672
                                    let expr_15 := fun_getSqrtPriceAtTick(cleaned_5)
                                    /// @src 29:10512:10779
                                    var_delta := /** @src 38:553:668 */ and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:10579:10761 */ fun_toInt128(/** @src 29:10579:10750 */ fun_getAmount1Delta(expr_15, /** @src 29:10674:10712 */ fun_getSqrtPriceAtTick(cleaned_6), /** @src 6:4791:17612 */ signextend(15, expr_7))))
                                }
                                default /// @src 29:9757:10794
                                {
                                    /// @src 29:9841:9976
                                    let expr_16 := fun_toInt128(/** @src 29:9841:9940 */ fun_getAmount0Delta(expr_14, /** @src 29:9885:9923 */ fun_getSqrtPriceAtTick(cleaned_6), /** @src 6:4791:17612 */ signextend(15, expr_7)))
                                    /// @src 29:9797:10151
                                    var_delta := /** @src 38:553:668 */ or(shl(/** @src 6:4791:17612 */ 0x80, /** @src 38:553:668 */ expr_16), and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:9998:10133 */ fun_toInt128(/** @src 29:9998:10097 */ fun_getAmount1Delta(/** @src 29:10028:10066 */ fun_getSqrtPriceAtTick(cleaned_5), /** @src 29:9998:10097 */ expr_14, /** @src 6:4791:17612 */ signextend(15, expr_7)))))
                                    /// @src 29:10210:10224
                                    let _49 := add(mload(0x80), /** @src 30:2447:3056 */ 0x03)
                                    /// @src 6:4791:17612
                                    sstore(/** @src 29:10170:10241 */ _49, /** @src 6:4791:17612 */ or(and(sload(/** @src 29:10170:10241 */ _49), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(/** @src 29:10187:10241 */ fun_addDelta(/** @src 6:4791:17612 */ and(sload(/** @src 29:10210:10224 */ _49), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff), signextend(15, expr_7)), 0xffffffffffffffffffffffffffffffff)))
                                }
                            }
                            default /// @src 29:9197:10794
                            {
                                /// @src 29:9568:9606
                                let expr_17 := fun_getSqrtPriceAtTick(cleaned_5)
                                /// @src 29:9469:9736
                                var_delta := /** @src 38:553:668 */ shl(/** @src 6:4791:17612 */ 0x80, /** @src 29:9513:9695 */ fun_toInt128(/** @src 29:9513:9684 */ fun_getAmount0Delta(expr_17, /** @src 29:9608:9646 */ fun_getSqrtPriceAtTick(cleaned_6), /** @src 6:4791:17612 */ signextend(15, expr_7))))
                            }
                        }
                        /// @src 38:1032:1047
                        let expr_18 := fun_toInt128(/** @src 38:785:1005 */ add(sar(/** @src 6:4791:17612 */ 0x80, /** @src 38:785:1005 */ var_delta), sar(/** @src 6:4791:17612 */ 0x80, /** @src 38:785:1005 */ var_balanceDelta_1)))
                        /// @src 38:553:668
                        let var_balanceDelta_2 := or(shl(/** @src 6:4791:17612 */ 0x80, /** @src 38:553:668 */ expr_18), and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 38:1049:1064 */ fun_toInt128(/** @src 38:785:1005 */ add(signextend(/** @src 6:4791:17612 */ 15, /** @src 38:785:1005 */ var_delta), signextend(/** @src 6:4791:17612 */ 15, /** @src 38:785:1005 */ var_balanceDelta_1)))))
                        /// @src 6:4791:17612
                        let cleaned_14 := signextend(2, mload(/** @src 6:8833:8849 */ memPtr_1))
                        /// @src 6:4791:17612
                        let cleaned_15 := signextend(2, mload(add(memPtr_1, 32)))
                        let _50 := mload(add(memPtr_1, 64))
                        let _51 := mload(add(memPtr_1, 96))
                        /// @src 6:8801:8904
                        let _52 := /** @src 6:4791:17612 */ mload(64)
                        mstore(_52, cleaned_14)
                        mstore(add(_52, 32), cleaned_15)
                        mstore(add(_52, 64), _50)
                        mstore(add(_52, 96), _51)
                        /// @src 6:8801:8904
                        log3(_52, /** @src 6:4791:17612 */ 0x80, /** @src 6:8801:8904 */ 0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec, expr_3, /** @src 23:8814:8824 */ caller())
                        /// @src 6:8974:9053
                        let expr_component, expr_component_1 := fun_afterModifyLiquidity(/** @src 6:4791:17612 */ and(mload(/** @src 6:7996:8005 */ add(value0_8, /** @src 6:4791:17612 */ 0x80)), 0xffffffffffffffffffffffffffffffffffffffff), /** @src 6:8974:9053 */ value0_8, memPtr_1, var_balanceDelta_2, var_balanceDelta_1, value2, value3_1)
                        /// @src 6:9165:9274
                        if /** @src 38:1676:1724 */ iszero(iszero(expr_component_1))
                        /// @src 6:9165:9274
                        {
                            /// @src 6:9255:9273
                            fun_accountPoolBalanceDelta(value0_8, expr_component_1, /** @src 6:4791:17612 */ and(mload(/** @src 6:7996:8005 */ add(value0_8, /** @src 6:4791:17612 */ 0x80)), 0xffffffffffffffffffffffffffffffffffffffff))
                        }
                        /// @src 6:9328:9338
                        fun_accountPoolBalanceDelta(value0_8, expr_component, /** @src 23:8814:8824 */ caller())
                        /// @src 6:4791:17612
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
                        /// @src 5:1169:1245
                        fun_checkNotDelegateCall()
                        /// @src 6:6341:6356
                        let _54 := add(value0_9, 96)
                        /// @src 6:4791:17612
                        let cleaned_16 := signextend(2, mload(/** @src 6:6341:6356 */ _54))
                        /// @src 6:6337:6433
                        if /** @src 6:6341:6375 */ sgt(/** @src 6:4791:17612 */ cleaned_16, /** @src 36:1676:1691 */ 32767)
                        /// @src 6:6337:6433
                        {
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:6377:6405 */ 0xb70024f800000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_16)
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                        }
                        /// @src 6:4791:17612
                        let cleaned_17 := signextend(2, mload(/** @src 6:6447:6462 */ _54))
                        /// @src 6:6443:6539
                        if /** @src 6:6447:6481 */ slt(/** @src 6:4791:17612 */ cleaned_17, 1)
                        /// @src 6:6443:6539
                        {
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:6483:6511 */ 0xe9e9058800000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1431:1574
                            mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1431:1574 */ cleaned_17)
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1431:1574 */ 0x24)
                        }
                        /// @src 6:4791:17612
                        let cleaned_18 := and(/** @src 6:5241:5266 */ mload(/** @src 6:6553:6566 */ value0_9), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 6:6570:6583
                        let _55 := add(value0_9, 32)
                        /// @src 6:4791:17612
                        let cleaned_19 := and(/** @src 6:5241:5266 */ mload(/** @src 6:6570:6583 */ _55), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 6:6549:6751
                        if /** @src 40:887:938 */ iszero(lt(/** @src 6:4791:17612 */ cleaned_18, cleaned_19))
                        /// @src 6:6549:6751
                        {
                            /// @src 19:3008:3327
                            let usr$fmp_2 := mload(/** @src 6:4791:17612 */ 64)
                            /// @src 19:3008:3327
                            mstore(usr$fmp_2, /** @src 6:6599:6635 */ 0x6e6c983000000000000000000000000000000000000000000000000000000000)
                            /// @src 19:3008:3327
                            mstore(add(usr$fmp_2, /** @src 6:4791:17612 */ 4), /** @src 19:3008:3327 */ cleaned_18)
                            mstore(add(usr$fmp_2, 0x24), cleaned_19)
                            revert(usr$fmp_2, 0x44)
                        }
                        /// @src 6:6765:6774
                        let _56 := add(value0_9, 128)
                        /// @src 6:4791:17612
                        let cleaned_20 := and(mload(/** @src 6:6765:6774 */ _56), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 6:6794:6801
                        let _57 := add(value0_9, /** @src 6:4791:17612 */ 64)
                        /// @src 6:6760:6869
                        if /** @src 6:6764:6802 */ iszero(/** @src 6:6765:6802 */ fun_isValidHookAddress(cleaned_20, /** @src 6:4791:17612 */ and(mload(/** @src 6:6794:6801 */ _57), /** @src 6:4791:17612 */ 0xffffff)))
                        /// @src 6:6760:6869
                        {
                            /// @src 19:1084:1260
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:6804:6838 */ 0xe65af6a000000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1084:1260
                            mstore(/** @src 6:4791:17612 */ 4, /** @src 19:1084:1260 */ cleaned_20)
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1084:1260 */ 0x24)
                        }
                        /// @src 6:6895:6920
                        let expr_19 := fun_getInitialLPFee(/** @src 6:4791:17612 */ and(mload(/** @src 6:6895:6902 */ _57), /** @src 6:4791:17612 */ 0xffffff))
                        let _58 := mload(/** @src 6:6931:6940 */ _56)
                        /// @src 6:4791:17612
                        let cleaned_21 := and(_58, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 23:8810:8869
                        if /** @src 23:8814:8841 */ iszero(eq(/** @src 23:8814:8824 */ caller(), /** @src 6:4791:17612 */ cleaned_21))
                        /// @src 23:8810:8869
                        {
                            /// @src 23:9089:9131
                            let var_6 := /** @src 6:4791:17612 */ 0
                            /// @src 23:16460:16501
                            var_6 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _58, 8192)))
                            /// @src 23:9085:9245
                            if /** @src 23:9089:9131 */ var_6
                            /// @src 23:9085:9245
                            {
                                /// @src 23:9161:9233
                                let expr_mpos_5 := /** @src 6:4791:17612 */ mload(64)
                                /// @src 23:9161:9233
                                mstore(add(expr_mpos_5, /** @src 6:6570:6583 */ 32), /** @src 23:9161:9233 */ 0xdc98354e00000000000000000000000000000000000000000000000000000000)
                                /// @src 6:4791:17612
                                mstore(/** @src 23:9161:9233 */ add(expr_mpos_5, 36), /** @src 23:8814:8824 */ caller())
                                /// @src 23:1397:1404
                                abi_encode_struct_PoolKey(value0_9, add(/** @src 23:9161:9233 */ expr_mpos_5, /** @src 23:1397:1404 */ 68))
                                /// @src 6:4791:17612
                                mstore(/** @src 23:1397:1404 */ add(/** @src 23:9161:9233 */ expr_mpos_5, /** @src 23:1397:1404 */ 228), /** @src 6:4791:17612 */ _53)
                                /// @src 23:9161:9233
                                mstore(expr_mpos_5, /** @src 23:1397:1404 */ 228)
                                /// @src 23:9161:9233
                                finalize_allocation(expr_mpos_5, 260)
                                /// @src 23:9147:9234
                                pop(fun_callHook(cleaned_21, expr_mpos_5))
                            }
                        }
                        /// @src 6:6999:7009
                        let expr_20 := /** @src 41:357:530 */ keccak256(/** @src 6:6999:7009 */ value0_9, /** @src 6:4791:17612 */ 160)
                        mstore(0, expr_20)
                        mstore(/** @src 6:6570:6583 */ 32, /** @src 6:7027:7033 */ 0x06)
                        /// @src 6:4791:17612
                        let dataSlot_20 := keccak256(0, 64)
                        /// @src 29:4665:4745
                        if /** @src 29:4669:4699 */ iszero(iszero(/** @src 44:1502:1595 */ and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff, sload(/** @src 29:4669:4679 */ dataSlot_20))))
                        /// @src 29:4665:4745
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 29:4701:4732 */ 0x7983c05100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 29:4763:4804
                        let expr_21 := fun_getTickAtSqrtPrice(value_9)
                        /// @src 6:4791:17612
                        sstore(dataSlot_20, /** @src 44:3217:3395 */ or(or(/** @src 44:2578:2735 */ and(shl(/** @src 6:4791:17612 */ 160, /** @src 44:2578:2735 */ expr_21), 0xffffff0000000000000000000000000000000000000000), /** @src 44:3217:3395 */ _53), and(shl(208, expr_19), 0xffffff0000000000000000000000000000000000000000000000000000)))
                        /// @src 6:4791:17612
                        let cleaned_22 := and(/** @src 6:5241:5266 */ mload(/** @src 6:7408:7421 */ value0_9), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let cleaned_23 := and(/** @src 6:5241:5266 */ mload(/** @src 6:7423:7436 */ _55), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let cleaned_24 := and(mload(/** @src 6:7438:7445 */ _57), /** @src 6:4791:17612 */ 0xffffff)
                        let cleaned_25 := signextend(2, mload(/** @src 6:7447:7462 */ _54))
                        /// @src 6:4791:17612
                        let cleaned_26 := and(mload(/** @src 6:7464:7473 */ _56), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 6:7393:7494
                        let _59 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 6:5241:5266
                        mstore(_59, /** @src 6:4791:17612 */ cleaned_24)
                        mstore(/** @src 6:5241:5266 */ add(_59, /** @src 6:6570:6583 */ 32), /** @src 6:4791:17612 */ cleaned_25)
                        /// @src 6:5241:5266
                        mstore(add(_59, /** @src 6:4791:17612 */ 64), cleaned_26)
                        mstore(/** @src 6:5241:5266 */ add(_59, /** @src 6:6341:6356 */ 96), /** @src 6:4791:17612 */ _53)
                        let _60 := signextend(2, expr_21)
                        mstore(/** @src 6:5241:5266 */ add(_59, /** @src 6:6765:6774 */ 128), /** @src 6:4791:17612 */ _60)
                        /// @src 6:7393:7494
                        log4(_59, /** @src 6:4791:17612 */ 160, /** @src 6:7393:7494 */ 0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438, expr_20, cleaned_22, cleaned_23)
                        /// @src 6:4791:17612
                        let _61 := mload(/** @src 6:7505:7514 */ _56)
                        /// @src 6:4791:17612
                        let cleaned_27 := and(_61, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 23:8810:8869
                        if /** @src 23:8814:8841 */ iszero(eq(/** @src 23:8814:8824 */ caller(), /** @src 6:4791:17612 */ cleaned_27))
                        /// @src 23:8810:8869
                        {
                            /// @src 23:9495:9536
                            let var_7 := /** @src 6:4791:17612 */ 0
                            /// @src 23:16460:16501
                            var_7 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 6:4791:17612 */ _61, 4096)))
                            /// @src 23:9491:9655
                            if /** @src 23:9495:9536 */ var_7
                            /// @src 23:9491:9655
                            {
                                /// @src 23:9566:9643
                                let expr_mpos_6 := /** @src 6:4791:17612 */ mload(64)
                                /// @src 23:9566:9643
                                mstore(add(expr_mpos_6, /** @src 6:6570:6583 */ 32), /** @src 23:9566:9643 */ 0x6fe7e6eb00000000000000000000000000000000000000000000000000000000)
                                /// @src 6:4791:17612
                                mstore(/** @src 23:9566:9643 */ add(expr_mpos_6, 36), /** @src 23:8814:8824 */ caller())
                                /// @src 23:1460:1467
                                abi_encode_struct_PoolKey(value0_9, add(/** @src 23:9566:9643 */ expr_mpos_6, /** @src 23:1460:1467 */ 68))
                                /// @src 6:4791:17612
                                mstore(/** @src 23:1460:1467 */ add(/** @src 23:9566:9643 */ expr_mpos_6, /** @src 23:1460:1467 */ 228), /** @src 6:4791:17612 */ _53)
                                mstore(/** @src 23:1460:1467 */ add(/** @src 23:9566:9643 */ expr_mpos_6, /** @src 23:1460:1467 */ 260), /** @src 6:4791:17612 */ _60)
                                /// @src 23:9566:9643
                                mstore(expr_mpos_6, /** @src 23:1460:1467 */ 260)
                                /// @src 23:9566:9643
                                finalize_allocation(expr_mpos_6, 292)
                                /// @src 23:9552:9644
                                pop(fun_callHook(cleaned_27, expr_mpos_6))
                            }
                        }
                        /// @src 6:4791:17612
                        let memPos_10 := mload(64)
                        mstore(memPos_10, _60)
                        return(memPos_10, /** @src 6:6570:6583 */ 32)
                    }
                    case /** @src 6:4791:17612 */ 0x7e87ce7d {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 192) { revert(0, 0) }
                        let value0_10 := abi_decode_struct_PoolKey(calldatasize())
                        let value1_4 := abi_decode_uint24()
                        /// @src 7:1375:1451
                        if /** @src 7:1379:1414 */ iszero(eq(/** @src 7:1379:1389 */ caller(), /** @src 6:4791:17612 */ and(sload(/** @src 7:1393:1414 */ 0x02), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)))
                        /// @src 7:1375:1451
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 7:1416:1438 */ 0x48f5c3ed00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 7:1461:1558
                        if /** @src 7:1465:1501 */ iszero(/** @src 31:1088:1340 */ and(lt(and(value1_4, 0xfff), 1001), lt(and(value1_4, 0xfff000), 4100096)))
                        /// @src 7:1461:1558
                        {
                            /// @src 19:1084:1260
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 7:1503:1531 */ 0xa7abe2f700000000000000000000000000000000000000000000000000000000)
                            /// @src 19:1084:1260
                            mstore(/** @src 6:4791:17612 */ 4, and(/** @src 7:1503:1558 */ value1_4, /** @src 6:4791:17612 */ 0xffffff))
                            /// @src 19:1084:1260
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:1084:1260 */ 0x24)
                        }
                        /// @src 7:1580:1590
                        let expr_22 := /** @src 41:357:530 */ keccak256(/** @src 7:1580:1590 */ value0_10, /** @src 6:4791:17612 */ 160)
                        mstore(0, expr_22)
                        mstore(0x20, /** @src 6:17402:17408 */ 0x06)
                        /// @src 6:4791:17612
                        let dataSlot_21 := keccak256(0, 64)
                        /// @src 29:5072:5097
                        fun_checkPoolInitialized(dataSlot_21)
                        /// @src 6:4791:17612
                        let _62 := sload(/** @src 29:5122:5132 */ dataSlot_21)
                        /// @src 6:4791:17612
                        sstore(dataSlot_21, /** @src 44:2855:3109 */ or(and(0xffffffffffff000000ffffffffffffffffffffffffffffffffffffffffffffff, _62), and(shl(184, value1_4), 0xffffff0000000000000000000000000000000000000000000000)))
                        /// @src 7:1658:1696
                        let _63 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 6:5241:5266
                        mstore(_63, /** @src 6:4791:17612 */ and(/** @src 6:5241:5266 */ value1_4, /** @src 6:4791:17612 */ 0xffffff))
                        /// @src 7:1658:1696
                        log2(_63, /** @src 6:4791:17612 */ 0x20, /** @src 7:1658:1696 */ 0xe9c42593e71f84403b84352cd168d693e2c9fcd1fdbcc3feb21d92b43e6696f9, expr_22)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0x80f0b44c {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
                        let value0_11 := abi_decode_address()
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:14054:14083
                        let expr_23 := /** @src 17:956:1029 */ extcodehash(/** @src 17:916:946 */ fun_computeSlot(/** @src 6:14072:14082 */ caller(), /** @src 6:14054:14083 */ value0_11))
                        /// @src 6:14191:14208
                        let expr_24 := fun_toInt128_5750(/** @src 6:4791:17612 */ calldataload(36))
                        /// @src 6:14218:14295
                        if /** @src 6:14222:14244 */ iszero(eq(/** @src 6:4791:17612 */ signextend(15, /** @src 6:14222:14244 */ expr_24), expr_23))
                        /// @src 6:14218:14295
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:14246:14282 */ 0xbda73abf00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:14429:14439
                        fun_accountDelta(value0_11, /** @src 6:4791:17612 */ signextend(15, sub(0, /** @src 6:14413:14427 */ expr_24)), /** @src 6:14072:14082 */ caller())
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0x8161b874 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
                        let value0_12 := abi_decode_address()
                        let value1_5 := abi_decode_address_40277()
                        let value_10 := calldataload(68)
                        /// @src 7:1899:1975
                        if /** @src 7:1903:1938 */ iszero(eq(/** @src 7:1903:1913 */ caller(), /** @src 6:4791:17612 */ and(sload(/** @src 7:1917:1938 */ 0x02), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)))
                        /// @src 7:1899:1975
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 7:1940:1962 */ 0x48f5c3ed00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 7:1990:2014
                        let var_8 := /** @src 6:4791:17612 */ 0
                        let _64 := and(/** @src 40:4998:5023 */ value1_5, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 40:4991:5056
                        var_8 := /** @src 40:4998:5056 */ iszero(/** @src 6:4791:17612 */ _64)
                        /// @src 7:1989:2066
                        let expr_25 := /** @src 7:1989:2014 */ iszero(/** @src 7:1990:2014 */ var_8)
                        /// @src 7:1989:2066
                        if expr_25
                        {
                            expr_25 := /** @src 40:448:499 */ eq(/** @src 6:4791:17612 */ and(/** @src 18:629:710 */ extcodehash(18037029214425852597980496522548842536420057720408124260691716999909707453369), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), _64)
                        }
                        /// @src 7:1985:2242
                        if expr_25
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 7:2184:2218 */ 0xc79e594800000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 7:2270:2324
                        let expr_26 := /** @src 6:4791:17612 */ 0
                        /// @src 7:2270:2324
                        switch /** @src 7:2271:2282 */ iszero(value_10)
                        case /** @src 7:2270:2324 */ 0 { expr_26 := value_10 }
                        default {
                            /// @src 6:4791:17612
                            mstore(0, _64)
                            mstore(32, 1)
                            /// @src 7:2270:2324
                            expr_26 := /** @src 6:4791:17612 */ sload(keccak256(0, 64))
                        }
                        mstore(0, _64)
                        mstore(32, 1)
                        let dataSlot_22 := keccak256(0, 64)
                        sstore(dataSlot_22, /** @src 7:2334:2382 */ checked_sub_uint256(/** @src 6:4791:17612 */ sload(/** @src 7:2334:2382 */ dataSlot_22), expr_26))
                        /// @src 7:2421:2436
                        fun_transfer(value1_5, value0_12, expr_26)
                        /// @src 6:4791:17612
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
                        mstore(32, /** @src 7:819:890 */ 1)
                        /// @src 6:4791:17612
                        let _65 := sload(keccak256(0, 64))
                        let memPos_13 := mload(64)
                        mstore(memPos_13, _65)
                        return(memPos_13, 32)
                    }
                    case 0x9bf6645f {
                        if callvalue() { revert(0, 0) }
                        let param_9, param_10 := abi_decode_array_bytes32_dyn_calldata(calldatasize())
                        /// @src 4:658:1594
                        let usr$memptr_2 := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 4:658:1594
                        let usr$memptr_3 := usr$memptr_2
                        mstore(usr$memptr_2, 0x20)
                        mstore(add(usr$memptr_2, 0x20), param_10)
                        usr$memptr_2 := add(usr$memptr_2, /** @src 6:4791:17612 */ 64)
                        /// @src 4:658:1594
                        let _66 := add(usr$memptr_3, shl(5, param_10))
                        let usr$end_1 := add(_66, /** @src 6:4791:17612 */ 64)
                        /// @src 4:658:1594
                        let usr$calldataptr := param_9
                        for { } 1 { }
                        {
                            mstore(usr$memptr_2, extcodehash(calldataload(usr$calldataptr)))
                            usr$memptr_2 := add(usr$memptr_2, 0x20)
                            usr$calldataptr := add(usr$calldataptr, 0x20)
                            if iszero(lt(usr$memptr_2, usr$end_1)) { break }
                        }
                        return(usr$memptr_3, add(sub(_66, usr$memptr_3), /** @src 6:4791:17612 */ 64))
                    }
                    case 0xa5841194 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        let value0_13 := abi_decode_address()
                        /// @src 6:12906:12930
                        let var_9 := /** @src 6:4791:17612 */ 0
                        let _67 := and(/** @src 40:4998:5023 */ value0_13, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 40:4991:5056
                        var_9 := /** @src 40:4998:5056 */ iszero(/** @src 6:4791:17612 */ _67)
                        /// @src 6:12902:13243
                        switch /** @src 6:12906:12930 */ var_9
                        case /** @src 6:12902:13243 */ 0 {
                            /// @src 6:13135:13159
                            let _68 := fun_balanceOfSelf(value0_13)
                            /// @src 18:937:1110
                            log2(/** @src 6:4791:17612 */ 0, 0, /** @src 18:937:1110 */ 18037029214425852597980496522548842536420057720408124260691716999909707453369, _67)
                            log2(/** @src 6:4791:17612 */ 0, 0, /** @src 18:937:1110 */ 13582234132832961652756477188584847927179359657859594952372729441197434191253, _68)
                        }
                        default /// @src 6:12902:13243
                        {
                            /// @src 18:766:839
                            log2(/** @src 6:4791:17612 */ 0, 0, /** @src 18:766:839 */ 18037029214425852597980496522548842536420057720408124260691716999909707453369, /** @src 6:4791:17612 */ 0)
                        }
                        return(0, 0)
                    }
                    case 0xb6363cf2 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 64) { revert(0, 0) }
                        let value0_14 := abi_decode_address()
                        let value1_6 := abi_decode_address_40277()
                        mstore(0, and(value0_14, 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(32, /** @src 1:697:785 */ 3)
                        /// @src 6:4791:17612
                        let dataSlot_23 := keccak256(0, 64)
                        /// @src 1:697:785
                        let dataSlot_24 := /** @src -1:-1:-1 */ 0
                        /// @src 6:4791:17612
                        mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:697:785 */ value1_6, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0x20, /** @src 1:697:785 */ dataSlot_23)
                        /// @src 6:4791:17612
                        dataSlot_24 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                        let value_12 := and(sload(/** @src 1:697:785 */ dataSlot_24), /** @src 6:4791:17612 */ 0xff)
                        let memPos_14 := mload(64)
                        mstore(memPos_14, iszero(iszero(value_12)))
                        return(memPos_14, 32)
                    }
                    case 0xdbd035ff {
                        if callvalue() { revert(0, 0) }
                        let param_11, param_12 := abi_decode_array_bytes32_dyn_calldata(calldatasize())
                        /// @src 3:1664:2600
                        let usr$memptr_4 := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 3:1664:2600
                        let usr$memptr_5 := usr$memptr_4
                        mstore(usr$memptr_4, 0x20)
                        mstore(add(usr$memptr_4, 0x20), param_12)
                        usr$memptr_4 := add(usr$memptr_4, /** @src 6:4791:17612 */ 64)
                        /// @src 3:1664:2600
                        let _69 := add(usr$memptr_5, shl(5, param_12))
                        let usr$end_2 := add(_69, /** @src 6:4791:17612 */ 64)
                        /// @src 3:1664:2600
                        let usr$calldataptr_1 := param_11
                        for { } 1 { }
                        {
                            mstore(usr$memptr_4, sload(calldataload(usr$calldataptr_1)))
                            usr$memptr_4 := add(usr$memptr_4, 0x20)
                            usr$calldataptr_1 := add(usr$calldataptr_1, 0x20)
                            if iszero(lt(usr$memptr_4, usr$end_2)) { break }
                        }
                        return(usr$memptr_5, add(sub(_69, usr$memptr_5), /** @src 6:4791:17612 */ 64))
                    }
                    case 0xf02de3b2 {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0) }
                        let value_13 := and(sload(/** @src 7:931:967 */ 2), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let memPos_15 := mload(64)
                        mstore(memPos_15, value_13)
                        return(memPos_15, 32)
                    }
                    case 0xf135baaa {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        /// @src 4:422:521
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 4:422:521 */ extcodehash(/** @src 6:4791:17612 */ calldataload(4)))
                        /// @src 4:422:521
                        return(/** @src 6:4791:17612 */ 0, 32)
                    }
                    case 0xf2fde38b {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 32) { revert(0, 0) }
                        let value0_15 := abi_decode_address()
                        let _70 := sload(0)
                        /// @src 0:756:800
                        require_helper_stringliteral_269d(/** @src 0:764:783 */ eq(/** @src 0:764:774 */ caller(), /** @src 6:4791:17612 */ and(_70, 0xffffffffffffffffffffffffffffffffffffffff)))
                        let _71 := and(value0_15, 0xffffffffffffffffffffffffffffffffffffffff)
                        sstore(0, or(and(_70, 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), _71))
                        /// @src 0:1424:1466
                        log3(/** @src 6:4791:17612 */ 0, 0, /** @src 0:1424:1466 */ 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0, /** @src 0:764:774 */ caller(), /** @src 0:1424:1466 */ _71)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0xf3cd914c {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 288) { revert(0, 0) }
                        let value0_16 := abi_decode_struct_PoolKey(calldatasize())
                        if slt(add(calldatasize(), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5c), 0x60) { revert(0, 0) }
                        let memPtr_4 := mload(64)
                        finalize_allocation_40320(memPtr_4)
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
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 5:1169:1245
                        fun_checkNotDelegateCall()
                        /// @src 6:9590:9667
                        if /** @src 6:9594:9621 */ iszero(/** @src 6:4791:17612 */ mload(/** @src 6:9594:9616 */ _72))
                        /// @src 6:9590:9667
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:9623:9654 */ 0xbe8b850700000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        /// @src 6:9689:9699
                        let expr_27 := /** @src 41:357:530 */ keccak256(/** @src 6:9689:9699 */ value0_16, /** @src 6:4791:17612 */ 160)
                        mstore(0, expr_27)
                        mstore(32, /** @src 6:17402:17408 */ 0x06)
                        /// @src 6:4791:17612
                        let dataSlot_25 := keccak256(0, 64)
                        /// @src 6:9757:9782
                        fun_checkPoolInitialized(dataSlot_25)
                        /// @src 6:9966:9975
                        let _74 := add(value0_16, 128)
                        /// @src 6:9966:10009
                        let expr_component_2, expr_component_3, expr_component_4 := fun_beforeSwap(/** @src 6:4791:17612 */ and(mload(/** @src 6:9966:9975 */ _74), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), /** @src 6:9966:10009 */ value0_16, memPtr_4, value2_1, value3_2)
                        /// @src 6:4791:17612
                        let cleaned_28 := signextend(2, mload(/** @src 6:10285:10300 */ add(value0_16, /** @src 6:4791:17612 */ 0x60)))
                        let cleaned_29 := iszero(iszero(mload(/** @src 6:10334:10351 */ memPtr_4)))
                        /// @src 6:4791:17612
                        let cleaned_30 := and(mload(/** @src 6:10443:10467 */ _73), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let memPtr_5 := mload(64)
                        finalize_allocation_40323(memPtr_5)
                        mstore(memPtr_5, expr_component_2)
                        mstore(/** @src 6:10234:10536 */ add(memPtr_5, /** @src 6:4791:17612 */ 32), cleaned_28)
                        mstore(/** @src 6:10234:10536 */ add(memPtr_5, /** @src 6:4791:17612 */ 64), cleaned_29)
                        mstore(/** @src 6:10234:10536 */ add(memPtr_5, /** @src 6:4791:17612 */ 0x60), cleaned_30)
                        mstore(/** @src 6:10234:10536 */ add(memPtr_5, /** @src 6:9966:9975 */ 128), /** @src 6:4791:17612 */ and(expr_component_4, 0xffffff))
                        let cleaned_31 := iszero(iszero(mload(/** @src 6:10554:10571 */ memPtr_4)))
                        /// @src 6:10554:10603
                        let expr_28 := /** @src 6:4791:17612 */ 0
                        /// @src 6:10554:10603
                        switch cleaned_31
                        case 0 {
                            expr_28 := /** @src 6:4791:17612 */ and(/** @src 6:5241:5266 */ mload(/** @src 6:10590:10603 */ add(value0_16, /** @src 6:4791:17612 */ 32)), 0xffffffffffffffffffffffffffffffffffffffff)
                        }
                        default /// @src 6:10554:10603
                        {
                            expr_28 := /** @src 6:4791:17612 */ and(/** @src 6:5241:5266 */ mload(/** @src 6:10574:10587 */ value0_16), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        }
                        /// @src 6:11470:11487
                        let expr_component_5, expr_component_6, expr_component_7, expr_component_mpos := fun_swap(dataSlot_25, memPtr_5)
                        /// @src 6:11542:11620
                        if /** @src 6:11546:11566 */ iszero(iszero(expr_component_6))
                        /// @src 6:11542:11620
                        {
                            /// @src 6:4791:17612
                            mstore(0, and(expr_28, 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(32, 1)
                            let dataSlot_26 := keccak256(0, 64)
                            sstore(dataSlot_26, /** @src 20:258:293 */ add(/** @src 6:4791:17612 */ sload(/** @src 7:2977:3016 */ dataSlot_26), /** @src 20:258:293 */ expr_component_6))
                        }
                        /// @src 6:4791:17612
                        let cleaned_32 := and(mload(/** @src 6:11851:11870 */ expr_component_mpos), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        let cleaned_33 := and(mload(/** @src 6:11884:11900 */ add(expr_component_mpos, /** @src 6:4791:17612 */ 64)), 0xffffffffffffffffffffffffffffffff)
                        let cleaned_34 := signextend(2, mload(/** @src 6:11914:11925 */ add(expr_component_mpos, /** @src 6:4791:17612 */ 32)))
                        /// @src 6:11735:11956
                        let _75 := /** @src 6:4791:17612 */ mload(64)
                        mstore(_75, signextend(/** @src 38:2241:2330 */ 15, /** @src 38:2052:2135 */ sar(/** @src 6:9966:9975 */ 128, /** @src 6:11793:11808 */ expr_component_5)))
                        /// @src 6:4791:17612
                        mstore(add(_75, 32), /** @src 38:2241:2330 */ signextend(15, /** @src 6:11822:11837 */ expr_component_5))
                        /// @src 6:4791:17612
                        mstore(add(_75, 64), cleaned_32)
                        mstore(add(_75, 0x60), cleaned_33)
                        mstore(add(_75, /** @src 6:9966:9975 */ 128), /** @src 6:4791:17612 */ cleaned_34)
                        /// @src 6:5241:5266
                        mstore(/** @src 6:4791:17612 */ add(_75, 160), and(/** @src 6:5241:5266 */ expr_component_7, /** @src 6:4791:17612 */ 0xffffff))
                        /// @src 6:11735:11956
                        log3(_75, /** @src 6:4791:17612 */ 192, /** @src 6:11735:11956 */ 0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f, expr_27, /** @src 6:11769:11779 */ caller())
                        /// @src 6:10710:10780
                        let expr_component_8, expr_component_9 := fun_afterSwap(/** @src 6:4791:17612 */ and(mload(/** @src 6:10710:10719 */ _74), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), /** @src 6:10710:10780 */ value0_16, memPtr_4, /** @src 6:10169:10632 */ expr_component_5, /** @src 6:10710:10780 */ value2_1, value3_2, expr_component_3)
                        /// @src 6:10892:11001
                        if /** @src 38:1676:1724 */ iszero(iszero(expr_component_9))
                        /// @src 6:10892:11001
                        {
                            /// @src 6:10982:11000
                            fun_accountPoolBalanceDelta(value0_16, expr_component_9, /** @src 6:4791:17612 */ and(mload(/** @src 6:10990:10999 */ _74), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        }
                        /// @src 6:11053:11063
                        fun_accountPoolBalanceDelta(value0_16, expr_component_8, /** @src 6:11769:11779 */ caller())
                        /// @src 6:4791:17612
                        let memPos_16 := mload(64)
                        mstore(memPos_16, expr_component_8)
                        return(memPos_16, 32)
                    }
                    case 0xf5298aca {
                        if callvalue() { revert(0, 0) }
                        let param_13, param_14, param_15 := abi_decode_addresst_uint256t_uint256(calldatasize())
                        /// @src 6:5425:5484
                        if /** @src 6:5429:5447 */ iszero(/** @src 26:837:921 */ extcodehash(87100234046427240614499661373387320107015461065347489303548037305558901893923))
                        /// @src 6:5425:5484
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 6:5449:5471 */ 0x54e3ca0d00000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, 4)
                        }
                        let cleaned_35 := and(param_14, 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 6:15066:15083
                        let expr_29 := fun_toInt128_5750(param_15)
                        /// @src 6:15085:15095
                        fun_accountDelta(cleaned_35, expr_29, caller())
                        /// @src 6:4791:17612
                        let _76 := and(/** @src 2:651:665 */ param_13, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 2:651:694
                        let expr_30 := /** @src 2:651:665 */ iszero(eq(/** @src 6:4791:17612 */ _76, /** @src 6:15085:15095 */ caller()))
                        /// @src 2:651:694
                        if expr_30
                        {
                            /// @src 6:4791:17612
                            mstore(0, _76)
                            mstore(0x20, /** @src 2:670:680 */ 0x03)
                            /// @src 6:4791:17612
                            let dataSlot_27 := keccak256(0, 64)
                            /// @src 2:670:694
                            let dataSlot_28 := /** @src -1:-1:-1 */ 0
                            /// @src 6:4791:17612
                            mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 6:15085:15095 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, /** @src 2:670:686 */ dataSlot_27)
                            /// @src 6:4791:17612
                            dataSlot_28 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                            /// @src 2:651:694
                            expr_30 := /** @src 2:669:694 */ iszero(/** @src 6:4791:17612 */ and(sload(/** @src 2:670:694 */ dataSlot_28), /** @src 6:4791:17612 */ 0xff))
                        }
                        /// @src 2:647:916
                        if expr_30
                        {
                            /// @src 6:4791:17612
                            mstore(0, _76)
                            mstore(0x20, /** @src 2:736:745 */ 0x05)
                            /// @src 6:4791:17612
                            let dataSlot_29 := keccak256(0, 64)
                            /// @src 2:736:759
                            let dataSlot_30 := /** @src -1:-1:-1 */ 0
                            /// @src 6:4791:17612
                            mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 6:15085:15095 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, /** @src 2:736:751 */ dataSlot_29)
                            /// @src 6:4791:17612
                            dataSlot_30 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                            mstore(0, cleaned_35)
                            mstore(0x20, /** @src 2:736:759 */ dataSlot_30)
                            /// @src 6:4791:17612
                            let _77 := sload(keccak256(0, 64))
                            /// @src 2:777:906
                            if /** @src 2:781:817 */ iszero(eq(_77, /** @src 2:800:817 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
                            /// @src 2:777:906
                            {
                                /// @src 2:867:891
                                let expr_31 := checked_sub_uint256(_77, param_15)
                                /// @src 6:4791:17612
                                mstore(0, _76)
                                mstore(0x20, /** @src 2:736:745 */ 0x05)
                                /// @src 6:4791:17612
                                let dataSlot_31 := keccak256(0, 64)
                                /// @src 2:837:860
                                let dataSlot_32 := /** @src -1:-1:-1 */ 0
                                /// @src 6:4791:17612
                                mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 6:15085:15095 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                                mstore(0x20, /** @src 2:837:852 */ dataSlot_31)
                                /// @src 6:4791:17612
                                dataSlot_32 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                                mstore(0, cleaned_35)
                                mstore(0x20, /** @src 2:837:860 */ dataSlot_32)
                                /// @src 6:4791:17612
                                sstore(keccak256(0, 64), expr_31)
                            }
                        }
                        mstore(0, _76)
                        mstore(0x20, 4)
                        let dataSlot_33 := keccak256(0, 64)
                        mstore(0, cleaned_35)
                        mstore(0x20, dataSlot_33)
                        let dataSlot_34 := keccak256(0, 64)
                        sstore(dataSlot_34, /** @src 1:3388:3419 */ checked_sub_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:3388:3419 */ dataSlot_34), param_15))
                        /// @src 1:3435:3487
                        let _78 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 1:3435:3487
                        log4(_78, sub(abi_encode_address_uint256(_78, /** @src 6:15085:15095 */ caller(), /** @src 1:3435:3487 */ param_15), _78), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, _76, /** @src 6:4791:17612 */ 0, /** @src 1:3435:3487 */ cleaned_35)
                        /// @src 6:4791:17612
                        return(0, 0)
                    }
                    case 0xfe99049a {
                        if callvalue() { revert(0, 0) }
                        if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 128) { revert(0, 0) }
                        let value0_17 := abi_decode_address()
                        let value1_7 := abi_decode_address_40277()
                        let value_16 := calldataload(68)
                        let value_17 := calldataload(100)
                        let _79 := and(/** @src 1:1594:1614 */ value0_17, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 1:1594:1649
                        let expr_32 := /** @src 1:1594:1614 */ iszero(eq(/** @src 1:1594:1604 */ caller(), /** @src 6:4791:17612 */ _79))
                        /// @src 1:1594:1649
                        if expr_32
                        {
                            /// @src 6:4791:17612
                            mstore(0, _79)
                            mstore(32, /** @src 1:1619:1629 */ 0x03)
                            /// @src 6:4791:17612
                            let dataSlot_35 := keccak256(0, 64)
                            /// @src 1:1619:1649
                            let dataSlot_36 := /** @src -1:-1:-1 */ 0
                            /// @src 6:4791:17612
                            mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:1594:1604 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, /** @src 1:1619:1637 */ dataSlot_35)
                            /// @src 6:4791:17612
                            dataSlot_36 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                            /// @src 1:1594:1649
                            expr_32 := /** @src 1:1618:1649 */ iszero(/** @src 6:4791:17612 */ and(sload(/** @src 1:1619:1649 */ dataSlot_36), /** @src 6:4791:17612 */ 0xff))
                        }
                        /// @src 1:1590:1827
                        if expr_32
                        {
                            /// @src 6:4791:17612
                            mstore(0, _79)
                            mstore(32, /** @src 1:1683:1692 */ 0x05)
                            /// @src 6:4791:17612
                            let dataSlot_37 := keccak256(0, 64)
                            /// @src 1:1683:1712
                            let dataSlot_38 := /** @src -1:-1:-1 */ 0
                            /// @src 6:4791:17612
                            mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:1594:1604 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, /** @src 1:1683:1700 */ dataSlot_37)
                            /// @src 6:4791:17612
                            dataSlot_38 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                            mstore(0, value_16)
                            mstore(32, /** @src 1:1683:1712 */ dataSlot_38)
                            /// @src 6:4791:17612
                            let _80 := sload(keccak256(0, 64))
                            /// @src 1:1730:1816
                            if /** @src 1:1734:1762 */ iszero(eq(_80, /** @src 1:1745:1762 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
                            /// @src 1:1730:1816
                            {
                                /// @src 1:1800:1816
                                let expr_33 := checked_sub_uint256(_80, value_17)
                                /// @src 6:4791:17612
                                mstore(0, _79)
                                mstore(32, /** @src 1:1683:1692 */ 0x05)
                                /// @src 6:4791:17612
                                let dataSlot_39 := keccak256(0, 64)
                                /// @src 1:1764:1793
                                let dataSlot_40 := /** @src -1:-1:-1 */ 0
                                /// @src 6:4791:17612
                                mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ and(/** @src 1:1594:1604 */ caller(), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                                mstore(0x20, /** @src 1:1764:1781 */ dataSlot_39)
                                /// @src 6:4791:17612
                                dataSlot_40 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                                mstore(0, value_16)
                                mstore(32, /** @src 1:1764:1793 */ dataSlot_40)
                                /// @src 6:4791:17612
                                sstore(keccak256(0, 64), expr_33)
                            }
                        }
                        mstore(0, _79)
                        mstore(32, 4)
                        let dataSlot_41 := keccak256(0, 64)
                        mstore(0, value_16)
                        mstore(32, dataSlot_41)
                        let dataSlot_42 := keccak256(0, 64)
                        sstore(dataSlot_42, /** @src 1:1837:1868 */ checked_sub_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:1837:1868 */ dataSlot_42), value_17))
                        /// @src 6:4791:17612
                        let _81 := and(value1_7, 0xffffffffffffffffffffffffffffffffffffffff)
                        mstore(0, _81)
                        mstore(32, 4)
                        let dataSlot_43 := keccak256(0, 64)
                        mstore(0, value_16)
                        mstore(32, dataSlot_43)
                        let dataSlot_44 := keccak256(0, 64)
                        sstore(dataSlot_44, /** @src 1:1879:1912 */ checked_add_uint256(/** @src 6:4791:17612 */ sload(/** @src 1:1879:1912 */ dataSlot_44), value_17))
                        /// @src 1:1928:1978
                        let _82 := /** @src 6:4791:17612 */ mload(64)
                        /// @src 1:1928:1978
                        log4(_82, sub(abi_encode_address_uint256(_82, /** @src 1:1594:1604 */ caller(), /** @src 1:1928:1978 */ value_17), _82), 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859, _79, _81, value_16)
                        /// @src 6:4791:17612
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
            function abi_decode_address_40277() -> value
            {
                value := calldataload(36)
                if iszero(eq(value, and(value, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
            }
            function abi_decode_addresst_uint256t_uint256(dataEnd) -> value0, value1, value2
            {
                if slt(add(dataEnd, 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 96) { revert(0, 0) }
                let value := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                value := calldataload(4)
                if iszero(eq(value, and(value, 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0) }
                value0 := value
                value1 := calldataload(36)
                value2 := calldataload(68)
            }
            function finalize_allocation_40292(memPtr)
            {
                let newFreePtr := add(memPtr, 0x80)
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
                {
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x41)
                    revert(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x24)
                }
                mstore(64, newFreePtr)
            }
            function finalize_allocation_40320(memPtr)
            {
                let newFreePtr := add(memPtr, 0x60)
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
                {
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x41)
                    revert(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x24)
                }
                mstore(64, newFreePtr)
            }
            function finalize_allocation_40323(memPtr)
            {
                let newFreePtr := add(memPtr, 160)
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
                {
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x41)
                    revert(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x24)
                }
                mstore(64, newFreePtr)
            }
            function finalize_allocation(memPtr, size)
            {
                let newFreePtr := add(memPtr, and(add(size, 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr))
                {
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x41)
                    revert(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x24)
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
                finalize_allocation_40323(memPtr)
                value := memPtr
                let value_1 := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                value_1 := calldataload(4)
                if iszero(eq(value_1, and(value_1, 0xffffffffffffffffffffffffffffffffffffffff)))
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                mstore(memPtr, value_1)
                let value_2 := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                value_2 := calldataload(36)
                if iszero(eq(value_2, and(value_2, 0xffffffffffffffffffffffffffffffffffffffff)))
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                mstore(add(memPtr, 32), value_2)
                let value_3 := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                value_3 := calldataload(68)
                if iszero(eq(value_3, and(value_3, 0xffffff)))
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                mstore(add(memPtr, 64), value_3)
                let value_4 := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                value_4 := calldataload(100)
                if iszero(eq(value_4, signextend(2, value_4)))
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                mstore(add(memPtr, 96), value_4)
                let value_5 := calldataload(132)
                if iszero(eq(value_5, and(value_5, 0xffffffffffffffffffffffffffffffffffffffff)))
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
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
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                let length := calldataload(add(4, offset))
                if gt(length, 0xffffffffffffffff)
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
                if gt(add(add(offset, shl(5, length)), 36), dataEnd)
                {
                    revert(/** @src -1:-1:-1 */ 0, 0)
                }
                /// @src 6:4791:17612
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
                mstore(add(add(pos, length), 0x20), /** @src -1:-1:-1 */ 0)
                /// @src 6:4791:17612
                end := add(add(pos, and(add(length, 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), 0x20)
            }
            /// @ast-id 5750 @src 32:2098:2266
            function fun_toInt128_5750(var_x) -> var
            {
                /// @src 32:2168:2225
                if /** @src 32:2172:2185 */ iszero(lt(var_x, /** @src 32:2177:2185 */ 0x80000000000000000000000000000000))
                /// @src 32:2168:2225
                {
                    /// @src 19:814:910
                    mstore(0, /** @src 32:2187:2212 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(0, 0x04)
                }
                /// @src 32:2235:2259
                var := /** @src 6:4791:17612 */ signextend(15, /** @src 32:2249:2258 */ var_x)
            }
            /// @ast-id 1156 @src 6:16552:16908
            function fun_accountDelta(var_currency, var_delta, var_target)
            {
                /// @src 6:4791:17612
                let _1 := signextend(15, /** @src 6:16647:16657 */ var_delta)
                /// @src 6:16643:16666
                if /** @src 6:16647:16657 */ iszero(/** @src 6:4791:17612 */ _1)
                /// @src 6:16643:16666
                {
                    /// @src 6:16659:16666
                    leave
                }
                /// @src 17:1367:1397
                let expr := fun_computeSlot(var_target, var_currency)
                /// @src 17:1408:1484
                let var_previous := extcodehash(expr)
                /// @src 17:1500:1516
                let expr_1 := checked_add_int256(var_previous, /** @src 6:4791:17612 */ _1)
                /// @src 17:1526:1597
                log2(/** @src 6:16656:16657 */ 0x00, 0x00, /** @src 17:1526:1597 */ expr, expr_1)
                /// @src 6:16754:16902
                switch /** @src 6:16758:16767 */ iszero(expr_1)
                case /** @src 6:16754:16902 */ 0 {
                    /// @src 6:16829:16902
                    if /** @src 6:16833:16846 */ iszero(var_previous)
                    /// @src 6:16829:16902
                    {
                        /// @src 27:763:943
                        log2(/** @src 6:16656:16657 */ 0x00, 0x00, /** @src 27:763:943 */ 56671960505278111519104690822132496699113179860588238901689140059013086026251, add(extcodehash(56671960505278111519104690822132496699113179860588238901689140059013086026251), 1))
                    }
                }
                default /// @src 6:16754:16902
                {
                    /// @src 27:1271:1451
                    log2(/** @src 6:16656:16657 */ 0x00, 0x00, /** @src 27:1271:1451 */ 56671960505278111519104690822132496699113179860588238901689140059013086026251, add(extcodehash(56671960505278111519104690822132496699113179860588238901689140059013086026251), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
                }
            }
            /// @ast-id 6698 @src 40:1472:4345
            function fun_transfer(var_currency, var_to, var_amount)
            {
                /// @src 40:1769:1793
                let var := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                let _1 := and(/** @src 40:4998:5023 */ var_currency, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 40:4991:5056
                var := /** @src 40:4998:5056 */ iszero(/** @src 6:4791:17612 */ _1)
                /// @src 40:1765:4339
                switch /** @src 40:1769:1793 */ var
                case /** @src 40:1765:4339 */ 0 {
                    /// @src 40:2238:4012
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
                    mstore(add(usr$fmp, 4), and(var_to, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                    /// @src 40:2238:4012
                    mstore(add(usr$fmp, 36), var_amount)
                    let var_success := and(or(and(eq(mload(/** @src -1:-1:-1 */ 0), /** @src 40:2238:4012 */ 1), gt(returndatasize(), 31)), iszero(returndatasize())), call(gas(), var_currency, /** @src -1:-1:-1 */ 0, /** @src 40:2238:4012 */ usr$fmp, 68, /** @src -1:-1:-1 */ 0, /** @src 40:2238:4012 */ 32))
                    mstore(usr$fmp, /** @src -1:-1:-1 */ 0)
                    /// @src 40:2238:4012
                    mstore(add(usr$fmp, 32), /** @src -1:-1:-1 */ 0)
                    /// @src 40:2238:4012
                    mstore(add(usr$fmp, 0x40), /** @src -1:-1:-1 */ 0)
                    /// @src 40:4120:4329
                    if /** @src 40:4124:4132 */ iszero(var_success)
                    /// @src 40:4120:4329
                    {
                        /// @src 19:3741:5165
                        let usr$encodedDataSize := and(add(returndatasize(), /** @src 40:2238:4012 */ 31), /** @src 19:3741:5165 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
                        let usr$fmp_1 := mload(/** @src 40:2238:4012 */ 0x40)
                        /// @src 19:3741:5165
                        mstore(usr$fmp_1, /** @src 19:3710:3731 */ 0x90bfb86500000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3741:5165
                        mstore(add(usr$fmp_1, /** @src 40:2238:4012 */ 4), /** @src 19:3741:5165 */ _1)
                        mstore(add(usr$fmp_1, /** @src 40:2238:4012 */ 36), 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3741:5165
                        mstore(add(usr$fmp_1, /** @src 40:2238:4012 */ 68), /** @src 19:3741:5165 */ 0x80)
                        mstore(add(usr$fmp_1, 0x64), add(0xa0, usr$encodedDataSize))
                        mstore(add(usr$fmp_1, 0x84), returndatasize())
                        returndatacopy(add(usr$fmp_1, 0xa4), /** @src -1:-1:-1 */ 0, /** @src 19:3741:5165 */ returndatasize())
                        let _2 := add(usr$fmp_1, usr$encodedDataSize)
                        mstore(add(_2, 0xa4), /** @src 40:2238:4012 */ 4)
                        /// @src 19:3741:5165
                        mstore(add(_2, 0xc4), /** @src 40:4268:4296 */ 0xf27f64e400000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3741:5165
                        revert(usr$fmp_1, add(0xe4, usr$encodedDataSize))
                    }
                }
                default /// @src 40:1765:4339
                {
                    /// @src 40:2081:2208
                    if /** @src 40:2085:2093 */ iszero(/** @src 40:1809:1972 */ call(gas(), var_to, var_amount, /** @src -1:-1:-1 */ 0, 0, 0, 0))
                    /// @src 40:2081:2208
                    {
                        /// @src 19:3741:5165
                        let usr$encodedDataSize_1 := and(add(returndatasize(), 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
                        let usr$fmp_2 := mload(0x40)
                        mstore(usr$fmp_2, /** @src 19:3710:3731 */ 0x90bfb86500000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3741:5165
                        mstore(add(usr$fmp_2, 0x04), and(var_to, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                        /// @src 19:3741:5165
                        mstore(add(usr$fmp_2, 0x24), /** @src -1:-1:-1 */ 0)
                        /// @src 19:3741:5165
                        mstore(add(usr$fmp_2, 0x44), 0x80)
                        mstore(add(usr$fmp_2, 0x64), add(0xa0, usr$encodedDataSize_1))
                        mstore(add(usr$fmp_2, 0x84), returndatasize())
                        returndatacopy(add(usr$fmp_2, 0xa4), /** @src -1:-1:-1 */ 0, /** @src 19:3741:5165 */ returndatasize())
                        let _3 := add(usr$fmp_2, usr$encodedDataSize_1)
                        mstore(add(_3, 0xa4), 0x04)
                        mstore(add(_3, 0xc4), /** @src 40:2163:2192 */ 0xf4b3b1bc00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3741:5165
                        revert(usr$fmp_2, add(0xe4, usr$encodedDataSize_1))
                    }
                }
            }
            /// @ast-id 1109 @src 6:15649:16474
            function fun_settle(var_recipient) -> var_paid
            {
                /// @src 6:15703:15715
                var_paid := /** @src 6:4791:17612 */ 0
                /// @src 6:15747:15783
                let expr := /** @src 18:629:710 */ extcodehash(18037029214425852597980496522548842536420057720408124260691716999909707453369)
                /// @src 6:15916:15940
                let var := /** @src 6:4791:17612 */ 0
                /// @src 40:4991:5056
                var := /** @src 40:4998:5056 */ iszero(/** @src 6:4791:17612 */ and(/** @src 40:4998:5023 */ expr, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 6:15912:16406
                switch /** @src 6:15916:15940 */ var
                case /** @src 6:15912:16406 */ 0 {
                    /// @src 6:16003:16062
                    if /** @src 6:16007:16020 */ iszero(iszero(/** @src 6:16007:16016 */ callvalue()))
                    /// @src 6:16003:16062
                    {
                        /// @src 19:814:910
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 6:16022:16049 */ 0xb0ec849e00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 6:16314:16349
                    var_paid := /** @src 6:16321:16349 */ checked_sub_uint256(/** @src 6:16276:16300 */ fun_balanceOfSelf(expr), /** @src 18:1199:1280 */ extcodehash(13582234132832961652756477188584847927179359657859594952372729441197434191253))
                    /// @src 18:766:839
                    log2(/** @src 6:4791:17612 */ 0, 0, /** @src 18:629:710 */ 18037029214425852597980496522548842536420057720408124260691716999909707453369, /** @src 6:4791:17612 */ 0)
                }
                default /// @src 6:15912:16406
                {
                    /// @src 6:15956:15972
                    var_paid := /** @src 6:15963:15972 */ callvalue()
                }
                /// @src 6:16457:16466
                fun_accountDelta(expr, /** @src 6:16440:16455 */ fun_toInt128_5750(var_paid), /** @src 6:16457:16466 */ var_recipient)
            }
            /// @ast-id 1405 @src 5:963:1100
            function fun_checkNotDelegateCall()
            {
                /// @src 5:1018:1093
                if /** @src 5:1022:1047 */ iszero(eq(/** @src 5:1030:1034 */ address(), /** @src 6:4791:17612 */ and(/** @src 5:1039:1047 */ loadimmutable("1375"), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)))
                /// @src 5:1018:1093
                {
                    /// @src 19:814:910
                    mstore(0, /** @src 5:1049:1080 */ 0x0d89438e00000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(0, 0x04)
                }
            }
            /// @ast-id 5344 @src 29:28591:28748
            function fun_checkPoolInitialized(var_self_5326_slot)
            {
                /// @src 29:28665:28741
                if /** @src 29:28669:28699 */ iszero(/** @src 44:1502:1595 */ and(1461501637330902918203684832716283019655932542975, /** @src 6:4791:17612 */ sload(/** @src 29:28669:28679 */ var_self_5326_slot)))
                /// @src 29:28665:28741
                {
                    /// @src 19:814:910
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 29:28701:28728 */ 0x486aa30700000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(/** @src -1:-1:-1 */ 0, /** @src 19:814:910 */ 0x04)
                }
            }
            /// @src 23:1907:1913
            function abi_encode_struct_PoolKey(value, pos)
            {
                /// @src 6:5241:5266
                mstore(pos, /** @src 6:4791:17612 */ and(/** @src 23:1907:1913 */ mload(value), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 6:5241:5266
                mstore(/** @src 23:1907:1913 */ add(pos, 0x20), /** @src 6:4791:17612 */ and(/** @src 23:1907:1913 */ mload(add(value, 0x20)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 6:5241:5266
                mstore(/** @src 23:1907:1913 */ add(pos, 0x40), /** @src 6:4791:17612 */ and(/** @src 23:1907:1913 */ mload(add(value, 0x40)), /** @src 6:4791:17612 */ 0xffffff))
                mstore(/** @src 23:1907:1913 */ add(pos, 0x60), /** @src 6:4791:17612 */ signextend(2, /** @src 23:1907:1913 */ mload(add(value, 0x60))))
                /// @src 6:5241:5266
                mstore(/** @src 23:1907:1913 */ add(pos, 0x80), /** @src 6:4791:17612 */ and(/** @src 23:1907:1913 */ mload(add(value, 0x80)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
            }
            /// @src 23:1907:1913
            function abi_encode_address_struct_PoolKey_uint256_uint256_bytes_calldata(headStart, value0, value1, value2, value3, value4, value5) -> tail
            {
                /// @src 6:4791:17612
                mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:1907:1913
                abi_encode_struct_PoolKey(value1, add(headStart, 32))
                /// @src 6:4791:17612
                mstore(/** @src 23:1907:1913 */ add(headStart, 192), /** @src 6:4791:17612 */ value2)
                mstore(/** @src 23:1907:1913 */ add(headStart, 224), /** @src 6:4791:17612 */ value3)
                /// @src 23:1907:1913
                mstore(add(headStart, 256), 288)
                tail := abi_encode_bytes_calldata(value4, value5, add(headStart, 288))
            }
            /// @ast-id 1187 @src 6:16986:17218
            function fun_accountPoolBalanceDelta(var_key_mpos, var_delta, var_target)
            {
                /// @src 6:4791:17612
                let cleaned := and(/** @src 6:5241:5266 */ mload(/** @src 6:17109:17122 */ var_key_mpos), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 6:17141:17147
                fun_accountDelta(cleaned, /** @src 38:2052:2135 */ sar(128, /** @src 6:17124:17139 */ var_delta), /** @src 6:17141:17147 */ var_target)
                /// @src 6:4791:17612
                let cleaned_1 := and(/** @src 6:5241:5266 */ mload(/** @src 6:17172:17185 */ add(var_key_mpos, 32)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 6:17204:17210
                fun_accountDelta(cleaned_1, /** @src 38:2241:2330 */ signextend(15, /** @src 6:17187:17202 */ var_delta), /** @src 6:17204:17210 */ var_target)
            }
            /// @ast-id 3608 @src 24:1833:1955
            function fun_validate(var_self)
            {
                /// @src 6:4791:17612
                let cleaned := and(var_self, 0xffffff)
                /// @src 24:1888:1948
                if /** @src 24:1667:1685 */ gt(cleaned, /** @src 24:1111:1118 */ 0x0f4240)
                /// @src 24:1888:1948
                {
                    /// @src 19:1084:1260
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 24:1909:1931 */ 0x1400211300000000000000000000000000000000000000000000000000000000)
                    /// @src 19:1084:1260
                    mstore(0x04, cleaned)
                    revert(/** @src -1:-1:-1 */ 0, /** @src 19:1084:1260 */ 0x24)
                }
            }
            /// @src 23:1665:1671
            function abi_encode_struct_ModifyLiquidityParams(value, pos)
            {
                /// @src 6:4791:17612
                mstore(pos, signextend(2, /** @src 23:1665:1671 */ mload(value)))
                /// @src 6:4791:17612
                mstore(/** @src 23:1665:1671 */ add(pos, 0x20), /** @src 6:4791:17612 */ signextend(2, /** @src 23:1665:1671 */ mload(add(value, 0x20))))
                /// @src 6:4791:17612
                mstore(/** @src 23:1665:1671 */ add(pos, 0x40), mload(add(value, 0x40)))
                /// @src 6:4791:17612
                mstore(/** @src 23:1665:1671 */ add(pos, 0x60), mload(add(value, 0x60)))
            }
            function abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_bytes_calldata(headStart, value0, value1, value2, value3, value4) -> tail
            {
                /// @src 6:4791:17612
                mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:1665:1671
                abi_encode_struct_PoolKey(value1, add(headStart, 32))
                abi_encode_struct_ModifyLiquidityParams(value2, add(headStart, 192))
                mstore(add(headStart, 320), 352)
                tail := abi_encode_bytes_calldata(value3, value4, add(headStart, 352))
            }
            /// @ast-id 5693 @src 32:1460:1611
            function fun_toInt128(var_x) -> var_y
            {
                /// @src 32:1531:1544
                var_y := /** @src 6:4791:17612 */ signextend(15, /** @src 32:1535:1544 */ var_x)
                /// @src 32:1554:1604
                if /** @src 32:1558:1564 */ iszero(eq(/** @src 6:4791:17612 */ var_y, /** @src 32:1558:1564 */ var_x))
                /// @src 32:1554:1604
                {
                    /// @src 19:814:910
                    mstore(0, /** @src 32:1566:1591 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(0, 0x04)
                }
            }
            /// @src 23:1733:1739
            function abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(headStart, value0, value1, value2, value3, value4, value5, value6) -> tail
            {
                /// @src 6:4791:17612
                mstore(headStart, and(value0, 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:1733:1739
                abi_encode_struct_PoolKey(value1, add(headStart, 32))
                abi_encode_struct_ModifyLiquidityParams(value2, add(headStart, 192))
                /// @src 6:4791:17612
                mstore(/** @src 23:1733:1739 */ add(headStart, 320), /** @src 6:4791:17612 */ value3)
                mstore(/** @src 23:1733:1739 */ add(headStart, 352), /** @src 6:4791:17612 */ value4)
                /// @src 23:1733:1739
                mstore(add(headStart, 384), 416)
                tail := abi_encode_bytes_calldata(value5, value6, add(headStart, 416))
            }
            /// @ast-id 3153 @src 23:10471:12029
            function fun_afterModifyLiquidity(var_self_3029_address, var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length) -> var_callerDelta, var_hookDelta
            {
                /// @src 23:10740:10762
                var_hookDelta := /** @src 6:4791:17612 */ 0
                /// @src 23:10774:10853
                if /** @src 23:10778:10805 */ eq(/** @src 23:10778:10788 */ caller(), /** @src 6:4791:17612 */ and(/** @src 23:10792:10805 */ var_self_3029_address, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:10774:10853
                {
                    /// @src 23:10807:10853
                    var_callerDelta := var_delta
                    var_hookDelta := /** @src 6:4791:17612 */ 0
                    /// @src 23:10807:10853
                    leave
                }
                /// @src 23:10864:10883
                var_callerDelta := var_delta
                /// @src 23:10893:12023
                switch /** @src 23:10897:10922 */ sgt(/** @src 6:4791:17612 */ mload(/** @src 23:10897:10918 */ add(var_params_3035_mpos, 64)), /** @src 6:4791:17612 */ 0)
                case /** @src 23:10893:12023 */ 0 {
                    /// @src 23:11490:11537
                    let var := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:11490:11537 */ var_self_3029_address, /** @src 6:4791:17612 */ 256)))
                    /// @src 23:11486:12013
                    if /** @src 23:11490:11537 */ var
                    /// @src 23:11486:12013
                    {
                        /// @src 23:11662:11816
                        let expr_3133_mpos := /** @src 6:4791:17612 */ mload(/** @src 23:10897:10918 */ 64)
                        /// @src 23:11662:11816
                        mstore(add(expr_3133_mpos, 0x20), 0x6c2bbe7e00000000000000000000000000000000000000000000000000000000)
                        let _1 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(add(expr_3133_mpos, 36), /** @src 23:10778:10788 */ caller(), /** @src 23:11662:11816 */ var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length), expr_3133_mpos)
                        mstore(expr_3133_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                        finalize_allocation(expr_3133_mpos, _1)
                        /// @src 23:11842:11903
                        let var_1 := /** @src -1:-1:-1 */ 0
                        /// @src 23:16460:16501
                        var_1 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:11842:11903 */ var_self_3029_address, /** @src 6:4791:17612 */ 1)))
                        /// @src 23:11557:11943
                        var_hookDelta := /** @src 23:11608:11925 */ fun_callHookWithReturnDelta(var_self_3029_address, expr_3133_mpos, /** @src 23:11842:11903 */ var_1)
                        /// @src 23:11961:11998
                        var_callerDelta := /** @src 23:11975:11998 */ fun_sub(var_delta, var_hookDelta)
                    }
                }
                default /// @src 23:10893:12023
                {
                    /// @src 23:10942:10986
                    let var_2 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_2 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:10942:10986 */ var_self_3029_address, /** @src 6:4791:17612 */ 1024)))
                    /// @src 23:10938:11456
                    if /** @src 23:10942:10986 */ var_2
                    /// @src 23:10938:11456
                    {
                        /// @src 23:11111:11262
                        let expr_3094_mpos := /** @src 6:4791:17612 */ mload(/** @src 23:10897:10918 */ 64)
                        /// @src 23:11111:11262
                        mstore(add(expr_3094_mpos, 0x20), 0x9f063efc00000000000000000000000000000000000000000000000000000000)
                        let _2 := sub(abi_encode_address_struct_PoolKey_struct_ModifyLiquidityParams_userDefinedValueType_BalanceDelta_userDefinedValueType_BalanceDelta_bytes_calldata(add(expr_3094_mpos, 36), /** @src 23:10778:10788 */ caller(), /** @src 23:11111:11262 */ var_key_3032_mpos, var_params_3035_mpos, var_delta, var_feesAccrued, var_hookData_offset, var_hookData_length), expr_3094_mpos)
                        mstore(expr_3094_mpos, add(_2, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                        finalize_allocation(expr_3094_mpos, _2)
                        /// @src 23:11288:11346
                        let var_3 := /** @src -1:-1:-1 */ 0
                        /// @src 23:16460:16501
                        var_3 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:11288:11346 */ var_self_3029_address, /** @src 6:4791:17612 */ 2)))
                        /// @src 23:11006:11386
                        var_hookDelta := /** @src 23:11057:11368 */ fun_callHookWithReturnDelta(var_self_3029_address, expr_3094_mpos, /** @src 23:11288:11346 */ var_3)
                        /// @src 23:11404:11441
                        var_callerDelta := /** @src 23:11418:11441 */ fun_sub(var_callerDelta, var_hookDelta)
                    }
                }
            }
            /// @ast-id 2760 @src 23:5485:6604
            function fun_isValidHookAddress(var_self_2668_address, var_fee) -> var_
            {
                /// @src 23:5561:5565
                var_ := /** @src 6:4791:17612 */ 0
                /// @src 23:5704:5740
                let var := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5704:5740 */ var_self_2668_address, /** @src 6:4791:17612 */ 128)))
                /// @src 23:5703:5794
                let expr := /** @src 23:5703:5740 */ iszero(/** @src 23:5704:5740 */ var)
                /// @src 23:5703:5794
                if expr
                {
                    /// @src 23:5744:5794
                    let var_1 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_1 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5744:5794 */ var_self_2668_address, /** @src 6:4791:17612 */ 8)))
                    /// @src 23:5703:5794
                    expr := var_1
                }
                /// @src 23:5699:5808
                if expr
                {
                    /// @src 23:5796:5808
                    var_ := /** @src 6:4791:17612 */ 0
                    /// @src 23:5796:5808
                    leave
                }
                /// @src 23:5823:5858
                let var_2 := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var_2 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5823:5858 */ var_self_2668_address, /** @src 6:4791:17612 */ 64)))
                /// @src 23:5822:5911
                let expr_1 := /** @src 23:5822:5858 */ iszero(/** @src 23:5823:5858 */ var_2)
                /// @src 23:5822:5911
                if expr_1
                {
                    /// @src 23:5862:5911
                    let var_3 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_3 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5862:5911 */ var_self_2668_address, /** @src 6:4791:17612 */ 4)))
                    /// @src 23:5822:5911
                    expr_1 := var_3
                }
                /// @src 23:5818:5925
                if expr_1
                {
                    /// @src 23:5913:5925
                    var_ := /** @src 6:4791:17612 */ 0
                    /// @src 23:5913:5925
                    leave
                }
                /// @src 23:5940:5984
                let var_4 := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var_4 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5940:5984 */ var_self_2668_address, /** @src 6:4791:17612 */ 1024)))
                /// @src 23:5939:6046
                let expr_2 := /** @src 23:5939:5984 */ iszero(/** @src 23:5940:5984 */ var_4)
                /// @src 23:5939:6046
                if expr_2
                {
                    /// @src 23:5988:6046
                    let var_5 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_5 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:5988:6046 */ var_self_2668_address, /** @src 6:4791:17612 */ 2)))
                    /// @src 23:5939:6046
                    expr_2 := var_5
                }
                /// @src 23:5935:6093
                if expr_2
                {
                    /// @src 23:6070:6082
                    var_ := /** @src 6:4791:17612 */ 0
                    /// @src 23:6070:6082
                    leave
                }
                /// @src 23:6120:6167
                let var_6 := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var_6 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:6120:6167 */ var_self_2668_address, /** @src 6:4791:17612 */ 256)))
                /// @src 23:6119:6248
                let expr_3 := /** @src 23:6119:6167 */ iszero(/** @src 23:6120:6167 */ var_6)
                /// @src 23:6119:6248
                if expr_3
                {
                    /// @src 23:6187:6248
                    let var_7 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_7 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:6187:6248 */ var_self_2668_address, /** @src 6:4791:17612 */ 1)))
                    /// @src 23:6119:6248
                    expr_3 := var_7
                }
                /// @src 23:6102:6271
                if expr_3
                {
                    /// @src 23:6259:6271
                    var_ := /** @src 6:4791:17612 */ 0
                    /// @src 23:6259:6271
                    leave
                }
                /// @src 23:6455:6597
                let expr_4 := /** @src 6:4791:17612 */ 0
                /// @src 23:6455:6597
                switch /** @src 23:6455:6482 */ iszero(/** @src 6:4791:17612 */ and(/** @src 23:6455:6468 */ var_self_2668_address, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                case /** @src 23:6455:6597 */ 0 {
                    /// @src 23:6532:6574
                    let _1 := iszero(/** @src 23:6532:6570 */ and(/** @src 23:6455:6468 */ var_self_2668_address, /** @src 23:1325:1338 */ 0x3fff))
                    /// @src 23:6532:6596
                    let expr_5 := /** @src 23:6532:6574 */ iszero(_1)
                    /// @src 23:6532:6596
                    if _1
                    {
                        expr_5 := /** @src 24:1379:1403 */ eq(/** @src 6:4791:17612 */ and(/** @src 23:6578:6596 */ var_fee, /** @src 6:4791:17612 */ 0xffffff), /** @src 24:552:560 */ 0x800000)
                    }
                    /// @src 23:6455:6597
                    expr_4 := expr_5
                }
                default {
                    expr_4 := /** @src 23:6497:6516 */ iszero(/** @src 24:1379:1403 */ eq(/** @src 6:4791:17612 */ and(/** @src 23:6498:6516 */ var_fee, /** @src 6:4791:17612 */ 0xffffff), /** @src 24:552:560 */ 0x800000))
                }
                /// @src 23:6448:6597
                var_ := expr_4
            }
            /// @ast-id 3630 @src 24:2333:2553
            function fun_getInitialLPFee(var_self) -> var
            {
                /// @src 24:2394:2400
                var := /** @src 6:4791:17612 */ 0
                /// @src 24:2467:2500
                if /** @src 24:1379:1403 */ eq(/** @src 6:4791:17612 */ and(/** @src 24:2471:2490 */ var_self, /** @src 6:4791:17612 */ 0xffffff), /** @src 24:552:560 */ 0x800000)
                /// @src 24:2467:2500
                {
                    /// @src 24:2492:2500
                    var := /** @src 6:4791:17612 */ 0
                    /// @src 24:2492:2500
                    leave
                }
                /// @src 24:2510:2523
                fun_validate(var_self)
                /// @src 24:2535:2546
                var := var_self
            }
            /// @ast-id 6732 @src 40:4351:4627
            function fun_balanceOfSelf(var_currency) -> var
            {
                /// @src 40:4416:4423
                var := /** @src 6:4791:17612 */ 0
                /// @src 40:4439:4463
                let var_1 := /** @src 6:4791:17612 */ 0
                let _1 := and(/** @src 40:4998:5023 */ var_currency, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 40:4991:5056
                var_1 := /** @src 40:4998:5056 */ iszero(/** @src 6:4791:17612 */ _1)
                /// @src 40:4435:4621
                switch /** @src 40:4439:4463 */ var_1
                case /** @src 40:4435:4621 */ 0 {
                    /// @src 40:4545:4610
                    let _2 := /** @src 6:4791:17612 */ mload(64)
                    /// @src 40:4545:4610
                    mstore(_2, /** @src 6:4791:17612 */ 0x70a0823100000000000000000000000000000000000000000000000000000000)
                    mstore(/** @src 40:4545:4610 */ add(_2, 4), /** @src 40:4604:4608 */ address())
                    /// @src 40:4545:4610
                    let _3 := staticcall(gas(), _1, _2, 36, _2, /** @src 6:4791:17612 */ 32)
                    /// @src 40:4545:4610
                    if iszero(_3)
                    {
                        /// @src 6:4791:17612
                        let pos := mload(64)
                        returndatacopy(pos, 0, returndatasize())
                        revert(pos, returndatasize())
                    }
                    /// @src 40:4545:4610
                    let expr := /** @src 6:4791:17612 */ 0
                    /// @src 40:4545:4610
                    if _3
                    {
                        let _4 := /** @src 6:4791:17612 */ 32
                        /// @src 40:4545:4610
                        if gt(/** @src 6:4791:17612 */ 32, /** @src 40:4545:4610 */ returndatasize()) { _4 := returndatasize() }
                        finalize_allocation(_2, _4)
                        /// @src 6:4791:17612
                        if slt(sub(/** @src 40:4545:4610 */ add(_2, _4), /** @src 6:4791:17612 */ _2), 32) { revert(0, 0) }
                        /// @src 40:4545:4610
                        expr := /** @src 6:4791:17612 */ mload(_2)
                    }
                    /// @src 40:4538:4610
                    var := expr
                    leave
                }
                default /// @src 40:4435:4621
                {
                    /// @src 40:4479:4507
                    var := /** @src 40:4486:4507 */ selfbalance()
                    /// @src 40:4479:4507
                    leave
                }
            }
            /// @src 39:809:832
            function abi_encode_struct_SwapParams(value, pos)
            {
                /// @src 6:4791:17612
                mstore(pos, iszero(iszero(/** @src 39:809:832 */ mload(value))))
                /// @src 6:4791:17612
                mstore(/** @src 39:809:832 */ add(pos, 0x20), mload(add(value, 0x20)))
                /// @src 6:4791:17612
                mstore(/** @src 39:809:832 */ add(pos, 0x40), /** @src 6:4791:17612 */ and(/** @src 39:809:832 */ mload(add(value, 0x40)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
            }
            /// @src 39:809:832
            function checked_add_int256(x, y) -> sum
            {
                sum := add(x, y)
                let _1 := slt(sum, y)
                let _2 := slt(x, 0)
                if or(and(iszero(_2), _1), and(_2, iszero(_1)))
                {
                    /// @src 6:4791:17612
                    mstore(/** @src 39:809:832 */ 0, /** @src 6:4791:17612 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x11)
                    revert(/** @src 39:809:832 */ 0, /** @src 6:4791:17612 */ 0x24)
                }
            }
            /// @ast-id 3294 @src 23:12116:14083
            function fun_beforeSwap(var_self_3157_address, var_key_3160_mpos, var_params_3163_mpos, var_hookData_3165_offset, var_hookData_3165_length) -> var_amountToSwap, var_hookReturn, var_lpFeeOverride
            {
                /// @src 23:12275:12301
                var_hookReturn := /** @src 6:4791:17612 */ 0
                /// @src 23:12303:12323
                var_lpFeeOverride := /** @src 6:4791:17612 */ 0
                /// @src 23:12339:12376
                var_amountToSwap := /** @src 6:4791:17612 */ mload(/** @src 23:12354:12376 */ add(var_params_3163_mpos, 32))
                /// @src 23:12386:12490
                if /** @src 23:12390:12417 */ eq(/** @src 23:12390:12400 */ caller(), /** @src 6:4791:17612 */ and(/** @src 23:12404:12417 */ var_self_3157_address, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:12386:12490
                {
                    /// @src 23:12419:12490
                    var_amountToSwap := var_amountToSwap
                    var_hookReturn := /** @src 6:4791:17612 */ 0
                    /// @src 23:12419:12490
                    var_lpFeeOverride := /** @src 6:4791:17612 */ 0
                    /// @src 23:12419:12490
                    leave
                }
                /// @src 23:12505:12541
                let var := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:12505:12541 */ var_self_3157_address, /** @src 6:4791:17612 */ 128)))
                /// @src 23:12501:14077
                if /** @src 23:12505:12541 */ var
                /// @src 23:12501:14077
                {
                    /// @src 23:12594:12664
                    let expr_3212_mpos := /** @src 6:4791:17612 */ mload(64)
                    /// @src 23:12594:12664
                    mstore(add(expr_3212_mpos, /** @src 23:12354:12376 */ 32), /** @src 23:12594:12664 */ 0x575e24b400000000000000000000000000000000000000000000000000000000)
                    /// @src 6:4791:17612
                    mstore(/** @src 23:12594:12664 */ add(expr_3212_mpos, 36), /** @src 23:12390:12400 */ caller())
                    /// @src 39:809:832
                    abi_encode_struct_PoolKey(var_key_3160_mpos, add(/** @src 23:12594:12664 */ expr_3212_mpos, /** @src 39:809:832 */ 68))
                    abi_encode_struct_SwapParams(var_params_3163_mpos, add(/** @src 23:12594:12664 */ expr_3212_mpos, /** @src 39:809:832 */ 228))
                    mstore(add(/** @src 23:12594:12664 */ expr_3212_mpos, /** @src 39:809:832 */ 324), 320)
                    /// @src 23:12594:12664
                    let _1 := sub(/** @src 39:809:832 */ abi_encode_bytes_calldata(var_hookData_3165_offset, var_hookData_3165_length, add(/** @src 23:12594:12664 */ expr_3212_mpos, /** @src 39:809:832 */ 356)), /** @src 23:12594:12664 */ expr_3212_mpos)
                    mstore(expr_3212_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                    finalize_allocation(expr_3212_mpos, _1)
                    /// @src 23:12579:12665
                    let expr_3213_mpos := fun_callHook(var_self_3157_address, expr_3212_mpos)
                    /// @src 23:12779:12845
                    if /** @src 23:12783:12802 */ iszero(eq(/** @src 6:4791:17612 */ mload(/** @src 23:12783:12796 */ expr_3213_mpos), /** @src 23:12800:12802 */ 0x60))
                    /// @src 23:12779:12845
                    {
                        /// @src 19:814:910
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 23:12804:12832 */ 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 23:13115:13176
                    if /** @src 24:1379:1403 */ eq(/** @src 6:4791:17612 */ and(mload(/** @src 23:13119:13126 */ add(var_key_3160_mpos, /** @src 6:4791:17612 */ 64)), 0xffffff), /** @src 24:552:560 */ 0x800000)
                    /// @src 23:13115:13176
                    {
                        /// @src 23:13143:13176
                        var_lpFeeOverride := /** @src 28:828:910 */ mload(add(/** @src 23:13159:13176 */ expr_3213_mpos, /** @src 23:12800:12802 */ 0x60))
                    }
                    /// @src 23:13266:13316
                    let var_1 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_1 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:13266:13316 */ var_self_3157_address, /** @src 6:4791:17612 */ 8)))
                    /// @src 23:13262:14067
                    if /** @src 23:13266:13316 */ var_1
                    /// @src 23:13262:14067
                    {
                        /// @src 23:13336:13396
                        var_hookReturn := /** @src 28:1104:1191 */ mload(add(/** @src 23:13370:13395 */ expr_3213_mpos, /** @src 6:4791:17612 */ 64))
                        let _2 := signextend(15, /** @src 38:2052:2135 */ sar(/** @src 23:1791:1797 */ 0x80, /** @src 23:13533:13563 */ var_hookReturn))
                        /// @src 23:13721:14053
                        if /** @src 23:13725:13748 */ iszero(iszero(/** @src 6:4791:17612 */ _2))
                        /// @src 23:13721:14053
                        {
                            /// @src 23:13790:13806
                            let expr := slt(var_amountToSwap, /** @src 6:4791:17612 */ 0)
                            /// @src 23:13828:13862
                            var_amountToSwap := checked_add_int256(var_amountToSwap, /** @src 6:4791:17612 */ _2)
                            /// @src 23:13888:13936
                            let expr_1 := /** @src 6:4791:17612 */ 0
                            /// @src 23:13888:13936
                            switch expr
                            case 0 {
                                expr_1 := /** @src 23:13920:13936 */ slt(var_amountToSwap, /** @src 6:4791:17612 */ 0)
                            }
                            default /// @src 23:13888:13936
                            {
                                expr_1 := /** @src 23:13901:13917 */ sgt(var_amountToSwap, /** @src 6:4791:17612 */ 0)
                            }
                            /// @src 23:13884:14035
                            if expr_1
                            {
                                /// @src 19:814:910
                                mstore(/** @src 6:4791:17612 */ 0, /** @src 23:13964:13999 */ 0xfa0b71d600000000000000000000000000000000000000000000000000000000)
                                /// @src 19:814:910
                                revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                            }
                        }
                    }
                }
            }
            /// @src 6:4791:17612
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
            /// @ast-id 3420 @src 23:14169:15507
            function fun_afterSwap(var_self_address, var_key_3301_mpos, var_params_mpos, var_swapDelta, var_hookData_3309_offset, var_hookData_3309_length, var_beforeSwapHookReturn) -> var, var_1
            {
                /// @src 23:14444:14527
                if /** @src 23:14448:14475 */ eq(/** @src 23:14448:14458 */ caller(), /** @src 6:4791:17612 */ and(/** @src 23:14462:14475 */ var_self_address, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 23:14444:14527
                {
                    /// @src 23:14477:14527
                    var := var_swapDelta
                    var_1 := /** @src 6:4791:17612 */ 0
                    /// @src 23:14477:14527
                    leave
                }
                /// @src 23:14566:14606
                let expr := /** @src 38:2052:2135 */ sar(128, /** @src 23:14566:14606 */ var_beforeSwapHookReturn)
                /// @src 23:14616:14688
                let var_hookDeltaUnspecified := /** @src 38:2241:2330 */ signextend(15, /** @src 23:14646:14688 */ var_beforeSwapHookReturn)
                /// @src 23:14703:14738
                let var_2 := /** @src -1:-1:-1 */ 0
                /// @src 23:16460:16501
                var_2 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:14703:14738 */ var_self_address, /** @src 6:4791:17612 */ 64)))
                /// @src 23:14699:15007
                if /** @src 23:14703:14738 */ var_2
                /// @src 23:14699:15007
                {
                    /// @src 23:14824:14904
                    let expr_mpos := /** @src 6:4791:17612 */ mload(/** @src 23:1847:1853 */ 0x40)
                    /// @src 23:14824:14904
                    mstore(add(expr_mpos, 0x20), 0xb47b2fb100000000000000000000000000000000000000000000000000000000)
                    /// @src 6:4791:17612
                    mstore(/** @src 23:14824:14904 */ add(expr_mpos, 36), /** @src 23:14448:14458 */ caller())
                    /// @src 6:4791:17612
                    abi_encode_struct_PoolKey(var_key_3301_mpos, add(/** @src 23:14824:14904 */ expr_mpos, /** @src 6:4791:17612 */ 68))
                    abi_encode_struct_SwapParams(var_params_mpos, add(/** @src 23:14824:14904 */ expr_mpos, /** @src 6:4791:17612 */ 228))
                    mstore(add(/** @src 23:14824:14904 */ expr_mpos, /** @src 6:4791:17612 */ 324), var_swapDelta)
                    mstore(add(/** @src 23:14824:14904 */ expr_mpos, /** @src 6:4791:17612 */ 356), 352)
                    /// @src 23:14824:14904
                    let _1 := sub(/** @src 6:4791:17612 */ abi_encode_bytes_calldata(var_hookData_3309_offset, var_hookData_3309_length, add(/** @src 23:14824:14904 */ expr_mpos, /** @src 6:4791:17612 */ 388)), /** @src 23:14824:14904 */ expr_mpos)
                    mstore(expr_mpos, add(_1, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                    finalize_allocation(expr_mpos, _1)
                    /// @src 23:14922:14971
                    let var_3 := /** @src -1:-1:-1 */ 0
                    /// @src 23:16460:16501
                    var_3 := /** @src 23:16467:16501 */ iszero(iszero(/** @src 23:16467:16496 */ and(/** @src 23:14922:14971 */ var_self_address, /** @src 6:4791:17612 */ 4)))
                    /// @src 23:14754:14996
                    var_hookDeltaUnspecified := checked_add_int128(var_hookDeltaUnspecified, /** @src 23:14778:14996 */ fun_toInt128(/** @src 23:14778:14985 */ fun_callHookWithReturnDelta(var_self_address, expr_mpos, /** @src 23:14922:14971 */ var_3)))
                }
                /// @src 23:15017:15039
                let var_hookDelta := /** @src 6:4791:17612 */ 0
                /// @src 23:15017:15039
                var_hookDelta := /** @src 6:4791:17612 */ 0
                /// @src 23:15053:15078
                let _2 := iszero(/** @src 6:4791:17612 */ signextend(/** @src 38:2241:2330 */ 15, /** @src 23:15053:15078 */ var_hookDeltaUnspecified))
                /// @src 23:15053:15105
                let expr_1 := /** @src 23:15053:15078 */ iszero(_2)
                /// @src 23:15053:15105
                if _2
                {
                    expr_1 := /** @src 23:15082:15105 */ iszero(iszero(/** @src 6:4791:17612 */ signextend(/** @src 38:2241:2330 */ 15, /** @src 23:15082:15105 */ expr)))
                }
                /// @src 23:15049:15462
                if expr_1
                {
                    /// @src 23:15134:15160
                    let expr_2 := slt(/** @src 6:4791:17612 */ mload(/** @src 23:15134:15156 */ add(var_params_mpos, 32)), /** @src 6:4791:17612 */ 0)
                    /// @src 23:15134:15181
                    let expr_3 := eq(/** @src 6:4791:17612 */ expr_2, iszero(iszero(mload(/** @src 23:15164:15181 */ var_params_mpos))))
                    /// @src 23:15133:15332
                    let expr_4 := /** @src 6:4791:17612 */ 0
                    /// @src 23:15133:15332
                    switch expr_3
                    case 0 {
                        expr_4 := /** @src 38:553:668 */ or(shl(/** @src 38:2052:2135 */ 128, /** @src 38:553:668 */ var_hookDeltaUnspecified), and(0xffffffffffffffffffffffffffffffff, expr))
                    }
                    default /// @src 23:15133:15332
                    {
                        expr_4 := /** @src 38:553:668 */ or(shl(/** @src 38:2052:2135 */ 128, /** @src 38:553:668 */ expr), and(0xffffffffffffffffffffffffffffffff, var_hookDeltaUnspecified))
                    }
                    /// @src 23:15121:15332
                    var_hookDelta := expr_4
                    /// @src 23:15418:15451
                    var_swapDelta := /** @src 23:15430:15451 */ fun_sub(var_swapDelta, expr_4)
                }
                /// @src 23:15471:15500
                var := var_swapDelta
                var_1 := var_hookDelta
            }
            /// @ast-id 2816 @src 23:6780:8056
            function fun_callHook(var_self_2764_address, var_data_mpos) -> var_result_mpos
            {
                /// @src 23:6901:7017
                let _1 := mload(var_data_mpos)
                let _2 := add(var_data_mpos, 0x20)
                /// @src 23:7107:7209
                if /** @src 23:7111:7119 */ iszero(/** @src 23:6901:7017 */ call(gas(), var_self_2764_address, /** @src -1:-1:-1 */ 0, /** @src 23:6901:7017 */ _2, _1, /** @src -1:-1:-1 */ 0, 0))
                /// @src 23:7107:7209
                {
                    /// @src 23:7171:7183
                    let value := /** @src -1:-1:-1 */ 0
                    /// @src 6:4791:17612
                    let length := mload(var_data_mpos)
                    let _3 := mload(_2)
                    value := and(_3, 0xffffffff00000000000000000000000000000000000000000000000000000000)
                    if lt(length, 4)
                    {
                        value := and(and(_3, shl(shl(3, sub(4, length)), 0xffffffff00000000000000000000000000000000000000000000000000000000)), 0xffffffff00000000000000000000000000000000000000000000000000000000)
                    }
                    /// @src 19:3741:5165
                    let usr$encodedDataSize := and(add(returndatasize(), 31), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, /** @src 19:3710:3731 */ 0x90bfb86500000000000000000000000000000000000000000000000000000000)
                    /// @src 19:3741:5165
                    mstore(add(usr$fmp, /** @src 6:4791:17612 */ 4), and(/** @src 23:7156:7169 */ var_self_2764_address, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                    /// @src 19:3741:5165
                    mstore(add(usr$fmp, 0x24), and(value, /** @src 6:4791:17612 */ 0xffffffff00000000000000000000000000000000000000000000000000000000))
                    /// @src 19:3741:5165
                    mstore(add(usr$fmp, 0x44), 0x80)
                    mstore(add(usr$fmp, 0x64), add(0xa0, usr$encodedDataSize))
                    mstore(add(usr$fmp, 0x84), returndatasize())
                    returndatacopy(add(usr$fmp, 0xa4), /** @src -1:-1:-1 */ 0, /** @src 19:3741:5165 */ returndatasize())
                    let _4 := add(usr$fmp, usr$encodedDataSize)
                    mstore(add(_4, 0xa4), /** @src 6:4791:17612 */ 4)
                    /// @src 19:3741:5165
                    mstore(add(_4, 0xc4), /** @src 23:7185:7208 */ 0xa9e35b2f00000000000000000000000000000000000000000000000000000000)
                    /// @src 19:3741:5165
                    revert(usr$fmp, add(0xe4, usr$encodedDataSize))
                }
                /// @src 23:7280:7784
                var_result_mpos := mload(0x40)
                mstore(0x40, add(var_result_mpos, and(add(returndatasize(), 0x3f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)))
                mstore(var_result_mpos, returndatasize())
                let _5 := returndatasize()
                let _6 := add(var_result_mpos, /** @src 23:6901:7017 */ 0x20)
                /// @src 23:7280:7784
                returndatacopy(_6, /** @src -1:-1:-1 */ 0, /** @src 23:7280:7784 */ _5)
                /// @src 23:7914:7982
                let expr := /** @src 23:7914:7932 */ lt(/** @src 6:4791:17612 */ mload(/** @src 23:7914:7927 */ var_result_mpos), /** @src 23:6901:7017 */ 0x20)
                /// @src 23:7914:7982
                if iszero(expr)
                {
                    /// @src 23:7936:7958
                    let expr_1 := /** @src 28:563:648 */ mload(_6)
                    /// @src 23:7914:7982
                    expr := /** @src 23:7936:7982 */ iszero(eq(/** @src 6:4791:17612 */ and(/** @src 23:7936:7982 */ expr_1, /** @src 6:4791:17612 */ 0xffffffff00000000000000000000000000000000000000000000000000000000), and(/** @src 28:563:648 */ mload(_2), /** @src 6:4791:17612 */ 0xffffffff00000000000000000000000000000000000000000000000000000000)))
                }
                /// @src 23:7910:8050
                if expr
                {
                    /// @src 19:814:910
                    mstore(/** @src -1:-1:-1 */ 0, /** @src 23:7998:8026 */ 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(/** @src -1:-1:-1 */ 0, /** @src 19:814:910 */ 0x04)
                }
            }
            /// @ast-id 8416 @src 35:2108:3518
            function fun_flipTick(var_self_8407_slot, var_tick, var_tickSpacing)
            {
                /// @src 35:2509:3512
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
            /// @ast-id 5360 @src 29:28935:29035
            function fun_clearTick(var_self_5348_slot, var_tick)
            {
                /// @src 29:29012:29028
                let dataSlot := /** @src -1:-1:-1 */ 0
                /// @src 6:4791:17612
                mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ signextend(2, /** @src 29:29012:29028 */ var_tick))
                /// @src 6:4791:17612
                mstore(0x20, /** @src 29:29012:29022 */ add(var_self_5348_slot, 4))
                /// @src 6:4791:17612
                dataSlot := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                sstore(/** @src 29:29012:29028 */ dataSlot, /** @src 29:29005:29028 */ 0)
                /// @src 6:4791:17612
                sstore(add(/** @src 29:29012:29028 */ dataSlot, /** @src 6:4791:17612 */ 1), /** @src 29:29005:29028 */ 0)
                /// @src 6:4791:17612
                sstore(add(/** @src 29:29012:29028 */ dataSlot, /** @src 6:4791:17612 */ 2), /** @src 29:29005:29028 */ 0)
            }
            /// @ast-id 6164 @src 36:3149:7167
            function fun_getSqrtPriceAtTick(var_tick) -> var_sqrtPriceX96
            {
                /// @src 36:3297:3756
                let var_tick_1 := signextend(2, var_tick)
                let usr$mask := sar(255, var_tick_1)
                let var_absTick := xor(usr$mask, add(usr$mask, var_tick_1))
                /// @src 36:3770:3848
                if /** @src 36:3774:3809 */ gt(var_absTick, /** @src 36:1317:1323 */ 0x0d89e8)
                /// @src 36:3770:3848
                {
                    /// @src 19:1431:1574
                    mstore(0, /** @src 36:3811:3831 */ 0x8b86327a00000000000000000000000000000000000000000000000000000000)
                    /// @src 19:1431:1574
                    mstore(0x04, var_tick_1)
                    revert(0, 0x24)
                }
                /// @src 36:4356:4369
                let var_price := /** @src -1:-1:-1 */ 0
                /// @src 36:4383:4543
                var_price := xor(0x0100000000000000000000000000000000, mul(0x01fffcb933bd6fad37aa2d162d1a594001, and(var_absTick, 0x1)))
                /// @src 36:4556:4639
                if /** @src 36:4560:4578 */ iszero(iszero(/** @src 36:4560:4573 */ and(var_absTick, /** @src 36:3297:3756 */ 2)))
                /// @src 36:4556:4639
                {
                    /// @src 36:4580:4639
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:4589:4631 */ var_price, /** @src 36:4597:4631 */ 0xfff97272373d413259a46990580e213a))
                }
                /// @src 36:4653:4736
                if /** @src 36:4657:4675 */ iszero(iszero(/** @src 36:4657:4670 */ and(var_absTick, /** @src 36:4667:4670 */ 0x04)))
                /// @src 36:4653:4736
                {
                    /// @src 36:4677:4736
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:4686:4728 */ var_price, /** @src 36:4694:4728 */ 0xfff2e50f5f656932ef12357cf3c7fdcc))
                }
                /// @src 36:4750:4833
                if /** @src 36:4754:4772 */ iszero(iszero(/** @src 36:4754:4767 */ and(var_absTick, /** @src 36:4764:4767 */ 0x08)))
                /// @src 36:4750:4833
                {
                    /// @src 36:4774:4833
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:4783:4825 */ var_price, /** @src 36:4791:4825 */ 0xffe5caca7e10e4e61c3624eaa0941cd0))
                }
                /// @src 36:4847:4931
                if /** @src 36:4851:4870 */ iszero(iszero(/** @src 36:4851:4865 */ and(var_absTick, /** @src 36:4861:4865 */ 0x10)))
                /// @src 36:4847:4931
                {
                    /// @src 36:4872:4931
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:4881:4923 */ var_price, /** @src 36:4889:4923 */ 0xffcb9843d60f6159c9db58835c926644))
                }
                /// @src 36:4945:5029
                if /** @src 36:4949:4968 */ iszero(iszero(/** @src 36:4949:4963 */ and(var_absTick, /** @src 36:4959:4963 */ 0x20)))
                /// @src 36:4945:5029
                {
                    /// @src 36:4970:5029
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:4979:5021 */ var_price, /** @src 36:4987:5021 */ 0xff973b41fa98c081472e6896dfb254c0))
                }
                /// @src 36:5043:5127
                if /** @src 36:5047:5066 */ iszero(iszero(/** @src 36:5047:5061 */ and(var_absTick, /** @src 36:5057:5061 */ 0x40)))
                /// @src 36:5043:5127
                {
                    /// @src 36:5068:5127
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5077:5119 */ var_price, /** @src 36:5085:5119 */ 0xff2ea16466c96a3843ec78b326b52861))
                }
                /// @src 36:5141:5225
                if /** @src 36:5145:5164 */ iszero(iszero(/** @src 36:5145:5159 */ and(var_absTick, /** @src 36:4383:4543 */ 128)))
                /// @src 36:5141:5225
                {
                    /// @src 36:5166:5225
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5175:5217 */ var_price, /** @src 36:5183:5217 */ 0xfe5dee046a99a2a811c461f1969c3053))
                }
                /// @src 36:5239:5324
                if /** @src 36:5243:5263 */ iszero(iszero(/** @src 36:5243:5258 */ and(var_absTick, /** @src 36:5253:5258 */ 0x0100)))
                /// @src 36:5239:5324
                {
                    /// @src 36:5265:5324
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5274:5316 */ var_price, /** @src 36:5282:5316 */ 0xfcbe86c7900a88aedcffc83b479aa3a4))
                }
                /// @src 36:5338:5423
                if /** @src 36:5342:5362 */ iszero(iszero(/** @src 36:5342:5357 */ and(var_absTick, /** @src 36:5352:5357 */ 0x0200)))
                /// @src 36:5338:5423
                {
                    /// @src 36:5364:5423
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5373:5415 */ var_price, /** @src 36:5381:5415 */ 0xf987a7253ac413176f2b074cf7815e54))
                }
                /// @src 36:5437:5522
                if /** @src 36:5441:5461 */ iszero(iszero(/** @src 36:5441:5456 */ and(var_absTick, /** @src 36:5451:5456 */ 0x0400)))
                /// @src 36:5437:5522
                {
                    /// @src 36:5463:5522
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5472:5514 */ var_price, /** @src 36:5480:5514 */ 0xf3392b0822b70005940c7a398e4b70f3))
                }
                /// @src 36:5536:5621
                if /** @src 36:5540:5560 */ iszero(iszero(/** @src 36:5540:5555 */ and(var_absTick, /** @src 36:5550:5555 */ 0x0800)))
                /// @src 36:5536:5621
                {
                    /// @src 36:5562:5621
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5571:5613 */ var_price, /** @src 36:5579:5613 */ 0xe7159475a2c29b7443b29c7fa6e889d9))
                }
                /// @src 36:5635:5721
                if /** @src 36:5639:5660 */ iszero(iszero(/** @src 36:5639:5655 */ and(var_absTick, /** @src 36:5649:5655 */ 0x1000)))
                /// @src 36:5635:5721
                {
                    /// @src 36:5662:5721
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5671:5713 */ var_price, /** @src 36:5679:5713 */ 0xd097f3bdfd2022b8845ad8f792aa5825))
                }
                /// @src 36:5735:5821
                if /** @src 36:5739:5760 */ iszero(iszero(/** @src 36:5739:5755 */ and(var_absTick, /** @src 36:5749:5755 */ 0x2000)))
                /// @src 36:5735:5821
                {
                    /// @src 36:5762:5821
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5771:5813 */ var_price, /** @src 36:5779:5813 */ 0xa9f746462d870fdf8a65dc1f90e061e5))
                }
                /// @src 36:5835:5921
                if /** @src 36:5839:5860 */ iszero(iszero(/** @src 36:5839:5855 */ and(var_absTick, /** @src 36:5849:5855 */ 0x4000)))
                /// @src 36:5835:5921
                {
                    /// @src 36:5862:5921
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5871:5913 */ var_price, /** @src 36:5879:5913 */ 0x70d869a156d2a1b890bb3df62baf32f7))
                }
                /// @src 36:5935:6021
                if /** @src 36:5939:5960 */ iszero(iszero(/** @src 36:5939:5955 */ and(var_absTick, /** @src 36:5949:5955 */ 0x8000)))
                /// @src 36:5935:6021
                {
                    /// @src 36:5962:6021
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:5971:6013 */ var_price, /** @src 36:5979:6013 */ 0x31be135f97d08fd981231505542fcfa6))
                }
                /// @src 36:6035:6121
                if /** @src 36:6039:6061 */ iszero(iszero(/** @src 36:6039:6056 */ and(var_absTick, /** @src 36:6049:6056 */ 0x010000)))
                /// @src 36:6035:6121
                {
                    /// @src 36:6063:6121
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:6072:6113 */ var_price, /** @src 36:6080:6113 */ 0x09aa508b5b7a84e1c677de54f3e99bc9))
                }
                /// @src 36:6135:6220
                if /** @src 36:6139:6161 */ iszero(iszero(/** @src 36:6139:6156 */ and(var_absTick, /** @src 36:6149:6156 */ 0x020000)))
                /// @src 36:6135:6220
                {
                    /// @src 36:6163:6220
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:6172:6212 */ var_price, /** @src 36:6180:6212 */ 0x5d6af8dedb81196699c329225ee604))
                }
                /// @src 36:6234:6317
                if /** @src 36:6238:6260 */ iszero(iszero(/** @src 36:6238:6255 */ and(var_absTick, /** @src 36:6248:6255 */ 0x040000)))
                /// @src 36:6234:6317
                {
                    /// @src 36:6262:6317
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:6271:6309 */ var_price, /** @src 36:6279:6309 */ 0x2216e584f5fa1ea926041bedfe98))
                }
                /// @src 36:6331:6409
                if /** @src 36:6335:6357 */ iszero(iszero(/** @src 36:6335:6352 */ and(var_absTick, /** @src 36:6345:6352 */ 0x080000)))
                /// @src 36:6331:6409
                {
                    /// @src 36:6359:6409
                    var_price := /** @src 6:4791:17612 */ shr(/** @src 36:4383:4543 */ 128, /** @src 6:4791:17612 */ mul(/** @src 36:6368:6401 */ var_price, /** @src 36:6376:6401 */ 0x048a170391f7dc42444e8fa2))
                }
                /// @src 36:6424:7151
                if sgt(var_tick_1, /** @src -1:-1:-1 */ 0)
                /// @src 36:6424:7151
                {
                    var_price := div(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, var_price)
                }
                var_sqrtPriceX96 := shr(/** @src 36:4959:4963 */ 0x20, /** @src 36:6424:7151 */ add(var_price, 0xffffffff))
            }
            /// @ast-id 8113 @src 33:13649:14073
            function fun_getAmount1Delta(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
            {
                /// @src 33:13838:14056
                let expr := /** @src 33:13850:13851 */ 0x00
                /// @src 33:13838:14056
                switch /** @src 33:13838:13851 */ slt(/** @src 6:4791:17612 */ signextend(15, /** @src 33:13838:13851 */ var_liquidity), /** @src 33:13850:13851 */ 0x00)
                case /** @src 33:13838:14056 */ 0 {
                    /// @src 33:13974:14045
                    let _1 := fun_getAmount1Delta_40483(var_sqrtPriceAX96, var_sqrtPriceBX96, /** @src 6:4791:17612 */ and(0xffffffffffffffffffffffffffffffff, /** @src 33:13838:13851 */ var_liquidity))
                    /// @src 32:1871:1920
                    if /** @src 32:1875:1880 */ slt(_1, /** @src 33:13850:13851 */ 0x00)
                    /// @src 32:1871:1920
                    {
                        /// @src 19:814:910
                        mstore(/** @src 33:13850:13851 */ 0x00, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 33:13850:13851 */ 0x00, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 33:13838:14056
                    expr := /** @src 6:4791:17612 */ sub(/** @src 33:13850:13851 */ 0x00, /** @src 6:4791:17612 */ _1)
                }
                default /// @src 33:13838:14056
                {
                    /// @src 33:13870:13943
                    let _2 := fun_getAmount1Delta_40484(var_sqrtPriceAX96, var_sqrtPriceBX96, /** @src 6:4791:17612 */ and(0xffffffffffffffffffffffffffffffff, sub(/** @src 33:13850:13851 */ 0x00, /** @src 33:13924:13934 */ var_liquidity)))
                    /// @src 32:1871:1920
                    if /** @src 32:1875:1880 */ slt(_2, /** @src 33:13850:13851 */ 0x00)
                    /// @src 32:1871:1920
                    {
                        /// @src 19:814:910
                        mstore(/** @src 33:13850:13851 */ 0x00, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 33:13850:13851 */ 0x00, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 33:13838:14056
                    expr := _2
                }
                /// @src 33:13831:14056
                var := expr
            }
            /// @ast-id 8070 @src 33:12876:13300
            function fun_getAmount0Delta(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
            {
                /// @src 33:13065:13283
                let expr := /** @src 33:13077:13078 */ 0x00
                /// @src 33:13065:13283
                switch /** @src 33:13065:13078 */ slt(/** @src 6:4791:17612 */ signextend(15, /** @src 33:13065:13078 */ var_liquidity), /** @src 33:13077:13078 */ 0x00)
                case /** @src 33:13065:13283 */ 0 {
                    /// @src 33:13201:13272
                    let _1 := fun_getAmount0Delta_40485(var_sqrtPriceAX96, var_sqrtPriceBX96, /** @src 6:4791:17612 */ and(0xffffffffffffffffffffffffffffffff, /** @src 33:13065:13078 */ var_liquidity))
                    /// @src 32:1871:1920
                    if /** @src 32:1875:1880 */ slt(_1, /** @src 33:13077:13078 */ 0x00)
                    /// @src 32:1871:1920
                    {
                        /// @src 19:814:910
                        mstore(/** @src 33:13077:13078 */ 0x00, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 33:13077:13078 */ 0x00, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 33:13065:13283
                    expr := /** @src 6:4791:17612 */ sub(/** @src 33:13077:13078 */ 0x00, /** @src 6:4791:17612 */ _1)
                }
                default /// @src 33:13065:13283
                {
                    /// @src 33:13097:13170
                    let _2 := fun_getAmount0Delta_40486(var_sqrtPriceAX96, var_sqrtPriceBX96, /** @src 6:4791:17612 */ and(0xffffffffffffffffffffffffffffffff, sub(/** @src 33:13077:13078 */ 0x00, /** @src 33:13151:13161 */ var_liquidity)))
                    /// @src 32:1871:1920
                    if /** @src 32:1875:1880 */ slt(_2, /** @src 33:13077:13078 */ 0x00)
                    /// @src 32:1871:1920
                    {
                        /// @src 19:814:910
                        mstore(/** @src 33:13077:13078 */ 0x00, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 33:13077:13078 */ 0x00, /** @src 19:814:910 */ 0x04)
                    }
                    /// @src 33:13065:13283
                    expr := _2
                }
                /// @src 33:13058:13283
                var := expr
            }
            /// @ast-id 7622 @src 25:369:739
            function fun_addDelta(var_x, var_y) -> var_z
            {
                /// @src 25:452:733
                var_z := add(and(var_x, 0xffffffffffffffffffffffffffffffff), signextend(15, var_y))
                if shr(128, var_z)
                {
                    mstore(0, 0x93dafdf1)
                    revert(0x1c, 0x04)
                }
            }
            /// @ast-id 2858 @src 23:8196:8681
            function fun_callHookWithReturnDelta(var_self_2820_address, var_data_2822_mpos, var_parseReturn) -> var
            {
                /// @src 23:8297:8303
                var := /** @src 6:4791:17612 */ 0
                /// @src 23:8337:8357
                let expr_2834_mpos := fun_callHook(var_self_2820_address, var_data_2822_mpos)
                /// @src 23:8445:8471
                if /** @src 23:8449:8461 */ iszero(var_parseReturn)
                /// @src 23:8445:8471
                {
                    /// @src 23:8463:8471
                    var := /** @src 6:4791:17612 */ 0
                    /// @src 23:8463:8471
                    leave
                }
                /// @src 23:8566:8632
                if /** @src 23:8570:8589 */ iszero(eq(/** @src 6:4791:17612 */ mload(/** @src 23:8570:8583 */ expr_2834_mpos), /** @src 23:8587:8589 */ 0x40))
                /// @src 23:8566:8632
                {
                    /// @src 19:814:910
                    mstore(/** @src 6:4791:17612 */ 0, /** @src 23:8591:8619 */ 0x1e048e1d00000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                }
                /// @src 23:8642:8674
                var := /** @src 28:1104:1191 */ mload(add(/** @src 23:8649:8674 */ expr_2834_mpos, /** @src 23:8587:8589 */ 0x40))
            }
            /// @ast-id 6395 @src 38:1070:1466
            function fun_sub(var_a, var_b) -> var
            {
                /// @src 38:1430:1445
                let expr := fun_toInt128(/** @src 38:1183:1403 */ sub(sar(128, var_a), sar(128, var_b)))
                /// @src 38:1408:1463
                var := /** @src 38:553:668 */ or(shl(/** @src 38:1183:1403 */ 128, /** @src 38:553:668 */ expr), and(0xffffffffffffffffffffffffffffffff, /** @src 38:1447:1462 */ fun_toInt128(/** @src 38:1183:1403 */ sub(signextend(15, var_a), signextend(15, var_b)))))
            }
            /// @ast-id 6304 @src 36:7627:12379
            function fun_getTickAtSqrtPrice(var_sqrtPriceX96) -> var_tick
            {
                /// @src 36:8178:8346
                if /** @src 36:8182:8261 */ gt(/** @src 6:4791:17612 */ and(/** @src 36:1862:1872 */ add(/** @src 36:8183:8212 */ var_sqrtPriceX96, /** @src 36:1862:1872 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffd895d), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), /** @src 36:2282:2348 */ 0xfffd8963efd1fc6a506488495d951d5163961682)
                /// @src 36:8178:8346
                {
                    /// @src 19:1084:1260
                    mstore(0, /** @src 36:8281:8306 */ 0x6148752400000000000000000000000000000000000000000000000000000000)
                    /// @src 19:1084:1260
                    mstore(0x04, and(var_sqrtPriceX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                    /// @src 19:1084:1260
                    revert(0, 0x24)
                }
                /// @src 36:8418:8435
                let var_r := /** @src 6:4791:17612 */ and(shl(/** @src 36:8401:8403 */ 0x20, /** @src 36:8376:8397 */ var_sqrtPriceX96), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff00000000)
                /// @src 36:2282:2348
                let result := /** @src 36:8418:8435 */ var_r
                /// @src 6:4791:17612
                let value := and(/** @src 36:8463:8492 */ fun_mostSignificantBit(var_r), /** @src 6:4791:17612 */ 0xff)
                /// @src 36:8507:8590
                switch /** @src 36:8511:8521 */ iszero(lt(value, /** @src 36:8518:8521 */ 0x80))
                case /** @src 36:8507:8590 */ 0 {
                    /// @src 36:8566:8590
                    var_r := /** @src 6:4791:17612 */ shl(sub(/** @src 36:8580:8583 */ 0x7f, /** @src 36:8580:8589 */ value), /** @src 36:2282:2348 */ var_r)
                }
                default /// @src 36:8507:8590
                {
                    /// @src 36:8523:8547
                    var_r := /** @src 6:4791:17612 */ shr(add(/** @src 36:8537:8546 */ value, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81), /** @src 36:2282:2348 */ result)
                }
                /// @src 36:8660:8856
                let _1 := mul(var_r, var_r)
                let var_r_1 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:8660:8856 */ _1), shr(127, _1))
                /// @src 36:8869:9065
                let _2 := mul(var_r_1, var_r_1)
                let var_r_2 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:8869:9065 */ _2), shr(/** @src 36:8660:8856 */ 127, /** @src 36:8869:9065 */ _2))
                /// @src 36:9078:9274
                let _3 := mul(var_r_2, var_r_2)
                let var_r_3 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:9078:9274 */ _3), shr(/** @src 36:8660:8856 */ 127, /** @src 36:9078:9274 */ _3))
                /// @src 36:9287:9483
                let _4 := mul(var_r_3, var_r_3)
                let var_r_4 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:9287:9483 */ _4), shr(/** @src 36:8660:8856 */ 127, /** @src 36:9287:9483 */ _4))
                /// @src 36:9496:9692
                let _5 := mul(var_r_4, var_r_4)
                let var_r_5 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:9496:9692 */ _5), shr(/** @src 36:8660:8856 */ 127, /** @src 36:9496:9692 */ _5))
                /// @src 36:9705:9901
                let _6 := mul(var_r_5, var_r_5)
                let var_r_6 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:9705:9901 */ _6), shr(/** @src 36:8660:8856 */ 127, /** @src 36:9705:9901 */ _6))
                /// @src 36:9914:10110
                let _7 := mul(var_r_6, var_r_6)
                let var_r_7 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:9914:10110 */ _7), shr(/** @src 36:8660:8856 */ 127, /** @src 36:9914:10110 */ _7))
                /// @src 36:10123:10319
                let _8 := mul(var_r_7, var_r_7)
                let var_r_8 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:10123:10319 */ _8), shr(/** @src 36:8660:8856 */ 127, /** @src 36:10123:10319 */ _8))
                /// @src 36:10332:10528
                let _9 := mul(var_r_8, var_r_8)
                let var_r_9 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:10332:10528 */ _9), shr(/** @src 36:8660:8856 */ 127, /** @src 36:10332:10528 */ _9))
                /// @src 36:10541:10737
                let _10 := mul(var_r_9, var_r_9)
                let var_r_10 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:10541:10737 */ _10), shr(/** @src 36:8660:8856 */ 127, /** @src 36:10541:10737 */ _10))
                /// @src 36:10750:10946
                let _11 := mul(var_r_10, var_r_10)
                let var_r_11 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:10750:10946 */ _11), shr(/** @src 36:8660:8856 */ 127, /** @src 36:10750:10946 */ _11))
                /// @src 36:10959:11155
                let _12 := mul(var_r_11, var_r_11)
                let var_r_12 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:10959:11155 */ _12), shr(/** @src 36:8660:8856 */ 127, /** @src 36:10959:11155 */ _12))
                /// @src 36:11168:11364
                let _13 := mul(var_r_12, var_r_12)
                let var_r_13 := shr(shr(/** @src 6:4791:17612 */ 0xff, /** @src 36:11168:11364 */ _13), shr(/** @src 36:8660:8856 */ 127, /** @src 36:11168:11364 */ _13))
                /// @src 36:11579:11611
                let expr := /** @src 36:2282:2348 */ mul(/** @src 36:11377:11542 */ or(/** @src 36:11168:11364 */ or(/** @src 36:10959:11155 */ or(/** @src 36:10750:10946 */ or(/** @src 36:10541:10737 */ or(/** @src 36:10332:10528 */ or(/** @src 36:10123:10319 */ or(/** @src 36:9914:10110 */ or(/** @src 36:9705:9901 */ or(/** @src 36:9496:9692 */ or(/** @src 36:9287:9483 */ or(/** @src 36:9078:9274 */ or(/** @src 36:8869:9065 */ or(/** @src 36:8660:8856 */ or(/** @src 6:4791:17612 */ shl(/** @src 36:8643:8645 */ 0x40, /** @src 36:2282:2348 */ add(/** @src 36:8621:8638 */ value, /** @src 36:2282:2348 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff80)), /** @src 36:8660:8856 */ and(shr(192, _1), 0x8000000000000000)), /** @src 36:8869:9065 */ and(shr(193, _2), 0x4000000000000000)), /** @src 36:9078:9274 */ and(shr(194, _3), 0x2000000000000000)), /** @src 36:9287:9483 */ and(shr(195, _4), 0x1000000000000000)), /** @src 36:9496:9692 */ and(shr(196, _5), 0x0800000000000000)), /** @src 36:9705:9901 */ and(shr(197, _6), 0x0400000000000000)), /** @src 36:9914:10110 */ and(shr(198, _7), 0x0200000000000000)), /** @src 36:10123:10319 */ and(shr(199, _8), 0x0100000000000000)), /** @src 36:10332:10528 */ and(shr(200, _9), 0x80000000000000)), /** @src 36:10541:10737 */ and(shr(201, _10), 0x40000000000000)), /** @src 36:10750:10946 */ and(shr(202, _11), 0x20000000000000)), /** @src 36:10959:11155 */ and(shr(203, _12), 0x10000000000000)), /** @src 36:11168:11364 */ and(shr(204, _13), 0x08000000000000)), /** @src 36:11377:11542 */ and(shr(205, mul(var_r_13, var_r_13)), 0x04000000000000)), /** @src 36:11587:11611 */ 0x3627a301d71055774c85)
                /// @src 6:4791:17612
                let cleaned := signextend(2, /** @src 36:2282:2348 */ sar(/** @src 36:8518:8521 */ 0x80, /** @src 36:2282:2348 */ add(/** @src 36:11788:11841 */ expr, /** @src 36:2282:2348 */ 0xfffffffffffffffffffffffffffffffffd709b7e5480fba5a50fed5e62ffc556)))
                /// @src 6:4791:17612
                let cleaned_1 := signextend(2, /** @src 36:2282:2348 */ sar(/** @src 36:8518:8521 */ 0x80, /** @src 36:2282:2348 */ add(/** @src 36:12185:12240 */ expr, /** @src 36:12201:12240 */ 0xdb2df09e81959a81455e260799a0632f)))
                /// @src 36:12271:12362
                let expr_1 := /** @src -1:-1:-1 */ 0
                /// @src 36:12271:12362
                switch /** @src 36:12271:12288 */ eq(/** @src 6:4791:17612 */ cleaned, cleaned_1)
                case /** @src 36:12271:12362 */ 0 {
                    /// @src 36:12301:12343
                    let expr_2 := iszero(gt(/** @src 6:4791:17612 */ and(/** @src 36:12301:12327 */ fun_getSqrtPriceAtTick(cleaned_1), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), and(/** @src 36:8376:8397 */ var_sqrtPriceX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)))
                    /// @src 36:12301:12362
                    let expr_3 := /** @src -1:-1:-1 */ 0
                    /// @src 36:12301:12362
                    switch expr_2
                    case 0 { expr_3 := cleaned }
                    default { expr_3 := cleaned_1 }
                    /// @src 36:12271:12362
                    expr_1 := expr_3
                }
                default { expr_1 := cleaned }
                /// @src 36:12264:12362
                var_tick := expr_1
            }
            /// @ast-id 2153 @src 17:439:791
            function fun_computeSlot(var_target, var_currency) -> var_hashSlot
            {
                /// @src 17:547:785
                mstore(0, and(var_target, 0xffffffffffffffffffffffffffffffffffffffff))
                mstore(32, and(var_currency, 0xffffffffffffffffffffffffffffffffffffffff))
                var_hashSlot := keccak256(0, 64)
            }
            /// @src 31:633:642
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
            /// @ast-id 5021 @src 29:12231:21851
            function fun_swap(var_self_slot, var_params_4413_mpos) -> var_swapDelta, var_amountToProtocol, var_swapFee, var_result_4424_mpos
            {
                /// @src 29:12349:12373
                var_amountToProtocol := /** @src 6:4791:17612 */ 0
                let memPtr := mload(64)
                finalize_allocation_40320(memPtr)
                mstore(memPtr, 0)
                let _1 := add(memPtr, 32)
                mstore(_1, 0)
                let _2 := add(memPtr, 64)
                mstore(_2, 0)
                /// @src 29:12391:12415
                var_result_4424_mpos := memPtr
                /// @src 6:4791:17612
                let _3 := sload(/** @src 29:12450:12460 */ var_self_slot)
                /// @src 6:4791:17612
                let _4 := iszero(mload(/** @src 29:12488:12505 */ add(var_params_4413_mpos, /** @src 6:4791:17612 */ 64)))
                /// @src 29:12550:12652
                let expr := /** @src 6:4791:17612 */ 0
                /// @src 29:12550:12652
                switch /** @src 6:4791:17612 */ iszero(_4)
                case /** @src 29:12550:12652 */ 0 {
                    expr := /** @src 6:4791:17612 */ and(shr(196, /** @src 29:12609:12633 */ _3), /** @src 6:4791:17612 */ 4095)
                }
                default /// @src 29:12550:12652
                {
                    expr := /** @src 31:743:755 */ and(/** @src 44:1882:1999 */ shr(184, /** @src 29:12563:12587 */ _3), /** @src 31:750:755 */ 0x0fff)
                }
                /// @src 29:12780:12836
                let var_amountSpecifiedRemaining := /** @src 6:4791:17612 */ mload(/** @src 29:12814:12836 */ var_params_4413_mpos)
                /// @src 29:12929:12956
                let var_amountCalculated := /** @src 6:4791:17612 */ 0
                /// @src 29:13037:13062
                let expr_1 := /** @src 44:1502:1595 */ and(1461501637330902918203684832716283019655932542975, /** @src 29:13037:13062 */ _3)
                /// @src 6:4791:17612
                mstore(memPtr, expr_1)
                mstore(_1, /** @src 44:1682:1780 */ signextend(2, shr(160, /** @src 29:13128:13145 */ _3)))
                /// @src 6:4791:17612
                mstore(_2, and(sload(/** @src 29:13221:13235 */ add(var_self_slot, 3)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff))
                let _5 := mload(/** @src 29:13451:13471 */ add(var_params_4413_mpos, 128))
                /// @src 29:13451:13592
                let expr_2 := /** @src 6:4791:17612 */ 0
                /// @src 29:13451:13592
                switch /** @src 24:2836:2865 */ iszero(iszero(/** @src 24:2836:2860 */ and(/** @src 6:4791:17612 */ _5, /** @src 24:819:827 */ 0x400000)))
                case /** @src 29:13451:13592 */ 0 {
                    expr_2 := /** @src 44:2089:2194 */ and(/** @src 6:4791:17612 */ 0xffffff, /** @src 44:2089:2194 */ shr(208, /** @src 29:13574:13592 */ _3))
                }
                default /// @src 29:13451:13592
                {
                    /// @src 24:3537:3562
                    let expr_3 := /** @src 24:3147:3174 */ and(/** @src 6:4791:17612 */ _5, /** @src 24:975:983 */ 0xbfffff)
                    /// @src 24:3572:3584
                    fun_validate(expr_3)
                    /// @src 29:13451:13592
                    expr_2 := expr_3
                }
                /// @src 29:13617:13687
                let expr_4 := /** @src 6:4791:17612 */ 0
                /// @src 29:13617:13687
                switch /** @src 29:13617:13633 */ iszero(/** @src 6:4791:17612 */ and(/** @src 29:12516:12652 */ expr, /** @src 6:4791:17612 */ 0xffff))
                case /** @src 29:13617:13687 */ 0 {
                    /// @src 31:1864:2104
                    let var_self := and(/** @src 29:12516:12652 */ expr, /** @src 31:1864:2104 */ 0xfff)
                    let var_lpFee := and(expr_2, /** @src 6:4791:17612 */ 0xffffff)
                    /// @src 29:13617:13687
                    expr_4 := /** @src 31:1864:2104 */ sub(add(var_self, var_lpFee), div(mul(var_self, var_lpFee), 1000000))
                }
                default /// @src 29:13617:13687
                { expr_4 := expr_2 }
                /// @src 29:13607:13687
                var_swapFee := expr_4
                /// @src 29:13843:14043
                if /** @src 29:13847:13879 */ iszero(lt(/** @src 6:4791:17612 */ and(/** @src 29:13847:13879 */ expr_4, /** @src 6:4791:17612 */ 0xffffff), /** @src 34:563:566 */ 0x0f4240))
                /// @src 29:13843:14043
                {
                    /// @src 29:13925:14033
                    if /** @src 29:13929:13955 */ sgt(/** @src 6:4791:17612 */ mload(/** @src 29:13929:13951 */ var_params_4413_mpos), /** @src 6:4791:17612 */ 0)
                    /// @src 29:13925:14033
                    {
                        /// @src 19:814:910
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 29:13975:14005 */ 0x9620624600000000000000000000000000000000000000000000000000000000)
                        /// @src 19:814:910
                        revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                    }
                }
                /// @src 29:14247:14339
                if /** @src 29:14251:14278 */ iszero(/** @src 6:4791:17612 */ mload(/** @src 29:14251:14273 */ var_params_4413_mpos))
                /// @src 29:14247:14339
                {
                    /// @src 29:14280:14339
                    var_swapDelta := /** @src 6:4791:17612 */ 0
                    /// @src 29:14280:14339
                    var_amountToProtocol := /** @src 6:4791:17612 */ 0
                    /// @src 29:14280:14339
                    var_swapFee := expr_4
                    var_result_4424_mpos := memPtr
                    leave
                }
                /// @src 29:14350:15371
                switch /** @src 6:4791:17612 */ iszero(_4)
                case /** @src 29:14350:15371 */ 0 {
                    /// @src 29:15005:15029
                    let _6 := add(var_params_4413_mpos, /** @src 6:4791:17612 */ 96)
                    let cleaned := and(mload(/** @src 29:15005:15029 */ _6), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 29:15001:15191
                    if /** @src 29:15005:15058 */ iszero(gt(/** @src 6:4791:17612 */ cleaned, expr_1))
                    /// @src 29:15001:15191
                    {
                        /// @src 19:3008:3327
                        let usr$fmp := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 19:3008:3327
                        mstore(usr$fmp, /** @src 29:15078:15112 */ 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3008:3327
                        mstore(add(usr$fmp, 0x04), expr_1)
                        mstore(add(usr$fmp, 0x24), cleaned)
                        revert(usr$fmp, 0x44)
                    }
                    /// @src 6:4791:17612
                    let cleaned_1 := and(mload(/** @src 29:15208:15232 */ _6), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 29:15204:15361
                    if /** @src 29:15208:15259 */ iszero(lt(/** @src 6:4791:17612 */ cleaned_1, /** @src 36:2042:2091 */ 0xfffd8963efd1fc6a506488495d951d5263988d26))
                    /// @src 29:15204:15361
                    {
                        /// @src 19:1084:1260
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 29:15279:15309 */ 0x9e4d7cc700000000000000000000000000000000000000000000000000000000)
                        /// @src 19:1084:1260
                        mstore(0x04, cleaned_1)
                        revert(/** @src 6:4791:17612 */ 0, /** @src 19:1084:1260 */ 0x24)
                    }
                }
                default /// @src 29:14350:15371
                {
                    /// @src 29:14384:14408
                    let _7 := add(var_params_4413_mpos, /** @src 6:4791:17612 */ 96)
                    let cleaned_2 := and(mload(/** @src 29:14384:14408 */ _7), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 29:14380:14570
                    if /** @src 29:14384:14437 */ iszero(lt(/** @src 6:4791:17612 */ cleaned_2, expr_1))
                    /// @src 29:14380:14570
                    {
                        /// @src 19:3008:3327
                        let usr$fmp_1 := mload(/** @src 6:4791:17612 */ 64)
                        /// @src 19:3008:3327
                        mstore(usr$fmp_1, /** @src 29:14457:14491 */ 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000)
                        /// @src 19:3008:3327
                        mstore(add(usr$fmp_1, 0x04), expr_1)
                        mstore(add(usr$fmp_1, 0x24), cleaned_2)
                        revert(usr$fmp_1, 0x44)
                    }
                    /// @src 6:4791:17612
                    let cleaned_3 := and(mload(/** @src 29:14818:14842 */ _7), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 29:14814:14971
                    if /** @src 29:14818:14869 */ iszero(gt(/** @src 6:4791:17612 */ cleaned_3, /** @src 36:1862:1872 */ 0x01000276a3))
                    /// @src 29:14814:14971
                    {
                        /// @src 19:1084:1260
                        mstore(/** @src 6:4791:17612 */ 0, /** @src 29:14889:14919 */ 0x9e4d7cc700000000000000000000000000000000000000000000000000000000)
                        /// @src 19:1084:1260
                        mstore(0x04, cleaned_3)
                        revert(/** @src 6:4791:17612 */ 0, /** @src 19:1084:1260 */ 0x24)
                    }
                }
                /// @src 6:4791:17612
                let memPtr_1 := mload(64)
                let newFreePtr := add(memPtr_1, /** @src 36:2042:2091 */ 256)
                /// @src 6:4791:17612
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr_1))
                {
                    mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x41)
                    revert(0, 0x24)
                }
                mstore(64, newFreePtr)
                /// @src 36:2042:2091
                mstore(memPtr_1, /** @src 6:4791:17612 */ 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, /** @src 6:4791:17612 */ 32), 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, /** @src 6:4791:17612 */ 64), 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, /** @src 6:4791:17612 */ 96), 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, /** @src 29:13451:13471 */ 128), /** @src 6:4791:17612 */ 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, /** @src 44:1682:1780 */ 160), /** @src 6:4791:17612 */ 0)
                /// @src 36:2042:2091
                mstore(add(memPtr_1, 192), /** @src 6:4791:17612 */ 0)
                /// @src 29:15446:15512
                let expr_5 := /** @src 6:4791:17612 */ 0
                /// @src 29:15446:15512
                switch /** @src 6:4791:17612 */ iszero(_4)
                case /** @src 29:15446:15512 */ 0 {
                    expr_5 := /** @src 6:4791:17612 */ sload(/** @src 29:15487:15512 */ add(var_self_slot, /** @src 44:1682:1780 */ 2))
                }
                default /// @src 29:15446:15512
                {
                    expr_5 := /** @src 6:4791:17612 */ sload(/** @src 29:15459:15484 */ add(var_self_slot, 1))
                }
                /// @src 6:4791:17612
                mstore(/** @src 36:2042:2091 */ add(memPtr_1, 224), /** @src 6:4791:17612 */ expr_5)
                /// @src 29:15639:20883
                for { }
                /** @src 34:1328:2247 */ 0x1
                /// @src 29:15639:20883
                { }
                {
                    /// @src 29:15648:15728
                    let expr_6 := /** @src 29:15648:15677 */ iszero(var_amountSpecifiedRemaining)
                    /// @src 29:15648:15728
                    if iszero(expr_6)
                    {
                        /// @src 6:4791:17612
                        let cleaned_4 := and(mload(/** @src 29:15681:15700 */ var_result_4424_mpos), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                        /// @src 29:15648:15728
                        expr_6 := /** @src 29:15681:15728 */ eq(/** @src 6:4791:17612 */ cleaned_4, and(mload(/** @src 29:15704:15728 */ add(var_params_4413_mpos, /** @src 6:4791:17612 */ 96)), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975))
                    }
                    /// @src 29:15646:15729
                    if /** @src 6:4791:17612 */ iszero(/** @src 29:15646:15729 */ iszero(expr_6)) { break }
                    /// @src 6:4791:17612
                    mstore(memPtr_1, and(mload(/** @src 29:15770:15789 */ var_result_4424_mpos), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975))
                    /// @src 6:4791:17612
                    let cleaned_5 := signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 29:15905:15916 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 32)))
                    let cleaned_6 := signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 29:15918:15936 */ add(var_params_4413_mpos, /** @src 6:4791:17612 */ 32)))
                    /// @src 29:15856:15949
                    let var_next := /** @src 6:4791:17612 */ 0
                    /// @src 29:15856:15949
                    let var_initialized := /** @src 6:4791:17612 */ 0
                    /// @src 35:846:1242
                    let var_compressed := sub(sdiv(cleaned_5, cleaned_6), slt(smod(cleaned_5, cleaned_6), /** @src 6:4791:17612 */ 0))
                    /// @src 35:4565:6247
                    switch /** @src 6:4791:17612 */ iszero(_4)
                    case /** @src 35:4565:6247 */ 0 {
                        /// @src 6:4791:17612
                        let _8 := add(/** @src 35:5539:5551 */ var_compressed, /** @src 34:1328:2247 */ 0x1)
                        /// @src 35:5702:5715
                        let dataSlot := /** @src 6:4791:17612 */ 0
                        mstore(0, signextend(1, /** @src 35:1676:1846 */ sar(8, /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ _8))))
                        mstore(0x20, /** @src 29:15856:15871 */ add(var_self_slot, 5))
                        /// @src 6:4791:17612
                        dataSlot := keccak256(0, 0x40)
                        /// @src 35:5702:5722
                        let expr_7 := and(/** @src 6:4791:17612 */ sload(/** @src 35:5702:5715 */ dataSlot), /** @src 35:5647:5667 */ not(/** @src 6:4791:17612 */ add(shl(and(_8, /** @src 35:1676:1846 */ 0xff), /** @src 34:1328:2247 */ 0x1), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)))
                        /// @src 35:5869:5880
                        let _9 := iszero(expr_7)
                        /// @src 35:5855:5880
                        var_initialized := /** @src 35:5869:5880 */ iszero(_9)
                        /// @src 35:6019:6232
                        let expr_8 := /** @src 6:4791:17612 */ 0
                        /// @src 35:6019:6232
                        switch var_initialized
                        case 0 {
                            expr_8 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mul(signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ add(signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ _8), signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ and(sub(/** @src 35:1676:1846 */ 0xff, and(0xff, /** @src 6:4791:17612 */ _8)), /** @src 35:1676:1846 */ 0xff)))), /** @src 35:6164:6232 */ cleaned_6))
                        }
                        default /// @src 35:6019:6232
                        {
                            /// @src 6:4791:17612
                            if _9 { revert(0, 0) }
                            /// @src 16:1766:2600
                            let var_x := and(expr_7, sub(/** @src 6:4791:17612 */ 0, /** @src 16:1766:2600 */ expr_7))
                            let var_r := and(shr(247, shl(and(shr(248, mul(var_x, 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff)), 252), 0x8040405543005266443200005020610674053026020000107506200176117077)), 480)
                            /// @src 35:6019:6232
                            expr_8 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mul(signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ add(signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ _8), signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ and(sub(/** @src 16:1766:2600 */ or(var_r, byte(and(div(0xd76453e0, shr(var_r, var_x)), /** @src 6:4791:17612 */ 31), /** @src 16:1766:2600 */ 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405)), /** @src 35:1676:1846 */ and(0xff, /** @src 6:4791:17612 */ _8)), /** @src 35:1676:1846 */ 0xff)))), /** @src 6:4791:17612 */ cleaned_6))
                        }
                        /// @src 35:6012:6232
                        var_next := expr_8
                    }
                    default /// @src 35:4565:6247
                    {
                        /// @src 35:1676:1846
                        let var_bitPos := and(var_compressed, 0xff)
                        /// @src 35:4839:4852
                        let dataSlot_1 := /** @src -1:-1:-1 */ 0
                        /// @src 6:4791:17612
                        mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ signextend(1, /** @src 35:1676:1846 */ sar(8, signextend(/** @src 44:1682:1780 */ 2, /** @src 35:1676:1846 */ var_compressed))))
                        /// @src 6:4791:17612
                        mstore(0x20, /** @src 29:15856:15871 */ add(var_self_slot, 5))
                        /// @src 6:4791:17612
                        dataSlot_1 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                        /// @src 35:4839:4859
                        let expr_9 := and(/** @src 6:4791:17612 */ sload(/** @src 35:4839:4852 */ dataSlot_1), /** @src 6:4791:17612 */ shr(sub(/** @src 35:1676:1846 */ 0xff, /** @src 6:4791:17612 */ var_bitPos), /** @src 35:4748:4765 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
                        /// @src 35:5000:5025
                        var_initialized := /** @src 35:5014:5025 */ iszero(iszero(expr_9))
                        /// @src 35:5164:5358
                        let expr_10 := /** @src 6:4791:17612 */ 0
                        /// @src 35:5164:5358
                        switch var_initialized
                        case 0 {
                            expr_10 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mul(signextend(/** @src 44:1682:1780 */ 2, /** @src 31:633:642 */ sub(/** @src 35:5309:5343 */ var_compressed, /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ var_bitPos))), /** @src 35:5308:5358 */ cleaned_6))
                        }
                        default /// @src 35:5164:5358
                        {
                            expr_10 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mul(signextend(/** @src 44:1682:1780 */ 2, /** @src 31:633:642 */ sub(var_compressed, /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ and(sub(var_bitPos, /** @src 35:5234:5268 */ fun_mostSignificantBit(expr_9)), /** @src 35:1676:1846 */ 0xff)))), /** @src 6:4791:17612 */ cleaned_6))
                        }
                        /// @src 35:5157:5358
                        var_next := expr_10
                    }
                    /// @src 6:4791:17612
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 64), iszero(iszero(var_initialized)))
                    let _10 := signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ var_next)
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32), _10)
                    /// @src 29:16077:16183
                    if /** @src 29:16081:16115 */ iszero(sgt(_10, /** @src 36:1032:1039 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618))
                    /// @src 29:16077:16183
                    {
                        /// @src 6:4791:17612
                        mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32), /** @src 36:1032:1039 */ 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618)
                    }
                    /// @src 29:16196:16302
                    if /** @src 29:16200:16234 */ iszero(slt(/** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32))), /** @src 36:1317:1323 */ 0x0d89e8))
                    /// @src 29:16196:16302
                    {
                        /// @src 6:4791:17612
                        mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32), /** @src 36:1317:1323 */ 0x0d89e8)
                    }
                    /// @src 6:4791:17612
                    let _11 := and(/** @src 29:16387:16429 */ fun_getSqrtPriceAtTick(/** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32)))), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 6:4791:17612
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 96), _11)
                    let cleaned_7 := and(mload(/** @src 29:16676:16695 */ var_result_4424_mpos), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 6:4791:17612
                    let cleaned_8 := and(mload(/** @src 29:16776:16800 */ add(var_params_4413_mpos, /** @src 6:4791:17612 */ 96)), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 34:1328:2247
                    let var_sqrtPriceTargetX96 := xor(cleaned_8, mul(xor(_11, cleaned_8), xor(lt(_11, cleaned_8), and(/** @src 6:4791:17612 */ iszero(_4), /** @src 34:1328:2247 */ 0x1))))
                    /// @src 6:4791:17612
                    let cleaned_9 := and(mload(/** @src 29:16819:16835 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 64)), 0xffffffffffffffffffffffffffffffff)
                    /// @src 29:16634:16916
                    let var_sqrtPriceNextX96 := /** @src 6:4791:17612 */ 0
                    /// @src 29:16634:16916
                    let var_amountIn := /** @src 6:4791:17612 */ 0
                    /// @src 29:16634:16916
                    let var_amountOut := /** @src 6:4791:17612 */ 0
                    /// @src 29:16634:16916
                    let var_feeAmount := /** @src 6:4791:17612 */ 0
                    /// @src 34:3923:3964
                    let expr_11 := iszero(lt(/** @src 6:4791:17612 */ cleaned_7, and(/** @src 34:3923:3964 */ var_sqrtPriceTargetX96, /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)))
                    /// @src 34:4027:6949
                    switch /** @src 34:3993:4012 */ slt(var_amountSpecifiedRemaining, /** @src 6:4791:17612 */ 0)
                    case /** @src 34:4027:6949 */ 0 {
                        /// @src 34:5746:5978
                        let expr_12 := /** @src 6:4791:17612 */ 0
                        /// @src 34:5746:5978
                        switch expr_11
                        case 0 {
                            expr_12 := /** @src 34:5890:5978 */ fun_getAmount0Delta_40486(cleaned_7, var_sqrtPriceTargetX96, cleaned_9)
                        }
                        default /// @src 34:5746:5978
                        {
                            expr_12 := /** @src 34:5779:5867 */ fun_getAmount1Delta_40484(var_sqrtPriceTargetX96, cleaned_7, cleaned_9)
                        }
                        /// @src 34:5734:5978
                        var_amountOut := expr_12
                        /// @src 34:5996:6512
                        switch /** @src 34:6000:6037 */ iszero(lt(var_amountSpecifiedRemaining, expr_12))
                        case /** @src 34:5996:6512 */ 0 {
                            /// @src 34:6297:6333
                            var_amountOut := var_amountSpecifiedRemaining
                            /// @src 33:8211:8569
                            if or(iszero(cleaned_7), iszero(cleaned_9))
                            {
                                mstore(/** @src 6:4791:17612 */ 0, /** @src 33:8211:8569 */ 0x4f2461b8)
                                revert(0x1c, 0x04)
                            }
                            /// @src 33:8646:8840
                            let expr_13 := /** @src 6:4791:17612 */ 0
                            /// @src 33:8646:8840
                            switch expr_11
                            case 0 {
                                expr_13 := /** @src 33:8764:8840 */ fun_getNextSqrtPriceFromAmount0RoundingUp_40493(cleaned_7, cleaned_9, var_amountSpecifiedRemaining)
                            }
                            default /// @src 33:8646:8840
                            {
                                /// @src 33:8671:8749
                                let var := /** @src 6:4791:17612 */ 0
                                /// @ast-id 7843 @src 33:4438:5888
                                let var_add := /** @src 6:4791:17612 */ 0
                                /// @src 33:4597:4604
                                var := /** @src 6:4791:17612 */ 0
                                /// @src 33:4774:5882
                                var_add := /** @src 6:4791:17612 */ 0
                                /// @src 33:5152:5357
                                let expr_14 := /** @src 6:4791:17612 */ 0
                                /// @src 33:5152:5357
                                switch /** @src 33:5152:5179 */ iszero(gt(var_amountSpecifiedRemaining, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                                case /** @src 33:5152:5357 */ 0 {
                                    /// @src 6:4791:17612
                                    let _12 := and(/** @src 33:5295:5357 */ cleaned_9, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                                    /// @src 33:5295:5357
                                    let var_result := /** @src 6:4791:17612 */ 0
                                    /// @src 22:5306:5340
                                    var_result := /** @src 22:5315:5340 */ fun_mulDiv(var_amountSpecifiedRemaining, /** @src 21:335:362 */ 0x01000000000000000000000000, /** @src 22:5315:5340 */ _12)
                                    /// @src 22:5358:5383
                                    if iszero(_12)
                                    {
                                        /// @src 31:633:642
                                        mstore(/** @src 6:4791:17612 */ 0, /** @src 31:633:642 */ 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                                        mstore(4, 0x12)
                                        revert(/** @src 6:4791:17612 */ 0, /** @src 31:633:642 */ 0x24)
                                    }
                                    /// @src 22:5354:5444
                                    if /** @src 22:5358:5388 */ iszero(iszero(/** @src 22:5358:5383 */ mulmod(var_amountSpecifiedRemaining, /** @src 21:335:362 */ 0x01000000000000000000000000, /** @src 22:5358:5383 */ _12)))
                                    /// @src 22:5354:5444
                                    {
                                        /// @src 22:5416:5424
                                        var_result := /** @src 6:4791:17612 */ add(/** @src 22:5416:5424 */ var_result, /** @src 6:4791:17612 */ 1)
                                        if /** @src 22:5416:5428 */ iszero(var_result)
                                        /// @src 6:4791:17612
                                        { revert(0, 0) }
                                    }
                                    /// @src 33:5152:5357
                                    expr_14 := var_result
                                }
                                default {
                                    /// @src 36:2282:2348
                                    let result := /** @src 6:4791:17612 */ shl(/** @src 21:295:297 */ 0x60, /** @src 36:2282:2348 */ var_amountSpecifiedRemaining)
                                    /// @src 6:4791:17612
                                    let _13 := and(/** @src 33:5202:5272 */ cleaned_9, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                                    /// @src 33:5152:5357
                                    expr_14 := /** @src 37:558:644 */ add(div(result, _13), iszero(iszero(mod(result, _13))))
                                }
                                /// @src 33:5468:5745
                                let _14 := and(/** @src 33:8671:8749 */ cleaned_7, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                                /// @src 33:5468:5745
                                if iszero(gt(_14, expr_14))
                                {
                                    mstore(/** @src 6:4791:17612 */ 0, /** @src 33:5468:5745 */ 0x4323a555)
                                    revert(0x1c, 0x04)
                                }
                                /// @src 33:5822:5857
                                var := /** @src 6:4791:17612 */ and(sub(_14, /** @src 33:5837:5856 */ expr_14), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                                /// @src 33:8646:8840
                                expr_13 := var
                            }
                            /// @src 34:6355:6493
                            var_sqrtPriceNextX96 := expr_13
                        }
                        default /// @src 34:5996:6512
                        {
                            /// @src 34:6126:6163
                            var_sqrtPriceNextX96 := var_sqrtPriceTargetX96
                        }
                        /// @src 34:6540:6766
                        let expr_15 := /** @src 6:4791:17612 */ 0
                        /// @src 34:6540:6766
                        switch expr_11
                        case 0 {
                            expr_15 := /** @src 34:6681:6766 */ fun_getAmount1Delta_40483(cleaned_7, var_sqrtPriceNextX96, cleaned_9)
                        }
                        default /// @src 34:6540:6766
                        {
                            expr_15 := /** @src 34:6573:6658 */ fun_getAmount0Delta_40485(var_sqrtPriceNextX96, cleaned_7, cleaned_9)
                        }
                        /// @src 34:6529:6766
                        var_amountIn := expr_15
                        /// @src 34:6852:6934
                        var_feeAmount := /** @src 34:6864:6934 */ fun_mulDivRoundingUp(expr_15, /** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff), sub(/** @src 34:563:566 */ 0x0f4240, /** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff)))
                    }
                    default /// @src 34:4027:6949
                    {
                        /// @src 34:4154:4177
                        let expr_16 := /** @src 6:4791:17612 */ sub(/** @src 34:563:566 */ 0x0f4240, /** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff))
                        /// @src 34:4111:4192
                        let expr_17 := fun_mulDiv_40497(/** @src 6:4791:17612 */ sub(0, /** @src 34:4135:4151 */ var_amountSpecifiedRemaining), /** @src 34:4111:4192 */ expr_16)
                        /// @src 34:4221:4451
                        let expr_18 := /** @src 6:4791:17612 */ 0
                        /// @src 34:4221:4451
                        switch expr_11
                        case 0 {
                            expr_18 := /** @src 34:4364:4451 */ fun_getAmount1Delta_40483(cleaned_7, var_sqrtPriceTargetX96, cleaned_9)
                        }
                        default /// @src 34:4221:4451
                        {
                            expr_18 := /** @src 34:4254:4341 */ fun_getAmount0Delta_40485(var_sqrtPriceTargetX96, cleaned_7, cleaned_9)
                        }
                        /// @src 34:4210:4451
                        var_amountIn := expr_18
                        /// @src 34:4469:5438
                        switch /** @src 34:4473:4507 */ iszero(lt(expr_17, expr_18))
                        case /** @src 34:4469:5438 */ 0 {
                            /// @src 34:5021:5054
                            var_amountIn := expr_17
                            /// @src 33:6731:7089
                            if or(iszero(cleaned_7), iszero(cleaned_9))
                            {
                                mstore(/** @src 6:4791:17612 */ 0, /** @src 33:6731:7089 */ 0x4f2461b8)
                                revert(0x1c, 0x04)
                            }
                            /// @src 33:7172:7362
                            let expr_19 := /** @src 6:4791:17612 */ 0
                            /// @src 33:7172:7362
                            switch expr_11
                            case 0 {
                                /// @src 33:7286:7362
                                let var_1 := /** @src 6:4791:17612 */ 0
                                /// @src 33:4597:4604
                                var_1 := /** @src 6:4791:17612 */ 0
                                /// @src 33:4834:5006
                                let expr_20 := /** @src 6:4791:17612 */ 0
                                /// @src 33:4834:5006
                                switch /** @src 33:4834:4861 */ iszero(gt(expr_17, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                                case /** @src 33:4834:5006 */ 0 {
                                    expr_20 := /** @src 33:4954:5006 */ fun_mulDiv_40523(expr_17, /** @src 6:4791:17612 */ and(/** @src 33:4954:5006 */ cleaned_9, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff))
                                }
                                default /// @src 33:4834:5006
                                {
                                    expr_20 := /** @src 33:4884:4931 */ wrapping_div_uint256(/** @src 6:4791:17612 */ shl(/** @src 21:295:297 */ 0x60, /** @src 36:2282:2348 */ expr_17), /** @src 6:4791:17612 */ and(/** @src 33:4884:4931 */ cleaned_9, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff))
                                }
                                /// @src 33:5035:5084
                                var_1 := /** @src 33:5042:5084 */ fun_toUint160(/** @src 33:5043:5071 */ checked_add_uint256(/** @src 6:4791:17612 */ and(/** @src 33:7286:7362 */ cleaned_7, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), /** @src 33:5043:5071 */ expr_20))
                                /// @src 33:7172:7362
                                expr_19 := var_1
                            }
                            default {
                                expr_19 := /** @src 33:7197:7271 */ fun_getNextSqrtPriceFromAmount0RoundingUp(cleaned_7, cleaned_9, expr_17)
                            }
                            /// @src 34:5076:5248
                            var_sqrtPriceNextX96 := expr_19
                            /// @src 34:5371:5419
                            var_feeAmount := /** @src 6:4791:17612 */ sub(0, add(/** @src 34:4135:4151 */ var_amountSpecifiedRemaining, /** @src 34:5383:5419 */ expr_17))
                        }
                        default /// @src 34:4469:5438
                        {
                            /// @src 34:4595:4632
                            var_sqrtPriceNextX96 := var_sqrtPriceTargetX96
                            /// @src 34:4666:4922
                            let expr_21 := /** @src 6:4791:17612 */ 0
                            /// @src 34:4666:4922
                            switch /** @src 34:4666:4690 */ eq(/** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff), /** @src 34:563:566 */ 0x0f4240)
                            case /** @src 34:4666:4922 */ 0 {
                                expr_21 := /** @src 34:4852:4922 */ fun_mulDivRoundingUp(var_amountIn, /** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff), /** @src 34:4852:4922 */ expr_16)
                            }
                            default /// @src 34:4666:4922
                            { expr_21 := var_amountIn }
                            /// @src 34:4654:4922
                            var_feeAmount := expr_21
                        }
                        /// @src 34:5467:5695
                        let expr_22 := /** @src 6:4791:17612 */ 0
                        /// @src 34:5467:5695
                        switch expr_11
                        case 0 {
                            expr_22 := /** @src 34:5609:5695 */ fun_getAmount0Delta_40486(cleaned_7, var_sqrtPriceNextX96, cleaned_9)
                        }
                        default /// @src 34:5467:5695
                        {
                            expr_22 := /** @src 34:5500:5586 */ fun_getAmount1Delta_40484(var_sqrtPriceNextX96, cleaned_7, cleaned_9)
                        }
                        /// @src 34:5455:5695
                        var_amountOut := expr_22
                    }
                    /// @src 6:4791:17612
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, 192), /** @src 6:4791:17612 */ var_feeAmount)
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 44:1682:1780 */ 160), /** @src 6:4791:17612 */ var_amountOut)
                    mstore(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 29:13451:13471 */ 128), /** @src 6:4791:17612 */ var_amountIn)
                    mstore(var_result_4424_mpos, and(var_sqrtPriceNextX96, /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975))
                    /// @src 29:16961:17529
                    switch /** @src 29:16965:16991 */ sgt(/** @src 6:4791:17612 */ mload(/** @src 29:16965:16987 */ var_params_4413_mpos), /** @src 6:4791:17612 */ 0)
                    case /** @src 29:16961:17529 */ 0 {
                        /// @src 36:2042:2091
                        let _15 := mload(add(memPtr_1, /** @src 29:13451:13471 */ 128))
                        /// @src 20:258:293
                        let sum := add(_15, /** @src 36:2042:2091 */ mload(add(memPtr_1, 192)))
                        /// @src 32:1871:1920
                        if /** @src 32:1875:1880 */ slt(sum, /** @src 6:4791:17612 */ 0)
                        /// @src 32:1871:1920
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                        }
                        /// @src 29:17362:17433
                        var_amountSpecifiedRemaining := /** @src 20:258:293 */ add(var_amountSpecifiedRemaining, sum)
                        /// @src 36:2042:2091
                        let _16 := mload(add(memPtr_1, /** @src 44:1682:1780 */ 160))
                        /// @src 32:1871:1920
                        if /** @src 32:1875:1880 */ slt(_16, /** @src 6:4791:17612 */ 0)
                        /// @src 32:1871:1920
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                        }
                        /// @src 29:17469:17514
                        var_amountCalculated := checked_add_int256(var_amountCalculated, /** @src 29:17489:17514 */ _16)
                    }
                    default /// @src 29:16961:17529
                    {
                        /// @src 36:2042:2091
                        let _17 := mload(add(memPtr_1, /** @src 44:1682:1780 */ 160))
                        /// @src 32:1871:1920
                        if /** @src 32:1875:1880 */ slt(_17, /** @src 6:4791:17612 */ 0)
                        /// @src 32:1871:1920
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                        }
                        /// @src 29:17043:17096
                        var_amountSpecifiedRemaining := /** @src 6:4791:17612 */ sub(var_amountSpecifiedRemaining, _17)
                        /// @src 36:2042:2091
                        let _18 := mload(add(memPtr_1, /** @src 29:13451:13471 */ 128))
                        /// @src 29:17153:17183
                        let _19 := checked_add_uint256(_18, /** @src 36:2042:2091 */ mload(add(memPtr_1, 192)))
                        /// @src 32:1871:1920
                        if /** @src 32:1875:1880 */ slt(_19, /** @src 6:4791:17612 */ 0)
                        /// @src 32:1871:1920
                        {
                            /// @src 19:814:910
                            mstore(/** @src 6:4791:17612 */ 0, /** @src 32:1882:1907 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                            /// @src 19:814:910
                            revert(/** @src 6:4791:17612 */ 0, /** @src 19:814:910 */ 0x04)
                        }
                        /// @src 36:2042:2091
                        let diff := sub(var_amountCalculated, _19)
                        if and(/** @src 34:1328:2247 */ 0x1, /** @src 36:2042:2091 */ sgt(diff, var_amountCalculated))
                        {
                            /// @src 6:4791:17612
                            mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                            mstore(4, 0x11)
                            revert(0, 0x24)
                        }
                        /// @src 29:17132:17195
                        var_amountCalculated := diff
                    }
                    /// @src 29:17660:18611
                    if /** @src 29:17664:17679 */ iszero(/** @src 29:13617:13633 */ iszero(/** @src 6:4791:17612 */ and(/** @src 29:12516:12652 */ expr, /** @src 6:4791:17612 */ 0xffff)))
                    /// @src 29:17660:18611
                    {
                        /// @src 29:18159:18401
                        let expr_23 := /** @src 6:4791:17612 */ 0
                        /// @src 29:18159:18401
                        switch /** @src 29:18160:18182 */ eq(/** @src 6:4791:17612 */ and(/** @src 34:3840:3866 */ var_swapFee, /** @src 6:4791:17612 */ 0xffffff), and(/** @src 29:12516:12652 */ expr, /** @src 6:4791:17612 */ 0xffff))
                        case /** @src 29:18159:18401 */ 0 {
                            /// @src 36:2042:2091
                            let _20 := mload(add(memPtr_1, /** @src 29:13451:13471 */ 128))
                            /// @src 29:18159:18401
                            expr_23 := /** @src 31:633:642 */ div(/** @src 6:4791:17612 */ mul(/** @src 20:258:293 */ add(_20, /** @src 36:2042:2091 */ mload(add(memPtr_1, 192))), /** @src 6:4791:17612 */ and(/** @src 29:12516:12652 */ expr, /** @src 6:4791:17612 */ 0xffff)), /** @src 34:563:566 */ 0x0f4240)
                        }
                        default /// @src 29:18159:18401
                        {
                            expr_23 := /** @src 36:2042:2091 */ mload(add(memPtr_1, 192))
                        }
                        /// @src 6:4791:17612
                        mstore(/** @src 36:2042:2091 */ add(memPtr_1, 192), /** @src 6:4791:17612 */ sub(/** @src 36:2042:2091 */ mload(add(memPtr_1, 192)), /** @src 6:4791:17612 */ expr_23))
                        /// @src 29:18553:18578
                        var_amountToProtocol := /** @src 20:258:293 */ add(/** @src 29:18553:18578 */ var_amountToProtocol, expr_23)
                    }
                    /// @src 6:4791:17612
                    let cleaned_10 := and(mload(/** @src 29:16819:16835 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 64)), 0xffffffffffffffffffffffffffffffff)
                    /// @src 29:18666:19048
                    if /** @src 29:18670:18690 */ iszero(iszero(cleaned_10))
                    /// @src 29:18666:19048
                    {
                        /// @src 6:4791:17612
                        mstore(/** @src 36:2042:2091 */ add(memPtr_1, 224), /** @src 20:258:293 */ add(/** @src 36:2042:2091 */ mload(add(memPtr_1, 224)), /** @src 37:1070:1156 */ div(shl(/** @src 29:13451:13471 */ 128, /** @src 36:2042:2091 */ mload(add(memPtr_1, 192))), /** @src 37:1070:1156 */ cleaned_10)))
                    }
                    /// @src 6:4791:17612
                    let cleaned_11 := and(mload(/** @src 29:19488:19507 */ var_result_4424_mpos), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)
                    /// @src 29:19484:20873
                    switch /** @src 29:19488:19532 */ eq(/** @src 6:4791:17612 */ cleaned_11, and(mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 96)), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975))
                    case /** @src 29:19484:20873 */ 0 {
                        /// @src 29:20607:20873
                        if /** @src 29:20611:20656 */ iszero(eq(/** @src 6:4791:17612 */ cleaned_11, and(mload(/** @src 29:20634:20656 */ memPtr_1), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)))
                        /// @src 29:20607:20873
                        {
                            /// @src 6:4791:17612
                            mstore(/** @src 29:15905:15916 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 32), signextend(/** @src 44:1682:1780 */ 2, /** @src 29:20810:20858 */ fun_getTickAtSqrtPrice(/** @src 6:4791:17612 */ cleaned_11)))
                        }
                    }
                    default /// @src 29:19484:20873
                    {
                        /// @src 29:19623:20458
                        if /** @src 6:4791:17612 */ iszero(iszero(mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 64))))
                        /// @src 29:19623:20458
                        {
                            /// @src 29:19730:19900
                            let expr_4864_component := /** @src 6:4791:17612 */ 0
                            let expr_component := 0
                            /// @src 29:19730:19900
                            switch /** @src 6:4791:17612 */ iszero(_4)
                            case /** @src 29:19730:19900 */ 0 {
                                /// @src 6:4791:17612
                                let _21 := sload(/** @src 29:19848:19873 */ add(var_self_slot, /** @src 34:1328:2247 */ 0x1))
                                /// @src 36:2042:2091
                                let _22 := mload(add(memPtr_1, 224))
                                /// @src 29:19730:19900
                                expr_4864_component := _21
                                expr_component := _22
                            }
                            default {
                                /// @src 36:2042:2091
                                let _23 := mload(add(memPtr_1, 224))
                                /// @src 6:4791:17612
                                let _24 := sload(/** @src 29:19794:19819 */ add(var_self_slot, /** @src 44:1682:1780 */ 2))
                                /// @src 29:19730:19900
                                expr_4864_component := _23
                                expr_component := _24
                            }
                            /// @src 6:4791:17612
                            let cleaned_12 := signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32)))
                            /// @src 29:29769:29785
                            let dataSlot_2 := /** @src -1:-1:-1 */ 0
                            /// @src 6:4791:17612
                            mstore(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ signextend(2, /** @src 29:29769:29785 */ cleaned_12))
                            /// @src 6:4791:17612
                            mstore(0x20, /** @src 29:29769:29779 */ add(var_self_slot, 4))
                            /// @src 6:4791:17612
                            dataSlot_2 := keccak256(/** @src -1:-1:-1 */ 0, /** @src 6:4791:17612 */ 0x40)
                            /// @src 29:29851:29877
                            let _25 := add(dataSlot_2, /** @src 34:1328:2247 */ 0x1)
                            /// @src 6:4791:17612
                            sstore(_25, sub(expr_4864_component, sload(/** @src 29:29851:29877 */ _25)))
                            /// @src 29:29943:29969
                            let _26 := add(dataSlot_2, /** @src 44:1682:1780 */ 2)
                            /// @src 6:4791:17612
                            sstore(_26, sub(expr_component, sload(/** @src 29:29943:29969 */ _26)))
                            /// @src 29:19922:20047
                            let var_liquidityNet := /** @src 6:4791:17612 */ sar(/** @src 29:13451:13471 */ 128, /** @src 6:4791:17612 */ sload(/** @src 29:29998:30015 */ dataSlot_2))
                            /// @src 29:20277:20321
                            if /** @src 6:4791:17612 */ iszero(_4)
                            /// @src 29:20277:20321
                            {
                                /// @src 29:20293:20321
                                var_liquidityNet := /** @src 6:4791:17612 */ signextend(15, sub(0, /** @src 29:20308:20321 */ var_liquidityNet))
                            }
                            /// @src 6:4791:17612
                            mstore(/** @src 29:16819:16835 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 64), and(/** @src 29:20385:20439 */ fun_addDelta(/** @src 6:4791:17612 */ and(mload(/** @src 29:16819:16835 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 64)), 0xffffffffffffffffffffffffffffffff), /** @src 29:20385:20439 */ var_liquidityNet), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff))
                        }
                        /// @src 29:20522:20568
                        let expr_24 := /** @src 6:4791:17612 */ 0
                        /// @src 29:20522:20568
                        switch /** @src 6:4791:17612 */ iszero(_4)
                        case /** @src 29:20522:20568 */ 0 {
                            expr_24 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32)))
                        }
                        default /// @src 29:20522:20568
                        {
                            expr_24 := /** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 31:633:642 */ add(/** @src 6:4791:17612 */ signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ mload(/** @src 36:2042:2091 */ add(memPtr_1, /** @src 6:4791:17612 */ 32))), /** @src 31:633:642 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))
                        }
                        /// @src 6:4791:17612
                        mstore(/** @src 29:15905:15916 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 32), signextend(/** @src 44:1682:1780 */ 2, /** @src 6:4791:17612 */ expr_24))
                    }
                }
                /// @src 44:2578:2735
                let _27 := and(0xffffff0000000000000000000000000000000000000000, shl(/** @src 44:1682:1780 */ 160, /** @src 6:4791:17612 */ mload(/** @src 29:20925:20936 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 32))))
                sstore(var_self_slot, /** @src 44:2342:2473 */ or(or(_27, and(/** @src 44:2578:2735 */ _3, /** @src 44:2342:2473 */ 0xffffffffffffffffff0000000000000000000000000000000000000000000000)), /** @src 6:4791:17612 */ and(mload(/** @src 29:20954:20973 */ var_result_4424_mpos), /** @src 44:1502:1595 */ 1461501637330902918203684832716283019655932542975)))
                /// @src 6:4791:17612
                let cleaned_13 := and(sload(/** @src 29:13221:13235 */ add(var_self_slot, 3)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                let cleaned_14 := and(mload(/** @src 29:21049:21065 */ add(var_result_4424_mpos, /** @src 6:4791:17612 */ 64)), 0xffffffffffffffffffffffffffffffff)
                /// @src 29:21027:21100
                if /** @src 29:21031:21065 */ iszero(eq(/** @src 6:4791:17612 */ cleaned_13, /** @src 29:21031:21065 */ cleaned_14))
                /// @src 29:21027:21100
                {
                    /// @src 6:4791:17612
                    sstore(/** @src 29:13221:13235 */ add(var_self_slot, 3), /** @src 6:4791:17612 */ or(and(sload(/** @src 29:13221:13235 */ add(var_self_slot, 3)), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(cleaned_14, 0xffffffffffffffffffffffffffffffff)))
                }
                /// @src 29:21147:21324
                switch /** @src 6:4791:17612 */ _4
                case /** @src 29:21147:21324 */ 0 {
                    /// @src 6:4791:17612
                    sstore(/** @src 29:21261:21286 */ add(var_self_slot, /** @src 34:1328:2247 */ 0x1), /** @src 36:2042:2091 */ mload(add(memPtr_1, 224)))
                }
                default /// @src 29:21147:21324
                {
                    /// @src 6:4791:17612
                    sstore(/** @src 29:21178:21203 */ add(var_self_slot, /** @src 44:1682:1780 */ 2), /** @src 36:2042:2091 */ mload(add(memPtr_1, 224)))
                }
                /// @src 6:4791:17612
                let _28 := mload(/** @src 29:21420:21442 */ var_params_4413_mpos)
                /// @src 29:21401:21835
                switch /** @src 29:21405:21447 */ iszero(eq(/** @src 6:4791:17612 */ iszero(_4), /** @src 29:21420:21446 */ slt(_28, /** @src 6:4791:17612 */ 0)))
                case /** @src 29:21401:21835 */ 0 {
                    /// @src 29:21711:21773
                    let expr_25 := fun_toInt128(/** @src 6:4791:17612 */ sub(_28, var_amountSpecifiedRemaining))
                    /// @src 29:21663:21820
                    var_swapDelta := /** @src 38:553:668 */ or(shl(/** @src 29:13451:13471 */ 128, /** @src 38:553:668 */ expr_25), and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:21775:21802 */ fun_toInt128(var_amountCalculated)))
                }
                default /// @src 29:21401:21835
                {
                    /// @src 29:21515:21542
                    let expr_26 := fun_toInt128(var_amountCalculated)
                    /// @src 29:21467:21624
                    var_swapDelta := /** @src 38:553:668 */ or(shl(/** @src 29:13451:13471 */ 128, /** @src 38:553:668 */ expr_26), and(/** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff, /** @src 29:21544:21606 */ fun_toInt128(/** @src 6:4791:17612 */ sub(mload(/** @src 29:21545:21567 */ var_params_4413_mpos), /** @src 6:4791:17612 */ var_amountSpecifiedRemaining))))
                }
            }
            /// @ast-id 8874 @src 22:741:4882
            function fun_mulDiv_40301(var_a, var_b) -> var_result
            {
                /// @src 22:823:837
                var_result := /** @src 6:4791:17612 */ 0
                /// @src 22:1212:1217
                let expr := /** @src 6:4791:17612 */ mul(/** @src 22:1212:1217 */ var_a, var_b)
                /// @src 22:1347:1494
                let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                let _1 := lt(usr$mm, expr)
                let _2 := sub(usr$mm, expr)
                let var_prod1 := sub(_2, _1)
                /// @src 6:4791:17612
                if iszero(/** @src 22:1619:1638 */ gt(/** @src 20:258:293 */ 0x0100000000000000000000000000000000, /** @src 22:1619:1638 */ var_prod1))
                /// @src 6:4791:17612
                { revert(0, 0) }
                /// @src 22:1716:1893
                if /** @src 22:1720:1730 */ eq(/** @src 22:1347:1494 */ _2, _1)
                /// @src 22:1716:1893
                {
                    /// @src 22:1865:1878
                    var_result := /** @src 22:1750:1848 */ shr(128, expr)
                    /// @src 22:1865:1878
                    leave
                }
                /// @src 22:2224:2319
                let var_remainder := mulmod(var_a, var_b, /** @src 20:258:293 */ 0x0100000000000000000000000000000000)
                /// @src 22:4852:4865
                var_result := /** @src 22:3363:3384 */ or(/** @src 22:2977:3059 */ shr(128, /** @src 22:2391:2536 */ sub(expr, var_remainder)), /** @src 6:4791:17612 */ shl(/** @src 22:2977:3059 */ 128, /** @src 22:2391:2536 */ sub(var_prod1, gt(var_remainder, expr))))
            }
            /// @ast-id 8874 @src 22:741:4882
            function fun_mulDiv_40497(var_a, var_b) -> var_result
            {
                /// @src 22:823:837
                var_result := /** @src 6:4791:17612 */ 0
                /// @src 22:1212:1217
                let expr := /** @src 6:4791:17612 */ mul(/** @src 22:1212:1217 */ var_a, var_b)
                /// @src 22:1347:1494
                let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                let _1 := lt(usr$mm, expr)
                let _2 := sub(usr$mm, expr)
                let var_prod1 := sub(_2, _1)
                /// @src 6:4791:17612
                if iszero(/** @src 22:1619:1638 */ gt(/** @src 34:563:566 */ 0x0f4240, /** @src 22:1619:1638 */ var_prod1))
                /// @src 6:4791:17612
                { revert(0, 0) }
                /// @src 22:1716:1893
                if /** @src 22:1720:1730 */ eq(/** @src 22:1347:1494 */ _2, _1)
                /// @src 22:1716:1893
                {
                    /// @src 22:1865:1878
                    var_result := /** @src 22:1750:1848 */ div(expr, /** @src 34:563:566 */ 0x0f4240)
                    /// @src 22:1865:1878
                    leave
                }
                /// @src 22:2224:2319
                let var_remainder := mulmod(var_a, var_b, /** @src 34:563:566 */ 0x0f4240)
                /// @src 22:4852:4865
                var_result := /** @src 6:4791:17612 */ mul(/** @src 22:3363:3384 */ or(/** @src 22:2977:3059 */ shr(6, /** @src 22:2391:2536 */ sub(expr, var_remainder)), /** @src 6:4791:17612 */ shl(250, /** @src 22:2391:2536 */ sub(var_prod1, gt(var_remainder, expr)))), /** @src 6:4791:17612 */ 0xde8f6cefed634549b62c77574f722e1ac57e23f24d8fd5cb790fb65668c26139)
            }
            /// @ast-id 8874 @src 22:741:4882
            function fun_mulDiv_40504(var_a, var_b) -> var_result
            {
                /// @src 22:823:837
                var_result := /** @src 6:4791:17612 */ 0
                /// @src 22:1212:1217
                let expr := /** @src 6:4791:17612 */ mul(/** @src 22:1212:1217 */ var_a, var_b)
                /// @src 22:1347:1494
                let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                let _1 := lt(usr$mm, expr)
                let _2 := sub(usr$mm, expr)
                let var_prod1 := sub(_2, _1)
                /// @src 6:4791:17612
                if iszero(/** @src 22:1619:1638 */ gt(/** @src 21:335:362 */ 0x01000000000000000000000000, /** @src 22:1619:1638 */ var_prod1))
                /// @src 6:4791:17612
                { revert(0, 0) }
                /// @src 22:1716:1893
                if /** @src 22:1720:1730 */ eq(/** @src 22:1347:1494 */ _2, _1)
                /// @src 22:1716:1893
                {
                    /// @src 22:1865:1878
                    var_result := /** @src 22:1750:1848 */ shr(96, expr)
                    /// @src 22:1865:1878
                    leave
                }
                /// @src 22:2224:2319
                let var_remainder := mulmod(var_a, var_b, /** @src 21:335:362 */ 0x01000000000000000000000000)
                /// @src 22:4852:4865
                var_result := /** @src 22:3363:3384 */ or(/** @src 22:2977:3059 */ shr(96, /** @src 22:2391:2536 */ sub(expr, var_remainder)), /** @src 6:4791:17612 */ shl(160, /** @src 22:2391:2536 */ sub(var_prod1, gt(var_remainder, expr))))
            }
            /// @ast-id 8874 @src 22:741:4882
            function fun_mulDiv_40523(var_a, var_denominator) -> var_result
            {
                /// @src 22:823:837
                var_result := /** @src 6:4791:17612 */ 0
                /// @src 22:1212:1217
                let expr := /** @src 6:4791:17612 */ shl(96, /** @src 22:1212:1217 */ var_a)
                /// @src 22:1347:1494
                let usr$mm := mulmod(var_a, /** @src 21:335:362 */ 0x01000000000000000000000000, /** @src 22:1347:1494 */ 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                let _1 := lt(usr$mm, expr)
                let _2 := sub(usr$mm, expr)
                let var_prod1 := sub(_2, _1)
                /// @src 6:4791:17612
                if iszero(/** @src 22:1619:1638 */ gt(var_denominator, var_prod1))
                /// @src 6:4791:17612
                { revert(0, 0) }
                /// @src 22:1716:1893
                if /** @src 22:1720:1730 */ eq(/** @src 22:1347:1494 */ _2, _1)
                /// @src 22:1716:1893
                {
                    /// @src 22:1865:1878
                    var_result := /** @src 22:1750:1848 */ div(expr, var_denominator)
                    /// @src 22:1865:1878
                    leave
                }
                /// @src 22:2224:2319
                let var_remainder := mulmod(var_a, /** @src 21:335:362 */ 0x01000000000000000000000000, /** @src 22:2224:2319 */ var_denominator)
                /// @src 22:2716:2747
                let expr_1 := and(/** @src 6:4791:17612 */ sub(0, /** @src 22:2717:2732 */ var_denominator), /** @src 22:2716:2747 */ var_denominator)
                /// @src 22:2811:2905
                let var_denominator_1 := div(var_denominator, expr_1)
                /// @src 22:3756:3777
                let expr_2 := xor(/** @src 6:4791:17612 */ mul(/** @src 22:3757:3758 */ 0x03, /** @src 22:3757:3772 */ var_denominator_1), /** @src 22:3776:3777 */ 0x02)
                /// @src 22:4008:4036
                let expr_3 := /** @src 6:4791:17612 */ mul(/** @src 22:4008:4036 */ expr_2, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4019:4036 */ var_denominator_1, expr_2)))
                /// @src 22:4070:4098
                let expr_4 := /** @src 6:4791:17612 */ mul(/** @src 22:4070:4098 */ expr_3, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4081:4098 */ var_denominator_1, expr_3)))
                /// @src 22:4133:4161
                let expr_5 := /** @src 6:4791:17612 */ mul(/** @src 22:4133:4161 */ expr_4, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4144:4161 */ var_denominator_1, expr_4)))
                /// @src 22:4196:4224
                let expr_6 := /** @src 6:4791:17612 */ mul(/** @src 22:4196:4224 */ expr_5, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4207:4224 */ var_denominator_1, expr_5)))
                /// @src 22:4259:4287
                let expr_7 := /** @src 6:4791:17612 */ mul(/** @src 22:4259:4287 */ expr_6, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4270:4287 */ var_denominator_1, expr_6)))
                /// @src 22:4852:4865
                var_result := /** @src 6:4791:17612 */ mul(/** @src 22:3363:3384 */ or(/** @src 22:2977:3059 */ div(/** @src 22:2391:2536 */ sub(expr, var_remainder), /** @src 22:2977:3059 */ expr_1), /** @src 6:4791:17612 */ mul(/** @src 22:2391:2536 */ sub(var_prod1, gt(var_remainder, expr)), /** @src 22:3254:3350 */ add(div(sub(/** @src 6:4791:17612 */ 0, /** @src 22:3254:3350 */ expr_1), expr_1), 1))), /** @src 6:4791:17612 */ mul(/** @src 22:4323:4351 */ expr_7, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4334:4351 */ var_denominator_1, expr_7))))
            }
            /// @ast-id 8874 @src 22:741:4882
            function fun_mulDiv(var_a, var_b, var_denominator) -> var_result
            {
                /// @src 22:823:837
                var_result := /** @src 6:4791:17612 */ 0
                /// @src 22:1212:1217
                let expr := /** @src 6:4791:17612 */ mul(/** @src 22:1212:1217 */ var_a, var_b)
                /// @src 22:1347:1494
                let usr$mm := mulmod(var_a, var_b, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                let _1 := lt(usr$mm, expr)
                let _2 := sub(usr$mm, expr)
                let var_prod1 := sub(_2, _1)
                /// @src 6:4791:17612
                if iszero(/** @src 22:1619:1638 */ gt(var_denominator, var_prod1))
                /// @src 6:4791:17612
                { revert(0, 0) }
                /// @src 22:1716:1893
                if /** @src 22:1720:1730 */ eq(/** @src 22:1347:1494 */ _2, _1)
                /// @src 22:1716:1893
                {
                    /// @src 22:1865:1878
                    var_result := /** @src 22:1750:1848 */ div(expr, var_denominator)
                    /// @src 22:1865:1878
                    leave
                }
                /// @src 22:2224:2319
                let var_remainder := mulmod(var_a, var_b, var_denominator)
                /// @src 22:2716:2747
                let expr_1 := and(/** @src 6:4791:17612 */ sub(0, /** @src 22:2717:2732 */ var_denominator), /** @src 22:2716:2747 */ var_denominator)
                /// @src 22:2811:2905
                let var_denominator_1 := div(var_denominator, expr_1)
                /// @src 22:3756:3777
                let expr_2 := xor(/** @src 6:4791:17612 */ mul(/** @src 22:3757:3758 */ 0x03, /** @src 22:3757:3772 */ var_denominator_1), /** @src 22:3776:3777 */ 0x02)
                /// @src 22:4008:4036
                let expr_3 := /** @src 6:4791:17612 */ mul(/** @src 22:4008:4036 */ expr_2, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4019:4036 */ var_denominator_1, expr_2)))
                /// @src 22:4070:4098
                let expr_4 := /** @src 6:4791:17612 */ mul(/** @src 22:4070:4098 */ expr_3, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4081:4098 */ var_denominator_1, expr_3)))
                /// @src 22:4133:4161
                let expr_5 := /** @src 6:4791:17612 */ mul(/** @src 22:4133:4161 */ expr_4, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4144:4161 */ var_denominator_1, expr_4)))
                /// @src 22:4196:4224
                let expr_6 := /** @src 6:4791:17612 */ mul(/** @src 22:4196:4224 */ expr_5, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4207:4224 */ var_denominator_1, expr_5)))
                /// @src 22:4259:4287
                let expr_7 := /** @src 6:4791:17612 */ mul(/** @src 22:4259:4287 */ expr_6, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4270:4287 */ var_denominator_1, expr_6)))
                /// @src 22:4852:4865
                var_result := /** @src 6:4791:17612 */ mul(/** @src 22:3363:3384 */ or(/** @src 22:2977:3059 */ div(/** @src 22:2391:2536 */ sub(expr, var_remainder), /** @src 22:2977:3059 */ expr_1), /** @src 6:4791:17612 */ mul(/** @src 22:2391:2536 */ sub(var_prod1, gt(var_remainder, expr)), /** @src 22:3254:3350 */ add(div(sub(/** @src 6:4791:17612 */ 0, /** @src 22:3254:3350 */ expr_1), expr_1), 1))), /** @src 6:4791:17612 */ mul(/** @src 22:4323:4351 */ expr_7, /** @src 6:4791:17612 */ sub(/** @src 22:3776:3777 */ 0x02, /** @src 6:4791:17612 */ mul(/** @src 22:4334:4351 */ var_denominator_1, expr_7))))
            }
            /// @ast-id 8027 @src 33:11589:12527
            function fun_getAmount1Delta_40483(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var_amount1
            {
                /// @src 33:10595:11125
                let usr$diff := sub(and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and(var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
                let usr$mask := sar(255, usr$diff)
                let var_res := xor(usr$mask, add(usr$mask, usr$diff))
                /// @src 33:11907:11925
                let expr := /** @src 6:4791:17612 */ and(/** @src 33:11907:11925 */ var_liquidity, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff)
                /// @src 33:12323:12374
                let expr_1 := fun_mulDiv_40504(expr, var_res)
                /// @src 33:12384:12521
                var_amount1 := add(expr_1, and(iszero(iszero(mulmod(expr, var_res, /** @src 21:335:362 */ 0x01000000000000000000000000))), /** @src 33:14040:14044 */ 0x01))
            }
            /// @ast-id 8027 @src 33:11589:12527
            function fun_getAmount1Delta_40484(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var_amount1
            {
                /// @src 33:10595:11125
                let usr$diff := sub(and(var_sqrtPriceAX96, 0xffffffffffffffffffffffffffffffffffffffff), and(var_sqrtPriceBX96, 0xffffffffffffffffffffffffffffffffffffffff))
                let usr$mask := sar(255, usr$diff)
                /// @src 33:12384:12521
                var_amount1 := /** @src 33:12323:12374 */ fun_mulDiv_40504(/** @src 6:4791:17612 */ and(/** @src 33:11907:11925 */ var_liquidity, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff), /** @src 33:10595:11125 */ xor(usr$mask, add(usr$mask, usr$diff)))
            }
            /// @ast-id 7971 @src 33:9398:10448
            function fun_getAmount0Delta_40485(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
            {
                /// @src 33:9596:9694
                if /** @src 33:9600:9629 */ gt(/** @src 6:4791:17612 */ and(/** @src 33:9600:9629 */ var_sqrtPriceAX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), and(/** @src 33:9600:9629 */ var_sqrtPriceBX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 33:9596:9694
                {
                    /// @src 33:9664:9694
                    let expr_component := var_sqrtPriceBX96
                    /// @src 33:9631:9694
                    var_sqrtPriceBX96 := var_sqrtPriceAX96
                    var_sqrtPriceAX96 := expr_component
                }
                /// @src 33:9783:10045
                let _1 := and(var_sqrtPriceAX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 33:9783:10045
                if iszero(_1)
                {
                    mstore(0, 0x00bfc921)
                    revert(0x1c, 0x04)
                }
                /// @src 33:10211:10431
                let expr := /** @src -1:-1:-1 */ 0
                /// @src 33:10262:10326
                let expr_1 := fun_mulDivRoundingUp(/** @src 6:4791:17612 */ and(shl(/** @src 21:295:297 */ 0x60, /** @src 33:10080:10098 */ var_liquidity), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff000000000000000000000000), and(/** @src 36:1862:1872 */ sub(/** @src 33:10160:10189 */ var_sqrtPriceBX96, var_sqrtPriceAX96), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), and(/** @src 33:10262:10326 */ var_sqrtPriceBX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 33:10211:10431
                expr := /** @src 37:558:644 */ add(div(expr_1, _1), iszero(iszero(mod(expr_1, _1))))
                /// @src 33:10204:10431
                var := expr
            }
            /// @ast-id 7971 @src 33:9398:10448
            function fun_getAmount0Delta_40486(var_sqrtPriceAX96, var_sqrtPriceBX96, var_liquidity) -> var
            {
                /// @ast-id 7971
                let var_roundUp := /** @src 33:13077:13078 */ 0x00
                /// @src 33:9596:9694
                if /** @src 33:9600:9629 */ gt(/** @src 6:4791:17612 */ and(/** @src 33:9600:9629 */ var_sqrtPriceAX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), and(/** @src 33:9600:9629 */ var_sqrtPriceBX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff))
                /// @src 33:9596:9694
                {
                    /// @src 33:9664:9694
                    let expr_component := var_sqrtPriceBX96
                    /// @src 33:9631:9694
                    var_sqrtPriceBX96 := var_sqrtPriceAX96
                    var_sqrtPriceAX96 := expr_component
                }
                /// @src 33:9783:10045
                let _1 := and(var_sqrtPriceAX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 33:9783:10045
                if iszero(_1)
                {
                    mstore(/** @src 33:13077:13078 */ 0x00, /** @src 33:9783:10045 */ 0x00bfc921)
                    revert(0x1c, 0x04)
                }
                /// @src 33:10211:10431
                let expr := /** @src 33:13077:13078 */ 0x00
                /// @src 33:10211:10431
                var_roundUp := /** @src 33:13077:13078 */ 0x00
                /// @src 33:10211:10431
                expr := /** @src 33:10361:10431 */ wrapping_div_uint256(/** @src 33:10361:10415 */ fun_mulDiv(/** @src 6:4791:17612 */ and(shl(/** @src 21:295:297 */ 0x60, /** @src 33:10080:10098 */ var_liquidity), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff000000000000000000000000), and(/** @src 36:1862:1872 */ sub(/** @src 33:10160:10189 */ var_sqrtPriceBX96, var_sqrtPriceAX96), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff), and(/** @src 33:10361:10415 */ var_sqrtPriceBX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)), _1)
                /// @src 33:10204:10431
                var := expr
            }
            /// @ast-id 8932 @src 16:653:1317
            function fun_mostSignificantBit(var_x) -> var_r
            {
                /// @src 6:4791:17612
                if /** @src 16:742:747 */ iszero(var_x)
                /// @src 6:4791:17612
                {
                    revert(/** @src 16:746:747 */ 0x00, 0x00)
                }
                /// @src 16:759:1311
                let var_r_1 := shl(7, lt(0xffffffffffffffffffffffffffffffff, var_x))
                let var_r_2 := or(var_r_1, shl(6, lt(0xffffffffffffffff, shr(var_r_1, var_x))))
                let var_r_3 := or(var_r_2, shl(5, lt(0xffffffff, shr(var_r_2, var_x))))
                let var_r_4 := or(var_r_3, shl(4, lt(0xffff, shr(var_r_3, var_x))))
                let var_r_5 := or(var_r_4, shl(3, lt(0xff, shr(var_r_4, var_x))))
                var_r := or(var_r_5, byte(and(0x1f, shr(shr(var_r_5, var_x), 0x8421084210842108cc6318c6db6d54be)), 0x0706060506020500060203020504000106050205030304010505030400000000))
            }
            /// @ast-id 8912 @src 22:5164:5460
            function fun_mulDivRoundingUp(var_a, var_b, var_denominator) -> var_result
            {
                /// @src 22:5306:5340
                var_result := /** @src 22:5315:5340 */ fun_mulDiv(var_a, var_b, var_denominator)
                /// @src 22:5358:5383
                if iszero(var_denominator)
                {
                    /// @src 31:633:642
                    mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                    mstore(4, 0x12)
                    revert(0, 0x24)
                }
                /// @src 22:5354:5444
                if /** @src 22:5358:5388 */ iszero(iszero(/** @src 22:5358:5383 */ mulmod(var_a, var_b, var_denominator)))
                /// @src 22:5354:5444
                {
                    /// @src 22:5416:5424
                    var_result := /** @src 6:4791:17612 */ add(/** @src 22:5416:5424 */ var_result, /** @src 6:4791:17612 */ 1)
                    if /** @src 22:5416:5428 */ iszero(var_result)
                    /// @src 6:4791:17612
                    {
                        revert(/** @src 22:5387:5388 */ 0x00, 0x00)
                    }
                }
            }
            /// @ast-id 7752 @src 33:1535:3600
            function fun_getNextSqrtPriceFromAmount0RoundingUp_40493(var_sqrtPX96, var_liquidity, var_amount) -> var
            {
                /// @ast-id 7752
                let var_add := /** @src 6:4791:17612 */ 0
                /// @src 33:1692:1699
                var := /** @src 6:4791:17612 */ 0
                /// @src 33:1827:1859
                if /** @src 33:1831:1842 */ iszero(var_amount)
                /// @src 33:1827:1859
                {
                    /// @src 33:1844:1859
                    var := var_sqrtPX96
                    leave
                }
                /// @src 36:2282:2348
                let result := /** @src 6:4791:17612 */ and(shl(/** @src 21:295:297 */ 0x60, /** @src 33:1890:1908 */ var_liquidity), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff000000000000000000000000)
                /// @src 33:1946:3594
                var_add := /** @src 6:4791:17612 */ 0
                /// @src 33:2636:2653
                let _1 := /** @src 6:4791:17612 */ and(/** @src 33:2636:2653 */ var_sqrtPX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 33:2636:2653
                let expr := /** @src 6:4791:17612 */ mul(/** @src 33:2636:2653 */ var_amount, _1)
                /// @src 33:2951:3413
                if iszero(and(eq(div(expr, var_amount), _1), gt(result, expr)))
                {
                    mstore(/** @src 33:1946:3594 */ 0, /** @src 33:2951:3413 */ 0xf5c787f1)
                    revert(0x1c, 0x04)
                }
                /// @src 33:3490:3569
                var := /** @src 33:3497:3569 */ fun_toUint160(/** @src 33:3497:3557 */ fun_mulDivRoundingUp(result, _1, /** @src 6:4791:17612 */ sub(/** @src 33:3452:3472 */ result, expr)))
            }
            /// @ast-id 7752 @src 33:1535:3600
            function fun_getNextSqrtPriceFromAmount0RoundingUp(var_sqrtPX96, var_liquidity, var_amount) -> var
            {
                /// @src 33:1692:1699
                var := /** @src 6:4791:17612 */ 0
                /// @src 33:1827:1859
                if /** @src 33:1831:1842 */ iszero(var_amount)
                /// @src 33:1827:1859
                {
                    /// @src 33:1844:1859
                    var := var_sqrtPX96
                    leave
                }
                /// @src 36:2282:2348
                let result := /** @src 6:4791:17612 */ and(shl(/** @src 21:295:297 */ 0x60, /** @src 33:1890:1908 */ var_liquidity), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffff000000000000000000000000)
                /// @src 33:2015:2032
                let _1 := /** @src 6:4791:17612 */ and(/** @src 33:2015:2032 */ var_sqrtPX96, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 33:2015:2032
                let expr := /** @src 6:4791:17612 */ mul(/** @src 33:2015:2032 */ var_amount, _1)
                /// @src 33:2050:2395
                if /** @src 33:2054:2082 */ eq(/** @src 33:2054:2070 */ wrapping_div_uint256(expr, var_amount), /** @src 33:2054:2082 */ _1)
                /// @src 33:2050:2395
                {
                    /// @src 33:2128:2148
                    let expr_1 := /** @src 20:258:293 */ add(/** @src 33:2128:2148 */ result, expr)
                    /// @src 33:2170:2377
                    if /** @src 33:2174:2199 */ iszero(lt(expr_1, result))
                    /// @src 33:2170:2377
                    {
                        /// @src 33:2278:2354
                        var := /** @src 6:4791:17612 */ and(/** @src 33:2293:2353 */ fun_mulDivRoundingUp(result, _1, expr_1), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                        /// @src 33:2278:2354
                        leave
                    }
                }
                /// @src 33:2525:2557
                let _2 := checked_add_uint256(/** @src 33:2526:2547 */ wrapping_div_uint256(result, _1), /** @src 33:2525:2557 */ var_amount)
                /// @src 33:2473:2559
                var := /** @src 6:4791:17612 */ and(/** @src 37:558:644 */ add(div(result, _2), iszero(iszero(mod(result, _2)))), /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
            }
            /// @ast-id 5612 @src 32:460:615
            function fun_toUint160(var_x) -> var_y
            {
                /// @src 32:534:548
                var_y := /** @src 6:4791:17612 */ and(/** @src 32:538:548 */ var_x, /** @src 6:4791:17612 */ 0xffffffffffffffffffffffffffffffffffffffff)
                /// @src 32:558:608
                if /** @src 32:562:568 */ iszero(eq(/** @src 6:4791:17612 */ var_y, /** @src 32:562:568 */ var_x))
                /// @src 32:558:608
                {
                    /// @src 19:814:910
                    mstore(0, /** @src 32:570:595 */ 0x93dafdf100000000000000000000000000000000000000000000000000000000)
                    /// @src 19:814:910
                    revert(0, 0x04)
                }
            }
        }
        data ".metadata" hex"a164736f6c634300081a000a"
    }
}
