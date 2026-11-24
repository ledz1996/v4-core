
/// @use-src 0:"solmate/src/auth/Owned.sol", 1:"src/ERC6909.sol", 2:"src/ERC6909Claims.sol", 3:"src/Extsload.sol", 4:"src/Exttload.sol", 5:"src/NoDelegateCall.sol", 6:"src/PoolManager.sol", 7:"src/ProtocolFees.sol", 8:"src/interfaces/IExtsload.sol", 9:"src/interfaces/IExttload.sol", 11:"src/interfaces/IPoolManager.sol", 12:"src/interfaces/IProtocolFees.sol", 15:"src/interfaces/external/IERC6909Claims.sol"
object "PoolManager_1216" {
    code {
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."
        mstore(64, memoryguard(160))
        if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }

        let _1 := copy_arguments_for_constructor_129_object_PoolManager_1216()
        constructor_PoolManager_1216(_1)

        let _2 := allocate_unbounded()
        codecopy(_2, dataoffset("PoolManager_1216_deployed"), datasize("PoolManager_1216_deployed"))

        setimmutable(_2, "1375", mload(128))

        return(_2, datasize("PoolManager_1216_deployed"))

        function allocate_unbounded() -> memPtr {
            memPtr := mload(64)
        }

        function revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() {
            revert(0, 0)
        }

        function round_up_to_mul_of_32(value) -> result {
            result := and(add(value, 31), not(31))
        }

        function panic_error_0x41() {
            mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
            mstore(4, 0x41)
            revert(0, 0x24)
        }

        function finalize_allocation(memPtr, size) {
            let newFreePtr := add(memPtr, round_up_to_mul_of_32(size))
            // protect against overflow
            if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr)) { panic_error_0x41() }
            mstore(64, newFreePtr)
        }

        function allocate_memory(size) -> memPtr {
            memPtr := allocate_unbounded()
            finalize_allocation(memPtr, size)
        }

        function revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() {
            revert(0, 0)
        }

        function revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() {
            revert(0, 0)
        }

        function cleanup_t_uint160(value) -> cleaned {
            cleaned := and(value, 0xffffffffffffffffffffffffffffffffffffffff)
        }

        function cleanup_t_address(value) -> cleaned {
            cleaned := cleanup_t_uint160(value)
        }

        function validator_revert_t_address(value) {
            if iszero(eq(value, cleanup_t_address(value))) { revert(0, 0) }
        }

        function abi_decode_t_address_fromMemory(offset, end) -> value {
            value := mload(offset)
            validator_revert_t_address(value)
        }

        function abi_decode_tuple_t_address_fromMemory(headStart, dataEnd) -> value0 {
            if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

            {

                let offset := 0

                value0 := abi_decode_t_address_fromMemory(add(headStart, offset), dataEnd)
            }

        }

        function copy_arguments_for_constructor_129_object_PoolManager_1216() -> ret_param_0 {
            let programSize := datasize("PoolManager_1216")
            let argSize := sub(codesize(), programSize)

            let memoryDataOffset := allocate_memory(argSize)
            codecopy(memoryDataOffset, programSize, argSize)

            ret_param_0 := abi_decode_tuple_t_address_fromMemory(memoryDataOffset, add(memoryDataOffset, argSize))
        }

        /// @ast-id 129
        /// @src 6:5508:5571  "constructor(address initialOwner) ProtocolFees(initialOwner) {}"
        function constructor_PoolManager_1216(var_initialOwner_122) {
            /// @src 6:5555:5567  "initialOwner"
            let _3 := var_initialOwner_122
            let expr_125 := _3
            let _4 := expr_125

            /// @src 6:5508:5571  "constructor(address initialOwner) ProtocolFees(initialOwner) {}"
            constructor_Exttload_1362(_4)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 4:272:1602  "abstract contract Exttload is IExttload {..."
        function constructor_Exttload_1362(_4) {

            /// @src 4:272:1602  "abstract contract Exttload is IExttload {..."
            constructor_Extsload_1332(_4)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 3:261:2608  "abstract contract Extsload is IExtsload {..."
        function constructor_Extsload_1332(_4) {

            /// @src 3:261:2608  "abstract contract Extsload is IExtsload {..."
            constructor_ERC6909Claims_1289(_4)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 2:185:957  "abstract contract ERC6909Claims is ERC6909 {..."
        function constructor_ERC6909Claims_1289(_4) {

            /// @src 2:185:957  "abstract contract ERC6909Claims is ERC6909 {..."
            constructor_ERC6909_7191(_4)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 1:463:3496  "abstract contract ERC6909 is IERC6909Claims {..."
        function constructor_ERC6909_7191(_4) {

            /// @src 1:463:3496  "abstract contract ERC6909 is IERC6909Claims {..."
            constructor_NoDelegateCall_1414(_4)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        function identity(value) -> ret {
            ret := value
        }

        function convert_t_uint160_to_t_uint160(value) -> converted {
            converted := cleanup_t_uint160(identity(cleanup_t_uint160(value)))
        }

        function convert_t_uint160_to_t_address(value) -> converted {
            converted := convert_t_uint160_to_t_uint160(value)
        }

        function convert_t_contract$_NoDelegateCall_$1414_to_t_address(value) -> converted {
            converted := convert_t_uint160_to_t_address(value)
        }

        /// @ast-id 1386
        /// @src 5:478:731  "constructor() {..."
        function constructor_NoDelegateCall_1414(_4) {

            /// @src 5:478:731  "constructor() {..."
            constructor_ProtocolFees_1641(_4)

            /// @src 5:719:723  "this"
            let expr_1381_address := address()
            /// @src 5:711:724  "address(this)"
            let expr_1382 := convert_t_contract$_NoDelegateCall_$1414_to_t_address(expr_1381_address)
            /// @src 5:700:724  "original = address(this)"
            let _5 := expr_1382
            mstore(128, _5)
            let expr_1383 := expr_1382

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @ast-id 1467
        /// @src 7:974:1030  "constructor(address initialOwner) Owned(initialOwner) {}"
        function constructor_ProtocolFees_1641(var_initialOwner_1460) {
            /// @src 7:1014:1026  "initialOwner"
            let _6 := var_initialOwner_1460
            let expr_1463 := _6
            let _7 := expr_1463

            /// @src 7:974:1030  "constructor(address initialOwner) Owned(initialOwner) {}"
            constructor_Owned_7306(_7)

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        function shift_left_0(value) -> newValue {
            newValue :=

            shl(0, value)

        }

        function update_byte_slice_20_shift_0(value, toInsert) -> result {
            let mask := 0xffffffffffffffffffffffffffffffffffffffff
            toInsert := shift_left_0(toInsert)
            value := and(value, not(mask))
            result := or(value, and(toInsert, mask))
        }

        function convert_t_address_to_t_address(value) -> converted {
            converted := convert_t_uint160_to_t_address(value)
        }

        function prepare_store_t_address(value) -> ret {
            ret := value
        }

        function update_storage_value_offset_0t_address_to_t_address(slot, value_0) {
            let convertedValue_0 := convert_t_address_to_t_address(value_0)
            sstore(slot, update_byte_slice_20_shift_0(sload(slot), prepare_store_t_address(convertedValue_0)))
        }

        function cleanup_t_rational_0_by_1(value) -> cleaned {
            cleaned := value
        }

        function convert_t_rational_0_by_1_to_t_uint160(value) -> converted {
            converted := cleanup_t_uint160(identity(cleanup_t_rational_0_by_1(value)))
        }

        function convert_t_rational_0_by_1_to_t_address(value) -> converted {
            converted := convert_t_rational_0_by_1_to_t_uint160(value)
        }

        function abi_encode_tuple__to__fromStack(headStart ) -> tail {
            tail := add(headStart, 0)

        }

        /// @ast-id 7287
        /// @src 0:1007:1122  "constructor(address _owner) {..."
        function constructor_Owned_7306(var__owner_7271) {

            /// @src 0:1007:1122  "constructor(address _owner) {..."
            constructor_IPoolManager_2123()

            /// @src 0:1053:1059  "_owner"
            let _8 := var__owner_7271
            let expr_7275 := _8
            /// @src 0:1045:1059  "owner = _owner"
            update_storage_value_offset_0t_address_to_t_address(0x00, expr_7275)
            let expr_7276 := expr_7275
            /// @src 0:1104:1105  "0"
            let expr_7281 := 0x00
            /// @src 0:1096:1106  "address(0)"
            let expr_7282 := convert_t_rational_0_by_1_to_t_address(expr_7281)
            /// @src 0:1108:1114  "_owner"
            let _9 := var__owner_7271
            let expr_7283 := _9
            /// @src 0:1075:1115  "OwnershipTransferred(address(0), _owner)"
            let _10 := 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0
            let _11 := convert_t_address_to_t_address(expr_7282)
            let _12 := convert_t_address_to_t_address(expr_7283)
            {
                let _13 := allocate_unbounded()
                let _14 := abi_encode_tuple__to__fromStack(_13 )
                log3(_13, sub(_14, _13) , _10, _11, _12)
            }
        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 11:609:12834  "interface IPoolManager is IProtocolFees, IERC6909Claims, IExtsload, IExttload {..."
        function constructor_IPoolManager_2123() {

            /// @src 11:609:12834  "interface IPoolManager is IProtocolFees, IERC6909Claims, IExtsload, IExttload {..."
            constructor_IExttload_7246()

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 9:145:698  "interface IExttload {..."
        function constructor_IExttload_7246() {

            /// @src 9:145:698  "interface IExttload {..."
            constructor_IExtsload_7224()

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 8:134:1022  "interface IExtsload {..."
        function constructor_IExtsload_7224() {

            /// @src 8:134:1022  "interface IExtsload {..."
            constructor_IERC6909Claims_7569()

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 15:136:3161  "interface IERC6909Claims {..."
        function constructor_IERC6909Claims_7569() {

            /// @src 15:136:3161  "interface IERC6909Claims {..."
            constructor_IProtocolFees_7383()

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        /// @src 12:277:2488  "interface IProtocolFees {..."
        function constructor_IProtocolFees_7383() {

            /// @src 12:277:2488  "interface IProtocolFees {..."

        }
        /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

    }
    /// @use-src 0:"solmate/src/auth/Owned.sol", 1:"src/ERC6909.sol", 2:"src/ERC6909Claims.sol", 3:"src/Extsload.sol", 4:"src/Exttload.sol", 5:"src/NoDelegateCall.sol", 6:"src/PoolManager.sol", 7:"src/ProtocolFees.sol", 16:"src/libraries/BitMath.sol", 17:"src/libraries/CurrencyDelta.sol", 18:"src/libraries/CurrencyReserves.sol", 19:"src/libraries/CustomRevert.sol", 20:"src/libraries/FixedPoint128.sol", 21:"src/libraries/FixedPoint96.sol", 22:"src/libraries/FullMath.sol", 23:"src/libraries/Hooks.sol", 24:"src/libraries/LPFeeLibrary.sol", 25:"src/libraries/LiquidityMath.sol", 26:"src/libraries/Lock.sol", 27:"src/libraries/NonzeroDeltaCount.sol", 28:"src/libraries/ParseBytes.sol", 29:"src/libraries/Pool.sol", 30:"src/libraries/Position.sol", 31:"src/libraries/ProtocolFeeLibrary.sol", 32:"src/libraries/SafeCast.sol", 33:"src/libraries/SqrtPriceMath.sol", 34:"src/libraries/SwapMath.sol", 35:"src/libraries/TickBitmap.sol", 36:"src/libraries/TickMath.sol", 37:"src/libraries/UnsafeMath.sol", 38:"src/types/BalanceDelta.sol", 39:"src/types/BeforeSwapDelta.sol", 40:"src/types/Currency.sol", 41:"src/types/PoolId.sol", 44:"src/types/Slot0.sol"
    object "PoolManager_1216_deployed" {
        code {
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."
            mstore(64, memoryguard(128))

            if iszero(lt(calldatasize(), 4))
            {
                let selector := shift_right_224_unsigned(calldataload(0))
                switch selector

                case 0x00fdd58e
                {
                    // balanceOf(address,uint256)

                    external_fun_balanceOf_6917()
                }

                case 0x01ffc9a7
                {
                    // supportsInterface(bytes4)

                    external_fun_supportsInterface_7130()
                }

                case 0x095bcdb6
                {
                    // transfer(address,uint256,uint256)

                    external_fun_transfer_6966()
                }

                case 0x0b0d9c09
                {
                    // take(address,address,uint256)

                    external_fun_take_833()
                }

                case 0x11da60b4
                {
                    // settle()

                    external_fun_settle_847()
                }

                case 0x156e29f6
                {
                    // mint(address,uint256,uint256)

                    external_fun_mint_950()
                }

                case 0x1e2eaeaf
                {
                    // extsload(bytes32)

                    external_fun_extsload_1306()
                }

                case 0x234266d7
                {
                    // donate((address,address,uint24,int24,address),uint256,uint256,bytes)

                    external_fun_donate_768()
                }

                case 0x2d771389
                {
                    // setProtocolFeeController(address)

                    external_fun_setProtocolFeeController_1484()
                }

                case 0x35fd631a
                {
                    // extsload(bytes32,uint256)

                    external_fun_extsload_1319()
                }

                case 0x3dd45adb
                {
                    // settleFor(address)

                    external_fun_settleFor_862()
                }

                case 0x426a8493
                {
                    // approve(address,uint256,uint256)

                    external_fun_approve_7086()
                }

                case 0x48c89491
                {
                    // unlock(bytes)

                    external_fun_unlock_183()
                }

                case 0x52759651
                {
                    // updateDynamicLPFee((address,address,uint24,int24,address),uint24)

                    external_fun_updateDynamicLPFee_1040()
                }

                case 0x558a7297
                {
                    // setOperator(address,bool)

                    external_fun_setOperator_7114()
                }

                case 0x598af9e7
                {
                    // allowance(address,address,uint256)

                    external_fun_allowance_6925()
                }

                case 0x5a6bcfda
                {
                    // modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)

                    external_fun_modifyLiquidity_474()
                }

                case 0x6276cbbe
                {
                    // initialize((address,address,uint24,int24,address),uint160)

                    external_fun_initialize_330()
                }

                case 0x7e87ce7d
                {
                    // setProtocolFee((address,address,uint24,int24,address),uint24)

                    external_fun_setProtocolFee_1538()
                }

                case 0x80f0b44c
                {
                    // clear(address,uint256)

                    external_fun_clear_909()
                }

                case 0x8161b874
                {
                    // collectProtocolFees(address,address,uint256)

                    external_fun_collectProtocolFees_1608()
                }

                case 0x8da5cb5b
                {
                    // owner()

                    external_fun_owner_7257()
                }

                case 0x97e8cd4e
                {
                    // protocolFeesAccrued(address)

                    external_fun_protocolFeesAccrued_1455()
                }

                case 0x9bf6645f
                {
                    // exttload(bytes32[])

                    external_fun_exttload_1361()
                }

                case 0xa5841194
                {
                    // sync(address)

                    external_fun_sync_800()
                }

                case 0xb6363cf2
                {
                    // isOperator(address,address)

                    external_fun_isOperator_6911()
                }

                case 0xdbd035ff
                {
                    // extsload(bytes32[])

                    external_fun_extsload_1331()
                }

                case 0xf02de3b2
                {
                    // protocolFeeController()

                    external_fun_protocolFeeController_1458()
                }

                case 0xf135baaa
                {
                    // exttload(bytes32)

                    external_fun_exttload_1349()
                }

                case 0xf2fde38b
                {
                    // transferOwnership(address)

                    external_fun_transferOwnership_7305()
                }

                case 0xf3cd914c
                {
                    // swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)

                    external_fun_swap_616()
                }

                case 0xf5298aca
                {
                    // burn(address,uint256,uint256)

                    external_fun_burn_988()
                }

                case 0xfe99049a
                {
                    // transferFrom(address,address,uint256,uint256)

                    external_fun_transferFrom_7053()
                }

                default {}
            }

            revert_error_42b3090547df1d2001c96683413b8cf91c1b902ef5e3cb8d9f6f304cf7446f74()

            function shift_right_224_unsigned(value) -> newValue {
                newValue :=

                shr(224, value)

            }

            function allocate_unbounded() -> memPtr {
                memPtr := mload(64)
            }

            function revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() {
                revert(0, 0)
            }

            function revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() {
                revert(0, 0)
            }

            function revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() {
                revert(0, 0)
            }

            function cleanup_t_uint160(value) -> cleaned {
                cleaned := and(value, 0xffffffffffffffffffffffffffffffffffffffff)
            }

            function cleanup_t_address(value) -> cleaned {
                cleaned := cleanup_t_uint160(value)
            }

            function validator_revert_t_address(value) {
                if iszero(eq(value, cleanup_t_address(value))) { revert(0, 0) }
            }

            function abi_decode_t_address(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_address(value)
            }

            function cleanup_t_uint256(value) -> cleaned {
                cleaned := value
            }

            function validator_revert_t_uint256(value) {
                if iszero(eq(value, cleanup_t_uint256(value))) { revert(0, 0) }
            }

            function abi_decode_t_uint256(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_uint256(value)
            }

            function abi_decode_tuple_t_addresst_uint256(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 64) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function identity(value) -> ret {
                ret := value
            }

            function convert_t_uint160_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_uint160(value)))
            }

            function convert_t_uint160_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_uint160(value)
            }

            function convert_t_address_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            function mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(slot , key) -> dataSlot {
                mstore(0, convert_t_address_to_t_address(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function convert_t_uint256_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint256(value)))
            }

            function mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(slot , key) -> dataSlot {
                mstore(0, convert_t_uint256_to_t_uint256(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function shift_right_unsigned_dynamic(bits, value) -> newValue {
                newValue :=

                shr(bits, value)

            }

            function cleanup_from_storage_t_uint256(value) -> cleaned {
                cleaned := value
            }

            function extract_from_storage_value_dynamict_uint256(slot_value, offset) -> value {
                value := cleanup_from_storage_t_uint256(shift_right_unsigned_dynamic(mul(offset, 8), slot_value))
            }

            function read_from_storage_split_dynamic_t_uint256(slot, offset) -> value {
                value := extract_from_storage_value_dynamict_uint256(sload(slot), offset)

            }

            /// @ast-id 6917
            /// @src 1:792:873  "mapping(address owner => mapping(uint256 id => uint256 balance)) public balanceOf"
            function getter_fun_balanceOf_6917(key_0, key_1) -> ret {

                let slot := 4
                let offset := 0

                slot := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(slot, key_0)

                slot := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(slot, key_1)

                ret := read_from_storage_split_dynamic_t_uint256(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function abi_encode_t_uint256_to_t_uint256_fromStack(value, pos) {
                mstore(pos, cleanup_t_uint256(value))
            }

            function abi_encode_tuple_t_uint256__to_t_uint256__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_uint256_to_t_uint256_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_balanceOf_6917() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_addresst_uint256(4, calldatasize())
                let ret_0 :=  getter_fun_balanceOf_6917(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function cleanup_t_bytes4(value) -> cleaned {
                cleaned := and(value, 0xffffffff00000000000000000000000000000000000000000000000000000000)
            }

            function validator_revert_t_bytes4(value) {
                if iszero(eq(value, cleanup_t_bytes4(value))) { revert(0, 0) }
            }

            function abi_decode_t_bytes4(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_bytes4(value)
            }

            function abi_decode_tuple_t_bytes4(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_bytes4(add(headStart, offset), dataEnd)
                }

            }

            function cleanup_t_bool(value) -> cleaned {
                cleaned := iszero(iszero(value))
            }

            function abi_encode_t_bool_to_t_bool_fromStack(value, pos) {
                mstore(pos, cleanup_t_bool(value))
            }

            function abi_encode_tuple_t_bool__to_t_bool__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_bool_to_t_bool_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_supportsInterface_7130() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_bytes4(4, calldatasize())
                let ret_0 :=  fun_supportsInterface_7130(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_addresst_uint256t_uint256(headStart, dataEnd) -> value0, value1, value2 {
                if slt(sub(dataEnd, headStart), 96) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 64

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_transfer_6966() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_uint256t_uint256(4, calldatasize())
                let ret_0 :=  fun_transfer_6966(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function validator_revert_t_userDefinedValueType$_Currency_$6525(value) {
                if iszero(eq(value, cleanup_t_address(value))) { revert(0, 0) }
            }

            function abi_decode_t_userDefinedValueType$_Currency_$6525(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_userDefinedValueType$_Currency_$6525(value)
            }

            function abi_decode_tuple_t_userDefinedValueType$_Currency_$6525t_addresst_uint256(headStart, dataEnd) -> value0, value1, value2 {
                if slt(sub(dataEnd, headStart), 96) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 64

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function abi_encode_tuple__to__fromStack(headStart ) -> tail {
                tail := add(headStart, 0)

            }

            function external_fun_take_833() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_userDefinedValueType$_Currency_$6525t_addresst_uint256(4, calldatasize())
                fun_take_833(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_(headStart, dataEnd)   {
                if slt(sub(dataEnd, headStart), 0) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

            }

            function external_fun_settle_847() {

                abi_decode_tuple_(4, calldatasize())
                let ret_0 :=  fun_settle_847()
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_mint_950() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_uint256t_uint256(4, calldatasize())
                fun_mint_950(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function cleanup_t_bytes32(value) -> cleaned {
                cleaned := value
            }

            function validator_revert_t_bytes32(value) {
                if iszero(eq(value, cleanup_t_bytes32(value))) { revert(0, 0) }
            }

            function abi_decode_t_bytes32(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_bytes32(value)
            }

            function abi_decode_tuple_t_bytes32(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_bytes32(add(headStart, offset), dataEnd)
                }

            }

            function abi_encode_t_bytes32_to_t_bytes32_fromStack(value, pos) {
                mstore(pos, cleanup_t_bytes32(value))
            }

            function abi_encode_tuple_t_bytes32__to_t_bytes32__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_bytes32_to_t_bytes32_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_extsload_1306() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_bytes32(4, calldatasize())
                let ret_0 :=  fun_extsload_1306(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bytes32__to_t_bytes32__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function revert_error_3538a459e4a0eb828f1aed5ebe5dc96fe59620a31d9b33e41259bb820cae769f() {
                revert(0, 0)
            }

            function round_up_to_mul_of_32(value) -> result {
                result := and(add(value, 31), not(31))
            }

            function panic_error_0x41() {
                mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                mstore(4, 0x41)
                revert(0, 0x24)
            }

            function finalize_allocation(memPtr, size) {
                let newFreePtr := add(memPtr, round_up_to_mul_of_32(size))
                // protect against overflow
                if or(gt(newFreePtr, 0xffffffffffffffff), lt(newFreePtr, memPtr)) { panic_error_0x41() }
                mstore(64, newFreePtr)
            }

            function allocate_memory(size) -> memPtr {
                memPtr := allocate_unbounded()
                finalize_allocation(memPtr, size)
            }

            function revert_error_5e8f644817bc4960744f35c15999b6eff64ae702f94b1c46297cfd4e1aec2421() {
                revert(0, 0)
            }

            function cleanup_t_uint24(value) -> cleaned {
                cleaned := and(value, 0xffffff)
            }

            function validator_revert_t_uint24(value) {
                if iszero(eq(value, cleanup_t_uint24(value))) { revert(0, 0) }
            }

            function abi_decode_t_uint24(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_uint24(value)
            }

            function cleanup_t_int24(value) -> cleaned {
                cleaned := signextend(2, value)
            }

            function validator_revert_t_int24(value) {
                if iszero(eq(value, cleanup_t_int24(value))) { revert(0, 0) }
            }

            function abi_decode_t_int24(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_int24(value)
            }

            function cleanup_t_contract$_IHooks_$1840(value) -> cleaned {
                cleaned := cleanup_t_address(value)
            }

            function validator_revert_t_contract$_IHooks_$1840(value) {
                if iszero(eq(value, cleanup_t_contract$_IHooks_$1840(value))) { revert(0, 0) }
            }

            function abi_decode_t_contract$_IHooks_$1840(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_contract$_IHooks_$1840(value)
            }

            // struct PoolKey
            function abi_decode_t_struct$_PoolKey_$6871_memory_ptr(headStart, end) -> value {
                if slt(sub(end, headStart), 0xa0) { revert_error_3538a459e4a0eb828f1aed5ebe5dc96fe59620a31d9b33e41259bb820cae769f() }
                value := allocate_memory(0xa0)

                {
                    // currency0

                    let offset := 0

                    mstore(add(value, 0x00), abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), end))

                }

                {
                    // currency1

                    let offset := 32

                    mstore(add(value, 0x20), abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), end))

                }

                {
                    // fee

                    let offset := 64

                    mstore(add(value, 0x40), abi_decode_t_uint24(add(headStart, offset), end))

                }

                {
                    // tickSpacing

                    let offset := 96

                    mstore(add(value, 0x60), abi_decode_t_int24(add(headStart, offset), end))

                }

                {
                    // hooks

                    let offset := 128

                    mstore(add(value, 0x80), abi_decode_t_contract$_IHooks_$1840(add(headStart, offset), end))

                }

            }

            function revert_error_1b9f4a0a5773e33b91aa01db23bf8c55fce1411167c872835e7fa00a4f17d46d() {
                revert(0, 0)
            }

            function revert_error_15abf5612cd996bc235ba1e55a4a30ac60e6bb601ff7ba4ad3f179b6be8d0490() {
                revert(0, 0)
            }

            function revert_error_81385d8c0b31fffe14be1da910c8bd3a80be4cfa248e04f42ec0faea3132a8ef() {
                revert(0, 0)
            }

            // bytes
            function abi_decode_t_bytes_calldata_ptr(offset, end) -> arrayPos, length {
                if iszero(slt(add(offset, 0x1f), end)) { revert_error_1b9f4a0a5773e33b91aa01db23bf8c55fce1411167c872835e7fa00a4f17d46d() }
                length := calldataload(offset)
                if gt(length, 0xffffffffffffffff) { revert_error_15abf5612cd996bc235ba1e55a4a30ac60e6bb601ff7ba4ad3f179b6be8d0490() }
                arrayPos := add(offset, 0x20)
                if gt(add(arrayPos, mul(length, 0x01)), end) { revert_error_81385d8c0b31fffe14be1da910c8bd3a80be4cfa248e04f42ec0faea3132a8ef() }
            }

            function abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint256t_uint256t_bytes_calldata_ptr(headStart, dataEnd) -> value0, value1, value2, value3, value4 {
                if slt(sub(dataEnd, headStart), 256) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_struct$_PoolKey_$6871_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 160

                    value1 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 192

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

                {

                    let offset := calldataload(add(headStart, 224))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value3, value4 := abi_decode_t_bytes_calldata_ptr(add(headStart, offset), dataEnd)
                }

            }

            function cleanup_t_int256(value) -> cleaned {
                cleaned := value
            }

            function convert_t_int256_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_int256(value)))
            }

            function abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value, pos) {
                mstore(pos, convert_t_int256_to_t_int256(value))
            }

            function abi_encode_tuple_t_userDefinedValueType$_BalanceDelta_$6311__to_t_int256__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_donate_768() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2, param_3, param_4 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint256t_uint256t_bytes_calldata_ptr(4, calldatasize())
                let ret_0 :=  fun_donate_768(param_0, param_1, param_2, param_3, param_4)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_userDefinedValueType$_BalanceDelta_$6311__to_t_int256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_address(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_setProtocolFeeController_1484() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_address(4, calldatasize())
                fun_setProtocolFeeController_1484(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_bytes32t_uint256(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 64) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_bytes32(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function array_length_t_array$_t_bytes32_$dyn_memory_ptr(value) -> length {

                length := mload(value)

            }

            function array_storeLengthForEncoding_t_array$_t_bytes32_$dyn_memory_ptr_fromStack(pos, length) -> updated_pos {
                mstore(pos, length)
                updated_pos := add(pos, 0x20)
            }

            function array_dataslot_t_array$_t_bytes32_$dyn_memory_ptr(ptr) -> data {
                data := ptr

                data := add(ptr, 0x20)

            }

            function abi_encode_t_bytes32_to_t_bytes32(value, pos) {
                mstore(pos, cleanup_t_bytes32(value))
            }

            function abi_encodeUpdatedPos_t_bytes32_to_t_bytes32(value0, pos) -> updatedPos {
                abi_encode_t_bytes32_to_t_bytes32(value0, pos)
                updatedPos := add(pos, 0x20)
            }

            function array_nextElement_t_array$_t_bytes32_$dyn_memory_ptr(ptr) -> next {
                next := add(ptr, 0x20)
            }

            // bytes32[] -> bytes32[]
            function abi_encode_t_array$_t_bytes32_$dyn_memory_ptr_to_t_array$_t_bytes32_$dyn_memory_ptr_fromStack(value, pos)  -> end  {
                let length := array_length_t_array$_t_bytes32_$dyn_memory_ptr(value)
                pos := array_storeLengthForEncoding_t_array$_t_bytes32_$dyn_memory_ptr_fromStack(pos, length)
                let baseRef := array_dataslot_t_array$_t_bytes32_$dyn_memory_ptr(value)
                let srcPtr := baseRef
                for { let i := 0 } lt(i, length) { i := add(i, 1) }
                {
                    let elementValue0 := mload(srcPtr)
                    pos := abi_encodeUpdatedPos_t_bytes32_to_t_bytes32(elementValue0, pos)
                    srcPtr := array_nextElement_t_array$_t_bytes32_$dyn_memory_ptr(srcPtr)
                }
                end := pos
            }

            function abi_encode_tuple_t_array$_t_bytes32_$dyn_memory_ptr__to_t_array$_t_bytes32_$dyn_memory_ptr__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                mstore(add(headStart, 0), sub(tail, headStart))
                tail := abi_encode_t_array$_t_bytes32_$dyn_memory_ptr_to_t_array$_t_bytes32_$dyn_memory_ptr_fromStack(value0,  tail)

            }

            function external_fun_extsload_1319() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_bytes32t_uint256(4, calldatasize())
                let ret_0 :=  fun_extsload_1319(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_array$_t_bytes32_$dyn_memory_ptr__to_t_array$_t_bytes32_$dyn_memory_ptr__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_settleFor_862() {

                let param_0 :=  abi_decode_tuple_t_address(4, calldatasize())
                let ret_0 :=  fun_settleFor_862(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_approve_7086() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_uint256t_uint256(4, calldatasize())
                let ret_0 :=  fun_approve_7086(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_bytes_calldata_ptr(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := calldataload(add(headStart, 0))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value0, value1 := abi_decode_t_bytes_calldata_ptr(add(headStart, offset), dataEnd)
                }

            }

            function array_length_t_bytes_memory_ptr(value) -> length {

                length := mload(value)

            }

            function array_storeLengthForEncoding_t_bytes_memory_ptr_fromStack(pos, length) -> updated_pos {
                mstore(pos, length)
                updated_pos := add(pos, 0x20)
            }

            function copy_memory_to_memory_with_cleanup(src, dst, length) {

                mcopy(dst, src, length)
                mstore(add(dst, length), 0)

            }

            function abi_encode_t_bytes_memory_ptr_to_t_bytes_memory_ptr_fromStack(value, pos) -> end {
                let length := array_length_t_bytes_memory_ptr(value)
                pos := array_storeLengthForEncoding_t_bytes_memory_ptr_fromStack(pos, length)
                copy_memory_to_memory_with_cleanup(add(value, 0x20), pos, length)
                end := add(pos, round_up_to_mul_of_32(length))
            }

            function abi_encode_tuple_t_bytes_memory_ptr__to_t_bytes_memory_ptr__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                mstore(add(headStart, 0), sub(tail, headStart))
                tail := abi_encode_t_bytes_memory_ptr_to_t_bytes_memory_ptr_fromStack(value0,  tail)

            }

            function external_fun_unlock_183() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_bytes_calldata_ptr(4, calldatasize())
                let ret_0 :=  fun_unlock_183(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bytes_memory_ptr__to_t_bytes_memory_ptr__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint24(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 192) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_struct$_PoolKey_$6871_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 160

                    value1 := abi_decode_t_uint24(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_updateDynamicLPFee_1040() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint24(4, calldatasize())
                fun_updateDynamicLPFee_1040(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function validator_revert_t_bool(value) {
                if iszero(eq(value, cleanup_t_bool(value))) { revert(0, 0) }
            }

            function abi_decode_t_bool(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_bool(value)
            }

            function abi_decode_tuple_t_addresst_bool(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 64) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_bool(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_setOperator_7114() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_addresst_bool(4, calldatasize())
                let ret_0 :=  fun_setOperator_7114(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_addresst_addresst_uint256(headStart, dataEnd) -> value0, value1, value2 {
                if slt(sub(dataEnd, headStart), 96) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 64

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(slot , key) -> dataSlot {
                mstore(0, convert_t_address_to_t_address(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            /// @ast-id 6925
            /// @src 1:880:988  "mapping(address owner => mapping(address spender => mapping(uint256 id => uint256 amount))) public allowance"
            function getter_fun_allowance_6925(key_0, key_1, key_2) -> ret {

                let slot := 5
                let offset := 0

                slot := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(slot, key_0)

                slot := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(slot, key_1)

                slot := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(slot, key_2)

                ret := read_from_storage_split_dynamic_t_uint256(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function external_fun_allowance_6925() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_addresst_uint256(4, calldatasize())
                let ret_0 :=  getter_fun_allowance_6925(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function validator_revert_t_int256(value) {
                if iszero(eq(value, cleanup_t_int256(value))) { revert(0, 0) }
            }

            function abi_decode_t_int256(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_int256(value)
            }

            // struct ModifyLiquidityParams
            function abi_decode_t_struct$_ModifyLiquidityParams_$6887_memory_ptr(headStart, end) -> value {
                if slt(sub(end, headStart), 0x80) { revert_error_3538a459e4a0eb828f1aed5ebe5dc96fe59620a31d9b33e41259bb820cae769f() }
                value := allocate_memory(0x80)

                {
                    // tickLower

                    let offset := 0

                    mstore(add(value, 0x00), abi_decode_t_int24(add(headStart, offset), end))

                }

                {
                    // tickUpper

                    let offset := 32

                    mstore(add(value, 0x20), abi_decode_t_int24(add(headStart, offset), end))

                }

                {
                    // liquidityDelta

                    let offset := 64

                    mstore(add(value, 0x40), abi_decode_t_int256(add(headStart, offset), end))

                }

                {
                    // salt

                    let offset := 96

                    mstore(add(value, 0x60), abi_decode_t_bytes32(add(headStart, offset), end))

                }

            }

            function abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_struct$_ModifyLiquidityParams_$6887_memory_ptrt_bytes_calldata_ptr(headStart, dataEnd) -> value0, value1, value2, value3 {
                if slt(sub(dataEnd, headStart), 320) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_struct$_PoolKey_$6871_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 160

                    value1 := abi_decode_t_struct$_ModifyLiquidityParams_$6887_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := calldataload(add(headStart, 288))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value2, value3 := abi_decode_t_bytes_calldata_ptr(add(headStart, offset), dataEnd)
                }

            }

            function abi_encode_tuple_t_userDefinedValueType$_BalanceDelta_$6311_t_userDefinedValueType$_BalanceDelta_$6311__to_t_int256_t_int256__fromStack(headStart , value0, value1) -> tail {
                tail := add(headStart, 64)

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value0,  add(headStart, 0))

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value1,  add(headStart, 32))

            }

            function external_fun_modifyLiquidity_474() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2, param_3 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_struct$_ModifyLiquidityParams_$6887_memory_ptrt_bytes_calldata_ptr(4, calldatasize())
                let ret_0, ret_1 :=  fun_modifyLiquidity_474(param_0, param_1, param_2, param_3)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_userDefinedValueType$_BalanceDelta_$6311_t_userDefinedValueType$_BalanceDelta_$6311__to_t_int256_t_int256__fromStack(memPos , ret_0, ret_1)
                return(memPos, sub(memEnd, memPos))

            }

            function validator_revert_t_uint160(value) {
                if iszero(eq(value, cleanup_t_uint160(value))) { revert(0, 0) }
            }

            function abi_decode_t_uint160(offset, end) -> value {
                value := calldataload(offset)
                validator_revert_t_uint160(value)
            }

            function abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint160(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 192) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_struct$_PoolKey_$6871_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 160

                    value1 := abi_decode_t_uint160(add(headStart, offset), dataEnd)
                }

            }

            function abi_encode_t_int24_to_t_int24_fromStack(value, pos) {
                mstore(pos, cleanup_t_int24(value))
            }

            function abi_encode_tuple_t_int24__to_t_int24__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_int24_to_t_int24_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_initialize_330() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint160(4, calldatasize())
                let ret_0 :=  fun_initialize_330(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_int24__to_t_int24__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_setProtocolFee_1538() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_uint24(4, calldatasize())
                fun_setProtocolFee_1538(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_userDefinedValueType$_Currency_$6525t_uint256(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 64) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_clear_909() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_userDefinedValueType$_Currency_$6525t_uint256(4, calldatasize())
                fun_clear_909(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_addresst_userDefinedValueType$_Currency_$6525t_uint256(headStart, dataEnd) -> value0, value1, value2 {
                if slt(sub(dataEnd, headStart), 96) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 64

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_collectProtocolFees_1608() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_userDefinedValueType$_Currency_$6525t_uint256(4, calldatasize())
                let ret_0 :=  fun_collectProtocolFees_1608(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function cleanup_from_storage_t_address(value) -> cleaned {
                cleaned := and(value, 0xffffffffffffffffffffffffffffffffffffffff)
            }

            function extract_from_storage_value_dynamict_address(slot_value, offset) -> value {
                value := cleanup_from_storage_t_address(shift_right_unsigned_dynamic(mul(offset, 8), slot_value))
            }

            function read_from_storage_split_dynamic_t_address(slot, offset) -> value {
                value := extract_from_storage_value_dynamict_address(sload(slot), offset)

            }

            /// @ast-id 7257
            /// @src 0:690:710  "address public owner"
            function getter_fun_owner_7257() -> ret {

                let slot := 0
                let offset := 0

                ret := read_from_storage_split_dynamic_t_address(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function abi_encode_t_address_to_t_address_fromStack(value, pos) {
                mstore(pos, cleanup_t_address(value))
            }

            function abi_encode_tuple_t_address__to_t_address__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

            }

            function external_fun_owner_7257() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                abi_decode_tuple_(4, calldatasize())
                let ret_0 :=  getter_fun_owner_7257()
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_address__to_t_address__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_userDefinedValueType$_Currency_$6525(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_userDefinedValueType$_Currency_$6525(add(headStart, offset), dataEnd)
                }

            }

            function mapping_index_access_t_mapping$_t_userDefinedValueType$_Currency_$6525_$_t_uint256_$_of_t_userDefinedValueType$_Currency_$6525(slot , key) -> dataSlot {
                mstore(0, convert_t_address_to_t_address(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            /// @ast-id 1455
            /// @src 7:819:890  "mapping(Currency currency => uint256 amount) public protocolFeesAccrued"
            function getter_fun_protocolFeesAccrued_1455(key_0) -> ret {

                let slot := 1
                let offset := 0

                slot := mapping_index_access_t_mapping$_t_userDefinedValueType$_Currency_$6525_$_t_uint256_$_of_t_userDefinedValueType$_Currency_$6525(slot, key_0)

                ret := read_from_storage_split_dynamic_t_uint256(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function external_fun_protocolFeesAccrued_1455() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_userDefinedValueType$_Currency_$6525(4, calldatasize())
                let ret_0 :=  getter_fun_protocolFeesAccrued_1455(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            // bytes32[]
            function abi_decode_t_array$_t_bytes32_$dyn_calldata_ptr(offset, end) -> arrayPos, length {
                if iszero(slt(add(offset, 0x1f), end)) { revert_error_1b9f4a0a5773e33b91aa01db23bf8c55fce1411167c872835e7fa00a4f17d46d() }
                length := calldataload(offset)
                if gt(length, 0xffffffffffffffff) { revert_error_15abf5612cd996bc235ba1e55a4a30ac60e6bb601ff7ba4ad3f179b6be8d0490() }
                arrayPos := add(offset, 0x20)
                if gt(add(arrayPos, mul(length, 0x20)), end) { revert_error_81385d8c0b31fffe14be1da910c8bd3a80be4cfa248e04f42ec0faea3132a8ef() }
            }

            function abi_decode_tuple_t_array$_t_bytes32_$dyn_calldata_ptr(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := calldataload(add(headStart, 0))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value0, value1 := abi_decode_t_array$_t_bytes32_$dyn_calldata_ptr(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_exttload_1361() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_array$_t_bytes32_$dyn_calldata_ptr(4, calldatasize())
                let ret_0 :=  fun_exttload_1361(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_array$_t_bytes32_$dyn_memory_ptr__to_t_array$_t_bytes32_$dyn_memory_ptr__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_sync_800() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_userDefinedValueType$_Currency_$6525(4, calldatasize())
                fun_sync_800(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_addresst_address(headStart, dataEnd) -> value0, value1 {
                if slt(sub(dataEnd, headStart), 64) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

            }

            function mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_bool_$_$_of_t_address(slot , key) -> dataSlot {
                mstore(0, convert_t_address_to_t_address(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function mapping_index_access_t_mapping$_t_address_$_t_bool_$_of_t_address(slot , key) -> dataSlot {
                mstore(0, convert_t_address_to_t_address(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function cleanup_from_storage_t_bool(value) -> cleaned {
                cleaned := and(value, 0xff)
            }

            function extract_from_storage_value_dynamict_bool(slot_value, offset) -> value {
                value := cleanup_from_storage_t_bool(shift_right_unsigned_dynamic(mul(offset, 8), slot_value))
            }

            function read_from_storage_split_dynamic_t_bool(slot, offset) -> value {
                value := extract_from_storage_value_dynamict_bool(sload(slot), offset)

            }

            /// @ast-id 6911
            /// @src 1:697:785  "mapping(address owner => mapping(address operator => bool isOperator)) public isOperator"
            function getter_fun_isOperator_6911(key_0, key_1) -> ret {

                let slot := 3
                let offset := 0

                slot := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_bool_$_$_of_t_address(slot, key_0)

                slot := mapping_index_access_t_mapping$_t_address_$_t_bool_$_of_t_address(slot, key_1)

                ret := read_from_storage_split_dynamic_t_bool(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function external_fun_isOperator_6911() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_addresst_address(4, calldatasize())
                let ret_0 :=  getter_fun_isOperator_6911(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_extsload_1331() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1 :=  abi_decode_tuple_t_array$_t_bytes32_$dyn_calldata_ptr(4, calldatasize())
                let ret_0 :=  fun_extsload_1331(param_0, param_1)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_array$_t_bytes32_$dyn_memory_ptr__to_t_array$_t_bytes32_$dyn_memory_ptr__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            /// @ast-id 1458
            /// @src 7:931:967  "address public protocolFeeController"
            function getter_fun_protocolFeeController_1458() -> ret {

                let slot := 2
                let offset := 0

                ret := read_from_storage_split_dynamic_t_address(slot, offset)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function external_fun_protocolFeeController_1458() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                abi_decode_tuple_(4, calldatasize())
                let ret_0 :=  getter_fun_protocolFeeController_1458()
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_address__to_t_address__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_exttload_1349() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_bytes32(4, calldatasize())
                let ret_0 :=  fun_exttload_1349(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bytes32__to_t_bytes32__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_transferOwnership_7305() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0 :=  abi_decode_tuple_t_address(4, calldatasize())
                fun_transferOwnership_7305(param_0)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            // struct SwapParams
            function abi_decode_t_struct$_SwapParams_$6898_memory_ptr(headStart, end) -> value {
                if slt(sub(end, headStart), 0x60) { revert_error_3538a459e4a0eb828f1aed5ebe5dc96fe59620a31d9b33e41259bb820cae769f() }
                value := allocate_memory(0x60)

                {
                    // zeroForOne

                    let offset := 0

                    mstore(add(value, 0x00), abi_decode_t_bool(add(headStart, offset), end))

                }

                {
                    // amountSpecified

                    let offset := 32

                    mstore(add(value, 0x20), abi_decode_t_int256(add(headStart, offset), end))

                }

                {
                    // sqrtPriceLimitX96

                    let offset := 64

                    mstore(add(value, 0x40), abi_decode_t_uint160(add(headStart, offset), end))

                }

            }

            function abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_struct$_SwapParams_$6898_memory_ptrt_bytes_calldata_ptr(headStart, dataEnd) -> value0, value1, value2, value3 {
                if slt(sub(dataEnd, headStart), 288) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_struct$_PoolKey_$6871_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 160

                    value1 := abi_decode_t_struct$_SwapParams_$6898_memory_ptr(add(headStart, offset), dataEnd)
                }

                {

                    let offset := calldataload(add(headStart, 256))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value2, value3 := abi_decode_t_bytes_calldata_ptr(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_swap_616() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2, param_3 :=  abi_decode_tuple_t_struct$_PoolKey_$6871_memory_ptrt_struct$_SwapParams_$6898_memory_ptrt_bytes_calldata_ptr(4, calldatasize())
                let ret_0 :=  fun_swap_616(param_0, param_1, param_2, param_3)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_userDefinedValueType$_BalanceDelta_$6311__to_t_int256__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function external_fun_burn_988() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2 :=  abi_decode_tuple_t_addresst_uint256t_uint256(4, calldatasize())
                fun_burn_988(param_0, param_1, param_2)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple__to__fromStack(memPos  )
                return(memPos, sub(memEnd, memPos))

            }

            function abi_decode_tuple_t_addresst_addresst_uint256t_uint256(headStart, dataEnd) -> value0, value1, value2, value3 {
                if slt(sub(dataEnd, headStart), 128) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 32

                    value1 := abi_decode_t_address(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 64

                    value2 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

                {

                    let offset := 96

                    value3 := abi_decode_t_uint256(add(headStart, offset), dataEnd)
                }

            }

            function external_fun_transferFrom_7053() {

                if callvalue() { revert_error_ca66f745a3ce8ff40e2ccaf1ad45db7774001b90d25810abd9040049be7bf4bb() }
                let param_0, param_1, param_2, param_3 :=  abi_decode_tuple_t_addresst_addresst_uint256t_uint256(4, calldatasize())
                let ret_0 :=  fun_transferFrom_7053(param_0, param_1, param_2, param_3)
                let memPos := allocate_unbounded()
                let memEnd := abi_encode_tuple_t_bool__to_t_bool__fromStack(memPos , ret_0)
                return(memPos, sub(memEnd, memPos))

            }

            function revert_error_42b3090547df1d2001c96683413b8cf91c1b902ef5e3cb8d9f6f304cf7446f74() {
                revert(0, 0)
            }

            function zero_value_for_split_t_bool() -> ret {
                ret := 0
            }

            function cleanup_t_rational_33540519_by_1(value) -> cleaned {
                cleaned := value
            }

            function shift_left_224(value) -> newValue {
                newValue :=

                shl(224, value)

            }

            function convert_t_rational_33540519_by_1_to_t_bytes4(value) -> converted {
                converted := cleanup_t_bytes4(shift_left_224(cleanup_t_rational_33540519_by_1(value)))
            }

            function cleanup_t_rational_258158515_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_258158515_by_1_to_t_bytes4(value) -> converted {
                converted := cleanup_t_bytes4(shift_left_224(cleanup_t_rational_258158515_by_1(value)))
            }

            /// @ast-id 7130
            /// @src 1:2663:2904  "function supportsInterface(bytes4 interfaceId) public view virtual returns (bool) {..."
            function fun_supportsInterface_7130(var_interfaceId_7116) -> var__7119 {
                /// @src 1:2739:2743  "bool"
                let zero_t_bool_1 := zero_value_for_split_t_bool()
                var__7119 := zero_t_bool_1

                /// @src 1:2762:2773  "interfaceId"
                let _2 := var_interfaceId_7116
                let expr_7121 := _2
                /// @src 1:2777:2787  "0x01ffc9a7"
                let expr_7122 := 0x01ffc9a7
                /// @src 1:2762:2787  "interfaceId == 0x01ffc9a7"
                let expr_7123 := eq(cleanup_t_bytes4(expr_7121), convert_t_rational_33540519_by_1_to_t_bytes4(expr_7122))
                /// @src 1:2762:2862  "interfaceId == 0x01ffc9a7 // ERC165 Interface ID for ERC165..."
                let expr_7127 := expr_7123
                if iszero(expr_7127) {
                    /// @src 1:2837:2848  "interfaceId"
                    let _3 := var_interfaceId_7116
                    let expr_7124 := _3
                    /// @src 1:2852:2862  "0x0f632fb3"
                    let expr_7125 := 0x0f632fb3
                    /// @src 1:2837:2862  "interfaceId == 0x0f632fb3"
                    let expr_7126 := eq(cleanup_t_bytes4(expr_7124), convert_t_rational_258158515_by_1_to_t_bytes4(expr_7125))
                    /// @src 1:2762:2862  "interfaceId == 0x01ffc9a7 // ERC165 Interface ID for ERC165..."
                    expr_7127 := expr_7126
                }
                /// @src 1:2755:2862  "return interfaceId == 0x01ffc9a7 // ERC165 Interface ID for ERC165..."
                var__7119 := expr_7127
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function shift_right_0_unsigned(value) -> newValue {
                newValue :=

                shr(0, value)

            }

            function extract_from_storage_value_offset_0t_uint256(slot_value) -> value {
                value := cleanup_from_storage_t_uint256(shift_right_0_unsigned(slot_value))
            }

            function read_from_storage_split_offset_0_t_uint256(slot) -> value {
                value := extract_from_storage_value_offset_0t_uint256(sload(slot))

            }

            function panic_error_0x11() {
                mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                mstore(4, 0x11)
                revert(0, 0x24)
            }

            function checked_sub_t_uint256(x, y) -> diff {
                x := cleanup_t_uint256(x)
                y := cleanup_t_uint256(y)
                diff := sub(x, y)

                if gt(diff, x) { panic_error_0x11() }

            }

            function shift_left_0(value) -> newValue {
                newValue :=

                shl(0, value)

            }

            function update_byte_slice_32_shift_0(value, toInsert) -> result {
                let mask := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                toInsert := shift_left_0(toInsert)
                value := and(value, not(mask))
                result := or(value, and(toInsert, mask))
            }

            function prepare_store_t_uint256(value) -> ret {
                ret := value
            }

            function update_storage_value_offset_0t_uint256_to_t_uint256(slot, value_0) {
                let convertedValue_0 := convert_t_uint256_to_t_uint256(value_0)
                sstore(slot, update_byte_slice_32_shift_0(sload(slot), prepare_store_t_uint256(convertedValue_0)))
            }

            function checked_add_t_uint256(x, y) -> sum {
                x := cleanup_t_uint256(x)
                y := cleanup_t_uint256(y)
                sum := add(x, y)

                if gt(x, sum) { panic_error_0x11() }

            }

            function abi_encode_tuple_t_address_t_uint256__to_t_address_t_uint256__fromStack(headStart , value0, value1) -> tail {
                tail := add(headStart, 64)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_uint256_to_t_uint256_fromStack(value1,  add(headStart, 32))

            }

            /// @ast-id 6966
            /// @src 1:1178:1460  "function transfer(address receiver, uint256 id, uint256 amount) public virtual returns (bool) {..."
            function fun_transfer_6966(var_receiver_6927, var_id_6929, var_amount_6931) -> var__6934 {
                /// @src 1:1266:1270  "bool"
                let zero_t_bool_4 := zero_value_for_split_t_bool()
                var__6934 := zero_t_bool_4

                /// @src 1:1311:1317  "amount"
                let _5 := var_amount_6931
                let expr_6942 := _5
                /// @src 1:1282:1291  "balanceOf"
                let _6_slot := 0x04
                let expr_6936_slot := _6_slot
                /// @src 1:1292:1302  "msg.sender"
                let expr_6938 := caller()
                /// @src 1:1282:1303  "balanceOf[msg.sender]"
                let _7 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_6936_slot,expr_6938)
                let _8_slot := _7
                let expr_6940_slot := _8_slot
                /// @src 1:1304:1306  "id"
                let _9 := var_id_6929
                let expr_6939 := _9
                /// @src 1:1282:1307  "balanceOf[msg.sender][id]"
                let _10 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_6940_slot,expr_6939)
                /// @src 1:1282:1317  "balanceOf[msg.sender][id] -= amount"
                let _11 := read_from_storage_split_offset_0_t_uint256(_10)
                let expr_6943 := checked_sub_t_uint256(_11, expr_6942)

                update_storage_value_offset_0t_uint256_to_t_uint256(_10, expr_6943)
                /// @src 1:1355:1361  "amount"
                let _12 := var_amount_6931
                let expr_6950 := _12
                /// @src 1:1328:1337  "balanceOf"
                let _13_slot := 0x04
                let expr_6945_slot := _13_slot
                /// @src 1:1338:1346  "receiver"
                let _14 := var_receiver_6927
                let expr_6946 := _14
                /// @src 1:1328:1347  "balanceOf[receiver]"
                let _15 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_6945_slot,expr_6946)
                let _16_slot := _15
                let expr_6948_slot := _16_slot
                /// @src 1:1348:1350  "id"
                let _17 := var_id_6929
                let expr_6947 := _17
                /// @src 1:1328:1351  "balanceOf[receiver][id]"
                let _18 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_6948_slot,expr_6947)
                /// @src 1:1328:1361  "balanceOf[receiver][id] += amount"
                let _19 := read_from_storage_split_offset_0_t_uint256(_18)
                let expr_6951 := checked_add_t_uint256(_19, expr_6950)

                update_storage_value_offset_0t_uint256_to_t_uint256(_18, expr_6951)
                /// @src 1:1386:1396  "msg.sender"
                let expr_6955 := caller()
                /// @src 1:1398:1408  "msg.sender"
                let expr_6957 := caller()
                /// @src 1:1410:1418  "receiver"
                let _20 := var_receiver_6927
                let expr_6958 := _20
                /// @src 1:1420:1422  "id"
                let _21 := var_id_6929
                let expr_6959 := _21
                /// @src 1:1424:1430  "amount"
                let _22 := var_amount_6931
                let expr_6960 := _22
                /// @src 1:1377:1431  "Transfer(msg.sender, msg.sender, receiver, id, amount)"
                let _23 := 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859
                let _24 := convert_t_address_to_t_address(expr_6957)
                let _25 := convert_t_address_to_t_address(expr_6958)
                let _26 := convert_t_uint256_to_t_uint256(expr_6959)
                {
                    let _27 := allocate_unbounded()
                    let _28 := abi_encode_tuple_t_address_t_uint256__to_t_address_t_uint256__fromStack(_27 , expr_6955, expr_6960)
                    log4(_27, sub(_28, _27) , _23, _24, _25, _26)
                }/// @src 1:1449:1453  "true"
                let expr_6963 := 0x01
                /// @src 1:1442:1453  "return true"
                var__6934 := expr_6963
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_811(var_currency_804, var_to_806, var_amount_808) {

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                fun_take_833_inner(var_currency_804, var_to_806, var_amount_808)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_int128(value) -> cleaned {
                cleaned := signextend(15, value)
            }

            function negate_wrapping_t_int128(value) -> ret {
                ret := cleanup_t_int128(sub(0, value))
            }

            /// @src 6:13288:13589  "function take(Currency currency, address to, uint256 amount) external onlyWhenUnlocked {..."
            function fun_take_833_inner(var_currency_804, var_to_806, var_amount_808) {

                /// @src 6:13486:13494  "currency"
                let _29 := var_currency_804
                let expr_814 := _29
                /// @src 6:13498:13504  "amount"
                let _30 := var_amount_808
                let expr_815 := _30
                /// @src 6:13498:13513  "amount.toInt128"
                let expr_816_self := expr_815
                /// @src 6:13498:13515  "amount.toInt128()"
                let expr_817 := fun_toInt128_5750(expr_816_self)
                /// @src 6:13497:13516  "(amount.toInt128())"
                let expr_818 := expr_817
                /// @src 6:13496:13516  "-(amount.toInt128())"
                let expr_819 := negate_wrapping_t_int128(expr_818)
                /// @src 6:13518:13528  "msg.sender"
                let expr_821 := caller()
                fun__accountDelta_1156(expr_814, expr_819, expr_821)
                /// @src 6:13543:13551  "currency"
                let _31 := var_currency_804
                let expr_824 := _31
                /// @src 6:13543:13560  "currency.transfer"
                let expr_826_self := expr_824
                /// @src 6:13561:13563  "to"
                let _32 := var_to_806
                let expr_827 := _32
                /// @src 6:13565:13571  "amount"
                let _33 := var_amount_808
                let expr_828 := _33
                fun_transfer_6698(expr_826_self, expr_827, expr_828)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 833
            /// @src 6:13288:13589  "function take(Currency currency, address to, uint256 amount) external onlyWhenUnlocked {..."
            function fun_take_833(var_currency_804, var_to_806, var_amount_808) {

                modifier_onlyWhenUnlocked_811(var_currency_804, var_to_806, var_amount_808)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_uint256() -> ret {
                ret := 0
            }

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_837(var__839) -> _35 {
                _35 := var__839

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                _35 := fun_settle_847_inner(var__839)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 6:13628:13741  "function settle() external payable onlyWhenUnlocked returns (uint256) {..."
            function fun_settle_847_inner(_36) -> var__839 {
                var__839 := _36

                /// @src 6:13723:13733  "msg.sender"
                let expr_843 := caller()
                /// @src 6:13715:13734  "_settle(msg.sender)"
                let expr_844 := fun__settle_1109(expr_843)
                /// @src 6:13708:13734  "return _settle(msg.sender)"
                var__839 := expr_844
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 847
            /// @src 6:13628:13741  "function settle() external payable onlyWhenUnlocked returns (uint256) {..."
            function fun_settle_847() -> var__839 {
                /// @src 6:13689:13696  "uint256"
                let zero_t_uint256_34 := zero_value_for_split_t_uint256()
                var__839 := zero_t_uint256_34

                var__839 := modifier_onlyWhenUnlocked_837(var__839)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_919(var_to_912, var_id_914, var_amount_916) {

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                fun_mint_950_inner(var_to_912, var_id_914, var_amount_916)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 6:14496:14855  "function mint(address to, uint256 id, uint256 amount) external onlyWhenUnlocked {..."
            function fun_mint_950_inner(var_to_912, var_id_914, var_amount_916) {

                /// @src 6:14630:14645  "CurrencyLibrary"
                let expr_924_address := linkersymbol("src/types/Currency.sol:CurrencyLibrary")
                /// @src 6:14653:14655  "id"
                let _37 := var_id_914
                let expr_926 := _37
                /// @src 6:14630:14656  "CurrencyLibrary.fromId(id)"
                let expr_927 := fun_fromId_6818(expr_926)
                /// @src 6:14610:14656  "Currency currency = CurrencyLibrary.fromId(id)"
                let var_currency_923 := expr_927
                /// @src 6:14747:14755  "currency"
                let _38 := var_currency_923
                let expr_930 := _38
                /// @src 6:14759:14765  "amount"
                let _39 := var_amount_916
                let expr_931 := _39
                /// @src 6:14759:14774  "amount.toInt128"
                let expr_932_self := expr_931
                /// @src 6:14759:14776  "amount.toInt128()"
                let expr_933 := fun_toInt128_5750(expr_932_self)
                /// @src 6:14758:14777  "(amount.toInt128())"
                let expr_934 := expr_933
                /// @src 6:14757:14777  "-(amount.toInt128())"
                let expr_935 := negate_wrapping_t_int128(expr_934)
                /// @src 6:14779:14789  "msg.sender"
                let expr_937 := caller()
                fun__accountDelta_1156(expr_930, expr_935, expr_937)
                /// @src 6:14810:14812  "to"
                let _40 := var_to_912
                let expr_941 := _40
                /// @src 6:14814:14822  "currency"
                let _41 := var_currency_923
                let expr_942 := _41
                /// @src 6:14814:14827  "currency.toId"
                let expr_943_self := expr_942
                /// @src 6:14814:14829  "currency.toId()"
                let expr_944 := fun_toId_6798(expr_943_self)
                /// @src 6:14831:14837  "amount"
                let _42 := var_amount_916
                let expr_945 := _42
                fun__mint_7160(expr_941, expr_944, expr_945)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 950
            /// @src 6:14496:14855  "function mint(address to, uint256 id, uint256 amount) external onlyWhenUnlocked {..."
            function fun_mint_950(var_to_912, var_id_914, var_amount_916) {

                modifier_onlyWhenUnlocked_919(var_to_912, var_id_914, var_amount_916)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_bytes32() -> ret {
                ret := 0
            }

            /// @ast-id 1306
            /// @src 3:337:516  "function extsload(bytes32 slot) external view returns (bytes32) {..."
            function fun_extsload_1306(var_slot_1299) -> var__1302 {
                /// @src 3:392:399  "bytes32"
                let zero_t_bytes32_43 := zero_value_for_split_t_bytes32()
                var__1302 := zero_t_bytes32_43

                /// @src 3:411:510  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, sload(var_slot_1299))
                    return(0, 0x20)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311() -> ret {
                ret := 0
            }

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_694(var_delta_699, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length) -> _45 {
                _45 := var_delta_699

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                _45 := modifier_noDelegateCall_696(var_delta_699, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1413
            /// @src 5:1169:1245  "modifier noDelegateCall() {..."
            function modifier_noDelegateCall_696(var_delta_699, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length) -> _46 {
                _46 := var_delta_699

                fun_checkNotDelegateCall_1405()
                /// @src 5:1237:1238  "_"
                _46 := fun_donate_768_inner(var_delta_699, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function read_from_memoryt_contract$_IHooks_$1840(ptr) -> returnValue {

                let value := cleanup_t_contract$_IHooks_$1840(mload(ptr))

                returnValue :=

                value

            }

            function convert_t_bytes32_to_t_bytes32(value) -> converted {
                converted := cleanup_t_bytes32(value)
            }

            function abi_encode_tuple_t_uint256_t_uint256__to_t_uint256_t_uint256__fromStack(headStart , value0, value1) -> tail {
                tail := add(headStart, 64)

                abi_encode_t_uint256_to_t_uint256_fromStack(value0,  add(headStart, 0))

                abi_encode_t_uint256_to_t_uint256_fromStack(value1,  add(headStart, 32))

            }

            /// @src 6:12025:12757  "function donate(PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_donate_768_inner(_47, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length) -> var_delta_699 {
                var_delta_699 := _47

                /// @src 6:12252:12255  "key"
                let _48_mpos := var_key_685_mpos
                let expr_704_mpos := _48_mpos
                /// @src 6:12252:12260  "key.toId"
                let expr_705_self_mpos := expr_704_mpos
                /// @src 6:12252:12262  "key.toId()"
                let expr_706 := fun_toId_6838(expr_705_self_mpos)
                /// @src 6:12236:12262  "PoolId poolId = key.toId()"
                let var_poolId_703 := expr_706
                /// @src 6:12307:12313  "poolId"
                let _49 := var_poolId_703
                let expr_714 := _49
                /// @src 6:12298:12314  "_getPool(poolId)"
                let expr_715_slot := fun__getPool_1203(expr_714)
                /// @src 6:12272:12314  "Pool.State storage pool = _getPool(poolId)"
                let var_pool_712_slot := expr_715_slot
                /// @src 6:12324:12328  "pool"
                let _50_slot := var_pool_712_slot
                let expr_717_slot := _50_slot
                /// @src 6:12324:12349  "pool.checkPoolInitialized"
                let expr_719_self_slot := expr_717_slot
                fun_checkPoolInitialized_5344(expr_719_self_slot)
                /// @src 6:12362:12365  "key"
                let _51_mpos := var_key_685_mpos
                let expr_722_mpos := _51_mpos
                /// @src 6:12362:12371  "key.hooks"
                let _52 := add(expr_722_mpos, 128)
                let _53_address := read_from_memoryt_contract$_IHooks_$1840(_52)
                let expr_725_address := _53_address
                /// @src 6:12362:12384  "key.hooks.beforeDonate"
                let expr_726_self_address := expr_725_address
                /// @src 6:12385:12388  "key"
                let _54_mpos := var_key_685_mpos
                let expr_727_mpos := _54_mpos
                /// @src 6:12390:12397  "amount0"
                let _55 := var_amount0_687
                let expr_728 := _55
                /// @src 6:12399:12406  "amount1"
                let _56 := var_amount1_689
                let expr_729 := _56
                /// @src 6:12408:12416  "hookData"
                let _57_offset := var_hookData_691_offset
                let _57_length := var_hookData_691_length
                let expr_730_offset := _57_offset
                let expr_730_length := _57_length
                fun_beforeDonate_3463(expr_726_self_address, expr_727_mpos, expr_728, expr_729, expr_730_offset, expr_730_length)
                /// @src 6:12436:12440  "pool"
                let _58_slot := var_pool_712_slot
                let expr_734_slot := _58_slot
                /// @src 6:12436:12447  "pool.donate"
                let expr_735_self_slot := expr_734_slot
                /// @src 6:12448:12455  "amount0"
                let _59 := var_amount0_687
                let expr_736 := _59
                /// @src 6:12457:12464  "amount1"
                let _60 := var_amount1_689
                let expr_737 := _60
                /// @src 6:12436:12465  "pool.donate(amount0, amount1)"
                let expr_738 := fun_donate_5102(expr_735_self_slot, expr_736, expr_737)
                /// @src 6:12428:12465  "delta = pool.donate(amount0, amount1)"
                var_delta_699 := expr_738
                let expr_739 := expr_738
                /// @src 6:12501:12504  "key"
                let _61_mpos := var_key_685_mpos
                let expr_742_mpos := _61_mpos
                /// @src 6:12506:12511  "delta"
                let _62 := var_delta_699
                let expr_743 := _62
                /// @src 6:12513:12523  "msg.sender"
                let expr_745 := caller()
                fun__accountPoolBalanceDelta_1187(expr_742_mpos, expr_743, expr_745)
                /// @src 6:12648:12654  "poolId"
                let _63 := var_poolId_703
                let expr_749 := _63
                /// @src 6:12656:12666  "msg.sender"
                let expr_751 := caller()
                /// @src 6:12668:12675  "amount0"
                let _64 := var_amount0_687
                let expr_752 := _64
                /// @src 6:12677:12684  "amount1"
                let _65 := var_amount1_689
                let expr_753 := _65
                /// @src 6:12641:12685  "Donate(poolId, msg.sender, amount0, amount1)"
                let _66 := 0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb
                let _67 := convert_t_bytes32_to_t_bytes32(expr_749)
                let _68 := convert_t_address_to_t_address(expr_751)
                {
                    let _69 := allocate_unbounded()
                    let _70 := abi_encode_tuple_t_uint256_t_uint256__to_t_uint256_t_uint256__fromStack(_69 , expr_752, expr_753)
                    log3(_69, sub(_70, _69) , _66, _67, _68)
                }/// @src 6:12696:12699  "key"
                let _71_mpos := var_key_685_mpos
                let expr_756_mpos := _71_mpos
                /// @src 6:12696:12705  "key.hooks"
                let _72 := add(expr_756_mpos, 128)
                let _73_address := read_from_memoryt_contract$_IHooks_$1840(_72)
                let expr_759_address := _73_address
                /// @src 6:12696:12717  "key.hooks.afterDonate"
                let expr_760_self_address := expr_759_address
                /// @src 6:12718:12721  "key"
                let _74_mpos := var_key_685_mpos
                let expr_761_mpos := _74_mpos
                /// @src 6:12723:12730  "amount0"
                let _75 := var_amount0_687
                let expr_762 := _75
                /// @src 6:12732:12739  "amount1"
                let _76 := var_amount1_689
                let expr_763 := _76
                /// @src 6:12741:12749  "hookData"
                let _77_offset := var_hookData_691_offset
                let _77_length := var_hookData_691_length
                let expr_764_offset := _77_offset
                let expr_764_length := _77_length
                fun_afterDonate_3506(expr_760_self_address, expr_761_mpos, expr_762, expr_763, expr_764_offset, expr_764_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 768
            /// @src 6:12025:12757  "function donate(PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_donate_768(var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length) -> var_delta_699 {
                /// @src 6:12202:12220  "BalanceDelta delta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_44 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_delta_699 := zero_t_userDefinedValueType$_BalanceDelta_$6311_44

                var_delta_699 := modifier_onlyWhenUnlocked_694(var_delta_699, var_key_685_mpos, var_amount0_687, var_amount1_689, var_hookData_691_offset, var_hookData_691_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function extract_from_storage_value_offset_0t_address(slot_value) -> value {
                value := cleanup_from_storage_t_address(shift_right_0_unsigned(slot_value))
            }

            function read_from_storage_split_offset_0_t_address(slot) -> value {
                value := extract_from_storage_value_offset_0t_address(sload(slot))

            }

            function array_storeLengthForEncoding_t_string_memory_ptr_fromStack(pos, length) -> updated_pos {
                mstore(pos, length)
                updated_pos := add(pos, 0x20)
            }

            function store_literal_in_memory_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528(memPtr) {

                mstore(add(memPtr, 0), "UNAUTHORIZED")

            }

            function abi_encode_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528_to_t_string_memory_ptr_fromStack(pos) -> end {
                pos := array_storeLengthForEncoding_t_string_memory_ptr_fromStack(pos, 12)
                store_literal_in_memory_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528(pos)
                end := add(pos, 32)
            }

            function abi_encode_tuple_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528__to_t_string_memory_ptr__fromStack(headStart ) -> tail {
                tail := add(headStart, 32)

                mstore(add(headStart, 0), sub(tail, headStart))
                tail := abi_encode_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528_to_t_string_memory_ptr_fromStack( tail)

            }

            function require_helper_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528(condition ) {
                if iszero(condition)
                {

                    let memPtr := allocate_unbounded()

                    mstore(memPtr, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                    let end := abi_encode_tuple_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528__to_t_string_memory_ptr__fromStack(add(memPtr, 4) )
                    revert(memPtr, sub(end, memPtr))
                }
            }

            /// @ast-id 7269
            /// @src 0:717:819  "modifier onlyOwner() virtual {..."
            function modifier_onlyOwner_1473(var_controller_1470) {

                /// @src 0:764:774  "msg.sender"
                let expr_7261 := caller()
                /// @src 0:778:783  "owner"
                let _78 := read_from_storage_split_offset_0_t_address(0x00)
                let expr_7262 := _78
                /// @src 0:764:783  "msg.sender == owner"
                let expr_7263 := eq(cleanup_t_address(expr_7261), cleanup_t_address(expr_7262))
                /// @src 0:756:800  "require(msg.sender == owner, \"UNAUTHORIZED\")"
                require_helper_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528(expr_7263)
                /// @src 0:811:812  "_"
                fun_setProtocolFeeController_1484_inner(var_controller_1470)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function update_byte_slice_20_shift_0(value, toInsert) -> result {
                let mask := 0xffffffffffffffffffffffffffffffffffffffff
                toInsert := shift_left_0(toInsert)
                value := and(value, not(mask))
                result := or(value, and(toInsert, mask))
            }

            function prepare_store_t_address(value) -> ret {
                ret := value
            }

            function update_storage_value_offset_0t_address_to_t_address(slot, value_0) {
                let convertedValue_0 := convert_t_address_to_t_address(value_0)
                sstore(slot, update_byte_slice_20_shift_0(sload(slot), prepare_store_t_address(convertedValue_0)))
            }

            /// @src 7:1070:1249  "function setProtocolFeeController(address controller) external onlyOwner {..."
            function fun_setProtocolFeeController_1484_inner(var_controller_1470) {

                /// @src 7:1177:1187  "controller"
                let _79 := var_controller_1470
                let expr_1476 := _79
                /// @src 7:1153:1187  "protocolFeeController = controller"
                update_storage_value_offset_0t_address_to_t_address(0x02, expr_1476)
                let expr_1477 := expr_1476
                /// @src 7:1231:1241  "controller"
                let _80 := var_controller_1470
                let expr_1480 := _80
                /// @src 7:1202:1242  "ProtocolFeeControllerUpdated(controller)"
                let _81 := 0xb4bd8ef53df690b9943d3318996006dbb82a25f54719d8c8035b516a2a5b8acc
                let _82 := convert_t_address_to_t_address(expr_1480)
                {
                    let _83 := allocate_unbounded()
                    let _84 := abi_encode_tuple__to__fromStack(_83 )
                    log2(_83, sub(_84, _83) , _81, _82)
                }
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1484
            /// @src 7:1070:1249  "function setProtocolFeeController(address controller) external onlyOwner {..."
            function fun_setProtocolFeeController_1484(var_controller_1470) {

                modifier_onlyOwner_1473(var_controller_1470)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_array$_t_bytes32_$dyn_memory_ptr() -> ret {
                ret := 96
            }

            /// @ast-id 1319
            /// @src 3:552:1533  "function extsload(bytes32 startSlot, uint256 nSlots) external view returns (bytes32[] memory) {..."
            function fun_extsload_1319(var_startSlot_1309, var_nSlots_1311) -> var__1315_mpos {
                /// @src 3:628:644  "bytes32[] memory"
                let zero_t_array$_t_bytes32_$dyn_memory_ptr_85_mpos := zero_value_for_split_t_array$_t_bytes32_$dyn_memory_ptr()
                var__1315_mpos := zero_t_array$_t_bytes32_$dyn_memory_ptr_85_mpos

                /// @src 3:656:1527  "assembly (\"memory-safe\") {..."
                {
                    let usr$memptr := mload(0x40)
                    let usr$start := usr$memptr
                    let usr$length := shl(5, var_nSlots_1311)
                    mstore(usr$memptr, 0x20)
                    mstore(add(usr$memptr, 0x20), var_nSlots_1311)
                    usr$memptr := add(usr$memptr, 0x40)
                    let usr$end := add(usr$memptr, usr$length)
                    for { } 1 { }
                    {
                        mstore(usr$memptr, sload(var_startSlot_1309))
                        usr$memptr := add(usr$memptr, 0x20)
                        var_startSlot_1309 := add(var_startSlot_1309, 1)
                        if iszero(lt(usr$memptr, usr$end)) { break }
                    }
                    return(usr$start, sub(usr$end, usr$start))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_853(var__855, var_recipient_850) -> _87 {
                _87 := var__855

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                _87 := fun_settleFor_862_inner(var__855, var_recipient_850)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 6:13780:13912  "function settleFor(address recipient) external payable onlyWhenUnlocked returns (uint256) {..."
            function fun_settleFor_862_inner(_88, var_recipient_850) -> var__855 {
                var__855 := _88

                /// @src 6:13895:13904  "recipient"
                let _89 := var_recipient_850
                let expr_858 := _89
                /// @src 6:13887:13905  "_settle(recipient)"
                let expr_859 := fun__settle_1109(expr_858)
                /// @src 6:13880:13905  "return _settle(recipient)"
                var__855 := expr_859
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 862
            /// @src 6:13780:13912  "function settleFor(address recipient) external payable onlyWhenUnlocked returns (uint256) {..."
            function fun_settleFor_862(var_recipient_850) -> var__855 {
                /// @src 6:13861:13868  "uint256"
                let zero_t_uint256_86 := zero_value_for_split_t_uint256()
                var__855 := zero_t_uint256_86

                var__855 := modifier_onlyWhenUnlocked_853(var__855, var_recipient_850)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7086
            /// @src 1:2013:2244  "function approve(address spender, uint256 id, uint256 amount) public virtual returns (bool) {..."
            function fun_approve_7086(var_spender_7055, var_id_7057, var_amount_7059) -> var__7062 {
                /// @src 1:2099:2103  "bool"
                let zero_t_bool_90 := zero_value_for_split_t_bool()
                var__7062 := zero_t_bool_90

                /// @src 1:2152:2158  "amount"
                let _91 := var_amount_7059
                let expr_7072 := _91
                /// @src 1:2115:2124  "allowance"
                let _92_slot := 0x05
                let expr_7064_slot := _92_slot
                /// @src 1:2125:2135  "msg.sender"
                let expr_7066 := caller()
                /// @src 1:2115:2136  "allowance[msg.sender]"
                let _93 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(expr_7064_slot,expr_7066)
                let _94_slot := _93
                let expr_7069_slot := _94_slot
                /// @src 1:2137:2144  "spender"
                let _95 := var_spender_7055
                let expr_7067 := _95
                /// @src 1:2115:2145  "allowance[msg.sender][spender]"
                let _96 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7069_slot,expr_7067)
                let _97_slot := _96
                let expr_7070_slot := _97_slot
                /// @src 1:2146:2148  "id"
                let _98 := var_id_7057
                let expr_7068 := _98
                /// @src 1:2115:2149  "allowance[msg.sender][spender][id]"
                let _99 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7070_slot,expr_7068)
                /// @src 1:2115:2158  "allowance[msg.sender][spender][id] = amount"
                update_storage_value_offset_0t_uint256_to_t_uint256(_99, expr_7072)
                let expr_7073 := expr_7072
                /// @src 1:2183:2193  "msg.sender"
                let expr_7077 := caller()
                /// @src 1:2195:2202  "spender"
                let _100 := var_spender_7055
                let expr_7078 := _100
                /// @src 1:2204:2206  "id"
                let _101 := var_id_7057
                let expr_7079 := _101
                /// @src 1:2208:2214  "amount"
                let _102 := var_amount_7059
                let expr_7080 := _102
                /// @src 1:2174:2215  "Approval(msg.sender, spender, id, amount)"
                let _103 := 0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7
                let _104 := convert_t_address_to_t_address(expr_7077)
                let _105 := convert_t_address_to_t_address(expr_7078)
                let _106 := convert_t_uint256_to_t_uint256(expr_7079)
                {
                    let _107 := allocate_unbounded()
                    let _108 := abi_encode_tuple_t_uint256__to_t_uint256__fromStack(_107 , expr_7080)
                    log4(_107, sub(_108, _107) , _103, _104, _105, _106)
                }/// @src 1:2233:2237  "true"
                let expr_7083 := 0x01
                /// @src 1:2226:2237  "return true"
                var__7062 := expr_7083
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_bytes_memory_ptr() -> ret {
                ret := 96
            }

            function convert_t_uint160_to_t_contract$_IUnlockCallback_$2135(value) -> converted {
                converted := convert_t_uint160_to_t_uint160(value)
            }

            function convert_t_address_to_t_contract$_IUnlockCallback_$2135(value) -> converted {
                converted := convert_t_uint160_to_t_contract$_IUnlockCallback_$2135(value)
            }

            function convert_t_contract$_IUnlockCallback_$2135_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            function revert_error_0cc013b6b3b6beabea4e3a74a6d380f0df81852ca99887912475e1f66b2a2c20() {
                revert(0, 0)
            }

            function revert_error_987264b3b1d58a9c7f8255e93e81c77d86d6299019c33110a076957a3e06e2ae() {
                revert(0, 0)
            }

            function array_allocation_size_t_bytes_memory_ptr(length) -> size {
                // Make sure we can allocate memory without overflow
                if gt(length, 0xffffffffffffffff) { panic_error_0x41() }

                size := round_up_to_mul_of_32(length)

                // add length slot
                size := add(size, 0x20)

            }

            function abi_decode_available_length_t_bytes_memory_ptr_fromMemory(src, length, end) -> array {
                array := allocate_memory(array_allocation_size_t_bytes_memory_ptr(length))
                mstore(array, length)
                let dst := add(array, 0x20)
                if gt(add(src, length), end) { revert_error_987264b3b1d58a9c7f8255e93e81c77d86d6299019c33110a076957a3e06e2ae() }
                copy_memory_to_memory_with_cleanup(src, dst, length)
            }

            // bytes
            function abi_decode_t_bytes_memory_ptr_fromMemory(offset, end) -> array {
                if iszero(slt(add(offset, 0x1f), end)) { revert_error_1b9f4a0a5773e33b91aa01db23bf8c55fce1411167c872835e7fa00a4f17d46d() }
                let length := mload(offset)
                array := abi_decode_available_length_t_bytes_memory_ptr_fromMemory(add(offset, 0x20), length, end)
            }

            function abi_decode_tuple_t_bytes_memory_ptr_fromMemory(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := mload(add(headStart, 0))
                    if gt(offset, 0xffffffffffffffff) { revert_error_c1322bf8034eace5e0b5c7295db60986aa89aae5e0ea0873e4689e076861a5db() }

                    value0 := abi_decode_t_bytes_memory_ptr_fromMemory(add(headStart, offset), dataEnd)
                }

            }

            function copy_calldata_to_memory_with_cleanup(src, dst, length) {

                calldatacopy(dst, src, length)
                mstore(add(dst, length), 0)

            }

            // bytes -> bytes
            function abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(start, length, pos) -> end {
                pos := array_storeLengthForEncoding_t_bytes_memory_ptr_fromStack(pos, length)

                copy_calldata_to_memory_with_cleanup(start, pos, length)
                end := add(pos, round_up_to_mul_of_32(length))
            }

            function abi_encode_tuple_t_bytes_calldata_ptr__to_t_bytes_memory_ptr__fromStack(headStart , value0, value1) -> tail {
                tail := add(headStart, 32)

                mstore(add(headStart, 0), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value0, value1,  tail)

            }

            function revert_forward_1() {
                let pos := allocate_unbounded()
                returndatacopy(pos, 0, returndatasize())
                revert(pos, returndatasize())
            }

            function cleanup_t_rational_0_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_0_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_0_by_1(value)))
            }

            /// @ast-id 183
            /// @src 6:5610:6078  "function unlock(bytes calldata data) external override returns (bytes memory result) {..."
            function fun_unlock_183(var_data_132_offset, var_data_132_length) -> var_result_136_mpos {
                /// @src 6:5674:5693  "bytes memory result"
                let zero_t_bytes_memory_ptr_109_mpos := zero_value_for_split_t_bytes_memory_ptr()
                var_result_136_mpos := zero_t_bytes_memory_ptr_109_mpos

                /// @src 6:5709:5713  "Lock"
                let expr_138_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5709:5726  "Lock.isUnlocked()"
                let expr_140 := fun_isUnlocked_3702()
                /// @src 6:5705:5765  "if (Lock.isUnlocked()) AlreadyUnlocked.selector.revertWith()"
                if expr_140 {
                    /// @src 6:5728:5752  "AlreadyUnlocked.selector"
                    let expr_144 := 0x5090d6c600000000000000000000000000000000000000000000000000000000
                    /// @src 6:5728:5763  "AlreadyUnlocked.selector.revertWith"
                    let expr_145_self := expr_144
                    fun_revertWith_2274(expr_145_self)
                    /// @src 6:5705:5765  "if (Lock.isUnlocked()) AlreadyUnlocked.selector.revertWith()"
                }
                /// @src 6:5776:5780  "Lock"
                let expr_149_address := linkersymbol("src/libraries/Lock.sol:Lock")
                fun_unlock_3690()
                /// @src 6:5932:5942  "msg.sender"
                let expr_157 := caller()
                /// @src 6:5916:5943  "IUnlockCallback(msg.sender)"
                let expr_158_address := convert_t_address_to_t_contract$_IUnlockCallback_$2135(expr_157)
                /// @src 6:5916:5958  "IUnlockCallback(msg.sender).unlockCallback"
                let expr_159_address := convert_t_contract$_IUnlockCallback_$2135_to_t_address(expr_158_address)
                let expr_159_functionSelector := 0x91dd7346
                /// @src 6:5959:5963  "data"
                let _110_offset := var_data_132_offset
                let _110_length := var_data_132_length
                let expr_160_offset := _110_offset
                let expr_160_length := _110_length
                /// @src 6:5916:5964  "IUnlockCallback(msg.sender).unlockCallback(data)"

                // storage for arguments and returned data
                let _111 := allocate_unbounded()
                mstore(_111, shift_left_224(expr_159_functionSelector))
                let _112 := abi_encode_tuple_t_bytes_calldata_ptr__to_t_bytes_memory_ptr__fromStack(add(_111, 4) , expr_160_offset, expr_160_length)

                let _113 := call(gas(), expr_159_address,  0,  _111, sub(_112, _111), _111, 0)

                if iszero(_113) { revert_forward_1() }

                let expr_161_mpos
                if _113 {

                    let _114 := returndatasize()
                    returndatacopy(_111, 0, _114)

                    // update freeMemoryPointer according to dynamic return size
                    finalize_allocation(_111, _114)

                    // decode return parameters from external try-call into retVars
                    expr_161_mpos :=  abi_decode_tuple_t_bytes_memory_ptr_fromMemory(_111, add(_111, _114))
                }
                /// @src 6:5907:5964  "result = IUnlockCallback(msg.sender).unlockCallback(data)"
                var_result_136_mpos := expr_161_mpos
                let _115_mpos := var_result_136_mpos
                let expr_162_mpos := _115_mpos
                /// @src 6:5979:5996  "NonzeroDeltaCount"
                let expr_164_address := linkersymbol("src/libraries/NonzeroDeltaCount.sol:NonzeroDeltaCount")
                /// @src 6:5979:6003  "NonzeroDeltaCount.read()"
                let expr_166 := fun_read_3716()
                /// @src 6:6007:6008  "0"
                let expr_167 := 0x00
                /// @src 6:5979:6008  "NonzeroDeltaCount.read() != 0"
                let expr_168 := iszero(eq(cleanup_t_uint256(expr_166), convert_t_rational_0_by_1_to_t_uint256(expr_167)))
                /// @src 6:5975:6050  "if (NonzeroDeltaCount.read() != 0) CurrencyNotSettled.selector.revertWith()"
                if expr_168 {
                    /// @src 6:6010:6037  "CurrencyNotSettled.selector"
                    let expr_172 := 0x5212cba100000000000000000000000000000000000000000000000000000000
                    /// @src 6:6010:6048  "CurrencyNotSettled.selector.revertWith"
                    let expr_173_self := expr_172
                    fun_revertWith_2274(expr_173_self)
                    /// @src 6:5975:6050  "if (NonzeroDeltaCount.read() != 0) CurrencyNotSettled.selector.revertWith()"
                }
                /// @src 6:6060:6064  "Lock"
                let expr_177_address := linkersymbol("src/libraries/Lock.sol:Lock")
                fun_lock_3695()

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function read_from_memoryt_uint24(ptr) -> returnValue {

                let value := cleanup_t_uint24(mload(ptr))

                returnValue :=

                value

            }

            function convert_t_contract$_IHooks_$1840_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            function mapping_index_access_t_mapping$_t_userDefinedValueType$_PoolId_$6825_$_t_struct$_State_$3870_storage_$_of_t_userDefinedValueType$_PoolId_$6825(slot , key) -> dataSlot {
                mstore(0, convert_t_bytes32_to_t_bytes32(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function convert_t_struct$_State_$3870_storage_to_t_struct$_State_$3870_storage_ptr(value) -> converted {
                converted := value
            }

            /// @ast-id 1040
            /// @src 6:15192:15545  "function updateDynamicLPFee(PoolKey memory key, uint24 newDynamicLPFee) external {..."
            function fun_updateDynamicLPFee_1040(var_key_992_mpos, var_newDynamicLPFee_994) {

                /// @src 6:15288:15291  "key"
                let _116_mpos := var_key_992_mpos
                let expr_997_mpos := _116_mpos
                /// @src 6:15288:15295  "key.fee"
                let _117 := add(expr_997_mpos, 64)
                let _118 := read_from_memoryt_uint24(_117)
                let expr_998 := _118
                /// @src 6:15288:15308  "key.fee.isDynamicFee"
                let expr_999_self := expr_998
                /// @src 6:15288:15310  "key.fee.isDynamicFee()"
                let expr_1000 := fun_isDynamicFee_3575(expr_999_self)
                /// @src 6:15287:15310  "!key.fee.isDynamicFee()"
                let expr_1001 := cleanup_t_bool(iszero(expr_1000))
                /// @src 6:15287:15346  "!key.fee.isDynamicFee() || msg.sender != address(key.hooks)"
                let expr_1010 := expr_1001
                if iszero(expr_1010) {
                    /// @src 6:15314:15324  "msg.sender"
                    let expr_1003 := caller()
                    /// @src 6:15336:15339  "key"
                    let _119_mpos := var_key_992_mpos
                    let expr_1006_mpos := _119_mpos
                    /// @src 6:15336:15345  "key.hooks"
                    let _120 := add(expr_1006_mpos, 128)
                    let _121_address := read_from_memoryt_contract$_IHooks_$1840(_120)
                    let expr_1007_address := _121_address
                    /// @src 6:15328:15346  "address(key.hooks)"
                    let expr_1008 := convert_t_contract$_IHooks_$1840_to_t_address(expr_1007_address)
                    /// @src 6:15314:15346  "msg.sender != address(key.hooks)"
                    let expr_1009 := iszero(eq(cleanup_t_address(expr_1003), cleanup_t_address(expr_1008)))
                    /// @src 6:15287:15346  "!key.fee.isDynamicFee() || msg.sender != address(key.hooks)"
                    expr_1010 := expr_1009
                }
                /// @src 6:15283:15425  "if (!key.fee.isDynamicFee() || msg.sender != address(key.hooks)) {..."
                if expr_1010 {
                    /// @src 6:15362:15401  "UnauthorizedDynamicLPFeeUpdate.selector"
                    let expr_1014 := 0x30d2164100000000000000000000000000000000000000000000000000000000
                    /// @src 6:15362:15412  "UnauthorizedDynamicLPFeeUpdate.selector.revertWith"
                    let expr_1015_self := expr_1014
                    fun_revertWith_2274(expr_1015_self)
                    /// @src 6:15283:15425  "if (!key.fee.isDynamicFee() || msg.sender != address(key.hooks)) {..."
                }
                /// @src 6:15434:15449  "newDynamicLPFee"
                let _122 := var_newDynamicLPFee_994
                let expr_1020 := _122
                /// @src 6:15434:15458  "newDynamicLPFee.validate"
                let expr_1022_self := expr_1020
                fun_validate_3608(expr_1022_self)
                /// @src 6:15482:15485  "key"
                let _123_mpos := var_key_992_mpos
                let expr_1028_mpos := _123_mpos
                /// @src 6:15482:15490  "key.toId"
                let expr_1029_self_mpos := expr_1028_mpos
                /// @src 6:15482:15492  "key.toId()"
                let expr_1030 := fun_toId_6838(expr_1029_self_mpos)
                /// @src 6:15470:15492  "PoolId id = key.toId()"
                let var_id_1027 := expr_1030
                /// @src 6:15502:15508  "_pools"
                let _124_slot := 0x06
                let expr_1032_slot := _124_slot
                /// @src 6:15509:15511  "id"
                let _125 := var_id_1027
                let expr_1033 := _125
                /// @src 6:15502:15512  "_pools[id]"
                let _126 := mapping_index_access_t_mapping$_t_userDefinedValueType$_PoolId_$6825_$_t_struct$_State_$3870_storage_$_of_t_userDefinedValueType$_PoolId_$6825(expr_1032_slot,expr_1033)
                let _127_slot := _126
                let expr_1034_slot := _127_slot
                /// @src 6:15502:15521  "_pools[id].setLPFee"
                let expr_1035_self_slot := convert_t_struct$_State_$3870_storage_to_t_struct$_State_$3870_storage_ptr(expr_1034_slot)
                /// @src 6:15522:15537  "newDynamicLPFee"
                let _128 := var_newDynamicLPFee_994
                let expr_1036 := _128
                fun_setLPFee_4022(expr_1035_self_slot, expr_1036)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function update_byte_slice_1_shift_0(value, toInsert) -> result {
                let mask := 255
                toInsert := shift_left_0(toInsert)
                value := and(value, not(mask))
                result := or(value, and(toInsert, mask))
            }

            function convert_t_bool_to_t_bool(value) -> converted {
                converted := cleanup_t_bool(value)
            }

            function prepare_store_t_bool(value) -> ret {
                ret := value
            }

            function update_storage_value_offset_0t_bool_to_t_bool(slot, value_0) {
                let convertedValue_0 := convert_t_bool_to_t_bool(value_0)
                sstore(slot, update_byte_slice_1_shift_0(sload(slot), prepare_store_t_bool(convertedValue_0)))
            }

            /// @ast-id 7114
            /// @src 1:2250:2475  "function setOperator(address operator, bool approved) public virtual returns (bool) {..."
            function fun_setOperator_7114(var_operator_7088, var_approved_7090) -> var__7093 {
                /// @src 1:2328:2332  "bool"
                let zero_t_bool_129 := zero_value_for_split_t_bool()
                var__7093 := zero_t_bool_129

                /// @src 1:2379:2387  "approved"
                let _130 := var_approved_7090
                let expr_7101 := _130
                /// @src 1:2344:2354  "isOperator"
                let _131_slot := 0x03
                let expr_7095_slot := _131_slot
                /// @src 1:2355:2365  "msg.sender"
                let expr_7097 := caller()
                /// @src 1:2344:2366  "isOperator[msg.sender]"
                let _132 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_bool_$_$_of_t_address(expr_7095_slot,expr_7097)
                let _133_slot := _132
                let expr_7099_slot := _133_slot
                /// @src 1:2367:2375  "operator"
                let _134 := var_operator_7088
                let expr_7098 := _134
                /// @src 1:2344:2376  "isOperator[msg.sender][operator]"
                let _135 := mapping_index_access_t_mapping$_t_address_$_t_bool_$_of_t_address(expr_7099_slot,expr_7098)
                /// @src 1:2344:2387  "isOperator[msg.sender][operator] = approved"
                update_storage_value_offset_0t_bool_to_t_bool(_135, expr_7101)
                let expr_7102 := expr_7101
                /// @src 1:2415:2425  "msg.sender"
                let expr_7106 := caller()
                /// @src 1:2427:2435  "operator"
                let _136 := var_operator_7088
                let expr_7107 := _136
                /// @src 1:2437:2445  "approved"
                let _137 := var_approved_7090
                let expr_7108 := _137
                /// @src 1:2403:2446  "OperatorSet(msg.sender, operator, approved)"
                let _138 := 0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267
                let _139 := convert_t_address_to_t_address(expr_7106)
                let _140 := convert_t_address_to_t_address(expr_7107)
                {
                    let _141 := allocate_unbounded()
                    let _142 := abi_encode_tuple_t_bool__to_t_bool__fromStack(_141 , expr_7108)
                    log3(_141, sub(_142, _141) , _138, _139, _140)
                }/// @src 1:2464:2468  "true"
                let expr_7111 := 0x01
                /// @src 1:2457:2468  "return true"
                var__7093 := expr_7111
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_342(var_callerDelta_347, var_feesAccrued_350, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length) -> _145, _146 {
                _145 := var_callerDelta_347
                _146 := var_feesAccrued_350

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                _145, _146 := modifier_noDelegateCall_344(var_callerDelta_347, var_feesAccrued_350, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1413
            /// @src 5:1169:1245  "modifier noDelegateCall() {..."
            function modifier_noDelegateCall_344(var_callerDelta_347, var_feesAccrued_350, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length) -> _147, _148 {
                _147 := var_callerDelta_347
                _148 := var_feesAccrued_350

                fun_checkNotDelegateCall_1405()
                /// @src 5:1237:1238  "_"
                _147, _148 := fun_modifyLiquidity_474_inner(var_callerDelta_347, var_feesAccrued_350, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function read_from_memoryt_int24(ptr) -> returnValue {

                let value := cleanup_t_int24(mload(ptr))

                returnValue :=

                value

            }

            function read_from_memoryt_int256(ptr) -> returnValue {

                let value := cleanup_t_int256(mload(ptr))

                returnValue :=

                value

            }

            function read_from_memoryt_bytes32(ptr) -> returnValue {

                let value := cleanup_t_bytes32(mload(ptr))

                returnValue :=

                value

            }

            function allocate_memory_struct_t_struct$_ModifyLiquidityParams_$4035_storage_ptr() -> memPtr {
                memPtr := allocate_memory(192)
            }

            function write_to_memory_t_address(memPtr, value) {
                mstore(memPtr, cleanup_t_address(value))
            }

            function write_to_memory_t_int24(memPtr, value) {
                mstore(memPtr, cleanup_t_int24(value))
            }

            function write_to_memory_t_int128(memPtr, value) {
                mstore(memPtr, cleanup_t_int128(value))
            }

            function write_to_memory_t_bytes32(memPtr, value) {
                mstore(memPtr, cleanup_t_bytes32(value))
            }

            function abi_encode_t_int256_to_t_int256_fromStack(value, pos) {
                mstore(pos, cleanup_t_int256(value))
            }

            function abi_encode_tuple_t_int24_t_int24_t_int256_t_bytes32__to_t_int24_t_int24_t_int256_t_bytes32__fromStack(headStart , value0, value1, value2, value3) -> tail {
                tail := add(headStart, 128)

                abi_encode_t_int24_to_t_int24_fromStack(value0,  add(headStart, 0))

                abi_encode_t_int24_to_t_int24_fromStack(value1,  add(headStart, 32))

                abi_encode_t_int256_to_t_int256_fromStack(value2,  add(headStart, 64))

                abi_encode_t_bytes32_to_t_bytes32_fromStack(value3,  add(headStart, 96))

            }

            function convert_t_rational_0_by_1_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_rational_0_by_1(value)))
            }

            /// @src 38:1889:1951  "BalanceDelta public constant ZERO_DELTA = BalanceDelta.wrap(0)"
            function constant_ZERO_DELTA_6448() -> ret {
                /// @src 38:1949:1950  "0"
                let expr_6446 := 0x00
                /// @src 38:1931:1951  "BalanceDelta.wrap(0)"
                let expr_6447 := convert_t_rational_0_by_1_to_t_int256(expr_6446)
                let _207 := expr_6447

                ret := _207
            }

            /// @src 6:7601:9346  "function modifyLiquidity(PoolKey memory key, ModifyLiquidityParams memory params, bytes calldata hookData)..."
            function fun_modifyLiquidity_474_inner(_149, _150, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length) -> var_callerDelta_347, var_feesAccrued_350 {
                var_callerDelta_347 := _149
                var_feesAccrued_350 := _150

                /// @src 6:7868:7871  "key"
                let _151_mpos := var_key_334_mpos
                let expr_355_mpos := _151_mpos
                /// @src 6:7868:7876  "key.toId"
                let expr_356_self_mpos := expr_355_mpos
                /// @src 6:7868:7878  "key.toId()"
                let expr_357 := fun_toId_6838(expr_356_self_mpos)
                /// @src 6:7856:7878  "PoolId id = key.toId()"
                let var_id_354 := expr_357
                /// @src 6:7937:7939  "id"
                let _152 := var_id_354
                let expr_365 := _152
                /// @src 6:7928:7940  "_getPool(id)"
                let expr_366_slot := fun__getPool_1203(expr_365)
                /// @src 6:7902:7940  "Pool.State storage pool = _getPool(id)"
                let var_pool_363_slot := expr_366_slot
                /// @src 6:7954:7958  "pool"
                let _153_slot := var_pool_363_slot
                let expr_368_slot := _153_slot
                /// @src 6:7954:7979  "pool.checkPoolInitialized"
                let expr_370_self_slot := expr_368_slot
                fun_checkPoolInitialized_5344(expr_370_self_slot)
                /// @src 6:7996:7999  "key"
                let _154_mpos := var_key_334_mpos
                let expr_373_mpos := _154_mpos
                /// @src 6:7996:8005  "key.hooks"
                let _155 := add(expr_373_mpos, 128)
                let _156_address := read_from_memoryt_contract$_IHooks_$1840(_155)
                let expr_376_address := _156_address
                /// @src 6:7996:8027  "key.hooks.beforeModifyLiquidity"
                let expr_377_self_address := expr_376_address
                /// @src 6:8028:8031  "key"
                let _157_mpos := var_key_334_mpos
                let expr_378_mpos := _157_mpos
                /// @src 6:8033:8039  "params"
                let _158_mpos := var_params_337_mpos
                let expr_379_mpos := _158_mpos
                /// @src 6:8041:8049  "hookData"
                let _159_offset := var_hookData_339_offset
                let _159_length := var_hookData_339_length
                let expr_380_offset := _159_offset
                let expr_380_length := _159_length
                fun_beforeModifyLiquidity_3025(expr_377_self_address, expr_378_mpos, expr_379_mpos, expr_380_offset, expr_380_length)
                /// @src 6:8065:8092  "BalanceDelta principalDelta"
                let var_principalDelta_385
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_160 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_principalDelta_385 := zero_t_userDefinedValueType$_BalanceDelta_$6311_160
                /// @src 6:8138:8142  "pool"
                let _161_slot := var_pool_363_slot
                let expr_390_slot := _161_slot
                /// @src 6:8138:8158  "pool.modifyLiquidity"
                let expr_391_self_slot := expr_390_slot
                /// @src 6:8176:8180  "Pool"
                let expr_392_address := linkersymbol("src/libraries/Pool.sol:Pool")
                /// @src 6:8232:8242  "msg.sender"
                let expr_395 := caller()
                /// @src 6:8275:8281  "params"
                let _162_mpos := var_params_337_mpos
                let expr_396_mpos := _162_mpos
                /// @src 6:8275:8291  "params.tickLower"
                let _163 := add(expr_396_mpos, 0)
                let _164 := read_from_memoryt_int24(_163)
                let expr_397 := _164
                /// @src 6:8324:8330  "params"
                let _165_mpos := var_params_337_mpos
                let expr_398_mpos := _165_mpos
                /// @src 6:8324:8340  "params.tickUpper"
                let _166 := add(expr_398_mpos, 32)
                let _167 := read_from_memoryt_int24(_166)
                let expr_399 := _167
                /// @src 6:8378:8384  "params"
                let _168_mpos := var_params_337_mpos
                let expr_400_mpos := _168_mpos
                /// @src 6:8378:8399  "params.liquidityDelta"
                let _169 := add(expr_400_mpos, 64)
                let _170 := read_from_memoryt_int256(_169)
                let expr_401 := _170
                /// @src 6:8378:8408  "params.liquidityDelta.toInt128"
                let expr_402_self := expr_401
                /// @src 6:8378:8410  "params.liquidityDelta.toInt128()"
                let expr_403 := fun_toInt128_5693(expr_402_self)
                /// @src 6:8445:8448  "key"
                let _171_mpos := var_key_334_mpos
                let expr_404_mpos := _171_mpos
                /// @src 6:8445:8460  "key.tickSpacing"
                let _172 := add(expr_404_mpos, 96)
                let _173 := read_from_memoryt_int24(_172)
                let expr_405 := _173
                /// @src 6:8488:8494  "params"
                let _174_mpos := var_params_337_mpos
                let expr_406_mpos := _174_mpos
                /// @src 6:8488:8499  "params.salt"
                let _175 := add(expr_406_mpos, 96)
                let _176 := read_from_memoryt_bytes32(_175)
                let expr_407 := _176
                /// @src 6:8176:8518  "Pool.ModifyLiquidityParams({..."
                let expr_408_mpos := allocate_memory_struct_t_struct$_ModifyLiquidityParams_$4035_storage_ptr()
                write_to_memory_t_address(add(expr_408_mpos, 0), expr_395)
                write_to_memory_t_int24(add(expr_408_mpos, 32), expr_397)
                write_to_memory_t_int24(add(expr_408_mpos, 64), expr_399)
                write_to_memory_t_int128(add(expr_408_mpos, 96), expr_403)
                write_to_memory_t_int24(add(expr_408_mpos, 128), expr_405)
                write_to_memory_t_bytes32(add(expr_408_mpos, 160), expr_407)
                /// @src 6:8138:8532  "pool.modifyLiquidity(..."
                let expr_409_component_1, expr_409_component_2 := fun_modifyLiquidity_4371(expr_391_self_slot, expr_408_mpos)
                /// @src 6:8106:8532  "(principalDelta, feesAccrued) = pool.modifyLiquidity(..."
                var_feesAccrued_350 := expr_409_component_2
                var_principalDelta_385 := expr_409_component_1
                /// @src 6:8637:8651  "principalDelta"
                let _177 := var_principalDelta_385
                let expr_413 := _177
                /// @src 6:8654:8665  "feesAccrued"
                let _178 := var_feesAccrued_350
                let expr_414 := _178
                /// @src 6:8637:8665  "principalDelta + feesAccrued"
                let expr_415 := fun_add_6366(expr_413, expr_414)
                /// @src 6:8623:8665  "callerDelta = principalDelta + feesAccrued"
                var_callerDelta_347 := expr_415
                let expr_416 := expr_415
                /// @src 6:8817:8819  "id"
                let _179 := var_id_354
                let expr_420 := _179
                /// @src 6:8821:8831  "msg.sender"
                let expr_422 := caller()
                /// @src 6:8833:8839  "params"
                let _180_mpos := var_params_337_mpos
                let expr_423_mpos := _180_mpos
                /// @src 6:8833:8849  "params.tickLower"
                let _181 := add(expr_423_mpos, 0)
                let _182 := read_from_memoryt_int24(_181)
                let expr_424 := _182
                /// @src 6:8851:8857  "params"
                let _183_mpos := var_params_337_mpos
                let expr_425_mpos := _183_mpos
                /// @src 6:8851:8867  "params.tickUpper"
                let _184 := add(expr_425_mpos, 32)
                let _185 := read_from_memoryt_int24(_184)
                let expr_426 := _185
                /// @src 6:8869:8875  "params"
                let _186_mpos := var_params_337_mpos
                let expr_427_mpos := _186_mpos
                /// @src 6:8869:8890  "params.liquidityDelta"
                let _187 := add(expr_427_mpos, 64)
                let _188 := read_from_memoryt_int256(_187)
                let expr_428 := _188
                /// @src 6:8892:8898  "params"
                let _189_mpos := var_params_337_mpos
                let expr_429_mpos := _189_mpos
                /// @src 6:8892:8903  "params.salt"
                let _190 := add(expr_429_mpos, 96)
                let _191 := read_from_memoryt_bytes32(_190)
                let expr_430 := _191
                /// @src 6:8801:8904  "ModifyLiquidity(id, msg.sender, params.tickLower, params.tickUpper, params.liquidityDelta, params.salt)"
                let _192 := 0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec
                let _193 := convert_t_bytes32_to_t_bytes32(expr_420)
                let _194 := convert_t_address_to_t_address(expr_422)
                {
                    let _195 := allocate_unbounded()
                    let _196 := abi_encode_tuple_t_int24_t_int24_t_int256_t_bytes32__to_t_int24_t_int24_t_int256_t_bytes32__fromStack(_195 , expr_424, expr_426, expr_428, expr_430)
                    log3(_195, sub(_196, _195) , _192, _193, _194)
                }/// @src 6:8915:8937  "BalanceDelta hookDelta"
                let var_hookDelta_435
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_197 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_hookDelta_435 := zero_t_userDefinedValueType$_BalanceDelta_$6311_197
                /// @src 6:8974:8977  "key"
                let _198_mpos := var_key_334_mpos
                let expr_440_mpos := _198_mpos
                /// @src 6:8974:8983  "key.hooks"
                let _199 := add(expr_440_mpos, 128)
                let _200_address := read_from_memoryt_contract$_IHooks_$1840(_199)
                let expr_441_address := _200_address
                /// @src 6:8974:9004  "key.hooks.afterModifyLiquidity"
                let expr_442_self_address := expr_441_address
                /// @src 6:9005:9008  "key"
                let _201_mpos := var_key_334_mpos
                let expr_443_mpos := _201_mpos
                /// @src 6:9010:9016  "params"
                let _202_mpos := var_params_337_mpos
                let expr_444_mpos := _202_mpos
                /// @src 6:9018:9029  "callerDelta"
                let _203 := var_callerDelta_347
                let expr_445 := _203
                /// @src 6:9031:9042  "feesAccrued"
                let _204 := var_feesAccrued_350
                let expr_446 := _204
                /// @src 6:9044:9052  "hookData"
                let _205_offset := var_hookData_339_offset
                let _205_length := var_hookData_339_length
                let expr_447_offset := _205_offset
                let expr_447_length := _205_length
                /// @src 6:8974:9053  "key.hooks.afterModifyLiquidity(key, params, callerDelta, feesAccrued, hookData)"
                let expr_448_component_1, expr_448_component_2 := fun_afterModifyLiquidity_3153(expr_442_self_address, expr_443_mpos, expr_444_mpos, expr_445, expr_446, expr_447_offset, expr_447_length)
                /// @src 6:8947:9053  "(callerDelta, hookDelta) = key.hooks.afterModifyLiquidity(key, params, callerDelta, feesAccrued, hookData)"
                var_hookDelta_435 := expr_448_component_2
                var_callerDelta_347 := expr_448_component_1
                /// @src 6:9169:9178  "hookDelta"
                let _206 := var_hookDelta_435
                let expr_451 := _206
                /// @src 6:9182:9201  "BalanceDeltaLibrary"
                let expr_452_address := linkersymbol("src/types/BalanceDelta.sol:BalanceDeltaLibrary")
                /// @src 6:9182:9212  "BalanceDeltaLibrary.ZERO_DELTA"
                let expr_453 := constant_ZERO_DELTA_6448()
                /// @src 6:9169:9212  "hookDelta != BalanceDeltaLibrary.ZERO_DELTA"
                let expr_454 := fun_neq_6439(expr_451, expr_453)
                /// @src 6:9165:9274  "if (hookDelta != BalanceDeltaLibrary.ZERO_DELTA) _accountPoolBalanceDelta(key, hookDelta, address(key.hooks))"
                if expr_454 {
                    /// @src 6:9239:9242  "key"
                    let _208_mpos := var_key_334_mpos
                    let expr_456_mpos := _208_mpos
                    /// @src 6:9244:9253  "hookDelta"
                    let _209 := var_hookDelta_435
                    let expr_457 := _209
                    /// @src 6:9263:9266  "key"
                    let _210_mpos := var_key_334_mpos
                    let expr_460_mpos := _210_mpos
                    /// @src 6:9263:9272  "key.hooks"
                    let _211 := add(expr_460_mpos, 128)
                    let _212_address := read_from_memoryt_contract$_IHooks_$1840(_211)
                    let expr_461_address := _212_address
                    /// @src 6:9255:9273  "address(key.hooks)"
                    let expr_462 := convert_t_contract$_IHooks_$1840_to_t_address(expr_461_address)
                    fun__accountPoolBalanceDelta_1187(expr_456_mpos, expr_457, expr_462)
                    /// @src 6:9165:9274  "if (hookDelta != BalanceDeltaLibrary.ZERO_DELTA) _accountPoolBalanceDelta(key, hookDelta, address(key.hooks))"
                }
                /// @src 6:9310:9313  "key"
                let _213_mpos := var_key_334_mpos
                let expr_467_mpos := _213_mpos
                /// @src 6:9315:9326  "callerDelta"
                let _214 := var_callerDelta_347
                let expr_468 := _214
                /// @src 6:9328:9338  "msg.sender"
                let expr_470 := caller()
                fun__accountPoolBalanceDelta_1187(expr_467_mpos, expr_468, expr_470)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 474
            /// @src 6:7601:9346  "function modifyLiquidity(PoolKey memory key, ModifyLiquidityParams memory params, bytes calldata hookData)..."
            function fun_modifyLiquidity_474(var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length) -> var_callerDelta_347, var_feesAccrued_350 {
                /// @src 6:7790:7814  "BalanceDelta callerDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_143 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_callerDelta_347 := zero_t_userDefinedValueType$_BalanceDelta_$6311_143
                /// @src 6:7816:7840  "BalanceDelta feesAccrued"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_144 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_feesAccrued_350 := zero_t_userDefinedValueType$_BalanceDelta_$6311_144

                var_callerDelta_347, var_feesAccrued_350 := modifier_onlyWhenUnlocked_342(var_callerDelta_347, var_feesAccrued_350, var_key_334_mpos, var_params_337_mpos, var_hookData_339_offset, var_hookData_339_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_int24() -> ret {
                ret := 0
            }

            /// @ast-id 1413
            /// @src 5:1169:1245  "modifier noDelegateCall() {..."
            function modifier_noDelegateCall_192(var_tick_194, var_key_187_mpos, var_sqrtPriceX96_189) -> _216 {
                _216 := var_tick_194

                fun_checkNotDelegateCall_1405()
                /// @src 5:1237:1238  "_"
                _216 := fun_initialize_330_inner(var_tick_194, var_key_187_mpos, var_sqrtPriceX96_189)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_int16(value) -> cleaned {
                cleaned := signextend(1, value)
            }

            function convert_t_int16_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_int16(value)))
            }

            /// @src 36:1633:1691  "int24 internal constant MAX_TICK_SPACING = type(int16).max"
            function constant_MAX_TICK_SPACING_5792() -> ret {
                /// @src 36:1676:1691  "type(int16).max"
                let expr_5791 := 32767
                let _221 := convert_t_int16_to_t_int24(expr_5791)

                ret := _221
            }

            /// @src 6:5125:5192  "int24 private constant MAX_TICK_SPACING = TickMath.MAX_TICK_SPACING"
            function constant_MAX_TICK_SPACING_93() -> ret {
                /// @src 6:5167:5175  "TickMath"
                let expr_91_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 6:5167:5192  "TickMath.MAX_TICK_SPACING"
                let expr_92 := constant_MAX_TICK_SPACING_5792()
                let _222 := expr_92

                ret := _222
            }

            function cleanup_t_rational_1_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1_by_1_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_rational_1_by_1(value)))
            }

            /// @src 36:1468:1512  "int24 internal constant MIN_TICK_SPACING = 1"
            function constant_MIN_TICK_SPACING_5784() -> ret {
                /// @src 36:1511:1512  "1"
                let expr_5783 := 0x01
                let _229 := convert_t_rational_1_by_1_to_t_int24(expr_5783)

                ret := _229
            }

            /// @src 6:5199:5266  "int24 private constant MIN_TICK_SPACING = TickMath.MIN_TICK_SPACING"
            function constant_MIN_TICK_SPACING_97() -> ret {
                /// @src 6:5241:5249  "TickMath"
                let expr_95_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 6:5241:5266  "TickMath.MIN_TICK_SPACING"
                let expr_96 := constant_MIN_TICK_SPACING_5784()
                let _230 := expr_96

                ret := _230
            }

            function read_from_memoryt_userDefinedValueType$_Currency_$6525(ptr) -> returnValue {

                let value := cleanup_t_address(mload(ptr))

                returnValue :=

                value

            }

            function abi_encode_t_uint24_to_t_uint24_fromStack(value, pos) {
                mstore(pos, cleanup_t_uint24(value))
            }

            function abi_encode_t_contract$_IHooks_$1840_to_t_address_fromStack(value, pos) {
                mstore(pos, convert_t_contract$_IHooks_$1840_to_t_address(value))
            }

            function abi_encode_t_uint160_to_t_uint160_fromStack(value, pos) {
                mstore(pos, cleanup_t_uint160(value))
            }

            function abi_encode_tuple_t_uint24_t_int24_t_contract$_IHooks_$1840_t_uint160_t_int24__to_t_uint24_t_int24_t_address_t_uint160_t_int24__fromStack(headStart , value0, value1, value2, value3, value4) -> tail {
                tail := add(headStart, 160)

                abi_encode_t_uint24_to_t_uint24_fromStack(value0,  add(headStart, 0))

                abi_encode_t_int24_to_t_int24_fromStack(value1,  add(headStart, 32))

                abi_encode_t_contract$_IHooks_$1840_to_t_address_fromStack(value2,  add(headStart, 64))

                abi_encode_t_uint160_to_t_uint160_fromStack(value3,  add(headStart, 96))

                abi_encode_t_int24_to_t_int24_fromStack(value4,  add(headStart, 128))

            }

            /// @src 6:6117:7562  "function initialize(PoolKey memory key, uint160 sqrtPriceX96) external noDelegateCall returns (int24 tick) {..."
            function fun_initialize_330_inner(_217, var_key_187_mpos, var_sqrtPriceX96_189) -> var_tick_194 {
                var_tick_194 := _217

                /// @src 6:6341:6344  "key"
                let _218_mpos := var_key_187_mpos
                let expr_196_mpos := _218_mpos
                /// @src 6:6341:6356  "key.tickSpacing"
                let _219 := add(expr_196_mpos, 96)
                let _220 := read_from_memoryt_int24(_219)
                let expr_197 := _220
                /// @src 6:6359:6375  "MAX_TICK_SPACING"
                let expr_198 := constant_MAX_TICK_SPACING_93()
                /// @src 6:6341:6375  "key.tickSpacing > MAX_TICK_SPACING"
                let expr_199 := sgt(cleanup_t_int24(expr_197), cleanup_t_int24(expr_198))
                /// @src 6:6337:6433  "if (key.tickSpacing > MAX_TICK_SPACING) TickSpacingTooLarge.selector.revertWith(key.tickSpacing)"
                if expr_199 {
                    /// @src 6:6377:6405  "TickSpacingTooLarge.selector"
                    let expr_203 := 0xb70024f800000000000000000000000000000000000000000000000000000000
                    /// @src 6:6377:6416  "TickSpacingTooLarge.selector.revertWith"
                    let expr_204_self := expr_203
                    /// @src 6:6417:6420  "key"
                    let _223_mpos := var_key_187_mpos
                    let expr_205_mpos := _223_mpos
                    /// @src 6:6417:6432  "key.tickSpacing"
                    let _224 := add(expr_205_mpos, 96)
                    let _225 := read_from_memoryt_int24(_224)
                    let expr_206 := _225
                    fun_revertWith_2294(expr_204_self, expr_206)
                    /// @src 6:6337:6433  "if (key.tickSpacing > MAX_TICK_SPACING) TickSpacingTooLarge.selector.revertWith(key.tickSpacing)"
                }
                /// @src 6:6447:6450  "key"
                let _226_mpos := var_key_187_mpos
                let expr_210_mpos := _226_mpos
                /// @src 6:6447:6462  "key.tickSpacing"
                let _227 := add(expr_210_mpos, 96)
                let _228 := read_from_memoryt_int24(_227)
                let expr_211 := _228
                /// @src 6:6465:6481  "MIN_TICK_SPACING"
                let expr_212 := constant_MIN_TICK_SPACING_97()
                /// @src 6:6447:6481  "key.tickSpacing < MIN_TICK_SPACING"
                let expr_213 := slt(cleanup_t_int24(expr_211), cleanup_t_int24(expr_212))
                /// @src 6:6443:6539  "if (key.tickSpacing < MIN_TICK_SPACING) TickSpacingTooSmall.selector.revertWith(key.tickSpacing)"
                if expr_213 {
                    /// @src 6:6483:6511  "TickSpacingTooSmall.selector"
                    let expr_217 := 0xe9e9058800000000000000000000000000000000000000000000000000000000
                    /// @src 6:6483:6522  "TickSpacingTooSmall.selector.revertWith"
                    let expr_218_self := expr_217
                    /// @src 6:6523:6526  "key"
                    let _231_mpos := var_key_187_mpos
                    let expr_219_mpos := _231_mpos
                    /// @src 6:6523:6538  "key.tickSpacing"
                    let _232 := add(expr_219_mpos, 96)
                    let _233 := read_from_memoryt_int24(_232)
                    let expr_220 := _233
                    fun_revertWith_2294(expr_218_self, expr_220)
                    /// @src 6:6443:6539  "if (key.tickSpacing < MIN_TICK_SPACING) TickSpacingTooSmall.selector.revertWith(key.tickSpacing)"
                }
                /// @src 6:6553:6556  "key"
                let _234_mpos := var_key_187_mpos
                let expr_224_mpos := _234_mpos
                /// @src 6:6553:6566  "key.currency0"
                let _235 := add(expr_224_mpos, 0)
                let _236 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_235)
                let expr_225 := _236
                /// @src 6:6570:6573  "key"
                let _237_mpos := var_key_187_mpos
                let expr_226_mpos := _237_mpos
                /// @src 6:6570:6583  "key.currency1"
                let _238 := add(expr_226_mpos, 32)
                let _239 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_238)
                let expr_227 := _239
                /// @src 6:6553:6583  "key.currency0 >= key.currency1"
                let expr_228 := fun_greaterThanOrEqualTo_6624(expr_225, expr_227)
                /// @src 6:6549:6751  "if (key.currency0 >= key.currency1) {..."
                if expr_228 {
                    /// @src 6:6599:6635  "CurrenciesOutOfOrderOrEqual.selector"
                    let expr_232 := 0x6e6c983000000000000000000000000000000000000000000000000000000000
                    /// @src 6:6599:6646  "CurrenciesOutOfOrderOrEqual.selector.revertWith"
                    let expr_233_self := expr_232
                    /// @src 6:6680:6683  "key"
                    let _240_mpos := var_key_187_mpos
                    let expr_236_mpos := _240_mpos
                    /// @src 6:6680:6693  "key.currency0"
                    let _241 := add(expr_236_mpos, 0)
                    let _242 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_241)
                    let expr_237 := _242
                    /// @src 6:6664:6694  "Currency.unwrap(key.currency0)"
                    let expr_238 := convert_t_address_to_t_address(expr_237)
                    /// @src 6:6712:6715  "key"
                    let _243_mpos := var_key_187_mpos
                    let expr_241_mpos := _243_mpos
                    /// @src 6:6712:6725  "key.currency1"
                    let _244 := add(expr_241_mpos, 32)
                    let _245 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_244)
                    let expr_242 := _245
                    /// @src 6:6696:6726  "Currency.unwrap(key.currency1)"
                    let expr_243 := convert_t_address_to_t_address(expr_242)
                    fun_revertWith_2340(expr_233_self, expr_238, expr_243)
                    /// @src 6:6549:6751  "if (key.currency0 >= key.currency1) {..."
                }
                /// @src 6:6765:6768  "key"
                let _246_mpos := var_key_187_mpos
                let expr_248_mpos := _246_mpos
                /// @src 6:6765:6774  "key.hooks"
                let _247 := add(expr_248_mpos, 128)
                let _248_address := read_from_memoryt_contract$_IHooks_$1840(_247)
                let expr_249_address := _248_address
                /// @src 6:6765:6793  "key.hooks.isValidHookAddress"
                let expr_250_self_address := expr_249_address
                /// @src 6:6794:6797  "key"
                let _249_mpos := var_key_187_mpos
                let expr_251_mpos := _249_mpos
                /// @src 6:6794:6801  "key.fee"
                let _250 := add(expr_251_mpos, 64)
                let _251 := read_from_memoryt_uint24(_250)
                let expr_252 := _251
                /// @src 6:6765:6802  "key.hooks.isValidHookAddress(key.fee)"
                let expr_253 := fun_isValidHookAddress_2760(expr_250_self_address, expr_252)
                /// @src 6:6764:6802  "!key.hooks.isValidHookAddress(key.fee)"
                let expr_254 := cleanup_t_bool(iszero(expr_253))
                /// @src 6:6760:6869  "if (!key.hooks.isValidHookAddress(key.fee)) Hooks.HookAddressNotValid.selector.revertWith(address(key.hooks))"
                if expr_254 {
                    /// @src 6:6804:6809  "Hooks"
                    let expr_255_address := linkersymbol("src/libraries/Hooks.sol:Hooks")
                    /// @src 6:6804:6838  "Hooks.HookAddressNotValid.selector"
                    let expr_260 := 0xe65af6a000000000000000000000000000000000000000000000000000000000
                    /// @src 6:6804:6849  "Hooks.HookAddressNotValid.selector.revertWith"
                    let expr_261_self := expr_260
                    /// @src 6:6858:6861  "key"
                    let _252_mpos := var_key_187_mpos
                    let expr_264_mpos := _252_mpos
                    /// @src 6:6858:6867  "key.hooks"
                    let _253 := add(expr_264_mpos, 128)
                    let _254_address := read_from_memoryt_contract$_IHooks_$1840(_253)
                    let expr_265_address := _254_address
                    /// @src 6:6850:6868  "address(key.hooks)"
                    let expr_266 := convert_t_contract$_IHooks_$1840_to_t_address(expr_265_address)
                    fun_revertWith_2284(expr_261_self, expr_266)
                    /// @src 6:6760:6869  "if (!key.hooks.isValidHookAddress(key.fee)) Hooks.HookAddressNotValid.selector.revertWith(address(key.hooks))"
                }
                /// @src 6:6895:6898  "key"
                let _255_mpos := var_key_187_mpos
                let expr_272_mpos := _255_mpos
                /// @src 6:6895:6902  "key.fee"
                let _256 := add(expr_272_mpos, 64)
                let _257 := read_from_memoryt_uint24(_256)
                let expr_273 := _257
                /// @src 6:6895:6918  "key.fee.getInitialLPFee"
                let expr_274_self := expr_273
                /// @src 6:6895:6920  "key.fee.getInitialLPFee()"
                let expr_275 := fun_getInitialLPFee_3630(expr_274_self)
                /// @src 6:6880:6920  "uint24 lpFee = key.fee.getInitialLPFee()"
                let var_lpFee_271 := expr_275
                /// @src 6:6931:6934  "key"
                let _258_mpos := var_key_187_mpos
                let expr_277_mpos := _258_mpos
                /// @src 6:6931:6940  "key.hooks"
                let _259 := add(expr_277_mpos, 128)
                let _260_address := read_from_memoryt_contract$_IHooks_$1840(_259)
                let expr_280_address := _260_address
                /// @src 6:6931:6957  "key.hooks.beforeInitialize"
                let expr_281_self_address := expr_280_address
                /// @src 6:6958:6961  "key"
                let _261_mpos := var_key_187_mpos
                let expr_282_mpos := _261_mpos
                /// @src 6:6963:6975  "sqrtPriceX96"
                let _262 := var_sqrtPriceX96_189
                let expr_283 := _262
                fun_beforeInitialize_2912(expr_281_self_address, expr_282_mpos, expr_283)
                /// @src 6:6999:7002  "key"
                let _263_mpos := var_key_187_mpos
                let expr_289_mpos := _263_mpos
                /// @src 6:6999:7007  "key.toId"
                let expr_290_self_mpos := expr_289_mpos
                /// @src 6:6999:7009  "key.toId()"
                let expr_291 := fun_toId_6838(expr_290_self_mpos)
                /// @src 6:6987:7009  "PoolId id = key.toId()"
                let var_id_288 := expr_291
                /// @src 6:7027:7033  "_pools"
                let _264_slot := 0x06
                let expr_294_slot := _264_slot
                /// @src 6:7034:7036  "id"
                let _265 := var_id_288
                let expr_295 := _265
                /// @src 6:7027:7037  "_pools[id]"
                let _266 := mapping_index_access_t_mapping$_t_userDefinedValueType$_PoolId_$6825_$_t_struct$_State_$3870_storage_$_of_t_userDefinedValueType$_PoolId_$6825(expr_294_slot,expr_295)
                let _267_slot := _266
                let expr_296_slot := _267_slot
                /// @src 6:7027:7048  "_pools[id].initialize"
                let expr_297_self_slot := convert_t_struct$_State_$3870_storage_to_t_struct$_State_$3870_storage_ptr(expr_296_slot)
                /// @src 6:7049:7061  "sqrtPriceX96"
                let _268 := var_sqrtPriceX96_189
                let expr_298 := _268
                /// @src 6:7063:7068  "lpFee"
                let _269 := var_lpFee_271
                let expr_299 := _269
                /// @src 6:7027:7069  "_pools[id].initialize(sqrtPriceX96, lpFee)"
                let expr_300 := fun_initialize_3973(expr_297_self_slot, expr_298, expr_299)
                /// @src 6:7020:7069  "tick = _pools[id].initialize(sqrtPriceX96, lpFee)"
                var_tick_194 := expr_300
                let expr_301 := expr_300
                /// @src 6:7404:7406  "id"
                let _270 := var_id_288
                let expr_304 := _270
                /// @src 6:7408:7411  "key"
                let _271_mpos := var_key_187_mpos
                let expr_305_mpos := _271_mpos
                /// @src 6:7408:7421  "key.currency0"
                let _272 := add(expr_305_mpos, 0)
                let _273 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_272)
                let expr_306 := _273
                /// @src 6:7423:7426  "key"
                let _274_mpos := var_key_187_mpos
                let expr_307_mpos := _274_mpos
                /// @src 6:7423:7436  "key.currency1"
                let _275 := add(expr_307_mpos, 32)
                let _276 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_275)
                let expr_308 := _276
                /// @src 6:7438:7441  "key"
                let _277_mpos := var_key_187_mpos
                let expr_309_mpos := _277_mpos
                /// @src 6:7438:7445  "key.fee"
                let _278 := add(expr_309_mpos, 64)
                let _279 := read_from_memoryt_uint24(_278)
                let expr_310 := _279
                /// @src 6:7447:7450  "key"
                let _280_mpos := var_key_187_mpos
                let expr_311_mpos := _280_mpos
                /// @src 6:7447:7462  "key.tickSpacing"
                let _281 := add(expr_311_mpos, 96)
                let _282 := read_from_memoryt_int24(_281)
                let expr_312 := _282
                /// @src 6:7464:7467  "key"
                let _283_mpos := var_key_187_mpos
                let expr_313_mpos := _283_mpos
                /// @src 6:7464:7473  "key.hooks"
                let _284 := add(expr_313_mpos, 128)
                let _285_address := read_from_memoryt_contract$_IHooks_$1840(_284)
                let expr_314_address := _285_address
                /// @src 6:7475:7487  "sqrtPriceX96"
                let _286 := var_sqrtPriceX96_189
                let expr_315 := _286
                /// @src 6:7489:7493  "tick"
                let _287 := var_tick_194
                let expr_316 := _287
                /// @src 6:7393:7494  "Initialize(id, key.currency0, key.currency1, key.fee, key.tickSpacing, key.hooks, sqrtPriceX96, tick)"
                let _288 := 0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438
                let _289 := convert_t_bytes32_to_t_bytes32(expr_304)
                let _290 := convert_t_address_to_t_address(expr_306)
                let _291 := convert_t_address_to_t_address(expr_308)
                {
                    let _292 := allocate_unbounded()
                    let _293 := abi_encode_tuple_t_uint24_t_int24_t_contract$_IHooks_$1840_t_uint160_t_int24__to_t_uint24_t_int24_t_address_t_uint160_t_int24__fromStack(_292 , expr_310, expr_312, expr_314_address, expr_315, expr_316)
                    log4(_292, sub(_293, _292) , _288, _289, _290, _291)
                }/// @src 6:7505:7508  "key"
                let _294_mpos := var_key_187_mpos
                let expr_319_mpos := _294_mpos
                /// @src 6:7505:7514  "key.hooks"
                let _295 := add(expr_319_mpos, 128)
                let _296_address := read_from_memoryt_contract$_IHooks_$1840(_295)
                let expr_322_address := _296_address
                /// @src 6:7505:7530  "key.hooks.afterInitialize"
                let expr_323_self_address := expr_322_address
                /// @src 6:7531:7534  "key"
                let _297_mpos := var_key_187_mpos
                let expr_324_mpos := _297_mpos
                /// @src 6:7536:7548  "sqrtPriceX96"
                let _298 := var_sqrtPriceX96_189
                let expr_325 := _298
                /// @src 6:7550:7554  "tick"
                let _299 := var_tick_194
                let expr_326 := _299
                fun_afterInitialize_2952(expr_323_self_address, expr_324_mpos, expr_325, expr_326)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 330
            /// @src 6:6117:7562  "function initialize(PoolKey memory key, uint160 sqrtPriceX96) external noDelegateCall returns (int24 tick) {..."
            function fun_initialize_330(var_key_187_mpos, var_sqrtPriceX96_189) -> var_tick_194 {
                /// @src 6:6212:6222  "int24 tick"
                let zero_t_int24_215 := zero_value_for_split_t_int24()
                var_tick_194 := zero_t_int24_215

                var_tick_194 := modifier_noDelegateCall_192(var_tick_194, var_key_187_mpos, var_sqrtPriceX96_189)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_uint24_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_uint24(value)))
            }

            function abi_encode_tuple_t_uint24__to_t_uint24__fromStack(headStart , value0) -> tail {
                tail := add(headStart, 32)

                abi_encode_t_uint24_to_t_uint24_fromStack(value0,  add(headStart, 0))

            }

            /// @ast-id 1538
            /// @src 7:1289:1703  "function setProtocolFee(PoolKey memory key, uint24 newProtocolFee) external {..."
            function fun_setProtocolFee_1538(var_key_1488_mpos, var_newProtocolFee_1490) {

                /// @src 7:1379:1389  "msg.sender"
                let expr_1494 := caller()
                /// @src 7:1393:1414  "protocolFeeController"
                let _300 := read_from_storage_split_offset_0_t_address(0x02)
                let expr_1495 := _300
                /// @src 7:1379:1414  "msg.sender != protocolFeeController"
                let expr_1496 := iszero(eq(cleanup_t_address(expr_1494), cleanup_t_address(expr_1495)))
                /// @src 7:1375:1451  "if (msg.sender != protocolFeeController) InvalidCaller.selector.revertWith()"
                if expr_1496 {
                    /// @src 7:1416:1438  "InvalidCaller.selector"
                    let expr_1500 := 0x48f5c3ed00000000000000000000000000000000000000000000000000000000
                    /// @src 7:1416:1449  "InvalidCaller.selector.revertWith"
                    let expr_1501_self := expr_1500
                    fun_revertWith_2274(expr_1501_self)
                    /// @src 7:1375:1451  "if (msg.sender != protocolFeeController) InvalidCaller.selector.revertWith()"
                }
                /// @src 7:1466:1480  "newProtocolFee"
                let _301 := var_newProtocolFee_1490
                let expr_1505 := _301
                /// @src 7:1466:1499  "newProtocolFee.isValidProtocolFee"
                let expr_1506_self := expr_1505
                /// @src 7:1466:1501  "newProtocolFee.isValidProtocolFee()"
                let expr_1507 := fun_isValidProtocolFee_7442(expr_1506_self)
                /// @src 7:1465:1501  "!newProtocolFee.isValidProtocolFee()"
                let expr_1508 := cleanup_t_bool(iszero(expr_1507))
                /// @src 7:1461:1558  "if (!newProtocolFee.isValidProtocolFee()) ProtocolFeeTooLarge.selector.revertWith(newProtocolFee)"
                if expr_1508 {
                    /// @src 7:1503:1531  "ProtocolFeeTooLarge.selector"
                    let expr_1512 := 0xa7abe2f700000000000000000000000000000000000000000000000000000000
                    /// @src 7:1503:1542  "ProtocolFeeTooLarge.selector.revertWith"
                    let expr_1513_self := expr_1512
                    /// @src 7:1543:1557  "newProtocolFee"
                    let _302 := var_newProtocolFee_1490
                    let expr_1514 := _302
                    /// @src 7:1503:1558  "ProtocolFeeTooLarge.selector.revertWith(newProtocolFee)"
                    let _303 := convert_t_uint24_to_t_uint160(expr_1514)
                    fun_revertWith_2304(expr_1513_self, _303)
                    /// @src 7:1461:1558  "if (!newProtocolFee.isValidProtocolFee()) ProtocolFeeTooLarge.selector.revertWith(newProtocolFee)"
                }
                /// @src 7:1580:1583  "key"
                let _304_mpos := var_key_1488_mpos
                let expr_1521_mpos := _304_mpos
                /// @src 7:1580:1588  "key.toId"
                let expr_1522_self_mpos := expr_1521_mpos
                /// @src 7:1580:1590  "key.toId()"
                let expr_1523 := fun_toId_6838(expr_1522_self_mpos)
                /// @src 7:1568:1590  "PoolId id = key.toId()"
                let var_id_1520 := expr_1523
                /// @src 7:1609:1611  "id"
                let _305 := var_id_1520
                let expr_1526 := _305
                /// @src 7:1600:1612  "_getPool(id)"
                let expr_1527_slot := fun__getPool_1203(expr_1526)
                /// @src 7:1600:1627  "_getPool(id).setProtocolFee"
                let expr_1528_self_slot := expr_1527_slot
                /// @src 7:1628:1642  "newProtocolFee"
                let _306 := var_newProtocolFee_1490
                let expr_1529 := _306
                fun_setProtocolFee_3997(expr_1528_self_slot, expr_1529)
                /// @src 7:1677:1679  "id"
                let _307 := var_id_1520
                let expr_1533 := _307
                /// @src 7:1681:1695  "newProtocolFee"
                let _308 := var_newProtocolFee_1490
                let expr_1534 := _308
                /// @src 7:1658:1696  "ProtocolFeeUpdated(id, newProtocolFee)"
                let _309 := 0xe9c42593e71f84403b84352cd168d693e2c9fcd1fdbcc3feb21d92b43e6696f9
                let _310 := convert_t_bytes32_to_t_bytes32(expr_1533)
                {
                    let _311 := allocate_unbounded()
                    let _312 := abi_encode_tuple_t_uint24__to_t_uint24__fromStack(_311 , expr_1534)
                    log2(_311, sub(_312, _311) , _309, _310)
                }
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_871(var_currency_866, var_amount_868) {

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                fun_clear_909_inner(var_currency_866, var_amount_868)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_int128_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_int128(value)))
            }

            /// @src 6:13951:14457  "function clear(Currency currency, uint256 amount) external onlyWhenUnlocked {..."
            function fun_clear_909_inner(var_currency_866, var_amount_868) {

                /// @src 6:14054:14062  "currency"
                let _313 := var_currency_866
                let expr_875 := _313
                /// @src 6:14054:14071  "currency.getDelta"
                let expr_876_self := expr_875
                /// @src 6:14072:14082  "msg.sender"
                let expr_878 := caller()
                /// @src 6:14054:14083  "currency.getDelta(msg.sender)"
                let expr_879 := fun_getDelta_2172(expr_876_self, expr_878)
                /// @src 6:14037:14083  "int256 current = currency.getDelta(msg.sender)"
                let var_current_874 := expr_879
                /// @src 6:14191:14197  "amount"
                let _314 := var_amount_868
                let expr_883 := _314
                /// @src 6:14191:14206  "amount.toInt128"
                let expr_884_self := expr_883
                /// @src 6:14191:14208  "amount.toInt128()"
                let expr_885 := fun_toInt128_5750(expr_884_self)
                /// @src 6:14170:14208  "int128 amountDelta = amount.toInt128()"
                let var_amountDelta_882 := expr_885
                /// @src 6:14222:14233  "amountDelta"
                let _315 := var_amountDelta_882
                let expr_887 := _315
                /// @src 6:14237:14244  "current"
                let _316 := var_current_874
                let expr_888 := _316
                /// @src 6:14222:14244  "amountDelta != current"
                let expr_889 := iszero(eq(convert_t_int128_to_t_int256(expr_887), cleanup_t_int256(expr_888)))
                /// @src 6:14218:14295  "if (amountDelta != current) MustClearExactPositiveDelta.selector.revertWith()"
                if expr_889 {
                    /// @src 6:14246:14282  "MustClearExactPositiveDelta.selector"
                    let expr_893 := 0xbda73abf00000000000000000000000000000000000000000000000000000000
                    /// @src 6:14246:14293  "MustClearExactPositiveDelta.selector.revertWith"
                    let expr_894_self := expr_893
                    fun_revertWith_2274(expr_894_self)
                    /// @src 6:14218:14295  "if (amountDelta != current) MustClearExactPositiveDelta.selector.revertWith()"
                }
                /// @src 6:14403:14411  "currency"
                let _317 := var_currency_866
                let expr_899 := _317
                /// @src 6:14415:14426  "amountDelta"
                let _318 := var_amountDelta_882
                let expr_900 := _318
                /// @src 6:14414:14427  "(amountDelta)"
                let expr_901 := expr_900
                /// @src 6:14413:14427  "-(amountDelta)"
                let expr_902 := negate_wrapping_t_int128(expr_901)
                /// @src 6:14429:14439  "msg.sender"
                let expr_904 := caller()
                fun__accountDelta_1156(expr_899, expr_902, expr_904)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 909
            /// @src 6:13951:14457  "function clear(Currency currency, uint256 amount) external onlyWhenUnlocked {..."
            function fun_clear_909(var_currency_866, var_amount_868) {

                modifier_onlyWhenUnlocked_871(var_currency_866, var_amount_868)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1608
            /// @src 7:1743:2444  "function collectProtocolFees(address recipient, Currency currency, uint256 amount)..."
            function fun_collectProtocolFees_1608(var_recipient_1541, var_currency_1544, var_amount_1546) -> var_amountCollected_1549 {
                /// @src 7:1860:1883  "uint256 amountCollected"
                let zero_t_uint256_319 := zero_value_for_split_t_uint256()
                var_amountCollected_1549 := zero_t_uint256_319

                /// @src 7:1903:1913  "msg.sender"
                let expr_1552 := caller()
                /// @src 7:1917:1938  "protocolFeeController"
                let _320 := read_from_storage_split_offset_0_t_address(0x02)
                let expr_1553 := _320
                /// @src 7:1903:1938  "msg.sender != protocolFeeController"
                let expr_1554 := iszero(eq(cleanup_t_address(expr_1552), cleanup_t_address(expr_1553)))
                /// @src 7:1899:1975  "if (msg.sender != protocolFeeController) InvalidCaller.selector.revertWith()"
                if expr_1554 {
                    /// @src 7:1940:1962  "InvalidCaller.selector"
                    let expr_1558 := 0x48f5c3ed00000000000000000000000000000000000000000000000000000000
                    /// @src 7:1940:1973  "InvalidCaller.selector.revertWith"
                    let expr_1559_self := expr_1558
                    fun_revertWith_2274(expr_1559_self)
                    /// @src 7:1899:1975  "if (msg.sender != protocolFeeController) InvalidCaller.selector.revertWith()"
                }
                /// @src 7:1990:1998  "currency"
                let _321 := var_currency_1544
                let expr_1563 := _321
                /// @src 7:1990:2012  "currency.isAddressZero"
                let expr_1564_self := expr_1563
                /// @src 7:1990:2014  "currency.isAddressZero()"
                let expr_1565 := fun_isAddressZero_6781(expr_1564_self)
                /// @src 7:1989:2014  "!currency.isAddressZero()"
                let expr_1566 := cleanup_t_bool(iszero(expr_1565))
                /// @src 7:1989:2066  "!currency.isAddressZero() && CurrencyReserves.getSyncedCurrency() == currency"
                let expr_1572 := expr_1566
                if expr_1572 {
                    /// @src 7:2018:2034  "CurrencyReserves"
                    let expr_1567_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                    /// @src 7:2018:2054  "CurrencyReserves.getSyncedCurrency()"
                    let expr_1569 := fun_getSyncedCurrency_2229()
                    /// @src 7:2058:2066  "currency"
                    let _322 := var_currency_1544
                    let expr_1570 := _322
                    /// @src 7:2018:2066  "CurrencyReserves.getSyncedCurrency() == currency"
                    let expr_1571 := fun_equals_6558(expr_1569, expr_1570)
                    /// @src 7:1989:2066  "!currency.isAddressZero() && CurrencyReserves.getSyncedCurrency() == currency"
                    expr_1572 := expr_1571
                }
                /// @src 7:1985:2242  "if (!currency.isAddressZero() && CurrencyReserves.getSyncedCurrency() == currency) {..."
                if expr_1572 {
                    /// @src 7:2184:2218  "ProtocolFeeCurrencySynced.selector"
                    let expr_1576 := 0xc79e594800000000000000000000000000000000000000000000000000000000
                    /// @src 7:2184:2229  "ProtocolFeeCurrencySynced.selector.revertWith"
                    let expr_1577_self := expr_1576
                    fun_revertWith_2274(expr_1577_self)
                    /// @src 7:1985:2242  "if (!currency.isAddressZero() && CurrencyReserves.getSyncedCurrency() == currency) {..."
                }
                /// @src 7:2271:2277  "amount"
                let _323 := var_amount_1546
                let expr_1583 := _323
                /// @src 7:2281:2282  "0"
                let expr_1584 := 0x00
                /// @src 7:2271:2282  "amount == 0"
                let expr_1585 := eq(cleanup_t_uint256(expr_1583), convert_t_rational_0_by_1_to_t_uint256(expr_1584))
                /// @src 7:2270:2283  "(amount == 0)"
                let expr_1586 := expr_1585
                /// @src 7:2270:2324  "(amount == 0) ? protocolFeesAccrued[currency] : amount"
                let expr_1591
                switch expr_1586
                case 0 {
                    /// @src 7:2318:2324  "amount"
                    let _324 := var_amount_1546
                    let expr_1590 := _324
                    /// @src 7:2270:2324  "(amount == 0) ? protocolFeesAccrued[currency] : amount"
                    expr_1591 := expr_1590
                }
                default {
                    /// @src 7:2286:2305  "protocolFeesAccrued"
                    let _325_slot := 0x01
                    let expr_1587_slot := _325_slot
                    /// @src 7:2306:2314  "currency"
                    let _326 := var_currency_1544
                    let expr_1588 := _326
                    /// @src 7:2286:2315  "protocolFeesAccrued[currency]"
                    let _327 := mapping_index_access_t_mapping$_t_userDefinedValueType$_Currency_$6525_$_t_uint256_$_of_t_userDefinedValueType$_Currency_$6525(expr_1587_slot,expr_1588)
                    let _328 := read_from_storage_split_offset_0_t_uint256(_327)
                    let expr_1589 := _328
                    /// @src 7:2270:2324  "(amount == 0) ? protocolFeesAccrued[currency] : amount"
                    expr_1591 := expr_1589
                }
                /// @src 7:2252:2324  "amountCollected = (amount == 0) ? protocolFeesAccrued[currency] : amount"
                var_amountCollected_1549 := expr_1591
                let expr_1592 := expr_1591
                /// @src 7:2367:2382  "amountCollected"
                let _329 := var_amountCollected_1549
                let expr_1597 := _329
                /// @src 7:2334:2353  "protocolFeesAccrued"
                let _330_slot := 0x01
                let expr_1594_slot := _330_slot
                /// @src 7:2354:2362  "currency"
                let _331 := var_currency_1544
                let expr_1595 := _331
                /// @src 7:2334:2363  "protocolFeesAccrued[currency]"
                let _332 := mapping_index_access_t_mapping$_t_userDefinedValueType$_Currency_$6525_$_t_uint256_$_of_t_userDefinedValueType$_Currency_$6525(expr_1594_slot,expr_1595)
                /// @src 7:2334:2382  "protocolFeesAccrued[currency] -= amountCollected"
                let _333 := read_from_storage_split_offset_0_t_uint256(_332)
                let expr_1598 := checked_sub_t_uint256(_333, expr_1597)

                update_storage_value_offset_0t_uint256_to_t_uint256(_332, expr_1598)
                /// @src 7:2392:2400  "currency"
                let _334 := var_currency_1544
                let expr_1600 := _334
                /// @src 7:2392:2409  "currency.transfer"
                let expr_1602_self := expr_1600
                /// @src 7:2410:2419  "recipient"
                let _335 := var_recipient_1541
                let expr_1603 := _335
                /// @src 7:2421:2436  "amountCollected"
                let _336 := var_amountCollected_1549
                let expr_1604 := _336
                fun_transfer_6698(expr_1602_self, expr_1603, expr_1604)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1361
            /// @src 4:563:1600  "function exttload(bytes32[] calldata slots) external view returns (bytes32[] memory) {..."
            function fun_exttload_1361(var_slots_1353_offset, var_slots_1353_length) -> var__1357_mpos {
                /// @src 4:630:646  "bytes32[] memory"
                let zero_t_array$_t_bytes32_$dyn_memory_ptr_337_mpos := zero_value_for_split_t_array$_t_bytes32_$dyn_memory_ptr()
                var__1357_mpos := zero_t_array$_t_bytes32_$dyn_memory_ptr_337_mpos

                /// @src 4:658:1594  "assembly (\"memory-safe\") {..."
                {
                    let usr$memptr := mload(0x40)
                    let usr$start := usr$memptr
                    mstore(usr$memptr, 0x20)
                    mstore(add(usr$memptr, 0x20), var_slots_1353_length)
                    usr$memptr := add(usr$memptr, 0x40)
                    let usr$end := add(usr$memptr, shl(5, var_slots_1353_length))
                    let usr$calldataptr := var_slots_1353_offset
                    for { } 1 { }
                    {
                        mstore(usr$memptr, tload(calldataload(usr$calldataptr)))
                        usr$memptr := add(usr$memptr, 0x20)
                        usr$calldataptr := add(usr$calldataptr, 0x20)
                        if iszero(lt(usr$memptr, usr$end)) { break }
                    }
                    return(usr$start, sub(usr$end, usr$start))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 800
            /// @src 6:12796:13249  "function sync(Currency currency) external {..."
            function fun_sync_800(var_currency_772) {

                /// @src 6:12906:12914  "currency"
                let _338 := var_currency_772
                let expr_775 := _338
                /// @src 6:12906:12928  "currency.isAddressZero"
                let expr_776_self := expr_775
                /// @src 6:12906:12930  "currency.isAddressZero()"
                let expr_777 := fun_isAddressZero_6781(expr_776_self)
                /// @src 6:12902:13243  "if (currency.isAddressZero()) {..."
                switch expr_777
                case 0 {
                    /// @src 6:13135:13143  "currency"
                    let _339 := var_currency_772
                    let expr_786 := _339
                    /// @src 6:13135:13157  "currency.balanceOfSelf"
                    let expr_787_self := expr_786
                    /// @src 6:13135:13159  "currency.balanceOfSelf()"
                    let expr_788 := fun_balanceOfSelf_6732(expr_787_self)
                    /// @src 6:13117:13159  "uint256 balance = currency.balanceOfSelf()"
                    let var_balance_785 := expr_788
                    /// @src 6:13173:13189  "CurrencyReserves"
                    let expr_790_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                    /// @src 6:13214:13222  "currency"
                    let _340 := var_currency_772
                    let expr_793 := _340
                    /// @src 6:13224:13231  "balance"
                    let _341 := var_balance_785
                    let expr_794 := _341
                    fun_syncCurrencyAndReserves_2244(expr_793, expr_794)
                    /// @src 6:12902:13243  "if (currency.isAddressZero()) {..."
                }
                default {
                    /// @src 6:13054:13070  "CurrencyReserves"
                    let expr_778_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                    fun_resetCurrency_2234()
                    /// @src 6:12902:13243  "if (currency.isAddressZero()) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1331
            /// @src 3:1569:2606  "function extsload(bytes32[] calldata slots) external view returns (bytes32[] memory) {..."
            function fun_extsload_1331(var_slots_1323_offset, var_slots_1323_length) -> var__1327_mpos {
                /// @src 3:1636:1652  "bytes32[] memory"
                let zero_t_array$_t_bytes32_$dyn_memory_ptr_342_mpos := zero_value_for_split_t_array$_t_bytes32_$dyn_memory_ptr()
                var__1327_mpos := zero_t_array$_t_bytes32_$dyn_memory_ptr_342_mpos

                /// @src 3:1664:2600  "assembly (\"memory-safe\") {..."
                {
                    let usr$memptr := mload(0x40)
                    let usr$start := usr$memptr
                    mstore(usr$memptr, 0x20)
                    mstore(add(usr$memptr, 0x20), var_slots_1323_length)
                    usr$memptr := add(usr$memptr, 0x40)
                    let usr$end := add(usr$memptr, shl(5, var_slots_1323_length))
                    let usr$calldataptr := var_slots_1323_offset
                    for { } 1 { }
                    {
                        mstore(usr$memptr, sload(calldataload(usr$calldataptr)))
                        usr$memptr := add(usr$memptr, 0x20)
                        usr$calldataptr := add(usr$calldataptr, 0x20)
                        if iszero(lt(usr$memptr, usr$end)) { break }
                    }
                    return(usr$start, sub(usr$end, usr$start))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1349
            /// @src 4:348:527  "function exttload(bytes32 slot) external view returns (bytes32) {..."
            function fun_exttload_1349(var_slot_1342) -> var__1345 {
                /// @src 4:403:410  "bytes32"
                let zero_t_bytes32_343 := zero_value_for_split_t_bytes32()
                var__1345 := zero_t_bytes32_343

                /// @src 4:422:521  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, tload(var_slot_1342))
                    return(0, 0x20)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7269
            /// @src 0:717:819  "modifier onlyOwner() virtual {..."
            function modifier_onlyOwner_7292(var_newOwner_7289) {

                /// @src 0:764:774  "msg.sender"
                let expr_7261 := caller()
                /// @src 0:778:783  "owner"
                let _344 := read_from_storage_split_offset_0_t_address(0x00)
                let expr_7262 := _344
                /// @src 0:764:783  "msg.sender == owner"
                let expr_7263 := eq(cleanup_t_address(expr_7261), cleanup_t_address(expr_7262))
                /// @src 0:756:800  "require(msg.sender == owner, \"UNAUTHORIZED\")"
                require_helper_t_stringliteral_269df367cd41cace5897a935d0e0858fe4543b5619d45e09af6b124c1bb3d528(expr_7263)
                /// @src 0:811:812  "_"
                fun_transferOwnership_7305_inner(var_newOwner_7289)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 0:1312:1473  "function transferOwnership(address newOwner) public virtual onlyOwner {..."
            function fun_transferOwnership_7305_inner(var_newOwner_7289) {

                /// @src 0:1400:1408  "newOwner"
                let _345 := var_newOwner_7289
                let expr_7295 := _345
                /// @src 0:1392:1408  "owner = newOwner"
                update_storage_value_offset_0t_address_to_t_address(0x00, expr_7295)
                let expr_7296 := expr_7295
                /// @src 0:1445:1455  "msg.sender"
                let expr_7300 := caller()
                /// @src 0:1457:1465  "newOwner"
                let _346 := var_newOwner_7289
                let expr_7301 := _346
                /// @src 0:1424:1466  "OwnershipTransferred(msg.sender, newOwner)"
                let _347 := 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0
                let _348 := convert_t_address_to_t_address(expr_7300)
                let _349 := convert_t_address_to_t_address(expr_7301)
                {
                    let _350 := allocate_unbounded()
                    let _351 := abi_encode_tuple__to__fromStack(_350 )
                    log3(_350, sub(_351, _350) , _347, _348, _349)
                }
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7305
            /// @src 0:1312:1473  "function transferOwnership(address newOwner) public virtual onlyOwner {..."
            function fun_transferOwnership_7305(var_newOwner_7289) {

                modifier_onlyOwner_7292(var_newOwner_7289)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_486(var_swapDelta_491, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length) -> _353 {
                _353 := var_swapDelta_491

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                _353 := modifier_noDelegateCall_488(var_swapDelta_491, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1413
            /// @src 5:1169:1245  "modifier noDelegateCall() {..."
            function modifier_noDelegateCall_488(var_swapDelta_491, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length) -> _354 {
                _354 := var_swapDelta_491

                fun_checkNotDelegateCall_1405()
                /// @src 5:1237:1238  "_"
                _354 := fun_swap_616_inner(var_swapDelta_491, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_userDefinedValueType$_BeforeSwapDelta_$6473() -> ret {
                ret := 0
            }

            function zero_value_for_split_t_int256() -> ret {
                ret := 0
            }

            function zero_value_for_split_t_uint24() -> ret {
                ret := 0
            }

            function read_from_memoryt_bool(ptr) -> returnValue {

                let value := cleanup_t_bool(mload(ptr))

                returnValue :=

                value

            }

            function read_from_memoryt_uint160(ptr) -> returnValue {

                let value := cleanup_t_uint160(mload(ptr))

                returnValue :=

                value

            }

            function allocate_memory_struct_t_struct$_SwapParams_$4406_storage_ptr() -> memPtr {
                memPtr := allocate_memory(160)
            }

            function write_to_memory_t_int256(memPtr, value) {
                mstore(memPtr, cleanup_t_int256(value))
            }

            function write_to_memory_t_bool(memPtr, value) {
                mstore(memPtr, cleanup_t_bool(value))
            }

            function write_to_memory_t_uint160(memPtr, value) {
                mstore(memPtr, cleanup_t_uint160(value))
            }

            function write_to_memory_t_uint24(memPtr, value) {
                mstore(memPtr, cleanup_t_uint24(value))
            }

            /// @src 6:9385:11071  "function swap(PoolKey memory key, SwapParams memory params, bytes calldata hookData)..."
            function fun_swap_616_inner(_355, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length) -> var_swapDelta_491 {
                var_swapDelta_491 := _355

                /// @src 6:9594:9600  "params"
                let _356_mpos := var_params_481_mpos
                let expr_493_mpos := _356_mpos
                /// @src 6:9594:9616  "params.amountSpecified"
                let _357 := add(expr_493_mpos, 32)
                let _358 := read_from_memoryt_int256(_357)
                let expr_494 := _358
                /// @src 6:9620:9621  "0"
                let expr_495 := 0x00
                /// @src 6:9594:9621  "params.amountSpecified == 0"
                let expr_496 := eq(cleanup_t_int256(expr_494), convert_t_rational_0_by_1_to_t_int256(expr_495))
                /// @src 6:9590:9667  "if (params.amountSpecified == 0) SwapAmountCannotBeZero.selector.revertWith()"
                if expr_496 {
                    /// @src 6:9623:9654  "SwapAmountCannotBeZero.selector"
                    let expr_500 := 0xbe8b850700000000000000000000000000000000000000000000000000000000
                    /// @src 6:9623:9665  "SwapAmountCannotBeZero.selector.revertWith"
                    let expr_501_self := expr_500
                    fun_revertWith_2274(expr_501_self)
                    /// @src 6:9590:9667  "if (params.amountSpecified == 0) SwapAmountCannotBeZero.selector.revertWith()"
                }
                /// @src 6:9689:9692  "key"
                let _359_mpos := var_key_478_mpos
                let expr_508_mpos := _359_mpos
                /// @src 6:9689:9697  "key.toId"
                let expr_509_self_mpos := expr_508_mpos
                /// @src 6:9689:9699  "key.toId()"
                let expr_510 := fun_toId_6838(expr_509_self_mpos)
                /// @src 6:9677:9699  "PoolId id = key.toId()"
                let var_id_507 := expr_510
                /// @src 6:9744:9746  "id"
                let _360 := var_id_507
                let expr_518 := _360
                /// @src 6:9735:9747  "_getPool(id)"
                let expr_519_slot := fun__getPool_1203(expr_518)
                /// @src 6:9709:9747  "Pool.State storage pool = _getPool(id)"
                let var_pool_516_slot := expr_519_slot
                /// @src 6:9757:9761  "pool"
                let _361_slot := var_pool_516_slot
                let expr_521_slot := _361_slot
                /// @src 6:9757:9782  "pool.checkPoolInitialized"
                let expr_523_self_slot := expr_521_slot
                fun_checkPoolInitialized_5344(expr_523_self_slot)
                /// @src 6:9795:9826  "BeforeSwapDelta beforeSwapDelta"
                let var_beforeSwapDelta_528
                let zero_t_userDefinedValueType$_BeforeSwapDelta_$6473_362 := zero_value_for_split_t_userDefinedValueType$_BeforeSwapDelta_$6473()
                var_beforeSwapDelta_528 := zero_t_userDefinedValueType$_BeforeSwapDelta_$6473_362
                /// @src 6:9850:9869  "int256 amountToSwap"
                let var_amountToSwap_531
                let zero_t_int256_363 := zero_value_for_split_t_int256()
                var_amountToSwap_531 := zero_t_int256_363
                /// @src 6:9883:9903  "uint24 lpFeeOverride"
                let var_lpFeeOverride_534
                let zero_t_uint24_364 := zero_value_for_split_t_uint24()
                var_lpFeeOverride_534 := zero_t_uint24_364
                /// @src 6:9966:9969  "key"
                let _365_mpos := var_key_478_mpos
                let expr_540_mpos := _365_mpos
                /// @src 6:9966:9975  "key.hooks"
                let _366 := add(expr_540_mpos, 128)
                let _367_address := read_from_memoryt_contract$_IHooks_$1840(_366)
                let expr_541_address := _367_address
                /// @src 6:9966:9986  "key.hooks.beforeSwap"
                let expr_542_self_address := expr_541_address
                /// @src 6:9987:9990  "key"
                let _368_mpos := var_key_478_mpos
                let expr_543_mpos := _368_mpos
                /// @src 6:9992:9998  "params"
                let _369_mpos := var_params_481_mpos
                let expr_544_mpos := _369_mpos
                /// @src 6:10000:10008  "hookData"
                let _370_offset := var_hookData_483_offset
                let _370_length := var_hookData_483_length
                let expr_545_offset := _370_offset
                let expr_545_length := _370_length
                /// @src 6:9966:10009  "key.hooks.beforeSwap(key, params, hookData)"
                let expr_546_component_1, expr_546_component_2, expr_546_component_3 := fun_beforeSwap_3294(expr_542_self_address, expr_543_mpos, expr_544_mpos, expr_545_offset, expr_545_length)
                /// @src 6:9917:10009  "(amountToSwap, beforeSwapDelta, lpFeeOverride) = key.hooks.beforeSwap(key, params, hookData)"
                var_lpFeeOverride_534 := expr_546_component_3
                var_beforeSwapDelta_528 := expr_546_component_2
                var_amountToSwap_531 := expr_546_component_1
                /// @src 6:10192:10196  "pool"
                let _371_slot := var_pool_516_slot
                let expr_551_slot := _371_slot
                /// @src 6:10214:10216  "id"
                let _372 := var_id_507
                let expr_552 := _372
                /// @src 6:10234:10238  "Pool"
                let expr_553_address := linkersymbol("src/libraries/Pool.sol:Pool")
                /// @src 6:10285:10288  "key"
                let _373_mpos := var_key_478_mpos
                let expr_555_mpos := _373_mpos
                /// @src 6:10285:10300  "key.tickSpacing"
                let _374 := add(expr_555_mpos, 96)
                let _375 := read_from_memoryt_int24(_374)
                let expr_556 := _375
                /// @src 6:10334:10340  "params"
                let _376_mpos := var_params_481_mpos
                let expr_557_mpos := _376_mpos
                /// @src 6:10334:10351  "params.zeroForOne"
                let _377 := add(expr_557_mpos, 0)
                let _378 := read_from_memoryt_bool(_377)
                let expr_558 := _378
                /// @src 6:10390:10402  "amountToSwap"
                let _379 := var_amountToSwap_531
                let expr_559 := _379
                /// @src 6:10443:10449  "params"
                let _380_mpos := var_params_481_mpos
                let expr_560_mpos := _380_mpos
                /// @src 6:10443:10467  "params.sqrtPriceLimitX96"
                let _381 := add(expr_560_mpos, 64)
                let _382 := read_from_memoryt_uint160(_381)
                let expr_561 := _382
                /// @src 6:10504:10517  "lpFeeOverride"
                let _383 := var_lpFeeOverride_534
                let expr_562 := _383
                /// @src 6:10234:10536  "Pool.SwapParams({..."
                let expr_563_mpos := allocate_memory_struct_t_struct$_SwapParams_$4406_storage_ptr()
                write_to_memory_t_int256(add(expr_563_mpos, 0), expr_559)
                write_to_memory_t_int24(add(expr_563_mpos, 32), expr_556)
                write_to_memory_t_bool(add(expr_563_mpos, 64), expr_558)
                write_to_memory_t_uint160(add(expr_563_mpos, 96), expr_561)
                write_to_memory_t_uint24(add(expr_563_mpos, 128), expr_562)
                /// @src 6:10554:10560  "params"
                let _384_mpos := var_params_481_mpos
                let expr_564_mpos := _384_mpos
                /// @src 6:10554:10571  "params.zeroForOne"
                let _385 := add(expr_564_mpos, 0)
                let _386 := read_from_memoryt_bool(_385)
                let expr_565 := _386
                /// @src 6:10554:10603  "params.zeroForOne ? key.currency0 : key.currency1"
                let expr_570
                switch expr_565
                case 0 {
                    /// @src 6:10590:10593  "key"
                    let _387_mpos := var_key_478_mpos
                    let expr_568_mpos := _387_mpos
                    /// @src 6:10590:10603  "key.currency1"
                    let _388 := add(expr_568_mpos, 32)
                    let _389 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_388)
                    let expr_569 := _389
                    /// @src 6:10554:10603  "params.zeroForOne ? key.currency0 : key.currency1"
                    expr_570 := expr_569
                }
                default {
                    /// @src 6:10574:10577  "key"
                    let _390_mpos := var_key_478_mpos
                    let expr_566_mpos := _390_mpos
                    /// @src 6:10574:10587  "key.currency0"
                    let _391 := add(expr_566_mpos, 0)
                    let _392 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_391)
                    let expr_567 := _392
                    /// @src 6:10554:10603  "params.zeroForOne ? key.currency0 : key.currency1"
                    expr_570 := expr_567
                }
                /// @src 6:10169:10632  "_swap(..."
                let expr_571 := fun__swap_681(expr_551_slot, expr_552, expr_563_mpos, expr_570)
                /// @src 6:10157:10632  "swapDelta = _swap(..."
                var_swapDelta_491 := expr_571
                let expr_572 := expr_571
                /// @src 6:10653:10675  "BalanceDelta hookDelta"
                let var_hookDelta_577
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_393 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_hookDelta_577 := zero_t_userDefinedValueType$_BalanceDelta_$6311_393
                /// @src 6:10710:10713  "key"
                let _394_mpos := var_key_478_mpos
                let expr_582_mpos := _394_mpos
                /// @src 6:10710:10719  "key.hooks"
                let _395 := add(expr_582_mpos, 128)
                let _396_address := read_from_memoryt_contract$_IHooks_$1840(_395)
                let expr_583_address := _396_address
                /// @src 6:10710:10729  "key.hooks.afterSwap"
                let expr_584_self_address := expr_583_address
                /// @src 6:10730:10733  "key"
                let _397_mpos := var_key_478_mpos
                let expr_585_mpos := _397_mpos
                /// @src 6:10735:10741  "params"
                let _398_mpos := var_params_481_mpos
                let expr_586_mpos := _398_mpos
                /// @src 6:10743:10752  "swapDelta"
                let _399 := var_swapDelta_491
                let expr_587 := _399
                /// @src 6:10754:10762  "hookData"
                let _400_offset := var_hookData_483_offset
                let _400_length := var_hookData_483_length
                let expr_588_offset := _400_offset
                let expr_588_length := _400_length
                /// @src 6:10764:10779  "beforeSwapDelta"
                let _401 := var_beforeSwapDelta_528
                let expr_589 := _401
                /// @src 6:10710:10780  "key.hooks.afterSwap(key, params, swapDelta, hookData, beforeSwapDelta)"
                let expr_590_component_1, expr_590_component_2 := fun_afterSwap_3420(expr_584_self_address, expr_585_mpos, expr_586_mpos, expr_587, expr_588_offset, expr_588_length, expr_589)
                /// @src 6:10685:10780  "(swapDelta, hookDelta) = key.hooks.afterSwap(key, params, swapDelta, hookData, beforeSwapDelta)"
                var_hookDelta_577 := expr_590_component_2
                var_swapDelta_491 := expr_590_component_1
                /// @src 6:10896:10905  "hookDelta"
                let _402 := var_hookDelta_577
                let expr_593 := _402
                /// @src 6:10909:10928  "BalanceDeltaLibrary"
                let expr_594_address := linkersymbol("src/types/BalanceDelta.sol:BalanceDeltaLibrary")
                /// @src 6:10909:10939  "BalanceDeltaLibrary.ZERO_DELTA"
                let expr_595 := constant_ZERO_DELTA_6448()
                /// @src 6:10896:10939  "hookDelta != BalanceDeltaLibrary.ZERO_DELTA"
                let expr_596 := fun_neq_6439(expr_593, expr_595)
                /// @src 6:10892:11001  "if (hookDelta != BalanceDeltaLibrary.ZERO_DELTA) _accountPoolBalanceDelta(key, hookDelta, address(key.hooks))"
                if expr_596 {
                    /// @src 6:10966:10969  "key"
                    let _403_mpos := var_key_478_mpos
                    let expr_598_mpos := _403_mpos
                    /// @src 6:10971:10980  "hookDelta"
                    let _404 := var_hookDelta_577
                    let expr_599 := _404
                    /// @src 6:10990:10993  "key"
                    let _405_mpos := var_key_478_mpos
                    let expr_602_mpos := _405_mpos
                    /// @src 6:10990:10999  "key.hooks"
                    let _406 := add(expr_602_mpos, 128)
                    let _407_address := read_from_memoryt_contract$_IHooks_$1840(_406)
                    let expr_603_address := _407_address
                    /// @src 6:10982:11000  "address(key.hooks)"
                    let expr_604 := convert_t_contract$_IHooks_$1840_to_t_address(expr_603_address)
                    fun__accountPoolBalanceDelta_1187(expr_598_mpos, expr_599, expr_604)
                    /// @src 6:10892:11001  "if (hookDelta != BalanceDeltaLibrary.ZERO_DELTA) _accountPoolBalanceDelta(key, hookDelta, address(key.hooks))"
                }
                /// @src 6:11037:11040  "key"
                let _408_mpos := var_key_478_mpos
                let expr_609_mpos := _408_mpos
                /// @src 6:11042:11051  "swapDelta"
                let _409 := var_swapDelta_491
                let expr_610 := _409
                /// @src 6:11053:11063  "msg.sender"
                let expr_612 := caller()
                fun__accountPoolBalanceDelta_1187(expr_609_mpos, expr_610, expr_612)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 616
            /// @src 6:9385:11071  "function swap(PoolKey memory key, SwapParams memory params, bytes calldata hookData)..."
            function fun_swap_616(var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length) -> var_swapDelta_491 {
                /// @src 6:9552:9574  "BalanceDelta swapDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_352 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_swapDelta_491 := zero_t_userDefinedValueType$_BalanceDelta_$6311_352

                var_swapDelta_491 := modifier_onlyWhenUnlocked_486(var_swapDelta_491, var_key_478_mpos, var_params_481_mpos, var_hookData_483_offset, var_hookData_483_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 120
            /// @src 6:5387:5502  "modifier onlyWhenUnlocked() {..."
            function modifier_onlyWhenUnlocked_960(var_from_953, var_id_955, var_amount_957) {

                /// @src 6:5430:5434  "Lock"
                let expr_106_address := linkersymbol("src/libraries/Lock.sol:Lock")
                /// @src 6:5430:5447  "Lock.isUnlocked()"
                let expr_108 := fun_isUnlocked_3702()
                /// @src 6:5429:5447  "!Lock.isUnlocked()"
                let expr_109 := cleanup_t_bool(iszero(expr_108))
                /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                if expr_109 {
                    /// @src 6:5449:5471  "ManagerLocked.selector"
                    let expr_113 := 0x54e3ca0d00000000000000000000000000000000000000000000000000000000
                    /// @src 6:5449:5482  "ManagerLocked.selector.revertWith"
                    let expr_114_self := expr_113
                    fun_revertWith_2274(expr_114_self)
                    /// @src 6:5425:5484  "if (!Lock.isUnlocked()) ManagerLocked.selector.revertWith()"
                }
                /// @src 6:5494:5495  "_"
                fun_burn_988_inner(var_from_953, var_id_955, var_amount_957)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 6:14894:15153  "function burn(address from, uint256 id, uint256 amount) external onlyWhenUnlocked {..."
            function fun_burn_988_inner(var_from_953, var_id_955, var_amount_957) {

                /// @src 6:15006:15021  "CurrencyLibrary"
                let expr_965_address := linkersymbol("src/types/Currency.sol:CurrencyLibrary")
                /// @src 6:15029:15031  "id"
                let _410 := var_id_955
                let expr_967 := _410
                /// @src 6:15006:15032  "CurrencyLibrary.fromId(id)"
                let expr_968 := fun_fromId_6818(expr_967)
                /// @src 6:14986:15032  "Currency currency = CurrencyLibrary.fromId(id)"
                let var_currency_964 := expr_968
                /// @src 6:15056:15064  "currency"
                let _411 := var_currency_964
                let expr_971 := _411
                /// @src 6:15066:15072  "amount"
                let _412 := var_amount_957
                let expr_972 := _412
                /// @src 6:15066:15081  "amount.toInt128"
                let expr_973_self := expr_972
                /// @src 6:15066:15083  "amount.toInt128()"
                let expr_974 := fun_toInt128_5750(expr_973_self)
                /// @src 6:15085:15095  "msg.sender"
                let expr_976 := caller()
                fun__accountDelta_1156(expr_971, expr_974, expr_976)
                /// @src 6:15116:15120  "from"
                let _413 := var_from_953
                let expr_980 := _413
                /// @src 6:15122:15130  "currency"
                let _414 := var_currency_964
                let expr_981 := _414
                /// @src 6:15122:15135  "currency.toId"
                let expr_982_self := expr_981
                /// @src 6:15122:15137  "currency.toId()"
                let expr_983 := fun_toId_6798(expr_982_self)
                /// @src 6:15139:15145  "amount"
                let _415 := var_amount_957
                let expr_984 := _415
                fun__burnFrom_1288(expr_980, expr_983, expr_984)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 988
            /// @src 6:14894:15153  "function burn(address from, uint256 id, uint256 amount) external onlyWhenUnlocked {..."
            function fun_burn_988(var_from_953, var_id_955, var_amount_957) {

                modifier_onlyWhenUnlocked_960(var_from_953, var_id_955, var_amount_957)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function extract_from_storage_value_offset_0t_bool(slot_value) -> value {
                value := cleanup_from_storage_t_bool(shift_right_0_unsigned(slot_value))
            }

            function read_from_storage_split_offset_0_t_bool(slot) -> value {
                value := extract_from_storage_value_offset_0t_bool(sload(slot))

            }

            /// @ast-id 7053
            /// @src 1:1466:2007  "function transferFrom(address sender, address receiver, uint256 id, uint256 amount) public virtual returns (bool) {..."
            function fun_transferFrom_7053(var_sender_6968, var_receiver_6970, var_id_6972, var_amount_6974) -> var__6977 {
                /// @src 1:1574:1578  "bool"
                let zero_t_bool_416 := zero_value_for_split_t_bool()
                var__6977 := zero_t_bool_416

                /// @src 1:1594:1604  "msg.sender"
                let expr_6980 := caller()
                /// @src 1:1608:1614  "sender"
                let _417 := var_sender_6968
                let expr_6981 := _417
                /// @src 1:1594:1614  "msg.sender != sender"
                let expr_6982 := iszero(eq(cleanup_t_address(expr_6980), cleanup_t_address(expr_6981)))
                /// @src 1:1594:1649  "msg.sender != sender && !isOperator[sender][msg.sender]"
                let expr_6990 := expr_6982
                if expr_6990 {
                    /// @src 1:1619:1629  "isOperator"
                    let _418_slot := 0x03
                    let expr_6983_slot := _418_slot
                    /// @src 1:1630:1636  "sender"
                    let _419 := var_sender_6968
                    let expr_6984 := _419
                    /// @src 1:1619:1637  "isOperator[sender]"
                    let _420 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_bool_$_$_of_t_address(expr_6983_slot,expr_6984)
                    let _421_slot := _420
                    let expr_6985_slot := _421_slot
                    /// @src 1:1638:1648  "msg.sender"
                    let expr_6987 := caller()
                    /// @src 1:1619:1649  "isOperator[sender][msg.sender]"
                    let _422 := mapping_index_access_t_mapping$_t_address_$_t_bool_$_of_t_address(expr_6985_slot,expr_6987)
                    let _423 := read_from_storage_split_offset_0_t_bool(_422)
                    let expr_6988 := _423
                    /// @src 1:1618:1649  "!isOperator[sender][msg.sender]"
                    let expr_6989 := cleanup_t_bool(iszero(expr_6988))
                    /// @src 1:1594:1649  "msg.sender != sender && !isOperator[sender][msg.sender]"
                    expr_6990 := expr_6989
                }
                /// @src 1:1590:1827  "if (msg.sender != sender && !isOperator[sender][msg.sender]) {..."
                if expr_6990 {
                    /// @src 1:1683:1692  "allowance"
                    let _424_slot := 0x05
                    let expr_6993_slot := _424_slot
                    /// @src 1:1693:1699  "sender"
                    let _425 := var_sender_6968
                    let expr_6994 := _425
                    /// @src 1:1683:1700  "allowance[sender]"
                    let _426 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(expr_6993_slot,expr_6994)
                    let _427_slot := _426
                    let expr_6995_slot := _427_slot
                    /// @src 1:1701:1711  "msg.sender"
                    let expr_6997 := caller()
                    /// @src 1:1683:1712  "allowance[sender][msg.sender]"
                    let _428 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_6995_slot,expr_6997)
                    let _429_slot := _428
                    let expr_6998_slot := _429_slot
                    /// @src 1:1713:1715  "id"
                    let _430 := var_id_6972
                    let expr_6999 := _430
                    /// @src 1:1683:1716  "allowance[sender][msg.sender][id]"
                    let _431 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_6998_slot,expr_6999)
                    let _432 := read_from_storage_split_offset_0_t_uint256(_431)
                    let expr_7000 := _432
                    /// @src 1:1665:1716  "uint256 allowed = allowance[sender][msg.sender][id]"
                    let var_allowed_6992 := expr_7000
                    /// @src 1:1734:1741  "allowed"
                    let _433 := var_allowed_6992
                    let expr_7002 := _433
                    /// @src 1:1745:1762  "type(uint256).max"
                    let expr_7007 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                    /// @src 1:1734:1762  "allowed != type(uint256).max"
                    let expr_7008 := iszero(eq(cleanup_t_uint256(expr_7002), cleanup_t_uint256(expr_7007)))
                    /// @src 1:1730:1816  "if (allowed != type(uint256).max) allowance[sender][msg.sender][id] = allowed - amount"
                    if expr_7008 {
                        /// @src 1:1800:1807  "allowed"
                        let _434 := var_allowed_6992
                        let expr_7017 := _434
                        /// @src 1:1810:1816  "amount"
                        let _435 := var_amount_6974
                        let expr_7018 := _435
                        /// @src 1:1800:1816  "allowed - amount"
                        let expr_7019 := checked_sub_t_uint256(expr_7017, expr_7018)

                        /// @src 1:1764:1773  "allowance"
                        let _436_slot := 0x05
                        let expr_7009_slot := _436_slot
                        /// @src 1:1774:1780  "sender"
                        let _437 := var_sender_6968
                        let expr_7010 := _437
                        /// @src 1:1764:1781  "allowance[sender]"
                        let _438 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(expr_7009_slot,expr_7010)
                        let _439_slot := _438
                        let expr_7014_slot := _439_slot
                        /// @src 1:1782:1792  "msg.sender"
                        let expr_7012 := caller()
                        /// @src 1:1764:1793  "allowance[sender][msg.sender]"
                        let _440 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7014_slot,expr_7012)
                        let _441_slot := _440
                        let expr_7015_slot := _441_slot
                        /// @src 1:1794:1796  "id"
                        let _442 := var_id_6972
                        let expr_7013 := _442
                        /// @src 1:1764:1797  "allowance[sender][msg.sender][id]"
                        let _443 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7015_slot,expr_7013)
                        /// @src 1:1764:1816  "allowance[sender][msg.sender][id] = allowed - amount"
                        update_storage_value_offset_0t_uint256_to_t_uint256(_443, expr_7019)
                        let expr_7020 := expr_7019
                        /// @src 1:1730:1816  "if (allowed != type(uint256).max) allowance[sender][msg.sender][id] = allowed - amount"
                    }
                    /// @src 1:1590:1827  "if (msg.sender != sender && !isOperator[sender][msg.sender]) {..."
                }
                /// @src 1:1862:1868  "amount"
                let _444 := var_amount_6974
                let expr_7030 := _444
                /// @src 1:1837:1846  "balanceOf"
                let _445_slot := 0x04
                let expr_7025_slot := _445_slot
                /// @src 1:1847:1853  "sender"
                let _446 := var_sender_6968
                let expr_7026 := _446
                /// @src 1:1837:1854  "balanceOf[sender]"
                let _447 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7025_slot,expr_7026)
                let _448_slot := _447
                let expr_7028_slot := _448_slot
                /// @src 1:1855:1857  "id"
                let _449 := var_id_6972
                let expr_7027 := _449
                /// @src 1:1837:1858  "balanceOf[sender][id]"
                let _450 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7028_slot,expr_7027)
                /// @src 1:1837:1868  "balanceOf[sender][id] -= amount"
                let _451 := read_from_storage_split_offset_0_t_uint256(_450)
                let expr_7031 := checked_sub_t_uint256(_451, expr_7030)

                update_storage_value_offset_0t_uint256_to_t_uint256(_450, expr_7031)
                /// @src 1:1906:1912  "amount"
                let _452 := var_amount_6974
                let expr_7038 := _452
                /// @src 1:1879:1888  "balanceOf"
                let _453_slot := 0x04
                let expr_7033_slot := _453_slot
                /// @src 1:1889:1897  "receiver"
                let _454 := var_receiver_6970
                let expr_7034 := _454
                /// @src 1:1879:1898  "balanceOf[receiver]"
                let _455 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7033_slot,expr_7034)
                let _456_slot := _455
                let expr_7036_slot := _456_slot
                /// @src 1:1899:1901  "id"
                let _457 := var_id_6972
                let expr_7035 := _457
                /// @src 1:1879:1902  "balanceOf[receiver][id]"
                let _458 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7036_slot,expr_7035)
                /// @src 1:1879:1912  "balanceOf[receiver][id] += amount"
                let _459 := read_from_storage_split_offset_0_t_uint256(_458)
                let expr_7039 := checked_add_t_uint256(_459, expr_7038)

                update_storage_value_offset_0t_uint256_to_t_uint256(_458, expr_7039)
                /// @src 1:1937:1947  "msg.sender"
                let expr_7043 := caller()
                /// @src 1:1949:1955  "sender"
                let _460 := var_sender_6968
                let expr_7044 := _460
                /// @src 1:1957:1965  "receiver"
                let _461 := var_receiver_6970
                let expr_7045 := _461
                /// @src 1:1967:1969  "id"
                let _462 := var_id_6972
                let expr_7046 := _462
                /// @src 1:1971:1977  "amount"
                let _463 := var_amount_6974
                let expr_7047 := _463
                /// @src 1:1928:1978  "Transfer(msg.sender, sender, receiver, id, amount)"
                let _464 := 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859
                let _465 := convert_t_address_to_t_address(expr_7044)
                let _466 := convert_t_address_to_t_address(expr_7045)
                let _467 := convert_t_uint256_to_t_uint256(expr_7046)
                {
                    let _468 := allocate_unbounded()
                    let _469 := abi_encode_tuple_t_address_t_uint256__to_t_address_t_uint256__fromStack(_468 , expr_7043, expr_7047)
                    log4(_468, sub(_469, _468) , _464, _465, _466, _467)
                }/// @src 1:1996:2000  "true"
                let expr_7050 := 0x01
                /// @src 1:1989:2000  "return true"
                var__6977 := expr_7050
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3702
            /// @src 26:767:927  "function isUnlocked() internal view returns (bool unlocked) {..."
            function fun_isUnlocked_3702() -> var_unlocked_3698 {
                /// @src 26:812:825  "bool unlocked"
                let zero_t_bool_470 := zero_value_for_split_t_bool()
                var_unlocked_3698 := zero_t_bool_470

                /// @src 26:837:921  "assembly (\"memory-safe\") {..."
                {
                    var_unlocked_3698 := tload(87100234046427240614499661373387320107015461065347489303548037305558901893923)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2274
            /// @src 19:753:916  "function revertWith(bytes4 selector) internal pure {..."
            function fun_revertWith_2274(var_selector_2269) {

                /// @src 19:814:910  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, var_selector_2269)
                    revert(0, 0x04)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_int128() -> ret {
                ret := 0
            }

            function cleanup_t_rational_170141183460469231731687303715884105728_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_170141183460469231731687303715884105728_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_170141183460469231731687303715884105728_by_1(value)))
            }

            function convert_t_uint256_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_uint256(value)))
            }

            function convert_t_int256_to_t_int128(value) -> converted {
                converted := cleanup_t_int128(identity(cleanup_t_int256(value)))
            }

            /// @ast-id 5750
            /// @src 32:2098:2266  "function toInt128(uint256 x) internal pure returns (int128) {..."
            function fun_toInt128_5750(var_x_5723) -> var__5726 {
                /// @src 32:2150:2156  "int128"
                let zero_t_int128_471 := zero_value_for_split_t_int128()
                var__5726 := zero_t_int128_471

                /// @src 32:2172:2173  "x"
                let _472 := var_x_5723
                let expr_5728 := _472
                /// @src 32:2177:2185  "1 << 127"
                let expr_5731 := 0x80000000000000000000000000000000
                /// @src 32:2172:2185  "x >= 1 << 127"
                let expr_5732 := iszero(lt(cleanup_t_uint256(expr_5728), convert_t_rational_170141183460469231731687303715884105728_by_1_to_t_uint256(expr_5731)))
                /// @src 32:2168:2225  "if (x >= 1 << 127) SafeCastOverflow.selector.revertWith()"
                if expr_5732 {
                    /// @src 32:2187:2212  "SafeCastOverflow.selector"
                    let expr_5736 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
                    /// @src 32:2187:2223  "SafeCastOverflow.selector.revertWith"
                    let expr_5737_self := expr_5736
                    fun_revertWith_2274(expr_5737_self)
                    /// @src 32:2168:2225  "if (x >= 1 << 127) SafeCastOverflow.selector.revertWith()"
                }
                /// @src 32:2256:2257  "x"
                let _473 := var_x_5723
                let expr_5745 := _473
                /// @src 32:2249:2258  "int256(x)"
                let expr_5746 := convert_t_uint256_to_t_int256(expr_5745)
                /// @src 32:2242:2259  "int128(int256(x))"
                let expr_5747 := convert_t_int256_to_t_int128(expr_5746)
                /// @src 32:2235:2259  "return int128(int256(x))"
                var__5726 := expr_5747
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_0_by_1_to_t_int128(value) -> converted {
                converted := cleanup_t_int128(identity(cleanup_t_rational_0_by_1(value)))
            }

            /// @ast-id 1156
            /// @src 6:16552:16908  "function _accountDelta(Currency currency, int128 delta, address target) internal {..."
            function fun__accountDelta_1156(var_currency_1113, var_delta_1115, var_target_1117) {

                /// @src 6:16647:16652  "delta"
                let _474 := var_delta_1115
                let expr_1120 := _474
                /// @src 6:16656:16657  "0"
                let expr_1121 := 0x00
                /// @src 6:16647:16657  "delta == 0"
                let expr_1122 := eq(cleanup_t_int128(expr_1120), convert_t_rational_0_by_1_to_t_int128(expr_1121))
                /// @src 6:16643:16666  "if (delta == 0) return;"
                if expr_1122 {
                    /// @src 6:16659:16666  "return;"
                    leave
                    /// @src 6:16643:16666  "if (delta == 0) return;"
                }
                /// @src 6:16709:16717  "currency"
                let _475 := var_currency_1113
                let expr_1129 := _475
                /// @src 6:16709:16728  "currency.applyDelta"
                let expr_1130_self := expr_1129
                /// @src 6:16729:16735  "target"
                let _476 := var_target_1117
                let expr_1131 := _476
                /// @src 6:16737:16742  "delta"
                let _477 := var_delta_1115
                let expr_1132 := _477
                /// @src 6:16709:16743  "currency.applyDelta(target, delta)"
                let expr_1133_component_1, expr_1133_component_2 := fun_applyDelta_2203(expr_1130_self, expr_1131, expr_1132)
                /// @src 6:16676:16743  "(int256 previous, int256 next) = currency.applyDelta(target, delta)"
                let var_previous_1126 := expr_1133_component_1
                let var_next_1128 := expr_1133_component_2
                /// @src 6:16758:16762  "next"
                let _478 := var_next_1128
                let expr_1135 := _478
                /// @src 6:16766:16767  "0"
                let expr_1136 := 0x00
                /// @src 6:16758:16767  "next == 0"
                let expr_1137 := eq(cleanup_t_int256(expr_1135), convert_t_rational_0_by_1_to_t_int256(expr_1136))
                /// @src 6:16754:16902  "if (next == 0) {..."
                switch expr_1137
                case 0 {
                    /// @src 6:16833:16841  "previous"
                    let _479 := var_previous_1126
                    let expr_1144 := _479
                    /// @src 6:16845:16846  "0"
                    let expr_1145 := 0x00
                    /// @src 6:16833:16846  "previous == 0"
                    let expr_1146 := eq(cleanup_t_int256(expr_1144), convert_t_rational_0_by_1_to_t_int256(expr_1145))
                    /// @src 6:16829:16902  "if (previous == 0) {..."
                    if expr_1146 {
                        /// @src 6:16862:16879  "NonzeroDeltaCount"
                        let expr_1147_address := linkersymbol("src/libraries/NonzeroDeltaCount.sol:NonzeroDeltaCount")
                        fun_increment_3721()
                        /// @src 6:16829:16902  "if (previous == 0) {..."
                    }
                    /// @src 6:16754:16902  "if (next == 0) {..."
                }
                default {
                    /// @src 6:16783:16800  "NonzeroDeltaCount"
                    let expr_1138_address := linkersymbol("src/libraries/NonzeroDeltaCount.sol:NonzeroDeltaCount")
                    fun_decrement_3727()
                    /// @src 6:16754:16902  "if (next == 0) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_0_by_1_to_t_bytes4(value) -> converted {
                converted := cleanup_t_bytes4(shift_left_224(cleanup_t_rational_0_by_1(value)))
            }

            /// @ast-id 6698
            /// @src 40:1472:4345  "function transfer(Currency currency, address to, uint256 amount) internal {..."
            function fun_transfer_6698(var_currency_6645, var_to_6647, var_amount_6649) {

                /// @src 40:1743:1755  "bool success"
                let var_success_6653
                let zero_t_bool_480 := zero_value_for_split_t_bool()
                var_success_6653 := zero_t_bool_480
                /// @src 40:1769:1777  "currency"
                let _481 := var_currency_6645
                let expr_6655 := _481
                /// @src 40:1769:1791  "currency.isAddressZero"
                let expr_6656_self := expr_6655
                /// @src 40:1769:1793  "currency.isAddressZero()"
                let expr_6657 := fun_isAddressZero_6781(expr_6656_self)
                /// @src 40:1765:4339  "if (currency.isAddressZero()) {..."
                switch expr_6657
                case 0 {
                    /// @src 40:2238:4012  "assembly (\"memory-safe\") {..."
                    {
                        let usr$fmp := mload(0x40)
                        mstore(usr$fmp, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
                        mstore(add(usr$fmp, 4), and(var_to_6647, 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(add(usr$fmp, 36), var_amount_6649)
                        var_success_6653 := and(or(and(eq(mload(0), 1), gt(returndatasize(), 31)), iszero(returndatasize())), call(gas(), var_currency_6645, 0, usr$fmp, 68, 0, 32))
                        mstore(usr$fmp, 0)
                        mstore(add(usr$fmp, 0x20), 0)
                        mstore(add(usr$fmp, 0x40), 0)
                    }
                    /// @src 40:4125:4132  "success"
                    let _482 := var_success_6653
                    let expr_6677 := _482
                    /// @src 40:4124:4132  "!success"
                    let expr_6678 := cleanup_t_bool(iszero(expr_6677))
                    /// @src 40:4120:4329  "if (!success) {..."
                    if expr_6678 {
                        /// @src 40:4152:4164  "CustomRevert"
                        let expr_6679_address := linkersymbol("src/libraries/CustomRevert.sol:CustomRevert")
                        /// @src 40:4224:4232  "currency"
                        let _483 := var_currency_6645
                        let expr_6684 := _483
                        /// @src 40:4208:4233  "Currency.unwrap(currency)"
                        let expr_6685 := convert_t_address_to_t_address(expr_6684)
                        /// @src 40:4235:4266  "IERC20Minimal.transfer.selector"
                        let expr_6688 := 0xa9059cbb00000000000000000000000000000000000000000000000000000000
                        /// @src 40:4268:4296  "ERC20TransferFailed.selector"
                        let expr_6690 := 0xf27f64e400000000000000000000000000000000000000000000000000000000
                        fun_bubbleUpAndRevertWith_2357(expr_6685, expr_6688, expr_6690)
                        /// @src 40:4120:4329  "if (!success) {..."
                    }
                    /// @src 40:1765:4339  "if (currency.isAddressZero()) {..."
                }
                default {
                    /// @src 40:1809:1972  "assembly (\"memory-safe\") {..."
                    {
                        var_success_6653 := call(gas(), var_to_6647, var_amount_6649, 0, 0, 0, 0)
                    }
                    /// @src 40:2086:2093  "success"
                    let _484 := var_success_6653
                    let expr_6659 := _484
                    /// @src 40:2085:2093  "!success"
                    let expr_6660 := cleanup_t_bool(iszero(expr_6659))
                    /// @src 40:2081:2208  "if (!success) {..."
                    if expr_6660 {
                        /// @src 40:2113:2125  "CustomRevert"
                        let expr_6661_address := linkersymbol("src/libraries/CustomRevert.sol:CustomRevert")
                        /// @src 40:2148:2150  "to"
                        let _485 := var_to_6647
                        let expr_6664 := _485
                        /// @src 40:2159:2160  "0"
                        let expr_6667 := 0x00
                        /// @src 40:2152:2161  "bytes4(0)"
                        let expr_6668 := convert_t_rational_0_by_1_to_t_bytes4(expr_6667)
                        /// @src 40:2163:2192  "NativeTransferFailed.selector"
                        let expr_6670 := 0xf4b3b1bc00000000000000000000000000000000000000000000000000000000
                        fun_bubbleUpAndRevertWith_2357(expr_6664, expr_6668, expr_6670)
                        /// @src 40:2081:2208  "if (!success) {..."
                    }
                    /// @src 40:1765:4339  "if (currency.isAddressZero()) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1109
            /// @src 6:15649:16474  "function _settle(address recipient) internal returns (uint256 paid) {..."
            function fun__settle_1109(var_recipient_1042) -> var_paid_1045 {
                /// @src 6:15703:15715  "uint256 paid"
                let zero_t_uint256_486 := zero_value_for_split_t_uint256()
                var_paid_1045 := zero_t_uint256_486

                /// @src 6:15747:15763  "CurrencyReserves"
                let expr_1050_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                /// @src 6:15747:15783  "CurrencyReserves.getSyncedCurrency()"
                let expr_1052 := fun_getSyncedCurrency_2229()
                /// @src 6:15727:15783  "Currency currency = CurrencyReserves.getSyncedCurrency()"
                let var_currency_1049 := expr_1052
                /// @src 6:15916:15924  "currency"
                let _487 := var_currency_1049
                let expr_1054 := _487
                /// @src 6:15916:15938  "currency.isAddressZero"
                let expr_1055_self := expr_1054
                /// @src 6:15916:15940  "currency.isAddressZero()"
                let expr_1056 := fun_isAddressZero_6781(expr_1055_self)
                /// @src 6:15912:16406  "if (currency.isAddressZero()) {..."
                switch expr_1056
                case 0 {
                    /// @src 6:16007:16016  "msg.value"
                    let expr_1064 := callvalue()
                    /// @src 6:16019:16020  "0"
                    let expr_1065 := 0x00
                    /// @src 6:16007:16020  "msg.value > 0"
                    let expr_1066 := gt(cleanup_t_uint256(expr_1064), convert_t_rational_0_by_1_to_t_uint256(expr_1065))
                    /// @src 6:16003:16062  "if (msg.value > 0) NonzeroNativeValue.selector.revertWith()"
                    if expr_1066 {
                        /// @src 6:16022:16049  "NonzeroNativeValue.selector"
                        let expr_1070 := 0xb0ec849e00000000000000000000000000000000000000000000000000000000
                        /// @src 6:16022:16060  "NonzeroNativeValue.selector.revertWith"
                        let expr_1071_self := expr_1070
                        fun_revertWith_2274(expr_1071_self)
                        /// @src 6:16003:16062  "if (msg.value > 0) NonzeroNativeValue.selector.revertWith()"
                    }
                    /// @src 6:16204:16220  "CurrencyReserves"
                    let expr_1077_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                    /// @src 6:16204:16240  "CurrencyReserves.getSyncedReserves()"
                    let expr_1079 := fun_getSyncedReserves_2251()
                    /// @src 6:16179:16240  "uint256 reservesBefore = CurrencyReserves.getSyncedReserves()"
                    let var_reservesBefore_1076 := expr_1079
                    /// @src 6:16276:16284  "currency"
                    let _488 := var_currency_1049
                    let expr_1083 := _488
                    /// @src 6:16276:16298  "currency.balanceOfSelf"
                    let expr_1084_self := expr_1083
                    /// @src 6:16276:16300  "currency.balanceOfSelf()"
                    let expr_1085 := fun_balanceOfSelf_6732(expr_1084_self)
                    /// @src 6:16254:16300  "uint256 reservesNow = currency.balanceOfSelf()"
                    let var_reservesNow_1082 := expr_1085
                    /// @src 6:16321:16332  "reservesNow"
                    let _489 := var_reservesNow_1082
                    let expr_1088 := _489
                    /// @src 6:16335:16349  "reservesBefore"
                    let _490 := var_reservesBefore_1076
                    let expr_1089 := _490
                    /// @src 6:16321:16349  "reservesNow - reservesBefore"
                    let expr_1090 := checked_sub_t_uint256(expr_1088, expr_1089)

                    /// @src 6:16314:16349  "paid = reservesNow - reservesBefore"
                    var_paid_1045 := expr_1090
                    let expr_1091 := expr_1090
                    /// @src 6:16363:16379  "CurrencyReserves"
                    let expr_1093_address := linkersymbol("src/libraries/CurrencyReserves.sol:CurrencyReserves")
                    fun_resetCurrency_2234()
                    /// @src 6:15912:16406  "if (currency.isAddressZero()) {..."
                }
                default {
                    /// @src 6:15963:15972  "msg.value"
                    let expr_1059 := callvalue()
                    /// @src 6:15956:15972  "paid = msg.value"
                    var_paid_1045 := expr_1059
                    let expr_1060 := expr_1059
                    /// @src 6:15912:16406  "if (currency.isAddressZero()) {..."
                }
                /// @src 6:16430:16438  "currency"
                let _491 := var_currency_1049
                let expr_1101 := _491
                /// @src 6:16440:16444  "paid"
                let _492 := var_paid_1045
                let expr_1102 := _492
                /// @src 6:16440:16453  "paid.toInt128"
                let expr_1103_self := expr_1102
                /// @src 6:16440:16455  "paid.toInt128()"
                let expr_1104 := fun_toInt128_5750(expr_1103_self)
                /// @src 6:16457:16466  "recipient"
                let _493 := var_recipient_1042
                let expr_1105 := _493
                fun__accountDelta_1156(expr_1101, expr_1104, expr_1105)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_userDefinedValueType$_Currency_$6525() -> ret {
                ret := 0
            }

            function convert_t_uint256_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_uint256(value)))
            }

            /// @ast-id 6818
            /// @src 40:5335:5455  "function fromId(uint256 id) internal pure returns (Currency) {..."
            function fun_fromId_6818(var_id_6800) -> var__6804 {
                /// @src 40:5386:5394  "Currency"
                let zero_t_userDefinedValueType$_Currency_$6525_494 := zero_value_for_split_t_userDefinedValueType$_Currency_$6525()
                var__6804 := zero_t_userDefinedValueType$_Currency_$6525_494

                /// @src 40:5443:5445  "id"
                let _495 := var_id_6800
                let expr_6812 := _495
                /// @src 40:5435:5446  "uint160(id)"
                let expr_6813 := convert_t_uint256_to_t_uint160(expr_6812)
                /// @src 40:5427:5447  "address(uint160(id))"
                let expr_6814 := convert_t_uint160_to_t_address(expr_6813)
                /// @src 40:5413:5448  "Currency.wrap(address(uint160(id)))"
                let expr_6815 := convert_t_address_to_t_address(expr_6814)
                /// @src 40:5406:5448  "return Currency.wrap(address(uint160(id)))"
                var__6804 := expr_6815
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_address_to_t_uint160(value) -> converted {
                converted := convert_t_uint160_to_t_uint160(value)
            }

            function convert_t_uint160_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint160(value)))
            }

            /// @ast-id 6798
            /// @src 40:5069:5192  "function toId(Currency currency) internal pure returns (uint256) {..."
            function fun_toId_6798(var_currency_6784) -> var__6787 {
                /// @src 40:5125:5132  "uint256"
                let zero_t_uint256_496 := zero_value_for_split_t_uint256()
                var__6787 := zero_t_uint256_496

                /// @src 40:5175:5183  "currency"
                let _497 := var_currency_6784
                let expr_6793 := _497
                /// @src 40:5159:5184  "Currency.unwrap(currency)"
                let expr_6794 := convert_t_address_to_t_address(expr_6793)
                /// @src 40:5151:5185  "uint160(Currency.unwrap(currency))"
                let expr_6795 := convert_t_address_to_t_uint160(expr_6794)
                /// @src 40:5144:5185  "return uint160(Currency.unwrap(currency))"
                var__6787 := convert_t_uint160_to_t_uint256(expr_6795)
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_0_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_0_by_1(value)))
            }

            function convert_t_rational_0_by_1_to_t_address(value) -> converted {
                converted := convert_t_rational_0_by_1_to_t_uint160(value)
            }

            /// @ast-id 7160
            /// @src 1:3098:3296  "function _mint(address receiver, uint256 id, uint256 amount) internal virtual {..."
            function fun__mint_7160(var_receiver_7132, var_id_7134, var_amount_7136) {

                /// @src 1:3213:3219  "amount"
                let _498 := var_amount_7136
                let expr_7144 := _498
                /// @src 1:3186:3195  "balanceOf"
                let _499_slot := 0x04
                let expr_7139_slot := _499_slot
                /// @src 1:3196:3204  "receiver"
                let _500 := var_receiver_7132
                let expr_7140 := _500
                /// @src 1:3186:3205  "balanceOf[receiver]"
                let _501 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7139_slot,expr_7140)
                let _502_slot := _501
                let expr_7142_slot := _502_slot
                /// @src 1:3206:3208  "id"
                let _503 := var_id_7134
                let expr_7141 := _503
                /// @src 1:3186:3209  "balanceOf[receiver][id]"
                let _504 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7142_slot,expr_7141)
                /// @src 1:3186:3219  "balanceOf[receiver][id] += amount"
                let _505 := read_from_storage_split_offset_0_t_uint256(_504)
                let expr_7145 := checked_add_t_uint256(_505, expr_7144)

                update_storage_value_offset_0t_uint256_to_t_uint256(_504, expr_7145)
                /// @src 1:3244:3254  "msg.sender"
                let expr_7149 := caller()
                /// @src 1:3264:3265  "0"
                let expr_7152 := 0x00
                /// @src 1:3256:3266  "address(0)"
                let expr_7153 := convert_t_rational_0_by_1_to_t_address(expr_7152)
                /// @src 1:3268:3276  "receiver"
                let _506 := var_receiver_7132
                let expr_7154 := _506
                /// @src 1:3278:3280  "id"
                let _507 := var_id_7134
                let expr_7155 := _507
                /// @src 1:3282:3288  "amount"
                let _508 := var_amount_7136
                let expr_7156 := _508
                /// @src 1:3235:3289  "Transfer(msg.sender, address(0), receiver, id, amount)"
                let _509 := 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859
                let _510 := convert_t_address_to_t_address(expr_7153)
                let _511 := convert_t_address_to_t_address(expr_7154)
                let _512 := convert_t_uint256_to_t_uint256(expr_7155)
                {
                    let _513 := allocate_unbounded()
                    let _514 := abi_encode_tuple_t_address_t_uint256__to_t_address_t_uint256__fromStack(_513 , expr_7149, expr_7156)
                    log4(_513, sub(_514, _513) , _509, _510, _511, _512)
                }
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_contract$_NoDelegateCall_$1414_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            /// @ast-id 1405
            /// @src 5:963:1100  "function checkNotDelegateCall() private view {..."
            function fun_checkNotDelegateCall_1405() {

                /// @src 5:1030:1034  "this"
                let expr_1392_address := address()
                /// @src 5:1022:1035  "address(this)"
                let expr_1393 := convert_t_contract$_NoDelegateCall_$1414_to_t_address(expr_1392_address)
                /// @src 5:1039:1047  "original"
                let _515 := loadimmutable("1375")
                let expr_1394 := _515
                /// @src 5:1022:1047  "address(this) != original"
                let expr_1395 := iszero(eq(cleanup_t_address(expr_1393), cleanup_t_address(expr_1394)))
                /// @src 5:1018:1093  "if (address(this) != original) DelegateCallNotAllowed.selector.revertWith()"
                if expr_1395 {
                    /// @src 5:1049:1080  "DelegateCallNotAllowed.selector"
                    let expr_1399 := 0x0d89438e00000000000000000000000000000000000000000000000000000000
                    /// @src 5:1049:1091  "DelegateCallNotAllowed.selector.revertWith"
                    let expr_1400_self := expr_1399
                    fun_revertWith_2274(expr_1400_self)
                    /// @src 5:1018:1093  "if (address(this) != original) DelegateCallNotAllowed.selector.revertWith()"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_userDefinedValueType$_PoolId_$6825() -> ret {
                ret := 0
            }

            /// @ast-id 6838
            /// @src 41:271:536  "function toId(PoolKey memory poolKey) internal pure returns (PoolId poolId) {..."
            function fun_toId_6838(var_poolKey_6830_mpos) -> var_poolId_6834 {
                /// @src 41:332:345  "PoolId poolId"
                let zero_t_userDefinedValueType$_PoolId_$6825_516 := zero_value_for_split_t_userDefinedValueType$_PoolId_$6825()
                var_poolId_6834 := zero_t_userDefinedValueType$_PoolId_$6825_516

                /// @src 41:357:530  "assembly (\"memory-safe\") {..."
                {
                    var_poolId_6834 := keccak256(var_poolKey_6830_mpos, 0xa0)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1203
            /// @src 6:17304:17419  "function _getPool(PoolId id) internal view override returns (Pool.State storage) {..."
            function fun__getPool_1203(var_id_1191) -> var__1196_slot {

                /// @src 6:17402:17408  "_pools"
                let _517_slot := 0x06
                let expr_1198_slot := _517_slot
                /// @src 6:17409:17411  "id"
                let _518 := var_id_1191
                let expr_1199 := _518
                /// @src 6:17402:17412  "_pools[id]"
                let _519 := mapping_index_access_t_mapping$_t_userDefinedValueType$_PoolId_$6825_$_t_struct$_State_$3870_storage_$_of_t_userDefinedValueType$_PoolId_$6825(expr_1198_slot,expr_1199)
                let _520_slot := _519
                let expr_1200_slot := _520_slot
                /// @src 6:17395:17412  "return _pools[id]"
                var__1196_slot := convert_t_struct$_State_$3870_storage_to_t_struct$_State_$3870_storage_ptr(expr_1200_slot)
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_from_storage_t_userDefinedValueType$_Slot0_$8632(value) -> cleaned {
                cleaned := value
            }

            function extract_from_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632(slot_value) -> value {
                value := cleanup_from_storage_t_userDefinedValueType$_Slot0_$8632(shift_right_0_unsigned(slot_value))
            }

            function read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(slot) -> value {
                value := extract_from_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632(sload(slot))

            }

            /// @ast-id 5344
            /// @src 29:28591:28748  "function checkPoolInitialized(State storage self) internal view {..."
            function fun_checkPoolInitialized_5344(var_self_5326_slot) {

                /// @src 29:28669:28673  "self"
                let _521_slot := var_self_5326_slot
                let expr_5329_slot := _521_slot
                /// @src 29:28669:28679  "self.slot0"
                let _522 := add(expr_5329_slot, 0)
                let _523 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_522)
                let expr_5330 := _523
                /// @src 29:28669:28692  "self.slot0.sqrtPriceX96"
                let expr_5331_self := expr_5330
                /// @src 29:28669:28694  "self.slot0.sqrtPriceX96()"
                let expr_5332 := fun_sqrtPriceX96_8662(expr_5331_self)
                /// @src 29:28698:28699  "0"
                let expr_5333 := 0x00
                /// @src 29:28669:28699  "self.slot0.sqrtPriceX96() == 0"
                let expr_5334 := eq(cleanup_t_uint160(expr_5332), convert_t_rational_0_by_1_to_t_uint160(expr_5333))
                /// @src 29:28665:28741  "if (self.slot0.sqrtPriceX96() == 0) PoolNotInitialized.selector.revertWith()"
                if expr_5334 {
                    /// @src 29:28701:28728  "PoolNotInitialized.selector"
                    let expr_5338 := 0x486aa30700000000000000000000000000000000000000000000000000000000
                    /// @src 29:28701:28739  "PoolNotInitialized.selector.revertWith"
                    let expr_5339_self := expr_5338
                    fun_revertWith_2274(expr_5339_self)
                    /// @src 29:28665:28741  "if (self.slot0.sqrtPriceX96() == 0) PoolNotInitialized.selector.revertWith()"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2875
            /// @src 23:8767:8875  "modifier noSelfCall(IHooks self) {..."
            function modifier_noSelfCall_3437(var_self_3424_address, var_key_3427_mpos, var_amount0_3429, var_amount1_3431, var_hookData_3433_offset, var_hookData_3433_length) {

                /// @src 23:15746:15750  "self"
                let _524_address := var_self_3424_address
                let expr_3436_address := _524_address
                let _525_address := expr_3436_address
                let var_self_2862_address := _525_address

                /// @src 23:8814:8824  "msg.sender"
                let expr_2865 := caller()
                /// @src 23:8836:8840  "self"
                let _526_address := var_self_2862_address
                let expr_2868_address := _526_address
                /// @src 23:8828:8841  "address(self)"
                let expr_2869 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2868_address)
                /// @src 23:8814:8841  "msg.sender != address(self)"
                let expr_2870 := iszero(eq(cleanup_t_address(expr_2865), cleanup_t_address(expr_2869)))
                /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                if expr_2870 {
                    /// @src 23:8857:8858  "_"
                    fun_beforeDonate_3463_inner(var_self_3424_address, var_key_3427_mpos, var_amount0_3429, var_amount1_3431, var_hookData_3433_offset, var_hookData_3433_length)
                    /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_32_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_32_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_32_by_1(value)))
            }

            /// @src 23:1860:1913  "uint160 internal constant BEFORE_DONATE_FLAG = 1 << 5"
            function constant_BEFORE_DONATE_FLAG_2461() -> ret {
                /// @src 23:1907:1913  "1 << 5"
                let expr_2460 := 0x20
                let _528 := convert_t_rational_32_by_1_to_t_uint160(expr_2460)

                ret := _528
            }

            function abi_encode_t_userDefinedValueType$_Currency_$6525_to_t_address(value, pos) {
                mstore(pos, convert_t_address_to_t_address(value))
            }

            function abi_encode_t_uint24_to_t_uint24(value, pos) {
                mstore(pos, cleanup_t_uint24(value))
            }

            function abi_encode_t_int24_to_t_int24(value, pos) {
                mstore(pos, cleanup_t_int24(value))
            }

            function abi_encode_t_contract$_IHooks_$1840_to_t_address(value, pos) {
                mstore(pos, convert_t_contract$_IHooks_$1840_to_t_address(value))
            }

            // struct PoolKey -> struct PoolKey
            function abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value, pos)  {
                let tail := add(pos, 0xa0)

                {
                    // currency0

                    let memberValue0 := mload(add(value, 0x00))
                    abi_encode_t_userDefinedValueType$_Currency_$6525_to_t_address(memberValue0, add(pos, 0x00))
                }

                {
                    // currency1

                    let memberValue0 := mload(add(value, 0x20))
                    abi_encode_t_userDefinedValueType$_Currency_$6525_to_t_address(memberValue0, add(pos, 0x20))
                }

                {
                    // fee

                    let memberValue0 := mload(add(value, 0x40))
                    abi_encode_t_uint24_to_t_uint24(memberValue0, add(pos, 0x40))
                }

                {
                    // tickSpacing

                    let memberValue0 := mload(add(value, 0x60))
                    abi_encode_t_int24_to_t_int24(memberValue0, add(pos, 0x60))
                }

                {
                    // hooks

                    let memberValue0 := mload(add(value, 0x80))
                    abi_encode_t_contract$_IHooks_$1840_to_t_address(memberValue0, add(pos, 0x80))
                }

            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_memory_ptr__fromStack(headStart , value0, value1, value2, value3, value4, value5) -> tail {
                tail := add(headStart, 288)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_uint256_to_t_uint256_fromStack(value2,  add(headStart, 192))

                abi_encode_t_uint256_to_t_uint256_fromStack(value3,  add(headStart, 224))

                mstore(add(headStart, 256), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value4, value5,  tail)

            }

            /// @src 23:15596:15938  "function beforeDonate(IHooks self, PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_beforeDonate_3463_inner(var_self_3424_address, var_key_3427_mpos, var_amount0_3429, var_amount1_3431, var_hookData_3433_offset, var_hookData_3433_length) {

                /// @src 23:15770:15774  "self"
                let _527_address := var_self_3424_address
                let expr_3439_address := _527_address
                /// @src 23:15770:15788  "self.hasPermission"
                let expr_3440_self_address := expr_3439_address
                /// @src 23:15789:15807  "BEFORE_DONATE_FLAG"
                let expr_3441 := constant_BEFORE_DONATE_FLAG_2461()
                /// @src 23:15770:15808  "self.hasPermission(BEFORE_DONATE_FLAG)"
                let expr_3442 := fun_hasPermission_3529(expr_3440_self_address, expr_3441)
                /// @src 23:15766:15932  "if (self.hasPermission(BEFORE_DONATE_FLAG)) {..."
                if expr_3442 {
                    /// @src 23:15824:15828  "self"
                    let _529_address := var_self_3424_address
                    let expr_3443_address := _529_address
                    /// @src 23:15824:15837  "self.callHook"
                    let expr_3445_self_address := expr_3443_address
                    /// @src 23:15875:15885  "msg.sender"
                    let expr_3451 := caller()
                    /// @src 23:15874:15919  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3456_component_1 := expr_3451
                    /// @src 23:15887:15890  "key"
                    let _530_mpos := var_key_3427_mpos
                    let expr_3452_mpos := _530_mpos
                    /// @src 23:15874:15919  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3456_component_2_mpos := expr_3452_mpos
                    /// @src 23:15892:15899  "amount0"
                    let _531 := var_amount0_3429
                    let expr_3453 := _531
                    /// @src 23:15874:15919  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3456_component_3 := expr_3453
                    /// @src 23:15901:15908  "amount1"
                    let _532 := var_amount1_3431
                    let expr_3454 := _532
                    /// @src 23:15874:15919  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3456_component_4 := expr_3454
                    /// @src 23:15910:15918  "hookData"
                    let _533_offset := var_hookData_3433_offset
                    let _533_length := var_hookData_3433_length
                    let expr_3455_offset := _533_offset
                    let expr_3455_length := _533_length
                    /// @src 23:15874:15919  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3456_component_5_offset := expr_3455_offset
                    let expr_3456_component_5_length := expr_3455_length
                    /// @src 23:15838:15920  "abi.encodeCall(IHooks.beforeDonate, (msg.sender, key, amount0, amount1, hookData))"

                    let expr_3457_mpos := allocate_unbounded()
                    let _534 := add(expr_3457_mpos, 0x20)

                    mstore(_534, 0xb6a8b0fa00000000000000000000000000000000000000000000000000000000)
                    _534 := add(_534, 4)

                    let _535 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_memory_ptr__fromStack(_534, expr_3451, expr_3452_mpos, expr_3453, expr_3454, expr_3455_offset, expr_3455_length)
                    mstore(expr_3457_mpos, sub(_535, add(expr_3457_mpos, 0x20)))
                    finalize_allocation(expr_3457_mpos, sub(_535, expr_3457_mpos))
                    /// @src 23:15824:15921  "self.callHook(abi.encodeCall(IHooks.beforeDonate, (msg.sender, key, amount0, amount1, hookData)))"
                    let expr_3458_mpos := fun_callHook_2816(expr_3445_self_address, expr_3457_mpos)
                    /// @src 23:15766:15932  "if (self.hasPermission(BEFORE_DONATE_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3463
            /// @src 23:15596:15938  "function beforeDonate(IHooks self, PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_beforeDonate_3463(var_self_3424_address, var_key_3427_mpos, var_amount0_3429, var_amount1_3431, var_hookData_3433_offset, var_hookData_3433_length) {

                modifier_noSelfCall_3437(var_self_3424_address, var_key_3427_mpos, var_amount0_3429, var_amount1_3431, var_hookData_3433_offset, var_hookData_3433_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_from_storage_t_uint128(value) -> cleaned {
                cleaned := and(value, 0xffffffffffffffffffffffffffffffff)
            }

            function extract_from_storage_value_offset_0t_uint128(slot_value) -> value {
                value := cleanup_from_storage_t_uint128(shift_right_0_unsigned(slot_value))
            }

            function read_from_storage_split_offset_0_t_uint128(slot) -> value {
                value := extract_from_storage_value_offset_0t_uint128(sload(slot))

            }

            function cleanup_t_uint128(value) -> cleaned {
                cleaned := and(value, 0xffffffffffffffffffffffffffffffff)
            }

            function convert_t_rational_0_by_1_to_t_uint128(value) -> converted {
                converted := cleanup_t_uint128(identity(cleanup_t_rational_0_by_1(value)))
            }

            function cleanup_t_rational_340282366920938463463374607431768211456_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_340282366920938463463374607431768211456_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_340282366920938463463374607431768211456_by_1(value)))
            }

            /// @src 20:225:293  "uint256 internal constant Q128 = 0x100000000000000000000000000000000"
            function constant_Q128_7606() -> ret {
                /// @src 20:258:293  "0x100000000000000000000000000000000"
                let expr_7605 := 0x0100000000000000000000000000000000
                let _545 := convert_t_rational_340282366920938463463374607431768211456_by_1_to_t_uint256(expr_7605)

                ret := _545
            }

            function convert_t_uint128_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint128(value)))
            }

            function wrapping_add_t_uint256(x, y) -> sum {
                sum := cleanup_t_uint256(add(x, y))
            }

            /// @ast-id 5102
            /// @src 29:21937:22814  "function donate(State storage state, uint256 amount0, uint256 amount1) internal returns (BalanceDelta delta) {..."
            function fun_donate_5102(var_state_5025_slot, var_amount0_5027, var_amount1_5029) -> var_delta_5033 {
                /// @src 29:22026:22044  "BalanceDelta delta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_536 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_delta_5033 := zero_t_userDefinedValueType$_BalanceDelta_$6311_536

                /// @src 29:22076:22081  "state"
                let _537_slot := var_state_5025_slot
                let expr_5037_slot := _537_slot
                /// @src 29:22076:22091  "state.liquidity"
                let _538 := add(expr_5037_slot, 3)
                let _539 := read_from_storage_split_offset_0_t_uint128(_538)
                let expr_5038 := _539
                /// @src 29:22056:22091  "uint128 liquidity = state.liquidity"
                let var_liquidity_5036 := expr_5038
                /// @src 29:22105:22114  "liquidity"
                let _540 := var_liquidity_5036
                let expr_5040 := _540
                /// @src 29:22118:22119  "0"
                let expr_5041 := 0x00
                /// @src 29:22105:22119  "liquidity == 0"
                let expr_5042 := eq(cleanup_t_uint128(expr_5040), convert_t_rational_0_by_1_to_t_uint128(expr_5041))
                /// @src 29:22101:22167  "if (liquidity == 0) NoLiquidityToReceiveFees.selector.revertWith()"
                if expr_5042 {
                    /// @src 29:22121:22154  "NoLiquidityToReceiveFees.selector"
                    let expr_5046 := 0xa74f97ab00000000000000000000000000000000000000000000000000000000
                    /// @src 29:22121:22165  "NoLiquidityToReceiveFees.selector.revertWith"
                    let expr_5047_self := expr_5046
                    fun_revertWith_2274(expr_5047_self)
                    /// @src 29:22101:22167  "if (liquidity == 0) NoLiquidityToReceiveFees.selector.revertWith()"
                }
                /// @src 29:22298:22305  "amount0"
                let _541 := var_amount0_5027
                let expr_5053 := _541
                /// @src 29:22298:22314  "amount0.toInt128"
                let expr_5054_self := expr_5053
                /// @src 29:22298:22316  "amount0.toInt128()"
                let expr_5055 := fun_toInt128_5750(expr_5054_self)
                /// @src 29:22297:22317  "(amount0.toInt128())"
                let expr_5056 := expr_5055
                /// @src 29:22296:22317  "-(amount0.toInt128())"
                let expr_5057 := negate_wrapping_t_int128(expr_5056)
                /// @src 29:22321:22328  "amount1"
                let _542 := var_amount1_5029
                let expr_5058 := _542
                /// @src 29:22321:22337  "amount1.toInt128"
                let expr_5059_self := expr_5058
                /// @src 29:22321:22339  "amount1.toInt128()"
                let expr_5060 := fun_toInt128_5750(expr_5059_self)
                /// @src 29:22320:22340  "(amount1.toInt128())"
                let expr_5061 := expr_5060
                /// @src 29:22319:22340  "-(amount1.toInt128())"
                let expr_5062 := negate_wrapping_t_int128(expr_5061)
                /// @src 29:22281:22341  "toBalanceDelta(-(amount0.toInt128()), -(amount1.toInt128()))"
                let expr_5063 := fun_toBalanceDelta_6337(expr_5057, expr_5062)
                /// @src 29:22273:22341  "delta = toBalanceDelta(-(amount0.toInt128()), -(amount1.toInt128()))"
                var_delta_5033 := expr_5063
                let expr_5064 := expr_5063
                /// @src 29:22503:22510  "amount0"
                let _543 := var_amount0_5027
                let expr_5066 := _543
                /// @src 29:22513:22514  "0"
                let expr_5067 := 0x00
                /// @src 29:22503:22514  "amount0 > 0"
                let expr_5068 := gt(cleanup_t_uint256(expr_5066), convert_t_rational_0_by_1_to_t_uint256(expr_5067))
                /// @src 29:22499:22642  "if (amount0 > 0) {..."
                if expr_5068 {
                    /// @src 29:22564:22574  "UnsafeMath"
                    let expr_5072_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                    /// @src 29:22588:22595  "amount0"
                    let _544 := var_amount0_5027
                    let expr_5074 := _544
                    /// @src 29:22597:22610  "FixedPoint128"
                    let expr_5075_address := linkersymbol("src/libraries/FixedPoint128.sol:FixedPoint128")
                    /// @src 29:22597:22615  "FixedPoint128.Q128"
                    let expr_5076 := constant_Q128_7606()
                    /// @src 29:22617:22626  "liquidity"
                    let _546 := var_liquidity_5036
                    let expr_5077 := _546
                    /// @src 29:22564:22627  "UnsafeMath.simpleMulDiv(amount0, FixedPoint128.Q128, liquidity)"
                    let _547 := convert_t_uint128_to_t_uint256(expr_5077)
                    let expr_5078 := fun_simpleMulDiv_8627(expr_5074, expr_5076, _547)
                    /// @src 29:22534:22539  "state"
                    let _548_slot := var_state_5025_slot
                    let expr_5069_slot := _548_slot
                    /// @src 29:22534:22560  "state.feeGrowthGlobal0X128"
                    let _549 := add(expr_5069_slot, 1)
                    /// @src 29:22534:22627  "state.feeGrowthGlobal0X128 += UnsafeMath.simpleMulDiv(amount0, FixedPoint128.Q128, liquidity)"
                    let _550 := read_from_storage_split_offset_0_t_uint256(_549)
                    let expr_5079 := wrapping_add_t_uint256(_550, expr_5078)

                    update_storage_value_offset_0t_uint256_to_t_uint256(_549, expr_5079)
                    /// @src 29:22499:22642  "if (amount0 > 0) {..."
                }
                /// @src 29:22659:22666  "amount1"
                let _551 := var_amount1_5029
                let expr_5083 := _551
                /// @src 29:22669:22670  "0"
                let expr_5084 := 0x00
                /// @src 29:22659:22670  "amount1 > 0"
                let expr_5085 := gt(cleanup_t_uint256(expr_5083), convert_t_rational_0_by_1_to_t_uint256(expr_5084))
                /// @src 29:22655:22798  "if (amount1 > 0) {..."
                if expr_5085 {
                    /// @src 29:22720:22730  "UnsafeMath"
                    let expr_5089_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                    /// @src 29:22744:22751  "amount1"
                    let _552 := var_amount1_5029
                    let expr_5091 := _552
                    /// @src 29:22753:22766  "FixedPoint128"
                    let expr_5092_address := linkersymbol("src/libraries/FixedPoint128.sol:FixedPoint128")
                    /// @src 29:22753:22771  "FixedPoint128.Q128"
                    let expr_5093 := constant_Q128_7606()
                    /// @src 29:22773:22782  "liquidity"
                    let _553 := var_liquidity_5036
                    let expr_5094 := _553
                    /// @src 29:22720:22783  "UnsafeMath.simpleMulDiv(amount1, FixedPoint128.Q128, liquidity)"
                    let _554 := convert_t_uint128_to_t_uint256(expr_5094)
                    let expr_5095 := fun_simpleMulDiv_8627(expr_5091, expr_5093, _554)
                    /// @src 29:22690:22695  "state"
                    let _555_slot := var_state_5025_slot
                    let expr_5086_slot := _555_slot
                    /// @src 29:22690:22716  "state.feeGrowthGlobal1X128"
                    let _556 := add(expr_5086_slot, 2)
                    /// @src 29:22690:22783  "state.feeGrowthGlobal1X128 += UnsafeMath.simpleMulDiv(amount1, FixedPoint128.Q128, liquidity)"
                    let _557 := read_from_storage_split_offset_0_t_uint256(_556)
                    let expr_5096 := wrapping_add_t_uint256(_557, expr_5095)

                    update_storage_value_offset_0t_uint256_to_t_uint256(_556, expr_5096)
                    /// @src 29:22655:22798  "if (amount1 > 0) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1187
            /// @src 6:16986:17218  "function _accountPoolBalanceDelta(PoolKey memory key, BalanceDelta delta, address target) internal {..."
            function fun__accountPoolBalanceDelta_1187(var_key_1160_mpos, var_delta_1163, var_target_1165) {

                /// @src 6:17109:17112  "key"
                let _558_mpos := var_key_1160_mpos
                let expr_1169_mpos := _558_mpos
                /// @src 6:17109:17122  "key.currency0"
                let _559 := add(expr_1169_mpos, 0)
                let _560 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_559)
                let expr_1170 := _560
                /// @src 6:17124:17129  "delta"
                let _561 := var_delta_1163
                let expr_1171 := _561
                /// @src 6:17124:17137  "delta.amount0"
                let expr_1172_self := expr_1171
                /// @src 6:17124:17139  "delta.amount0()"
                let expr_1173 := fun_amount0_6458(expr_1172_self)
                /// @src 6:17141:17147  "target"
                let _562 := var_target_1165
                let expr_1174 := _562
                fun__accountDelta_1156(expr_1170, expr_1173, expr_1174)
                /// @src 6:17172:17175  "key"
                let _563_mpos := var_key_1160_mpos
                let expr_1178_mpos := _563_mpos
                /// @src 6:17172:17185  "key.currency1"
                let _564 := add(expr_1178_mpos, 32)
                let _565 := read_from_memoryt_userDefinedValueType$_Currency_$6525(_564)
                let expr_1179 := _565
                /// @src 6:17187:17192  "delta"
                let _566 := var_delta_1163
                let expr_1180 := _566
                /// @src 6:17187:17200  "delta.amount1"
                let expr_1181_self := expr_1180
                /// @src 6:17187:17202  "delta.amount1()"
                let expr_1182 := fun_amount1_6468(expr_1181_self)
                /// @src 6:17204:17210  "target"
                let _567 := var_target_1165
                let expr_1183 := _567
                fun__accountDelta_1156(expr_1179, expr_1182, expr_1183)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2875
            /// @src 23:8767:8875  "modifier noSelfCall(IHooks self) {..."
            function modifier_noSelfCall_3480(var_self_3467_address, var_key_3470_mpos, var_amount0_3472, var_amount1_3474, var_hookData_3476_offset, var_hookData_3476_length) {

                /// @src 23:16175:16179  "self"
                let _568_address := var_self_3467_address
                let expr_3479_address := _568_address
                let _569_address := expr_3479_address
                let var_self_2862_address := _569_address

                /// @src 23:8814:8824  "msg.sender"
                let expr_2865 := caller()
                /// @src 23:8836:8840  "self"
                let _570_address := var_self_2862_address
                let expr_2868_address := _570_address
                /// @src 23:8828:8841  "address(self)"
                let expr_2869 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2868_address)
                /// @src 23:8814:8841  "msg.sender != address(self)"
                let expr_2870 := iszero(eq(cleanup_t_address(expr_2865), cleanup_t_address(expr_2869)))
                /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                if expr_2870 {
                    /// @src 23:8857:8858  "_"
                    fun_afterDonate_3506_inner(var_self_3467_address, var_key_3470_mpos, var_amount0_3472, var_amount1_3474, var_hookData_3476_offset, var_hookData_3476_length)
                    /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_16_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_16_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_16_by_1(value)))
            }

            /// @src 23:1919:1971  "uint160 internal constant AFTER_DONATE_FLAG = 1 << 4"
            function constant_AFTER_DONATE_FLAG_2466() -> ret {
                /// @src 23:1965:1971  "1 << 4"
                let expr_2465 := 0x10
                let _572 := convert_t_rational_16_by_1_to_t_uint160(expr_2465)

                ret := _572
            }

            /// @src 23:16026:16365  "function afterDonate(IHooks self, PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_afterDonate_3506_inner(var_self_3467_address, var_key_3470_mpos, var_amount0_3472, var_amount1_3474, var_hookData_3476_offset, var_hookData_3476_length) {

                /// @src 23:16199:16203  "self"
                let _571_address := var_self_3467_address
                let expr_3482_address := _571_address
                /// @src 23:16199:16217  "self.hasPermission"
                let expr_3483_self_address := expr_3482_address
                /// @src 23:16218:16235  "AFTER_DONATE_FLAG"
                let expr_3484 := constant_AFTER_DONATE_FLAG_2466()
                /// @src 23:16199:16236  "self.hasPermission(AFTER_DONATE_FLAG)"
                let expr_3485 := fun_hasPermission_3529(expr_3483_self_address, expr_3484)
                /// @src 23:16195:16359  "if (self.hasPermission(AFTER_DONATE_FLAG)) {..."
                if expr_3485 {
                    /// @src 23:16252:16256  "self"
                    let _573_address := var_self_3467_address
                    let expr_3486_address := _573_address
                    /// @src 23:16252:16265  "self.callHook"
                    let expr_3488_self_address := expr_3486_address
                    /// @src 23:16302:16312  "msg.sender"
                    let expr_3494 := caller()
                    /// @src 23:16301:16346  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3499_component_1 := expr_3494
                    /// @src 23:16314:16317  "key"
                    let _574_mpos := var_key_3470_mpos
                    let expr_3495_mpos := _574_mpos
                    /// @src 23:16301:16346  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3499_component_2_mpos := expr_3495_mpos
                    /// @src 23:16319:16326  "amount0"
                    let _575 := var_amount0_3472
                    let expr_3496 := _575
                    /// @src 23:16301:16346  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3499_component_3 := expr_3496
                    /// @src 23:16328:16335  "amount1"
                    let _576 := var_amount1_3474
                    let expr_3497 := _576
                    /// @src 23:16301:16346  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3499_component_4 := expr_3497
                    /// @src 23:16337:16345  "hookData"
                    let _577_offset := var_hookData_3476_offset
                    let _577_length := var_hookData_3476_length
                    let expr_3498_offset := _577_offset
                    let expr_3498_length := _577_length
                    /// @src 23:16301:16346  "(msg.sender, key, amount0, amount1, hookData)"
                    let expr_3499_component_5_offset := expr_3498_offset
                    let expr_3499_component_5_length := expr_3498_length
                    /// @src 23:16266:16347  "abi.encodeCall(IHooks.afterDonate, (msg.sender, key, amount0, amount1, hookData))"

                    let expr_3500_mpos := allocate_unbounded()
                    let _578 := add(expr_3500_mpos, 0x20)

                    mstore(_578, 0xe1b4af6900000000000000000000000000000000000000000000000000000000)
                    _578 := add(_578, 4)

                    let _579 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint256_t_uint256_t_bytes_memory_ptr__fromStack(_578, expr_3494, expr_3495_mpos, expr_3496, expr_3497, expr_3498_offset, expr_3498_length)
                    mstore(expr_3500_mpos, sub(_579, add(expr_3500_mpos, 0x20)))
                    finalize_allocation(expr_3500_mpos, sub(_579, expr_3500_mpos))
                    /// @src 23:16252:16348  "self.callHook(abi.encodeCall(IHooks.afterDonate, (msg.sender, key, amount0, amount1, hookData)))"
                    let expr_3501_mpos := fun_callHook_2816(expr_3488_self_address, expr_3500_mpos)
                    /// @src 23:16195:16359  "if (self.hasPermission(AFTER_DONATE_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3506
            /// @src 23:16026:16365  "function afterDonate(IHooks self, PoolKey memory key, uint256 amount0, uint256 amount1, bytes calldata hookData)..."
            function fun_afterDonate_3506(var_self_3467_address, var_key_3470_mpos, var_amount0_3472, var_amount1_3474, var_hookData_3476_offset, var_hookData_3476_length) {

                modifier_noSelfCall_3480(var_self_3467_address, var_key_3470_mpos, var_amount0_3472, var_amount1_3474, var_hookData_3476_offset, var_hookData_3476_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3690
            /// @src 26:490:634  "function unlock() internal {..."
            function fun_unlock_3690() {

                /// @src 26:527:628  "assembly (\"memory-safe\") {..."
                {
                    tstore(87100234046427240614499661373387320107015461065347489303548037305558901893923, true)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3716
            /// @src 27:558:717  "function read() internal view returns (uint256 count) {..."
            function fun_read_3716() -> var_count_3712 {
                /// @src 27:597:610  "uint256 count"
                let zero_t_uint256_580 := zero_value_for_split_t_uint256()
                var_count_3712 := zero_t_uint256_580

                /// @src 27:622:711  "assembly (\"memory-safe\") {..."
                {
                    var_count_3712 := tload(56671960505278111519104690822132496699113179860588238901689140059013086026251)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3695
            /// @src 26:640:761  "function lock() internal {..."
            function fun_lock_3695() {

                /// @src 26:675:755  "assembly (\"memory-safe\") {..."
                {
                    tstore(87100234046427240614499661373387320107015461065347489303548037305558901893923, false)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_8388608_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_8388608_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_8388608_by_1(value)))
            }

            /// @src 24:510:560  "uint24 public constant DYNAMIC_FEE_FLAG = 0x800000"
            function constant_DYNAMIC_FEE_FLAG_3550() -> ret {
                /// @src 24:552:560  "0x800000"
                let expr_3549 := 0x800000
                let _583 := convert_t_rational_8388608_by_1_to_t_uint24(expr_3549)

                ret := _583
            }

            /// @ast-id 3575
            /// @src 24:1298:1410  "function isDynamicFee(uint24 self) internal pure returns (bool) {..."
            function fun_isDynamicFee_3575(var_self_3565) -> var__3568 {
                /// @src 24:1356:1360  "bool"
                let zero_t_bool_581 := zero_value_for_split_t_bool()
                var__3568 := zero_t_bool_581

                /// @src 24:1379:1383  "self"
                let _582 := var_self_3565
                let expr_3570 := _582
                /// @src 24:1387:1403  "DYNAMIC_FEE_FLAG"
                let expr_3571 := constant_DYNAMIC_FEE_FLAG_3550()
                /// @src 24:1379:1403  "self == DYNAMIC_FEE_FLAG"
                let expr_3572 := eq(cleanup_t_uint24(expr_3570), cleanup_t_uint24(expr_3571))
                /// @src 24:1372:1403  "return self == DYNAMIC_FEE_FLAG"
                var__3568 := expr_3572
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3608
            /// @src 24:1833:1955  "function validate(uint24 self) internal pure {..."
            function fun_validate_3608(var_self_3591) {

                /// @src 24:1893:1897  "self"
                let _584 := var_self_3591
                let expr_3594 := _584
                /// @src 24:1893:1905  "self.isValid"
                let expr_3595_self := expr_3594
                /// @src 24:1893:1907  "self.isValid()"
                let expr_3596 := fun_isValid_3588(expr_3595_self)
                /// @src 24:1892:1907  "!self.isValid()"
                let expr_3597 := cleanup_t_bool(iszero(expr_3596))
                /// @src 24:1888:1948  "if (!self.isValid()) LPFeeTooLarge.selector.revertWith(self)"
                if expr_3597 {
                    /// @src 24:1909:1931  "LPFeeTooLarge.selector"
                    let expr_3601 := 0x1400211300000000000000000000000000000000000000000000000000000000
                    /// @src 24:1909:1942  "LPFeeTooLarge.selector.revertWith"
                    let expr_3602_self := expr_3601
                    /// @src 24:1943:1947  "self"
                    let _585 := var_self_3591
                    let expr_3603 := _585
                    /// @src 24:1909:1948  "LPFeeTooLarge.selector.revertWith(self)"
                    let _586 := convert_t_uint24_to_t_uint160(expr_3603)
                    fun_revertWith_2304(expr_3602_self, _586)
                    /// @src 24:1888:1948  "if (!self.isValid()) LPFeeTooLarge.selector.revertWith(self)"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function prepare_store_t_userDefinedValueType$_Slot0_$8632(value) -> ret {
                ret := shift_right_0_unsigned(value)
            }

            function update_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632_to_t_userDefinedValueType$_Slot0_$8632(slot, value_0) {
                let convertedValue_0 := convert_t_bytes32_to_t_bytes32(value_0)
                sstore(slot, update_byte_slice_32_shift_0(sload(slot), prepare_store_t_userDefinedValueType$_Slot0_$8632(convertedValue_0)))
            }

            /// @ast-id 4022
            /// @src 29:5235:5389  "function setLPFee(State storage self, uint24 lpFee) internal {..."
            function fun_setLPFee_4022(var_self_4001_slot, var_lpFee_4003) {

                /// @src 29:5306:5310  "self"
                let _587_slot := var_self_4001_slot
                let expr_4006_slot := _587_slot
                /// @src 29:5306:5331  "self.checkPoolInitialized"
                let expr_4008_self_slot := expr_4006_slot
                fun_checkPoolInitialized_5344(expr_4008_self_slot)
                /// @src 29:5356:5360  "self"
                let _588_slot := var_self_4001_slot
                let expr_4014_slot := _588_slot
                /// @src 29:5356:5366  "self.slot0"
                let _589 := add(expr_4014_slot, 0)
                let _590 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_589)
                let expr_4015 := _590
                /// @src 29:5356:5375  "self.slot0.setLpFee"
                let expr_4016_self := expr_4015
                /// @src 29:5376:5381  "lpFee"
                let _591 := var_lpFee_4003
                let expr_4017 := _591
                /// @src 29:5356:5382  "self.slot0.setLpFee(lpFee)"
                let expr_4018 := fun_setLpFee_8744(expr_4016_self, expr_4017)
                /// @src 29:5343:5347  "self"
                let _592_slot := var_self_4001_slot
                let expr_4011_slot := _592_slot
                /// @src 29:5343:5353  "self.slot0"
                let _593 := add(expr_4011_slot, 0)
                /// @src 29:5343:5382  "self.slot0 = self.slot0.setLpFee(lpFee)"
                update_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632_to_t_userDefinedValueType$_Slot0_$8632(_593, expr_4018)
                let expr_4019 := expr_4018

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2875
            /// @src 23:8767:8875  "modifier noSelfCall(IHooks self) {..."
            function modifier_noSelfCall_2968(var_self_2956_address, var_key_2959_mpos, var_params_2962_mpos, var_hookData_2964_offset, var_hookData_2964_length) {

                /// @src 23:9943:9947  "self"
                let _594_address := var_self_2956_address
                let expr_2967_address := _594_address
                let _595_address := expr_2967_address
                let var_self_2862_address := _595_address

                /// @src 23:8814:8824  "msg.sender"
                let expr_2865 := caller()
                /// @src 23:8836:8840  "self"
                let _596_address := var_self_2862_address
                let expr_2868_address := _596_address
                /// @src 23:8828:8841  "address(self)"
                let expr_2869 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2868_address)
                /// @src 23:8814:8841  "msg.sender != address(self)"
                let expr_2870 := iszero(eq(cleanup_t_address(expr_2865), cleanup_t_address(expr_2869)))
                /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                if expr_2870 {
                    /// @src 23:8857:8858  "_"
                    fun_beforeModifyLiquidity_3025_inner(var_self_2956_address, var_key_2959_mpos, var_params_2962_mpos, var_hookData_2964_offset, var_hookData_2964_length)
                    /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_2048_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_2048_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_2048_by_1(value)))
            }

            /// @src 23:1474:1535  "uint160 internal constant BEFORE_ADD_LIQUIDITY_FLAG = 1 << 11"
            function constant_BEFORE_ADD_LIQUIDITY_FLAG_2431() -> ret {
                /// @src 23:1528:1535  "1 << 11"
                let expr_2430 := 0x0800
                let _601 := convert_t_rational_2048_by_1_to_t_uint160(expr_2430)

                ret := _601
            }

            function cleanup_t_rational_512_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_512_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_512_by_1(value)))
            }

            /// @src 23:1608:1671  "uint160 internal constant BEFORE_REMOVE_LIQUIDITY_FLAG = 1 << 9"
            function constant_BEFORE_REMOVE_LIQUIDITY_FLAG_2441() -> ret {
                /// @src 23:1665:1671  "1 << 9"
                let expr_2440 := 0x0200
                let _606 := convert_t_rational_512_by_1_to_t_uint160(expr_2440)

                ret := _606
            }

            function abi_encode_t_int256_to_t_int256(value, pos) {
                mstore(pos, cleanup_t_int256(value))
            }

            // struct ModifyLiquidityParams -> struct ModifyLiquidityParams
            function abi_encode_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_to_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_fromStack(value, pos)  {
                let tail := add(pos, 0x80)

                {
                    // tickLower

                    let memberValue0 := mload(add(value, 0x00))
                    abi_encode_t_int24_to_t_int24(memberValue0, add(pos, 0x00))
                }

                {
                    // tickUpper

                    let memberValue0 := mload(add(value, 0x20))
                    abi_encode_t_int24_to_t_int24(memberValue0, add(pos, 0x20))
                }

                {
                    // liquidityDelta

                    let memberValue0 := mload(add(value, 0x40))
                    abi_encode_t_int256_to_t_int256(memberValue0, add(pos, 0x40))
                }

                {
                    // salt

                    let memberValue0 := mload(add(value, 0x60))
                    abi_encode_t_bytes32_to_t_bytes32(memberValue0, add(pos, 0x60))
                }

            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_memory_ptr__fromStack(headStart , value0, value1, value2, value3, value4) -> tail {
                tail := add(headStart, 352)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_to_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_fromStack(value2,  add(headStart, 192))

                mstore(add(headStart, 320), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value3, value4,  tail)

            }

            /// @src 23:9759:10374  "function beforeModifyLiquidity(..."
            function fun_beforeModifyLiquidity_3025_inner(var_self_2956_address, var_key_2959_mpos, var_params_2962_mpos, var_hookData_2964_offset, var_hookData_2964_length) {

                /// @src 23:9963:9969  "params"
                let _597_mpos := var_params_2962_mpos
                let expr_2970_mpos := _597_mpos
                /// @src 23:9963:9984  "params.liquidityDelta"
                let _598 := add(expr_2970_mpos, 64)
                let _599 := read_from_memoryt_int256(_598)
                let expr_2971 := _599
                /// @src 23:9987:9988  "0"
                let expr_2972 := 0x00
                /// @src 23:9963:9988  "params.liquidityDelta > 0"
                let expr_2973 := sgt(cleanup_t_int256(expr_2971), convert_t_rational_0_by_1_to_t_int256(expr_2972))
                /// @src 23:9963:10037  "params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)"
                let expr_2978 := expr_2973
                if expr_2978 {
                    /// @src 23:9992:9996  "self"
                    let _600_address := var_self_2956_address
                    let expr_2974_address := _600_address
                    /// @src 23:9992:10010  "self.hasPermission"
                    let expr_2975_self_address := expr_2974_address
                    /// @src 23:10011:10036  "BEFORE_ADD_LIQUIDITY_FLAG"
                    let expr_2976 := constant_BEFORE_ADD_LIQUIDITY_FLAG_2431()
                    /// @src 23:9992:10037  "self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)"
                    let expr_2977 := fun_hasPermission_3529(expr_2975_self_address, expr_2976)
                    /// @src 23:9963:10037  "params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)"
                    expr_2978 := expr_2977
                }
                /// @src 23:9959:10368  "if (params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)) {..."
                switch expr_2978
                case 0 {
                    /// @src 23:10167:10173  "params"
                    let _602_mpos := var_params_2962_mpos
                    let expr_2996_mpos := _602_mpos
                    /// @src 23:10167:10188  "params.liquidityDelta"
                    let _603 := add(expr_2996_mpos, 64)
                    let _604 := read_from_memoryt_int256(_603)
                    let expr_2997 := _604
                    /// @src 23:10192:10193  "0"
                    let expr_2998 := 0x00
                    /// @src 23:10167:10193  "params.liquidityDelta <= 0"
                    let expr_2999 := iszero(sgt(cleanup_t_int256(expr_2997), convert_t_rational_0_by_1_to_t_int256(expr_2998)))
                    /// @src 23:10167:10245  "params.liquidityDelta <= 0 && self.hasPermission(BEFORE_REMOVE_LIQUIDITY_FLAG)"
                    let expr_3004 := expr_2999
                    if expr_3004 {
                        /// @src 23:10197:10201  "self"
                        let _605_address := var_self_2956_address
                        let expr_3000_address := _605_address
                        /// @src 23:10197:10215  "self.hasPermission"
                        let expr_3001_self_address := expr_3000_address
                        /// @src 23:10216:10244  "BEFORE_REMOVE_LIQUIDITY_FLAG"
                        let expr_3002 := constant_BEFORE_REMOVE_LIQUIDITY_FLAG_2441()
                        /// @src 23:10197:10245  "self.hasPermission(BEFORE_REMOVE_LIQUIDITY_FLAG)"
                        let expr_3003 := fun_hasPermission_3529(expr_3001_self_address, expr_3002)
                        /// @src 23:10167:10245  "params.liquidityDelta <= 0 && self.hasPermission(BEFORE_REMOVE_LIQUIDITY_FLAG)"
                        expr_3004 := expr_3003
                    }
                    /// @src 23:10163:10368  "if (params.liquidityDelta <= 0 && self.hasPermission(BEFORE_REMOVE_LIQUIDITY_FLAG)) {..."
                    if expr_3004 {
                        /// @src 23:10261:10265  "self"
                        let _607_address := var_self_2956_address
                        let expr_3005_address := _607_address
                        /// @src 23:10261:10274  "self.callHook"
                        let expr_3007_self_address := expr_3005_address
                        /// @src 23:10321:10331  "msg.sender"
                        let expr_3013 := caller()
                        /// @src 23:10320:10355  "(msg.sender, key, params, hookData)"
                        let expr_3017_component_1 := expr_3013
                        /// @src 23:10333:10336  "key"
                        let _608_mpos := var_key_2959_mpos
                        let expr_3014_mpos := _608_mpos
                        /// @src 23:10320:10355  "(msg.sender, key, params, hookData)"
                        let expr_3017_component_2_mpos := expr_3014_mpos
                        /// @src 23:10338:10344  "params"
                        let _609_mpos := var_params_2962_mpos
                        let expr_3015_mpos := _609_mpos
                        /// @src 23:10320:10355  "(msg.sender, key, params, hookData)"
                        let expr_3017_component_3_mpos := expr_3015_mpos
                        /// @src 23:10346:10354  "hookData"
                        let _610_offset := var_hookData_2964_offset
                        let _610_length := var_hookData_2964_length
                        let expr_3016_offset := _610_offset
                        let expr_3016_length := _610_length
                        /// @src 23:10320:10355  "(msg.sender, key, params, hookData)"
                        let expr_3017_component_4_offset := expr_3016_offset
                        let expr_3017_component_4_length := expr_3016_length
                        /// @src 23:10275:10356  "abi.encodeCall(IHooks.beforeRemoveLiquidity, (msg.sender, key, params, hookData))"

                        let expr_3018_mpos := allocate_unbounded()
                        let _611 := add(expr_3018_mpos, 0x20)

                        mstore(_611, 0x21d0ee7000000000000000000000000000000000000000000000000000000000)
                        _611 := add(_611, 4)

                        let _612 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_memory_ptr__fromStack(_611, expr_3013, expr_3014_mpos, expr_3015_mpos, expr_3016_offset, expr_3016_length)
                        mstore(expr_3018_mpos, sub(_612, add(expr_3018_mpos, 0x20)))
                        finalize_allocation(expr_3018_mpos, sub(_612, expr_3018_mpos))
                        /// @src 23:10261:10357  "self.callHook(abi.encodeCall(IHooks.beforeRemoveLiquidity, (msg.sender, key, params, hookData)))"
                        let expr_3019_mpos := fun_callHook_2816(expr_3007_self_address, expr_3018_mpos)
                        /// @src 23:10163:10368  "if (params.liquidityDelta <= 0 && self.hasPermission(BEFORE_REMOVE_LIQUIDITY_FLAG)) {..."
                    }
                    /// @src 23:9959:10368  "if (params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)) {..."
                }
                default {
                    /// @src 23:10053:10057  "self"
                    let _613_address := var_self_2956_address
                    let expr_2979_address := _613_address
                    /// @src 23:10053:10066  "self.callHook"
                    let expr_2981_self_address := expr_2979_address
                    /// @src 23:10110:10120  "msg.sender"
                    let expr_2987 := caller()
                    /// @src 23:10109:10144  "(msg.sender, key, params, hookData)"
                    let expr_2991_component_1 := expr_2987
                    /// @src 23:10122:10125  "key"
                    let _614_mpos := var_key_2959_mpos
                    let expr_2988_mpos := _614_mpos
                    /// @src 23:10109:10144  "(msg.sender, key, params, hookData)"
                    let expr_2991_component_2_mpos := expr_2988_mpos
                    /// @src 23:10127:10133  "params"
                    let _615_mpos := var_params_2962_mpos
                    let expr_2989_mpos := _615_mpos
                    /// @src 23:10109:10144  "(msg.sender, key, params, hookData)"
                    let expr_2991_component_3_mpos := expr_2989_mpos
                    /// @src 23:10135:10143  "hookData"
                    let _616_offset := var_hookData_2964_offset
                    let _616_length := var_hookData_2964_length
                    let expr_2990_offset := _616_offset
                    let expr_2990_length := _616_length
                    /// @src 23:10109:10144  "(msg.sender, key, params, hookData)"
                    let expr_2991_component_4_offset := expr_2990_offset
                    let expr_2991_component_4_length := expr_2990_length
                    /// @src 23:10067:10145  "abi.encodeCall(IHooks.beforeAddLiquidity, (msg.sender, key, params, hookData))"

                    let expr_2992_mpos := allocate_unbounded()
                    let _617 := add(expr_2992_mpos, 0x20)

                    mstore(_617, 0x259982e500000000000000000000000000000000000000000000000000000000)
                    _617 := add(_617, 4)

                    let _618 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_bytes_memory_ptr__fromStack(_617, expr_2987, expr_2988_mpos, expr_2989_mpos, expr_2990_offset, expr_2990_length)
                    mstore(expr_2992_mpos, sub(_618, add(expr_2992_mpos, 0x20)))
                    finalize_allocation(expr_2992_mpos, sub(_618, expr_2992_mpos))
                    /// @src 23:10053:10146  "self.callHook(abi.encodeCall(IHooks.beforeAddLiquidity, (msg.sender, key, params, hookData)))"
                    let expr_2993_mpos := fun_callHook_2816(expr_2981_self_address, expr_2992_mpos)
                    /// @src 23:9959:10368  "if (params.liquidityDelta > 0 && self.hasPermission(BEFORE_ADD_LIQUIDITY_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3025
            /// @src 23:9759:10374  "function beforeModifyLiquidity(..."
            function fun_beforeModifyLiquidity_3025(var_self_2956_address, var_key_2959_mpos, var_params_2962_mpos, var_hookData_2964_offset, var_hookData_2964_length) {

                modifier_noSelfCall_2968(var_self_2956_address, var_key_2959_mpos, var_params_2962_mpos, var_hookData_2964_offset, var_hookData_2964_length)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5693
            /// @src 32:1460:1611  "function toInt128(int256 x) internal pure returns (int128 y) {..."
            function fun_toInt128_5693(var_x_5669) -> var_y_5672 {
                /// @src 32:1511:1519  "int128 y"
                let zero_t_int128_619 := zero_value_for_split_t_int128()
                var_y_5672 := zero_t_int128_619

                /// @src 32:1542:1543  "x"
                let _620 := var_x_5669
                let expr_5677 := _620
                /// @src 32:1535:1544  "int128(x)"
                let expr_5678 := convert_t_int256_to_t_int128(expr_5677)
                /// @src 32:1531:1544  "y = int128(x)"
                var_y_5672 := expr_5678
                let expr_5679 := expr_5678
                /// @src 32:1558:1559  "y"
                let _621 := var_y_5672
                let expr_5681 := _621
                /// @src 32:1563:1564  "x"
                let _622 := var_x_5669
                let expr_5682 := _622
                /// @src 32:1558:1564  "y != x"
                let expr_5683 := iszero(eq(convert_t_int128_to_t_int256(expr_5681), cleanup_t_int256(expr_5682)))
                /// @src 32:1554:1604  "if (y != x) SafeCastOverflow.selector.revertWith()"
                if expr_5683 {
                    /// @src 32:1566:1591  "SafeCastOverflow.selector"
                    let expr_5687 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
                    /// @src 32:1566:1602  "SafeCastOverflow.selector.revertWith"
                    let expr_5688_self := expr_5687
                    fun_revertWith_2274(expr_5688_self)
                    /// @src 32:1554:1604  "if (y != x) SafeCastOverflow.selector.revertWith()"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function read_from_memoryt_int128(ptr) -> returnValue {

                let value := cleanup_t_int128(mload(ptr))

                returnValue :=

                value

            }

            function allocate_memory_struct_t_struct$_ModifyLiquidityState_$4044_memory_ptr() -> memPtr {
                memPtr := allocate_memory(128)
            }

            function zero_value_for_t_bool() -> ret {
                ret := 0
            }

            function zero_value_for_t_uint128() -> ret {
                ret := 0
            }

            function allocate_and_zero_memory_struct_t_struct$_ModifyLiquidityState_$4044_memory_ptr() -> memPtr {
                memPtr := allocate_memory_struct_t_struct$_ModifyLiquidityState_$4044_memory_ptr()
                let offset := memPtr

                mstore(offset, zero_value_for_t_bool())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint128())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_bool())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint128())
                offset := add(offset, 32)

            }

            function zero_value_for_split_t_struct$_ModifyLiquidityState_$4044_memory_ptr() -> ret {
                ret := allocate_and_zero_memory_struct_t_struct$_ModifyLiquidityState_$4044_memory_ptr()
            }

            function write_to_memory_t_uint128(memPtr, value) {
                mstore(memPtr, cleanup_t_uint128(value))
            }

            function read_from_memoryt_uint128(ptr) -> returnValue {

                let value := cleanup_t_uint128(mload(ptr))

                returnValue :=

                value

            }

            function read_from_memoryt_address(ptr) -> returnValue {

                let value := cleanup_t_address(mload(ptr))

                returnValue :=

                value

            }

            function update_byte_slice_16_shift_0(value, toInsert) -> result {
                let mask := 0xffffffffffffffffffffffffffffffff
                toInsert := shift_left_0(toInsert)
                value := and(value, not(mask))
                result := or(value, and(toInsert, mask))
            }

            function convert_t_uint128_to_t_uint128(value) -> converted {
                converted := cleanup_t_uint128(identity(cleanup_t_uint128(value)))
            }

            function prepare_store_t_uint128(value) -> ret {
                ret := value
            }

            function update_storage_value_offset_0t_uint128_to_t_uint128(slot, value_0) {
                let convertedValue_0 := convert_t_uint128_to_t_uint128(value_0)
                sstore(slot, update_byte_slice_16_shift_0(sload(slot), prepare_store_t_uint128(convertedValue_0)))
            }

            /// @ast-id 4371
            /// @src 29:6410:10810  "function modifyLiquidity(State storage self, ModifyLiquidityParams memory params)..."
            function fun_modifyLiquidity_4371(var_self_4048_slot, var_params_4051_mpos) -> var_delta_4055, var_feeDelta_4058 {
                /// @src 29:6526:6544  "BalanceDelta delta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_623 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_delta_4055 := zero_t_userDefinedValueType$_BalanceDelta_$6311_623
                /// @src 29:6546:6567  "BalanceDelta feeDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_624 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_feeDelta_4058 := zero_t_userDefinedValueType$_BalanceDelta_$6311_624

                /// @src 29:6607:6613  "params"
                let _625_mpos := var_params_4051_mpos
                let expr_4062_mpos := _625_mpos
                /// @src 29:6607:6628  "params.liquidityDelta"
                let _626 := add(expr_4062_mpos, 96)
                let _627 := read_from_memoryt_int128(_626)
                let expr_4063 := _627
                /// @src 29:6583:6628  "int128 liquidityDelta = params.liquidityDelta"
                let var_liquidityDelta_4061 := expr_4063
                /// @src 29:6656:6662  "params"
                let _628_mpos := var_params_4051_mpos
                let expr_4067_mpos := _628_mpos
                /// @src 29:6656:6672  "params.tickLower"
                let _629 := add(expr_4067_mpos, 32)
                let _630 := read_from_memoryt_int24(_629)
                let expr_4068 := _630
                /// @src 29:6638:6672  "int24 tickLower = params.tickLower"
                let var_tickLower_4066 := expr_4068
                /// @src 29:6700:6706  "params"
                let _631_mpos := var_params_4051_mpos
                let expr_4072_mpos := _631_mpos
                /// @src 29:6700:6716  "params.tickUpper"
                let _632 := add(expr_4072_mpos, 64)
                let _633 := read_from_memoryt_int24(_632)
                let expr_4073 := _633
                /// @src 29:6682:6716  "int24 tickUpper = params.tickUpper"
                let var_tickUpper_4071 := expr_4073
                /// @src 29:6737:6746  "tickLower"
                let _634 := var_tickLower_4066
                let expr_4076 := _634
                /// @src 29:6748:6757  "tickUpper"
                let _635 := var_tickUpper_4071
                let expr_4077 := _635
                fun_checkTicks_3918(expr_4076, expr_4077)
                /// @src 29:6783:6816  "ModifyLiquidityState memory state"
                let var_state_4082_mpos
                let zero_t_struct$_ModifyLiquidityState_$4044_memory_ptr_636_mpos := zero_value_for_split_t_struct$_ModifyLiquidityState_$4044_memory_ptr()
                var_state_4082_mpos := zero_t_struct$_ModifyLiquidityState_$4044_memory_ptr_636_mpos
                /// @src 29:6888:6902  "liquidityDelta"
                let _637 := var_liquidityDelta_4061
                let expr_4084 := _637
                /// @src 29:6906:6907  "0"
                let expr_4085 := 0x00
                /// @src 29:6888:6907  "liquidityDelta != 0"
                let expr_4086 := iszero(eq(cleanup_t_int128(expr_4084), convert_t_rational_0_by_1_to_t_int128(expr_4085)))
                /// @src 29:6884:8072  "if (liquidityDelta != 0) {..."
                if expr_4086 {
                    /// @src 29:7013:7017  "self"
                    let _638_slot := var_self_4048_slot
                    let expr_4094_slot := _638_slot
                    /// @src 29:7019:7028  "tickLower"
                    let _639 := var_tickLower_4066
                    let expr_4095 := _639
                    /// @src 29:7030:7044  "liquidityDelta"
                    let _640 := var_liquidityDelta_4061
                    let expr_4096 := _640
                    /// @src 29:7046:7051  "false"
                    let expr_4097 := 0x00
                    /// @src 29:7002:7052  "updateTick(self, tickLower, liquidityDelta, false)"
                    let expr_4098_component_1, expr_4098_component_2 := fun_updateTick_5302(expr_4094_slot, expr_4095, expr_4096, expr_4097)
                    /// @src 29:6928:6933  "state"
                    let _641_mpos := var_state_4082_mpos
                    let expr_4087_mpos := _641_mpos
                    /// @src 29:6928:6946  "state.flippedLower"
                    let _642 := add(expr_4087_mpos, 0)
                    /// @src 29:6948:6953  "state"
                    let _643_mpos := var_state_4082_mpos
                    let expr_4090_mpos := _643_mpos
                    /// @src 29:6948:6978  "state.liquidityGrossAfterLower"
                    let _644 := add(expr_4090_mpos, 32)
                    /// @src 29:6927:7052  "(state.flippedLower, state.liquidityGrossAfterLower) =..."
                    let _645 := expr_4098_component_2
                    write_to_memory_t_uint128(_644, _645)
                    let _646 := expr_4098_component_1
                    write_to_memory_t_bool(_642, _646)
                    /// @src 29:7136:7140  "self"
                    let _647_slot := var_self_4048_slot
                    let expr_4108_slot := _647_slot
                    /// @src 29:7142:7151  "tickUpper"
                    let _648 := var_tickUpper_4071
                    let expr_4109 := _648
                    /// @src 29:7153:7167  "liquidityDelta"
                    let _649 := var_liquidityDelta_4061
                    let expr_4110 := _649
                    /// @src 29:7169:7173  "true"
                    let expr_4111 := 0x01
                    /// @src 29:7125:7174  "updateTick(self, tickUpper, liquidityDelta, true)"
                    let expr_4112_component_1, expr_4112_component_2 := fun_updateTick_5302(expr_4108_slot, expr_4109, expr_4110, expr_4111)
                    /// @src 29:7071:7076  "state"
                    let _650_mpos := var_state_4082_mpos
                    let expr_4101_mpos := _650_mpos
                    /// @src 29:7071:7089  "state.flippedUpper"
                    let _651 := add(expr_4101_mpos, 64)
                    /// @src 29:7091:7096  "state"
                    let _652_mpos := var_state_4082_mpos
                    let expr_4104_mpos := _652_mpos
                    /// @src 29:7091:7121  "state.liquidityGrossAfterUpper"
                    let _653 := add(expr_4104_mpos, 96)
                    /// @src 29:7070:7174  "(state.flippedUpper, state.liquidityGrossAfterUpper) = updateTick(self, tickUpper, liquidityDelta, true)"
                    let _654 := expr_4112_component_2
                    write_to_memory_t_uint128(_653, _654)
                    let _655 := expr_4112_component_1
                    write_to_memory_t_bool(_651, _655)
                    /// @src 29:7279:7293  "liquidityDelta"
                    let _656 := var_liquidityDelta_4061
                    let expr_4115 := _656
                    /// @src 29:7297:7298  "0"
                    let expr_4116 := 0x00
                    /// @src 29:7279:7298  "liquidityDelta >= 0"
                    let expr_4117 := iszero(slt(cleanup_t_int128(expr_4115), convert_t_rational_0_by_1_to_t_int128(expr_4116)))
                    /// @src 29:7275:7783  "if (liquidityDelta >= 0) {..."
                    if expr_4117 {
                        /// @src 29:7385:7391  "params"
                        let _657_mpos := var_params_4051_mpos
                        let expr_4121_mpos := _657_mpos
                        /// @src 29:7385:7403  "params.tickSpacing"
                        let _658 := add(expr_4121_mpos, 128)
                        let _659 := read_from_memoryt_int24(_658)
                        let expr_4122 := _659
                        /// @src 29:7352:7404  "tickSpacingToMaxLiquidityPerTick(params.tickSpacing)"
                        let expr_4123 := fun_tickSpacingToMaxLiquidityPerTick_5322(expr_4122)
                        /// @src 29:7322:7404  "uint128 maxLiquidityPerTick = tickSpacingToMaxLiquidityPerTick(params.tickSpacing)"
                        let var_maxLiquidityPerTick_4119 := expr_4123
                        /// @src 29:7430:7435  "state"
                        let _660_mpos := var_state_4082_mpos
                        let expr_4125_mpos := _660_mpos
                        /// @src 29:7430:7460  "state.liquidityGrossAfterLower"
                        let _661 := add(expr_4125_mpos, 32)
                        let _662 := read_from_memoryt_uint128(_661)
                        let expr_4126 := _662
                        /// @src 29:7463:7482  "maxLiquidityPerTick"
                        let _663 := var_maxLiquidityPerTick_4119
                        let expr_4127 := _663
                        /// @src 29:7430:7482  "state.liquidityGrossAfterLower > maxLiquidityPerTick"
                        let expr_4128 := gt(cleanup_t_uint128(expr_4126), cleanup_t_uint128(expr_4127))
                        /// @src 29:7426:7585  "if (state.liquidityGrossAfterLower > maxLiquidityPerTick) {..."
                        if expr_4128 {
                            /// @src 29:7510:7540  "TickLiquidityOverflow.selector"
                            let expr_4132 := 0xb8e3c38500000000000000000000000000000000000000000000000000000000
                            /// @src 29:7510:7551  "TickLiquidityOverflow.selector.revertWith"
                            let expr_4133_self := expr_4132
                            /// @src 29:7552:7561  "tickLower"
                            let _664 := var_tickLower_4066
                            let expr_4134 := _664
                            fun_revertWith_2294(expr_4133_self, expr_4134)
                            /// @src 29:7426:7585  "if (state.liquidityGrossAfterLower > maxLiquidityPerTick) {..."
                        }
                        /// @src 29:7610:7615  "state"
                        let _665_mpos := var_state_4082_mpos
                        let expr_4139_mpos := _665_mpos
                        /// @src 29:7610:7640  "state.liquidityGrossAfterUpper"
                        let _666 := add(expr_4139_mpos, 96)
                        let _667 := read_from_memoryt_uint128(_666)
                        let expr_4140 := _667
                        /// @src 29:7643:7662  "maxLiquidityPerTick"
                        let _668 := var_maxLiquidityPerTick_4119
                        let expr_4141 := _668
                        /// @src 29:7610:7662  "state.liquidityGrossAfterUpper > maxLiquidityPerTick"
                        let expr_4142 := gt(cleanup_t_uint128(expr_4140), cleanup_t_uint128(expr_4141))
                        /// @src 29:7606:7765  "if (state.liquidityGrossAfterUpper > maxLiquidityPerTick) {..."
                        if expr_4142 {
                            /// @src 29:7690:7720  "TickLiquidityOverflow.selector"
                            let expr_4146 := 0xb8e3c38500000000000000000000000000000000000000000000000000000000
                            /// @src 29:7690:7731  "TickLiquidityOverflow.selector.revertWith"
                            let expr_4147_self := expr_4146
                            /// @src 29:7732:7741  "tickUpper"
                            let _669 := var_tickUpper_4071
                            let expr_4148 := _669
                            fun_revertWith_2294(expr_4147_self, expr_4148)
                            /// @src 29:7606:7765  "if (state.liquidityGrossAfterUpper > maxLiquidityPerTick) {..."
                        }
                        /// @src 29:7275:7783  "if (liquidityDelta >= 0) {..."
                    }
                    /// @src 29:7805:7810  "state"
                    let _670_mpos := var_state_4082_mpos
                    let expr_4155_mpos := _670_mpos
                    /// @src 29:7805:7823  "state.flippedLower"
                    let _671 := add(expr_4155_mpos, 0)
                    let _672 := read_from_memoryt_bool(_671)
                    let expr_4156 := _672
                    /// @src 29:7801:7921  "if (state.flippedLower) {..."
                    if expr_4156 {
                        /// @src 29:7847:7851  "self"
                        let _673_slot := var_self_4048_slot
                        let expr_4157_slot := _673_slot
                        /// @src 29:7847:7862  "self.tickBitmap"
                        let _674 := add(expr_4157_slot, 5)
                        let _675_slot := _674
                        let expr_4160_slot := _675_slot
                        /// @src 29:7847:7871  "self.tickBitmap.flipTick"
                        let expr_4161_self_slot := expr_4160_slot
                        /// @src 29:7872:7881  "tickLower"
                        let _676 := var_tickLower_4066
                        let expr_4162 := _676
                        /// @src 29:7883:7889  "params"
                        let _677_mpos := var_params_4051_mpos
                        let expr_4163_mpos := _677_mpos
                        /// @src 29:7883:7901  "params.tickSpacing"
                        let _678 := add(expr_4163_mpos, 128)
                        let _679 := read_from_memoryt_int24(_678)
                        let expr_4164 := _679
                        fun_flipTick_8416(expr_4161_self_slot, expr_4162, expr_4164)
                        /// @src 29:7801:7921  "if (state.flippedLower) {..."
                    }
                    /// @src 29:7942:7947  "state"
                    let _680_mpos := var_state_4082_mpos
                    let expr_4169_mpos := _680_mpos
                    /// @src 29:7942:7960  "state.flippedUpper"
                    let _681 := add(expr_4169_mpos, 64)
                    let _682 := read_from_memoryt_bool(_681)
                    let expr_4170 := _682
                    /// @src 29:7938:8058  "if (state.flippedUpper) {..."
                    if expr_4170 {
                        /// @src 29:7984:7988  "self"
                        let _683_slot := var_self_4048_slot
                        let expr_4171_slot := _683_slot
                        /// @src 29:7984:7999  "self.tickBitmap"
                        let _684 := add(expr_4171_slot, 5)
                        let _685_slot := _684
                        let expr_4174_slot := _685_slot
                        /// @src 29:7984:8008  "self.tickBitmap.flipTick"
                        let expr_4175_self_slot := expr_4174_slot
                        /// @src 29:8009:8018  "tickUpper"
                        let _686 := var_tickUpper_4071
                        let expr_4176 := _686
                        /// @src 29:8020:8026  "params"
                        let _687_mpos := var_params_4051_mpos
                        let expr_4177_mpos := _687_mpos
                        /// @src 29:8020:8038  "params.tickSpacing"
                        let _688 := add(expr_4177_mpos, 128)
                        let _689 := read_from_memoryt_int24(_688)
                        let expr_4178 := _689
                        fun_flipTick_8416(expr_4175_self_slot, expr_4176, expr_4178)
                        /// @src 29:7938:8058  "if (state.flippedUpper) {..."
                    }
                    /// @src 29:6884:8072  "if (liquidityDelta != 0) {..."
                }
                /// @src 29:8206:8210  "self"
                let _690_slot := var_self_4048_slot
                let expr_4190_slot := _690_slot
                /// @src 29:8212:8221  "tickLower"
                let _691 := var_tickLower_4066
                let expr_4191 := _691
                /// @src 29:8223:8232  "tickUpper"
                let _692 := var_tickUpper_4071
                let expr_4192 := _692
                /// @src 29:8187:8233  "getFeeGrowthInside(self, tickLower, tickUpper)"
                let expr_4193_component_1, expr_4193_component_2 := fun_getFeeGrowthInside_5207(expr_4190_slot, expr_4191, expr_4192)
                /// @src 29:8104:8233  "(uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128) =..."
                let var_feeGrowthInside0X128_4186 := expr_4193_component_1
                let var_feeGrowthInside1X128_4188 := expr_4193_component_2
                /// @src 29:8286:8290  "self"
                let _693_slot := var_self_4048_slot
                let expr_4200_slot := _693_slot
                /// @src 29:8286:8300  "self.positions"
                let _694 := add(expr_4200_slot, 6)
                let _695_slot := _694
                let expr_4201_slot := _695_slot
                /// @src 29:8286:8304  "self.positions.get"
                let expr_4202_self_slot := expr_4201_slot
                /// @src 29:8305:8311  "params"
                let _696_mpos := var_params_4051_mpos
                let expr_4203_mpos := _696_mpos
                /// @src 29:8305:8317  "params.owner"
                let _697 := add(expr_4203_mpos, 0)
                let _698 := read_from_memoryt_address(_697)
                let expr_4204 := _698
                /// @src 29:8319:8328  "tickLower"
                let _699 := var_tickLower_4066
                let expr_4205 := _699
                /// @src 29:8330:8339  "tickUpper"
                let _700 := var_tickUpper_4071
                let expr_4206 := _700
                /// @src 29:8341:8347  "params"
                let _701_mpos := var_params_4051_mpos
                let expr_4207_mpos := _701_mpos
                /// @src 29:8341:8352  "params.salt"
                let _702 := add(expr_4207_mpos, 160)
                let _703 := read_from_memoryt_bytes32(_702)
                let expr_4208 := _703
                /// @src 29:8286:8353  "self.positions.get(params.owner, tickLower, tickUpper, params.salt)"
                let expr_4209_slot := fun_get_5469(expr_4202_self_slot, expr_4204, expr_4205, expr_4206, expr_4208)
                /// @src 29:8252:8353  "Position.State storage position = self.positions.get(params.owner, tickLower, tickUpper, params.salt)"
                let var_position_4199_slot := expr_4209_slot
                /// @src 29:8432:8440  "position"
                let _704_slot := var_position_4199_slot
                let expr_4215_slot := _704_slot
                /// @src 29:8432:8447  "position.update"
                let expr_4216_self_slot := expr_4215_slot
                /// @src 29:8448:8462  "liquidityDelta"
                let _705 := var_liquidityDelta_4061
                let expr_4217 := _705
                /// @src 29:8464:8484  "feeGrowthInside0X128"
                let _706 := var_feeGrowthInside0X128_4186
                let expr_4218 := _706
                /// @src 29:8486:8506  "feeGrowthInside1X128"
                let _707 := var_feeGrowthInside1X128_4188
                let expr_4219 := _707
                /// @src 29:8432:8507  "position.update(liquidityDelta, feeGrowthInside0X128, feeGrowthInside1X128)"
                let expr_4220_component_1, expr_4220_component_2 := fun_update_5574(expr_4216_self_slot, expr_4217, expr_4218, expr_4219)
                /// @src 29:8371:8507  "(uint256 feesOwed0, uint256 feesOwed1) =..."
                let var_feesOwed0_4212 := expr_4220_component_1
                let var_feesOwed1_4214 := expr_4220_component_2
                /// @src 29:8623:8632  "feesOwed0"
                let _708 := var_feesOwed0_4212
                let expr_4224 := _708
                /// @src 29:8623:8641  "feesOwed0.toInt128"
                let expr_4225_self := expr_4224
                /// @src 29:8623:8643  "feesOwed0.toInt128()"
                let expr_4226 := fun_toInt128_5750(expr_4225_self)
                /// @src 29:8645:8654  "feesOwed1"
                let _709 := var_feesOwed1_4214
                let expr_4227 := _709
                /// @src 29:8645:8663  "feesOwed1.toInt128"
                let expr_4228_self := expr_4227
                /// @src 29:8645:8665  "feesOwed1.toInt128()"
                let expr_4229 := fun_toInt128_5750(expr_4228_self)
                /// @src 29:8608:8666  "toBalanceDelta(feesOwed0.toInt128(), feesOwed1.toInt128())"
                let expr_4230 := fun_toBalanceDelta_6337(expr_4226, expr_4229)
                /// @src 29:8597:8666  "feeDelta = toBalanceDelta(feesOwed0.toInt128(), feesOwed1.toInt128())"
                var_feeDelta_4058 := expr_4230
                let expr_4231 := expr_4230
                /// @src 29:8759:8773  "liquidityDelta"
                let _710 := var_liquidityDelta_4061
                let expr_4234 := _710
                /// @src 29:8776:8777  "0"
                let expr_4235 := 0x00
                /// @src 29:8759:8777  "liquidityDelta < 0"
                let expr_4236 := slt(cleanup_t_int128(expr_4234), convert_t_rational_0_by_1_to_t_int128(expr_4235))
                /// @src 29:8755:9010  "if (liquidityDelta < 0) {..."
                if expr_4236 {
                    /// @src 29:8801:8806  "state"
                    let _711_mpos := var_state_4082_mpos
                    let expr_4237_mpos := _711_mpos
                    /// @src 29:8801:8819  "state.flippedLower"
                    let _712 := add(expr_4237_mpos, 0)
                    let _713 := read_from_memoryt_bool(_712)
                    let expr_4238 := _713
                    /// @src 29:8797:8888  "if (state.flippedLower) {..."
                    if expr_4238 {
                        /// @src 29:8853:8857  "self"
                        let _714_slot := var_self_4048_slot
                        let expr_4240_slot := _714_slot
                        /// @src 29:8859:8868  "tickLower"
                        let _715 := var_tickLower_4066
                        let expr_4241 := _715
                        fun_clearTick_5360(expr_4240_slot, expr_4241)
                        /// @src 29:8797:8888  "if (state.flippedLower) {..."
                    }
                    /// @src 29:8909:8914  "state"
                    let _716_mpos := var_state_4082_mpos
                    let expr_4246_mpos := _716_mpos
                    /// @src 29:8909:8927  "state.flippedUpper"
                    let _717 := add(expr_4246_mpos, 64)
                    let _718 := read_from_memoryt_bool(_717)
                    let expr_4247 := _718
                    /// @src 29:8905:8996  "if (state.flippedUpper) {..."
                    if expr_4247 {
                        /// @src 29:8961:8965  "self"
                        let _719_slot := var_self_4048_slot
                        let expr_4249_slot := _719_slot
                        /// @src 29:8967:8976  "tickUpper"
                        let _720 := var_tickUpper_4071
                        let expr_4250 := _720
                        fun_clearTick_5360(expr_4249_slot, expr_4250)
                        /// @src 29:8905:8996  "if (state.flippedUpper) {..."
                    }
                    /// @src 29:8755:9010  "if (liquidityDelta < 0) {..."
                }
                /// @src 29:9034:9048  "liquidityDelta"
                let _721 := var_liquidityDelta_4061
                let expr_4258 := _721
                /// @src 29:9052:9053  "0"
                let expr_4259 := 0x00
                /// @src 29:9034:9053  "liquidityDelta != 0"
                let expr_4260 := iszero(eq(cleanup_t_int128(expr_4258), convert_t_rational_0_by_1_to_t_int128(expr_4259)))
                /// @src 29:9030:10804  "if (liquidityDelta != 0) {..."
                if expr_4260 {
                    /// @src 29:9084:9088  "self"
                    let _722_slot := var_self_4048_slot
                    let expr_4264_slot := _722_slot
                    /// @src 29:9084:9094  "self.slot0"
                    let _723 := add(expr_4264_slot, 0)
                    let _724 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_723)
                    let expr_4265 := _724
                    /// @src 29:9069:9094  "Slot0 _slot0 = self.slot0"
                    let var__slot0_4263 := expr_4265
                    /// @src 29:9146:9152  "_slot0"
                    let _725 := var__slot0_4263
                    let expr_4271 := _725
                    /// @src 29:9146:9157  "_slot0.tick"
                    let expr_4272_self := expr_4271
                    /// @src 29:9146:9159  "_slot0.tick()"
                    let expr_4273 := fun_tick_8672(expr_4272_self)
                    /// @src 29:9145:9183  "(_slot0.tick(), _slot0.sqrtPriceX96())"
                    let expr_4277_component_1 := expr_4273
                    /// @src 29:9161:9167  "_slot0"
                    let _726 := var__slot0_4263
                    let expr_4274 := _726
                    /// @src 29:9161:9180  "_slot0.sqrtPriceX96"
                    let expr_4275_self := expr_4274
                    /// @src 29:9161:9182  "_slot0.sqrtPriceX96()"
                    let expr_4276 := fun_sqrtPriceX96_8662(expr_4275_self)
                    /// @src 29:9145:9183  "(_slot0.tick(), _slot0.sqrtPriceX96())"
                    let expr_4277_component_2 := expr_4276
                    /// @src 29:9108:9183  "(int24 tick, uint160 sqrtPriceX96) = (_slot0.tick(), _slot0.sqrtPriceX96())"
                    let var_tick_4268 := expr_4277_component_1
                    let var_sqrtPriceX96_4270 := expr_4277_component_2
                    /// @src 29:9201:9205  "tick"
                    let _727 := var_tick_4268
                    let expr_4279 := _727
                    /// @src 29:9208:9217  "tickLower"
                    let _728 := var_tickLower_4066
                    let expr_4280 := _728
                    /// @src 29:9201:9217  "tick < tickLower"
                    let expr_4281 := slt(cleanup_t_int24(expr_4279), cleanup_t_int24(expr_4280))
                    /// @src 29:9197:10794  "if (tick < tickLower) {..."
                    switch expr_4281
                    case 0 {
                        /// @src 29:9761:9765  "tick"
                        let _729 := var_tick_4268
                        let expr_4303 := _729
                        /// @src 29:9768:9777  "tickUpper"
                        let _730 := var_tickUpper_4071
                        let expr_4304 := _730
                        /// @src 29:9761:9777  "tick < tickUpper"
                        let expr_4305 := slt(cleanup_t_int24(expr_4303), cleanup_t_int24(expr_4304))
                        /// @src 29:9757:10794  "if (tick < tickUpper) {..."
                        switch expr_4305
                        case 0 {
                            /// @src 29:10556:10557  "0"
                            let expr_4347 := 0x00
                            /// @src 29:10579:10592  "SqrtPriceMath"
                            let expr_4348_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                            /// @src 29:10634:10642  "TickMath"
                            let expr_4350_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                            /// @src 29:10662:10671  "tickLower"
                            let _731 := var_tickLower_4066
                            let expr_4352 := _731
                            /// @src 29:10634:10672  "TickMath.getSqrtPriceAtTick(tickLower)"
                            let expr_4353 := fun_getSqrtPriceAtTick_6164(expr_4352)
                            /// @src 29:10674:10682  "TickMath"
                            let expr_4354_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                            /// @src 29:10702:10711  "tickUpper"
                            let _732 := var_tickUpper_4071
                            let expr_4356 := _732
                            /// @src 29:10674:10712  "TickMath.getSqrtPriceAtTick(tickUpper)"
                            let expr_4357 := fun_getSqrtPriceAtTick_6164(expr_4356)
                            /// @src 29:10714:10728  "liquidityDelta"
                            let _733 := var_liquidityDelta_4061
                            let expr_4358 := _733
                            /// @src 29:10579:10750  "SqrtPriceMath.getAmount1Delta(..."
                            let expr_4359 := fun_getAmount1Delta_8113(expr_4353, expr_4357, expr_4358)
                            /// @src 29:10579:10759  "SqrtPriceMath.getAmount1Delta(..."
                            let expr_4360_self := expr_4359
                            /// @src 29:10579:10761  "SqrtPriceMath.getAmount1Delta(..."
                            let expr_4361 := fun_toInt128_5693(expr_4360_self)
                            /// @src 29:10520:10779  "toBalanceDelta(..."
                            let _734 := convert_t_rational_0_by_1_to_t_int128(expr_4347)
                            let expr_4362 := fun_toBalanceDelta_6337(_734, expr_4361)
                            /// @src 29:10512:10779  "delta = toBalanceDelta(..."
                            var_delta_4055 := expr_4362
                            let expr_4363 := expr_4362
                            /// @src 29:9757:10794  "if (tick < tickUpper) {..."
                        }
                        default {
                            /// @src 29:9841:9854  "SqrtPriceMath"
                            let expr_4308_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                            /// @src 29:9871:9883  "sqrtPriceX96"
                            let _735 := var_sqrtPriceX96_4270
                            let expr_4310 := _735
                            /// @src 29:9885:9893  "TickMath"
                            let expr_4311_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                            /// @src 29:9913:9922  "tickUpper"
                            let _736 := var_tickUpper_4071
                            let expr_4313 := _736
                            /// @src 29:9885:9923  "TickMath.getSqrtPriceAtTick(tickUpper)"
                            let expr_4314 := fun_getSqrtPriceAtTick_6164(expr_4313)
                            /// @src 29:9925:9939  "liquidityDelta"
                            let _737 := var_liquidityDelta_4061
                            let expr_4315 := _737
                            /// @src 29:9841:9940  "SqrtPriceMath.getAmount0Delta(sqrtPriceX96, TickMath.getSqrtPriceAtTick(tickUpper), liquidityDelta)"
                            let expr_4316 := fun_getAmount0Delta_8070(expr_4310, expr_4314, expr_4315)
                            /// @src 29:9841:9974  "SqrtPriceMath.getAmount0Delta(sqrtPriceX96, TickMath.getSqrtPriceAtTick(tickUpper), liquidityDelta)..."
                            let expr_4317_self := expr_4316
                            /// @src 29:9841:9976  "SqrtPriceMath.getAmount0Delta(sqrtPriceX96, TickMath.getSqrtPriceAtTick(tickUpper), liquidityDelta)..."
                            let expr_4318 := fun_toInt128_5693(expr_4317_self)
                            /// @src 29:9998:10011  "SqrtPriceMath"
                            let expr_4319_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                            /// @src 29:10028:10036  "TickMath"
                            let expr_4321_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                            /// @src 29:10056:10065  "tickLower"
                            let _738 := var_tickLower_4066
                            let expr_4323 := _738
                            /// @src 29:10028:10066  "TickMath.getSqrtPriceAtTick(tickLower)"
                            let expr_4324 := fun_getSqrtPriceAtTick_6164(expr_4323)
                            /// @src 29:10068:10080  "sqrtPriceX96"
                            let _739 := var_sqrtPriceX96_4270
                            let expr_4325 := _739
                            /// @src 29:10082:10096  "liquidityDelta"
                            let _740 := var_liquidityDelta_4061
                            let expr_4326 := _740
                            /// @src 29:9998:10097  "SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(tickLower), sqrtPriceX96, liquidityDelta)"
                            let expr_4327 := fun_getAmount1Delta_8113(expr_4324, expr_4325, expr_4326)
                            /// @src 29:9998:10131  "SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(tickLower), sqrtPriceX96, liquidityDelta)..."
                            let expr_4328_self := expr_4327
                            /// @src 29:9998:10133  "SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(tickLower), sqrtPriceX96, liquidityDelta)..."
                            let expr_4329 := fun_toInt128_5693(expr_4328_self)
                            /// @src 29:9805:10151  "toBalanceDelta(..."
                            let expr_4330 := fun_toBalanceDelta_6337(expr_4318, expr_4329)
                            /// @src 29:9797:10151  "delta = toBalanceDelta(..."
                            var_delta_4055 := expr_4330
                            let expr_4331 := expr_4330
                            /// @src 29:10187:10200  "LiquidityMath"
                            let expr_4336_address := linkersymbol("src/libraries/LiquidityMath.sol:LiquidityMath")
                            /// @src 29:10210:10214  "self"
                            let _741_slot := var_self_4048_slot
                            let expr_4338_slot := _741_slot
                            /// @src 29:10210:10224  "self.liquidity"
                            let _742 := add(expr_4338_slot, 3)
                            let _743 := read_from_storage_split_offset_0_t_uint128(_742)
                            let expr_4339 := _743
                            /// @src 29:10226:10240  "liquidityDelta"
                            let _744 := var_liquidityDelta_4061
                            let expr_4340 := _744
                            /// @src 29:10187:10241  "LiquidityMath.addDelta(self.liquidity, liquidityDelta)"
                            let expr_4341 := fun_addDelta_7622(expr_4339, expr_4340)
                            /// @src 29:10170:10174  "self"
                            let _745_slot := var_self_4048_slot
                            let expr_4333_slot := _745_slot
                            /// @src 29:10170:10184  "self.liquidity"
                            let _746 := add(expr_4333_slot, 3)
                            /// @src 29:10170:10241  "self.liquidity = LiquidityMath.addDelta(self.liquidity, liquidityDelta)"
                            update_storage_value_offset_0t_uint128_to_t_uint128(_746, expr_4341)
                            let expr_4342 := expr_4341
                            /// @src 29:9757:10794  "if (tick < tickUpper) {..."
                        }
                        /// @src 29:9197:10794  "if (tick < tickLower) {..."
                    }
                    default {
                        /// @src 29:9513:9526  "SqrtPriceMath"
                        let expr_4284_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 29:9568:9576  "TickMath"
                        let expr_4286_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                        /// @src 29:9596:9605  "tickLower"
                        let _747 := var_tickLower_4066
                        let expr_4288 := _747
                        /// @src 29:9568:9606  "TickMath.getSqrtPriceAtTick(tickLower)"
                        let expr_4289 := fun_getSqrtPriceAtTick_6164(expr_4288)
                        /// @src 29:9608:9616  "TickMath"
                        let expr_4290_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                        /// @src 29:9636:9645  "tickUpper"
                        let _748 := var_tickUpper_4071
                        let expr_4292 := _748
                        /// @src 29:9608:9646  "TickMath.getSqrtPriceAtTick(tickUpper)"
                        let expr_4293 := fun_getSqrtPriceAtTick_6164(expr_4292)
                        /// @src 29:9648:9662  "liquidityDelta"
                        let _749 := var_liquidityDelta_4061
                        let expr_4294 := _749
                        /// @src 29:9513:9684  "SqrtPriceMath.getAmount0Delta(..."
                        let expr_4295 := fun_getAmount0Delta_8070(expr_4289, expr_4293, expr_4294)
                        /// @src 29:9513:9693  "SqrtPriceMath.getAmount0Delta(..."
                        let expr_4296_self := expr_4295
                        /// @src 29:9513:9695  "SqrtPriceMath.getAmount0Delta(..."
                        let expr_4297 := fun_toInt128_5693(expr_4296_self)
                        /// @src 29:9717:9718  "0"
                        let expr_4298 := 0x00
                        /// @src 29:9477:9736  "toBalanceDelta(..."
                        let _750 := convert_t_rational_0_by_1_to_t_int128(expr_4298)
                        let expr_4299 := fun_toBalanceDelta_6337(expr_4297, _750)
                        /// @src 29:9469:9736  "delta = toBalanceDelta(..."
                        var_delta_4055 := expr_4299
                        let expr_4300 := expr_4299
                        /// @src 29:9197:10794  "if (tick < tickLower) {..."
                    }
                    /// @src 29:9030:10804  "if (liquidityDelta != 0) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6366
            /// @src 38:672:1068  "function add(BalanceDelta a, BalanceDelta b) pure returns (BalanceDelta) {..."
            function fun_add_6366(var_a_6340, var_b_6343) -> var__6347 {
                /// @src 38:731:743  "BalanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_751 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var__6347 := zero_t_userDefinedValueType$_BalanceDelta_$6311_751

                /// @src 38:751:762  "int256 res0"
                let var_res0_6350
                let zero_t_int256_752 := zero_value_for_split_t_int256()
                var_res0_6350 := zero_t_int256_752
                /// @src 38:768:779  "int256 res1"
                let var_res1_6353
                let zero_t_int256_753 := zero_value_for_split_t_int256()
                var_res1_6353 := zero_t_int256_753
                /// @src 38:785:1005  "assembly (\"memory-safe\") {..."
                {
                    let usr$a0 := sar(128, var_a_6340)
                    let usr$a1 := signextend(15, var_a_6340)
                    let usr$b0 := sar(128, var_b_6343)
                    let usr$b1 := signextend(15, var_b_6343)
                    var_res0_6350 := add(usr$a0, usr$b0)
                    var_res1_6353 := add(usr$a1, usr$b1)
                }
                /// @src 38:1032:1036  "res0"
                let _754 := var_res0_6350
                let expr_6357 := _754
                /// @src 38:1032:1045  "res0.toInt128"
                let expr_6358_self := expr_6357
                /// @src 38:1032:1047  "res0.toInt128()"
                let expr_6359 := fun_toInt128_5693(expr_6358_self)
                /// @src 38:1049:1053  "res1"
                let _755 := var_res1_6353
                let expr_6360 := _755
                /// @src 38:1049:1062  "res1.toInt128"
                let expr_6361_self := expr_6360
                /// @src 38:1049:1064  "res1.toInt128()"
                let expr_6362 := fun_toInt128_5693(expr_6361_self)
                /// @src 38:1017:1065  "toBalanceDelta(res0.toInt128(), res1.toInt128())"
                let expr_6363 := fun_toBalanceDelta_6337(expr_6359, expr_6362)
                /// @src 38:1010:1065  "return toBalanceDelta(res0.toInt128(), res1.toInt128())"
                var__6347 := expr_6363
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_256_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_256_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_256_by_1(value)))
            }

            /// @src 23:1677:1739  "uint160 internal constant AFTER_REMOVE_LIQUIDITY_FLAG = 1 << 8"
            function constant_AFTER_REMOVE_LIQUIDITY_FLAG_2446() -> ret {
                /// @src 23:1733:1739  "1 << 8"
                let expr_2445 := 0x0100
                let _765 := convert_t_rational_256_by_1_to_t_uint160(expr_2445)

                ret := _765
            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_userDefinedValueType$_BalanceDelta_$6311_t_userDefinedValueType$_BalanceDelta_$6311_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_int256_t_int256_t_bytes_memory_ptr__fromStack(headStart , value0, value1, value2, value3, value4, value5, value6) -> tail {
                tail := add(headStart, 416)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_to_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_fromStack(value2,  add(headStart, 192))

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value3,  add(headStart, 320))

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value4,  add(headStart, 352))

                mstore(add(headStart, 384), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value5, value6,  tail)

            }

            function convert_t_rational_1_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_1_by_1(value)))
            }

            /// @src 23:2198:2274  "uint160 internal constant AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG = 1 << 0"
            function constant_AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG_2486() -> ret {
                /// @src 23:2268:2274  "1 << 0"
                let expr_2485 := 0x01
                let _775 := convert_t_rational_1_by_1_to_t_uint160(expr_2485)

                ret := _775
            }

            function cleanup_t_rational_1024_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1024_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_1024_by_1(value)))
            }

            /// @src 23:1541:1601  "uint160 internal constant AFTER_ADD_LIQUIDITY_FLAG = 1 << 10"
            function constant_AFTER_ADD_LIQUIDITY_FLAG_2436() -> ret {
                /// @src 23:1594:1601  "1 << 10"
                let expr_2435 := 0x0400
                let _779 := convert_t_rational_1024_by_1_to_t_uint160(expr_2435)

                ret := _779
            }

            function cleanup_t_rational_2_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_2_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_2_by_1(value)))
            }

            /// @src 23:2119:2192  "uint160 internal constant AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG = 1 << 1"
            function constant_AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG_2481() -> ret {
                /// @src 23:2186:2192  "1 << 1"
                let expr_2480 := 0x02
                let _789 := convert_t_rational_2_by_1_to_t_uint160(expr_2480)

                ret := _789
            }

            /// @ast-id 3153
            /// @src 23:10471:12029  "function afterModifyLiquidity(..."
            function fun_afterModifyLiquidity_3153(var_self_3029_address, var_key_3032_mpos, var_params_3035_mpos, var_delta_3038, var_feesAccrued_3041, var_hookData_3043_offset, var_hookData_3043_length) -> var_callerDelta_3047, var_hookDelta_3050 {
                /// @src 23:10714:10738  "BalanceDelta callerDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_756 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_callerDelta_3047 := zero_t_userDefinedValueType$_BalanceDelta_$6311_756
                /// @src 23:10740:10762  "BalanceDelta hookDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_757 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_hookDelta_3050 := zero_t_userDefinedValueType$_BalanceDelta_$6311_757

                /// @src 23:10778:10788  "msg.sender"
                let expr_3053 := caller()
                /// @src 23:10800:10804  "self"
                let _758_address := var_self_3029_address
                let expr_3056_address := _758_address
                /// @src 23:10792:10805  "address(self)"
                let expr_3057 := convert_t_contract$_IHooks_$1840_to_t_address(expr_3056_address)
                /// @src 23:10778:10805  "msg.sender == address(self)"
                let expr_3058 := eq(cleanup_t_address(expr_3053), cleanup_t_address(expr_3057))
                /// @src 23:10774:10853  "if (msg.sender == address(self)) return (delta, BalanceDeltaLibrary.ZERO_DELTA)"
                if expr_3058 {
                    /// @src 23:10815:10820  "delta"
                    let _759 := var_delta_3038
                    let expr_3059 := _759
                    /// @src 23:10814:10853  "(delta, BalanceDeltaLibrary.ZERO_DELTA)"
                    let expr_3062_component_1 := expr_3059
                    /// @src 23:10822:10841  "BalanceDeltaLibrary"
                    let expr_3060_address := linkersymbol("src/types/BalanceDelta.sol:BalanceDeltaLibrary")
                    /// @src 23:10822:10852  "BalanceDeltaLibrary.ZERO_DELTA"
                    let expr_3061 := constant_ZERO_DELTA_6448()
                    /// @src 23:10814:10853  "(delta, BalanceDeltaLibrary.ZERO_DELTA)"
                    let expr_3062_component_2 := expr_3061
                    /// @src 23:10807:10853  "return (delta, BalanceDeltaLibrary.ZERO_DELTA)"
                    var_callerDelta_3047 := expr_3062_component_1
                    var_hookDelta_3050 := expr_3062_component_2
                    leave
                    /// @src 23:10774:10853  "if (msg.sender == address(self)) return (delta, BalanceDeltaLibrary.ZERO_DELTA)"
                }
                /// @src 23:10878:10883  "delta"
                let _760 := var_delta_3038
                let expr_3066 := _760
                /// @src 23:10864:10883  "callerDelta = delta"
                var_callerDelta_3047 := expr_3066
                let expr_3067 := expr_3066
                /// @src 23:10897:10903  "params"
                let _761_mpos := var_params_3035_mpos
                let expr_3069_mpos := _761_mpos
                /// @src 23:10897:10918  "params.liquidityDelta"
                let _762 := add(expr_3069_mpos, 64)
                let _763 := read_from_memoryt_int256(_762)
                let expr_3070 := _763
                /// @src 23:10921:10922  "0"
                let expr_3071 := 0x00
                /// @src 23:10897:10922  "params.liquidityDelta > 0"
                let expr_3072 := sgt(cleanup_t_int256(expr_3070), convert_t_rational_0_by_1_to_t_int256(expr_3071))
                /// @src 23:10893:12023  "if (params.liquidityDelta > 0) {..."
                switch expr_3072
                case 0 {
                    /// @src 23:11490:11494  "self"
                    let _764_address := var_self_3029_address
                    let expr_3112_address := _764_address
                    /// @src 23:11490:11508  "self.hasPermission"
                    let expr_3113_self_address := expr_3112_address
                    /// @src 23:11509:11536  "AFTER_REMOVE_LIQUIDITY_FLAG"
                    let expr_3114 := constant_AFTER_REMOVE_LIQUIDITY_FLAG_2446()
                    /// @src 23:11490:11537  "self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)"
                    let expr_3115 := fun_hasPermission_3529(expr_3113_self_address, expr_3114)
                    /// @src 23:11486:12013  "if (self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)) {..."
                    if expr_3115 {
                        /// @src 23:11608:11612  "self"
                        let _766_address := var_self_3029_address
                        let expr_3119_address := _766_address
                        /// @src 23:11608:11636  "self.callHookWithReturnDelta"
                        let expr_3120_self_address := expr_3119_address
                        /// @src 23:11736:11746  "msg.sender"
                        let expr_3126 := caller()
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_1 := expr_3126
                        /// @src 23:11748:11751  "key"
                        let _767_mpos := var_key_3032_mpos
                        let expr_3127_mpos := _767_mpos
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_2_mpos := expr_3127_mpos
                        /// @src 23:11753:11759  "params"
                        let _768_mpos := var_params_3035_mpos
                        let expr_3128_mpos := _768_mpos
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_3_mpos := expr_3128_mpos
                        /// @src 23:11761:11766  "delta"
                        let _769 := var_delta_3038
                        let expr_3129 := _769
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_4 := expr_3129
                        /// @src 23:11768:11779  "feesAccrued"
                        let _770 := var_feesAccrued_3041
                        let expr_3130 := _770
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_5 := expr_3130
                        /// @src 23:11781:11789  "hookData"
                        let _771_offset := var_hookData_3043_offset
                        let _771_length := var_hookData_3043_length
                        let expr_3131_offset := _771_offset
                        let expr_3131_length := _771_length
                        /// @src 23:11735:11790  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3132_component_6_offset := expr_3131_offset
                        let expr_3132_component_6_length := expr_3131_length
                        /// @src 23:11662:11816  "abi.encodeCall(..."

                        let expr_3133_mpos := allocate_unbounded()
                        let _772 := add(expr_3133_mpos, 0x20)

                        mstore(_772, 0x6c2bbe7e00000000000000000000000000000000000000000000000000000000)
                        _772 := add(_772, 4)

                        let _773 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_userDefinedValueType$_BalanceDelta_$6311_t_userDefinedValueType$_BalanceDelta_$6311_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_int256_t_int256_t_bytes_memory_ptr__fromStack(_772, expr_3126, expr_3127_mpos, expr_3128_mpos, expr_3129, expr_3130, expr_3131_offset, expr_3131_length)
                        mstore(expr_3133_mpos, sub(_773, add(expr_3133_mpos, 0x20)))
                        finalize_allocation(expr_3133_mpos, sub(_773, expr_3133_mpos))
                        /// @src 23:11842:11846  "self"
                        let _774_address := var_self_3029_address
                        let expr_3134_address := _774_address
                        /// @src 23:11842:11860  "self.hasPermission"
                        let expr_3135_self_address := expr_3134_address
                        /// @src 23:11861:11902  "AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG"
                        let expr_3136 := constant_AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG_2486()
                        /// @src 23:11842:11903  "self.hasPermission(AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG)"
                        let expr_3137 := fun_hasPermission_3529(expr_3135_self_address, expr_3136)
                        /// @src 23:11608:11925  "self.callHookWithReturnDelta(..."
                        let expr_3138 := fun_callHookWithReturnDelta_2858(expr_3120_self_address, expr_3133_mpos, expr_3137)
                        /// @src 23:11569:11943  "BalanceDelta.wrap(..."
                        let expr_3139 := convert_t_int256_to_t_int256(expr_3138)
                        /// @src 23:11557:11943  "hookDelta = BalanceDelta.wrap(..."
                        var_hookDelta_3050 := expr_3139
                        let expr_3140 := expr_3139
                        /// @src 23:11975:11986  "callerDelta"
                        let _776 := var_callerDelta_3047
                        let expr_3143 := _776
                        /// @src 23:11989:11998  "hookDelta"
                        let _777 := var_hookDelta_3050
                        let expr_3144 := _777
                        /// @src 23:11975:11998  "callerDelta - hookDelta"
                        let expr_3145 := fun_sub_6395(expr_3143, expr_3144)
                        /// @src 23:11961:11998  "callerDelta = callerDelta - hookDelta"
                        var_callerDelta_3047 := expr_3145
                        let expr_3146 := expr_3145
                        /// @src 23:11486:12013  "if (self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)) {..."
                    }
                    /// @src 23:10893:12023  "if (params.liquidityDelta > 0) {..."
                }
                default {
                    /// @src 23:10942:10946  "self"
                    let _778_address := var_self_3029_address
                    let expr_3073_address := _778_address
                    /// @src 23:10942:10960  "self.hasPermission"
                    let expr_3074_self_address := expr_3073_address
                    /// @src 23:10961:10985  "AFTER_ADD_LIQUIDITY_FLAG"
                    let expr_3075 := constant_AFTER_ADD_LIQUIDITY_FLAG_2436()
                    /// @src 23:10942:10986  "self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG)"
                    let expr_3076 := fun_hasPermission_3529(expr_3074_self_address, expr_3075)
                    /// @src 23:10938:11456  "if (self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG)) {..."
                    if expr_3076 {
                        /// @src 23:11057:11061  "self"
                        let _780_address := var_self_3029_address
                        let expr_3080_address := _780_address
                        /// @src 23:11057:11085  "self.callHookWithReturnDelta"
                        let expr_3081_self_address := expr_3080_address
                        /// @src 23:11182:11192  "msg.sender"
                        let expr_3087 := caller()
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_1 := expr_3087
                        /// @src 23:11194:11197  "key"
                        let _781_mpos := var_key_3032_mpos
                        let expr_3088_mpos := _781_mpos
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_2_mpos := expr_3088_mpos
                        /// @src 23:11199:11205  "params"
                        let _782_mpos := var_params_3035_mpos
                        let expr_3089_mpos := _782_mpos
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_3_mpos := expr_3089_mpos
                        /// @src 23:11207:11212  "delta"
                        let _783 := var_delta_3038
                        let expr_3090 := _783
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_4 := expr_3090
                        /// @src 23:11214:11225  "feesAccrued"
                        let _784 := var_feesAccrued_3041
                        let expr_3091 := _784
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_5 := expr_3091
                        /// @src 23:11227:11235  "hookData"
                        let _785_offset := var_hookData_3043_offset
                        let _785_length := var_hookData_3043_length
                        let expr_3092_offset := _785_offset
                        let expr_3092_length := _785_length
                        /// @src 23:11181:11236  "(msg.sender, key, params, delta, feesAccrued, hookData)"
                        let expr_3093_component_6_offset := expr_3092_offset
                        let expr_3093_component_6_length := expr_3092_length
                        /// @src 23:11111:11262  "abi.encodeCall(..."

                        let expr_3094_mpos := allocate_unbounded()
                        let _786 := add(expr_3094_mpos, 0x20)

                        mstore(_786, 0x9f063efc00000000000000000000000000000000000000000000000000000000)
                        _786 := add(_786, 4)

                        let _787 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_userDefinedValueType$_BalanceDelta_$6311_t_userDefinedValueType$_BalanceDelta_$6311_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_ModifyLiquidityParams_$6887_memory_ptr_t_int256_t_int256_t_bytes_memory_ptr__fromStack(_786, expr_3087, expr_3088_mpos, expr_3089_mpos, expr_3090, expr_3091, expr_3092_offset, expr_3092_length)
                        mstore(expr_3094_mpos, sub(_787, add(expr_3094_mpos, 0x20)))
                        finalize_allocation(expr_3094_mpos, sub(_787, expr_3094_mpos))
                        /// @src 23:11288:11292  "self"
                        let _788_address := var_self_3029_address
                        let expr_3095_address := _788_address
                        /// @src 23:11288:11306  "self.hasPermission"
                        let expr_3096_self_address := expr_3095_address
                        /// @src 23:11307:11345  "AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG"
                        let expr_3097 := constant_AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG_2481()
                        /// @src 23:11288:11346  "self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG)"
                        let expr_3098 := fun_hasPermission_3529(expr_3096_self_address, expr_3097)
                        /// @src 23:11057:11368  "self.callHookWithReturnDelta(..."
                        let expr_3099 := fun_callHookWithReturnDelta_2858(expr_3081_self_address, expr_3094_mpos, expr_3098)
                        /// @src 23:11018:11386  "BalanceDelta.wrap(..."
                        let expr_3100 := convert_t_int256_to_t_int256(expr_3099)
                        /// @src 23:11006:11386  "hookDelta = BalanceDelta.wrap(..."
                        var_hookDelta_3050 := expr_3100
                        let expr_3101 := expr_3100
                        /// @src 23:11418:11429  "callerDelta"
                        let _790 := var_callerDelta_3047
                        let expr_3104 := _790
                        /// @src 23:11432:11441  "hookDelta"
                        let _791 := var_hookDelta_3050
                        let expr_3105 := _791
                        /// @src 23:11418:11441  "callerDelta - hookDelta"
                        let expr_3106 := fun_sub_6395(expr_3104, expr_3105)
                        /// @src 23:11404:11441  "callerDelta = callerDelta - hookDelta"
                        var_callerDelta_3047 := expr_3106
                        let expr_3107 := expr_3106
                        /// @src 23:10938:11456  "if (self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG)) {..."
                    }
                    /// @src 23:10893:12023  "if (params.liquidityDelta > 0) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6439
            /// @src 38:1598:1727  "function neq(BalanceDelta a, BalanceDelta b) pure returns (bool) {..."
            function fun_neq_6439(var_a_6420, var_b_6423) -> var__6426 {
                /// @src 38:1657:1661  "bool"
                let zero_t_bool_792 := zero_value_for_split_t_bool()
                var__6426 := zero_t_bool_792

                /// @src 38:1696:1697  "a"
                let _793 := var_a_6420
                let expr_6430 := _793
                /// @src 38:1676:1698  "BalanceDelta.unwrap(a)"
                let expr_6431 := convert_t_int256_to_t_int256(expr_6430)
                /// @src 38:1722:1723  "b"
                let _794 := var_b_6423
                let expr_6434 := _794
                /// @src 38:1702:1724  "BalanceDelta.unwrap(b)"
                let expr_6435 := convert_t_int256_to_t_int256(expr_6434)
                /// @src 38:1676:1724  "BalanceDelta.unwrap(a) != BalanceDelta.unwrap(b)"
                let expr_6436 := iszero(eq(cleanup_t_int256(expr_6431), cleanup_t_int256(expr_6435)))
                /// @src 38:1669:1724  "return BalanceDelta.unwrap(a) != BalanceDelta.unwrap(b)"
                var__6426 := expr_6436
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2294
            /// @src 19:1357:1580  "function revertWith(bytes4 selector, int24 value) internal pure {..."
            function fun_revertWith_2294(var_selector_2287, var_value_2289) {

                /// @src 19:1431:1574  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, var_selector_2287)
                    mstore(0x04, signextend(2, var_value_2289))
                    revert(0, 0x24)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6624
            /// @src 40:789:941  "function greaterThanOrEqualTo(Currency currency, Currency other) pure returns (bool) {..."
            function fun_greaterThanOrEqualTo_6624(var_currency_6605, var_other_6608) -> var__6611 {
                /// @src 40:868:872  "bool"
                let zero_t_bool_795 := zero_value_for_split_t_bool()
                var__6611 := zero_t_bool_795

                /// @src 40:903:911  "currency"
                let _796 := var_currency_6605
                let expr_6615 := _796
                /// @src 40:887:912  "Currency.unwrap(currency)"
                let expr_6616 := convert_t_address_to_t_address(expr_6615)
                /// @src 40:932:937  "other"
                let _797 := var_other_6608
                let expr_6619 := _797
                /// @src 40:916:938  "Currency.unwrap(other)"
                let expr_6620 := convert_t_address_to_t_address(expr_6619)
                /// @src 40:887:938  "Currency.unwrap(currency) >= Currency.unwrap(other)"
                let expr_6621 := iszero(lt(cleanup_t_address(expr_6616), cleanup_t_address(expr_6620)))
                /// @src 40:880:938  "return Currency.unwrap(currency) >= Currency.unwrap(other)"
                var__6611 := expr_6621
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2340
            /// @src 19:2915:3333  "function revertWith(bytes4 selector, address value1, address value2) internal pure {..."
            function fun_revertWith_2340(var_selector_2331, var_value1_2333, var_value2_2335) {

                /// @src 19:3008:3327  "assembly (\"memory-safe\") {..."
                {
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, var_selector_2331)
                    mstore(add(usr$fmp, 0x04), and(var_value1_2333, 0xffffffffffffffffffffffffffffffffffffffff))
                    mstore(add(usr$fmp, 0x24), and(var_value2_2335, 0xffffffffffffffffffffffffffffffffffffffff))
                    revert(usr$fmp, 0x44)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_128_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_128_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_128_by_1(value)))
            }

            /// @src 23:1746:1797  "uint160 internal constant BEFORE_SWAP_FLAG = 1 << 7"
            function constant_BEFORE_SWAP_FLAG_2451() -> ret {
                /// @src 23:1791:1797  "1 << 7"
                let expr_2450 := 0x80
                let _800 := convert_t_rational_128_by_1_to_t_uint160(expr_2450)

                ret := _800
            }

            function cleanup_t_rational_8_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_8_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_8_by_1(value)))
            }

            /// @src 23:1978:2043  "uint160 internal constant BEFORE_SWAP_RETURNS_DELTA_FLAG = 1 << 3"
            function constant_BEFORE_SWAP_RETURNS_DELTA_FLAG_2471() -> ret {
                /// @src 23:2037:2043  "1 << 3"
                let expr_2470 := 0x08
                let _802 := convert_t_rational_8_by_1_to_t_uint160(expr_2470)

                ret := _802
            }

            function cleanup_t_rational_64_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_64_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_64_by_1(value)))
            }

            /// @src 23:1803:1853  "uint160 internal constant AFTER_SWAP_FLAG = 1 << 6"
            function constant_AFTER_SWAP_FLAG_2456() -> ret {
                /// @src 23:1847:1853  "1 << 6"
                let expr_2455 := 0x40
                let _804 := convert_t_rational_64_by_1_to_t_uint160(expr_2455)

                ret := _804
            }

            function cleanup_t_rational_4_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_4_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_4_by_1(value)))
            }

            /// @src 23:2049:2113  "uint160 internal constant AFTER_SWAP_RETURNS_DELTA_FLAG = 1 << 2"
            function constant_AFTER_SWAP_RETURNS_DELTA_FLAG_2476() -> ret {
                /// @src 23:2107:2113  "1 << 2"
                let expr_2475 := 0x04
                let _806 := convert_t_rational_4_by_1_to_t_uint160(expr_2475)

                ret := _806
            }

            function cleanup_t_rational_16383_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_16383_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_16383_by_1(value)))
            }

            /// @src 23:1275:1339  "uint160 internal constant ALL_HOOK_MASK = uint160((1 << 14) - 1)"
            function constant_ALL_HOOK_MASK_2416() -> ret {
                /// @src 23:1325:1338  "(1 << 14) - 1"
                let expr_2414 := 0x3fff
                /// @src 23:1317:1339  "uint160((1 << 14) - 1)"
                let expr_2415 := convert_t_rational_16383_by_1_to_t_uint160(expr_2414)
                let _813 := expr_2415

                ret := _813
            }

            /// @ast-id 2760
            /// @src 23:5485:6604  "function isValidHookAddress(IHooks self, uint24 fee) internal pure returns (bool) {..."
            function fun_isValidHookAddress_2760(var_self_2668_address, var_fee_2670) -> var__2673 {
                /// @src 23:5561:5565  "bool"
                let zero_t_bool_798 := zero_value_for_split_t_bool()
                var__2673 := zero_t_bool_798

                /// @src 23:5704:5708  "self"
                let _799_address := var_self_2668_address
                let expr_2675_address := _799_address
                /// @src 23:5704:5722  "self.hasPermission"
                let expr_2676_self_address := expr_2675_address
                /// @src 23:5723:5739  "BEFORE_SWAP_FLAG"
                let expr_2677 := constant_BEFORE_SWAP_FLAG_2451()
                /// @src 23:5704:5740  "self.hasPermission(BEFORE_SWAP_FLAG)"
                let expr_2678 := fun_hasPermission_3529(expr_2676_self_address, expr_2677)
                /// @src 23:5703:5740  "!self.hasPermission(BEFORE_SWAP_FLAG)"
                let expr_2679 := cleanup_t_bool(iszero(expr_2678))
                /// @src 23:5703:5794  "!self.hasPermission(BEFORE_SWAP_FLAG) && self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)"
                let expr_2684 := expr_2679
                if expr_2684 {
                    /// @src 23:5744:5748  "self"
                    let _801_address := var_self_2668_address
                    let expr_2680_address := _801_address
                    /// @src 23:5744:5762  "self.hasPermission"
                    let expr_2681_self_address := expr_2680_address
                    /// @src 23:5763:5793  "BEFORE_SWAP_RETURNS_DELTA_FLAG"
                    let expr_2682 := constant_BEFORE_SWAP_RETURNS_DELTA_FLAG_2471()
                    /// @src 23:5744:5794  "self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)"
                    let expr_2683 := fun_hasPermission_3529(expr_2681_self_address, expr_2682)
                    /// @src 23:5703:5794  "!self.hasPermission(BEFORE_SWAP_FLAG) && self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)"
                    expr_2684 := expr_2683
                }
                /// @src 23:5699:5808  "if (!self.hasPermission(BEFORE_SWAP_FLAG) && self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)) return false"
                if expr_2684 {
                    /// @src 23:5803:5808  "false"
                    let expr_2685 := 0x00
                    /// @src 23:5796:5808  "return false"
                    var__2673 := expr_2685
                    leave
                    /// @src 23:5699:5808  "if (!self.hasPermission(BEFORE_SWAP_FLAG) && self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)) return false"
                }
                /// @src 23:5823:5827  "self"
                let _803_address := var_self_2668_address
                let expr_2688_address := _803_address
                /// @src 23:5823:5841  "self.hasPermission"
                let expr_2689_self_address := expr_2688_address
                /// @src 23:5842:5857  "AFTER_SWAP_FLAG"
                let expr_2690 := constant_AFTER_SWAP_FLAG_2456()
                /// @src 23:5823:5858  "self.hasPermission(AFTER_SWAP_FLAG)"
                let expr_2691 := fun_hasPermission_3529(expr_2689_self_address, expr_2690)
                /// @src 23:5822:5858  "!self.hasPermission(AFTER_SWAP_FLAG)"
                let expr_2692 := cleanup_t_bool(iszero(expr_2691))
                /// @src 23:5822:5911  "!self.hasPermission(AFTER_SWAP_FLAG) && self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)"
                let expr_2697 := expr_2692
                if expr_2697 {
                    /// @src 23:5862:5866  "self"
                    let _805_address := var_self_2668_address
                    let expr_2693_address := _805_address
                    /// @src 23:5862:5880  "self.hasPermission"
                    let expr_2694_self_address := expr_2693_address
                    /// @src 23:5881:5910  "AFTER_SWAP_RETURNS_DELTA_FLAG"
                    let expr_2695 := constant_AFTER_SWAP_RETURNS_DELTA_FLAG_2476()
                    /// @src 23:5862:5911  "self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)"
                    let expr_2696 := fun_hasPermission_3529(expr_2694_self_address, expr_2695)
                    /// @src 23:5822:5911  "!self.hasPermission(AFTER_SWAP_FLAG) && self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)"
                    expr_2697 := expr_2696
                }
                /// @src 23:5818:5925  "if (!self.hasPermission(AFTER_SWAP_FLAG) && self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)) return false"
                if expr_2697 {
                    /// @src 23:5920:5925  "false"
                    let expr_2698 := 0x00
                    /// @src 23:5913:5925  "return false"
                    var__2673 := expr_2698
                    leave
                    /// @src 23:5818:5925  "if (!self.hasPermission(AFTER_SWAP_FLAG) && self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)) return false"
                }
                /// @src 23:5940:5944  "self"
                let _807_address := var_self_2668_address
                let expr_2701_address := _807_address
                /// @src 23:5940:5958  "self.hasPermission"
                let expr_2702_self_address := expr_2701_address
                /// @src 23:5959:5983  "AFTER_ADD_LIQUIDITY_FLAG"
                let expr_2703 := constant_AFTER_ADD_LIQUIDITY_FLAG_2436()
                /// @src 23:5940:5984  "self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG)"
                let expr_2704 := fun_hasPermission_3529(expr_2702_self_address, expr_2703)
                /// @src 23:5939:5984  "!self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG)"
                let expr_2705 := cleanup_t_bool(iszero(expr_2704))
                /// @src 23:5939:6046  "!self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG) && self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG)"
                let expr_2710 := expr_2705
                if expr_2710 {
                    /// @src 23:5988:5992  "self"
                    let _808_address := var_self_2668_address
                    let expr_2706_address := _808_address
                    /// @src 23:5988:6006  "self.hasPermission"
                    let expr_2707_self_address := expr_2706_address
                    /// @src 23:6007:6045  "AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG"
                    let expr_2708 := constant_AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG_2481()
                    /// @src 23:5988:6046  "self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG)"
                    let expr_2709 := fun_hasPermission_3529(expr_2707_self_address, expr_2708)
                    /// @src 23:5939:6046  "!self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG) && self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG)"
                    expr_2710 := expr_2709
                }
                /// @src 23:5935:6093  "if (!self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG) && self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG))..."
                if expr_2710 {
                    /// @src 23:6077:6082  "false"
                    let expr_2711 := 0x00
                    /// @src 23:6070:6082  "return false"
                    var__2673 := expr_2711
                    leave
                    /// @src 23:5935:6093  "if (!self.hasPermission(AFTER_ADD_LIQUIDITY_FLAG) && self.hasPermission(AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG))..."
                }
                /// @src 23:6120:6124  "self"
                let _809_address := var_self_2668_address
                let expr_2715_address := _809_address
                /// @src 23:6120:6138  "self.hasPermission"
                let expr_2716_self_address := expr_2715_address
                /// @src 23:6139:6166  "AFTER_REMOVE_LIQUIDITY_FLAG"
                let expr_2717 := constant_AFTER_REMOVE_LIQUIDITY_FLAG_2446()
                /// @src 23:6120:6167  "self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)"
                let expr_2718 := fun_hasPermission_3529(expr_2716_self_address, expr_2717)
                /// @src 23:6119:6167  "!self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)"
                let expr_2719 := cleanup_t_bool(iszero(expr_2718))
                /// @src 23:6119:6248  "!self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)..."
                let expr_2724 := expr_2719
                if expr_2724 {
                    /// @src 23:6187:6191  "self"
                    let _810_address := var_self_2668_address
                    let expr_2720_address := _810_address
                    /// @src 23:6187:6205  "self.hasPermission"
                    let expr_2721_self_address := expr_2720_address
                    /// @src 23:6206:6247  "AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG"
                    let expr_2722 := constant_AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG_2486()
                    /// @src 23:6187:6248  "self.hasPermission(AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG)"
                    let expr_2723 := fun_hasPermission_3529(expr_2721_self_address, expr_2722)
                    /// @src 23:6119:6248  "!self.hasPermission(AFTER_REMOVE_LIQUIDITY_FLAG)..."
                    expr_2724 := expr_2723
                }
                /// @src 23:6102:6271  "if (..."
                if expr_2724 {
                    /// @src 23:6266:6271  "false"
                    let expr_2725 := 0x00
                    /// @src 23:6259:6271  "return false"
                    var__2673 := expr_2725
                    leave
                    /// @src 23:6102:6271  "if (..."
                }
                /// @src 23:6463:6467  "self"
                let _811_address := var_self_2668_address
                let expr_2730_address := _811_address
                /// @src 23:6455:6468  "address(self)"
                let expr_2731 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2730_address)
                /// @src 23:6480:6481  "0"
                let expr_2734 := 0x00
                /// @src 23:6472:6482  "address(0)"
                let expr_2735 := convert_t_rational_0_by_1_to_t_address(expr_2734)
                /// @src 23:6455:6482  "address(self) == address(0)"
                let expr_2736 := eq(cleanup_t_address(expr_2731), cleanup_t_address(expr_2735))
                /// @src 23:6455:6597  "address(self) == address(0)..."
                let expr_2757
                switch expr_2736
                case 0 {
                    /// @src 23:6548:6552  "self"
                    let _812_address := var_self_2668_address
                    let expr_2745_address := _812_address
                    /// @src 23:6540:6553  "address(self)"
                    let expr_2746 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2745_address)
                    /// @src 23:6532:6554  "uint160(address(self))"
                    let expr_2747 := convert_t_address_to_t_uint160(expr_2746)
                    /// @src 23:6557:6570  "ALL_HOOK_MASK"
                    let expr_2748 := constant_ALL_HOOK_MASK_2416()
                    /// @src 23:6532:6570  "uint160(address(self)) & ALL_HOOK_MASK"
                    let expr_2749 := and(expr_2747, expr_2748)

                    /// @src 23:6573:6574  "0"
                    let expr_2750 := 0x00
                    /// @src 23:6532:6574  "uint160(address(self)) & ALL_HOOK_MASK > 0"
                    let expr_2751 := gt(cleanup_t_uint160(expr_2749), convert_t_rational_0_by_1_to_t_uint160(expr_2750))
                    /// @src 23:6532:6596  "uint160(address(self)) & ALL_HOOK_MASK > 0 || fee.isDynamicFee()"
                    let expr_2755 := expr_2751
                    if iszero(expr_2755) {
                        /// @src 23:6578:6581  "fee"
                        let _814 := var_fee_2670
                        let expr_2752 := _814
                        /// @src 23:6578:6594  "fee.isDynamicFee"
                        let expr_2753_self := expr_2752
                        /// @src 23:6578:6596  "fee.isDynamicFee()"
                        let expr_2754 := fun_isDynamicFee_3575(expr_2753_self)
                        /// @src 23:6532:6596  "uint160(address(self)) & ALL_HOOK_MASK > 0 || fee.isDynamicFee()"
                        expr_2755 := expr_2754
                    }
                    /// @src 23:6531:6597  "(uint160(address(self)) & ALL_HOOK_MASK > 0 || fee.isDynamicFee())"
                    let expr_2756 := expr_2755
                    /// @src 23:6455:6597  "address(self) == address(0)..."
                    expr_2757 := expr_2756
                }
                default {
                    /// @src 23:6498:6501  "fee"
                    let _815 := var_fee_2670
                    let expr_2737 := _815
                    /// @src 23:6498:6514  "fee.isDynamicFee"
                    let expr_2738_self := expr_2737
                    /// @src 23:6498:6516  "fee.isDynamicFee()"
                    let expr_2739 := fun_isDynamicFee_3575(expr_2738_self)
                    /// @src 23:6497:6516  "!fee.isDynamicFee()"
                    let expr_2740 := cleanup_t_bool(iszero(expr_2739))
                    /// @src 23:6455:6597  "address(self) == address(0)..."
                    expr_2757 := expr_2740
                }
                /// @src 23:6448:6597  "return address(self) == address(0)..."
                var__2673 := expr_2757
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2284
            /// @src 19:1009:1266  "function revertWith(bytes4 selector, address addr) internal pure {..."
            function fun_revertWith_2284(var_selector_2277, var_addr_2279) {

                /// @src 19:1084:1260  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, var_selector_2277)
                    mstore(0x04, and(var_addr_2279, 0xffffffffffffffffffffffffffffffffffffffff))
                    revert(0, 0x24)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_0_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_0_by_1(value)))
            }

            /// @ast-id 3630
            /// @src 24:2333:2553  "function getInitialLPFee(uint24 self) internal pure returns (uint24) {..."
            function fun_getInitialLPFee_3630(var_self_3611) -> var__3614 {
                /// @src 24:2394:2400  "uint24"
                let zero_t_uint24_816 := zero_value_for_split_t_uint24()
                var__3614 := zero_t_uint24_816

                /// @src 24:2471:2475  "self"
                let _817 := var_self_3611
                let expr_3616 := _817
                /// @src 24:2471:2488  "self.isDynamicFee"
                let expr_3617_self := expr_3616
                /// @src 24:2471:2490  "self.isDynamicFee()"
                let expr_3618 := fun_isDynamicFee_3575(expr_3617_self)
                /// @src 24:2467:2500  "if (self.isDynamicFee()) return 0"
                if expr_3618 {
                    /// @src 24:2499:2500  "0"
                    let expr_3619 := 0x00
                    /// @src 24:2492:2500  "return 0"
                    var__3614 := convert_t_rational_0_by_1_to_t_uint24(expr_3619)
                    leave
                    /// @src 24:2467:2500  "if (self.isDynamicFee()) return 0"
                }
                /// @src 24:2510:2514  "self"
                let _818 := var_self_3611
                let expr_3622 := _818
                /// @src 24:2510:2523  "self.validate"
                let expr_3624_self := expr_3622
                fun_validate_3608(expr_3624_self)
                /// @src 24:2542:2546  "self"
                let _819 := var_self_3611
                let expr_3627 := _819
                /// @src 24:2535:2546  "return self"
                var__3614 := expr_3627
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2875
            /// @src 23:8767:8875  "modifier noSelfCall(IHooks self) {..."
            function modifier_noSelfCall_2888(var_self_2879_address, var_key_2882_mpos, var_sqrtPriceX96_2884) {

                /// @src 23:9069:9073  "self"
                let _820_address := var_self_2879_address
                let expr_2887_address := _820_address
                let _821_address := expr_2887_address
                let var_self_2862_address := _821_address

                /// @src 23:8814:8824  "msg.sender"
                let expr_2865 := caller()
                /// @src 23:8836:8840  "self"
                let _822_address := var_self_2862_address
                let expr_2868_address := _822_address
                /// @src 23:8828:8841  "address(self)"
                let expr_2869 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2868_address)
                /// @src 23:8814:8841  "msg.sender != address(self)"
                let expr_2870 := iszero(eq(cleanup_t_address(expr_2865), cleanup_t_address(expr_2869)))
                /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                if expr_2870 {
                    /// @src 23:8857:8858  "_"
                    fun_beforeInitialize_2912_inner(var_self_2879_address, var_key_2882_mpos, var_sqrtPriceX96_2884)
                    /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_8192_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_8192_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_8192_by_1(value)))
            }

            /// @src 23:1346:1404  "uint160 internal constant BEFORE_INITIALIZE_FLAG = 1 << 13"
            function constant_BEFORE_INITIALIZE_FLAG_2421() -> ret {
                /// @src 23:1397:1404  "1 << 13"
                let expr_2420 := 0x2000
                let _824 := convert_t_rational_8192_by_1_to_t_uint160(expr_2420)

                ret := _824
            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160__fromStack(headStart , value0, value1, value2) -> tail {
                tail := add(headStart, 224)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_uint160_to_t_uint160_fromStack(value2,  add(headStart, 192))

            }

            /// @src 23:8968:9251  "function beforeInitialize(IHooks self, PoolKey memory key, uint160 sqrtPriceX96) internal noSelfCall(self) {..."
            function fun_beforeInitialize_2912_inner(var_self_2879_address, var_key_2882_mpos, var_sqrtPriceX96_2884) {

                /// @src 23:9089:9093  "self"
                let _823_address := var_self_2879_address
                let expr_2890_address := _823_address
                /// @src 23:9089:9107  "self.hasPermission"
                let expr_2891_self_address := expr_2890_address
                /// @src 23:9108:9130  "BEFORE_INITIALIZE_FLAG"
                let expr_2892 := constant_BEFORE_INITIALIZE_FLAG_2421()
                /// @src 23:9089:9131  "self.hasPermission(BEFORE_INITIALIZE_FLAG)"
                let expr_2893 := fun_hasPermission_3529(expr_2891_self_address, expr_2892)
                /// @src 23:9085:9245  "if (self.hasPermission(BEFORE_INITIALIZE_FLAG)) {..."
                if expr_2893 {
                    /// @src 23:9147:9151  "self"
                    let _825_address := var_self_2879_address
                    let expr_2894_address := _825_address
                    /// @src 23:9147:9160  "self.callHook"
                    let expr_2896_self_address := expr_2894_address
                    /// @src 23:9202:9212  "msg.sender"
                    let expr_2902 := caller()
                    /// @src 23:9201:9232  "(msg.sender, key, sqrtPriceX96)"
                    let expr_2905_component_1 := expr_2902
                    /// @src 23:9214:9217  "key"
                    let _826_mpos := var_key_2882_mpos
                    let expr_2903_mpos := _826_mpos
                    /// @src 23:9201:9232  "(msg.sender, key, sqrtPriceX96)"
                    let expr_2905_component_2_mpos := expr_2903_mpos
                    /// @src 23:9219:9231  "sqrtPriceX96"
                    let _827 := var_sqrtPriceX96_2884
                    let expr_2904 := _827
                    /// @src 23:9201:9232  "(msg.sender, key, sqrtPriceX96)"
                    let expr_2905_component_3 := expr_2904
                    /// @src 23:9161:9233  "abi.encodeCall(IHooks.beforeInitialize, (msg.sender, key, sqrtPriceX96))"

                    let expr_2906_mpos := allocate_unbounded()
                    let _828 := add(expr_2906_mpos, 0x20)

                    mstore(_828, 0xdc98354e00000000000000000000000000000000000000000000000000000000)
                    _828 := add(_828, 4)

                    let _829 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160__fromStack(_828, expr_2902, expr_2903_mpos, expr_2904)
                    mstore(expr_2906_mpos, sub(_829, add(expr_2906_mpos, 0x20)))
                    finalize_allocation(expr_2906_mpos, sub(_829, expr_2906_mpos))
                    /// @src 23:9147:9234  "self.callHook(abi.encodeCall(IHooks.beforeInitialize, (msg.sender, key, sqrtPriceX96)))"
                    let expr_2907_mpos := fun_callHook_2816(expr_2896_self_address, expr_2906_mpos)
                    /// @src 23:9085:9245  "if (self.hasPermission(BEFORE_INITIALIZE_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2912
            /// @src 23:8968:9251  "function beforeInitialize(IHooks self, PoolKey memory key, uint160 sqrtPriceX96) internal noSelfCall(self) {..."
            function fun_beforeInitialize_2912(var_self_2879_address, var_key_2882_mpos, var_sqrtPriceX96_2884) {

                modifier_noSelfCall_2888(var_self_2879_address, var_key_2882_mpos, var_sqrtPriceX96_2884)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_0_by_1_to_t_bytes32(value) -> converted {
                converted := cleanup_t_bytes32(shift_left_0(cleanup_t_rational_0_by_1(value)))
            }

            /// @ast-id 3973
            /// @src 29:4549:4983  "function initialize(State storage self, uint160 sqrtPriceX96, uint24 lpFee) internal returns (int24 tick) {..."
            function fun_initialize_3973(var_self_3921_slot, var_sqrtPriceX96_3923, var_lpFee_3925) -> var_tick_3928 {
                /// @src 29:4643:4653  "int24 tick"
                let zero_t_int24_830 := zero_value_for_split_t_int24()
                var_tick_3928 := zero_t_int24_830

                /// @src 29:4669:4673  "self"
                let _831_slot := var_self_3921_slot
                let expr_3930_slot := _831_slot
                /// @src 29:4669:4679  "self.slot0"
                let _832 := add(expr_3930_slot, 0)
                let _833 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_832)
                let expr_3931 := _833
                /// @src 29:4669:4692  "self.slot0.sqrtPriceX96"
                let expr_3932_self := expr_3931
                /// @src 29:4669:4694  "self.slot0.sqrtPriceX96()"
                let expr_3933 := fun_sqrtPriceX96_8662(expr_3932_self)
                /// @src 29:4698:4699  "0"
                let expr_3934 := 0x00
                /// @src 29:4669:4699  "self.slot0.sqrtPriceX96() != 0"
                let expr_3935 := iszero(eq(cleanup_t_uint160(expr_3933), convert_t_rational_0_by_1_to_t_uint160(expr_3934)))
                /// @src 29:4665:4745  "if (self.slot0.sqrtPriceX96() != 0) PoolAlreadyInitialized.selector.revertWith()"
                if expr_3935 {
                    /// @src 29:4701:4732  "PoolAlreadyInitialized.selector"
                    let expr_3939 := 0x7983c05100000000000000000000000000000000000000000000000000000000
                    /// @src 29:4701:4743  "PoolAlreadyInitialized.selector.revertWith"
                    let expr_3940_self := expr_3939
                    fun_revertWith_2274(expr_3940_self)
                    /// @src 29:4665:4745  "if (self.slot0.sqrtPriceX96() != 0) PoolAlreadyInitialized.selector.revertWith()"
                }
                /// @src 29:4763:4771  "TickMath"
                let expr_3945_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 29:4791:4803  "sqrtPriceX96"
                let _834 := var_sqrtPriceX96_3923
                let expr_3947 := _834
                /// @src 29:4763:4804  "TickMath.getTickAtSqrtPrice(sqrtPriceX96)"
                let expr_3948 := fun_getTickAtSqrtPrice_6304(expr_3947)
                /// @src 29:4756:4804  "tick = TickMath.getTickAtSqrtPrice(sqrtPriceX96)"
                var_tick_3928 := expr_3948
                let expr_3949 := expr_3948
                /// @src 29:4913:4914  "0"
                let expr_3958 := 0x00
                /// @src 29:4905:4915  "bytes32(0)"
                let expr_3959 := convert_t_rational_0_by_1_to_t_bytes32(expr_3958)
                /// @src 29:4894:4916  "Slot0.wrap(bytes32(0))"
                let expr_3960 := convert_t_bytes32_to_t_bytes32(expr_3959)
                /// @src 29:4894:4932  "Slot0.wrap(bytes32(0)).setSqrtPriceX96"
                let expr_3961_self := expr_3960
                /// @src 29:4933:4945  "sqrtPriceX96"
                let _835 := var_sqrtPriceX96_3923
                let expr_3962 := _835
                /// @src 29:4894:4946  "Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96)"
                let expr_3963 := fun_setSqrtPriceX96_8705(expr_3961_self, expr_3962)
                /// @src 29:4894:4954  "Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96).setTick"
                let expr_3964_self := expr_3963
                /// @src 29:4955:4959  "tick"
                let _836 := var_tick_3928
                let expr_3965 := _836
                /// @src 29:4894:4960  "Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96).setTick(tick)"
                let expr_3966 := fun_setTick_8718(expr_3964_self, expr_3965)
                /// @src 29:4894:4969  "Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96).setTick(tick).setLpFee"
                let expr_3967_self := expr_3966
                /// @src 29:4970:4975  "lpFee"
                let _837 := var_lpFee_3925
                let expr_3968 := _837
                /// @src 29:4894:4976  "Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96).setTick(tick).setLpFee(lpFee)"
                let expr_3969 := fun_setLpFee_8744(expr_3967_self, expr_3968)
                /// @src 29:4881:4885  "self"
                let _838_slot := var_self_3921_slot
                let expr_3951_slot := _838_slot
                /// @src 29:4881:4891  "self.slot0"
                let _839 := add(expr_3951_slot, 0)
                /// @src 29:4881:4976  "self.slot0 = Slot0.wrap(bytes32(0)).setSqrtPriceX96(sqrtPriceX96).setTick(tick).setLpFee(lpFee)"
                update_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632_to_t_userDefinedValueType$_Slot0_$8632(_839, expr_3969)
                let expr_3970 := expr_3969

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2875
            /// @src 23:8767:8875  "modifier noSelfCall(IHooks self) {..."
            function modifier_noSelfCall_2927(var_self_2916_address, var_key_2919_mpos, var_sqrtPriceX96_2921, var_tick_2923) {

                /// @src 23:9471:9475  "self"
                let _840_address := var_self_2916_address
                let expr_2926_address := _840_address
                let _841_address := expr_2926_address
                let var_self_2862_address := _841_address

                /// @src 23:8814:8824  "msg.sender"
                let expr_2865 := caller()
                /// @src 23:8836:8840  "self"
                let _842_address := var_self_2862_address
                let expr_2868_address := _842_address
                /// @src 23:8828:8841  "address(self)"
                let expr_2869 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2868_address)
                /// @src 23:8814:8841  "msg.sender != address(self)"
                let expr_2870 := iszero(eq(cleanup_t_address(expr_2865), cleanup_t_address(expr_2869)))
                /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                if expr_2870 {
                    /// @src 23:8857:8858  "_"
                    fun_afterInitialize_2952_inner(var_self_2916_address, var_key_2919_mpos, var_sqrtPriceX96_2921, var_tick_2923)
                    /// @src 23:8810:8869  "if (msg.sender != address(self)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_4096_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_4096_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_4096_by_1(value)))
            }

            /// @src 23:1410:1467  "uint160 internal constant AFTER_INITIALIZE_FLAG = 1 << 12"
            function constant_AFTER_INITIALIZE_FLAG_2426() -> ret {
                /// @src 23:1460:1467  "1 << 12"
                let expr_2425 := 0x1000
                let _844 := convert_t_rational_4096_by_1_to_t_uint160(expr_2425)

                ret := _844
            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160_t_int24__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160_t_int24__fromStack(headStart , value0, value1, value2, value3) -> tail {
                tail := add(headStart, 256)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_uint160_to_t_uint160_fromStack(value2,  add(headStart, 192))

                abi_encode_t_int24_to_t_int24_fromStack(value3,  add(headStart, 224))

            }

            /// @src 23:9343:9661  "function afterInitialize(IHooks self, PoolKey memory key, uint160 sqrtPriceX96, int24 tick)..."
            function fun_afterInitialize_2952_inner(var_self_2916_address, var_key_2919_mpos, var_sqrtPriceX96_2921, var_tick_2923) {

                /// @src 23:9495:9499  "self"
                let _843_address := var_self_2916_address
                let expr_2929_address := _843_address
                /// @src 23:9495:9513  "self.hasPermission"
                let expr_2930_self_address := expr_2929_address
                /// @src 23:9514:9535  "AFTER_INITIALIZE_FLAG"
                let expr_2931 := constant_AFTER_INITIALIZE_FLAG_2426()
                /// @src 23:9495:9536  "self.hasPermission(AFTER_INITIALIZE_FLAG)"
                let expr_2932 := fun_hasPermission_3529(expr_2930_self_address, expr_2931)
                /// @src 23:9491:9655  "if (self.hasPermission(AFTER_INITIALIZE_FLAG)) {..."
                if expr_2932 {
                    /// @src 23:9552:9556  "self"
                    let _845_address := var_self_2916_address
                    let expr_2933_address := _845_address
                    /// @src 23:9552:9565  "self.callHook"
                    let expr_2935_self_address := expr_2933_address
                    /// @src 23:9606:9616  "msg.sender"
                    let expr_2941 := caller()
                    /// @src 23:9605:9642  "(msg.sender, key, sqrtPriceX96, tick)"
                    let expr_2945_component_1 := expr_2941
                    /// @src 23:9618:9621  "key"
                    let _846_mpos := var_key_2919_mpos
                    let expr_2942_mpos := _846_mpos
                    /// @src 23:9605:9642  "(msg.sender, key, sqrtPriceX96, tick)"
                    let expr_2945_component_2_mpos := expr_2942_mpos
                    /// @src 23:9623:9635  "sqrtPriceX96"
                    let _847 := var_sqrtPriceX96_2921
                    let expr_2943 := _847
                    /// @src 23:9605:9642  "(msg.sender, key, sqrtPriceX96, tick)"
                    let expr_2945_component_3 := expr_2943
                    /// @src 23:9637:9641  "tick"
                    let _848 := var_tick_2923
                    let expr_2944 := _848
                    /// @src 23:9605:9642  "(msg.sender, key, sqrtPriceX96, tick)"
                    let expr_2945_component_4 := expr_2944
                    /// @src 23:9566:9643  "abi.encodeCall(IHooks.afterInitialize, (msg.sender, key, sqrtPriceX96, tick))"

                    let expr_2946_mpos := allocate_unbounded()
                    let _849 := add(expr_2946_mpos, 0x20)

                    mstore(_849, 0x6fe7e6eb00000000000000000000000000000000000000000000000000000000)
                    _849 := add(_849, 4)

                    let _850 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160_t_int24__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_uint160_t_int24__fromStack(_849, expr_2941, expr_2942_mpos, expr_2943, expr_2944)
                    mstore(expr_2946_mpos, sub(_850, add(expr_2946_mpos, 0x20)))
                    finalize_allocation(expr_2946_mpos, sub(_850, expr_2946_mpos))
                    /// @src 23:9552:9644  "self.callHook(abi.encodeCall(IHooks.afterInitialize, (msg.sender, key, sqrtPriceX96, tick)))"
                    let expr_2947_mpos := fun_callHook_2816(expr_2935_self_address, expr_2946_mpos)
                    /// @src 23:9491:9655  "if (self.hasPermission(AFTER_INITIALIZE_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2952
            /// @src 23:9343:9661  "function afterInitialize(IHooks self, PoolKey memory key, uint160 sqrtPriceX96, int24 tick)..."
            function fun_afterInitialize_2952(var_self_2916_address, var_key_2919_mpos, var_sqrtPriceX96_2921, var_tick_2923) {

                modifier_noSelfCall_2927(var_self_2916_address, var_key_2919_mpos, var_sqrtPriceX96_2921, var_tick_2923)
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7442
            /// @src 31:887:1346  "function isValidProtocolFee(uint24 self) internal pure returns (bool valid) {..."
            function fun_isValidProtocolFee_7442(var_self_7435) -> var_valid_7438 {
                /// @src 31:951:961  "bool valid"
                let zero_t_bool_851 := zero_value_for_split_t_bool()
                var_valid_7438 := zero_t_bool_851

                /// @src 31:1088:1340  "assembly (\"memory-safe\") {..."
                {
                    let usr$isZeroForOneFeeOk := lt(and(var_self_7435, 0xfff), 1001)
                    let usr$isOneForZeroFeeOk := lt(and(var_self_7435, 0xfff000), 4100096)
                    var_valid_7438 := and(usr$isZeroForOneFeeOk, usr$isOneForZeroFeeOk)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2304
            /// @src 19:1672:1931  "function revertWith(bytes4 selector, uint160 value) internal pure {..."
            function fun_revertWith_2304(var_selector_2297, var_value_2299) {

                /// @src 19:1748:1925  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, var_selector_2297)
                    mstore(0x04, and(var_value_2299, 0xffffffffffffffffffffffffffffffffffffffff))
                    revert(0, 0x24)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3997
            /// @src 29:4989:5167  "function setProtocolFee(State storage self, uint24 protocolFee) internal {..."
            function fun_setProtocolFee_3997(var_self_3976_slot, var_protocolFee_3978) {

                /// @src 29:5072:5076  "self"
                let _852_slot := var_self_3976_slot
                let expr_3981_slot := _852_slot
                /// @src 29:5072:5097  "self.checkPoolInitialized"
                let expr_3983_self_slot := expr_3981_slot
                fun_checkPoolInitialized_5344(expr_3983_self_slot)
                /// @src 29:5122:5126  "self"
                let _853_slot := var_self_3976_slot
                let expr_3989_slot := _853_slot
                /// @src 29:5122:5132  "self.slot0"
                let _854 := add(expr_3989_slot, 0)
                let _855 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_854)
                let expr_3990 := _855
                /// @src 29:5122:5147  "self.slot0.setProtocolFee"
                let expr_3991_self := expr_3990
                /// @src 29:5148:5159  "protocolFee"
                let _856 := var_protocolFee_3978
                let expr_3992 := _856
                /// @src 29:5122:5160  "self.slot0.setProtocolFee(protocolFee)"
                let expr_3993 := fun_setProtocolFee_8731(expr_3991_self, expr_3992)
                /// @src 29:5109:5113  "self"
                let _857_slot := var_self_3976_slot
                let expr_3986_slot := _857_slot
                /// @src 29:5109:5119  "self.slot0"
                let _858 := add(expr_3986_slot, 0)
                /// @src 29:5109:5160  "self.slot0 = self.slot0.setProtocolFee(protocolFee)"
                update_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632_to_t_userDefinedValueType$_Slot0_$8632(_858, expr_3993)
                let expr_3994 := expr_3993

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2172
            /// @src 17:797:1035  "function getDelta(Currency currency, address target) internal view returns (int256 delta) {..."
            function fun_getDelta_2172(var_currency_2156, var_target_2158) -> var_delta_2161 {
                /// @src 17:873:885  "int256 delta"
                let zero_t_int256_859 := zero_value_for_split_t_int256()
                var_delta_2161 := zero_t_int256_859

                /// @src 17:929:935  "target"
                let _860 := var_target_2158
                let expr_2166 := _860
                /// @src 17:937:945  "currency"
                let _861 := var_currency_2156
                let expr_2167 := _861
                /// @src 17:916:946  "_computeSlot(target, currency)"
                let expr_2168 := fun__computeSlot_2153(expr_2166, expr_2167)
                /// @src 17:897:946  "bytes32 hashSlot = _computeSlot(target, currency)"
                let var_hashSlot_2164 := expr_2168
                /// @src 17:956:1029  "assembly (\"memory-safe\") {..."
                {
                    var_delta_2161 := tload(var_hashSlot_2164)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 40:1400:1465  "Currency public constant ADDRESS_ZERO = Currency.wrap(address(0))"
            function constant_ADDRESS_ZERO_6642() -> ret {
                /// @src 40:1462:1463  "0"
                let expr_6639 := 0x00
                /// @src 40:1454:1464  "address(0)"
                let expr_6640 := convert_t_rational_0_by_1_to_t_address(expr_6639)
                /// @src 40:1440:1465  "Currency.wrap(address(0))"
                let expr_6641 := convert_t_address_to_t_address(expr_6640)
                let _864 := expr_6641

                ret := _864
            }

            /// @ast-id 6781
            /// @src 40:4910:5063  "function isAddressZero(Currency currency) internal pure returns (bool) {..."
            function fun_isAddressZero_6781(var_currency_6765) -> var__6768 {
                /// @src 40:4975:4979  "bool"
                let zero_t_bool_862 := zero_value_for_split_t_bool()
                var__6768 := zero_t_bool_862

                /// @src 40:5014:5022  "currency"
                let _863 := var_currency_6765
                let expr_6772 := _863
                /// @src 40:4998:5023  "Currency.unwrap(currency)"
                let expr_6773 := convert_t_address_to_t_address(expr_6772)
                /// @src 40:5043:5055  "ADDRESS_ZERO"
                let expr_6776 := constant_ADDRESS_ZERO_6642()
                /// @src 40:5027:5056  "Currency.unwrap(ADDRESS_ZERO)"
                let expr_6777 := convert_t_address_to_t_address(expr_6776)
                /// @src 40:4998:5056  "Currency.unwrap(currency) == Currency.unwrap(ADDRESS_ZERO)"
                let expr_6778 := eq(cleanup_t_address(expr_6773), cleanup_t_address(expr_6777))
                /// @src 40:4991:5056  "return Currency.unwrap(currency) == Currency.unwrap(ADDRESS_ZERO)"
                var__6768 := expr_6778
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2229
            /// @src 18:548:716  "function getSyncedCurrency() internal view returns (Currency currency) {..."
            function fun_getSyncedCurrency_2229() -> var_currency_2225 {
                /// @src 18:600:617  "Currency currency"
                let zero_t_userDefinedValueType$_Currency_$6525_865 := zero_value_for_split_t_userDefinedValueType$_Currency_$6525()
                var_currency_2225 := zero_t_userDefinedValueType$_Currency_$6525_865

                /// @src 18:629:710  "assembly (\"memory-safe\") {..."
                {
                    var_currency_2225 := tload(18037029214425852597980496522548842536420057720408124260691716999909707453369)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6558
            /// @src 40:364:502  "function equals(Currency currency, Currency other) pure returns (bool) {..."
            function fun_equals_6558(var_currency_6539, var_other_6542) -> var__6545 {
                /// @src 40:429:433  "bool"
                let zero_t_bool_866 := zero_value_for_split_t_bool()
                var__6545 := zero_t_bool_866

                /// @src 40:464:472  "currency"
                let _867 := var_currency_6539
                let expr_6549 := _867
                /// @src 40:448:473  "Currency.unwrap(currency)"
                let expr_6550 := convert_t_address_to_t_address(expr_6549)
                /// @src 40:493:498  "other"
                let _868 := var_other_6542
                let expr_6553 := _868
                /// @src 40:477:499  "Currency.unwrap(other)"
                let expr_6554 := convert_t_address_to_t_address(expr_6553)
                /// @src 40:448:499  "Currency.unwrap(currency) == Currency.unwrap(other)"
                let expr_6555 := eq(cleanup_t_address(expr_6550), cleanup_t_address(expr_6554))
                /// @src 40:441:499  "return Currency.unwrap(currency) == Currency.unwrap(other)"
                var__6545 := expr_6555
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_uint160_to_t_contract$_IERC20Minimal_$9021(value) -> converted {
                converted := convert_t_uint160_to_t_uint160(value)
            }

            function convert_t_address_to_t_contract$_IERC20Minimal_$9021(value) -> converted {
                converted := convert_t_uint160_to_t_contract$_IERC20Minimal_$9021(value)
            }

            function convert_t_contract$_IERC20Minimal_$9021_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            function convert_t_contract$_CurrencyLibrary_$6819_to_t_address(value) -> converted {
                converted := convert_t_uint160_to_t_address(value)
            }

            function abi_decode_t_uint256_fromMemory(offset, end) -> value {
                value := mload(offset)
                validator_revert_t_uint256(value)
            }

            function abi_decode_tuple_t_uint256_fromMemory(headStart, dataEnd) -> value0 {
                if slt(sub(dataEnd, headStart), 32) { revert_error_dbdddcbe895c83990c08b3492a0e83918d802a52331272ac6fdb6a7c4aea3b1b() }

                {

                    let offset := 0

                    value0 := abi_decode_t_uint256_fromMemory(add(headStart, offset), dataEnd)
                }

            }

            /// @ast-id 6732
            /// @src 40:4351:4627  "function balanceOfSelf(Currency currency) internal view returns (uint256) {..."
            function fun_balanceOfSelf_6732(var_currency_6701) -> var__6704 {
                /// @src 40:4416:4423  "uint256"
                let zero_t_uint256_869 := zero_value_for_split_t_uint256()
                var__6704 := zero_t_uint256_869

                /// @src 40:4439:4447  "currency"
                let _870 := var_currency_6701
                let expr_6706 := _870
                /// @src 40:4439:4461  "currency.isAddressZero"
                let expr_6707_self := expr_6706
                /// @src 40:4439:4463  "currency.isAddressZero()"
                let expr_6708 := fun_isAddressZero_6781(expr_6707_self)
                /// @src 40:4435:4621  "if (currency.isAddressZero()) {..."
                switch expr_6708
                case 0 {
                    /// @src 40:4575:4583  "currency"
                    let _871 := var_currency_6701
                    let expr_6719 := _871
                    /// @src 40:4559:4584  "Currency.unwrap(currency)"
                    let expr_6720 := convert_t_address_to_t_address(expr_6719)
                    /// @src 40:4545:4585  "IERC20Minimal(Currency.unwrap(currency))"
                    let expr_6721_address := convert_t_address_to_t_contract$_IERC20Minimal_$9021(expr_6720)
                    /// @src 40:4545:4595  "IERC20Minimal(Currency.unwrap(currency)).balanceOf"
                    let expr_6722_address := convert_t_contract$_IERC20Minimal_$9021_to_t_address(expr_6721_address)
                    let expr_6722_functionSelector := 0x70a08231
                    /// @src 40:4604:4608  "this"
                    let expr_6725_address := address()
                    /// @src 40:4596:4609  "address(this)"
                    let expr_6726 := convert_t_contract$_CurrencyLibrary_$6819_to_t_address(expr_6725_address)
                    /// @src 40:4545:4610  "IERC20Minimal(Currency.unwrap(currency)).balanceOf(address(this))"

                    // storage for arguments and returned data
                    let _872 := allocate_unbounded()
                    mstore(_872, shift_left_224(expr_6722_functionSelector))
                    let _873 := abi_encode_tuple_t_address__to_t_address__fromStack(add(_872, 4) , expr_6726)

                    let _874 := staticcall(gas(), expr_6722_address,  _872, sub(_873, _872), _872, 32)

                    if iszero(_874) { revert_forward_1() }

                    let expr_6727
                    if _874 {

                        let _875 := 32

                        if gt(_875, returndatasize()) {
                            _875 := returndatasize()
                        }

                        // update freeMemoryPointer according to dynamic return size
                        finalize_allocation(_872, _875)

                        // decode return parameters from external try-call into retVars
                        expr_6727 :=  abi_decode_tuple_t_uint256_fromMemory(_872, add(_872, _875))
                    }
                    /// @src 40:4538:4610  "return IERC20Minimal(Currency.unwrap(currency)).balanceOf(address(this))"
                    var__6704 := expr_6727
                    leave
                    /// @src 40:4435:4621  "if (currency.isAddressZero()) {..."
                }
                default {
                    /// @src 40:4494:4498  "this"
                    let expr_6711_address := address()
                    /// @src 40:4486:4499  "address(this)"
                    let expr_6712 := convert_t_contract$_CurrencyLibrary_$6819_to_t_address(expr_6711_address)
                    /// @src 40:4486:4507  "address(this).balance"
                    let expr_6713 := balance(expr_6712)
                    /// @src 40:4479:4507  "return address(this).balance"
                    var__6704 := expr_6713
                    leave
                    /// @src 40:4435:4621  "if (currency.isAddressZero()) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2244
            /// @src 18:851:1116  "function syncCurrencyAndReserves(Currency currency, uint256 value) internal {..."
            function fun_syncCurrencyAndReserves_2244(var_currency_2237, var_value_2239) {

                /// @src 18:937:1110  "assembly (\"memory-safe\") {..."
                {
                    tstore(18037029214425852597980496522548842536420057720408124260691716999909707453369, and(var_currency_2237, 0xffffffffffffffffffffffffffffffffffffffff))
                    tstore(13582234132832961652756477188584847927179359657859594952372729441197434191253, var_value_2239)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2234
            /// @src 18:722:845  "function resetCurrency() internal {..."
            function fun_resetCurrency_2234() {

                /// @src 18:766:839  "assembly (\"memory-safe\") {..."
                {
                    tstore(18037029214425852597980496522548842536420057720408124260691716999909707453369, 0)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @src 39:764:832  "BeforeSwapDelta public constant ZERO_DELTA = BeforeSwapDelta.wrap(0)"
            function constant_ZERO_DELTA_6494() -> ret {
                /// @src 39:830:831  "0"
                let expr_6492 := 0x00
                /// @src 39:809:832  "BeforeSwapDelta.wrap(0)"
                let expr_6493 := convert_t_rational_0_by_1_to_t_int256(expr_6492)
                let _884 := expr_6493

                ret := _884
            }

            function abi_encode_t_bool_to_t_bool(value, pos) {
                mstore(pos, cleanup_t_bool(value))
            }

            function abi_encode_t_uint160_to_t_uint160(value, pos) {
                mstore(pos, cleanup_t_uint160(value))
            }

            // struct SwapParams -> struct SwapParams
            function abi_encode_t_struct$_SwapParams_$6898_memory_ptr_to_t_struct$_SwapParams_$6898_memory_ptr_fromStack(value, pos)  {
                let tail := add(pos, 0x60)

                {
                    // zeroForOne

                    let memberValue0 := mload(add(value, 0x00))
                    abi_encode_t_bool_to_t_bool(memberValue0, add(pos, 0x00))
                }

                {
                    // amountSpecified

                    let memberValue0 := mload(add(value, 0x20))
                    abi_encode_t_int256_to_t_int256(memberValue0, add(pos, 0x20))
                }

                {
                    // sqrtPriceLimitX96

                    let memberValue0 := mload(add(value, 0x40))
                    abi_encode_t_uint160_to_t_uint160(memberValue0, add(pos, 0x40))
                }

            }

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_bytes_memory_ptr__fromStack(headStart , value0, value1, value2, value3, value4) -> tail {
                tail := add(headStart, 320)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_struct$_SwapParams_$6898_memory_ptr_to_t_struct$_SwapParams_$6898_memory_ptr_fromStack(value2,  add(headStart, 192))

                mstore(add(headStart, 288), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value3, value4,  tail)

            }

            function cleanup_t_rational_96_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_96_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_96_by_1(value)))
            }

            function checked_add_t_int256(x, y) -> sum {
                x := cleanup_t_int256(x)
                y := cleanup_t_int256(y)
                sum := add(x, y)

                // overflow, if x >= 0 and sum < y
                // underflow, if x < 0 and sum >= y
                if or(
                    and(iszero(slt(x, 0)), slt(sum, y)),
                    and(slt(x, 0), iszero(slt(sum, y)))
                ) { panic_error_0x11() }

            }

            /// @ast-id 3294
            /// @src 23:12116:14083  "function beforeSwap(IHooks self, PoolKey memory key, SwapParams memory params, bytes calldata hookData)..."
            function fun_beforeSwap_3294(var_self_3157_address, var_key_3160_mpos, var_params_3163_mpos, var_hookData_3165_offset, var_hookData_3165_length) -> var_amountToSwap_3168, var_hookReturn_3171, var_lpFeeOverride_3173 {
                /// @src 23:12254:12273  "int256 amountToSwap"
                let zero_t_int256_876 := zero_value_for_split_t_int256()
                var_amountToSwap_3168 := zero_t_int256_876
                /// @src 23:12275:12301  "BeforeSwapDelta hookReturn"
                let zero_t_userDefinedValueType$_BeforeSwapDelta_$6473_877 := zero_value_for_split_t_userDefinedValueType$_BeforeSwapDelta_$6473()
                var_hookReturn_3171 := zero_t_userDefinedValueType$_BeforeSwapDelta_$6473_877
                /// @src 23:12303:12323  "uint24 lpFeeOverride"
                let zero_t_uint24_878 := zero_value_for_split_t_uint24()
                var_lpFeeOverride_3173 := zero_t_uint24_878

                /// @src 23:12354:12360  "params"
                let _879_mpos := var_params_3163_mpos
                let expr_3176_mpos := _879_mpos
                /// @src 23:12354:12376  "params.amountSpecified"
                let _880 := add(expr_3176_mpos, 32)
                let _881 := read_from_memoryt_int256(_880)
                let expr_3177 := _881
                /// @src 23:12339:12376  "amountToSwap = params.amountSpecified"
                var_amountToSwap_3168 := expr_3177
                let expr_3178 := expr_3177
                /// @src 23:12390:12400  "msg.sender"
                let expr_3181 := caller()
                /// @src 23:12412:12416  "self"
                let _882_address := var_self_3157_address
                let expr_3184_address := _882_address
                /// @src 23:12404:12417  "address(self)"
                let expr_3185 := convert_t_contract$_IHooks_$1840_to_t_address(expr_3184_address)
                /// @src 23:12390:12417  "msg.sender == address(self)"
                let expr_3186 := eq(cleanup_t_address(expr_3181), cleanup_t_address(expr_3185))
                /// @src 23:12386:12490  "if (msg.sender == address(self)) return (amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                if expr_3186 {
                    /// @src 23:12427:12439  "amountToSwap"
                    let _883 := var_amountToSwap_3168
                    let expr_3187 := _883
                    /// @src 23:12426:12490  "(amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                    let expr_3191_component_1 := expr_3187
                    /// @src 23:12441:12463  "BeforeSwapDeltaLibrary"
                    let expr_3188_address := linkersymbol("src/types/BeforeSwapDelta.sol:BeforeSwapDeltaLibrary")
                    /// @src 23:12441:12474  "BeforeSwapDeltaLibrary.ZERO_DELTA"
                    let expr_3189 := constant_ZERO_DELTA_6494()
                    /// @src 23:12426:12490  "(amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                    let expr_3191_component_2 := expr_3189
                    /// @src 23:12476:12489  "lpFeeOverride"
                    let _885 := var_lpFeeOverride_3173
                    let expr_3190 := _885
                    /// @src 23:12426:12490  "(amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                    let expr_3191_component_3 := expr_3190
                    /// @src 23:12419:12490  "return (amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                    var_amountToSwap_3168 := expr_3191_component_1
                    var_hookReturn_3171 := expr_3191_component_2
                    var_lpFeeOverride_3173 := expr_3191_component_3
                    leave
                    /// @src 23:12386:12490  "if (msg.sender == address(self)) return (amountToSwap, BeforeSwapDeltaLibrary.ZERO_DELTA, lpFeeOverride)"
                }
                /// @src 23:12505:12509  "self"
                let _886_address := var_self_3157_address
                let expr_3194_address := _886_address
                /// @src 23:12505:12523  "self.hasPermission"
                let expr_3195_self_address := expr_3194_address
                /// @src 23:12524:12540  "BEFORE_SWAP_FLAG"
                let expr_3196 := constant_BEFORE_SWAP_FLAG_2451()
                /// @src 23:12505:12541  "self.hasPermission(BEFORE_SWAP_FLAG)"
                let expr_3197 := fun_hasPermission_3529(expr_3195_self_address, expr_3196)
                /// @src 23:12501:14077  "if (self.hasPermission(BEFORE_SWAP_FLAG)) {..."
                if expr_3197 {
                    /// @src 23:12588:12592  "self"
                    let _887_address := var_self_3157_address
                    let expr_3201_address := _887_address
                    /// @src 23:12629:12639  "msg.sender"
                    let expr_3207 := caller()
                    /// @src 23:12628:12663  "(msg.sender, key, params, hookData)"
                    let expr_3211_component_1 := expr_3207
                    /// @src 23:12641:12644  "key"
                    let _888_mpos := var_key_3160_mpos
                    let expr_3208_mpos := _888_mpos
                    /// @src 23:12628:12663  "(msg.sender, key, params, hookData)"
                    let expr_3211_component_2_mpos := expr_3208_mpos
                    /// @src 23:12646:12652  "params"
                    let _889_mpos := var_params_3163_mpos
                    let expr_3209_mpos := _889_mpos
                    /// @src 23:12628:12663  "(msg.sender, key, params, hookData)"
                    let expr_3211_component_3_mpos := expr_3209_mpos
                    /// @src 23:12654:12662  "hookData"
                    let _890_offset := var_hookData_3165_offset
                    let _890_length := var_hookData_3165_length
                    let expr_3210_offset := _890_offset
                    let expr_3210_length := _890_length
                    /// @src 23:12628:12663  "(msg.sender, key, params, hookData)"
                    let expr_3211_component_4_offset := expr_3210_offset
                    let expr_3211_component_4_length := expr_3210_length
                    /// @src 23:12594:12664  "abi.encodeCall(IHooks.beforeSwap, (msg.sender, key, params, hookData))"

                    let expr_3212_mpos := allocate_unbounded()
                    let _891 := add(expr_3212_mpos, 0x20)

                    mstore(_891, 0x575e24b400000000000000000000000000000000000000000000000000000000)
                    _891 := add(_891, 4)

                    let _892 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_bytes_memory_ptr__fromStack(_891, expr_3207, expr_3208_mpos, expr_3209_mpos, expr_3210_offset, expr_3210_length)
                    mstore(expr_3212_mpos, sub(_892, add(expr_3212_mpos, 0x20)))
                    finalize_allocation(expr_3212_mpos, sub(_892, expr_3212_mpos))
                    /// @src 23:12579:12665  "callHook(self, abi.encodeCall(IHooks.beforeSwap, (msg.sender, key, params, hookData)))"
                    let expr_3213_mpos := fun_callHook_2816(expr_3201_address, expr_3212_mpos)
                    /// @src 23:12557:12665  "bytes memory result = callHook(self, abi.encodeCall(IHooks.beforeSwap, (msg.sender, key, params, hookData)))"
                    let var_result_3199_mpos := expr_3213_mpos
                    /// @src 23:12783:12789  "result"
                    let _893_mpos := var_result_3199_mpos
                    let expr_3215_mpos := _893_mpos
                    /// @src 23:12783:12796  "result.length"
                    let expr_3216 := array_length_t_bytes_memory_ptr(expr_3215_mpos)
                    /// @src 23:12800:12802  "96"
                    let expr_3217 := 0x60
                    /// @src 23:12783:12802  "result.length != 96"
                    let expr_3218 := iszero(eq(cleanup_t_uint256(expr_3216), convert_t_rational_96_by_1_to_t_uint256(expr_3217)))
                    /// @src 23:12779:12845  "if (result.length != 96) InvalidHookResponse.selector.revertWith()"
                    if expr_3218 {
                        /// @src 23:12804:12832  "InvalidHookResponse.selector"
                        let expr_3222 := 0x1e048e1d00000000000000000000000000000000000000000000000000000000
                        /// @src 23:12804:12843  "InvalidHookResponse.selector.revertWith"
                        let expr_3223_self := expr_3222
                        fun_revertWith_2274(expr_3223_self)
                        /// @src 23:12779:12845  "if (result.length != 96) InvalidHookResponse.selector.revertWith()"
                    }
                    /// @src 23:13119:13122  "key"
                    let _894_mpos := var_key_3160_mpos
                    let expr_3227_mpos := _894_mpos
                    /// @src 23:13119:13126  "key.fee"
                    let _895 := add(expr_3227_mpos, 64)
                    let _896 := read_from_memoryt_uint24(_895)
                    let expr_3228 := _896
                    /// @src 23:13119:13139  "key.fee.isDynamicFee"
                    let expr_3229_self := expr_3228
                    /// @src 23:13119:13141  "key.fee.isDynamicFee()"
                    let expr_3230 := fun_isDynamicFee_3575(expr_3229_self)
                    /// @src 23:13115:13176  "if (key.fee.isDynamicFee()) lpFeeOverride = result.parseFee()"
                    if expr_3230 {
                        /// @src 23:13159:13165  "result"
                        let _897_mpos := var_result_3199_mpos
                        let expr_3232_mpos := _897_mpos
                        /// @src 23:13159:13174  "result.parseFee"
                        let expr_3233_self_mpos := expr_3232_mpos
                        /// @src 23:13159:13176  "result.parseFee()"
                        let expr_3234 := fun_parseFee_7590(expr_3233_self_mpos)
                        /// @src 23:13143:13176  "lpFeeOverride = result.parseFee()"
                        var_lpFeeOverride_3173 := expr_3234
                        let expr_3235 := expr_3234
                        /// @src 23:13115:13176  "if (key.fee.isDynamicFee()) lpFeeOverride = result.parseFee()"
                    }
                    /// @src 23:13266:13270  "self"
                    let _898_address := var_self_3157_address
                    let expr_3238_address := _898_address
                    /// @src 23:13266:13284  "self.hasPermission"
                    let expr_3239_self_address := expr_3238_address
                    /// @src 23:13285:13315  "BEFORE_SWAP_RETURNS_DELTA_FLAG"
                    let expr_3240 := constant_BEFORE_SWAP_RETURNS_DELTA_FLAG_2471()
                    /// @src 23:13266:13316  "self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)"
                    let expr_3241 := fun_hasPermission_3529(expr_3239_self_address, expr_3240)
                    /// @src 23:13262:14067  "if (self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)) {..."
                    if expr_3241 {
                        /// @src 23:13370:13376  "result"
                        let _899_mpos := var_result_3199_mpos
                        let expr_3245_mpos := _899_mpos
                        /// @src 23:13370:13393  "result.parseReturnDelta"
                        let expr_3246_self_mpos := expr_3245_mpos
                        /// @src 23:13370:13395  "result.parseReturnDelta()"
                        let expr_3247 := fun_parseReturnDelta_7599(expr_3246_self_mpos)
                        /// @src 23:13349:13396  "BeforeSwapDelta.wrap(result.parseReturnDelta())"
                        let expr_3248 := convert_t_int256_to_t_int256(expr_3247)
                        /// @src 23:13336:13396  "hookReturn = BeforeSwapDelta.wrap(result.parseReturnDelta())"
                        var_hookReturn_3171 := expr_3248
                        let expr_3249 := expr_3248
                        /// @src 23:13533:13543  "hookReturn"
                        let _900 := var_hookReturn_3171
                        let expr_3253 := _900
                        /// @src 23:13533:13561  "hookReturn.getSpecifiedDelta"
                        let expr_3254_self := expr_3253
                        /// @src 23:13533:13563  "hookReturn.getSpecifiedDelta()"
                        let expr_3255 := fun_getSpecifiedDelta_6505(expr_3254_self)
                        /// @src 23:13505:13563  "int128 hookDeltaSpecified = hookReturn.getSpecifiedDelta()"
                        let var_hookDeltaSpecified_3252 := expr_3255
                        /// @src 23:13725:13743  "hookDeltaSpecified"
                        let _901 := var_hookDeltaSpecified_3252
                        let expr_3257 := _901
                        /// @src 23:13747:13748  "0"
                        let expr_3258 := 0x00
                        /// @src 23:13725:13748  "hookDeltaSpecified != 0"
                        let expr_3259 := iszero(eq(cleanup_t_int128(expr_3257), convert_t_rational_0_by_1_to_t_int128(expr_3258)))
                        /// @src 23:13721:14053  "if (hookDeltaSpecified != 0) {..."
                        if expr_3259 {
                            /// @src 23:13790:13802  "amountToSwap"
                            let _902 := var_amountToSwap_3168
                            let expr_3262 := _902
                            /// @src 23:13805:13806  "0"
                            let expr_3263 := 0x00
                            /// @src 23:13790:13806  "amountToSwap < 0"
                            let expr_3264 := slt(cleanup_t_int256(expr_3262), convert_t_rational_0_by_1_to_t_int256(expr_3263))
                            /// @src 23:13772:13806  "bool exactInput = amountToSwap < 0"
                            let var_exactInput_3261 := expr_3264
                            /// @src 23:13844:13862  "hookDeltaSpecified"
                            let _903 := var_hookDeltaSpecified_3252
                            let expr_3267 := _903
                            /// @src 23:13828:13862  "amountToSwap += hookDeltaSpecified"
                            let _904 := convert_t_int128_to_t_int256(expr_3267)
                            let _905 := var_amountToSwap_3168
                            let expr_3268 := checked_add_t_int256(_905, _904)

                            var_amountToSwap_3168 := expr_3268
                            /// @src 23:13888:13898  "exactInput"
                            let _906 := var_exactInput_3261
                            let expr_3270 := _906
                            /// @src 23:13888:13936  "exactInput ? amountToSwap > 0 : amountToSwap < 0"
                            let expr_3277
                            switch expr_3270
                            case 0 {
                                /// @src 23:13920:13932  "amountToSwap"
                                let _907 := var_amountToSwap_3168
                                let expr_3274 := _907
                                /// @src 23:13935:13936  "0"
                                let expr_3275 := 0x00
                                /// @src 23:13920:13936  "amountToSwap < 0"
                                let expr_3276 := slt(cleanup_t_int256(expr_3274), convert_t_rational_0_by_1_to_t_int256(expr_3275))
                                /// @src 23:13888:13936  "exactInput ? amountToSwap > 0 : amountToSwap < 0"
                                expr_3277 := expr_3276
                            }
                            default {
                                /// @src 23:13901:13913  "amountToSwap"
                                let _908 := var_amountToSwap_3168
                                let expr_3271 := _908
                                /// @src 23:13916:13917  "0"
                                let expr_3272 := 0x00
                                /// @src 23:13901:13917  "amountToSwap > 0"
                                let expr_3273 := sgt(cleanup_t_int256(expr_3271), convert_t_rational_0_by_1_to_t_int256(expr_3272))
                                /// @src 23:13888:13936  "exactInput ? amountToSwap > 0 : amountToSwap < 0"
                                expr_3277 := expr_3273
                            }
                            /// @src 23:13884:14035  "if (exactInput ? amountToSwap > 0 : amountToSwap < 0) {..."
                            if expr_3277 {
                                /// @src 23:13964:13999  "HookDeltaExceedsSwapAmount.selector"
                                let expr_3281 := 0xfa0b71d600000000000000000000000000000000000000000000000000000000
                                /// @src 23:13964:14010  "HookDeltaExceedsSwapAmount.selector.revertWith"
                                let expr_3282_self := expr_3281
                                fun_revertWith_2274(expr_3282_self)
                                /// @src 23:13884:14035  "if (exactInput ? amountToSwap > 0 : amountToSwap < 0) {..."
                            }
                            /// @src 23:13721:14053  "if (hookDeltaSpecified != 0) {..."
                        }
                        /// @src 23:13262:14067  "if (self.hasPermission(BEFORE_SWAP_RETURNS_DELTA_FLAG)) {..."
                    }
                    /// @src 23:12501:14077  "if (self.hasPermission(BEFORE_SWAP_FLAG)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function abi_encode_t_int128_to_t_int128_fromStack(value, pos) {
                mstore(pos, cleanup_t_int128(value))
            }

            function abi_encode_t_uint128_to_t_uint128_fromStack(value, pos) {
                mstore(pos, cleanup_t_uint128(value))
            }

            function abi_encode_tuple_t_int128_t_int128_t_uint160_t_uint128_t_int24_t_uint24__to_t_int128_t_int128_t_uint160_t_uint128_t_int24_t_uint24__fromStack(headStart , value0, value1, value2, value3, value4, value5) -> tail {
                tail := add(headStart, 192)

                abi_encode_t_int128_to_t_int128_fromStack(value0,  add(headStart, 0))

                abi_encode_t_int128_to_t_int128_fromStack(value1,  add(headStart, 32))

                abi_encode_t_uint160_to_t_uint160_fromStack(value2,  add(headStart, 64))

                abi_encode_t_uint128_to_t_uint128_fromStack(value3,  add(headStart, 96))

                abi_encode_t_int24_to_t_int24_fromStack(value4,  add(headStart, 128))

                abi_encode_t_uint24_to_t_uint24_fromStack(value5,  add(headStart, 160))

            }

            /// @ast-id 681
            /// @src 6:11194:11986  "function _swap(Pool.State storage pool, PoolId id, Pool.SwapParams memory params, Currency inputCurrency)..."
            function fun__swap_681(var_pool_620_slot, var_id_623, var_params_626_mpos, var_inputCurrency_629) -> var__633 {
                /// @src 6:11334:11346  "BalanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_909 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var__633 := zero_t_userDefinedValueType$_BalanceDelta_$6311_909

                /// @src 6:11470:11474  "pool"
                let _910_slot := var_pool_620_slot
                let expr_645_slot := _910_slot
                /// @src 6:11470:11479  "pool.swap"
                let expr_646_self_slot := expr_645_slot
                /// @src 6:11480:11486  "params"
                let _911_mpos := var_params_626_mpos
                let expr_647_mpos := _911_mpos
                /// @src 6:11470:11487  "pool.swap(params)"
                let expr_648_component_1, expr_648_component_2, expr_648_component_3, expr_648_component_4_mpos := fun_swap_5021(expr_646_self_slot, expr_647_mpos)
                /// @src 6:11362:11487  "(BalanceDelta delta, uint256 amountToProtocol, uint24 swapFee, Pool.SwapResult memory result) =..."
                let var_delta_637 := expr_648_component_1
                let var_amountToProtocol_639 := expr_648_component_2
                let var_swapFee_641 := expr_648_component_3
                let var_result_644_mpos := expr_648_component_4_mpos
                /// @src 6:11546:11562  "amountToProtocol"
                let _912 := var_amountToProtocol_639
                let expr_650 := _912
                /// @src 6:11565:11566  "0"
                let expr_651 := 0x00
                /// @src 6:11546:11566  "amountToProtocol > 0"
                let expr_652 := gt(cleanup_t_uint256(expr_650), convert_t_rational_0_by_1_to_t_uint256(expr_651))
                /// @src 6:11542:11620  "if (amountToProtocol > 0) _updateProtocolFees(inputCurrency, amountToProtocol)"
                if expr_652 {
                    /// @src 6:11588:11601  "inputCurrency"
                    let _913 := var_inputCurrency_629
                    let expr_654 := _913
                    /// @src 6:11603:11619  "amountToProtocol"
                    let _914 := var_amountToProtocol_639
                    let expr_655 := _914
                    fun__updateProtocolFees_1640(expr_654, expr_655)
                    /// @src 6:11542:11620  "if (amountToProtocol > 0) _updateProtocolFees(inputCurrency, amountToProtocol)"
                }
                /// @src 6:11753:11755  "id"
                let _915 := var_id_623
                let expr_660 := _915
                /// @src 6:11769:11779  "msg.sender"
                let expr_662 := caller()
                /// @src 6:11793:11798  "delta"
                let _916 := var_delta_637
                let expr_663 := _916
                /// @src 6:11793:11806  "delta.amount0"
                let expr_664_self := expr_663
                /// @src 6:11793:11808  "delta.amount0()"
                let expr_665 := fun_amount0_6458(expr_664_self)
                /// @src 6:11822:11827  "delta"
                let _917 := var_delta_637
                let expr_666 := _917
                /// @src 6:11822:11835  "delta.amount1"
                let expr_667_self := expr_666
                /// @src 6:11822:11837  "delta.amount1()"
                let expr_668 := fun_amount1_6468(expr_667_self)
                /// @src 6:11851:11857  "result"
                let _918_mpos := var_result_644_mpos
                let expr_669_mpos := _918_mpos
                /// @src 6:11851:11870  "result.sqrtPriceX96"
                let _919 := add(expr_669_mpos, 0)
                let _920 := read_from_memoryt_uint160(_919)
                let expr_670 := _920
                /// @src 6:11884:11890  "result"
                let _921_mpos := var_result_644_mpos
                let expr_671_mpos := _921_mpos
                /// @src 6:11884:11900  "result.liquidity"
                let _922 := add(expr_671_mpos, 64)
                let _923 := read_from_memoryt_uint128(_922)
                let expr_672 := _923
                /// @src 6:11914:11920  "result"
                let _924_mpos := var_result_644_mpos
                let expr_673_mpos := _924_mpos
                /// @src 6:11914:11925  "result.tick"
                let _925 := add(expr_673_mpos, 32)
                let _926 := read_from_memoryt_int24(_925)
                let expr_674 := _926
                /// @src 6:11939:11946  "swapFee"
                let _927 := var_swapFee_641
                let expr_675 := _927
                /// @src 6:11735:11956  "Swap(..."
                let _928 := 0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f
                let _929 := convert_t_bytes32_to_t_bytes32(expr_660)
                let _930 := convert_t_address_to_t_address(expr_662)
                {
                    let _931 := allocate_unbounded()
                    let _932 := abi_encode_tuple_t_int128_t_int128_t_uint160_t_uint128_t_int24_t_uint24__to_t_int128_t_int128_t_uint160_t_uint128_t_int24_t_uint24__fromStack(_931 , expr_665, expr_668, expr_670, expr_672, expr_674, expr_675)
                    log3(_931, sub(_932, _931) , _928, _929, _930)
                }/// @src 6:11974:11979  "delta"
                let _933 := var_delta_637
                let expr_678 := _933
                /// @src 6:11967:11979  "return delta"
                var__633 := expr_678
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_userDefinedValueType$_BalanceDelta_$6311_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_int256_t_bytes_memory_ptr__fromStack(headStart , value0, value1, value2, value3, value4, value5) -> tail {
                tail := add(headStart, 352)

                abi_encode_t_address_to_t_address_fromStack(value0,  add(headStart, 0))

                abi_encode_t_struct$_PoolKey_$6871_memory_ptr_to_t_struct$_PoolKey_$6871_memory_ptr_fromStack(value1,  add(headStart, 32))

                abi_encode_t_struct$_SwapParams_$6898_memory_ptr_to_t_struct$_SwapParams_$6898_memory_ptr_fromStack(value2,  add(headStart, 192))

                abi_encode_t_userDefinedValueType$_BalanceDelta_$6311_to_t_int256_fromStack(value3,  add(headStart, 288))

                mstore(add(headStart, 320), sub(tail, headStart))
                tail := abi_encode_t_bytes_calldata_ptr_to_t_bytes_memory_ptr_fromStack(value4, value5,  tail)

            }

            function checked_add_t_int128(x, y) -> sum {
                x := cleanup_t_int128(x)
                y := cleanup_t_int128(y)
                sum := add(x, y)

                if or(
                    sgt(sum, 0x7fffffffffffffffffffffffffffffff),
                    slt(sum, 0xffffffffffffffffffffffffffffffff80000000000000000000000000000000)
                ) { panic_error_0x11() }

            }

            /// @ast-id 3420
            /// @src 23:14169:15507  "function afterSwap(..."
            function fun_afterSwap_3420(var_self_3298_address, var_key_3301_mpos, var_params_3304_mpos, var_swapDelta_3307, var_hookData_3309_offset, var_hookData_3309_length, var_beforeSwapHookReturn_3312) -> var__3316, var__3319 {
                /// @src 23:14406:14418  "BalanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_934 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var__3316 := zero_t_userDefinedValueType$_BalanceDelta_$6311_934
                /// @src 23:14420:14432  "BalanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_935 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var__3319 := zero_t_userDefinedValueType$_BalanceDelta_$6311_935

                /// @src 23:14448:14458  "msg.sender"
                let expr_3322 := caller()
                /// @src 23:14470:14474  "self"
                let _936_address := var_self_3298_address
                let expr_3325_address := _936_address
                /// @src 23:14462:14475  "address(self)"
                let expr_3326 := convert_t_contract$_IHooks_$1840_to_t_address(expr_3325_address)
                /// @src 23:14448:14475  "msg.sender == address(self)"
                let expr_3327 := eq(cleanup_t_address(expr_3322), cleanup_t_address(expr_3326))
                /// @src 23:14444:14527  "if (msg.sender == address(self)) return (swapDelta, BalanceDeltaLibrary.ZERO_DELTA)"
                if expr_3327 {
                    /// @src 23:14485:14494  "swapDelta"
                    let _937 := var_swapDelta_3307
                    let expr_3328 := _937
                    /// @src 23:14484:14527  "(swapDelta, BalanceDeltaLibrary.ZERO_DELTA)"
                    let expr_3331_component_1 := expr_3328
                    /// @src 23:14496:14515  "BalanceDeltaLibrary"
                    let expr_3329_address := linkersymbol("src/types/BalanceDelta.sol:BalanceDeltaLibrary")
                    /// @src 23:14496:14526  "BalanceDeltaLibrary.ZERO_DELTA"
                    let expr_3330 := constant_ZERO_DELTA_6448()
                    /// @src 23:14484:14527  "(swapDelta, BalanceDeltaLibrary.ZERO_DELTA)"
                    let expr_3331_component_2 := expr_3330
                    /// @src 23:14477:14527  "return (swapDelta, BalanceDeltaLibrary.ZERO_DELTA)"
                    var__3316 := expr_3331_component_1
                    var__3319 := expr_3331_component_2
                    leave
                    /// @src 23:14444:14527  "if (msg.sender == address(self)) return (swapDelta, BalanceDeltaLibrary.ZERO_DELTA)"
                }
                /// @src 23:14566:14586  "beforeSwapHookReturn"
                let _938 := var_beforeSwapHookReturn_3312
                let expr_3336 := _938
                /// @src 23:14566:14604  "beforeSwapHookReturn.getSpecifiedDelta"
                let expr_3337_self := expr_3336
                /// @src 23:14566:14606  "beforeSwapHookReturn.getSpecifiedDelta()"
                let expr_3338 := fun_getSpecifiedDelta_6505(expr_3337_self)
                /// @src 23:14538:14606  "int128 hookDeltaSpecified = beforeSwapHookReturn.getSpecifiedDelta()"
                let var_hookDeltaSpecified_3335 := expr_3338
                /// @src 23:14646:14666  "beforeSwapHookReturn"
                let _939 := var_beforeSwapHookReturn_3312
                let expr_3342 := _939
                /// @src 23:14646:14686  "beforeSwapHookReturn.getUnspecifiedDelta"
                let expr_3343_self := expr_3342
                /// @src 23:14646:14688  "beforeSwapHookReturn.getUnspecifiedDelta()"
                let expr_3344 := fun_getUnspecifiedDelta_6516(expr_3343_self)
                /// @src 23:14616:14688  "int128 hookDeltaUnspecified = beforeSwapHookReturn.getUnspecifiedDelta()"
                let var_hookDeltaUnspecified_3341 := expr_3344
                /// @src 23:14703:14707  "self"
                let _940_address := var_self_3298_address
                let expr_3346_address := _940_address
                /// @src 23:14703:14721  "self.hasPermission"
                let expr_3347_self_address := expr_3346_address
                /// @src 23:14722:14737  "AFTER_SWAP_FLAG"
                let expr_3348 := constant_AFTER_SWAP_FLAG_2456()
                /// @src 23:14703:14738  "self.hasPermission(AFTER_SWAP_FLAG)"
                let expr_3349 := fun_hasPermission_3529(expr_3347_self_address, expr_3348)
                /// @src 23:14699:15007  "if (self.hasPermission(AFTER_SWAP_FLAG)) {..."
                if expr_3349 {
                    /// @src 23:14778:14782  "self"
                    let _941_address := var_self_3298_address
                    let expr_3351_address := _941_address
                    /// @src 23:14778:14806  "self.callHookWithReturnDelta"
                    let expr_3352_self_address := expr_3351_address
                    /// @src 23:14858:14868  "msg.sender"
                    let expr_3358 := caller()
                    /// @src 23:14857:14903  "(msg.sender, key, params, swapDelta, hookData)"
                    let expr_3363_component_1 := expr_3358
                    /// @src 23:14870:14873  "key"
                    let _942_mpos := var_key_3301_mpos
                    let expr_3359_mpos := _942_mpos
                    /// @src 23:14857:14903  "(msg.sender, key, params, swapDelta, hookData)"
                    let expr_3363_component_2_mpos := expr_3359_mpos
                    /// @src 23:14875:14881  "params"
                    let _943_mpos := var_params_3304_mpos
                    let expr_3360_mpos := _943_mpos
                    /// @src 23:14857:14903  "(msg.sender, key, params, swapDelta, hookData)"
                    let expr_3363_component_3_mpos := expr_3360_mpos
                    /// @src 23:14883:14892  "swapDelta"
                    let _944 := var_swapDelta_3307
                    let expr_3361 := _944
                    /// @src 23:14857:14903  "(msg.sender, key, params, swapDelta, hookData)"
                    let expr_3363_component_4 := expr_3361
                    /// @src 23:14894:14902  "hookData"
                    let _945_offset := var_hookData_3309_offset
                    let _945_length := var_hookData_3309_length
                    let expr_3362_offset := _945_offset
                    let expr_3362_length := _945_length
                    /// @src 23:14857:14903  "(msg.sender, key, params, swapDelta, hookData)"
                    let expr_3363_component_5_offset := expr_3362_offset
                    let expr_3363_component_5_length := expr_3362_length
                    /// @src 23:14824:14904  "abi.encodeCall(IHooks.afterSwap, (msg.sender, key, params, swapDelta, hookData))"

                    let expr_3364_mpos := allocate_unbounded()
                    let _946 := add(expr_3364_mpos, 0x20)

                    mstore(_946, 0xb47b2fb100000000000000000000000000000000000000000000000000000000)
                    _946 := add(_946, 4)

                    let _947 := abi_encode_tuple_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_userDefinedValueType$_BalanceDelta_$6311_t_bytes_calldata_ptr__to_t_address_t_struct$_PoolKey_$6871_memory_ptr_t_struct$_SwapParams_$6898_memory_ptr_t_int256_t_bytes_memory_ptr__fromStack(_946, expr_3358, expr_3359_mpos, expr_3360_mpos, expr_3361, expr_3362_offset, expr_3362_length)
                    mstore(expr_3364_mpos, sub(_947, add(expr_3364_mpos, 0x20)))
                    finalize_allocation(expr_3364_mpos, sub(_947, expr_3364_mpos))
                    /// @src 23:14922:14926  "self"
                    let _948_address := var_self_3298_address
                    let expr_3365_address := _948_address
                    /// @src 23:14922:14940  "self.hasPermission"
                    let expr_3366_self_address := expr_3365_address
                    /// @src 23:14941:14970  "AFTER_SWAP_RETURNS_DELTA_FLAG"
                    let expr_3367 := constant_AFTER_SWAP_RETURNS_DELTA_FLAG_2476()
                    /// @src 23:14922:14971  "self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)"
                    let expr_3368 := fun_hasPermission_3529(expr_3366_self_address, expr_3367)
                    /// @src 23:14778:14985  "self.callHookWithReturnDelta(..."
                    let expr_3369 := fun_callHookWithReturnDelta_2858(expr_3352_self_address, expr_3364_mpos, expr_3368)
                    /// @src 23:14778:14994  "self.callHookWithReturnDelta(..."
                    let expr_3370_self := expr_3369
                    /// @src 23:14778:14996  "self.callHookWithReturnDelta(..."
                    let expr_3371 := fun_toInt128_5693(expr_3370_self)
                    /// @src 23:14754:14996  "hookDeltaUnspecified += self.callHookWithReturnDelta(..."
                    let _949 := var_hookDeltaUnspecified_3341
                    let expr_3372 := checked_add_t_int128(_949, expr_3371)

                    var_hookDeltaUnspecified_3341 := expr_3372
                    /// @src 23:14699:15007  "if (self.hasPermission(AFTER_SWAP_FLAG)) {..."
                }
                /// @src 23:15017:15039  "BalanceDelta hookDelta"
                let var_hookDelta_3378
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_950 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_hookDelta_3378 := zero_t_userDefinedValueType$_BalanceDelta_$6311_950
                /// @src 23:15053:15073  "hookDeltaUnspecified"
                let _951 := var_hookDeltaUnspecified_3341
                let expr_3380 := _951
                /// @src 23:15077:15078  "0"
                let expr_3381 := 0x00
                /// @src 23:15053:15078  "hookDeltaUnspecified != 0"
                let expr_3382 := iszero(eq(cleanup_t_int128(expr_3380), convert_t_rational_0_by_1_to_t_int128(expr_3381)))
                /// @src 23:15053:15105  "hookDeltaUnspecified != 0 || hookDeltaSpecified != 0"
                let expr_3386 := expr_3382
                if iszero(expr_3386) {
                    /// @src 23:15082:15100  "hookDeltaSpecified"
                    let _952 := var_hookDeltaSpecified_3335
                    let expr_3383 := _952
                    /// @src 23:15104:15105  "0"
                    let expr_3384 := 0x00
                    /// @src 23:15082:15105  "hookDeltaSpecified != 0"
                    let expr_3385 := iszero(eq(cleanup_t_int128(expr_3383), convert_t_rational_0_by_1_to_t_int128(expr_3384)))
                    /// @src 23:15053:15105  "hookDeltaUnspecified != 0 || hookDeltaSpecified != 0"
                    expr_3386 := expr_3385
                }
                /// @src 23:15049:15462  "if (hookDeltaUnspecified != 0 || hookDeltaSpecified != 0) {..."
                if expr_3386 {
                    /// @src 23:15134:15140  "params"
                    let _953_mpos := var_params_3304_mpos
                    let expr_3388_mpos := _953_mpos
                    /// @src 23:15134:15156  "params.amountSpecified"
                    let _954 := add(expr_3388_mpos, 32)
                    let _955 := read_from_memoryt_int256(_954)
                    let expr_3389 := _955
                    /// @src 23:15159:15160  "0"
                    let expr_3390 := 0x00
                    /// @src 23:15134:15160  "params.amountSpecified < 0"
                    let expr_3391 := slt(cleanup_t_int256(expr_3389), convert_t_rational_0_by_1_to_t_int256(expr_3390))
                    /// @src 23:15164:15170  "params"
                    let _956_mpos := var_params_3304_mpos
                    let expr_3392_mpos := _956_mpos
                    /// @src 23:15164:15181  "params.zeroForOne"
                    let _957 := add(expr_3392_mpos, 0)
                    let _958 := read_from_memoryt_bool(_957)
                    let expr_3393 := _958
                    /// @src 23:15134:15181  "params.amountSpecified < 0 == params.zeroForOne"
                    let expr_3394 := eq(cleanup_t_bool(expr_3391), cleanup_t_bool(expr_3393))
                    /// @src 23:15133:15182  "(params.amountSpecified < 0 == params.zeroForOne)"
                    let expr_3395 := expr_3394
                    /// @src 23:15133:15332  "(params.amountSpecified < 0 == params.zeroForOne)..."
                    let expr_3404
                    switch expr_3395
                    case 0 {
                        /// @src 23:15291:15311  "hookDeltaUnspecified"
                        let _959 := var_hookDeltaUnspecified_3341
                        let expr_3401 := _959
                        /// @src 23:15313:15331  "hookDeltaSpecified"
                        let _960 := var_hookDeltaSpecified_3335
                        let expr_3402 := _960
                        /// @src 23:15276:15332  "toBalanceDelta(hookDeltaUnspecified, hookDeltaSpecified)"
                        let expr_3403 := fun_toBalanceDelta_6337(expr_3401, expr_3402)
                        /// @src 23:15133:15332  "(params.amountSpecified < 0 == params.zeroForOne)..."
                        expr_3404 := expr_3403
                    }
                    default {
                        /// @src 23:15216:15234  "hookDeltaSpecified"
                        let _961 := var_hookDeltaSpecified_3335
                        let expr_3397 := _961
                        /// @src 23:15236:15256  "hookDeltaUnspecified"
                        let _962 := var_hookDeltaUnspecified_3341
                        let expr_3398 := _962
                        /// @src 23:15201:15257  "toBalanceDelta(hookDeltaSpecified, hookDeltaUnspecified)"
                        let expr_3399 := fun_toBalanceDelta_6337(expr_3397, expr_3398)
                        /// @src 23:15133:15332  "(params.amountSpecified < 0 == params.zeroForOne)..."
                        expr_3404 := expr_3399
                    }
                    /// @src 23:15121:15332  "hookDelta = (params.amountSpecified < 0 == params.zeroForOne)..."
                    var_hookDelta_3378 := expr_3404
                    let expr_3405 := expr_3404
                    /// @src 23:15430:15439  "swapDelta"
                    let _963 := var_swapDelta_3307
                    let expr_3408 := _963
                    /// @src 23:15442:15451  "hookDelta"
                    let _964 := var_hookDelta_3378
                    let expr_3409 := _964
                    /// @src 23:15430:15451  "swapDelta - hookDelta"
                    let expr_3410 := fun_sub_6395(expr_3408, expr_3409)
                    /// @src 23:15418:15451  "swapDelta = swapDelta - hookDelta"
                    var_swapDelta_3307 := expr_3410
                    let expr_3411 := expr_3410
                    /// @src 23:15049:15462  "if (hookDeltaUnspecified != 0 || hookDeltaSpecified != 0) {..."
                }
                /// @src 23:15479:15488  "swapDelta"
                let _965 := var_swapDelta_3307
                let expr_3415 := _965
                /// @src 23:15478:15500  "(swapDelta, hookDelta)"
                let expr_3417_component_1 := expr_3415
                /// @src 23:15490:15499  "hookDelta"
                let _966 := var_hookDelta_3378
                let expr_3416 := _966
                /// @src 23:15478:15500  "(swapDelta, hookDelta)"
                let expr_3417_component_2 := expr_3416
                /// @src 23:15471:15500  "return (swapDelta, hookDelta)"
                var__3316 := expr_3417_component_1
                var__3319 := expr_3417_component_2
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1288
            /// @src 2:530:955  "function _burnFrom(address from, uint256 id, uint256 amount) internal {..."
            function fun__burnFrom_1288(var_from_1226, var_id_1228, var_amount_1230) {

                /// @src 2:627:637  "msg.sender"
                let expr_1236 := caller()
                /// @src 2:610:637  "address sender = msg.sender"
                let var_sender_1234 := expr_1236
                /// @src 2:651:655  "from"
                let _967 := var_from_1226
                let expr_1238 := _967
                /// @src 2:659:665  "sender"
                let _968 := var_sender_1234
                let expr_1239 := _968
                /// @src 2:651:665  "from != sender"
                let expr_1240 := iszero(eq(cleanup_t_address(expr_1238), cleanup_t_address(expr_1239)))
                /// @src 2:651:694  "from != sender && !isOperator[from][sender]"
                let expr_1247 := expr_1240
                if expr_1247 {
                    /// @src 2:670:680  "isOperator"
                    let _969_slot := 0x03
                    let expr_1241_slot := _969_slot
                    /// @src 2:681:685  "from"
                    let _970 := var_from_1226
                    let expr_1242 := _970
                    /// @src 2:670:686  "isOperator[from]"
                    let _971 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_bool_$_$_of_t_address(expr_1241_slot,expr_1242)
                    let _972_slot := _971
                    let expr_1243_slot := _972_slot
                    /// @src 2:687:693  "sender"
                    let _973 := var_sender_1234
                    let expr_1244 := _973
                    /// @src 2:670:694  "isOperator[from][sender]"
                    let _974 := mapping_index_access_t_mapping$_t_address_$_t_bool_$_of_t_address(expr_1243_slot,expr_1244)
                    let _975 := read_from_storage_split_offset_0_t_bool(_974)
                    let expr_1245 := _975
                    /// @src 2:669:694  "!isOperator[from][sender]"
                    let expr_1246 := cleanup_t_bool(iszero(expr_1245))
                    /// @src 2:651:694  "from != sender && !isOperator[from][sender]"
                    expr_1247 := expr_1246
                }
                /// @src 2:647:916  "if (from != sender && !isOperator[from][sender]) {..."
                if expr_1247 {
                    /// @src 2:736:745  "allowance"
                    let _976_slot := 0x05
                    let expr_1250_slot := _976_slot
                    /// @src 2:746:750  "from"
                    let _977 := var_from_1226
                    let expr_1251 := _977
                    /// @src 2:736:751  "allowance[from]"
                    let _978 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(expr_1250_slot,expr_1251)
                    let _979_slot := _978
                    let expr_1252_slot := _979_slot
                    /// @src 2:752:758  "sender"
                    let _980 := var_sender_1234
                    let expr_1253 := _980
                    /// @src 2:736:759  "allowance[from][sender]"
                    let _981 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_1252_slot,expr_1253)
                    let _982_slot := _981
                    let expr_1254_slot := _982_slot
                    /// @src 2:760:762  "id"
                    let _983 := var_id_1228
                    let expr_1255 := _983
                    /// @src 2:736:763  "allowance[from][sender][id]"
                    let _984 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_1254_slot,expr_1255)
                    let _985 := read_from_storage_split_offset_0_t_uint256(_984)
                    let expr_1256 := _985
                    /// @src 2:710:763  "uint256 senderAllowance = allowance[from][sender][id]"
                    let var_senderAllowance_1249 := expr_1256
                    /// @src 2:781:796  "senderAllowance"
                    let _986 := var_senderAllowance_1249
                    let expr_1258 := _986
                    /// @src 2:800:817  "type(uint256).max"
                    let expr_1263 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                    /// @src 2:781:817  "senderAllowance != type(uint256).max"
                    let expr_1264 := iszero(eq(cleanup_t_uint256(expr_1258), cleanup_t_uint256(expr_1263)))
                    /// @src 2:777:906  "if (senderAllowance != type(uint256).max) {..."
                    if expr_1264 {
                        /// @src 2:867:882  "senderAllowance"
                        let _987 := var_senderAllowance_1249
                        let expr_1272 := _987
                        /// @src 2:885:891  "amount"
                        let _988 := var_amount_1230
                        let expr_1273 := _988
                        /// @src 2:867:891  "senderAllowance - amount"
                        let expr_1274 := checked_sub_t_uint256(expr_1272, expr_1273)

                        /// @src 2:837:846  "allowance"
                        let _989_slot := 0x05
                        let expr_1265_slot := _989_slot
                        /// @src 2:847:851  "from"
                        let _990 := var_from_1226
                        let expr_1266 := _990
                        /// @src 2:837:852  "allowance[from]"
                        let _991 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_$_of_t_address(expr_1265_slot,expr_1266)
                        let _992_slot := _991
                        let expr_1269_slot := _992_slot
                        /// @src 2:853:859  "sender"
                        let _993 := var_sender_1234
                        let expr_1267 := _993
                        /// @src 2:837:860  "allowance[from][sender]"
                        let _994 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_1269_slot,expr_1267)
                        let _995_slot := _994
                        let expr_1270_slot := _995_slot
                        /// @src 2:861:863  "id"
                        let _996 := var_id_1228
                        let expr_1268 := _996
                        /// @src 2:837:864  "allowance[from][sender][id]"
                        let _997 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_1270_slot,expr_1268)
                        /// @src 2:837:891  "allowance[from][sender][id] = senderAllowance - amount"
                        update_storage_value_offset_0t_uint256_to_t_uint256(_997, expr_1274)
                        let expr_1275 := expr_1274
                        /// @src 2:777:906  "if (senderAllowance != type(uint256).max) {..."
                    }
                    /// @src 2:647:916  "if (from != sender && !isOperator[from][sender]) {..."
                }
                /// @src 2:931:935  "from"
                let _998 := var_from_1226
                let expr_1282 := _998
                /// @src 2:937:939  "id"
                let _999 := var_id_1228
                let expr_1283 := _999
                /// @src 2:941:947  "amount"
                let _1000 := var_amount_1230
                let expr_1284 := _1000
                fun__burn_7190(expr_1282, expr_1283, expr_1284)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2203
            /// @src 17:1201:1603  "function applyDelta(Currency currency, address target, int128 delta)..."
            function fun_applyDelta_2203(var_currency_2176, var_target_2178, var_delta_2180) -> var_previous_2183, var_next_2185 {
                /// @src 17:1304:1319  "int256 previous"
                let zero_t_int256_1001 := zero_value_for_split_t_int256()
                var_previous_2183 := zero_t_int256_1001
                /// @src 17:1321:1332  "int256 next"
                let zero_t_int256_1002 := zero_value_for_split_t_int256()
                var_next_2185 := zero_t_int256_1002

                /// @src 17:1380:1386  "target"
                let _1003 := var_target_2178
                let expr_2190 := _1003
                /// @src 17:1388:1396  "currency"
                let _1004 := var_currency_2176
                let expr_2191 := _1004
                /// @src 17:1367:1397  "_computeSlot(target, currency)"
                let expr_2192 := fun__computeSlot_2153(expr_2190, expr_2191)
                /// @src 17:1348:1397  "bytes32 hashSlot = _computeSlot(target, currency)"
                let var_hashSlot_2188 := expr_2192
                /// @src 17:1408:1484  "assembly (\"memory-safe\") {..."
                {
                    var_previous_2183 := tload(var_hashSlot_2188)
                }
                /// @src 17:1500:1508  "previous"
                let _1005 := var_previous_2183
                let expr_2196 := _1005
                /// @src 17:1511:1516  "delta"
                let _1006 := var_delta_2180
                let expr_2197 := _1006
                /// @src 17:1500:1516  "previous + delta"
                let expr_2198 := checked_add_t_int256(expr_2196, convert_t_int128_to_t_int256(expr_2197))

                /// @src 17:1493:1516  "next = previous + delta"
                var_next_2185 := expr_2198
                let expr_2199 := expr_2198
                /// @src 17:1526:1597  "assembly (\"memory-safe\") {..."
                {
                    tstore(var_hashSlot_2188, var_next_2185)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3721
            /// @src 27:723:949  "function increment() internal {..."
            function fun_increment_3721() {

                /// @src 27:763:943  "assembly (\"memory-safe\") {..."
                {
                    let usr$count := tload(56671960505278111519104690822132496699113179860588238901689140059013086026251)
                    usr$count := add(usr$count, 1)
                    tstore(56671960505278111519104690822132496699113179860588238901689140059013086026251, usr$count)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3727
            /// @src 27:1231:1457  "function decrement() internal {..."
            function fun_decrement_3727() {

                /// @src 27:1271:1451  "assembly (\"memory-safe\") {..."
                {
                    let usr$count := tload(56671960505278111519104690822132496699113179860588238901689140059013086026251)
                    usr$count := sub(usr$count, 1)
                    tstore(56671960505278111519104690822132496699113179860588238901689140059013086026251, usr$count)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2357
            /// @src 19:3508:5171  "function bubbleUpAndRevertWith(..."
            function fun_bubbleUpAndRevertWith_2357(var_revertingContract_2343, var_revertingFunctionSelector_2345, var_additionalContext_2347) {

                /// @src 19:3710:3731  "WrappedError.selector"
                let expr_2353 := 0x90bfb86500000000000000000000000000000000000000000000000000000000
                /// @src 19:3680:3731  "bytes4 wrappedErrorSelector = WrappedError.selector"
                let var_wrappedErrorSelector_2351 := expr_2353
                /// @src 19:3741:5165  "assembly (\"memory-safe\") {..."
                {
                    let usr$encodedDataSize := mul(div(add(returndatasize(), 31), 32), 32)
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, var_wrappedErrorSelector_2351)
                    mstore(add(usr$fmp, 0x04), and(var_revertingContract_2343, 0xffffffffffffffffffffffffffffffffffffffff))
                    mstore(add(usr$fmp, 0x24), and(var_revertingFunctionSelector_2345, 0xffffffff00000000000000000000000000000000000000000000000000000000))
                    mstore(add(usr$fmp, 0x44), 0x80)
                    mstore(add(usr$fmp, 0x64), add(0xa0, usr$encodedDataSize))
                    mstore(add(usr$fmp, 0x84), returndatasize())
                    returndatacopy(add(usr$fmp, 0xa4), 0, returndatasize())
                    mstore(add(usr$fmp, add(0xa4, usr$encodedDataSize)), 0x04)
                    mstore(add(usr$fmp, add(0xc4, usr$encodedDataSize)), and(var_additionalContext_2347, 0xffffffff00000000000000000000000000000000000000000000000000000000))
                    revert(usr$fmp, add(0xe4, usr$encodedDataSize))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2251
            /// @src 18:1122:1286  "function getSyncedReserves() internal view returns (uint256 value) {..."
            function fun_getSyncedReserves_2251() -> var_value_2247 {
                /// @src 18:1174:1187  "uint256 value"
                let zero_t_uint256_1007 := zero_value_for_split_t_uint256()
                var_value_2247 := zero_t_uint256_1007

                /// @src 18:1199:1280  "assembly (\"memory-safe\") {..."
                {
                    var_value_2247 := tload(13582234132832961652756477188584847927179359657859594952372729441197434191253)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_uint160() -> ret {
                ret := 0
            }

            /// @ast-id 8662
            /// @src 44:1409:1601  "function sqrtPriceX96(Slot0 _packed) internal pure returns (uint160 _sqrtPriceX96) {..."
            function fun_sqrtPriceX96_8662(var__packed_8655) -> var__sqrtPriceX96_8658 {
                /// @src 44:1469:1490  "uint160 _sqrtPriceX96"
                let zero_t_uint160_1008 := zero_value_for_split_t_uint160()
                var__sqrtPriceX96_8658 := zero_t_uint160_1008

                /// @src 44:1502:1595  "assembly (\"memory-safe\") {..."
                {
                    var__sqrtPriceX96_8658 := and(1461501637330902918203684832716283019655932542975, var__packed_8655)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3529
            /// @src 23:16371:16508  "function hasPermission(IHooks self, uint160 flag) internal pure returns (bool) {..."
            function fun_hasPermission_3529(var_self_3509_address, var_flag_3511) -> var__3514 {
                /// @src 23:16444:16448  "bool"
                let zero_t_bool_1009 := zero_value_for_split_t_bool()
                var__3514 := zero_t_bool_1009

                /// @src 23:16483:16487  "self"
                let _1010_address := var_self_3509_address
                let expr_3520_address := _1010_address
                /// @src 23:16475:16488  "address(self)"
                let expr_3521 := convert_t_contract$_IHooks_$1840_to_t_address(expr_3520_address)
                /// @src 23:16467:16489  "uint160(address(self))"
                let expr_3522 := convert_t_address_to_t_uint160(expr_3521)
                /// @src 23:16492:16496  "flag"
                let _1011 := var_flag_3511
                let expr_3523 := _1011
                /// @src 23:16467:16496  "uint160(address(self)) & flag"
                let expr_3524 := and(expr_3522, expr_3523)

                /// @src 23:16500:16501  "0"
                let expr_3525 := 0x00
                /// @src 23:16467:16501  "uint160(address(self)) & flag != 0"
                let expr_3526 := iszero(eq(cleanup_t_uint160(expr_3524), convert_t_rational_0_by_1_to_t_uint160(expr_3525)))
                /// @src 23:16460:16501  "return uint160(address(self)) & flag != 0"
                var__3514 := expr_3526
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function array_dataslot_t_bytes_memory_ptr(ptr) -> data {
                data := ptr

                data := add(ptr, 0x20)

            }

            function read_from_memoryt_bytes4(ptr) -> returnValue {

                let value := cleanup_t_bytes4(mload(ptr))

                returnValue :=

                value

            }

            function shift_left_dynamic(bits, value) -> newValue {
                newValue :=

                shl(bits, value)

            }

            function convert_bytes_to_fixedbytes_from_t_bytes_memory_ptr_to_t_bytes4(array) -> value {

                let length := array_length_t_bytes_memory_ptr(array)
                let dataArea := array

                dataArea := array_dataslot_t_bytes_memory_ptr(array)

                value := read_from_memoryt_bytes4(dataArea)

                if lt(length, 4) {
                    value := and(
                        value,
                        shift_left_dynamic(
                            mul(8, sub(4, length)),
                            0xffffffff00000000000000000000000000000000000000000000000000000000
                        )
                    )
                }

            }

            function convert_t_rational_32_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_32_by_1(value)))
            }

            /// @ast-id 2816
            /// @src 23:6780:8056  "function callHook(IHooks self, bytes memory data) internal returns (bytes memory result) {..."
            function fun_callHook_2816(var_self_2764_address, var_data_2766_mpos) -> var_result_2769_mpos {
                /// @src 23:6848:6867  "bytes memory result"
                let zero_t_bytes_memory_ptr_1012_mpos := zero_value_for_split_t_bytes_memory_ptr()
                var_result_2769_mpos := zero_t_bytes_memory_ptr_1012_mpos

                /// @src 23:6879:6891  "bool success"
                let var_success_2772
                let zero_t_bool_1013 := zero_value_for_split_t_bool()
                var_success_2772 := zero_t_bool_1013
                /// @src 23:6901:7017  "assembly (\"memory-safe\") {..."
                {
                    var_success_2772 := call(gas(), var_self_2764_address, 0, add(var_data_2766_mpos, 0x20), mload(var_data_2766_mpos), 0, 0)
                }
                /// @src 23:7112:7119  "success"
                let _1014 := var_success_2772
                let expr_2775 := _1014
                /// @src 23:7111:7119  "!success"
                let expr_2776 := cleanup_t_bool(iszero(expr_2775))
                /// @src 23:7107:7209  "if (!success) CustomRevert.bubbleUpAndRevertWith(address(self), bytes4(data), HookCallFailed.selector)"
                if expr_2776 {
                    /// @src 23:7121:7133  "CustomRevert"
                    let expr_2777_address := linkersymbol("src/libraries/CustomRevert.sol:CustomRevert")
                    /// @src 23:7164:7168  "self"
                    let _1015_address := var_self_2764_address
                    let expr_2782_address := _1015_address
                    /// @src 23:7156:7169  "address(self)"
                    let expr_2783 := convert_t_contract$_IHooks_$1840_to_t_address(expr_2782_address)
                    /// @src 23:7178:7182  "data"
                    let _1016_mpos := var_data_2766_mpos
                    let expr_2786_mpos := _1016_mpos
                    /// @src 23:7171:7183  "bytes4(data)"
                    let expr_2787 := convert_bytes_to_fixedbytes_from_t_bytes_memory_ptr_to_t_bytes4(expr_2786_mpos)
                    /// @src 23:7185:7208  "HookCallFailed.selector"
                    let expr_2789 := 0xa9e35b2f00000000000000000000000000000000000000000000000000000000
                    fun_bubbleUpAndRevertWith_2357(expr_2783, expr_2787, expr_2789)
                    /// @src 23:7107:7209  "if (!success) CustomRevert.bubbleUpAndRevertWith(address(self), bytes4(data), HookCallFailed.selector)"
                }
                /// @src 23:7280:7784  "assembly (\"memory-safe\") {..."
                {
                    var_result_2769_mpos := mload(0x40)
                    mstore(0x40, add(var_result_2769_mpos, and(add(returndatasize(), 0x3f), not(0x1f))))
                    mstore(var_result_2769_mpos, returndatasize())
                    returndatacopy(add(var_result_2769_mpos, 0x20), 0, returndatasize())
                }
                /// @src 23:7914:7920  "result"
                let _1017_mpos := var_result_2769_mpos
                let expr_2794_mpos := _1017_mpos
                /// @src 23:7914:7927  "result.length"
                let expr_2795 := array_length_t_bytes_memory_ptr(expr_2794_mpos)
                /// @src 23:7930:7932  "32"
                let expr_2796 := 0x20
                /// @src 23:7914:7932  "result.length < 32"
                let expr_2797 := lt(cleanup_t_uint256(expr_2795), convert_t_rational_32_by_1_to_t_uint256(expr_2796))
                /// @src 23:7914:7982  "result.length < 32 || result.parseSelector() != data.parseSelector()"
                let expr_2805 := expr_2797
                if iszero(expr_2805) {
                    /// @src 23:7936:7942  "result"
                    let _1018_mpos := var_result_2769_mpos
                    let expr_2798_mpos := _1018_mpos
                    /// @src 23:7936:7956  "result.parseSelector"
                    let expr_2799_self_mpos := expr_2798_mpos
                    /// @src 23:7936:7958  "result.parseSelector()"
                    let expr_2800 := fun_parseSelector_7581(expr_2799_self_mpos)
                    /// @src 23:7962:7966  "data"
                    let _1019_mpos := var_data_2766_mpos
                    let expr_2801_mpos := _1019_mpos
                    /// @src 23:7962:7980  "data.parseSelector"
                    let expr_2802_self_mpos := expr_2801_mpos
                    /// @src 23:7962:7982  "data.parseSelector()"
                    let expr_2803 := fun_parseSelector_7581(expr_2802_self_mpos)
                    /// @src 23:7936:7982  "result.parseSelector() != data.parseSelector()"
                    let expr_2804 := iszero(eq(cleanup_t_bytes4(expr_2800), cleanup_t_bytes4(expr_2803)))
                    /// @src 23:7914:7982  "result.length < 32 || result.parseSelector() != data.parseSelector()"
                    expr_2805 := expr_2804
                }
                /// @src 23:7910:8050  "if (result.length < 32 || result.parseSelector() != data.parseSelector()) {..."
                if expr_2805 {
                    /// @src 23:7998:8026  "InvalidHookResponse.selector"
                    let expr_2809 := 0x1e048e1d00000000000000000000000000000000000000000000000000000000
                    /// @src 23:7998:8037  "InvalidHookResponse.selector.revertWith"
                    let expr_2810_self := expr_2809
                    fun_revertWith_2274(expr_2810_self)
                    /// @src 23:7910:8050  "if (result.length < 32 || result.parseSelector() != data.parseSelector()) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6337
            /// @src 38:448:670  "function toBalanceDelta(int128 _amount0, int128 _amount1) pure returns (BalanceDelta balanceDelta) {..."
            function fun_toBalanceDelta_6337(var__amount0_6327, var__amount1_6329) -> var_balanceDelta_6333 {
                /// @src 38:520:545  "BalanceDelta balanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_1020 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_balanceDelta_6333 := zero_t_userDefinedValueType$_BalanceDelta_$6311_1020

                /// @src 38:553:668  "assembly (\"memory-safe\") {..."
                {
                    var_balanceDelta_6333 := or(shl(128, var__amount0_6327), and(sub(shl(128, 1), 1), var__amount1_6329))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8627
            /// @src 37:956:1162  "function simpleMulDiv(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256 result) {..."
            function fun_simpleMulDiv_8627(var_a_8616, var_b_8618, var_denominator_8620) -> var_result_8623 {
                /// @src 37:1044:1058  "uint256 result"
                let zero_t_uint256_1021 := zero_value_for_split_t_uint256()
                var_result_8623 := zero_t_uint256_1021

                /// @src 37:1070:1156  "assembly (\"memory-safe\") {..."
                {
                    var_result_8623 := div(mul(var_a_8616, var_b_8618), var_denominator_8620)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6458
            /// @src 38:1958:2141  "function amount0(BalanceDelta balanceDelta) internal pure returns (int128 _amount0) {..."
            function fun_amount0_6458(var_balanceDelta_6451) -> var__amount0_6454 {
                /// @src 38:2025:2040  "int128 _amount0"
                let zero_t_int128_1022 := zero_value_for_split_t_int128()
                var__amount0_6454 := zero_t_int128_1022

                /// @src 38:2052:2135  "assembly (\"memory-safe\") {..."
                {
                    var__amount0_6454 := sar(128, var_balanceDelta_6451)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6468
            /// @src 38:2147:2336  "function amount1(BalanceDelta balanceDelta) internal pure returns (int128 _amount1) {..."
            function fun_amount1_6468(var_balanceDelta_6461) -> var__amount1_6464 {
                /// @src 38:2214:2229  "int128 _amount1"
                let zero_t_int128_1023 := zero_value_for_split_t_int128()
                var__amount1_6464 := zero_t_int128_1023

                /// @src 38:2241:2330  "assembly (\"memory-safe\") {..."
                {
                    var__amount1_6464 := signextend(15, var_balanceDelta_6461)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_1000000_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1000000_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_1000000_by_1(value)))
            }

            /// @src 24:1075:1118  "uint24 public constant MAX_LP_FEE = 1000000"
            function constant_MAX_LP_FEE_3562() -> ret {
                /// @src 24:1111:1118  "1000000"
                let expr_3561 := 0x0f4240
                let _1026 := convert_t_rational_1000000_by_1_to_t_uint24(expr_3561)

                ret := _1026
            }

            /// @ast-id 3588
            /// @src 24:1591:1692  "function isValid(uint24 self) internal pure returns (bool) {..."
            function fun_isValid_3588(var_self_3578) -> var__3581 {
                /// @src 24:1644:1648  "bool"
                let zero_t_bool_1024 := zero_value_for_split_t_bool()
                var__3581 := zero_t_bool_1024

                /// @src 24:1667:1671  "self"
                let _1025 := var_self_3578
                let expr_3583 := _1025
                /// @src 24:1675:1685  "MAX_LP_FEE"
                let expr_3584 := constant_MAX_LP_FEE_3562()
                /// @src 24:1667:1685  "self <= MAX_LP_FEE"
                let expr_3585 := iszero(gt(cleanup_t_uint24(expr_3583), cleanup_t_uint24(expr_3584)))
                /// @src 24:1660:1685  "return self <= MAX_LP_FEE"
                var__3581 := expr_3585
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_userDefinedValueType$_Slot0_$8632() -> ret {
                ret := 0
            }

            /// @ast-id 8744
            /// @src 44:3121:3401  "function setLpFee(Slot0 _packed, uint24 _lpFee) internal pure returns (Slot0 _result) {..."
            function fun_setLpFee_8744(var__packed_8734, var__lpFee_8736) -> var__result_8740 {
                /// @src 44:3192:3205  "Slot0 _result"
                let zero_t_userDefinedValueType$_Slot0_$8632_1027 := zero_value_for_split_t_userDefinedValueType$_Slot0_$8632()
                var__result_8740 := zero_t_userDefinedValueType$_Slot0_$8632_1027

                /// @src 44:3217:3395  "assembly (\"memory-safe\") {..."
                {
                    var__result_8740 := or(and(not(shl(208, 16777215)), var__packed_8734), shl(208, and(16777215, var__lpFee_8736)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_minus_887272_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_minus_887272_by_1_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_rational_minus_887272_by_1(value)))
            }

            /// @src 36:997:1039  "int24 internal constant MIN_TICK = -887272"
            function constant_MIN_TICK_5776() -> ret {
                /// @src 36:1032:1039  "-887272"
                let expr_5775 := 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff27618
                let _1033 := convert_t_rational_minus_887272_by_1_to_t_int24(expr_5775)

                ret := _1033
            }

            function cleanup_t_rational_887272_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_887272_by_1_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_rational_887272_by_1(value)))
            }

            /// @src 36:1282:1323  "int24 internal constant MAX_TICK = 887272"
            function constant_MAX_TICK_5780() -> ret {
                /// @src 36:1317:1323  "887272"
                let expr_5779 := 0x0d89e8
                let _1036 := convert_t_rational_887272_by_1_to_t_int24(expr_5779)

                ret := _1036
            }

            /// @ast-id 3918
            /// @src 29:4182:4543  "function checkTicks(int24 tickLower, int24 tickUpper) private pure {..."
            function fun_checkTicks_3918(var_tickLower_3873, var_tickUpper_3875) {

                /// @src 29:4263:4272  "tickLower"
                let _1028 := var_tickLower_3873
                let expr_3878 := _1028
                /// @src 29:4276:4285  "tickUpper"
                let _1029 := var_tickUpper_3875
                let expr_3879 := _1029
                /// @src 29:4263:4285  "tickLower >= tickUpper"
                let expr_3880 := iszero(slt(cleanup_t_int24(expr_3878), cleanup_t_int24(expr_3879)))
                /// @src 29:4259:4344  "if (tickLower >= tickUpper) TicksMisordered.selector.revertWith(tickLower, tickUpper)"
                if expr_3880 {
                    /// @src 29:4287:4311  "TicksMisordered.selector"
                    let expr_3884 := 0xc4433ed500000000000000000000000000000000000000000000000000000000
                    /// @src 29:4287:4322  "TicksMisordered.selector.revertWith"
                    let expr_3885_self := expr_3884
                    /// @src 29:4323:4332  "tickLower"
                    let _1030 := var_tickLower_3873
                    let expr_3886 := _1030
                    /// @src 29:4334:4343  "tickUpper"
                    let _1031 := var_tickUpper_3875
                    let expr_3887 := _1031
                    fun_revertWith_2316(expr_3885_self, expr_3886, expr_3887)
                    /// @src 29:4259:4344  "if (tickLower >= tickUpper) TicksMisordered.selector.revertWith(tickLower, tickUpper)"
                }
                /// @src 29:4358:4367  "tickLower"
                let _1032 := var_tickLower_3873
                let expr_3891 := _1032
                /// @src 29:4370:4378  "TickMath"
                let expr_3892_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 29:4370:4387  "TickMath.MIN_TICK"
                let expr_3893 := constant_MIN_TICK_5776()
                /// @src 29:4358:4387  "tickLower < TickMath.MIN_TICK"
                let expr_3894 := slt(cleanup_t_int24(expr_3891), cleanup_t_int24(expr_3893))
                /// @src 29:4354:4440  "if (tickLower < TickMath.MIN_TICK) TickLowerOutOfBounds.selector.revertWith(tickLower)"
                if expr_3894 {
                    /// @src 29:4389:4418  "TickLowerOutOfBounds.selector"
                    let expr_3898 := 0xd5e2f7ab00000000000000000000000000000000000000000000000000000000
                    /// @src 29:4389:4429  "TickLowerOutOfBounds.selector.revertWith"
                    let expr_3899_self := expr_3898
                    /// @src 29:4430:4439  "tickLower"
                    let _1034 := var_tickLower_3873
                    let expr_3900 := _1034
                    fun_revertWith_2294(expr_3899_self, expr_3900)
                    /// @src 29:4354:4440  "if (tickLower < TickMath.MIN_TICK) TickLowerOutOfBounds.selector.revertWith(tickLower)"
                }
                /// @src 29:4454:4463  "tickUpper"
                let _1035 := var_tickUpper_3875
                let expr_3904 := _1035
                /// @src 29:4466:4474  "TickMath"
                let expr_3905_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 29:4466:4483  "TickMath.MAX_TICK"
                let expr_3906 := constant_MAX_TICK_5780()
                /// @src 29:4454:4483  "tickUpper > TickMath.MAX_TICK"
                let expr_3907 := sgt(cleanup_t_int24(expr_3904), cleanup_t_int24(expr_3906))
                /// @src 29:4450:4536  "if (tickUpper > TickMath.MAX_TICK) TickUpperOutOfBounds.selector.revertWith(tickUpper)"
                if expr_3907 {
                    /// @src 29:4485:4514  "TickUpperOutOfBounds.selector"
                    let expr_3911 := 0x1ad777f800000000000000000000000000000000000000000000000000000000
                    /// @src 29:4485:4525  "TickUpperOutOfBounds.selector.revertWith"
                    let expr_3912_self := expr_3911
                    /// @src 29:4526:4535  "tickUpper"
                    let _1037 := var_tickUpper_3875
                    let expr_3913 := _1037
                    fun_revertWith_2294(expr_3912_self, expr_3913)
                    /// @src 29:4450:4536  "if (tickUpper > TickMath.MAX_TICK) TickUpperOutOfBounds.selector.revertWith(tickUpper)"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_uint128() -> ret {
                ret := 0
            }

            function convert_t_int24_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_int24(value)))
            }

            function mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(slot , key) -> dataSlot {
                mstore(0, convert_t_int24_to_t_int24(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function convert_t_struct$_TickInfo_$3845_storage_to_t_struct$_TickInfo_$3845_storage_ptr(value) -> converted {
                converted := value
            }

            function shift_right_128_unsigned(value) -> newValue {
                newValue :=

                shr(128, value)

            }

            function cleanup_from_storage_t_int128(value) -> cleaned {
                cleaned := signextend(15, value)
            }

            function extract_from_storage_value_offset_16t_int128(slot_value) -> value {
                value := cleanup_from_storage_t_int128(shift_right_128_unsigned(slot_value))
            }

            function read_from_storage_split_offset_16_t_int128(slot) -> value {
                value := extract_from_storage_value_offset_16t_int128(sload(slot))

            }

            function checked_sub_t_int128(x, y) -> diff {
                x := cleanup_t_int128(x)
                y := cleanup_t_int128(y)
                diff := sub(x, y)

                if or(
                    slt(diff, 0xffffffffffffffffffffffffffffffff80000000000000000000000000000000),
                    sgt(diff, 0x7fffffffffffffffffffffffffffffff)
                ) { panic_error_0x11() }

            }

            /// @ast-id 5302
            /// @src 29:25241:27171  "function updateTick(State storage self, int24 tick, int128 liquidityDelta, bool upper)..."
            function fun_updateTick_5302(var_self_5211_slot, var_tick_5213, var_liquidityDelta_5215, var_upper_5217) -> var_flipped_5220, var_liquidityGrossAfter_5222 {
                /// @src 29:25362:25374  "bool flipped"
                let zero_t_bool_1038 := zero_value_for_split_t_bool()
                var_flipped_5220 := zero_t_bool_1038
                /// @src 29:25376:25403  "uint128 liquidityGrossAfter"
                let zero_t_uint128_1039 := zero_value_for_split_t_uint128()
                var_liquidityGrossAfter_5222 := zero_t_uint128_1039

                /// @src 29:25443:25447  "self"
                let _1040_slot := var_self_5211_slot
                let expr_5227_slot := _1040_slot
                /// @src 29:25443:25453  "self.ticks"
                let _1041 := add(expr_5227_slot, 4)
                let _1042_slot := _1041
                let expr_5228_slot := _1042_slot
                /// @src 29:25454:25458  "tick"
                let _1043 := var_tick_5213
                let expr_5229 := _1043
                /// @src 29:25443:25459  "self.ticks[tick]"
                let _1044 := mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(expr_5228_slot,expr_5229)
                let _1045_slot := _1044
                let expr_5230_slot := _1045_slot
                /// @src 29:25419:25459  "TickInfo storage info = self.ticks[tick]"
                let var_info_5226_slot := convert_t_struct$_TickInfo_$3845_storage_to_t_struct$_TickInfo_$3845_storage_ptr(expr_5230_slot)
                /// @src 29:25501:25505  "info"
                let _1046_slot := var_info_5226_slot
                let expr_5234_slot := _1046_slot
                /// @src 29:25501:25520  "info.liquidityGross"
                let _1047 := add(expr_5234_slot, 0)
                let _1048 := read_from_storage_split_offset_0_t_uint128(_1047)
                let expr_5235 := _1048
                /// @src 29:25470:25520  "uint128 liquidityGrossBefore = info.liquidityGross"
                let var_liquidityGrossBefore_5233 := expr_5235
                /// @src 29:25558:25562  "info"
                let _1049_slot := var_info_5226_slot
                let expr_5239_slot := _1049_slot
                /// @src 29:25558:25575  "info.liquidityNet"
                let _1050 := add(expr_5239_slot, 0)
                let _1051 := read_from_storage_split_offset_16_t_int128(_1050)
                let expr_5240 := _1051
                /// @src 29:25530:25575  "int128 liquidityNetBefore = info.liquidityNet"
                let var_liquidityNetBefore_5238 := expr_5240
                /// @src 29:25608:25621  "LiquidityMath"
                let expr_5243_address := linkersymbol("src/libraries/LiquidityMath.sol:LiquidityMath")
                /// @src 29:25631:25651  "liquidityGrossBefore"
                let _1052 := var_liquidityGrossBefore_5233
                let expr_5245 := _1052
                /// @src 29:25653:25667  "liquidityDelta"
                let _1053 := var_liquidityDelta_5215
                let expr_5246 := _1053
                /// @src 29:25608:25668  "LiquidityMath.addDelta(liquidityGrossBefore, liquidityDelta)"
                let expr_5247 := fun_addDelta_7622(expr_5245, expr_5246)
                /// @src 29:25586:25668  "liquidityGrossAfter = LiquidityMath.addDelta(liquidityGrossBefore, liquidityDelta)"
                var_liquidityGrossAfter_5222 := expr_5247
                let expr_5248 := expr_5247
                /// @src 29:25690:25709  "liquidityGrossAfter"
                let _1054 := var_liquidityGrossAfter_5222
                let expr_5251 := _1054
                /// @src 29:25713:25714  "0"
                let expr_5252 := 0x00
                /// @src 29:25690:25714  "liquidityGrossAfter == 0"
                let expr_5253 := eq(cleanup_t_uint128(expr_5251), convert_t_rational_0_by_1_to_t_uint128(expr_5252))
                /// @src 29:25689:25715  "(liquidityGrossAfter == 0)"
                let expr_5254 := expr_5253
                /// @src 29:25720:25740  "liquidityGrossBefore"
                let _1055 := var_liquidityGrossBefore_5233
                let expr_5255 := _1055
                /// @src 29:25744:25745  "0"
                let expr_5256 := 0x00
                /// @src 29:25720:25745  "liquidityGrossBefore == 0"
                let expr_5257 := eq(cleanup_t_uint128(expr_5255), convert_t_rational_0_by_1_to_t_uint128(expr_5256))
                /// @src 29:25719:25746  "(liquidityGrossBefore == 0)"
                let expr_5258 := expr_5257
                /// @src 29:25689:25746  "(liquidityGrossAfter == 0) != (liquidityGrossBefore == 0)"
                let expr_5259 := iszero(eq(cleanup_t_bool(expr_5254), cleanup_t_bool(expr_5258)))
                /// @src 29:25679:25746  "flipped = (liquidityGrossAfter == 0) != (liquidityGrossBefore == 0)"
                var_flipped_5220 := expr_5259
                let expr_5260 := expr_5259
                /// @src 29:25761:25781  "liquidityGrossBefore"
                let _1056 := var_liquidityGrossBefore_5233
                let expr_5262 := _1056
                /// @src 29:25785:25786  "0"
                let expr_5263 := 0x00
                /// @src 29:25761:25786  "liquidityGrossBefore == 0"
                let expr_5264 := eq(cleanup_t_uint128(expr_5262), convert_t_rational_0_by_1_to_t_uint128(expr_5263))
                /// @src 29:25757:26114  "if (liquidityGrossBefore == 0) {..."
                if expr_5264 {
                    /// @src 29:25918:25922  "tick"
                    let _1057 := var_tick_5213
                    let expr_5265 := _1057
                    /// @src 29:25926:25930  "self"
                    let _1058_slot := var_self_5211_slot
                    let expr_5266_slot := _1058_slot
                    /// @src 29:25926:25936  "self.slot0"
                    let _1059 := add(expr_5266_slot, 0)
                    let _1060 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_1059)
                    let expr_5267 := _1060
                    /// @src 29:25926:25941  "self.slot0.tick"
                    let expr_5268_self := expr_5267
                    /// @src 29:25926:25943  "self.slot0.tick()"
                    let expr_5269 := fun_tick_8672(expr_5268_self)
                    /// @src 29:25918:25943  "tick <= self.slot0.tick()"
                    let expr_5270 := iszero(sgt(cleanup_t_int24(expr_5265), cleanup_t_int24(expr_5269)))
                    /// @src 29:25914:26104  "if (tick <= self.slot0.tick()) {..."
                    if expr_5270 {
                        /// @src 29:25992:25996  "self"
                        let _1061_slot := var_self_5211_slot
                        let expr_5274_slot := _1061_slot
                        /// @src 29:25992:26017  "self.feeGrowthGlobal0X128"
                        let _1062 := add(expr_5274_slot, 1)
                        let _1063 := read_from_storage_split_offset_0_t_uint256(_1062)
                        let expr_5275 := _1063
                        /// @src 29:25963:25967  "info"
                        let _1064_slot := var_info_5226_slot
                        let expr_5271_slot := _1064_slot
                        /// @src 29:25963:25989  "info.feeGrowthOutside0X128"
                        let _1065 := add(expr_5271_slot, 1)
                        /// @src 29:25963:26017  "info.feeGrowthOutside0X128 = self.feeGrowthGlobal0X128"
                        update_storage_value_offset_0t_uint256_to_t_uint256(_1065, expr_5275)
                        let expr_5276 := expr_5275
                        /// @src 29:26064:26068  "self"
                        let _1066_slot := var_self_5211_slot
                        let expr_5281_slot := _1066_slot
                        /// @src 29:26064:26089  "self.feeGrowthGlobal1X128"
                        let _1067 := add(expr_5281_slot, 2)
                        let _1068 := read_from_storage_split_offset_0_t_uint256(_1067)
                        let expr_5282 := _1068
                        /// @src 29:26035:26039  "info"
                        let _1069_slot := var_info_5226_slot
                        let expr_5278_slot := _1069_slot
                        /// @src 29:26035:26061  "info.feeGrowthOutside1X128"
                        let _1070 := add(expr_5278_slot, 2)
                        /// @src 29:26035:26089  "info.feeGrowthOutside1X128 = self.feeGrowthGlobal1X128"
                        update_storage_value_offset_0t_uint256_to_t_uint256(_1070, expr_5282)
                        let expr_5283 := expr_5282
                        /// @src 29:25914:26104  "if (tick <= self.slot0.tick()) {..."
                    }
                    /// @src 29:25757:26114  "if (liquidityGrossBefore == 0) {..."
                }
                /// @src 29:26344:26349  "upper"
                let _1071 := var_upper_5217
                let expr_5291 := _1071
                /// @src 29:26344:26425  "upper ? liquidityNetBefore - liquidityDelta : liquidityNetBefore + liquidityDelta"
                let expr_5298
                switch expr_5291
                case 0 {
                    /// @src 29:26390:26408  "liquidityNetBefore"
                    let _1072 := var_liquidityNetBefore_5238
                    let expr_5295 := _1072
                    /// @src 29:26411:26425  "liquidityDelta"
                    let _1073 := var_liquidityDelta_5215
                    let expr_5296 := _1073
                    /// @src 29:26390:26425  "liquidityNetBefore + liquidityDelta"
                    let expr_5297 := checked_add_t_int128(expr_5295, expr_5296)

                    /// @src 29:26344:26425  "upper ? liquidityNetBefore - liquidityDelta : liquidityNetBefore + liquidityDelta"
                    expr_5298 := expr_5297
                }
                default {
                    /// @src 29:26352:26370  "liquidityNetBefore"
                    let _1074 := var_liquidityNetBefore_5238
                    let expr_5292 := _1074
                    /// @src 29:26373:26387  "liquidityDelta"
                    let _1075 := var_liquidityDelta_5215
                    let expr_5293 := _1075
                    /// @src 29:26352:26387  "liquidityNetBefore - liquidityDelta"
                    let expr_5294 := checked_sub_t_int128(expr_5292, expr_5293)

                    /// @src 29:26344:26425  "upper ? liquidityNetBefore - liquidityDelta : liquidityNetBefore + liquidityDelta"
                    expr_5298 := expr_5294
                }
                /// @src 29:26322:26425  "int128 liquidityNet = upper ? liquidityNetBefore - liquidityDelta : liquidityNetBefore + liquidityDelta"
                let var_liquidityNet_5290 := expr_5298
                /// @src 29:26435:27165  "assembly (\"memory-safe\") {..."
                {
                    sstore(var_info_5226_slot, or(and(var_liquidityGrossAfter_5222, 0xffffffffffffffffffffffffffffffff), shl(128, var_liquidityNet_5290)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5322
            /// @src 29:27565:28518  "function tickSpacingToMaxLiquidityPerTick(int24 tickSpacing) internal pure returns (uint128 result) {..."
            function fun_tickSpacingToMaxLiquidityPerTick_5322(var_tickSpacing_5305) -> var_result_5308 {
                /// @src 29:27649:27663  "uint128 result"
                let zero_t_uint128_1076 := zero_value_for_split_t_uint128()
                var_result_5308 := zero_t_uint128_1076

                /// @src 29:28007:28015  "TickMath"
                let expr_5312_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 29:28007:28024  "TickMath.MAX_TICK"
                let expr_5313 := constant_MAX_TICK_5780()
                /// @src 29:27990:28024  "int24 MAX_TICK = TickMath.MAX_TICK"
                let var_MAX_TICK_5311 := expr_5313
                /// @src 29:28051:28059  "TickMath"
                let expr_5317_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                /// @src 29:28051:28068  "TickMath.MIN_TICK"
                let expr_5318 := constant_MIN_TICK_5776()
                /// @src 29:28034:28068  "int24 MIN_TICK = TickMath.MIN_TICK"
                let var_MIN_TICK_5316 := expr_5318
                /// @src 29:28155:28512  "assembly (\"memory-safe\") {..."
                {
                    var_tickSpacing_5305 := signextend(2, var_tickSpacing_5305)
                    let usr$minTick := sub(sdiv(var_MIN_TICK_5316, var_tickSpacing_5305), slt(smod(var_MIN_TICK_5316, var_tickSpacing_5305), 0))
                    let usr$maxTick := sdiv(var_MAX_TICK_5311, var_tickSpacing_5305)
                    let usr$numTicks := add(sub(usr$maxTick, usr$minTick), 1)
                    var_result_5308 := div(sub(shl(128, 1), 1), usr$numTicks)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8416
            /// @src 35:2108:3518  "function flipTick(mapping(int16 => uint256) storage self, int24 tick, int24 tickSpacing) internal {..."
            function fun_flipTick_8416(var_self_8407_slot, var_tick_8409, var_tickSpacing_8411) {

                /// @src 35:2509:3512  "assembly (\"memory-safe\") {..."
                {
                    var_tick_8409 := signextend(2, var_tick_8409)
                    var_tickSpacing_8411 := signextend(2, var_tickSpacing_8411)
                    if smod(var_tick_8409, var_tickSpacing_8411)
                    {
                        let usr$fmp := mload(0x40)
                        mstore(usr$fmp, 0xd4d8f3e6)
                        mstore(add(usr$fmp, 0x20), var_tick_8409)
                        mstore(add(usr$fmp, 0x40), var_tickSpacing_8411)
                        revert(add(usr$fmp, 0x1c), 0x44)
                    }
                    var_tick_8409 := sdiv(var_tick_8409, var_tickSpacing_8411)
                    mstore(0, sar(8, var_tick_8409))
                    mstore(0x20, var_self_8407_slot)
                    let usr$slot := keccak256(0, 0x40)
                    sstore(usr$slot, xor(sload(usr$slot), shl(and(var_tick_8409, 0xff), 1)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function wrapping_sub_t_uint256(x, y) -> diff {
                diff := cleanup_t_uint256(sub(x, y))
            }

            /// @ast-id 5207
            /// @src 29:23300:24503  "function getFeeGrowthInside(State storage self, int24 tickLower, int24 tickUpper)..."
            function fun_getFeeGrowthInside_5207(var_self_5106_slot, var_tickLower_5108, var_tickUpper_5110) -> var_feeGrowthInside0X128_5113, var_feeGrowthInside1X128_5115 {
                /// @src 29:23429:23457  "uint256 feeGrowthInside0X128"
                let zero_t_uint256_1077 := zero_value_for_split_t_uint256()
                var_feeGrowthInside0X128_5113 := zero_t_uint256_1077
                /// @src 29:23459:23487  "uint256 feeGrowthInside1X128"
                let zero_t_uint256_1078 := zero_value_for_split_t_uint256()
                var_feeGrowthInside1X128_5115 := zero_t_uint256_1078

                /// @src 29:23528:23532  "self"
                let _1079_slot := var_self_5106_slot
                let expr_5120_slot := _1079_slot
                /// @src 29:23528:23538  "self.ticks"
                let _1080 := add(expr_5120_slot, 4)
                let _1081_slot := _1080
                let expr_5121_slot := _1081_slot
                /// @src 29:23539:23548  "tickLower"
                let _1082 := var_tickLower_5108
                let expr_5122 := _1082
                /// @src 29:23528:23549  "self.ticks[tickLower]"
                let _1083 := mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(expr_5121_slot,expr_5122)
                let _1084_slot := _1083
                let expr_5123_slot := _1084_slot
                /// @src 29:23503:23549  "TickInfo storage lower = self.ticks[tickLower]"
                let var_lower_5119_slot := convert_t_struct$_TickInfo_$3845_storage_to_t_struct$_TickInfo_$3845_storage_ptr(expr_5123_slot)
                /// @src 29:23584:23588  "self"
                let _1085_slot := var_self_5106_slot
                let expr_5128_slot := _1085_slot
                /// @src 29:23584:23594  "self.ticks"
                let _1086 := add(expr_5128_slot, 4)
                let _1087_slot := _1086
                let expr_5129_slot := _1087_slot
                /// @src 29:23595:23604  "tickUpper"
                let _1088 := var_tickUpper_5110
                let expr_5130 := _1088
                /// @src 29:23584:23605  "self.ticks[tickUpper]"
                let _1089 := mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(expr_5129_slot,expr_5130)
                let _1090_slot := _1089
                let expr_5131_slot := _1090_slot
                /// @src 29:23559:23605  "TickInfo storage upper = self.ticks[tickUpper]"
                let var_upper_5127_slot := convert_t_struct$_TickInfo_$3845_storage_to_t_struct$_TickInfo_$3845_storage_ptr(expr_5131_slot)
                /// @src 29:23635:23639  "self"
                let _1091_slot := var_self_5106_slot
                let expr_5135_slot := _1091_slot
                /// @src 29:23635:23645  "self.slot0"
                let _1092 := add(expr_5135_slot, 0)
                let _1093 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_1092)
                let expr_5136 := _1093
                /// @src 29:23635:23650  "self.slot0.tick"
                let expr_5137_self := expr_5136
                /// @src 29:23635:23652  "self.slot0.tick()"
                let expr_5138 := fun_tick_8672(expr_5137_self)
                /// @src 29:23615:23652  "int24 tickCurrent = self.slot0.tick()"
                let var_tickCurrent_5134 := expr_5138
                /// @src 29:23691:23702  "tickCurrent"
                let _1094 := var_tickCurrent_5134
                let expr_5140 := _1094
                /// @src 29:23705:23714  "tickLower"
                let _1095 := var_tickLower_5108
                let expr_5141 := _1095
                /// @src 29:23691:23714  "tickCurrent < tickLower"
                let expr_5142 := slt(cleanup_t_int24(expr_5140), cleanup_t_int24(expr_5141))
                /// @src 29:23687:24487  "if (tickCurrent < tickLower) {..."
                switch expr_5142
                case 0 {
                    /// @src 29:23937:23948  "tickCurrent"
                    let _1096 := var_tickCurrent_5134
                    let expr_5160 := _1096
                    /// @src 29:23952:23961  "tickUpper"
                    let _1097 := var_tickUpper_5110
                    let expr_5161 := _1097
                    /// @src 29:23937:23961  "tickCurrent >= tickUpper"
                    let expr_5162 := iszero(slt(cleanup_t_int24(expr_5160), cleanup_t_int24(expr_5161)))
                    /// @src 29:23933:24487  "if (tickCurrent >= tickUpper) {..."
                    switch expr_5162
                    case 0 {
                        /// @src 29:24241:24245  "self"
                        let _1098_slot := var_self_5106_slot
                        let expr_5181_slot := _1098_slot
                        /// @src 29:24241:24266  "self.feeGrowthGlobal0X128"
                        let _1099 := add(expr_5181_slot, 1)
                        let _1100 := read_from_storage_split_offset_0_t_uint256(_1099)
                        let expr_5182 := _1100
                        /// @src 29:24269:24274  "lower"
                        let _1101_slot := var_lower_5119_slot
                        let expr_5183_slot := _1101_slot
                        /// @src 29:24269:24296  "lower.feeGrowthOutside0X128"
                        let _1102 := add(expr_5183_slot, 1)
                        let _1103 := read_from_storage_split_offset_0_t_uint256(_1102)
                        let expr_5184 := _1103
                        /// @src 29:24241:24296  "self.feeGrowthGlobal0X128 - lower.feeGrowthOutside0X128"
                        let expr_5185 := wrapping_sub_t_uint256(expr_5182, expr_5184)

                        /// @src 29:24299:24304  "upper"
                        let _1104_slot := var_upper_5127_slot
                        let expr_5186_slot := _1104_slot
                        /// @src 29:24299:24326  "upper.feeGrowthOutside0X128"
                        let _1105 := add(expr_5186_slot, 1)
                        let _1106 := read_from_storage_split_offset_0_t_uint256(_1105)
                        let expr_5187 := _1106
                        /// @src 29:24241:24326  "self.feeGrowthGlobal0X128 - lower.feeGrowthOutside0X128 - upper.feeGrowthOutside0X128"
                        let expr_5188 := wrapping_sub_t_uint256(expr_5185, expr_5187)

                        /// @src 29:24198:24326  "feeGrowthInside0X128 =..."
                        var_feeGrowthInside0X128_5113 := expr_5188
                        let expr_5189 := expr_5188
                        /// @src 29:24387:24391  "self"
                        let _1107_slot := var_self_5106_slot
                        let expr_5192_slot := _1107_slot
                        /// @src 29:24387:24412  "self.feeGrowthGlobal1X128"
                        let _1108 := add(expr_5192_slot, 2)
                        let _1109 := read_from_storage_split_offset_0_t_uint256(_1108)
                        let expr_5193 := _1109
                        /// @src 29:24415:24420  "lower"
                        let _1110_slot := var_lower_5119_slot
                        let expr_5194_slot := _1110_slot
                        /// @src 29:24415:24442  "lower.feeGrowthOutside1X128"
                        let _1111 := add(expr_5194_slot, 2)
                        let _1112 := read_from_storage_split_offset_0_t_uint256(_1111)
                        let expr_5195 := _1112
                        /// @src 29:24387:24442  "self.feeGrowthGlobal1X128 - lower.feeGrowthOutside1X128"
                        let expr_5196 := wrapping_sub_t_uint256(expr_5193, expr_5195)

                        /// @src 29:24445:24450  "upper"
                        let _1113_slot := var_upper_5127_slot
                        let expr_5197_slot := _1113_slot
                        /// @src 29:24445:24472  "upper.feeGrowthOutside1X128"
                        let _1114 := add(expr_5197_slot, 2)
                        let _1115 := read_from_storage_split_offset_0_t_uint256(_1114)
                        let expr_5198 := _1115
                        /// @src 29:24387:24472  "self.feeGrowthGlobal1X128 - lower.feeGrowthOutside1X128 - upper.feeGrowthOutside1X128"
                        let expr_5199 := wrapping_sub_t_uint256(expr_5196, expr_5198)

                        /// @src 29:24344:24472  "feeGrowthInside1X128 =..."
                        var_feeGrowthInside1X128_5115 := expr_5199
                        let expr_5200 := expr_5199
                        /// @src 29:23933:24487  "if (tickCurrent >= tickUpper) {..."
                    }
                    default {
                        /// @src 29:24004:24009  "upper"
                        let _1116_slot := var_upper_5127_slot
                        let expr_5164_slot := _1116_slot
                        /// @src 29:24004:24031  "upper.feeGrowthOutside0X128"
                        let _1117 := add(expr_5164_slot, 1)
                        let _1118 := read_from_storage_split_offset_0_t_uint256(_1117)
                        let expr_5165 := _1118
                        /// @src 29:24034:24039  "lower"
                        let _1119_slot := var_lower_5119_slot
                        let expr_5166_slot := _1119_slot
                        /// @src 29:24034:24061  "lower.feeGrowthOutside0X128"
                        let _1120 := add(expr_5166_slot, 1)
                        let _1121 := read_from_storage_split_offset_0_t_uint256(_1120)
                        let expr_5167 := _1121
                        /// @src 29:24004:24061  "upper.feeGrowthOutside0X128 - lower.feeGrowthOutside0X128"
                        let expr_5168 := wrapping_sub_t_uint256(expr_5165, expr_5167)

                        /// @src 29:23981:24061  "feeGrowthInside0X128 = upper.feeGrowthOutside0X128 - lower.feeGrowthOutside0X128"
                        var_feeGrowthInside0X128_5113 := expr_5168
                        let expr_5169 := expr_5168
                        /// @src 29:24102:24107  "upper"
                        let _1122_slot := var_upper_5127_slot
                        let expr_5172_slot := _1122_slot
                        /// @src 29:24102:24129  "upper.feeGrowthOutside1X128"
                        let _1123 := add(expr_5172_slot, 2)
                        let _1124 := read_from_storage_split_offset_0_t_uint256(_1123)
                        let expr_5173 := _1124
                        /// @src 29:24132:24137  "lower"
                        let _1125_slot := var_lower_5119_slot
                        let expr_5174_slot := _1125_slot
                        /// @src 29:24132:24159  "lower.feeGrowthOutside1X128"
                        let _1126 := add(expr_5174_slot, 2)
                        let _1127 := read_from_storage_split_offset_0_t_uint256(_1126)
                        let expr_5175 := _1127
                        /// @src 29:24102:24159  "upper.feeGrowthOutside1X128 - lower.feeGrowthOutside1X128"
                        let expr_5176 := wrapping_sub_t_uint256(expr_5173, expr_5175)

                        /// @src 29:24079:24159  "feeGrowthInside1X128 = upper.feeGrowthOutside1X128 - lower.feeGrowthOutside1X128"
                        var_feeGrowthInside1X128_5115 := expr_5176
                        let expr_5177 := expr_5176
                        /// @src 29:23933:24487  "if (tickCurrent >= tickUpper) {..."
                    }
                    /// @src 29:23687:24487  "if (tickCurrent < tickLower) {..."
                }
                default {
                    /// @src 29:23757:23762  "lower"
                    let _1128_slot := var_lower_5119_slot
                    let expr_5144_slot := _1128_slot
                    /// @src 29:23757:23784  "lower.feeGrowthOutside0X128"
                    let _1129 := add(expr_5144_slot, 1)
                    let _1130 := read_from_storage_split_offset_0_t_uint256(_1129)
                    let expr_5145 := _1130
                    /// @src 29:23787:23792  "upper"
                    let _1131_slot := var_upper_5127_slot
                    let expr_5146_slot := _1131_slot
                    /// @src 29:23787:23814  "upper.feeGrowthOutside0X128"
                    let _1132 := add(expr_5146_slot, 1)
                    let _1133 := read_from_storage_split_offset_0_t_uint256(_1132)
                    let expr_5147 := _1133
                    /// @src 29:23757:23814  "lower.feeGrowthOutside0X128 - upper.feeGrowthOutside0X128"
                    let expr_5148 := wrapping_sub_t_uint256(expr_5145, expr_5147)

                    /// @src 29:23734:23814  "feeGrowthInside0X128 = lower.feeGrowthOutside0X128 - upper.feeGrowthOutside0X128"
                    var_feeGrowthInside0X128_5113 := expr_5148
                    let expr_5149 := expr_5148
                    /// @src 29:23855:23860  "lower"
                    let _1134_slot := var_lower_5119_slot
                    let expr_5152_slot := _1134_slot
                    /// @src 29:23855:23882  "lower.feeGrowthOutside1X128"
                    let _1135 := add(expr_5152_slot, 2)
                    let _1136 := read_from_storage_split_offset_0_t_uint256(_1135)
                    let expr_5153 := _1136
                    /// @src 29:23885:23890  "upper"
                    let _1137_slot := var_upper_5127_slot
                    let expr_5154_slot := _1137_slot
                    /// @src 29:23885:23912  "upper.feeGrowthOutside1X128"
                    let _1138 := add(expr_5154_slot, 2)
                    let _1139 := read_from_storage_split_offset_0_t_uint256(_1138)
                    let expr_5155 := _1139
                    /// @src 29:23855:23912  "lower.feeGrowthOutside1X128 - upper.feeGrowthOutside1X128"
                    let expr_5156 := wrapping_sub_t_uint256(expr_5153, expr_5155)

                    /// @src 29:23832:23912  "feeGrowthInside1X128 = lower.feeGrowthOutside1X128 - upper.feeGrowthOutside1X128"
                    var_feeGrowthInside1X128_5115 := expr_5156
                    let expr_5157 := expr_5156
                    /// @src 29:23687:24487  "if (tickCurrent < tickLower) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function mapping_index_access_t_mapping$_t_bytes32_$_t_struct$_State_$5433_storage_$_of_t_bytes32(slot , key) -> dataSlot {
                mstore(0, convert_t_bytes32_to_t_bytes32(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function convert_t_struct$_State_$5433_storage_to_t_struct$_State_$5433_storage_ptr(value) -> converted {
                converted := value
            }

            /// @ast-id 5469
            /// @src 30:1464:1787  "function get(mapping(bytes32 => State) storage self, address owner, int24 tickLower, int24 tickUpper, bytes32 salt)..."
            function fun_get_5469(var_self_5439_slot, var_owner_5441, var_tickLower_5443, var_tickUpper_5445, var_salt_5447) -> var_position_5451_slot {

                /// @src 30:1708:1713  "owner"
                let _1140 := var_owner_5441
                let expr_5456 := _1140
                /// @src 30:1715:1724  "tickLower"
                let _1141 := var_tickLower_5443
                let expr_5457 := _1141
                /// @src 30:1726:1735  "tickUpper"
                let _1142 := var_tickUpper_5445
                let expr_5458 := _1142
                /// @src 30:1737:1741  "salt"
                let _1143 := var_salt_5447
                let expr_5459 := _1143
                /// @src 30:1687:1742  "calculatePositionKey(owner, tickLower, tickUpper, salt)"
                let expr_5460 := fun_calculatePositionKey_5485(expr_5456, expr_5457, expr_5458, expr_5459)
                /// @src 30:1665:1742  "bytes32 positionKey = calculatePositionKey(owner, tickLower, tickUpper, salt)"
                let var_positionKey_5454 := expr_5460
                /// @src 30:1763:1767  "self"
                let _1144_slot := var_self_5439_slot
                let expr_5463_slot := _1144_slot
                /// @src 30:1768:1779  "positionKey"
                let _1145 := var_positionKey_5454
                let expr_5464 := _1145
                /// @src 30:1763:1780  "self[positionKey]"
                let _1146 := mapping_index_access_t_mapping$_t_bytes32_$_t_struct$_State_$5433_storage_$_of_t_bytes32(expr_5463_slot,expr_5464)
                let _1147_slot := _1146
                let expr_5465_slot := _1147_slot
                /// @src 30:1752:1780  "position = self[positionKey]"
                var_position_5451_slot := convert_t_struct$_State_$5433_storage_to_t_struct$_State_$5433_storage_ptr(expr_5465_slot)
                let _1148_slot := var_position_5451_slot
                let expr_5466_slot := _1148_slot

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5574
            /// @src 30:3702:4810  "function update(..."
            function fun_update_5574(var_self_5489_slot, var_liquidityDelta_5491, var_feeGrowthInside0X128_5493, var_feeGrowthInside1X128_5495) -> var_feesOwed0_5498, var_feesOwed1_5500 {
                /// @src 30:3877:3894  "uint256 feesOwed0"
                let zero_t_uint256_1149 := zero_value_for_split_t_uint256()
                var_feesOwed0_5498 := zero_t_uint256_1149
                /// @src 30:3896:3913  "uint256 feesOwed1"
                let zero_t_uint256_1150 := zero_value_for_split_t_uint256()
                var_feesOwed1_5500 := zero_t_uint256_1150

                /// @src 30:3945:3949  "self"
                let _1151_slot := var_self_5489_slot
                let expr_5504_slot := _1151_slot
                /// @src 30:3945:3959  "self.liquidity"
                let _1152 := add(expr_5504_slot, 0)
                let _1153 := read_from_storage_split_offset_0_t_uint128(_1152)
                let expr_5505 := _1153
                /// @src 30:3925:3959  "uint128 liquidity = self.liquidity"
                let var_liquidity_5503 := expr_5505
                /// @src 30:3974:3988  "liquidityDelta"
                let _1154 := var_liquidityDelta_5491
                let expr_5507 := _1154
                /// @src 30:3992:3993  "0"
                let expr_5508 := 0x00
                /// @src 30:3974:3993  "liquidityDelta == 0"
                let expr_5509 := eq(cleanup_t_int128(expr_5507), convert_t_rational_0_by_1_to_t_int128(expr_5508))
                /// @src 30:3970:4240  "if (liquidityDelta == 0) {..."
                switch expr_5509
                case 0 {
                    /// @src 30:4180:4193  "LiquidityMath"
                    let expr_5525_address := linkersymbol("src/libraries/LiquidityMath.sol:LiquidityMath")
                    /// @src 30:4203:4212  "liquidity"
                    let _1155 := var_liquidity_5503
                    let expr_5527 := _1155
                    /// @src 30:4214:4228  "liquidityDelta"
                    let _1156 := var_liquidityDelta_5491
                    let expr_5528 := _1156
                    /// @src 30:4180:4229  "LiquidityMath.addDelta(liquidity, liquidityDelta)"
                    let expr_5529 := fun_addDelta_7622(expr_5527, expr_5528)
                    /// @src 30:4163:4167  "self"
                    let _1157_slot := var_self_5489_slot
                    let expr_5522_slot := _1157_slot
                    /// @src 30:4163:4177  "self.liquidity"
                    let _1158 := add(expr_5522_slot, 0)
                    /// @src 30:4163:4229  "self.liquidity = LiquidityMath.addDelta(liquidity, liquidityDelta)"
                    update_storage_value_offset_0t_uint128_to_t_uint128(_1158, expr_5529)
                    let expr_5530 := expr_5529
                    /// @src 30:3970:4240  "if (liquidityDelta == 0) {..."
                }
                default {
                    /// @src 30:4069:4078  "liquidity"
                    let _1159 := var_liquidity_5503
                    let expr_5510 := _1159
                    /// @src 30:4082:4083  "0"
                    let expr_5511 := 0x00
                    /// @src 30:4069:4083  "liquidity == 0"
                    let expr_5512 := eq(cleanup_t_uint128(expr_5510), convert_t_rational_0_by_1_to_t_uint128(expr_5511))
                    /// @src 30:4065:4132  "if (liquidity == 0) CannotUpdateEmptyPosition.selector.revertWith()"
                    if expr_5512 {
                        /// @src 30:4085:4119  "CannotUpdateEmptyPosition.selector"
                        let expr_5516 := 0xaefeb92400000000000000000000000000000000000000000000000000000000
                        /// @src 30:4085:4130  "CannotUpdateEmptyPosition.selector.revertWith"
                        let expr_5517_self := expr_5516
                        fun_revertWith_2274(expr_5517_self)
                        /// @src 30:4065:4132  "if (liquidity == 0) CannotUpdateEmptyPosition.selector.revertWith()"
                    }
                    /// @src 30:3970:4240  "if (liquidityDelta == 0) {..."
                }
                /// @src 30:4395:4403  "FullMath"
                let expr_5535_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                /// @src 30:4411:4431  "feeGrowthInside0X128"
                let _1160 := var_feeGrowthInside0X128_5493
                let expr_5537 := _1160
                /// @src 30:4434:4438  "self"
                let _1161_slot := var_self_5489_slot
                let expr_5538_slot := _1161_slot
                /// @src 30:4434:4463  "self.feeGrowthInside0LastX128"
                let _1162 := add(expr_5538_slot, 1)
                let _1163 := read_from_storage_split_offset_0_t_uint256(_1162)
                let expr_5539 := _1163
                /// @src 30:4411:4463  "feeGrowthInside0X128 - self.feeGrowthInside0LastX128"
                let expr_5540 := wrapping_sub_t_uint256(expr_5537, expr_5539)

                /// @src 30:4465:4474  "liquidity"
                let _1164 := var_liquidity_5503
                let expr_5541 := _1164
                /// @src 30:4476:4489  "FixedPoint128"
                let expr_5542_address := linkersymbol("src/libraries/FixedPoint128.sol:FixedPoint128")
                /// @src 30:4476:4494  "FixedPoint128.Q128"
                let expr_5543 := constant_Q128_7606()
                /// @src 30:4395:4495  "FullMath.mulDiv(feeGrowthInside0X128 - self.feeGrowthInside0LastX128, liquidity, FixedPoint128.Q128)"
                let _1165 := convert_t_uint128_to_t_uint256(expr_5541)
                let expr_5544 := fun_mulDiv_8874(expr_5540, _1165, expr_5543)
                /// @src 30:4367:4495  "feesOwed0 =..."
                var_feesOwed0_5498 := expr_5544
                let expr_5545 := expr_5544
                /// @src 30:4537:4545  "FullMath"
                let expr_5548_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                /// @src 30:4553:4573  "feeGrowthInside1X128"
                let _1166 := var_feeGrowthInside1X128_5495
                let expr_5550 := _1166
                /// @src 30:4576:4580  "self"
                let _1167_slot := var_self_5489_slot
                let expr_5551_slot := _1167_slot
                /// @src 30:4576:4605  "self.feeGrowthInside1LastX128"
                let _1168 := add(expr_5551_slot, 2)
                let _1169 := read_from_storage_split_offset_0_t_uint256(_1168)
                let expr_5552 := _1169
                /// @src 30:4553:4605  "feeGrowthInside1X128 - self.feeGrowthInside1LastX128"
                let expr_5553 := wrapping_sub_t_uint256(expr_5550, expr_5552)

                /// @src 30:4607:4616  "liquidity"
                let _1170 := var_liquidity_5503
                let expr_5554 := _1170
                /// @src 30:4618:4631  "FixedPoint128"
                let expr_5555_address := linkersymbol("src/libraries/FixedPoint128.sol:FixedPoint128")
                /// @src 30:4618:4636  "FixedPoint128.Q128"
                let expr_5556 := constant_Q128_7606()
                /// @src 30:4537:4637  "FullMath.mulDiv(feeGrowthInside1X128 - self.feeGrowthInside1LastX128, liquidity, FixedPoint128.Q128)"
                let _1171 := convert_t_uint128_to_t_uint256(expr_5554)
                let expr_5557 := fun_mulDiv_8874(expr_5553, _1171, expr_5556)
                /// @src 30:4509:4637  "feesOwed1 =..."
                var_feesOwed1_5500 := expr_5557
                let expr_5558 := expr_5557
                /// @src 30:4721:4741  "feeGrowthInside0X128"
                let _1172 := var_feeGrowthInside0X128_5493
                let expr_5564 := _1172
                /// @src 30:4689:4693  "self"
                let _1173_slot := var_self_5489_slot
                let expr_5561_slot := _1173_slot
                /// @src 30:4689:4718  "self.feeGrowthInside0LastX128"
                let _1174 := add(expr_5561_slot, 1)
                /// @src 30:4689:4741  "self.feeGrowthInside0LastX128 = feeGrowthInside0X128"
                update_storage_value_offset_0t_uint256_to_t_uint256(_1174, expr_5564)
                let expr_5565 := expr_5564
                /// @src 30:4783:4803  "feeGrowthInside1X128"
                let _1175 := var_feeGrowthInside1X128_5495
                let expr_5570 := _1175
                /// @src 30:4751:4755  "self"
                let _1176_slot := var_self_5489_slot
                let expr_5567_slot := _1176_slot
                /// @src 30:4751:4780  "self.feeGrowthInside1LastX128"
                let _1177 := add(expr_5567_slot, 2)
                /// @src 30:4751:4803  "self.feeGrowthInside1LastX128 = feeGrowthInside1X128"
                update_storage_value_offset_0t_uint256_to_t_uint256(_1177, expr_5570)
                let expr_5571 := expr_5570

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function update_byte_slice_dynamic32(value, shiftBytes, toInsert) -> result {
                let shiftBits := mul(shiftBytes, 8)
                let mask := shift_left_dynamic(shiftBits, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                toInsert := shift_left_dynamic(shiftBits, toInsert)
                value := and(value, not(mask))
                result := or(value, and(toInsert, mask))
            }

            function update_storage_value_t_uint256_to_t_uint256(slot, offset, value_0) {
                let convertedValue_0 := convert_t_uint256_to_t_uint256(value_0)
                sstore(slot, update_byte_slice_dynamic32(sload(slot), offset, prepare_store_t_uint256(convertedValue_0)))
            }

            function storage_set_to_zero_t_uint256(slot, offset) {
                let zero_0 := zero_value_for_split_t_uint256()
                update_storage_value_t_uint256_to_t_uint256(slot, offset, zero_0)
            }

            function clear_struct_storage_t_struct$_TickInfo_$3845_storage(slot) {

                sstore(add(slot, 0), 0)

                storage_set_to_zero_t_uint256(add(slot, 1), 0)

                storage_set_to_zero_t_uint256(add(slot, 2), 0)

            }

            function panic_error_0x00() {
                mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                mstore(4, 0x00)
                revert(0, 0x24)
            }

            function storage_set_to_zero_t_struct$_TickInfo_$3845_storage(slot, offset) {
                if iszero(eq(offset, 0)) { panic_error_0x00() }
                clear_struct_storage_t_struct$_TickInfo_$3845_storage(slot)
            }

            /// @ast-id 5360
            /// @src 29:28935:29035  "function clearTick(State storage self, int24 tick) internal {..."
            function fun_clearTick_5360(var_self_5348_slot, var_tick_5350) {

                /// @src 29:29012:29016  "self"
                let _1178_slot := var_self_5348_slot
                let expr_5353_slot := _1178_slot
                /// @src 29:29012:29022  "self.ticks"
                let _1179 := add(expr_5353_slot, 4)
                let _1180_slot := _1179
                let expr_5354_slot := _1180_slot
                /// @src 29:29023:29027  "tick"
                let _1181 := var_tick_5350
                let expr_5355 := _1181
                /// @src 29:29012:29028  "self.ticks[tick]"
                let _1182 := mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(expr_5354_slot,expr_5355)
                /// @src 29:29005:29028  "delete self.ticks[tick]"
                storage_set_to_zero_t_struct$_TickInfo_$3845_storage(_1182, 0)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8672
            /// @src 44:1607:1786  "function tick(Slot0 _packed) internal pure returns (int24 _tick) {..."
            function fun_tick_8672(var__packed_8665) -> var__tick_8668 {
                /// @src 44:1659:1670  "int24 _tick"
                let zero_t_int24_1183 := zero_value_for_split_t_int24()
                var__tick_8668 := zero_t_int24_1183

                /// @src 44:1682:1780  "assembly (\"memory-safe\") {..."
                {
                    var__tick_8668 := signextend(2, shr(160, var__packed_8665))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_int24_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_int24(value)))
            }

            function convert_t_int256_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_int256(value)))
            }

            function convert_t_rational_2_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_2_by_1(value)))
            }

            function cleanup_t_rational_340248342086729790484326174814286782778_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_340248342086729790484326174814286782778_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_340248342086729790484326174814286782778_by_1(value)))
            }

            function wrapping_mul_t_uint256(x, y) -> product {
                product := cleanup_t_uint256(mul(x, y))
            }

            function cleanup_t_uint8(value) -> cleaned {
                cleaned := and(value, 0xff)
            }

            function convert_t_rational_128_by_1_to_t_uint8(value) -> converted {
                converted := cleanup_t_uint8(identity(cleanup_t_rational_128_by_1(value)))
            }

            function shift_right_t_uint256_t_uint8(value, bits) -> result {
                bits := cleanup_t_uint8(bits)
                result := cleanup_t_uint256(shift_right_unsigned_dynamic(bits, cleanup_t_uint256(value)))
            }

            function convert_t_rational_4_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_4_by_1(value)))
            }

            function cleanup_t_rational_340214320654664324051920982716015181260_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_340214320654664324051920982716015181260_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_340214320654664324051920982716015181260_by_1(value)))
            }

            function convert_t_rational_8_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_8_by_1(value)))
            }

            function cleanup_t_rational_340146287995602323631171512101879684304_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_340146287995602323631171512101879684304_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_340146287995602323631171512101879684304_by_1(value)))
            }

            function convert_t_rational_16_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_16_by_1(value)))
            }

            function cleanup_t_rational_340010263488231146823593991679159461444_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_340010263488231146823593991679159461444_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_340010263488231146823593991679159461444_by_1(value)))
            }

            function cleanup_t_rational_339738377640345403697157401104375502016_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_339738377640345403697157401104375502016_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_339738377640345403697157401104375502016_by_1(value)))
            }

            function convert_t_rational_64_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_64_by_1(value)))
            }

            function cleanup_t_rational_339195258003219555707034227454543997025_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_339195258003219555707034227454543997025_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_339195258003219555707034227454543997025_by_1(value)))
            }

            function convert_t_rational_128_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_128_by_1(value)))
            }

            function cleanup_t_rational_338111622100601834656805679988414885971_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_338111622100601834656805679988414885971_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_338111622100601834656805679988414885971_by_1(value)))
            }

            function convert_t_rational_256_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_256_by_1(value)))
            }

            function cleanup_t_rational_335954724994790223023589805789778977700_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_335954724994790223023589805789778977700_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_335954724994790223023589805789778977700_by_1(value)))
            }

            function convert_t_rational_512_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_512_by_1(value)))
            }

            function cleanup_t_rational_331682121138379247127172139078559817300_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_331682121138379247127172139078559817300_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_331682121138379247127172139078559817300_by_1(value)))
            }

            function convert_t_rational_1024_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_1024_by_1(value)))
            }

            function cleanup_t_rational_323299236684853023288211250268160618739_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_323299236684853023288211250268160618739_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_323299236684853023288211250268160618739_by_1(value)))
            }

            function convert_t_rational_2048_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_2048_by_1(value)))
            }

            function cleanup_t_rational_307163716377032989948697243942600083929_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_307163716377032989948697243942600083929_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_307163716377032989948697243942600083929_by_1(value)))
            }

            function convert_t_rational_4096_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_4096_by_1(value)))
            }

            function cleanup_t_rational_277268403626896220162999269216087595045_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_277268403626896220162999269216087595045_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_277268403626896220162999269216087595045_by_1(value)))
            }

            function convert_t_rational_8192_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_8192_by_1(value)))
            }

            function cleanup_t_rational_225923453940442621947126027127485391333_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_225923453940442621947126027127485391333_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_225923453940442621947126027127485391333_by_1(value)))
            }

            function cleanup_t_rational_16384_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_16384_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_16384_by_1(value)))
            }

            function cleanup_t_rational_149997214084966997727330242082538205943_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_149997214084966997727330242082538205943_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_149997214084966997727330242082538205943_by_1(value)))
            }

            function cleanup_t_rational_32768_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_32768_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_32768_by_1(value)))
            }

            function cleanup_t_rational_66119101136024775622716233608466517926_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_66119101136024775622716233608466517926_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_66119101136024775622716233608466517926_by_1(value)))
            }

            function cleanup_t_rational_65536_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_65536_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_65536_by_1(value)))
            }

            function cleanup_t_rational_12847376061809297530290974190478138313_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_12847376061809297530290974190478138313_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_12847376061809297530290974190478138313_by_1(value)))
            }

            function cleanup_t_rational_131072_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_131072_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_131072_by_1(value)))
            }

            function cleanup_t_rational_485053260817066172746253684029974020_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_485053260817066172746253684029974020_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_485053260817066172746253684029974020_by_1(value)))
            }

            function cleanup_t_rational_262144_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_262144_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_262144_by_1(value)))
            }

            function cleanup_t_rational_691415978906521570653435304214168_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_691415978906521570653435304214168_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_691415978906521570653435304214168_by_1(value)))
            }

            function cleanup_t_rational_524288_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_524288_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_524288_by_1(value)))
            }

            function cleanup_t_rational_1404880482679654955896180642_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1404880482679654955896180642_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_1404880482679654955896180642_by_1(value)))
            }

            /// @ast-id 6164
            /// @src 36:3149:7167  "function getSqrtPriceAtTick(int24 tick) internal pure returns (uint160 sqrtPriceX96) {..."
            function fun_getSqrtPriceAtTick_6164(var_tick_5845) -> var_sqrtPriceX96_5848 {
                /// @src 36:3212:3232  "uint160 sqrtPriceX96"
                let zero_t_uint160_1184 := zero_value_for_split_t_uint160()
                var_sqrtPriceX96_5848 := zero_t_uint160_1184

                /// @src 36:3268:3283  "uint256 absTick"
                let var_absTick_5851
                let zero_t_uint256_1185 := zero_value_for_split_t_uint256()
                var_absTick_5851 := zero_t_uint256_1185
                /// @src 36:3297:3756  "assembly (\"memory-safe\") {..."
                {
                    var_tick_5845 := signextend(2, var_tick_5845)
                    let usr$mask := sar(255, var_tick_5845)
                    var_absTick_5851 := xor(usr$mask, add(usr$mask, var_tick_5845))
                }
                /// @src 36:3774:3781  "absTick"
                let _1186 := var_absTick_5851
                let expr_5854 := _1186
                /// @src 36:3799:3807  "MAX_TICK"
                let expr_5859 := constant_MAX_TICK_5780()
                /// @src 36:3792:3808  "int256(MAX_TICK)"
                let expr_5860 := convert_t_int24_to_t_int256(expr_5859)
                /// @src 36:3784:3809  "uint256(int256(MAX_TICK))"
                let expr_5861 := convert_t_int256_to_t_uint256(expr_5860)
                /// @src 36:3774:3809  "absTick > uint256(int256(MAX_TICK))"
                let expr_5862 := gt(cleanup_t_uint256(expr_5854), cleanup_t_uint256(expr_5861))
                /// @src 36:3770:3848  "if (absTick > uint256(int256(MAX_TICK))) InvalidTick.selector.revertWith(tick)"
                if expr_5862 {
                    /// @src 36:3811:3831  "InvalidTick.selector"
                    let expr_5866 := 0x8b86327a00000000000000000000000000000000000000000000000000000000
                    /// @src 36:3811:3842  "InvalidTick.selector.revertWith"
                    let expr_5867_self := expr_5866
                    /// @src 36:3843:3847  "tick"
                    let _1187 := var_tick_5845
                    let expr_5868 := _1187
                    fun_revertWith_2294(expr_5867_self, expr_5868)
                    /// @src 36:3770:3848  "if (absTick > uint256(int256(MAX_TICK))) InvalidTick.selector.revertWith(tick)"
                }
                /// @src 36:4356:4369  "uint256 price"
                let var_price_5873
                let zero_t_uint256_1188 := zero_value_for_split_t_uint256()
                var_price_5873 := zero_t_uint256_1188
                /// @src 36:4383:4543  "assembly (\"memory-safe\") {..."
                {
                    var_price_5873 := xor(shl(128, 1), mul(xor(shl(128, 1), 0xfffcb933bd6fad37aa2d162d1a594001), and(var_absTick_5851, 0x1)))
                }
                /// @src 36:4560:4567  "absTick"
                let _1189 := var_absTick_5851
                let expr_5876 := _1189
                /// @src 36:4570:4573  "0x2"
                let expr_5877 := 0x02
                /// @src 36:4560:4573  "absTick & 0x2"
                let expr_5878 := and(expr_5876, convert_t_rational_2_by_1_to_t_uint256(expr_5877))

                /// @src 36:4577:4578  "0"
                let expr_5879 := 0x00
                /// @src 36:4560:4578  "absTick & 0x2 != 0"
                let expr_5880 := iszero(eq(cleanup_t_uint256(expr_5878), convert_t_rational_0_by_1_to_t_uint256(expr_5879)))
                /// @src 36:4556:4639  "if (absTick & 0x2 != 0) price = (price * 0xfff97272373d413259a46990580e213a) >> 128"
                if expr_5880 {
                    /// @src 36:4589:4594  "price"
                    let _1190 := var_price_5873
                    let expr_5882 := _1190
                    /// @src 36:4597:4631  "0xfff97272373d413259a46990580e213a"
                    let expr_5883 := 0xfff97272373d413259a46990580e213a
                    /// @src 36:4589:4631  "price * 0xfff97272373d413259a46990580e213a"
                    let expr_5884 := wrapping_mul_t_uint256(expr_5882, convert_t_rational_340248342086729790484326174814286782778_by_1_to_t_uint256(expr_5883))

                    /// @src 36:4588:4632  "(price * 0xfff97272373d413259a46990580e213a)"
                    let expr_5885 := expr_5884
                    /// @src 36:4636:4639  "128"
                    let expr_5886 := 0x80
                    /// @src 36:4588:4639  "(price * 0xfff97272373d413259a46990580e213a) >> 128"
                    let _1191 := convert_t_rational_128_by_1_to_t_uint8(expr_5886)
                    let expr_5887 :=
                    shift_right_t_uint256_t_uint8(expr_5885, _1191)

                    /// @src 36:4580:4639  "price = (price * 0xfff97272373d413259a46990580e213a) >> 128"
                    var_price_5873 := expr_5887
                    let expr_5888 := expr_5887
                    /// @src 36:4556:4639  "if (absTick & 0x2 != 0) price = (price * 0xfff97272373d413259a46990580e213a) >> 128"
                }
                /// @src 36:4657:4664  "absTick"
                let _1192 := var_absTick_5851
                let expr_5891 := _1192
                /// @src 36:4667:4670  "0x4"
                let expr_5892 := 0x04
                /// @src 36:4657:4670  "absTick & 0x4"
                let expr_5893 := and(expr_5891, convert_t_rational_4_by_1_to_t_uint256(expr_5892))

                /// @src 36:4674:4675  "0"
                let expr_5894 := 0x00
                /// @src 36:4657:4675  "absTick & 0x4 != 0"
                let expr_5895 := iszero(eq(cleanup_t_uint256(expr_5893), convert_t_rational_0_by_1_to_t_uint256(expr_5894)))
                /// @src 36:4653:4736  "if (absTick & 0x4 != 0) price = (price * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128"
                if expr_5895 {
                    /// @src 36:4686:4691  "price"
                    let _1193 := var_price_5873
                    let expr_5897 := _1193
                    /// @src 36:4694:4728  "0xfff2e50f5f656932ef12357cf3c7fdcc"
                    let expr_5898 := 0xfff2e50f5f656932ef12357cf3c7fdcc
                    /// @src 36:4686:4728  "price * 0xfff2e50f5f656932ef12357cf3c7fdcc"
                    let expr_5899 := wrapping_mul_t_uint256(expr_5897, convert_t_rational_340214320654664324051920982716015181260_by_1_to_t_uint256(expr_5898))

                    /// @src 36:4685:4729  "(price * 0xfff2e50f5f656932ef12357cf3c7fdcc)"
                    let expr_5900 := expr_5899
                    /// @src 36:4733:4736  "128"
                    let expr_5901 := 0x80
                    /// @src 36:4685:4736  "(price * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128"
                    let _1194 := convert_t_rational_128_by_1_to_t_uint8(expr_5901)
                    let expr_5902 :=
                    shift_right_t_uint256_t_uint8(expr_5900, _1194)

                    /// @src 36:4677:4736  "price = (price * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128"
                    var_price_5873 := expr_5902
                    let expr_5903 := expr_5902
                    /// @src 36:4653:4736  "if (absTick & 0x4 != 0) price = (price * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128"
                }
                /// @src 36:4754:4761  "absTick"
                let _1195 := var_absTick_5851
                let expr_5906 := _1195
                /// @src 36:4764:4767  "0x8"
                let expr_5907 := 0x08
                /// @src 36:4754:4767  "absTick & 0x8"
                let expr_5908 := and(expr_5906, convert_t_rational_8_by_1_to_t_uint256(expr_5907))

                /// @src 36:4771:4772  "0"
                let expr_5909 := 0x00
                /// @src 36:4754:4772  "absTick & 0x8 != 0"
                let expr_5910 := iszero(eq(cleanup_t_uint256(expr_5908), convert_t_rational_0_by_1_to_t_uint256(expr_5909)))
                /// @src 36:4750:4833  "if (absTick & 0x8 != 0) price = (price * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128"
                if expr_5910 {
                    /// @src 36:4783:4788  "price"
                    let _1196 := var_price_5873
                    let expr_5912 := _1196
                    /// @src 36:4791:4825  "0xffe5caca7e10e4e61c3624eaa0941cd0"
                    let expr_5913 := 0xffe5caca7e10e4e61c3624eaa0941cd0
                    /// @src 36:4783:4825  "price * 0xffe5caca7e10e4e61c3624eaa0941cd0"
                    let expr_5914 := wrapping_mul_t_uint256(expr_5912, convert_t_rational_340146287995602323631171512101879684304_by_1_to_t_uint256(expr_5913))

                    /// @src 36:4782:4826  "(price * 0xffe5caca7e10e4e61c3624eaa0941cd0)"
                    let expr_5915 := expr_5914
                    /// @src 36:4830:4833  "128"
                    let expr_5916 := 0x80
                    /// @src 36:4782:4833  "(price * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128"
                    let _1197 := convert_t_rational_128_by_1_to_t_uint8(expr_5916)
                    let expr_5917 :=
                    shift_right_t_uint256_t_uint8(expr_5915, _1197)

                    /// @src 36:4774:4833  "price = (price * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128"
                    var_price_5873 := expr_5917
                    let expr_5918 := expr_5917
                    /// @src 36:4750:4833  "if (absTick & 0x8 != 0) price = (price * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128"
                }
                /// @src 36:4851:4858  "absTick"
                let _1198 := var_absTick_5851
                let expr_5921 := _1198
                /// @src 36:4861:4865  "0x10"
                let expr_5922 := 0x10
                /// @src 36:4851:4865  "absTick & 0x10"
                let expr_5923 := and(expr_5921, convert_t_rational_16_by_1_to_t_uint256(expr_5922))

                /// @src 36:4869:4870  "0"
                let expr_5924 := 0x00
                /// @src 36:4851:4870  "absTick & 0x10 != 0"
                let expr_5925 := iszero(eq(cleanup_t_uint256(expr_5923), convert_t_rational_0_by_1_to_t_uint256(expr_5924)))
                /// @src 36:4847:4931  "if (absTick & 0x10 != 0) price = (price * 0xffcb9843d60f6159c9db58835c926644) >> 128"
                if expr_5925 {
                    /// @src 36:4881:4886  "price"
                    let _1199 := var_price_5873
                    let expr_5927 := _1199
                    /// @src 36:4889:4923  "0xffcb9843d60f6159c9db58835c926644"
                    let expr_5928 := 0xffcb9843d60f6159c9db58835c926644
                    /// @src 36:4881:4923  "price * 0xffcb9843d60f6159c9db58835c926644"
                    let expr_5929 := wrapping_mul_t_uint256(expr_5927, convert_t_rational_340010263488231146823593991679159461444_by_1_to_t_uint256(expr_5928))

                    /// @src 36:4880:4924  "(price * 0xffcb9843d60f6159c9db58835c926644)"
                    let expr_5930 := expr_5929
                    /// @src 36:4928:4931  "128"
                    let expr_5931 := 0x80
                    /// @src 36:4880:4931  "(price * 0xffcb9843d60f6159c9db58835c926644) >> 128"
                    let _1200 := convert_t_rational_128_by_1_to_t_uint8(expr_5931)
                    let expr_5932 :=
                    shift_right_t_uint256_t_uint8(expr_5930, _1200)

                    /// @src 36:4872:4931  "price = (price * 0xffcb9843d60f6159c9db58835c926644) >> 128"
                    var_price_5873 := expr_5932
                    let expr_5933 := expr_5932
                    /// @src 36:4847:4931  "if (absTick & 0x10 != 0) price = (price * 0xffcb9843d60f6159c9db58835c926644) >> 128"
                }
                /// @src 36:4949:4956  "absTick"
                let _1201 := var_absTick_5851
                let expr_5936 := _1201
                /// @src 36:4959:4963  "0x20"
                let expr_5937 := 0x20
                /// @src 36:4949:4963  "absTick & 0x20"
                let expr_5938 := and(expr_5936, convert_t_rational_32_by_1_to_t_uint256(expr_5937))

                /// @src 36:4967:4968  "0"
                let expr_5939 := 0x00
                /// @src 36:4949:4968  "absTick & 0x20 != 0"
                let expr_5940 := iszero(eq(cleanup_t_uint256(expr_5938), convert_t_rational_0_by_1_to_t_uint256(expr_5939)))
                /// @src 36:4945:5029  "if (absTick & 0x20 != 0) price = (price * 0xff973b41fa98c081472e6896dfb254c0) >> 128"
                if expr_5940 {
                    /// @src 36:4979:4984  "price"
                    let _1202 := var_price_5873
                    let expr_5942 := _1202
                    /// @src 36:4987:5021  "0xff973b41fa98c081472e6896dfb254c0"
                    let expr_5943 := 0xff973b41fa98c081472e6896dfb254c0
                    /// @src 36:4979:5021  "price * 0xff973b41fa98c081472e6896dfb254c0"
                    let expr_5944 := wrapping_mul_t_uint256(expr_5942, convert_t_rational_339738377640345403697157401104375502016_by_1_to_t_uint256(expr_5943))

                    /// @src 36:4978:5022  "(price * 0xff973b41fa98c081472e6896dfb254c0)"
                    let expr_5945 := expr_5944
                    /// @src 36:5026:5029  "128"
                    let expr_5946 := 0x80
                    /// @src 36:4978:5029  "(price * 0xff973b41fa98c081472e6896dfb254c0) >> 128"
                    let _1203 := convert_t_rational_128_by_1_to_t_uint8(expr_5946)
                    let expr_5947 :=
                    shift_right_t_uint256_t_uint8(expr_5945, _1203)

                    /// @src 36:4970:5029  "price = (price * 0xff973b41fa98c081472e6896dfb254c0) >> 128"
                    var_price_5873 := expr_5947
                    let expr_5948 := expr_5947
                    /// @src 36:4945:5029  "if (absTick & 0x20 != 0) price = (price * 0xff973b41fa98c081472e6896dfb254c0) >> 128"
                }
                /// @src 36:5047:5054  "absTick"
                let _1204 := var_absTick_5851
                let expr_5951 := _1204
                /// @src 36:5057:5061  "0x40"
                let expr_5952 := 0x40
                /// @src 36:5047:5061  "absTick & 0x40"
                let expr_5953 := and(expr_5951, convert_t_rational_64_by_1_to_t_uint256(expr_5952))

                /// @src 36:5065:5066  "0"
                let expr_5954 := 0x00
                /// @src 36:5047:5066  "absTick & 0x40 != 0"
                let expr_5955 := iszero(eq(cleanup_t_uint256(expr_5953), convert_t_rational_0_by_1_to_t_uint256(expr_5954)))
                /// @src 36:5043:5127  "if (absTick & 0x40 != 0) price = (price * 0xff2ea16466c96a3843ec78b326b52861) >> 128"
                if expr_5955 {
                    /// @src 36:5077:5082  "price"
                    let _1205 := var_price_5873
                    let expr_5957 := _1205
                    /// @src 36:5085:5119  "0xff2ea16466c96a3843ec78b326b52861"
                    let expr_5958 := 0xff2ea16466c96a3843ec78b326b52861
                    /// @src 36:5077:5119  "price * 0xff2ea16466c96a3843ec78b326b52861"
                    let expr_5959 := wrapping_mul_t_uint256(expr_5957, convert_t_rational_339195258003219555707034227454543997025_by_1_to_t_uint256(expr_5958))

                    /// @src 36:5076:5120  "(price * 0xff2ea16466c96a3843ec78b326b52861)"
                    let expr_5960 := expr_5959
                    /// @src 36:5124:5127  "128"
                    let expr_5961 := 0x80
                    /// @src 36:5076:5127  "(price * 0xff2ea16466c96a3843ec78b326b52861) >> 128"
                    let _1206 := convert_t_rational_128_by_1_to_t_uint8(expr_5961)
                    let expr_5962 :=
                    shift_right_t_uint256_t_uint8(expr_5960, _1206)

                    /// @src 36:5068:5127  "price = (price * 0xff2ea16466c96a3843ec78b326b52861) >> 128"
                    var_price_5873 := expr_5962
                    let expr_5963 := expr_5962
                    /// @src 36:5043:5127  "if (absTick & 0x40 != 0) price = (price * 0xff2ea16466c96a3843ec78b326b52861) >> 128"
                }
                /// @src 36:5145:5152  "absTick"
                let _1207 := var_absTick_5851
                let expr_5966 := _1207
                /// @src 36:5155:5159  "0x80"
                let expr_5967 := 0x80
                /// @src 36:5145:5159  "absTick & 0x80"
                let expr_5968 := and(expr_5966, convert_t_rational_128_by_1_to_t_uint256(expr_5967))

                /// @src 36:5163:5164  "0"
                let expr_5969 := 0x00
                /// @src 36:5145:5164  "absTick & 0x80 != 0"
                let expr_5970 := iszero(eq(cleanup_t_uint256(expr_5968), convert_t_rational_0_by_1_to_t_uint256(expr_5969)))
                /// @src 36:5141:5225  "if (absTick & 0x80 != 0) price = (price * 0xfe5dee046a99a2a811c461f1969c3053) >> 128"
                if expr_5970 {
                    /// @src 36:5175:5180  "price"
                    let _1208 := var_price_5873
                    let expr_5972 := _1208
                    /// @src 36:5183:5217  "0xfe5dee046a99a2a811c461f1969c3053"
                    let expr_5973 := 0xfe5dee046a99a2a811c461f1969c3053
                    /// @src 36:5175:5217  "price * 0xfe5dee046a99a2a811c461f1969c3053"
                    let expr_5974 := wrapping_mul_t_uint256(expr_5972, convert_t_rational_338111622100601834656805679988414885971_by_1_to_t_uint256(expr_5973))

                    /// @src 36:5174:5218  "(price * 0xfe5dee046a99a2a811c461f1969c3053)"
                    let expr_5975 := expr_5974
                    /// @src 36:5222:5225  "128"
                    let expr_5976 := 0x80
                    /// @src 36:5174:5225  "(price * 0xfe5dee046a99a2a811c461f1969c3053) >> 128"
                    let _1209 := convert_t_rational_128_by_1_to_t_uint8(expr_5976)
                    let expr_5977 :=
                    shift_right_t_uint256_t_uint8(expr_5975, _1209)

                    /// @src 36:5166:5225  "price = (price * 0xfe5dee046a99a2a811c461f1969c3053) >> 128"
                    var_price_5873 := expr_5977
                    let expr_5978 := expr_5977
                    /// @src 36:5141:5225  "if (absTick & 0x80 != 0) price = (price * 0xfe5dee046a99a2a811c461f1969c3053) >> 128"
                }
                /// @src 36:5243:5250  "absTick"
                let _1210 := var_absTick_5851
                let expr_5981 := _1210
                /// @src 36:5253:5258  "0x100"
                let expr_5982 := 0x0100
                /// @src 36:5243:5258  "absTick & 0x100"
                let expr_5983 := and(expr_5981, convert_t_rational_256_by_1_to_t_uint256(expr_5982))

                /// @src 36:5262:5263  "0"
                let expr_5984 := 0x00
                /// @src 36:5243:5263  "absTick & 0x100 != 0"
                let expr_5985 := iszero(eq(cleanup_t_uint256(expr_5983), convert_t_rational_0_by_1_to_t_uint256(expr_5984)))
                /// @src 36:5239:5324  "if (absTick & 0x100 != 0) price = (price * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128"
                if expr_5985 {
                    /// @src 36:5274:5279  "price"
                    let _1211 := var_price_5873
                    let expr_5987 := _1211
                    /// @src 36:5282:5316  "0xfcbe86c7900a88aedcffc83b479aa3a4"
                    let expr_5988 := 0xfcbe86c7900a88aedcffc83b479aa3a4
                    /// @src 36:5274:5316  "price * 0xfcbe86c7900a88aedcffc83b479aa3a4"
                    let expr_5989 := wrapping_mul_t_uint256(expr_5987, convert_t_rational_335954724994790223023589805789778977700_by_1_to_t_uint256(expr_5988))

                    /// @src 36:5273:5317  "(price * 0xfcbe86c7900a88aedcffc83b479aa3a4)"
                    let expr_5990 := expr_5989
                    /// @src 36:5321:5324  "128"
                    let expr_5991 := 0x80
                    /// @src 36:5273:5324  "(price * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128"
                    let _1212 := convert_t_rational_128_by_1_to_t_uint8(expr_5991)
                    let expr_5992 :=
                    shift_right_t_uint256_t_uint8(expr_5990, _1212)

                    /// @src 36:5265:5324  "price = (price * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128"
                    var_price_5873 := expr_5992
                    let expr_5993 := expr_5992
                    /// @src 36:5239:5324  "if (absTick & 0x100 != 0) price = (price * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128"
                }
                /// @src 36:5342:5349  "absTick"
                let _1213 := var_absTick_5851
                let expr_5996 := _1213
                /// @src 36:5352:5357  "0x200"
                let expr_5997 := 0x0200
                /// @src 36:5342:5357  "absTick & 0x200"
                let expr_5998 := and(expr_5996, convert_t_rational_512_by_1_to_t_uint256(expr_5997))

                /// @src 36:5361:5362  "0"
                let expr_5999 := 0x00
                /// @src 36:5342:5362  "absTick & 0x200 != 0"
                let expr_6000 := iszero(eq(cleanup_t_uint256(expr_5998), convert_t_rational_0_by_1_to_t_uint256(expr_5999)))
                /// @src 36:5338:5423  "if (absTick & 0x200 != 0) price = (price * 0xf987a7253ac413176f2b074cf7815e54) >> 128"
                if expr_6000 {
                    /// @src 36:5373:5378  "price"
                    let _1214 := var_price_5873
                    let expr_6002 := _1214
                    /// @src 36:5381:5415  "0xf987a7253ac413176f2b074cf7815e54"
                    let expr_6003 := 0xf987a7253ac413176f2b074cf7815e54
                    /// @src 36:5373:5415  "price * 0xf987a7253ac413176f2b074cf7815e54"
                    let expr_6004 := wrapping_mul_t_uint256(expr_6002, convert_t_rational_331682121138379247127172139078559817300_by_1_to_t_uint256(expr_6003))

                    /// @src 36:5372:5416  "(price * 0xf987a7253ac413176f2b074cf7815e54)"
                    let expr_6005 := expr_6004
                    /// @src 36:5420:5423  "128"
                    let expr_6006 := 0x80
                    /// @src 36:5372:5423  "(price * 0xf987a7253ac413176f2b074cf7815e54) >> 128"
                    let _1215 := convert_t_rational_128_by_1_to_t_uint8(expr_6006)
                    let expr_6007 :=
                    shift_right_t_uint256_t_uint8(expr_6005, _1215)

                    /// @src 36:5364:5423  "price = (price * 0xf987a7253ac413176f2b074cf7815e54) >> 128"
                    var_price_5873 := expr_6007
                    let expr_6008 := expr_6007
                    /// @src 36:5338:5423  "if (absTick & 0x200 != 0) price = (price * 0xf987a7253ac413176f2b074cf7815e54) >> 128"
                }
                /// @src 36:5441:5448  "absTick"
                let _1216 := var_absTick_5851
                let expr_6011 := _1216
                /// @src 36:5451:5456  "0x400"
                let expr_6012 := 0x0400
                /// @src 36:5441:5456  "absTick & 0x400"
                let expr_6013 := and(expr_6011, convert_t_rational_1024_by_1_to_t_uint256(expr_6012))

                /// @src 36:5460:5461  "0"
                let expr_6014 := 0x00
                /// @src 36:5441:5461  "absTick & 0x400 != 0"
                let expr_6015 := iszero(eq(cleanup_t_uint256(expr_6013), convert_t_rational_0_by_1_to_t_uint256(expr_6014)))
                /// @src 36:5437:5522  "if (absTick & 0x400 != 0) price = (price * 0xf3392b0822b70005940c7a398e4b70f3) >> 128"
                if expr_6015 {
                    /// @src 36:5472:5477  "price"
                    let _1217 := var_price_5873
                    let expr_6017 := _1217
                    /// @src 36:5480:5514  "0xf3392b0822b70005940c7a398e4b70f3"
                    let expr_6018 := 0xf3392b0822b70005940c7a398e4b70f3
                    /// @src 36:5472:5514  "price * 0xf3392b0822b70005940c7a398e4b70f3"
                    let expr_6019 := wrapping_mul_t_uint256(expr_6017, convert_t_rational_323299236684853023288211250268160618739_by_1_to_t_uint256(expr_6018))

                    /// @src 36:5471:5515  "(price * 0xf3392b0822b70005940c7a398e4b70f3)"
                    let expr_6020 := expr_6019
                    /// @src 36:5519:5522  "128"
                    let expr_6021 := 0x80
                    /// @src 36:5471:5522  "(price * 0xf3392b0822b70005940c7a398e4b70f3) >> 128"
                    let _1218 := convert_t_rational_128_by_1_to_t_uint8(expr_6021)
                    let expr_6022 :=
                    shift_right_t_uint256_t_uint8(expr_6020, _1218)

                    /// @src 36:5463:5522  "price = (price * 0xf3392b0822b70005940c7a398e4b70f3) >> 128"
                    var_price_5873 := expr_6022
                    let expr_6023 := expr_6022
                    /// @src 36:5437:5522  "if (absTick & 0x400 != 0) price = (price * 0xf3392b0822b70005940c7a398e4b70f3) >> 128"
                }
                /// @src 36:5540:5547  "absTick"
                let _1219 := var_absTick_5851
                let expr_6026 := _1219
                /// @src 36:5550:5555  "0x800"
                let expr_6027 := 0x0800
                /// @src 36:5540:5555  "absTick & 0x800"
                let expr_6028 := and(expr_6026, convert_t_rational_2048_by_1_to_t_uint256(expr_6027))

                /// @src 36:5559:5560  "0"
                let expr_6029 := 0x00
                /// @src 36:5540:5560  "absTick & 0x800 != 0"
                let expr_6030 := iszero(eq(cleanup_t_uint256(expr_6028), convert_t_rational_0_by_1_to_t_uint256(expr_6029)))
                /// @src 36:5536:5621  "if (absTick & 0x800 != 0) price = (price * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128"
                if expr_6030 {
                    /// @src 36:5571:5576  "price"
                    let _1220 := var_price_5873
                    let expr_6032 := _1220
                    /// @src 36:5579:5613  "0xe7159475a2c29b7443b29c7fa6e889d9"
                    let expr_6033 := 0xe7159475a2c29b7443b29c7fa6e889d9
                    /// @src 36:5571:5613  "price * 0xe7159475a2c29b7443b29c7fa6e889d9"
                    let expr_6034 := wrapping_mul_t_uint256(expr_6032, convert_t_rational_307163716377032989948697243942600083929_by_1_to_t_uint256(expr_6033))

                    /// @src 36:5570:5614  "(price * 0xe7159475a2c29b7443b29c7fa6e889d9)"
                    let expr_6035 := expr_6034
                    /// @src 36:5618:5621  "128"
                    let expr_6036 := 0x80
                    /// @src 36:5570:5621  "(price * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128"
                    let _1221 := convert_t_rational_128_by_1_to_t_uint8(expr_6036)
                    let expr_6037 :=
                    shift_right_t_uint256_t_uint8(expr_6035, _1221)

                    /// @src 36:5562:5621  "price = (price * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128"
                    var_price_5873 := expr_6037
                    let expr_6038 := expr_6037
                    /// @src 36:5536:5621  "if (absTick & 0x800 != 0) price = (price * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128"
                }
                /// @src 36:5639:5646  "absTick"
                let _1222 := var_absTick_5851
                let expr_6041 := _1222
                /// @src 36:5649:5655  "0x1000"
                let expr_6042 := 0x1000
                /// @src 36:5639:5655  "absTick & 0x1000"
                let expr_6043 := and(expr_6041, convert_t_rational_4096_by_1_to_t_uint256(expr_6042))

                /// @src 36:5659:5660  "0"
                let expr_6044 := 0x00
                /// @src 36:5639:5660  "absTick & 0x1000 != 0"
                let expr_6045 := iszero(eq(cleanup_t_uint256(expr_6043), convert_t_rational_0_by_1_to_t_uint256(expr_6044)))
                /// @src 36:5635:5721  "if (absTick & 0x1000 != 0) price = (price * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128"
                if expr_6045 {
                    /// @src 36:5671:5676  "price"
                    let _1223 := var_price_5873
                    let expr_6047 := _1223
                    /// @src 36:5679:5713  "0xd097f3bdfd2022b8845ad8f792aa5825"
                    let expr_6048 := 0xd097f3bdfd2022b8845ad8f792aa5825
                    /// @src 36:5671:5713  "price * 0xd097f3bdfd2022b8845ad8f792aa5825"
                    let expr_6049 := wrapping_mul_t_uint256(expr_6047, convert_t_rational_277268403626896220162999269216087595045_by_1_to_t_uint256(expr_6048))

                    /// @src 36:5670:5714  "(price * 0xd097f3bdfd2022b8845ad8f792aa5825)"
                    let expr_6050 := expr_6049
                    /// @src 36:5718:5721  "128"
                    let expr_6051 := 0x80
                    /// @src 36:5670:5721  "(price * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128"
                    let _1224 := convert_t_rational_128_by_1_to_t_uint8(expr_6051)
                    let expr_6052 :=
                    shift_right_t_uint256_t_uint8(expr_6050, _1224)

                    /// @src 36:5662:5721  "price = (price * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128"
                    var_price_5873 := expr_6052
                    let expr_6053 := expr_6052
                    /// @src 36:5635:5721  "if (absTick & 0x1000 != 0) price = (price * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128"
                }
                /// @src 36:5739:5746  "absTick"
                let _1225 := var_absTick_5851
                let expr_6056 := _1225
                /// @src 36:5749:5755  "0x2000"
                let expr_6057 := 0x2000
                /// @src 36:5739:5755  "absTick & 0x2000"
                let expr_6058 := and(expr_6056, convert_t_rational_8192_by_1_to_t_uint256(expr_6057))

                /// @src 36:5759:5760  "0"
                let expr_6059 := 0x00
                /// @src 36:5739:5760  "absTick & 0x2000 != 0"
                let expr_6060 := iszero(eq(cleanup_t_uint256(expr_6058), convert_t_rational_0_by_1_to_t_uint256(expr_6059)))
                /// @src 36:5735:5821  "if (absTick & 0x2000 != 0) price = (price * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128"
                if expr_6060 {
                    /// @src 36:5771:5776  "price"
                    let _1226 := var_price_5873
                    let expr_6062 := _1226
                    /// @src 36:5779:5813  "0xa9f746462d870fdf8a65dc1f90e061e5"
                    let expr_6063 := 0xa9f746462d870fdf8a65dc1f90e061e5
                    /// @src 36:5771:5813  "price * 0xa9f746462d870fdf8a65dc1f90e061e5"
                    let expr_6064 := wrapping_mul_t_uint256(expr_6062, convert_t_rational_225923453940442621947126027127485391333_by_1_to_t_uint256(expr_6063))

                    /// @src 36:5770:5814  "(price * 0xa9f746462d870fdf8a65dc1f90e061e5)"
                    let expr_6065 := expr_6064
                    /// @src 36:5818:5821  "128"
                    let expr_6066 := 0x80
                    /// @src 36:5770:5821  "(price * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128"
                    let _1227 := convert_t_rational_128_by_1_to_t_uint8(expr_6066)
                    let expr_6067 :=
                    shift_right_t_uint256_t_uint8(expr_6065, _1227)

                    /// @src 36:5762:5821  "price = (price * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128"
                    var_price_5873 := expr_6067
                    let expr_6068 := expr_6067
                    /// @src 36:5735:5821  "if (absTick & 0x2000 != 0) price = (price * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128"
                }
                /// @src 36:5839:5846  "absTick"
                let _1228 := var_absTick_5851
                let expr_6071 := _1228
                /// @src 36:5849:5855  "0x4000"
                let expr_6072 := 0x4000
                /// @src 36:5839:5855  "absTick & 0x4000"
                let expr_6073 := and(expr_6071, convert_t_rational_16384_by_1_to_t_uint256(expr_6072))

                /// @src 36:5859:5860  "0"
                let expr_6074 := 0x00
                /// @src 36:5839:5860  "absTick & 0x4000 != 0"
                let expr_6075 := iszero(eq(cleanup_t_uint256(expr_6073), convert_t_rational_0_by_1_to_t_uint256(expr_6074)))
                /// @src 36:5835:5921  "if (absTick & 0x4000 != 0) price = (price * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128"
                if expr_6075 {
                    /// @src 36:5871:5876  "price"
                    let _1229 := var_price_5873
                    let expr_6077 := _1229
                    /// @src 36:5879:5913  "0x70d869a156d2a1b890bb3df62baf32f7"
                    let expr_6078 := 0x70d869a156d2a1b890bb3df62baf32f7
                    /// @src 36:5871:5913  "price * 0x70d869a156d2a1b890bb3df62baf32f7"
                    let expr_6079 := wrapping_mul_t_uint256(expr_6077, convert_t_rational_149997214084966997727330242082538205943_by_1_to_t_uint256(expr_6078))

                    /// @src 36:5870:5914  "(price * 0x70d869a156d2a1b890bb3df62baf32f7)"
                    let expr_6080 := expr_6079
                    /// @src 36:5918:5921  "128"
                    let expr_6081 := 0x80
                    /// @src 36:5870:5921  "(price * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128"
                    let _1230 := convert_t_rational_128_by_1_to_t_uint8(expr_6081)
                    let expr_6082 :=
                    shift_right_t_uint256_t_uint8(expr_6080, _1230)

                    /// @src 36:5862:5921  "price = (price * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128"
                    var_price_5873 := expr_6082
                    let expr_6083 := expr_6082
                    /// @src 36:5835:5921  "if (absTick & 0x4000 != 0) price = (price * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128"
                }
                /// @src 36:5939:5946  "absTick"
                let _1231 := var_absTick_5851
                let expr_6086 := _1231
                /// @src 36:5949:5955  "0x8000"
                let expr_6087 := 0x8000
                /// @src 36:5939:5955  "absTick & 0x8000"
                let expr_6088 := and(expr_6086, convert_t_rational_32768_by_1_to_t_uint256(expr_6087))

                /// @src 36:5959:5960  "0"
                let expr_6089 := 0x00
                /// @src 36:5939:5960  "absTick & 0x8000 != 0"
                let expr_6090 := iszero(eq(cleanup_t_uint256(expr_6088), convert_t_rational_0_by_1_to_t_uint256(expr_6089)))
                /// @src 36:5935:6021  "if (absTick & 0x8000 != 0) price = (price * 0x31be135f97d08fd981231505542fcfa6) >> 128"
                if expr_6090 {
                    /// @src 36:5971:5976  "price"
                    let _1232 := var_price_5873
                    let expr_6092 := _1232
                    /// @src 36:5979:6013  "0x31be135f97d08fd981231505542fcfa6"
                    let expr_6093 := 0x31be135f97d08fd981231505542fcfa6
                    /// @src 36:5971:6013  "price * 0x31be135f97d08fd981231505542fcfa6"
                    let expr_6094 := wrapping_mul_t_uint256(expr_6092, convert_t_rational_66119101136024775622716233608466517926_by_1_to_t_uint256(expr_6093))

                    /// @src 36:5970:6014  "(price * 0x31be135f97d08fd981231505542fcfa6)"
                    let expr_6095 := expr_6094
                    /// @src 36:6018:6021  "128"
                    let expr_6096 := 0x80
                    /// @src 36:5970:6021  "(price * 0x31be135f97d08fd981231505542fcfa6) >> 128"
                    let _1233 := convert_t_rational_128_by_1_to_t_uint8(expr_6096)
                    let expr_6097 :=
                    shift_right_t_uint256_t_uint8(expr_6095, _1233)

                    /// @src 36:5962:6021  "price = (price * 0x31be135f97d08fd981231505542fcfa6) >> 128"
                    var_price_5873 := expr_6097
                    let expr_6098 := expr_6097
                    /// @src 36:5935:6021  "if (absTick & 0x8000 != 0) price = (price * 0x31be135f97d08fd981231505542fcfa6) >> 128"
                }
                /// @src 36:6039:6046  "absTick"
                let _1234 := var_absTick_5851
                let expr_6101 := _1234
                /// @src 36:6049:6056  "0x10000"
                let expr_6102 := 0x010000
                /// @src 36:6039:6056  "absTick & 0x10000"
                let expr_6103 := and(expr_6101, convert_t_rational_65536_by_1_to_t_uint256(expr_6102))

                /// @src 36:6060:6061  "0"
                let expr_6104 := 0x00
                /// @src 36:6039:6061  "absTick & 0x10000 != 0"
                let expr_6105 := iszero(eq(cleanup_t_uint256(expr_6103), convert_t_rational_0_by_1_to_t_uint256(expr_6104)))
                /// @src 36:6035:6121  "if (absTick & 0x10000 != 0) price = (price * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128"
                if expr_6105 {
                    /// @src 36:6072:6077  "price"
                    let _1235 := var_price_5873
                    let expr_6107 := _1235
                    /// @src 36:6080:6113  "0x9aa508b5b7a84e1c677de54f3e99bc9"
                    let expr_6108 := 0x09aa508b5b7a84e1c677de54f3e99bc9
                    /// @src 36:6072:6113  "price * 0x9aa508b5b7a84e1c677de54f3e99bc9"
                    let expr_6109 := wrapping_mul_t_uint256(expr_6107, convert_t_rational_12847376061809297530290974190478138313_by_1_to_t_uint256(expr_6108))

                    /// @src 36:6071:6114  "(price * 0x9aa508b5b7a84e1c677de54f3e99bc9)"
                    let expr_6110 := expr_6109
                    /// @src 36:6118:6121  "128"
                    let expr_6111 := 0x80
                    /// @src 36:6071:6121  "(price * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128"
                    let _1236 := convert_t_rational_128_by_1_to_t_uint8(expr_6111)
                    let expr_6112 :=
                    shift_right_t_uint256_t_uint8(expr_6110, _1236)

                    /// @src 36:6063:6121  "price = (price * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128"
                    var_price_5873 := expr_6112
                    let expr_6113 := expr_6112
                    /// @src 36:6035:6121  "if (absTick & 0x10000 != 0) price = (price * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128"
                }
                /// @src 36:6139:6146  "absTick"
                let _1237 := var_absTick_5851
                let expr_6116 := _1237
                /// @src 36:6149:6156  "0x20000"
                let expr_6117 := 0x020000
                /// @src 36:6139:6156  "absTick & 0x20000"
                let expr_6118 := and(expr_6116, convert_t_rational_131072_by_1_to_t_uint256(expr_6117))

                /// @src 36:6160:6161  "0"
                let expr_6119 := 0x00
                /// @src 36:6139:6161  "absTick & 0x20000 != 0"
                let expr_6120 := iszero(eq(cleanup_t_uint256(expr_6118), convert_t_rational_0_by_1_to_t_uint256(expr_6119)))
                /// @src 36:6135:6220  "if (absTick & 0x20000 != 0) price = (price * 0x5d6af8dedb81196699c329225ee604) >> 128"
                if expr_6120 {
                    /// @src 36:6172:6177  "price"
                    let _1238 := var_price_5873
                    let expr_6122 := _1238
                    /// @src 36:6180:6212  "0x5d6af8dedb81196699c329225ee604"
                    let expr_6123 := 0x5d6af8dedb81196699c329225ee604
                    /// @src 36:6172:6212  "price * 0x5d6af8dedb81196699c329225ee604"
                    let expr_6124 := wrapping_mul_t_uint256(expr_6122, convert_t_rational_485053260817066172746253684029974020_by_1_to_t_uint256(expr_6123))

                    /// @src 36:6171:6213  "(price * 0x5d6af8dedb81196699c329225ee604)"
                    let expr_6125 := expr_6124
                    /// @src 36:6217:6220  "128"
                    let expr_6126 := 0x80
                    /// @src 36:6171:6220  "(price * 0x5d6af8dedb81196699c329225ee604) >> 128"
                    let _1239 := convert_t_rational_128_by_1_to_t_uint8(expr_6126)
                    let expr_6127 :=
                    shift_right_t_uint256_t_uint8(expr_6125, _1239)

                    /// @src 36:6163:6220  "price = (price * 0x5d6af8dedb81196699c329225ee604) >> 128"
                    var_price_5873 := expr_6127
                    let expr_6128 := expr_6127
                    /// @src 36:6135:6220  "if (absTick & 0x20000 != 0) price = (price * 0x5d6af8dedb81196699c329225ee604) >> 128"
                }
                /// @src 36:6238:6245  "absTick"
                let _1240 := var_absTick_5851
                let expr_6131 := _1240
                /// @src 36:6248:6255  "0x40000"
                let expr_6132 := 0x040000
                /// @src 36:6238:6255  "absTick & 0x40000"
                let expr_6133 := and(expr_6131, convert_t_rational_262144_by_1_to_t_uint256(expr_6132))

                /// @src 36:6259:6260  "0"
                let expr_6134 := 0x00
                /// @src 36:6238:6260  "absTick & 0x40000 != 0"
                let expr_6135 := iszero(eq(cleanup_t_uint256(expr_6133), convert_t_rational_0_by_1_to_t_uint256(expr_6134)))
                /// @src 36:6234:6317  "if (absTick & 0x40000 != 0) price = (price * 0x2216e584f5fa1ea926041bedfe98) >> 128"
                if expr_6135 {
                    /// @src 36:6271:6276  "price"
                    let _1241 := var_price_5873
                    let expr_6137 := _1241
                    /// @src 36:6279:6309  "0x2216e584f5fa1ea926041bedfe98"
                    let expr_6138 := 0x2216e584f5fa1ea926041bedfe98
                    /// @src 36:6271:6309  "price * 0x2216e584f5fa1ea926041bedfe98"
                    let expr_6139 := wrapping_mul_t_uint256(expr_6137, convert_t_rational_691415978906521570653435304214168_by_1_to_t_uint256(expr_6138))

                    /// @src 36:6270:6310  "(price * 0x2216e584f5fa1ea926041bedfe98)"
                    let expr_6140 := expr_6139
                    /// @src 36:6314:6317  "128"
                    let expr_6141 := 0x80
                    /// @src 36:6270:6317  "(price * 0x2216e584f5fa1ea926041bedfe98) >> 128"
                    let _1242 := convert_t_rational_128_by_1_to_t_uint8(expr_6141)
                    let expr_6142 :=
                    shift_right_t_uint256_t_uint8(expr_6140, _1242)

                    /// @src 36:6262:6317  "price = (price * 0x2216e584f5fa1ea926041bedfe98) >> 128"
                    var_price_5873 := expr_6142
                    let expr_6143 := expr_6142
                    /// @src 36:6234:6317  "if (absTick & 0x40000 != 0) price = (price * 0x2216e584f5fa1ea926041bedfe98) >> 128"
                }
                /// @src 36:6335:6342  "absTick"
                let _1243 := var_absTick_5851
                let expr_6146 := _1243
                /// @src 36:6345:6352  "0x80000"
                let expr_6147 := 0x080000
                /// @src 36:6335:6352  "absTick & 0x80000"
                let expr_6148 := and(expr_6146, convert_t_rational_524288_by_1_to_t_uint256(expr_6147))

                /// @src 36:6356:6357  "0"
                let expr_6149 := 0x00
                /// @src 36:6335:6357  "absTick & 0x80000 != 0"
                let expr_6150 := iszero(eq(cleanup_t_uint256(expr_6148), convert_t_rational_0_by_1_to_t_uint256(expr_6149)))
                /// @src 36:6331:6409  "if (absTick & 0x80000 != 0) price = (price * 0x48a170391f7dc42444e8fa2) >> 128"
                if expr_6150 {
                    /// @src 36:6368:6373  "price"
                    let _1244 := var_price_5873
                    let expr_6152 := _1244
                    /// @src 36:6376:6401  "0x48a170391f7dc42444e8fa2"
                    let expr_6153 := 0x048a170391f7dc42444e8fa2
                    /// @src 36:6368:6401  "price * 0x48a170391f7dc42444e8fa2"
                    let expr_6154 := wrapping_mul_t_uint256(expr_6152, convert_t_rational_1404880482679654955896180642_by_1_to_t_uint256(expr_6153))

                    /// @src 36:6367:6402  "(price * 0x48a170391f7dc42444e8fa2)"
                    let expr_6155 := expr_6154
                    /// @src 36:6406:6409  "128"
                    let expr_6156 := 0x80
                    /// @src 36:6367:6409  "(price * 0x48a170391f7dc42444e8fa2) >> 128"
                    let _1245 := convert_t_rational_128_by_1_to_t_uint8(expr_6156)
                    let expr_6157 :=
                    shift_right_t_uint256_t_uint8(expr_6155, _1245)

                    /// @src 36:6359:6409  "price = (price * 0x48a170391f7dc42444e8fa2) >> 128"
                    var_price_5873 := expr_6157
                    let expr_6158 := expr_6157
                    /// @src 36:6331:6409  "if (absTick & 0x80000 != 0) price = (price * 0x48a170391f7dc42444e8fa2) >> 128"
                }
                /// @src 36:6424:7151  "assembly (\"memory-safe\") {..."
                {
                    if sgt(var_tick_5845, 0)
                    {
                        var_price_5873 := div(not(0), var_price_5873)
                    }
                    var_sqrtPriceX96_5848 := shr(32, add(var_price_5873, sub(shl(32, 1), 1)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_int128_to_t_uint128(value) -> converted {
                converted := cleanup_t_uint128(identity(cleanup_t_int128(value)))
            }

            function negate_wrapping_t_int256(value) -> ret {
                ret := cleanup_t_int256(sub(0, value))
            }

            /// @ast-id 8113
            /// @src 33:13649:14073  "function getAmount1Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, int128 liquidity)..."
            function fun_getAmount1Delta_8113(var_sqrtPriceAX96_8073, var_sqrtPriceBX96_8075, var_liquidity_8077) -> var__8080 {
                /// @src 33:13785:13791  "int256"
                let zero_t_int256_1246 := zero_value_for_split_t_int256()
                var__8080 := zero_t_int256_1246

                /// @src 33:13838:13847  "liquidity"
                let _1247 := var_liquidity_8077
                let expr_8082 := _1247
                /// @src 33:13850:13851  "0"
                let expr_8083 := 0x00
                /// @src 33:13838:13851  "liquidity < 0"
                let expr_8084 := slt(cleanup_t_int128(expr_8082), convert_t_rational_0_by_1_to_t_int128(expr_8083))
                /// @src 33:13838:14056  "liquidity < 0..."
                let expr_8109
                switch expr_8084
                case 0 {
                    /// @src 33:13990:14003  "sqrtPriceAX96"
                    let _1248 := var_sqrtPriceAX96_8073
                    let expr_8098 := _1248
                    /// @src 33:14005:14018  "sqrtPriceBX96"
                    let _1249 := var_sqrtPriceBX96_8075
                    let expr_8099 := _1249
                    /// @src 33:14028:14037  "liquidity"
                    let _1250 := var_liquidity_8077
                    let expr_8102 := _1250
                    /// @src 33:14020:14038  "uint128(liquidity)"
                    let expr_8103 := convert_t_int128_to_t_uint128(expr_8102)
                    /// @src 33:14040:14044  "true"
                    let expr_8104 := 0x01
                    /// @src 33:13974:14045  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true)"
                    let expr_8105 := fun_getAmount1Delta_8027(expr_8098, expr_8099, expr_8103, expr_8104)
                    /// @src 33:13974:14054  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256"
                    let expr_8106_self := expr_8105
                    /// @src 33:13974:14056  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256()"
                    let expr_8107 := fun_toInt256_5720(expr_8106_self)
                    /// @src 33:13973:14056  "-getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256()"
                    let expr_8108 := negate_wrapping_t_int256(expr_8107)
                    /// @src 33:13838:14056  "liquidity < 0..."
                    expr_8109 := expr_8108
                }
                default {
                    /// @src 33:13886:13899  "sqrtPriceAX96"
                    let _1251 := var_sqrtPriceAX96_8073
                    let expr_8086 := _1251
                    /// @src 33:13901:13914  "sqrtPriceBX96"
                    let _1252 := var_sqrtPriceBX96_8075
                    let expr_8087 := _1252
                    /// @src 33:13925:13934  "liquidity"
                    let _1253 := var_liquidity_8077
                    let expr_8090 := _1253
                    /// @src 33:13924:13934  "-liquidity"
                    let expr_8091 := negate_wrapping_t_int128(expr_8090)
                    /// @src 33:13916:13935  "uint128(-liquidity)"
                    let expr_8092 := convert_t_int128_to_t_uint128(expr_8091)
                    /// @src 33:13937:13942  "false"
                    let expr_8093 := 0x00
                    /// @src 33:13870:13943  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false)"
                    let expr_8094 := fun_getAmount1Delta_8027(expr_8086, expr_8087, expr_8092, expr_8093)
                    /// @src 33:13870:13952  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false).toInt256"
                    let expr_8095_self := expr_8094
                    /// @src 33:13870:13954  "getAmount1Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false).toInt256()"
                    let expr_8096 := fun_toInt256_5720(expr_8095_self)
                    /// @src 33:13838:14056  "liquidity < 0..."
                    expr_8109 := expr_8096
                }
                /// @src 33:13831:14056  "return liquidity < 0..."
                var__8080 := expr_8109
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8070
            /// @src 33:12876:13300  "function getAmount0Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, int128 liquidity)..."
            function fun_getAmount0Delta_8070(var_sqrtPriceAX96_8030, var_sqrtPriceBX96_8032, var_liquidity_8034) -> var__8037 {
                /// @src 33:13012:13018  "int256"
                let zero_t_int256_1254 := zero_value_for_split_t_int256()
                var__8037 := zero_t_int256_1254

                /// @src 33:13065:13074  "liquidity"
                let _1255 := var_liquidity_8034
                let expr_8039 := _1255
                /// @src 33:13077:13078  "0"
                let expr_8040 := 0x00
                /// @src 33:13065:13078  "liquidity < 0"
                let expr_8041 := slt(cleanup_t_int128(expr_8039), convert_t_rational_0_by_1_to_t_int128(expr_8040))
                /// @src 33:13065:13283  "liquidity < 0..."
                let expr_8066
                switch expr_8041
                case 0 {
                    /// @src 33:13217:13230  "sqrtPriceAX96"
                    let _1256 := var_sqrtPriceAX96_8030
                    let expr_8055 := _1256
                    /// @src 33:13232:13245  "sqrtPriceBX96"
                    let _1257 := var_sqrtPriceBX96_8032
                    let expr_8056 := _1257
                    /// @src 33:13255:13264  "liquidity"
                    let _1258 := var_liquidity_8034
                    let expr_8059 := _1258
                    /// @src 33:13247:13265  "uint128(liquidity)"
                    let expr_8060 := convert_t_int128_to_t_uint128(expr_8059)
                    /// @src 33:13267:13271  "true"
                    let expr_8061 := 0x01
                    /// @src 33:13201:13272  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true)"
                    let expr_8062 := fun_getAmount0Delta_7971(expr_8055, expr_8056, expr_8060, expr_8061)
                    /// @src 33:13201:13281  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256"
                    let expr_8063_self := expr_8062
                    /// @src 33:13201:13283  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256()"
                    let expr_8064 := fun_toInt256_5720(expr_8063_self)
                    /// @src 33:13200:13283  "-getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(liquidity), true).toInt256()"
                    let expr_8065 := negate_wrapping_t_int256(expr_8064)
                    /// @src 33:13065:13283  "liquidity < 0..."
                    expr_8066 := expr_8065
                }
                default {
                    /// @src 33:13113:13126  "sqrtPriceAX96"
                    let _1259 := var_sqrtPriceAX96_8030
                    let expr_8043 := _1259
                    /// @src 33:13128:13141  "sqrtPriceBX96"
                    let _1260 := var_sqrtPriceBX96_8032
                    let expr_8044 := _1260
                    /// @src 33:13152:13161  "liquidity"
                    let _1261 := var_liquidity_8034
                    let expr_8047 := _1261
                    /// @src 33:13151:13161  "-liquidity"
                    let expr_8048 := negate_wrapping_t_int128(expr_8047)
                    /// @src 33:13143:13162  "uint128(-liquidity)"
                    let expr_8049 := convert_t_int128_to_t_uint128(expr_8048)
                    /// @src 33:13164:13169  "false"
                    let expr_8050 := 0x00
                    /// @src 33:13097:13170  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false)"
                    let expr_8051 := fun_getAmount0Delta_7971(expr_8043, expr_8044, expr_8049, expr_8050)
                    /// @src 33:13097:13179  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false).toInt256"
                    let expr_8052_self := expr_8051
                    /// @src 33:13097:13181  "getAmount0Delta(sqrtPriceAX96, sqrtPriceBX96, uint128(-liquidity), false).toInt256()"
                    let expr_8053 := fun_toInt256_5720(expr_8052_self)
                    /// @src 33:13065:13283  "liquidity < 0..."
                    expr_8066 := expr_8053
                }
                /// @src 33:13058:13283  "return liquidity < 0..."
                var__8037 := expr_8066
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7622
            /// @src 25:369:739  "function addDelta(uint128 x, int128 y) internal pure returns (uint128 z) {..."
            function fun_addDelta_7622(var_x_7613, var_y_7615) -> var_z_7618 {
                /// @src 25:431:440  "uint128 z"
                let zero_t_uint128_1262 := zero_value_for_split_t_uint128()
                var_z_7618 := zero_t_uint128_1262

                /// @src 25:452:733  "assembly (\"memory-safe\") {..."
                {
                    var_z_7618 := add(and(var_x_7613, 0xffffffffffffffffffffffffffffffff), signextend(15, var_y_7615))
                    if shr(128, var_z_7618)
                    {
                        mstore(0, 0x93dafdf1)
                        revert(0x1c, 0x04)
                    }
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2858
            /// @src 23:8196:8681  "function callHookWithReturnDelta(IHooks self, bytes memory data, bool parseReturn) internal returns (int256) {..."
            function fun_callHookWithReturnDelta_2858(var_self_2820_address, var_data_2822_mpos, var_parseReturn_2824) -> var__2827 {
                /// @src 23:8297:8303  "int256"
                let zero_t_int256_1263 := zero_value_for_split_t_int256()
                var__2827 := zero_t_int256_1263

                /// @src 23:8346:8350  "self"
                let _1264_address := var_self_2820_address
                let expr_2832_address := _1264_address
                /// @src 23:8352:8356  "data"
                let _1265_mpos := var_data_2822_mpos
                let expr_2833_mpos := _1265_mpos
                /// @src 23:8337:8357  "callHook(self, data)"
                let expr_2834_mpos := fun_callHook_2816(expr_2832_address, expr_2833_mpos)
                /// @src 23:8315:8357  "bytes memory result = callHook(self, data)"
                let var_result_2830_mpos := expr_2834_mpos
                /// @src 23:8450:8461  "parseReturn"
                let _1266 := var_parseReturn_2824
                let expr_2836 := _1266
                /// @src 23:8449:8461  "!parseReturn"
                let expr_2837 := cleanup_t_bool(iszero(expr_2836))
                /// @src 23:8445:8471  "if (!parseReturn) return 0"
                if expr_2837 {
                    /// @src 23:8470:8471  "0"
                    let expr_2838 := 0x00
                    /// @src 23:8463:8471  "return 0"
                    var__2827 := convert_t_rational_0_by_1_to_t_int256(expr_2838)
                    leave
                    /// @src 23:8445:8471  "if (!parseReturn) return 0"
                }
                /// @src 23:8570:8576  "result"
                let _1267_mpos := var_result_2830_mpos
                let expr_2841_mpos := _1267_mpos
                /// @src 23:8570:8583  "result.length"
                let expr_2842 := array_length_t_bytes_memory_ptr(expr_2841_mpos)
                /// @src 23:8587:8589  "64"
                let expr_2843 := 0x40
                /// @src 23:8570:8589  "result.length != 64"
                let expr_2844 := iszero(eq(cleanup_t_uint256(expr_2842), convert_t_rational_64_by_1_to_t_uint256(expr_2843)))
                /// @src 23:8566:8632  "if (result.length != 64) InvalidHookResponse.selector.revertWith()"
                if expr_2844 {
                    /// @src 23:8591:8619  "InvalidHookResponse.selector"
                    let expr_2848 := 0x1e048e1d00000000000000000000000000000000000000000000000000000000
                    /// @src 23:8591:8630  "InvalidHookResponse.selector.revertWith"
                    let expr_2849_self := expr_2848
                    fun_revertWith_2274(expr_2849_self)
                    /// @src 23:8566:8632  "if (result.length != 64) InvalidHookResponse.selector.revertWith()"
                }
                /// @src 23:8649:8655  "result"
                let _1268_mpos := var_result_2830_mpos
                let expr_2853_mpos := _1268_mpos
                /// @src 23:8649:8672  "result.parseReturnDelta"
                let expr_2854_self_mpos := expr_2853_mpos
                /// @src 23:8649:8674  "result.parseReturnDelta()"
                let expr_2855 := fun_parseReturnDelta_7599(expr_2854_self_mpos)
                /// @src 23:8642:8674  "return result.parseReturnDelta()"
                var__2827 := expr_2855
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6395
            /// @src 38:1070:1466  "function sub(BalanceDelta a, BalanceDelta b) pure returns (BalanceDelta) {..."
            function fun_sub_6395(var_a_6369, var_b_6372) -> var__6376 {
                /// @src 38:1129:1141  "BalanceDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_1269 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var__6376 := zero_t_userDefinedValueType$_BalanceDelta_$6311_1269

                /// @src 38:1149:1160  "int256 res0"
                let var_res0_6379
                let zero_t_int256_1270 := zero_value_for_split_t_int256()
                var_res0_6379 := zero_t_int256_1270
                /// @src 38:1166:1177  "int256 res1"
                let var_res1_6382
                let zero_t_int256_1271 := zero_value_for_split_t_int256()
                var_res1_6382 := zero_t_int256_1271
                /// @src 38:1183:1403  "assembly (\"memory-safe\") {..."
                {
                    let usr$a0 := sar(128, var_a_6369)
                    let usr$a1 := signextend(15, var_a_6369)
                    let usr$b0 := sar(128, var_b_6372)
                    let usr$b1 := signextend(15, var_b_6372)
                    var_res0_6379 := sub(usr$a0, usr$b0)
                    var_res1_6382 := sub(usr$a1, usr$b1)
                }
                /// @src 38:1430:1434  "res0"
                let _1272 := var_res0_6379
                let expr_6386 := _1272
                /// @src 38:1430:1443  "res0.toInt128"
                let expr_6387_self := expr_6386
                /// @src 38:1430:1445  "res0.toInt128()"
                let expr_6388 := fun_toInt128_5693(expr_6387_self)
                /// @src 38:1447:1451  "res1"
                let _1273 := var_res1_6382
                let expr_6389 := _1273
                /// @src 38:1447:1460  "res1.toInt128"
                let expr_6390_self := expr_6389
                /// @src 38:1447:1462  "res1.toInt128()"
                let expr_6391 := fun_toInt128_5693(expr_6390_self)
                /// @src 38:1415:1463  "toBalanceDelta(res0.toInt128(), res1.toInt128())"
                let expr_6392 := fun_toBalanceDelta_6337(expr_6388, expr_6391)
                /// @src 38:1408:1463  "return toBalanceDelta(res0.toInt128(), res1.toInt128())"
                var__6376 := expr_6392
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_4295128739_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_4295128739_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_4295128739_by_1(value)))
            }

            /// @src 36:1819:1872  "uint160 internal constant MIN_SQRT_PRICE = 4295128739"
            function constant_MIN_SQRT_PRICE_5796() -> ret {
                /// @src 36:1862:1872  "4295128739"
                let expr_5795 := 0x01000276a3
                let _1276 := convert_t_rational_4295128739_by_1_to_t_uint160(expr_5795)

                ret := _1276
            }

            function wrapping_sub_t_uint160(x, y) -> diff {
                diff := cleanup_t_uint160(sub(x, y))
            }

            function cleanup_t_rational_1461446703485210103287273052203988822374428841602_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1461446703485210103287273052203988822374428841602_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_1461446703485210103287273052203988822374428841602_by_1(value)))
            }

            /// @src 36:2200:2348  "uint160 internal constant MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE =..."
            function constant_MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE_5808() -> ret {
                /// @src 36:2282:2348  "1461446703485210103287273052203988822378723970342 - 4295128739 - 1"
                let expr_5807 := 0xfffd8963efd1fc6a506488495d951d5163961682
                let _1277 := convert_t_rational_1461446703485210103287273052203988822374428841602_by_1_to_t_uint160(expr_5807)

                ret := _1277
            }

            function convert_t_rational_32_by_1_to_t_uint8(value) -> converted {
                converted := cleanup_t_uint8(identity(cleanup_t_rational_32_by_1(value)))
            }

            function shift_left_t_uint256_t_uint8(value, bits) -> result {
                bits := cleanup_t_uint8(bits)
                result := cleanup_t_uint256(shift_left_dynamic(bits, cleanup_t_uint256(value)))
            }

            function convert_t_uint8_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint8(value)))
            }

            function cleanup_t_rational_127_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_127_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_127_by_1(value)))
            }

            function shift_left_t_uint256_t_uint256(value, bits) -> result {
                bits := cleanup_t_uint256(bits)
                result := cleanup_t_uint256(shift_left_dynamic(bits, cleanup_t_uint256(value)))
            }

            function shift_right_t_uint256_t_uint256(value, bits) -> result {
                bits := cleanup_t_uint256(bits)
                result := cleanup_t_uint256(shift_right_unsigned_dynamic(bits, cleanup_t_uint256(value)))
            }

            function convert_t_rational_128_by_1_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_rational_128_by_1(value)))
            }

            function wrapping_sub_t_int256(x, y) -> diff {
                diff := cleanup_t_int256(sub(x, y))
            }

            function convert_t_rational_64_by_1_to_t_uint8(value) -> converted {
                converted := cleanup_t_uint8(identity(cleanup_t_rational_64_by_1(value)))
            }

            function shift_left_t_int256_t_uint8(value, bits) -> result {
                bits := cleanup_t_uint8(bits)
                result := cleanup_t_int256(shift_left_dynamic(bits, cleanup_t_int256(value)))
            }

            function cleanup_t_rational_255738958999603826347141_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_255738958999603826347141_by_1_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_rational_255738958999603826347141_by_1(value)))
            }

            function wrapping_mul_t_int256(x, y) -> product {
                product := cleanup_t_int256(mul(x, y))
            }

            function cleanup_t_rational_3402992956809132418596140100660247210_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_3402992956809132418596140100660247210_by_1_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_rational_3402992956809132418596140100660247210_by_1(value)))
            }

            function shift_right_signed_dynamic(bits, value) -> result {

                result := sar(bits, value)

            }

            function shift_right_t_int256_t_uint8(value, bits) -> result {
                bits := cleanup_t_uint8(bits)
                result := cleanup_t_int256(shift_right_signed_dynamic(bits, cleanup_t_int256(value)))
            }

            function convert_t_int256_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_int256(value)))
            }

            function cleanup_t_rational_291339464771989622907027621153398088495_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_291339464771989622907027621153398088495_by_1_to_t_int256(value) -> converted {
                converted := cleanup_t_int256(identity(cleanup_t_rational_291339464771989622907027621153398088495_by_1(value)))
            }

            function wrapping_add_t_int256(x, y) -> sum {
                sum := cleanup_t_int256(add(x, y))
            }

            /// @ast-id 6304
            /// @src 36:7627:12379  "function getTickAtSqrtPrice(uint160 sqrtPriceX96) internal pure returns (int24 tick) {..."
            function fun_getTickAtSqrtPrice_6304(var_sqrtPriceX96_6167) -> var_tick_6170 {
                /// @src 36:7700:7710  "int24 tick"
                let zero_t_int24_1274 := zero_value_for_split_t_int24()
                var_tick_6170 := zero_t_int24_1274

                /// @src 36:8183:8195  "sqrtPriceX96"
                let _1275 := var_sqrtPriceX96_6167
                let expr_6172 := _1275
                /// @src 36:8198:8212  "MIN_SQRT_PRICE"
                let expr_6173 := constant_MIN_SQRT_PRICE_5796()
                /// @src 36:8183:8212  "sqrtPriceX96 - MIN_SQRT_PRICE"
                let expr_6174 := wrapping_sub_t_uint160(expr_6172, expr_6173)

                /// @src 36:8182:8213  "(sqrtPriceX96 - MIN_SQRT_PRICE)"
                let expr_6175 := expr_6174
                /// @src 36:8216:8261  "MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE"
                let expr_6176 := constant_MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE_5808()
                /// @src 36:8182:8261  "(sqrtPriceX96 - MIN_SQRT_PRICE) > MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE"
                let expr_6177 := gt(cleanup_t_uint160(expr_6175), cleanup_t_uint160(expr_6176))
                /// @src 36:8178:8346  "if ((sqrtPriceX96 - MIN_SQRT_PRICE) > MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE) {..."
                if expr_6177 {
                    /// @src 36:8281:8306  "InvalidSqrtPrice.selector"
                    let expr_6181 := 0x6148752400000000000000000000000000000000000000000000000000000000
                    /// @src 36:8281:8317  "InvalidSqrtPrice.selector.revertWith"
                    let expr_6182_self := expr_6181
                    /// @src 36:8318:8330  "sqrtPriceX96"
                    let _1278 := var_sqrtPriceX96_6167
                    let expr_6183 := _1278
                    fun_revertWith_2304(expr_6182_self, expr_6183)
                    /// @src 36:8178:8346  "if ((sqrtPriceX96 - MIN_SQRT_PRICE) > MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE) {..."
                }
                /// @src 36:8384:8396  "sqrtPriceX96"
                let _1279 := var_sqrtPriceX96_6167
                let expr_6192 := _1279
                /// @src 36:8376:8397  "uint256(sqrtPriceX96)"
                let expr_6193 := convert_t_uint160_to_t_uint256(expr_6192)
                /// @src 36:8401:8403  "32"
                let expr_6194 := 0x20
                /// @src 36:8376:8403  "uint256(sqrtPriceX96) << 32"
                let _1280 := convert_t_rational_32_by_1_to_t_uint8(expr_6194)
                let expr_6195 :=
                shift_left_t_uint256_t_uint8(expr_6193, _1280)

                /// @src 36:8360:8403  "uint256 price = uint256(sqrtPriceX96) << 32"
                let var_price_6189 := expr_6195
                /// @src 36:8430:8435  "price"
                let _1281 := var_price_6189
                let expr_6199 := _1281
                /// @src 36:8418:8435  "uint256 r = price"
                let var_r_6198 := expr_6199
                /// @src 36:8463:8470  "BitMath"
                let expr_6203_address := linkersymbol("src/libraries/BitMath.sol:BitMath")
                /// @src 36:8490:8491  "r"
                let _1282 := var_r_6198
                let expr_6205 := _1282
                /// @src 36:8463:8492  "BitMath.mostSignificantBit(r)"
                let expr_6206 := fun_mostSignificantBit_8932(expr_6205)
                /// @src 36:8449:8492  "uint256 msb = BitMath.mostSignificantBit(r)"
                let var_msb_6202 := convert_t_uint8_to_t_uint256(expr_6206)
                /// @src 36:8511:8514  "msb"
                let _1283 := var_msb_6202
                let expr_6208 := _1283
                /// @src 36:8518:8521  "128"
                let expr_6209 := 0x80
                /// @src 36:8511:8521  "msb >= 128"
                let expr_6210 := iszero(lt(cleanup_t_uint256(expr_6208), convert_t_rational_128_by_1_to_t_uint256(expr_6209)))
                /// @src 36:8507:8590  "if (msb >= 128) r = price >> (msb - 127);..."
                switch expr_6210
                case 0 {
                    /// @src 36:8570:8575  "price"
                    let _1284 := var_price_6189
                    let expr_6221 := _1284
                    /// @src 36:8580:8583  "127"
                    let expr_6222 := 0x7f
                    /// @src 36:8586:8589  "msb"
                    let _1285 := var_msb_6202
                    let expr_6223 := _1285
                    /// @src 36:8580:8589  "127 - msb"
                    let expr_6224 := wrapping_sub_t_uint256(convert_t_rational_127_by_1_to_t_uint256(expr_6222), expr_6223)

                    /// @src 36:8579:8590  "(127 - msb)"
                    let expr_6225 := expr_6224
                    /// @src 36:8570:8590  "price << (127 - msb)"
                    let expr_6226 :=
                    shift_left_t_uint256_t_uint256(expr_6221, expr_6225)

                    /// @src 36:8566:8590  "r = price << (127 - msb)"
                    var_r_6198 := expr_6226
                    let expr_6227 := expr_6226
                    /// @src 36:8507:8590  "if (msb >= 128) r = price >> (msb - 127);..."
                }
                default {
                    /// @src 36:8527:8532  "price"
                    let _1286 := var_price_6189
                    let expr_6212 := _1286
                    /// @src 36:8537:8540  "msb"
                    let _1287 := var_msb_6202
                    let expr_6213 := _1287
                    /// @src 36:8543:8546  "127"
                    let expr_6214 := 0x7f
                    /// @src 36:8537:8546  "msb - 127"
                    let expr_6215 := wrapping_sub_t_uint256(expr_6213, convert_t_rational_127_by_1_to_t_uint256(expr_6214))

                    /// @src 36:8536:8547  "(msb - 127)"
                    let expr_6216 := expr_6215
                    /// @src 36:8527:8547  "price >> (msb - 127)"
                    let expr_6217 :=
                    shift_right_t_uint256_t_uint256(expr_6212, expr_6216)

                    /// @src 36:8523:8547  "r = price >> (msb - 127)"
                    var_r_6198 := expr_6217
                    let expr_6218 := expr_6217
                    /// @src 36:8507:8590  "if (msb >= 128) r = price >> (msb - 127);..."
                }
                /// @src 36:8628:8631  "msb"
                let _1288 := var_msb_6202
                let expr_6234 := _1288
                /// @src 36:8621:8632  "int256(msb)"
                let expr_6235 := convert_t_uint256_to_t_int256(expr_6234)
                /// @src 36:8635:8638  "128"
                let expr_6236 := 0x80
                /// @src 36:8621:8638  "int256(msb) - 128"
                let expr_6237 := wrapping_sub_t_int256(expr_6235, convert_t_rational_128_by_1_to_t_int256(expr_6236))

                /// @src 36:8620:8639  "(int256(msb) - 128)"
                let expr_6238 := expr_6237
                /// @src 36:8643:8645  "64"
                let expr_6239 := 0x40
                /// @src 36:8620:8645  "(int256(msb) - 128) << 64"
                let _1289 := convert_t_rational_64_by_1_to_t_uint8(expr_6239)
                let expr_6240 :=
                shift_left_t_int256_t_uint8(expr_6238, _1289)

                /// @src 36:8605:8645  "int256 log_2 = (int256(msb) - 128) << 64"
                let var_log_2_6231 := expr_6240
                /// @src 36:8660:8856  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(63, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:8869:9065  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(62, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:9078:9274  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(61, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:9287:9483  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(60, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:9496:9692  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(59, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:9705:9901  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(58, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:9914:10110  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(57, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:10123:10319  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(56, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:10332:10528  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(55, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:10541:10737  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(54, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:10750:10946  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(53, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:10959:11155  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(52, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:11168:11364  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(51, usr$f))
                    var_r_6198 := shr(usr$f, var_r_6198)
                }
                /// @src 36:11377:11542  "assembly (\"memory-safe\") {..."
                {
                    var_r_6198 := shr(127, mul(var_r_6198, var_r_6198))
                    let usr$f := shr(128, var_r_6198)
                    var_log_2_6231 := or(var_log_2_6231, shl(50, usr$f))
                }
                /// @src 36:11579:11584  "log_2"
                let _1290 := var_log_2_6231
                let expr_6258 := _1290
                /// @src 36:11587:11611  "255738958999603826347141"
                let expr_6259 := 0x3627a301d71055774c85
                /// @src 36:11579:11611  "log_2 * 255738958999603826347141"
                let expr_6260 := wrapping_mul_t_int256(expr_6258, convert_t_rational_255738958999603826347141_by_1_to_t_int256(expr_6259))

                /// @src 36:11556:11611  "int256 log_sqrt10001 = log_2 * 255738958999603826347141"
                let var_log_sqrt10001_6257 := expr_6260
                /// @src 36:11788:11801  "log_sqrt10001"
                let _1291 := var_log_sqrt10001_6257
                let expr_6266 := _1291
                /// @src 36:11804:11841  "3402992956809132418596140100660247210"
                let expr_6267 := 0x028f6481ab7f045a5af012a19d003aaa
                /// @src 36:11788:11841  "log_sqrt10001 - 3402992956809132418596140100660247210"
                let expr_6268 := wrapping_sub_t_int256(expr_6266, convert_t_rational_3402992956809132418596140100660247210_by_1_to_t_int256(expr_6267))

                /// @src 36:11787:11842  "(log_sqrt10001 - 3402992956809132418596140100660247210)"
                let expr_6269 := expr_6268
                /// @src 36:11846:11849  "128"
                let expr_6270 := 0x80
                /// @src 36:11787:11849  "(log_sqrt10001 - 3402992956809132418596140100660247210) >> 128"
                let _1292 := convert_t_rational_128_by_1_to_t_uint8(expr_6270)
                let expr_6271 :=
                shift_right_t_int256_t_uint8(expr_6269, _1292)

                /// @src 36:11781:11850  "int24((log_sqrt10001 - 3402992956809132418596140100660247210) >> 128)"
                let expr_6272 := convert_t_int256_to_t_int24(expr_6271)
                /// @src 36:11765:11850  "int24 tickLow = int24((log_sqrt10001 - 3402992956809132418596140100660247210) >> 128)"
                let var_tickLow_6263 := expr_6272
                /// @src 36:12185:12198  "log_sqrt10001"
                let _1293 := var_log_sqrt10001_6257
                let expr_6278 := _1293
                /// @src 36:12201:12240  "291339464771989622907027621153398088495"
                let expr_6279 := 0xdb2df09e81959a81455e260799a0632f
                /// @src 36:12185:12240  "log_sqrt10001 + 291339464771989622907027621153398088495"
                let expr_6280 := wrapping_add_t_int256(expr_6278, convert_t_rational_291339464771989622907027621153398088495_by_1_to_t_int256(expr_6279))

                /// @src 36:12184:12241  "(log_sqrt10001 + 291339464771989622907027621153398088495)"
                let expr_6281 := expr_6280
                /// @src 36:12245:12248  "128"
                let expr_6282 := 0x80
                /// @src 36:12184:12248  "(log_sqrt10001 + 291339464771989622907027621153398088495) >> 128"
                let _1294 := convert_t_rational_128_by_1_to_t_uint8(expr_6282)
                let expr_6283 :=
                shift_right_t_int256_t_uint8(expr_6281, _1294)

                /// @src 36:12178:12249  "int24((log_sqrt10001 + 291339464771989622907027621153398088495) >> 128)"
                let expr_6284 := convert_t_int256_to_t_int24(expr_6283)
                /// @src 36:12163:12249  "int24 tickHi = int24((log_sqrt10001 + 291339464771989622907027621153398088495) >> 128)"
                let var_tickHi_6275 := expr_6284
                /// @src 36:12271:12278  "tickLow"
                let _1295 := var_tickLow_6263
                let expr_6287 := _1295
                /// @src 36:12282:12288  "tickHi"
                let _1296 := var_tickHi_6275
                let expr_6288 := _1296
                /// @src 36:12271:12288  "tickLow == tickHi"
                let expr_6289 := eq(cleanup_t_int24(expr_6287), cleanup_t_int24(expr_6288))
                /// @src 36:12271:12362  "tickLow == tickHi ? tickLow : getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                let expr_6299
                switch expr_6289
                case 0 {
                    /// @src 36:12320:12326  "tickHi"
                    let _1297 := var_tickHi_6275
                    let expr_6292 := _1297
                    /// @src 36:12301:12327  "getSqrtPriceAtTick(tickHi)"
                    let expr_6293 := fun_getSqrtPriceAtTick_6164(expr_6292)
                    /// @src 36:12331:12343  "sqrtPriceX96"
                    let _1298 := var_sqrtPriceX96_6167
                    let expr_6294 := _1298
                    /// @src 36:12301:12343  "getSqrtPriceAtTick(tickHi) <= sqrtPriceX96"
                    let expr_6295 := iszero(gt(cleanup_t_uint160(expr_6293), cleanup_t_uint160(expr_6294)))
                    /// @src 36:12301:12362  "getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                    let expr_6298
                    switch expr_6295
                    case 0 {
                        /// @src 36:12355:12362  "tickLow"
                        let _1299 := var_tickLow_6263
                        let expr_6297 := _1299
                        /// @src 36:12301:12362  "getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                        expr_6298 := expr_6297
                    }
                    default {
                        /// @src 36:12346:12352  "tickHi"
                        let _1300 := var_tickHi_6275
                        let expr_6296 := _1300
                        /// @src 36:12301:12362  "getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                        expr_6298 := expr_6296
                    }
                    /// @src 36:12271:12362  "tickLow == tickHi ? tickLow : getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                    expr_6299 := expr_6298
                }
                default {
                    /// @src 36:12291:12298  "tickLow"
                    let _1301 := var_tickLow_6263
                    let expr_6290 := _1301
                    /// @src 36:12271:12362  "tickLow == tickHi ? tickLow : getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                    expr_6299 := expr_6290
                }
                /// @src 36:12264:12362  "tick = tickLow == tickHi ? tickLow : getSqrtPriceAtTick(tickHi) <= sqrtPriceX96 ? tickHi : tickLow"
                var_tick_6170 := expr_6299
                let expr_6300 := expr_6299

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8705
            /// @src 44:2231:2479  "function setSqrtPriceX96(Slot0 _packed, uint160 _sqrtPriceX96) internal pure returns (Slot0 _result) {..."
            function fun_setSqrtPriceX96_8705(var__packed_8695, var__sqrtPriceX96_8697) -> var__result_8701 {
                /// @src 44:2317:2330  "Slot0 _result"
                let zero_t_userDefinedValueType$_Slot0_$8632_1302 := zero_value_for_split_t_userDefinedValueType$_Slot0_$8632()
                var__result_8701 := zero_t_userDefinedValueType$_Slot0_$8632_1302

                /// @src 44:2342:2473  "assembly (\"memory-safe\") {..."
                {
                    var__result_8701 := or(and(not(1461501637330902918203684832716283019655932542975), var__packed_8695), and(1461501637330902918203684832716283019655932542975, var__sqrtPriceX96_8697))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8718
            /// @src 44:2485:2741  "function setTick(Slot0 _packed, int24 _tick) internal pure returns (Slot0 _result) {..."
            function fun_setTick_8718(var__packed_8708, var__tick_8710) -> var__result_8714 {
                /// @src 44:2553:2566  "Slot0 _result"
                let zero_t_userDefinedValueType$_Slot0_$8632_1303 := zero_value_for_split_t_userDefinedValueType$_Slot0_$8632()
                var__result_8714 := zero_t_userDefinedValueType$_Slot0_$8632_1303

                /// @src 44:2578:2735  "assembly (\"memory-safe\") {..."
                {
                    var__result_8714 := or(and(not(shl(160, 16777215)), var__packed_8708), shl(160, and(16777215, var__tick_8710)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8731
            /// @src 44:2747:3115  "function setProtocolFee(Slot0 _packed, uint24 _protocolFee) internal pure returns (Slot0 _result) {..."
            function fun_setProtocolFee_8731(var__packed_8721, var__protocolFee_8723) -> var__result_8727 {
                /// @src 44:2830:2843  "Slot0 _result"
                let zero_t_userDefinedValueType$_Slot0_$8632_1304 := zero_value_for_split_t_userDefinedValueType$_Slot0_$8632()
                var__result_8727 := zero_t_userDefinedValueType$_Slot0_$8632_1304

                /// @src 44:2855:3109  "assembly (\"memory-safe\") {..."
                {
                    var__result_8727 := or(and(not(shl(184, 16777215)), var__packed_8721), shl(184, and(16777215, var__protocolFee_8723)))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2153
            /// @src 17:439:791  "function _computeSlot(address target, Currency currency) internal pure returns (bytes32 hashSlot) {..."
            function fun__computeSlot_2153(var_target_2143, var_currency_2146) -> var_hashSlot_2149 {
                /// @src 17:519:535  "bytes32 hashSlot"
                let zero_t_bytes32_1305 := zero_value_for_split_t_bytes32()
                var_hashSlot_2149 := zero_t_bytes32_1305

                /// @src 17:547:785  "assembly (\"memory-safe\") {..."
                {
                    mstore(0, and(var_target_2143, 0xffffffffffffffffffffffffffffffffffffffff))
                    mstore(32, and(var_currency_2146, 0xffffffffffffffffffffffffffffffffffffffff))
                    var_hashSlot_2149 := keccak256(0, 64)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7590
            /// @src 28:660:916  "function parseFee(bytes memory result) internal pure returns (uint24 lpFee) {..."
            function fun_parseFee_7590(var_result_7583_mpos) -> var_lpFee_7586 {
                /// @src 28:722:734  "uint24 lpFee"
                let zero_t_uint24_1306 := zero_value_for_split_t_uint24()
                var_lpFee_7586 := zero_t_uint24_1306

                /// @src 28:828:910  "assembly (\"memory-safe\") {..."
                {
                    var_lpFee_7586 := mload(add(var_result_7583_mpos, 0x60))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7599
            /// @src 28:922:1197  "function parseReturnDelta(bytes memory result) internal pure returns (int256 hookReturn) {..."
            function fun_parseReturnDelta_7599(var_result_7592_mpos) -> var_hookReturn_7595 {
                /// @src 28:992:1009  "int256 hookReturn"
                let zero_t_int256_1307 := zero_value_for_split_t_int256()
                var_hookReturn_7595 := zero_t_int256_1307

                /// @src 28:1104:1191  "assembly (\"memory-safe\") {..."
                {
                    var_hookReturn_7595 := mload(add(var_result_7592_mpos, 0x40))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6505
            /// @src 39:941:1135  "function getSpecifiedDelta(BeforeSwapDelta delta) internal pure returns (int128 deltaSpecified) {..."
            function fun_getSpecifiedDelta_6505(var_delta_6498) -> var_deltaSpecified_6501 {
                /// @src 39:1014:1035  "int128 deltaSpecified"
                let zero_t_int128_1308 := zero_value_for_split_t_int128()
                var_deltaSpecified_6501 := zero_t_int128_1308

                /// @src 39:1047:1129  "assembly (\"memory-safe\") {..."
                {
                    var_deltaSpecified_6501 := sar(128, var_delta_6498)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function allocate_memory_struct_t_struct$_SwapResult_$4378_memory_ptr() -> memPtr {
                memPtr := allocate_memory(96)
            }

            function zero_value_for_t_uint160() -> ret {
                ret := 0
            }

            function zero_value_for_t_int24() -> ret {
                ret := 0
            }

            function allocate_and_zero_memory_struct_t_struct$_SwapResult_$4378_memory_ptr() -> memPtr {
                memPtr := allocate_memory_struct_t_struct$_SwapResult_$4378_memory_ptr()
                let offset := memPtr

                mstore(offset, zero_value_for_t_uint160())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_int24())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint128())
                offset := add(offset, 32)

            }

            function zero_value_for_split_t_struct$_SwapResult_$4378_memory_ptr() -> ret {
                ret := allocate_and_zero_memory_struct_t_struct$_SwapResult_$4378_memory_ptr()
            }

            function cleanup_t_uint16(value) -> cleaned {
                cleaned := and(value, 0xffff)
            }

            function convert_t_uint16_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint16(value)))
            }

            function convert_t_uint256_to_t_uint16(value) -> converted {
                converted := cleanup_t_uint16(identity(cleanup_t_uint256(value)))
            }

            function convert_t_rational_1000000_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_1000000_by_1(value)))
            }

            /// @src 34:522:566  "uint256 internal constant MAX_SWAP_FEE = 1e6"
            function constant_MAX_SWAP_FEE_8125() -> ret {
                /// @src 34:563:566  "1e6"
                let expr_8124 := 0x0f4240
                let _1351 := convert_t_rational_1000000_by_1_to_t_uint256(expr_8124)

                ret := _1351
            }

            function convert_t_uint24_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_uint24(value)))
            }

            function cleanup_t_rational_1461446703485210103287273052203988822378723970342_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_1461446703485210103287273052203988822378723970342_by_1_to_t_uint160(value) -> converted {
                converted := cleanup_t_uint160(identity(cleanup_t_rational_1461446703485210103287273052203988822378723970342_by_1(value)))
            }

            /// @src 36:1999:2091  "uint160 internal constant MAX_SQRT_PRICE = 1461446703485210103287273052203988822378723970342"
            function constant_MAX_SQRT_PRICE_5800() -> ret {
                /// @src 36:2042:2091  "1461446703485210103287273052203988822378723970342"
                let expr_5799 := 0xfffd8963efd1fc6a506488495d951d5263988d26
                let _1372 := convert_t_rational_1461446703485210103287273052203988822378723970342_by_1_to_t_uint160(expr_5799)

                ret := _1372
            }

            function allocate_memory_struct_t_struct$_StepComputations_$4395_memory_ptr() -> memPtr {
                memPtr := allocate_memory(256)
            }

            function zero_value_for_t_uint256() -> ret {
                ret := 0
            }

            function allocate_and_zero_memory_struct_t_struct$_StepComputations_$4395_memory_ptr() -> memPtr {
                memPtr := allocate_memory_struct_t_struct$_StepComputations_$4395_memory_ptr()
                let offset := memPtr

                mstore(offset, zero_value_for_t_uint160())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_int24())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_bool())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint160())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint256())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint256())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint256())
                offset := add(offset, 32)

                mstore(offset, zero_value_for_t_uint256())
                offset := add(offset, 32)

            }

            function zero_value_for_split_t_struct$_StepComputations_$4395_memory_ptr() -> ret {
                ret := allocate_and_zero_memory_struct_t_struct$_StepComputations_$4395_memory_ptr()
            }

            function write_to_memory_t_uint256(memPtr, value) {
                mstore(memPtr, cleanup_t_uint256(value))
            }

            function read_from_memoryt_uint256(ptr) -> returnValue {

                let value := cleanup_t_uint256(mload(ptr))

                returnValue :=

                value

            }

            function checked_sub_t_int256(x, y) -> diff {
                x := cleanup_t_int256(x)
                y := cleanup_t_int256(y)
                diff := sub(x, y)

                // underflow, if y >= 0 and diff > x
                // overflow, if y < 0 and diff < x
                if or(
                    and(iszero(slt(y, 0)), sgt(diff, x)),
                    and(slt(y, 0), slt(diff, x))
                ) { panic_error_0x11() }

            }

            /// @src 31:588:642  "uint256 internal constant PIPS_DENOMINATOR = 1_000_000"
            function constant_PIPS_DENOMINATOR_7403() -> ret {
                /// @src 31:633:642  "1_000_000"
                let expr_7402 := 0x0f4240
                let _1510 := convert_t_rational_1000000_by_1_to_t_uint256(expr_7402)

                ret := _1510
            }

            function panic_error_0x12() {
                mstore(0, 35408467139433450592217433187231851964531694900788300625387963629091585785856)
                mstore(4, 0x12)
                revert(0, 0x24)
            }

            function wrapping_div_t_uint256(x, y) -> r {
                x := cleanup_t_uint256(x)
                y := cleanup_t_uint256(y)
                if iszero(y) { panic_error_0x12() }
                r := div(x, y)
            }

            function wrapping_sub_t_int24(x, y) -> diff {
                diff := cleanup_t_int24(sub(x, y))
            }

            /// @ast-id 5021
            /// @src 29:12231:21851  "function swap(State storage self, SwapParams memory params)..."
            function fun_swap_5021(var_self_4410_slot, var_params_4413_mpos) -> var_swapDelta_4417, var_amountToProtocol_4419, var_swapFee_4421, var_result_4424_mpos {
                /// @src 29:12325:12347  "BalanceDelta swapDelta"
                let zero_t_userDefinedValueType$_BalanceDelta_$6311_1309 := zero_value_for_split_t_userDefinedValueType$_BalanceDelta_$6311()
                var_swapDelta_4417 := zero_t_userDefinedValueType$_BalanceDelta_$6311_1309
                /// @src 29:12349:12373  "uint256 amountToProtocol"
                let zero_t_uint256_1310 := zero_value_for_split_t_uint256()
                var_amountToProtocol_4419 := zero_t_uint256_1310
                /// @src 29:12375:12389  "uint24 swapFee"
                let zero_t_uint24_1311 := zero_value_for_split_t_uint24()
                var_swapFee_4421 := zero_t_uint24_1311
                /// @src 29:12391:12415  "SwapResult memory result"
                let zero_t_struct$_SwapResult_$4378_memory_ptr_1312_mpos := zero_value_for_split_t_struct$_SwapResult_$4378_memory_ptr()
                var_result_4424_mpos := zero_t_struct$_SwapResult_$4378_memory_ptr_1312_mpos

                /// @src 29:12450:12454  "self"
                let _1313_slot := var_self_4410_slot
                let expr_4429_slot := _1313_slot
                /// @src 29:12450:12460  "self.slot0"
                let _1314 := add(expr_4429_slot, 0)
                let _1315 := read_from_storage_split_offset_0_t_userDefinedValueType$_Slot0_$8632(_1314)
                let expr_4430 := _1315
                /// @src 29:12431:12460  "Slot0 slot0Start = self.slot0"
                let var_slot0Start_4428 := expr_4430
                /// @src 29:12488:12494  "params"
                let _1316_mpos := var_params_4413_mpos
                let expr_4434_mpos := _1316_mpos
                /// @src 29:12488:12505  "params.zeroForOne"
                let _1317 := add(expr_4434_mpos, 64)
                let _1318 := read_from_memoryt_bool(_1317)
                let expr_4435 := _1318
                /// @src 29:12470:12505  "bool zeroForOne = params.zeroForOne"
                let var_zeroForOne_4433 := expr_4435
                /// @src 29:12550:12560  "zeroForOne"
                let _1319 := var_zeroForOne_4433
                let expr_4439 := _1319
                /// @src 29:12550:12652  "zeroForOne ? slot0Start.protocolFee().getZeroForOneFee() : slot0Start.protocolFee().getOneForZeroFee()"
                let expr_4450
                switch expr_4439
                case 0 {
                    /// @src 29:12609:12619  "slot0Start"
                    let _1320 := var_slot0Start_4428
                    let expr_4445 := _1320
                    /// @src 29:12609:12631  "slot0Start.protocolFee"
                    let expr_4446_self := expr_4445
                    /// @src 29:12609:12633  "slot0Start.protocolFee()"
                    let expr_4447 := fun_protocolFee_8682(expr_4446_self)
                    /// @src 29:12609:12650  "slot0Start.protocolFee().getOneForZeroFee"
                    let expr_4448_self := expr_4447
                    /// @src 29:12609:12652  "slot0Start.protocolFee().getOneForZeroFee()"
                    let expr_4449 := fun_getOneForZeroFee_7433(expr_4448_self)
                    /// @src 29:12550:12652  "zeroForOne ? slot0Start.protocolFee().getZeroForOneFee() : slot0Start.protocolFee().getOneForZeroFee()"
                    expr_4450 := expr_4449
                }
                default {
                    /// @src 29:12563:12573  "slot0Start"
                    let _1321 := var_slot0Start_4428
                    let expr_4440 := _1321
                    /// @src 29:12563:12585  "slot0Start.protocolFee"
                    let expr_4441_self := expr_4440
                    /// @src 29:12563:12587  "slot0Start.protocolFee()"
                    let expr_4442 := fun_protocolFee_8682(expr_4441_self)
                    /// @src 29:12563:12604  "slot0Start.protocolFee().getZeroForOneFee"
                    let expr_4443_self := expr_4442
                    /// @src 29:12563:12606  "slot0Start.protocolFee().getZeroForOneFee()"
                    let expr_4444 := fun_getZeroForOneFee_7418(expr_4443_self)
                    /// @src 29:12550:12652  "zeroForOne ? slot0Start.protocolFee().getZeroForOneFee() : slot0Start.protocolFee().getOneForZeroFee()"
                    expr_4450 := expr_4444
                }
                /// @src 29:12516:12652  "uint256 protocolFee =..."
                let var_protocolFee_4438 := convert_t_uint16_to_t_uint256(expr_4450)
                /// @src 29:12814:12820  "params"
                let _1322_mpos := var_params_4413_mpos
                let expr_4454_mpos := _1322_mpos
                /// @src 29:12814:12836  "params.amountSpecified"
                let _1323 := add(expr_4454_mpos, 0)
                let _1324 := read_from_memoryt_int256(_1323)
                let expr_4455 := _1324
                /// @src 29:12780:12836  "int256 amountSpecifiedRemaining = params.amountSpecified"
                let var_amountSpecifiedRemaining_4453 := expr_4455
                /// @src 29:12955:12956  "0"
                let expr_4459 := 0x00
                /// @src 29:12929:12956  "int256 amountCalculated = 0"
                let var_amountCalculated_4458 := convert_t_rational_0_by_1_to_t_int256(expr_4459)
                /// @src 29:13037:13047  "slot0Start"
                let _1325 := var_slot0Start_4428
                let expr_4464 := _1325
                /// @src 29:13037:13060  "slot0Start.sqrtPriceX96"
                let expr_4465_self := expr_4464
                /// @src 29:13037:13062  "slot0Start.sqrtPriceX96()"
                let expr_4466 := fun_sqrtPriceX96_8662(expr_4465_self)
                /// @src 29:13015:13021  "result"
                let _1326_mpos := var_result_4424_mpos
                let expr_4461_mpos := _1326_mpos
                /// @src 29:13015:13034  "result.sqrtPriceX96"
                let _1327 := add(expr_4461_mpos, 0)
                /// @src 29:13015:13062  "result.sqrtPriceX96 = slot0Start.sqrtPriceX96()"
                let _1328 := expr_4466
                write_to_memory_t_uint160(_1327, _1328)
                let expr_4467 := expr_4466
                /// @src 29:13128:13138  "slot0Start"
                let _1329 := var_slot0Start_4428
                let expr_4472 := _1329
                /// @src 29:13128:13143  "slot0Start.tick"
                let expr_4473_self := expr_4472
                /// @src 29:13128:13145  "slot0Start.tick()"
                let expr_4474 := fun_tick_8672(expr_4473_self)
                /// @src 29:13114:13120  "result"
                let _1330_mpos := var_result_4424_mpos
                let expr_4469_mpos := _1330_mpos
                /// @src 29:13114:13125  "result.tick"
                let _1331 := add(expr_4469_mpos, 32)
                /// @src 29:13114:13145  "result.tick = slot0Start.tick()"
                let _1332 := expr_4474
                write_to_memory_t_int24(_1331, _1332)
                let expr_4475 := expr_4474
                /// @src 29:13221:13225  "self"
                let _1333_slot := var_self_4410_slot
                let expr_4480_slot := _1333_slot
                /// @src 29:13221:13235  "self.liquidity"
                let _1334 := add(expr_4480_slot, 3)
                let _1335 := read_from_storage_split_offset_0_t_uint128(_1334)
                let expr_4481 := _1335
                /// @src 29:13202:13208  "result"
                let _1336_mpos := var_result_4424_mpos
                let expr_4477_mpos := _1336_mpos
                /// @src 29:13202:13218  "result.liquidity"
                let _1337 := add(expr_4477_mpos, 64)
                /// @src 29:13202:13235  "result.liquidity = self.liquidity"
                let _1338 := expr_4481
                write_to_memory_t_uint128(_1337, _1338)
                let expr_4482 := expr_4481
                /// @src 29:13451:13457  "params"
                let _1339_mpos := var_params_4413_mpos
                let expr_4486_mpos := _1339_mpos
                /// @src 29:13451:13471  "params.lpFeeOverride"
                let _1340 := add(expr_4486_mpos, 128)
                let _1341 := read_from_memoryt_uint24(_1340)
                let expr_4487 := _1341
                /// @src 29:13451:13482  "params.lpFeeOverride.isOverride"
                let expr_4488_self := expr_4487
                /// @src 29:13451:13484  "params.lpFeeOverride.isOverride()"
                let expr_4489 := fun_isOverride_3645(expr_4488_self)
                /// @src 29:13451:13592  "params.lpFeeOverride.isOverride()..."
                let expr_4497
                switch expr_4489
                case 0 {
                    /// @src 29:13574:13584  "slot0Start"
                    let _1342 := var_slot0Start_4428
                    let expr_4494 := _1342
                    /// @src 29:13574:13590  "slot0Start.lpFee"
                    let expr_4495_self := expr_4494
                    /// @src 29:13574:13592  "slot0Start.lpFee()"
                    let expr_4496 := fun_lpFee_8692(expr_4495_self)
                    /// @src 29:13451:13592  "params.lpFeeOverride.isOverride()..."
                    expr_4497 := expr_4496
                }
                default {
                    /// @src 29:13503:13509  "params"
                    let _1343_mpos := var_params_4413_mpos
                    let expr_4490_mpos := _1343_mpos
                    /// @src 29:13503:13523  "params.lpFeeOverride"
                    let _1344 := add(expr_4490_mpos, 128)
                    let _1345 := read_from_memoryt_uint24(_1344)
                    let expr_4491 := _1345
                    /// @src 29:13503:13553  "params.lpFeeOverride.removeOverrideFlagAndValidate"
                    let expr_4492_self := expr_4491
                    /// @src 29:13503:13555  "params.lpFeeOverride.removeOverrideFlagAndValidate()"
                    let expr_4493 := fun_removeOverrideFlagAndValidate_3678(expr_4492_self)
                    /// @src 29:13451:13592  "params.lpFeeOverride.isOverride()..."
                    expr_4497 := expr_4493
                }
                /// @src 29:13436:13592  "uint24 lpFee = params.lpFeeOverride.isOverride()..."
                let var_lpFee_4485 := expr_4497
                /// @src 29:13617:13628  "protocolFee"
                let _1346 := var_protocolFee_4438
                let expr_4500 := _1346
                /// @src 29:13632:13633  "0"
                let expr_4501 := 0x00
                /// @src 29:13617:13633  "protocolFee == 0"
                let expr_4502 := eq(cleanup_t_uint256(expr_4500), convert_t_rational_0_by_1_to_t_uint256(expr_4501))
                /// @src 29:13617:13687  "protocolFee == 0 ? lpFee : uint16(protocolFee).calculateSwapFee(lpFee)"
                let expr_4511
                switch expr_4502
                case 0 {
                    /// @src 29:13651:13662  "protocolFee"
                    let _1347 := var_protocolFee_4438
                    let expr_4506 := _1347
                    /// @src 29:13644:13663  "uint16(protocolFee)"
                    let expr_4507 := convert_t_uint256_to_t_uint16(expr_4506)
                    /// @src 29:13644:13680  "uint16(protocolFee).calculateSwapFee"
                    let expr_4508_self := expr_4507
                    /// @src 29:13681:13686  "lpFee"
                    let _1348 := var_lpFee_4485
                    let expr_4509 := _1348
                    /// @src 29:13644:13687  "uint16(protocolFee).calculateSwapFee(lpFee)"
                    let expr_4510 := fun_calculateSwapFee_7454(expr_4508_self, expr_4509)
                    /// @src 29:13617:13687  "protocolFee == 0 ? lpFee : uint16(protocolFee).calculateSwapFee(lpFee)"
                    expr_4511 := expr_4510
                }
                default {
                    /// @src 29:13636:13641  "lpFee"
                    let _1349 := var_lpFee_4485
                    let expr_4503 := _1349
                    /// @src 29:13617:13687  "protocolFee == 0 ? lpFee : uint16(protocolFee).calculateSwapFee(lpFee)"
                    expr_4511 := expr_4503
                }
                /// @src 29:13607:13687  "swapFee = protocolFee == 0 ? lpFee : uint16(protocolFee).calculateSwapFee(lpFee)"
                var_swapFee_4421 := expr_4511
                let expr_4512 := expr_4511
                /// @src 29:13847:13854  "swapFee"
                let _1350 := var_swapFee_4421
                let expr_4515 := _1350
                /// @src 29:13858:13866  "SwapMath"
                let expr_4516_address := linkersymbol("src/libraries/SwapMath.sol:SwapMath")
                /// @src 29:13858:13879  "SwapMath.MAX_SWAP_FEE"
                let expr_4517 := constant_MAX_SWAP_FEE_8125()
                /// @src 29:13847:13879  "swapFee >= SwapMath.MAX_SWAP_FEE"
                let expr_4518 := iszero(lt(convert_t_uint24_to_t_uint256(expr_4515), cleanup_t_uint256(expr_4517)))
                /// @src 29:13843:14043  "if (swapFee >= SwapMath.MAX_SWAP_FEE) {..."
                if expr_4518 {
                    /// @src 29:13929:13935  "params"
                    let _1352_mpos := var_params_4413_mpos
                    let expr_4519_mpos := _1352_mpos
                    /// @src 29:13929:13951  "params.amountSpecified"
                    let _1353 := add(expr_4519_mpos, 0)
                    let _1354 := read_from_memoryt_int256(_1353)
                    let expr_4520 := _1354
                    /// @src 29:13954:13955  "0"
                    let expr_4521 := 0x00
                    /// @src 29:13929:13955  "params.amountSpecified > 0"
                    let expr_4522 := sgt(cleanup_t_int256(expr_4520), convert_t_rational_0_by_1_to_t_int256(expr_4521))
                    /// @src 29:13925:14033  "if (params.amountSpecified > 0) {..."
                    if expr_4522 {
                        /// @src 29:13975:14005  "InvalidFeeForExactOut.selector"
                        let expr_4526 := 0x9620624600000000000000000000000000000000000000000000000000000000
                        /// @src 29:13975:14016  "InvalidFeeForExactOut.selector.revertWith"
                        let expr_4527_self := expr_4526
                        fun_revertWith_2274(expr_4527_self)
                        /// @src 29:13925:14033  "if (params.amountSpecified > 0) {..."
                    }
                    /// @src 29:13843:14043  "if (swapFee >= SwapMath.MAX_SWAP_FEE) {..."
                }
                /// @src 29:14251:14257  "params"
                let _1355_mpos := var_params_4413_mpos
                let expr_4534_mpos := _1355_mpos
                /// @src 29:14251:14273  "params.amountSpecified"
                let _1356 := add(expr_4534_mpos, 0)
                let _1357 := read_from_memoryt_int256(_1356)
                let expr_4535 := _1357
                /// @src 29:14277:14278  "0"
                let expr_4536 := 0x00
                /// @src 29:14251:14278  "params.amountSpecified == 0"
                let expr_4537 := eq(cleanup_t_int256(expr_4535), convert_t_rational_0_by_1_to_t_int256(expr_4536))
                /// @src 29:14247:14339  "if (params.amountSpecified == 0) return (BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                if expr_4537 {
                    /// @src 29:14288:14307  "BalanceDeltaLibrary"
                    let expr_4538_address := linkersymbol("src/types/BalanceDelta.sol:BalanceDeltaLibrary")
                    /// @src 29:14288:14318  "BalanceDeltaLibrary.ZERO_DELTA"
                    let expr_4539 := constant_ZERO_DELTA_6448()
                    /// @src 29:14287:14339  "(BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                    let expr_4543_component_1 := expr_4539
                    /// @src 29:14320:14321  "0"
                    let expr_4540 := 0x00
                    /// @src 29:14287:14339  "(BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                    let expr_4543_component_2 := expr_4540
                    /// @src 29:14323:14330  "swapFee"
                    let _1358 := var_swapFee_4421
                    let expr_4541 := _1358
                    /// @src 29:14287:14339  "(BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                    let expr_4543_component_3 := expr_4541
                    /// @src 29:14332:14338  "result"
                    let _1359_mpos := var_result_4424_mpos
                    let expr_4542_mpos := _1359_mpos
                    /// @src 29:14287:14339  "(BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                    let expr_4543_component_4_mpos := expr_4542_mpos
                    /// @src 29:14280:14339  "return (BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                    var_swapDelta_4417 := expr_4543_component_1
                    var_amountToProtocol_4419 := convert_t_rational_0_by_1_to_t_uint256(expr_4543_component_2)
                    var_swapFee_4421 := expr_4543_component_3
                    var_result_4424_mpos := expr_4543_component_4_mpos
                    leave
                    /// @src 29:14247:14339  "if (params.amountSpecified == 0) return (BalanceDeltaLibrary.ZERO_DELTA, 0, swapFee, result)"
                }
                /// @src 29:14354:14364  "zeroForOne"
                let _1360 := var_zeroForOne_4433
                let expr_4546 := _1360
                /// @src 29:14350:15371  "if (zeroForOne) {..."
                switch expr_4546
                case 0 {
                    /// @src 29:15005:15011  "params"
                    let _1361_mpos := var_params_4413_mpos
                    let expr_4584_mpos := _1361_mpos
                    /// @src 29:15005:15029  "params.sqrtPriceLimitX96"
                    let _1362 := add(expr_4584_mpos, 96)
                    let _1363 := read_from_memoryt_uint160(_1362)
                    let expr_4585 := _1363
                    /// @src 29:15033:15043  "slot0Start"
                    let _1364 := var_slot0Start_4428
                    let expr_4586 := _1364
                    /// @src 29:15033:15056  "slot0Start.sqrtPriceX96"
                    let expr_4587_self := expr_4586
                    /// @src 29:15033:15058  "slot0Start.sqrtPriceX96()"
                    let expr_4588 := fun_sqrtPriceX96_8662(expr_4587_self)
                    /// @src 29:15005:15058  "params.sqrtPriceLimitX96 <= slot0Start.sqrtPriceX96()"
                    let expr_4589 := iszero(gt(cleanup_t_uint160(expr_4585), cleanup_t_uint160(expr_4588)))
                    /// @src 29:15001:15191  "if (params.sqrtPriceLimitX96 <= slot0Start.sqrtPriceX96()) {..."
                    if expr_4589 {
                        /// @src 29:15078:15112  "PriceLimitAlreadyExceeded.selector"
                        let expr_4593 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
                        /// @src 29:15078:15123  "PriceLimitAlreadyExceeded.selector.revertWith"
                        let expr_4594_self := expr_4593
                        /// @src 29:15124:15134  "slot0Start"
                        let _1365 := var_slot0Start_4428
                        let expr_4595 := _1365
                        /// @src 29:15124:15147  "slot0Start.sqrtPriceX96"
                        let expr_4596_self := expr_4595
                        /// @src 29:15124:15149  "slot0Start.sqrtPriceX96()"
                        let expr_4597 := fun_sqrtPriceX96_8662(expr_4596_self)
                        /// @src 29:15151:15157  "params"
                        let _1366_mpos := var_params_4413_mpos
                        let expr_4598_mpos := _1366_mpos
                        /// @src 29:15151:15175  "params.sqrtPriceLimitX96"
                        let _1367 := add(expr_4598_mpos, 96)
                        let _1368 := read_from_memoryt_uint160(_1367)
                        let expr_4599 := _1368
                        fun_revertWith_2328(expr_4594_self, expr_4597, expr_4599)
                        /// @src 29:15001:15191  "if (params.sqrtPriceLimitX96 <= slot0Start.sqrtPriceX96()) {..."
                    }
                    /// @src 29:15208:15214  "params"
                    let _1369_mpos := var_params_4413_mpos
                    let expr_4604_mpos := _1369_mpos
                    /// @src 29:15208:15232  "params.sqrtPriceLimitX96"
                    let _1370 := add(expr_4604_mpos, 96)
                    let _1371 := read_from_memoryt_uint160(_1370)
                    let expr_4605 := _1371
                    /// @src 29:15236:15244  "TickMath"
                    let expr_4606_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                    /// @src 29:15236:15259  "TickMath.MAX_SQRT_PRICE"
                    let expr_4607 := constant_MAX_SQRT_PRICE_5800()
                    /// @src 29:15208:15259  "params.sqrtPriceLimitX96 >= TickMath.MAX_SQRT_PRICE"
                    let expr_4608 := iszero(lt(cleanup_t_uint160(expr_4605), cleanup_t_uint160(expr_4607)))
                    /// @src 29:15204:15361  "if (params.sqrtPriceLimitX96 >= TickMath.MAX_SQRT_PRICE) {..."
                    if expr_4608 {
                        /// @src 29:15279:15309  "PriceLimitOutOfBounds.selector"
                        let expr_4612 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
                        /// @src 29:15279:15320  "PriceLimitOutOfBounds.selector.revertWith"
                        let expr_4613_self := expr_4612
                        /// @src 29:15321:15327  "params"
                        let _1373_mpos := var_params_4413_mpos
                        let expr_4614_mpos := _1373_mpos
                        /// @src 29:15321:15345  "params.sqrtPriceLimitX96"
                        let _1374 := add(expr_4614_mpos, 96)
                        let _1375 := read_from_memoryt_uint160(_1374)
                        let expr_4615 := _1375
                        fun_revertWith_2304(expr_4613_self, expr_4615)
                        /// @src 29:15204:15361  "if (params.sqrtPriceLimitX96 >= TickMath.MAX_SQRT_PRICE) {..."
                    }
                    /// @src 29:14350:15371  "if (zeroForOne) {..."
                }
                default {
                    /// @src 29:14384:14390  "params"
                    let _1376_mpos := var_params_4413_mpos
                    let expr_4547_mpos := _1376_mpos
                    /// @src 29:14384:14408  "params.sqrtPriceLimitX96"
                    let _1377 := add(expr_4547_mpos, 96)
                    let _1378 := read_from_memoryt_uint160(_1377)
                    let expr_4548 := _1378
                    /// @src 29:14412:14422  "slot0Start"
                    let _1379 := var_slot0Start_4428
                    let expr_4549 := _1379
                    /// @src 29:14412:14435  "slot0Start.sqrtPriceX96"
                    let expr_4550_self := expr_4549
                    /// @src 29:14412:14437  "slot0Start.sqrtPriceX96()"
                    let expr_4551 := fun_sqrtPriceX96_8662(expr_4550_self)
                    /// @src 29:14384:14437  "params.sqrtPriceLimitX96 >= slot0Start.sqrtPriceX96()"
                    let expr_4552 := iszero(lt(cleanup_t_uint160(expr_4548), cleanup_t_uint160(expr_4551)))
                    /// @src 29:14380:14570  "if (params.sqrtPriceLimitX96 >= slot0Start.sqrtPriceX96()) {..."
                    if expr_4552 {
                        /// @src 29:14457:14491  "PriceLimitAlreadyExceeded.selector"
                        let expr_4556 := 0x7c9c6e8f00000000000000000000000000000000000000000000000000000000
                        /// @src 29:14457:14502  "PriceLimitAlreadyExceeded.selector.revertWith"
                        let expr_4557_self := expr_4556
                        /// @src 29:14503:14513  "slot0Start"
                        let _1380 := var_slot0Start_4428
                        let expr_4558 := _1380
                        /// @src 29:14503:14526  "slot0Start.sqrtPriceX96"
                        let expr_4559_self := expr_4558
                        /// @src 29:14503:14528  "slot0Start.sqrtPriceX96()"
                        let expr_4560 := fun_sqrtPriceX96_8662(expr_4559_self)
                        /// @src 29:14530:14536  "params"
                        let _1381_mpos := var_params_4413_mpos
                        let expr_4561_mpos := _1381_mpos
                        /// @src 29:14530:14554  "params.sqrtPriceLimitX96"
                        let _1382 := add(expr_4561_mpos, 96)
                        let _1383 := read_from_memoryt_uint160(_1382)
                        let expr_4562 := _1383
                        fun_revertWith_2328(expr_4557_self, expr_4560, expr_4562)
                        /// @src 29:14380:14570  "if (params.sqrtPriceLimitX96 >= slot0Start.sqrtPriceX96()) {..."
                    }
                    /// @src 29:14818:14824  "params"
                    let _1384_mpos := var_params_4413_mpos
                    let expr_4567_mpos := _1384_mpos
                    /// @src 29:14818:14842  "params.sqrtPriceLimitX96"
                    let _1385 := add(expr_4567_mpos, 96)
                    let _1386 := read_from_memoryt_uint160(_1385)
                    let expr_4568 := _1386
                    /// @src 29:14846:14854  "TickMath"
                    let expr_4569_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                    /// @src 29:14846:14869  "TickMath.MIN_SQRT_PRICE"
                    let expr_4570 := constant_MIN_SQRT_PRICE_5796()
                    /// @src 29:14818:14869  "params.sqrtPriceLimitX96 <= TickMath.MIN_SQRT_PRICE"
                    let expr_4571 := iszero(gt(cleanup_t_uint160(expr_4568), cleanup_t_uint160(expr_4570)))
                    /// @src 29:14814:14971  "if (params.sqrtPriceLimitX96 <= TickMath.MIN_SQRT_PRICE) {..."
                    if expr_4571 {
                        /// @src 29:14889:14919  "PriceLimitOutOfBounds.selector"
                        let expr_4575 := 0x9e4d7cc700000000000000000000000000000000000000000000000000000000
                        /// @src 29:14889:14930  "PriceLimitOutOfBounds.selector.revertWith"
                        let expr_4576_self := expr_4575
                        /// @src 29:14931:14937  "params"
                        let _1387_mpos := var_params_4413_mpos
                        let expr_4577_mpos := _1387_mpos
                        /// @src 29:14931:14955  "params.sqrtPriceLimitX96"
                        let _1388 := add(expr_4577_mpos, 96)
                        let _1389 := read_from_memoryt_uint160(_1388)
                        let expr_4578 := _1389
                        fun_revertWith_2304(expr_4576_self, expr_4578)
                        /// @src 29:14814:14971  "if (params.sqrtPriceLimitX96 <= TickMath.MIN_SQRT_PRICE) {..."
                    }
                    /// @src 29:14350:15371  "if (zeroForOne) {..."
                }
                /// @src 29:15381:15409  "StepComputations memory step"
                let var_step_4624_mpos
                let zero_t_struct$_StepComputations_$4395_memory_ptr_1390_mpos := zero_value_for_split_t_struct$_StepComputations_$4395_memory_ptr()
                var_step_4624_mpos := zero_t_struct$_StepComputations_$4395_memory_ptr_1390_mpos
                /// @src 29:15446:15456  "zeroForOne"
                let _1391 := var_zeroForOne_4433
                let expr_4629 := _1391
                /// @src 29:15446:15512  "zeroForOne ? self.feeGrowthGlobal0X128 : self.feeGrowthGlobal1X128"
                let expr_4634
                switch expr_4629
                case 0 {
                    /// @src 29:15487:15491  "self"
                    let _1392_slot := var_self_4410_slot
                    let expr_4632_slot := _1392_slot
                    /// @src 29:15487:15512  "self.feeGrowthGlobal1X128"
                    let _1393 := add(expr_4632_slot, 2)
                    let _1394 := read_from_storage_split_offset_0_t_uint256(_1393)
                    let expr_4633 := _1394
                    /// @src 29:15446:15512  "zeroForOne ? self.feeGrowthGlobal0X128 : self.feeGrowthGlobal1X128"
                    expr_4634 := expr_4633
                }
                default {
                    /// @src 29:15459:15463  "self"
                    let _1395_slot := var_self_4410_slot
                    let expr_4630_slot := _1395_slot
                    /// @src 29:15459:15484  "self.feeGrowthGlobal0X128"
                    let _1396 := add(expr_4630_slot, 1)
                    let _1397 := read_from_storage_split_offset_0_t_uint256(_1396)
                    let expr_4631 := _1397
                    /// @src 29:15446:15512  "zeroForOne ? self.feeGrowthGlobal0X128 : self.feeGrowthGlobal1X128"
                    expr_4634 := expr_4631
                }
                /// @src 29:15419:15423  "step"
                let _1398_mpos := var_step_4624_mpos
                let expr_4626_mpos := _1398_mpos
                /// @src 29:15419:15443  "step.feeGrowthGlobalX128"
                let _1399 := add(expr_4626_mpos, 224)
                /// @src 29:15419:15512  "step.feeGrowthGlobalX128 = zeroForOne ? self.feeGrowthGlobal0X128 : self.feeGrowthGlobal1X128"
                let _1400 := expr_4634
                write_to_memory_t_uint256(_1399, _1400)
                let expr_4635 := expr_4634
                /// @src 29:15639:20883  "while (!(amountSpecifiedRemaining == 0 || result.sqrtPriceX96 == params.sqrtPriceLimitX96)) {..."
                for {
                    } 1 {
                }
                {
                    /// @src 29:15648:15672  "amountSpecifiedRemaining"
                    let _1401 := var_amountSpecifiedRemaining_4453
                    let expr_4637 := _1401
                    /// @src 29:15676:15677  "0"
                    let expr_4638 := 0x00
                    /// @src 29:15648:15677  "amountSpecifiedRemaining == 0"
                    let expr_4639 := eq(cleanup_t_int256(expr_4637), convert_t_rational_0_by_1_to_t_int256(expr_4638))
                    /// @src 29:15648:15728  "amountSpecifiedRemaining == 0 || result.sqrtPriceX96 == params.sqrtPriceLimitX96"
                    let expr_4645 := expr_4639
                    if iszero(expr_4645) {
                        /// @src 29:15681:15687  "result"
                        let _1402_mpos := var_result_4424_mpos
                        let expr_4640_mpos := _1402_mpos
                        /// @src 29:15681:15700  "result.sqrtPriceX96"
                        let _1403 := add(expr_4640_mpos, 0)
                        let _1404 := read_from_memoryt_uint160(_1403)
                        let expr_4641 := _1404
                        /// @src 29:15704:15710  "params"
                        let _1405_mpos := var_params_4413_mpos
                        let expr_4642_mpos := _1405_mpos
                        /// @src 29:15704:15728  "params.sqrtPriceLimitX96"
                        let _1406 := add(expr_4642_mpos, 96)
                        let _1407 := read_from_memoryt_uint160(_1406)
                        let expr_4643 := _1407
                        /// @src 29:15681:15728  "result.sqrtPriceX96 == params.sqrtPriceLimitX96"
                        let expr_4644 := eq(cleanup_t_uint160(expr_4641), cleanup_t_uint160(expr_4643))
                        /// @src 29:15648:15728  "amountSpecifiedRemaining == 0 || result.sqrtPriceX96 == params.sqrtPriceLimitX96"
                        expr_4645 := expr_4644
                    }
                    /// @src 29:15647:15729  "(amountSpecifiedRemaining == 0 || result.sqrtPriceX96 == params.sqrtPriceLimitX96)"
                    let expr_4646 := expr_4645
                    /// @src 29:15646:15729  "!(amountSpecifiedRemaining == 0 || result.sqrtPriceX96 == params.sqrtPriceLimitX96)"
                    let expr_4647 := cleanup_t_bool(iszero(expr_4646))
                    if iszero(expr_4647) { break }
                    /// @src 29:15770:15776  "result"
                    let _1408_mpos := var_result_4424_mpos
                    let expr_4651_mpos := _1408_mpos
                    /// @src 29:15770:15789  "result.sqrtPriceX96"
                    let _1409 := add(expr_4651_mpos, 0)
                    let _1410 := read_from_memoryt_uint160(_1409)
                    let expr_4652 := _1410
                    /// @src 29:15745:15749  "step"
                    let _1411_mpos := var_step_4624_mpos
                    let expr_4648_mpos := _1411_mpos
                    /// @src 29:15745:15767  "step.sqrtPriceStartX96"
                    let _1412 := add(expr_4648_mpos, 0)
                    /// @src 29:15745:15789  "step.sqrtPriceStartX96 = result.sqrtPriceX96"
                    let _1413 := expr_4652
                    write_to_memory_t_uint160(_1412, _1413)
                    let expr_4653 := expr_4652
                    /// @src 29:15856:15860  "self"
                    let _1414_slot := var_self_4410_slot
                    let expr_4661_slot := _1414_slot
                    /// @src 29:15856:15871  "self.tickBitmap"
                    let _1415 := add(expr_4661_slot, 5)
                    let _1416_slot := _1415
                    let expr_4662_slot := _1416_slot
                    /// @src 29:15856:15904  "self.tickBitmap.nextInitializedTickWithinOneWord"
                    let expr_4663_self_slot := expr_4662_slot
                    /// @src 29:15905:15911  "result"
                    let _1417_mpos := var_result_4424_mpos
                    let expr_4664_mpos := _1417_mpos
                    /// @src 29:15905:15916  "result.tick"
                    let _1418 := add(expr_4664_mpos, 32)
                    let _1419 := read_from_memoryt_int24(_1418)
                    let expr_4665 := _1419
                    /// @src 29:15918:15924  "params"
                    let _1420_mpos := var_params_4413_mpos
                    let expr_4666_mpos := _1420_mpos
                    /// @src 29:15918:15936  "params.tickSpacing"
                    let _1421 := add(expr_4666_mpos, 32)
                    let _1422 := read_from_memoryt_int24(_1421)
                    let expr_4667 := _1422
                    /// @src 29:15938:15948  "zeroForOne"
                    let _1423 := var_zeroForOne_4433
                    let expr_4668 := _1423
                    /// @src 29:15856:15949  "self.tickBitmap.nextInitializedTickWithinOneWord(result.tick, params.tickSpacing, zeroForOne)"
                    let expr_4669_component_1, expr_4669_component_2 := fun_nextInitializedTickWithinOneWord_8597(expr_4663_self_slot, expr_4665, expr_4667, expr_4668)
                    /// @src 29:15805:15809  "step"
                    let _1424_mpos := var_step_4624_mpos
                    let expr_4655_mpos := _1424_mpos
                    /// @src 29:15805:15818  "step.tickNext"
                    let _1425 := add(expr_4655_mpos, 32)
                    /// @src 29:15820:15824  "step"
                    let _1426_mpos := var_step_4624_mpos
                    let expr_4658_mpos := _1426_mpos
                    /// @src 29:15820:15836  "step.initialized"
                    let _1427 := add(expr_4658_mpos, 64)
                    /// @src 29:15804:15949  "(step.tickNext, step.initialized) =..."
                    let _1428 := expr_4669_component_2
                    write_to_memory_t_bool(_1427, _1428)
                    let _1429 := expr_4669_component_1
                    write_to_memory_t_int24(_1425, _1429)
                    /// @src 29:16081:16085  "step"
                    let _1430_mpos := var_step_4624_mpos
                    let expr_4672_mpos := _1430_mpos
                    /// @src 29:16081:16094  "step.tickNext"
                    let _1431 := add(expr_4672_mpos, 32)
                    let _1432 := read_from_memoryt_int24(_1431)
                    let expr_4673 := _1432
                    /// @src 29:16098:16106  "TickMath"
                    let expr_4674_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                    /// @src 29:16098:16115  "TickMath.MIN_TICK"
                    let expr_4675 := constant_MIN_TICK_5776()
                    /// @src 29:16081:16115  "step.tickNext <= TickMath.MIN_TICK"
                    let expr_4676 := iszero(sgt(cleanup_t_int24(expr_4673), cleanup_t_int24(expr_4675)))
                    /// @src 29:16077:16183  "if (step.tickNext <= TickMath.MIN_TICK) {..."
                    if expr_4676 {
                        /// @src 29:16151:16159  "TickMath"
                        let expr_4680_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                        /// @src 29:16151:16168  "TickMath.MIN_TICK"
                        let expr_4681 := constant_MIN_TICK_5776()
                        /// @src 29:16135:16139  "step"
                        let _1433_mpos := var_step_4624_mpos
                        let expr_4677_mpos := _1433_mpos
                        /// @src 29:16135:16148  "step.tickNext"
                        let _1434 := add(expr_4677_mpos, 32)
                        /// @src 29:16135:16168  "step.tickNext = TickMath.MIN_TICK"
                        let _1435 := expr_4681
                        write_to_memory_t_int24(_1434, _1435)
                        let expr_4682 := expr_4681
                        /// @src 29:16077:16183  "if (step.tickNext <= TickMath.MIN_TICK) {..."
                    }
                    /// @src 29:16200:16204  "step"
                    let _1436_mpos := var_step_4624_mpos
                    let expr_4686_mpos := _1436_mpos
                    /// @src 29:16200:16213  "step.tickNext"
                    let _1437 := add(expr_4686_mpos, 32)
                    let _1438 := read_from_memoryt_int24(_1437)
                    let expr_4687 := _1438
                    /// @src 29:16217:16225  "TickMath"
                    let expr_4688_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                    /// @src 29:16217:16234  "TickMath.MAX_TICK"
                    let expr_4689 := constant_MAX_TICK_5780()
                    /// @src 29:16200:16234  "step.tickNext >= TickMath.MAX_TICK"
                    let expr_4690 := iszero(slt(cleanup_t_int24(expr_4687), cleanup_t_int24(expr_4689)))
                    /// @src 29:16196:16302  "if (step.tickNext >= TickMath.MAX_TICK) {..."
                    if expr_4690 {
                        /// @src 29:16270:16278  "TickMath"
                        let expr_4694_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                        /// @src 29:16270:16287  "TickMath.MAX_TICK"
                        let expr_4695 := constant_MAX_TICK_5780()
                        /// @src 29:16254:16258  "step"
                        let _1439_mpos := var_step_4624_mpos
                        let expr_4691_mpos := _1439_mpos
                        /// @src 29:16254:16267  "step.tickNext"
                        let _1440 := add(expr_4691_mpos, 32)
                        /// @src 29:16254:16287  "step.tickNext = TickMath.MAX_TICK"
                        let _1441 := expr_4695
                        write_to_memory_t_int24(_1440, _1441)
                        let expr_4696 := expr_4695
                        /// @src 29:16196:16302  "if (step.tickNext >= TickMath.MAX_TICK) {..."
                    }
                    /// @src 29:16387:16395  "TickMath"
                    let expr_4703_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                    /// @src 29:16415:16419  "step"
                    let _1442_mpos := var_step_4624_mpos
                    let expr_4705_mpos := _1442_mpos
                    /// @src 29:16415:16428  "step.tickNext"
                    let _1443 := add(expr_4705_mpos, 32)
                    let _1444 := read_from_memoryt_int24(_1443)
                    let expr_4706 := _1444
                    /// @src 29:16387:16429  "TickMath.getSqrtPriceAtTick(step.tickNext)"
                    let expr_4707 := fun_getSqrtPriceAtTick_6164(expr_4706)
                    /// @src 29:16363:16367  "step"
                    let _1445_mpos := var_step_4624_mpos
                    let expr_4700_mpos := _1445_mpos
                    /// @src 29:16363:16384  "step.sqrtPriceNextX96"
                    let _1446 := add(expr_4700_mpos, 96)
                    /// @src 29:16363:16429  "step.sqrtPriceNextX96 = TickMath.getSqrtPriceAtTick(step.tickNext)"
                    let _1447 := expr_4707
                    write_to_memory_t_uint160(_1446, _1447)
                    let expr_4708 := expr_4707
                    /// @src 29:16634:16642  "SwapMath"
                    let expr_4720_address := linkersymbol("src/libraries/SwapMath.sol:SwapMath")
                    /// @src 29:16676:16682  "result"
                    let _1448_mpos := var_result_4424_mpos
                    let expr_4722_mpos := _1448_mpos
                    /// @src 29:16676:16695  "result.sqrtPriceX96"
                    let _1449 := add(expr_4722_mpos, 0)
                    let _1450 := read_from_memoryt_uint160(_1449)
                    let expr_4723 := _1450
                    /// @src 29:16713:16721  "SwapMath"
                    let expr_4724_address := linkersymbol("src/libraries/SwapMath.sol:SwapMath")
                    /// @src 29:16741:16751  "zeroForOne"
                    let _1451 := var_zeroForOne_4433
                    let expr_4726 := _1451
                    /// @src 29:16753:16757  "step"
                    let _1452_mpos := var_step_4624_mpos
                    let expr_4727_mpos := _1452_mpos
                    /// @src 29:16753:16774  "step.sqrtPriceNextX96"
                    let _1453 := add(expr_4727_mpos, 96)
                    let _1454 := read_from_memoryt_uint160(_1453)
                    let expr_4728 := _1454
                    /// @src 29:16776:16782  "params"
                    let _1455_mpos := var_params_4413_mpos
                    let expr_4729_mpos := _1455_mpos
                    /// @src 29:16776:16800  "params.sqrtPriceLimitX96"
                    let _1456 := add(expr_4729_mpos, 96)
                    let _1457 := read_from_memoryt_uint160(_1456)
                    let expr_4730 := _1457
                    /// @src 29:16713:16801  "SwapMath.getSqrtPriceTarget(zeroForOne, step.sqrtPriceNextX96, params.sqrtPriceLimitX96)"
                    let expr_4731 := fun_getSqrtPriceTarget_8139(expr_4726, expr_4728, expr_4730)
                    /// @src 29:16819:16825  "result"
                    let _1458_mpos := var_result_4424_mpos
                    let expr_4732_mpos := _1458_mpos
                    /// @src 29:16819:16835  "result.liquidity"
                    let _1459 := add(expr_4732_mpos, 64)
                    let _1460 := read_from_memoryt_uint128(_1459)
                    let expr_4733 := _1460
                    /// @src 29:16853:16877  "amountSpecifiedRemaining"
                    let _1461 := var_amountSpecifiedRemaining_4453
                    let expr_4734 := _1461
                    /// @src 29:16895:16902  "swapFee"
                    let _1462 := var_swapFee_4421
                    let expr_4735 := _1462
                    /// @src 29:16634:16916  "SwapMath.computeSwapStep(..."
                    let expr_4736_component_1, expr_4736_component_2, expr_4736_component_3, expr_4736_component_4 := fun_computeSwapStep_8365(expr_4723, expr_4731, expr_4733, expr_4734, expr_4735)
                    /// @src 29:16564:16570  "result"
                    let _1463_mpos := var_result_4424_mpos
                    let expr_4710_mpos := _1463_mpos
                    /// @src 29:16564:16583  "result.sqrtPriceX96"
                    let _1464 := add(expr_4710_mpos, 0)
                    /// @src 29:16585:16589  "step"
                    let _1465_mpos := var_step_4624_mpos
                    let expr_4713_mpos := _1465_mpos
                    /// @src 29:16585:16598  "step.amountIn"
                    let _1466 := add(expr_4713_mpos, 128)
                    /// @src 29:16600:16604  "step"
                    let _1467_mpos := var_step_4624_mpos
                    let expr_4715_mpos := _1467_mpos
                    /// @src 29:16600:16614  "step.amountOut"
                    let _1468 := add(expr_4715_mpos, 160)
                    /// @src 29:16616:16620  "step"
                    let _1469_mpos := var_step_4624_mpos
                    let expr_4717_mpos := _1469_mpos
                    /// @src 29:16616:16630  "step.feeAmount"
                    let _1470 := add(expr_4717_mpos, 192)
                    /// @src 29:16563:16916  "(result.sqrtPriceX96, step.amountIn, step.amountOut, step.feeAmount) = SwapMath.computeSwapStep(..."
                    let _1471 := expr_4736_component_4
                    write_to_memory_t_uint256(_1470, _1471)
                    let _1472 := expr_4736_component_3
                    write_to_memory_t_uint256(_1468, _1472)
                    let _1473 := expr_4736_component_2
                    write_to_memory_t_uint256(_1466, _1473)
                    let _1474 := expr_4736_component_1
                    write_to_memory_t_uint160(_1464, _1474)
                    /// @src 29:16965:16971  "params"
                    let _1475_mpos := var_params_4413_mpos
                    let expr_4739_mpos := _1475_mpos
                    /// @src 29:16965:16987  "params.amountSpecified"
                    let _1476 := add(expr_4739_mpos, 0)
                    let _1477 := read_from_memoryt_int256(_1476)
                    let expr_4740 := _1477
                    /// @src 29:16990:16991  "0"
                    let expr_4741 := 0x00
                    /// @src 29:16965:16991  "params.amountSpecified > 0"
                    let expr_4742 := sgt(cleanup_t_int256(expr_4740), convert_t_rational_0_by_1_to_t_int256(expr_4741))
                    /// @src 29:16961:17529  "if (params.amountSpecified > 0) {..."
                    switch expr_4742
                    case 0 {
                        /// @src 29:17391:17395  "step"
                        let _1478_mpos := var_step_4624_mpos
                        let expr_4764_mpos := _1478_mpos
                        /// @src 29:17391:17404  "step.amountIn"
                        let _1479 := add(expr_4764_mpos, 128)
                        let _1480 := read_from_memoryt_uint256(_1479)
                        let expr_4765 := _1480
                        /// @src 29:17407:17411  "step"
                        let _1481_mpos := var_step_4624_mpos
                        let expr_4766_mpos := _1481_mpos
                        /// @src 29:17407:17421  "step.feeAmount"
                        let _1482 := add(expr_4766_mpos, 192)
                        let _1483 := read_from_memoryt_uint256(_1482)
                        let expr_4767 := _1483
                        /// @src 29:17391:17421  "step.amountIn + step.feeAmount"
                        let expr_4768 := wrapping_add_t_uint256(expr_4765, expr_4767)

                        /// @src 29:17390:17422  "(step.amountIn + step.feeAmount)"
                        let expr_4769 := expr_4768
                        /// @src 29:17390:17431  "(step.amountIn + step.feeAmount).toInt256"
                        let expr_4770_self := expr_4769
                        /// @src 29:17390:17433  "(step.amountIn + step.feeAmount).toInt256()"
                        let expr_4771 := fun_toInt256_5720(expr_4770_self)
                        /// @src 29:17362:17433  "amountSpecifiedRemaining += (step.amountIn + step.feeAmount).toInt256()"
                        let _1484 := var_amountSpecifiedRemaining_4453
                        let expr_4772 := wrapping_add_t_int256(_1484, expr_4771)

                        var_amountSpecifiedRemaining_4453 := expr_4772
                        /// @src 29:17489:17493  "step"
                        let _1485_mpos := var_step_4624_mpos
                        let expr_4776_mpos := _1485_mpos
                        /// @src 29:17489:17503  "step.amountOut"
                        let _1486 := add(expr_4776_mpos, 160)
                        let _1487 := read_from_memoryt_uint256(_1486)
                        let expr_4777 := _1487
                        /// @src 29:17489:17512  "step.amountOut.toInt256"
                        let expr_4778_self := expr_4777
                        /// @src 29:17489:17514  "step.amountOut.toInt256()"
                        let expr_4779 := fun_toInt256_5720(expr_4778_self)
                        /// @src 29:17469:17514  "amountCalculated += step.amountOut.toInt256()"
                        let _1488 := var_amountCalculated_4458
                        let expr_4780 := checked_add_t_int256(_1488, expr_4779)

                        var_amountCalculated_4458 := expr_4780
                        /// @src 29:16961:17529  "if (params.amountSpecified > 0) {..."
                    }
                    default {
                        /// @src 29:17071:17075  "step"
                        let _1489_mpos := var_step_4624_mpos
                        let expr_4744_mpos := _1489_mpos
                        /// @src 29:17071:17085  "step.amountOut"
                        let _1490 := add(expr_4744_mpos, 160)
                        let _1491 := read_from_memoryt_uint256(_1490)
                        let expr_4745 := _1491
                        /// @src 29:17071:17094  "step.amountOut.toInt256"
                        let expr_4746_self := expr_4745
                        /// @src 29:17071:17096  "step.amountOut.toInt256()"
                        let expr_4747 := fun_toInt256_5720(expr_4746_self)
                        /// @src 29:17043:17096  "amountSpecifiedRemaining -= step.amountOut.toInt256()"
                        let _1492 := var_amountSpecifiedRemaining_4453
                        let expr_4748 := wrapping_sub_t_int256(_1492, expr_4747)

                        var_amountSpecifiedRemaining_4453 := expr_4748
                        /// @src 29:17153:17157  "step"
                        let _1493_mpos := var_step_4624_mpos
                        let expr_4752_mpos := _1493_mpos
                        /// @src 29:17153:17166  "step.amountIn"
                        let _1494 := add(expr_4752_mpos, 128)
                        let _1495 := read_from_memoryt_uint256(_1494)
                        let expr_4753 := _1495
                        /// @src 29:17169:17173  "step"
                        let _1496_mpos := var_step_4624_mpos
                        let expr_4754_mpos := _1496_mpos
                        /// @src 29:17169:17183  "step.feeAmount"
                        let _1497 := add(expr_4754_mpos, 192)
                        let _1498 := read_from_memoryt_uint256(_1497)
                        let expr_4755 := _1498
                        /// @src 29:17153:17183  "step.amountIn + step.feeAmount"
                        let expr_4756 := checked_add_t_uint256(expr_4753, expr_4755)

                        /// @src 29:17152:17184  "(step.amountIn + step.feeAmount)"
                        let expr_4757 := expr_4756
                        /// @src 29:17152:17193  "(step.amountIn + step.feeAmount).toInt256"
                        let expr_4758_self := expr_4757
                        /// @src 29:17152:17195  "(step.amountIn + step.feeAmount).toInt256()"
                        let expr_4759 := fun_toInt256_5720(expr_4758_self)
                        /// @src 29:17132:17195  "amountCalculated -= (step.amountIn + step.feeAmount).toInt256()"
                        let _1499 := var_amountCalculated_4458
                        let expr_4760 := checked_sub_t_int256(_1499, expr_4759)

                        var_amountCalculated_4458 := expr_4760
                        /// @src 29:16961:17529  "if (params.amountSpecified > 0) {..."
                    }
                    /// @src 29:17664:17675  "protocolFee"
                    let _1500 := var_protocolFee_4438
                    let expr_4784 := _1500
                    /// @src 29:17678:17679  "0"
                    let expr_4785 := 0x00
                    /// @src 29:17664:17679  "protocolFee > 0"
                    let expr_4786 := gt(cleanup_t_uint256(expr_4784), convert_t_rational_0_by_1_to_t_uint256(expr_4785))
                    /// @src 29:17660:18611  "if (protocolFee > 0) {..."
                    if expr_4786 {
                        /// @src 29:18160:18167  "swapFee"
                        let _1501 := var_swapFee_4421
                        let expr_4789 := _1501
                        /// @src 29:18171:18182  "protocolFee"
                        let _1502 := var_protocolFee_4438
                        let expr_4790 := _1502
                        /// @src 29:18160:18182  "swapFee == protocolFee"
                        let expr_4791 := eq(convert_t_uint24_to_t_uint256(expr_4789), cleanup_t_uint256(expr_4790))
                        /// @src 29:18159:18183  "(swapFee == protocolFee)"
                        let expr_4792 := expr_4791
                        /// @src 29:18159:18401  "(swapFee == protocolFee)..."
                        let expr_4806
                        switch expr_4792
                        case 0 {
                            /// @src 29:18318:18322  "step"
                            let _1503_mpos := var_step_4624_mpos
                            let expr_4795_mpos := _1503_mpos
                            /// @src 29:18318:18331  "step.amountIn"
                            let _1504 := add(expr_4795_mpos, 128)
                            let _1505 := read_from_memoryt_uint256(_1504)
                            let expr_4796 := _1505
                            /// @src 29:18334:18338  "step"
                            let _1506_mpos := var_step_4624_mpos
                            let expr_4797_mpos := _1506_mpos
                            /// @src 29:18334:18348  "step.feeAmount"
                            let _1507 := add(expr_4797_mpos, 192)
                            let _1508 := read_from_memoryt_uint256(_1507)
                            let expr_4798 := _1508
                            /// @src 29:18318:18348  "step.amountIn + step.feeAmount"
                            let expr_4799 := wrapping_add_t_uint256(expr_4796, expr_4798)

                            /// @src 29:18317:18349  "(step.amountIn + step.feeAmount)"
                            let expr_4800 := expr_4799
                            /// @src 29:18352:18363  "protocolFee"
                            let _1509 := var_protocolFee_4438
                            let expr_4801 := _1509
                            /// @src 29:18317:18363  "(step.amountIn + step.feeAmount) * protocolFee"
                            let expr_4802 := wrapping_mul_t_uint256(expr_4800, expr_4801)

                            /// @src 29:18366:18384  "ProtocolFeeLibrary"
                            let expr_4803_address := linkersymbol("src/libraries/ProtocolFeeLibrary.sol:ProtocolFeeLibrary")
                            /// @src 29:18366:18401  "ProtocolFeeLibrary.PIPS_DENOMINATOR"
                            let expr_4804 := constant_PIPS_DENOMINATOR_7403()
                            /// @src 29:18317:18401  "(step.amountIn + step.feeAmount) * protocolFee / ProtocolFeeLibrary.PIPS_DENOMINATOR"
                            let expr_4805 := wrapping_div_t_uint256(expr_4802, expr_4804)

                            /// @src 29:18159:18401  "(swapFee == protocolFee)..."
                            expr_4806 := expr_4805
                        }
                        default {
                            /// @src 29:18210:18214  "step"
                            let _1511_mpos := var_step_4624_mpos
                            let expr_4793_mpos := _1511_mpos
                            /// @src 29:18210:18224  "step.feeAmount"
                            let _1512 := add(expr_4793_mpos, 192)
                            let _1513 := read_from_memoryt_uint256(_1512)
                            let expr_4794 := _1513
                            /// @src 29:18159:18401  "(swapFee == protocolFee)..."
                            expr_4806 := expr_4794
                        }
                        /// @src 29:18143:18401  "uint256 delta = (swapFee == protocolFee)..."
                        let var_delta_4788 := expr_4806
                        /// @src 29:18526:18531  "delta"
                        let _1514 := var_delta_4788
                        let expr_4811 := _1514
                        /// @src 29:18508:18512  "step"
                        let _1515_mpos := var_step_4624_mpos
                        let expr_4808_mpos := _1515_mpos
                        /// @src 29:18508:18522  "step.feeAmount"
                        let _1516 := add(expr_4808_mpos, 192)
                        /// @src 29:18508:18531  "step.feeAmount -= delta"
                        let _1517 := read_from_memoryt_uint256(_1516)
                        let expr_4812 := wrapping_sub_t_uint256(_1517, expr_4811)

                        let _1518 := expr_4812
                        write_to_memory_t_uint256(_1516, _1518)
                        /// @src 29:18573:18578  "delta"
                        let _1519 := var_delta_4788
                        let expr_4815 := _1519
                        /// @src 29:18553:18578  "amountToProtocol += delta"
                        let _1520 := var_amountToProtocol_4419
                        let expr_4816 := wrapping_add_t_uint256(_1520, expr_4815)

                        var_amountToProtocol_4419 := expr_4816
                        /// @src 29:17660:18611  "if (protocolFee > 0) {..."
                    }
                    /// @src 29:18670:18676  "result"
                    let _1521_mpos := var_result_4424_mpos
                    let expr_4821_mpos := _1521_mpos
                    /// @src 29:18670:18686  "result.liquidity"
                    let _1522 := add(expr_4821_mpos, 64)
                    let _1523 := read_from_memoryt_uint128(_1522)
                    let expr_4822 := _1523
                    /// @src 29:18689:18690  "0"
                    let expr_4823 := 0x00
                    /// @src 29:18670:18690  "result.liquidity > 0"
                    let expr_4824 := gt(cleanup_t_uint128(expr_4822), convert_t_rational_0_by_1_to_t_uint128(expr_4823))
                    /// @src 29:18666:19048  "if (result.liquidity > 0) {..."
                    if expr_4824 {
                        /// @src 29:18938:18948  "UnsafeMath"
                        let expr_4828_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                        /// @src 29:18962:18966  "step"
                        let _1524_mpos := var_step_4624_mpos
                        let expr_4830_mpos := _1524_mpos
                        /// @src 29:18962:18976  "step.feeAmount"
                        let _1525 := add(expr_4830_mpos, 192)
                        let _1526 := read_from_memoryt_uint256(_1525)
                        let expr_4831 := _1526
                        /// @src 29:18978:18991  "FixedPoint128"
                        let expr_4832_address := linkersymbol("src/libraries/FixedPoint128.sol:FixedPoint128")
                        /// @src 29:18978:18996  "FixedPoint128.Q128"
                        let expr_4833 := constant_Q128_7606()
                        /// @src 29:18998:19004  "result"
                        let _1527_mpos := var_result_4424_mpos
                        let expr_4834_mpos := _1527_mpos
                        /// @src 29:18998:19014  "result.liquidity"
                        let _1528 := add(expr_4834_mpos, 64)
                        let _1529 := read_from_memoryt_uint128(_1528)
                        let expr_4835 := _1529
                        /// @src 29:18938:19015  "UnsafeMath.simpleMulDiv(step.feeAmount, FixedPoint128.Q128, result.liquidity)"
                        let _1530 := convert_t_uint128_to_t_uint256(expr_4835)
                        let expr_4836 := fun_simpleMulDiv_8627(expr_4831, expr_4833, _1530)
                        /// @src 29:18886:18890  "step"
                        let _1531_mpos := var_step_4624_mpos
                        let expr_4825_mpos := _1531_mpos
                        /// @src 29:18886:18910  "step.feeGrowthGlobalX128"
                        let _1532 := add(expr_4825_mpos, 224)
                        /// @src 29:18886:19015  "step.feeGrowthGlobalX128 +=..."
                        let _1533 := read_from_memoryt_uint256(_1532)
                        let expr_4837 := wrapping_add_t_uint256(_1533, expr_4836)

                        let _1534 := expr_4837
                        write_to_memory_t_uint256(_1532, _1534)
                        /// @src 29:18666:19048  "if (result.liquidity > 0) {..."
                    }
                    /// @src 29:19488:19494  "result"
                    let _1535_mpos := var_result_4424_mpos
                    let expr_4842_mpos := _1535_mpos
                    /// @src 29:19488:19507  "result.sqrtPriceX96"
                    let _1536 := add(expr_4842_mpos, 0)
                    let _1537 := read_from_memoryt_uint160(_1536)
                    let expr_4843 := _1537
                    /// @src 29:19511:19515  "step"
                    let _1538_mpos := var_step_4624_mpos
                    let expr_4844_mpos := _1538_mpos
                    /// @src 29:19511:19532  "step.sqrtPriceNextX96"
                    let _1539 := add(expr_4844_mpos, 96)
                    let _1540 := read_from_memoryt_uint160(_1539)
                    let expr_4845 := _1540
                    /// @src 29:19488:19532  "result.sqrtPriceX96 == step.sqrtPriceNextX96"
                    let expr_4846 := eq(cleanup_t_uint160(expr_4843), cleanup_t_uint160(expr_4845))
                    /// @src 29:19484:20873  "if (result.sqrtPriceX96 == step.sqrtPriceNextX96) {..."
                    switch expr_4846
                    case 0 {
                        /// @src 29:20611:20617  "result"
                        let _1541_mpos := var_result_4424_mpos
                        let expr_4913_mpos := _1541_mpos
                        /// @src 29:20611:20630  "result.sqrtPriceX96"
                        let _1542 := add(expr_4913_mpos, 0)
                        let _1543 := read_from_memoryt_uint160(_1542)
                        let expr_4914 := _1543
                        /// @src 29:20634:20638  "step"
                        let _1544_mpos := var_step_4624_mpos
                        let expr_4915_mpos := _1544_mpos
                        /// @src 29:20634:20656  "step.sqrtPriceStartX96"
                        let _1545 := add(expr_4915_mpos, 0)
                        let _1546 := read_from_memoryt_uint160(_1545)
                        let expr_4916 := _1546
                        /// @src 29:20611:20656  "result.sqrtPriceX96 != step.sqrtPriceStartX96"
                        let expr_4917 := iszero(eq(cleanup_t_uint160(expr_4914), cleanup_t_uint160(expr_4916)))
                        /// @src 29:20607:20873  "if (result.sqrtPriceX96 != step.sqrtPriceStartX96) {..."
                        if expr_4917 {
                            /// @src 29:20810:20818  "TickMath"
                            let expr_4921_address := linkersymbol("src/libraries/TickMath.sol:TickMath")
                            /// @src 29:20838:20844  "result"
                            let _1547_mpos := var_result_4424_mpos
                            let expr_4923_mpos := _1547_mpos
                            /// @src 29:20838:20857  "result.sqrtPriceX96"
                            let _1548 := add(expr_4923_mpos, 0)
                            let _1549 := read_from_memoryt_uint160(_1548)
                            let expr_4924 := _1549
                            /// @src 29:20810:20858  "TickMath.getTickAtSqrtPrice(result.sqrtPriceX96)"
                            let expr_4925 := fun_getTickAtSqrtPrice_6304(expr_4924)
                            /// @src 29:20796:20802  "result"
                            let _1550_mpos := var_result_4424_mpos
                            let expr_4918_mpos := _1550_mpos
                            /// @src 29:20796:20807  "result.tick"
                            let _1551 := add(expr_4918_mpos, 32)
                            /// @src 29:20796:20858  "result.tick = TickMath.getTickAtSqrtPrice(result.sqrtPriceX96)"
                            let _1552 := expr_4925
                            write_to_memory_t_int24(_1551, _1552)
                            let expr_4926 := expr_4925
                            /// @src 29:20607:20873  "if (result.sqrtPriceX96 != step.sqrtPriceStartX96) {..."
                        }
                        /// @src 29:19484:20873  "if (result.sqrtPriceX96 == step.sqrtPriceNextX96) {..."
                    }
                    default {
                        /// @src 29:19627:19631  "step"
                        let _1553_mpos := var_step_4624_mpos
                        let expr_4847_mpos := _1553_mpos
                        /// @src 29:19627:19643  "step.initialized"
                        let _1554 := add(expr_4847_mpos, 64)
                        let _1555 := read_from_memoryt_bool(_1554)
                        let expr_4848 := _1555
                        /// @src 29:19623:20458  "if (step.initialized) {..."
                        if expr_4848 {
                            /// @src 29:19730:19740  "zeroForOne"
                            let _1556 := var_zeroForOne_4433
                            let expr_4853 := _1556
                            /// @src 29:19730:19900  "zeroForOne..."
                            let expr_4864_component_1, expr_4864_component_2
                            switch expr_4853
                            case 0 {
                                /// @src 29:19848:19852  "self"
                                let _1557_slot := var_self_4410_slot
                                let expr_4859_slot := _1557_slot
                                /// @src 29:19848:19873  "self.feeGrowthGlobal0X128"
                                let _1558 := add(expr_4859_slot, 1)
                                let _1559 := read_from_storage_split_offset_0_t_uint256(_1558)
                                let expr_4860 := _1559
                                /// @src 29:19847:19900  "(self.feeGrowthGlobal0X128, step.feeGrowthGlobalX128)"
                                let expr_4863_component_1 := expr_4860
                                /// @src 29:19875:19879  "step"
                                let _1560_mpos := var_step_4624_mpos
                                let expr_4861_mpos := _1560_mpos
                                /// @src 29:19875:19899  "step.feeGrowthGlobalX128"
                                let _1561 := add(expr_4861_mpos, 224)
                                let _1562 := read_from_memoryt_uint256(_1561)
                                let expr_4862 := _1562
                                /// @src 29:19847:19900  "(self.feeGrowthGlobal0X128, step.feeGrowthGlobalX128)"
                                let expr_4863_component_2 := expr_4862
                                /// @src 29:19730:19900  "zeroForOne..."
                                expr_4864_component_1 := expr_4863_component_1
                                expr_4864_component_2 := expr_4863_component_2
                            }
                            default {
                                /// @src 29:19768:19772  "step"
                                let _1563_mpos := var_step_4624_mpos
                                let expr_4854_mpos := _1563_mpos
                                /// @src 29:19768:19792  "step.feeGrowthGlobalX128"
                                let _1564 := add(expr_4854_mpos, 224)
                                let _1565 := read_from_memoryt_uint256(_1564)
                                let expr_4855 := _1565
                                /// @src 29:19767:19820  "(step.feeGrowthGlobalX128, self.feeGrowthGlobal1X128)"
                                let expr_4858_component_1 := expr_4855
                                /// @src 29:19794:19798  "self"
                                let _1566_slot := var_self_4410_slot
                                let expr_4856_slot := _1566_slot
                                /// @src 29:19794:19819  "self.feeGrowthGlobal1X128"
                                let _1567 := add(expr_4856_slot, 2)
                                let _1568 := read_from_storage_split_offset_0_t_uint256(_1567)
                                let expr_4857 := _1568
                                /// @src 29:19767:19820  "(step.feeGrowthGlobalX128, self.feeGrowthGlobal1X128)"
                                let expr_4858_component_2 := expr_4857
                                /// @src 29:19730:19900  "zeroForOne..."
                                expr_4864_component_1 := expr_4858_component_1
                                expr_4864_component_2 := expr_4858_component_2
                            }
                            /// @src 29:19667:19900  "(uint256 feeGrowthGlobal0X128, uint256 feeGrowthGlobal1X128) = zeroForOne..."
                            let var_feeGrowthGlobal0X128_4850 := expr_4864_component_1
                            let var_feeGrowthGlobal1X128_4852 := expr_4864_component_2
                            /// @src 29:19968:19972  "Pool"
                            let expr_4868_address := linkersymbol("src/libraries/Pool.sol:Pool")
                            /// @src 29:19983:19987  "self"
                            let _1569_slot := var_self_4410_slot
                            let expr_4870_slot := _1569_slot
                            /// @src 29:19989:19993  "step"
                            let _1570_mpos := var_step_4624_mpos
                            let expr_4871_mpos := _1570_mpos
                            /// @src 29:19989:20002  "step.tickNext"
                            let _1571 := add(expr_4871_mpos, 32)
                            let _1572 := read_from_memoryt_int24(_1571)
                            let expr_4872 := _1572
                            /// @src 29:20004:20024  "feeGrowthGlobal0X128"
                            let _1573 := var_feeGrowthGlobal0X128_4850
                            let expr_4873 := _1573
                            /// @src 29:20026:20046  "feeGrowthGlobal1X128"
                            let _1574 := var_feeGrowthGlobal1X128_4852
                            let expr_4874 := _1574
                            /// @src 29:19968:20047  "Pool.crossTick(self, step.tickNext, feeGrowthGlobal0X128, feeGrowthGlobal1X128)"
                            let expr_4875 := fun_crossTick_5408(expr_4870_slot, expr_4872, expr_4873, expr_4874)
                            /// @src 29:19922:20047  "int128 liquidityNet =..."
                            let var_liquidityNet_4867 := expr_4875
                            /// @src 29:20281:20291  "zeroForOne"
                            let _1575 := var_zeroForOne_4433
                            let expr_4877 := _1575
                            /// @src 29:20277:20321  "if (zeroForOne) liquidityNet = -liquidityNet"
                            if expr_4877 {
                                /// @src 29:20309:20321  "liquidityNet"
                                let _1576 := var_liquidityNet_4867
                                let expr_4879 := _1576
                                /// @src 29:20308:20321  "-liquidityNet"
                                let expr_4880 := negate_wrapping_t_int128(expr_4879)
                                /// @src 29:20293:20321  "liquidityNet = -liquidityNet"
                                var_liquidityNet_4867 := expr_4880
                                let expr_4881 := expr_4880
                                /// @src 29:20277:20321  "if (zeroForOne) liquidityNet = -liquidityNet"
                            }
                            /// @src 29:20385:20398  "LiquidityMath"
                            let expr_4888_address := linkersymbol("src/libraries/LiquidityMath.sol:LiquidityMath")
                            /// @src 29:20408:20414  "result"
                            let _1577_mpos := var_result_4424_mpos
                            let expr_4890_mpos := _1577_mpos
                            /// @src 29:20408:20424  "result.liquidity"
                            let _1578 := add(expr_4890_mpos, 64)
                            let _1579 := read_from_memoryt_uint128(_1578)
                            let expr_4891 := _1579
                            /// @src 29:20426:20438  "liquidityNet"
                            let _1580 := var_liquidityNet_4867
                            let expr_4892 := _1580
                            /// @src 29:20385:20439  "LiquidityMath.addDelta(result.liquidity, liquidityNet)"
                            let expr_4893 := fun_addDelta_7622(expr_4891, expr_4892)
                            /// @src 29:20366:20372  "result"
                            let _1581_mpos := var_result_4424_mpos
                            let expr_4885_mpos := _1581_mpos
                            /// @src 29:20366:20382  "result.liquidity"
                            let _1582 := add(expr_4885_mpos, 64)
                            /// @src 29:20366:20439  "result.liquidity = LiquidityMath.addDelta(result.liquidity, liquidityNet)"
                            let _1583 := expr_4893
                            write_to_memory_t_uint128(_1582, _1583)
                            let expr_4894 := expr_4893
                            /// @src 29:19623:20458  "if (step.initialized) {..."
                        }
                        /// @src 29:20522:20532  "zeroForOne"
                        let _1584 := var_zeroForOne_4433
                        let expr_4901 := _1584
                        /// @src 29:20522:20568  "zeroForOne ? step.tickNext - 1 : step.tickNext"
                        let expr_4908
                        switch expr_4901
                        case 0 {
                            /// @src 29:20555:20559  "step"
                            let _1585_mpos := var_step_4624_mpos
                            let expr_4906_mpos := _1585_mpos
                            /// @src 29:20555:20568  "step.tickNext"
                            let _1586 := add(expr_4906_mpos, 32)
                            let _1587 := read_from_memoryt_int24(_1586)
                            let expr_4907 := _1587
                            /// @src 29:20522:20568  "zeroForOne ? step.tickNext - 1 : step.tickNext"
                            expr_4908 := expr_4907
                        }
                        default {
                            /// @src 29:20535:20539  "step"
                            let _1588_mpos := var_step_4624_mpos
                            let expr_4902_mpos := _1588_mpos
                            /// @src 29:20535:20548  "step.tickNext"
                            let _1589 := add(expr_4902_mpos, 32)
                            let _1590 := read_from_memoryt_int24(_1589)
                            let expr_4903 := _1590
                            /// @src 29:20551:20552  "1"
                            let expr_4904 := 0x01
                            /// @src 29:20535:20552  "step.tickNext - 1"
                            let expr_4905 := wrapping_sub_t_int24(expr_4903, convert_t_rational_1_by_1_to_t_int24(expr_4904))

                            /// @src 29:20522:20568  "zeroForOne ? step.tickNext - 1 : step.tickNext"
                            expr_4908 := expr_4905
                        }
                        /// @src 29:20508:20514  "result"
                        let _1591_mpos := var_result_4424_mpos
                        let expr_4898_mpos := _1591_mpos
                        /// @src 29:20508:20519  "result.tick"
                        let _1592 := add(expr_4898_mpos, 32)
                        /// @src 29:20508:20568  "result.tick = zeroForOne ? step.tickNext - 1 : step.tickNext"
                        let _1593 := expr_4908
                        write_to_memory_t_int24(_1592, _1593)
                        let expr_4909 := expr_4908
                        /// @src 29:19484:20873  "if (result.sqrtPriceX96 == step.sqrtPriceNextX96) {..."
                    }
                }
                /// @src 29:20906:20916  "slot0Start"
                let _1594 := var_slot0Start_4428
                let expr_4936 := _1594
                /// @src 29:20906:20924  "slot0Start.setTick"
                let expr_4937_self := expr_4936
                /// @src 29:20925:20931  "result"
                let _1595_mpos := var_result_4424_mpos
                let expr_4938_mpos := _1595_mpos
                /// @src 29:20925:20936  "result.tick"
                let _1596 := add(expr_4938_mpos, 32)
                let _1597 := read_from_memoryt_int24(_1596)
                let expr_4939 := _1597
                /// @src 29:20906:20937  "slot0Start.setTick(result.tick)"
                let expr_4940 := fun_setTick_8718(expr_4937_self, expr_4939)
                /// @src 29:20906:20953  "slot0Start.setTick(result.tick).setSqrtPriceX96"
                let expr_4941_self := expr_4940
                /// @src 29:20954:20960  "result"
                let _1598_mpos := var_result_4424_mpos
                let expr_4942_mpos := _1598_mpos
                /// @src 29:20954:20973  "result.sqrtPriceX96"
                let _1599 := add(expr_4942_mpos, 0)
                let _1600 := read_from_memoryt_uint160(_1599)
                let expr_4943 := _1600
                /// @src 29:20906:20974  "slot0Start.setTick(result.tick).setSqrtPriceX96(result.sqrtPriceX96)"
                let expr_4944 := fun_setSqrtPriceX96_8705(expr_4941_self, expr_4943)
                /// @src 29:20893:20897  "self"
                let _1601_slot := var_self_4410_slot
                let expr_4933_slot := _1601_slot
                /// @src 29:20893:20903  "self.slot0"
                let _1602 := add(expr_4933_slot, 0)
                /// @src 29:20893:20974  "self.slot0 = slot0Start.setTick(result.tick).setSqrtPriceX96(result.sqrtPriceX96)"
                update_storage_value_offset_0t_userDefinedValueType$_Slot0_$8632_to_t_userDefinedValueType$_Slot0_$8632(_1602, expr_4944)
                let expr_4945 := expr_4944
                /// @src 29:21031:21035  "self"
                let _1603_slot := var_self_4410_slot
                let expr_4947_slot := _1603_slot
                /// @src 29:21031:21045  "self.liquidity"
                let _1604 := add(expr_4947_slot, 3)
                let _1605 := read_from_storage_split_offset_0_t_uint128(_1604)
                let expr_4948 := _1605
                /// @src 29:21049:21055  "result"
                let _1606_mpos := var_result_4424_mpos
                let expr_4949_mpos := _1606_mpos
                /// @src 29:21049:21065  "result.liquidity"
                let _1607 := add(expr_4949_mpos, 64)
                let _1608 := read_from_memoryt_uint128(_1607)
                let expr_4950 := _1608
                /// @src 29:21031:21065  "self.liquidity != result.liquidity"
                let expr_4951 := iszero(eq(cleanup_t_uint128(expr_4948), cleanup_t_uint128(expr_4950)))
                /// @src 29:21027:21100  "if (self.liquidity != result.liquidity) self.liquidity = result.liquidity"
                if expr_4951 {
                    /// @src 29:21084:21090  "result"
                    let _1609_mpos := var_result_4424_mpos
                    let expr_4955_mpos := _1609_mpos
                    /// @src 29:21084:21100  "result.liquidity"
                    let _1610 := add(expr_4955_mpos, 64)
                    let _1611 := read_from_memoryt_uint128(_1610)
                    let expr_4956 := _1611
                    /// @src 29:21067:21071  "self"
                    let _1612_slot := var_self_4410_slot
                    let expr_4952_slot := _1612_slot
                    /// @src 29:21067:21081  "self.liquidity"
                    let _1613 := add(expr_4952_slot, 3)
                    /// @src 29:21067:21100  "self.liquidity = result.liquidity"
                    update_storage_value_offset_0t_uint128_to_t_uint128(_1613, expr_4956)
                    let expr_4957 := expr_4956
                    /// @src 29:21027:21100  "if (self.liquidity != result.liquidity) self.liquidity = result.liquidity"
                }
                /// @src 29:21152:21162  "zeroForOne"
                let _1614 := var_zeroForOne_4433
                let expr_4960 := _1614
                /// @src 29:21151:21162  "!zeroForOne"
                let expr_4961 := cleanup_t_bool(iszero(expr_4960))
                /// @src 29:21147:21324  "if (!zeroForOne) {..."
                switch expr_4961
                case 0 {
                    /// @src 29:21289:21293  "step"
                    let _1615_mpos := var_step_4624_mpos
                    let expr_4973_mpos := _1615_mpos
                    /// @src 29:21289:21313  "step.feeGrowthGlobalX128"
                    let _1616 := add(expr_4973_mpos, 224)
                    let _1617 := read_from_memoryt_uint256(_1616)
                    let expr_4974 := _1617
                    /// @src 29:21261:21265  "self"
                    let _1618_slot := var_self_4410_slot
                    let expr_4970_slot := _1618_slot
                    /// @src 29:21261:21286  "self.feeGrowthGlobal0X128"
                    let _1619 := add(expr_4970_slot, 1)
                    /// @src 29:21261:21313  "self.feeGrowthGlobal0X128 = step.feeGrowthGlobalX128"
                    update_storage_value_offset_0t_uint256_to_t_uint256(_1619, expr_4974)
                    let expr_4975 := expr_4974
                    /// @src 29:21147:21324  "if (!zeroForOne) {..."
                }
                default {
                    /// @src 29:21206:21210  "step"
                    let _1620_mpos := var_step_4624_mpos
                    let expr_4965_mpos := _1620_mpos
                    /// @src 29:21206:21230  "step.feeGrowthGlobalX128"
                    let _1621 := add(expr_4965_mpos, 224)
                    let _1622 := read_from_memoryt_uint256(_1621)
                    let expr_4966 := _1622
                    /// @src 29:21178:21182  "self"
                    let _1623_slot := var_self_4410_slot
                    let expr_4962_slot := _1623_slot
                    /// @src 29:21178:21203  "self.feeGrowthGlobal1X128"
                    let _1624 := add(expr_4962_slot, 2)
                    /// @src 29:21178:21230  "self.feeGrowthGlobal1X128 = step.feeGrowthGlobalX128"
                    update_storage_value_offset_0t_uint256_to_t_uint256(_1624, expr_4966)
                    let expr_4967 := expr_4966
                    /// @src 29:21147:21324  "if (!zeroForOne) {..."
                }
                /// @src 29:21405:21415  "zeroForOne"
                let _1625 := var_zeroForOne_4433
                let expr_4979 := _1625
                /// @src 29:21420:21426  "params"
                let _1626_mpos := var_params_4413_mpos
                let expr_4980_mpos := _1626_mpos
                /// @src 29:21420:21442  "params.amountSpecified"
                let _1627 := add(expr_4980_mpos, 0)
                let _1628 := read_from_memoryt_int256(_1627)
                let expr_4981 := _1628
                /// @src 29:21445:21446  "0"
                let expr_4982 := 0x00
                /// @src 29:21420:21446  "params.amountSpecified < 0"
                let expr_4983 := slt(cleanup_t_int256(expr_4981), convert_t_rational_0_by_1_to_t_int256(expr_4982))
                /// @src 29:21419:21447  "(params.amountSpecified < 0)"
                let expr_4984 := expr_4983
                /// @src 29:21405:21447  "zeroForOne != (params.amountSpecified < 0)"
                let expr_4985 := iszero(eq(cleanup_t_bool(expr_4979), cleanup_t_bool(expr_4984)))
                /// @src 29:21401:21835  "if (zeroForOne != (params.amountSpecified < 0)) {..."
                switch expr_4985
                case 0 {
                    /// @src 29:21712:21718  "params"
                    let _1629_mpos := var_params_4413_mpos
                    let expr_5004_mpos := _1629_mpos
                    /// @src 29:21712:21734  "params.amountSpecified"
                    let _1630 := add(expr_5004_mpos, 0)
                    let _1631 := read_from_memoryt_int256(_1630)
                    let expr_5005 := _1631
                    /// @src 29:21737:21761  "amountSpecifiedRemaining"
                    let _1632 := var_amountSpecifiedRemaining_4453
                    let expr_5006 := _1632
                    /// @src 29:21712:21761  "params.amountSpecified - amountSpecifiedRemaining"
                    let expr_5007 := wrapping_sub_t_int256(expr_5005, expr_5006)

                    /// @src 29:21711:21762  "(params.amountSpecified - amountSpecifiedRemaining)"
                    let expr_5008 := expr_5007
                    /// @src 29:21711:21771  "(params.amountSpecified - amountSpecifiedRemaining).toInt128"
                    let expr_5009_self := expr_5008
                    /// @src 29:21711:21773  "(params.amountSpecified - amountSpecifiedRemaining).toInt128()"
                    let expr_5010 := fun_toInt128_5693(expr_5009_self)
                    /// @src 29:21775:21791  "amountCalculated"
                    let _1633 := var_amountCalculated_4458
                    let expr_5011 := _1633
                    /// @src 29:21775:21800  "amountCalculated.toInt128"
                    let expr_5012_self := expr_5011
                    /// @src 29:21775:21802  "amountCalculated.toInt128()"
                    let expr_5013 := fun_toInt128_5693(expr_5012_self)
                    /// @src 29:21675:21820  "toBalanceDelta(..."
                    let expr_5014 := fun_toBalanceDelta_6337(expr_5010, expr_5013)
                    /// @src 29:21663:21820  "swapDelta = toBalanceDelta(..."
                    var_swapDelta_4417 := expr_5014
                    let expr_5015 := expr_5014
                    /// @src 29:21401:21835  "if (zeroForOne != (params.amountSpecified < 0)) {..."
                }
                default {
                    /// @src 29:21515:21531  "amountCalculated"
                    let _1634 := var_amountCalculated_4458
                    let expr_4988 := _1634
                    /// @src 29:21515:21540  "amountCalculated.toInt128"
                    let expr_4989_self := expr_4988
                    /// @src 29:21515:21542  "amountCalculated.toInt128()"
                    let expr_4990 := fun_toInt128_5693(expr_4989_self)
                    /// @src 29:21545:21551  "params"
                    let _1635_mpos := var_params_4413_mpos
                    let expr_4991_mpos := _1635_mpos
                    /// @src 29:21545:21567  "params.amountSpecified"
                    let _1636 := add(expr_4991_mpos, 0)
                    let _1637 := read_from_memoryt_int256(_1636)
                    let expr_4992 := _1637
                    /// @src 29:21570:21594  "amountSpecifiedRemaining"
                    let _1638 := var_amountSpecifiedRemaining_4453
                    let expr_4993 := _1638
                    /// @src 29:21545:21594  "params.amountSpecified - amountSpecifiedRemaining"
                    let expr_4994 := wrapping_sub_t_int256(expr_4992, expr_4993)

                    /// @src 29:21544:21595  "(params.amountSpecified - amountSpecifiedRemaining)"
                    let expr_4995 := expr_4994
                    /// @src 29:21544:21604  "(params.amountSpecified - amountSpecifiedRemaining).toInt128"
                    let expr_4996_self := expr_4995
                    /// @src 29:21544:21606  "(params.amountSpecified - amountSpecifiedRemaining).toInt128()"
                    let expr_4997 := fun_toInt128_5693(expr_4996_self)
                    /// @src 29:21479:21624  "toBalanceDelta(..."
                    let expr_4998 := fun_toBalanceDelta_6337(expr_4990, expr_4997)
                    /// @src 29:21467:21624  "swapDelta = toBalanceDelta(..."
                    var_swapDelta_4417 := expr_4998
                    let expr_4999 := expr_4998
                    /// @src 29:21401:21835  "if (zeroForOne != (params.amountSpecified < 0)) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 1640
            /// @src 7:2870:3033  "function _updateProtocolFees(Currency currency, uint256 amount) internal {..."
            function fun__updateProtocolFees_1640(var_currency_1627, var_amount_1629) {

                /// @src 7:3010:3016  "amount"
                let _1639 := var_amount_1629
                let expr_1635 := _1639
                /// @src 7:2977:2996  "protocolFeesAccrued"
                let _1640_slot := 0x01
                let expr_1632_slot := _1640_slot
                /// @src 7:2997:3005  "currency"
                let _1641 := var_currency_1627
                let expr_1633 := _1641
                /// @src 7:2977:3006  "protocolFeesAccrued[currency]"
                let _1642 := mapping_index_access_t_mapping$_t_userDefinedValueType$_Currency_$6525_$_t_uint256_$_of_t_userDefinedValueType$_Currency_$6525(expr_1632_slot,expr_1633)
                /// @src 7:2977:3016  "protocolFeesAccrued[currency] += amount"
                let _1643 := read_from_storage_split_offset_0_t_uint256(_1642)
                let expr_1636 := wrapping_add_t_uint256(_1643, expr_1635)

                update_storage_value_offset_0t_uint256_to_t_uint256(_1642, expr_1636)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 6516
            /// @src 39:1257:1463  "function getUnspecifiedDelta(BeforeSwapDelta delta) internal pure returns (int128 deltaUnspecified) {..."
            function fun_getUnspecifiedDelta_6516(var_delta_6509) -> var_deltaUnspecified_6512 {
                /// @src 39:1332:1355  "int128 deltaUnspecified"
                let zero_t_int128_1644 := zero_value_for_split_t_int128()
                var_deltaUnspecified_6512 := zero_t_int128_1644

                /// @src 39:1367:1457  "assembly (\"memory-safe\") {..."
                {
                    var_deltaUnspecified_6512 := signextend(15, var_delta_6509)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7190
            /// @src 1:3302:3494  "function _burn(address sender, uint256 id, uint256 amount) internal virtual {..."
            function fun__burn_7190(var_sender_7162, var_id_7164, var_amount_7166) {

                /// @src 1:3413:3419  "amount"
                let _1645 := var_amount_7166
                let expr_7174 := _1645
                /// @src 1:3388:3397  "balanceOf"
                let _1646_slot := 0x04
                let expr_7169_slot := _1646_slot
                /// @src 1:3398:3404  "sender"
                let _1647 := var_sender_7162
                let expr_7170 := _1647
                /// @src 1:3388:3405  "balanceOf[sender]"
                let _1648 := mapping_index_access_t_mapping$_t_address_$_t_mapping$_t_uint256_$_t_uint256_$_$_of_t_address(expr_7169_slot,expr_7170)
                let _1649_slot := _1648
                let expr_7172_slot := _1649_slot
                /// @src 1:3406:3408  "id"
                let _1650 := var_id_7164
                let expr_7171 := _1650
                /// @src 1:3388:3409  "balanceOf[sender][id]"
                let _1651 := mapping_index_access_t_mapping$_t_uint256_$_t_uint256_$_of_t_uint256(expr_7172_slot,expr_7171)
                /// @src 1:3388:3419  "balanceOf[sender][id] -= amount"
                let _1652 := read_from_storage_split_offset_0_t_uint256(_1651)
                let expr_7175 := checked_sub_t_uint256(_1652, expr_7174)

                update_storage_value_offset_0t_uint256_to_t_uint256(_1651, expr_7175)
                /// @src 1:3444:3454  "msg.sender"
                let expr_7179 := caller()
                /// @src 1:3456:3462  "sender"
                let _1653 := var_sender_7162
                let expr_7180 := _1653
                /// @src 1:3472:3473  "0"
                let expr_7183 := 0x00
                /// @src 1:3464:3474  "address(0)"
                let expr_7184 := convert_t_rational_0_by_1_to_t_address(expr_7183)
                /// @src 1:3476:3478  "id"
                let _1654 := var_id_7164
                let expr_7185 := _1654
                /// @src 1:3480:3486  "amount"
                let _1655 := var_amount_7166
                let expr_7186 := _1655
                /// @src 1:3435:3487  "Transfer(msg.sender, sender, address(0), id, amount)"
                let _1656 := 0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859
                let _1657 := convert_t_address_to_t_address(expr_7180)
                let _1658 := convert_t_address_to_t_address(expr_7184)
                let _1659 := convert_t_uint256_to_t_uint256(expr_7185)
                {
                    let _1660 := allocate_unbounded()
                    let _1661 := abi_encode_tuple_t_address_t_uint256__to_t_address_t_uint256__fromStack(_1660 , expr_7179, expr_7186)
                    log4(_1660, sub(_1661, _1660) , _1656, _1657, _1658, _1659)
                }
            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_bytes4() -> ret {
                ret := 0
            }

            /// @ast-id 7581
            /// @src 28:394:654  "function parseSelector(bytes memory result) internal pure returns (bytes4 selector) {..."
            function fun_parseSelector_7581(var_result_7574_mpos) -> var_selector_7577 {
                /// @src 28:461:476  "bytes4 selector"
                let zero_t_bytes4_1662 := zero_value_for_split_t_bytes4()
                var_selector_7577 := zero_t_bytes4_1662

                /// @src 28:563:648  "assembly (\"memory-safe\") {..."
                {
                    var_selector_7577 := mload(add(var_result_7574_mpos, 0x20))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2316
            /// @src 19:2003:2349  "function revertWith(bytes4 selector, int24 value1, int24 value2) internal pure {..."
            function fun_revertWith_2316(var_selector_2307, var_value1_2309, var_value2_2311) {

                /// @src 19:2092:2343  "assembly (\"memory-safe\") {..."
                {
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, var_selector_2307)
                    mstore(add(usr$fmp, 0x04), signextend(2, var_value1_2309))
                    mstore(add(usr$fmp, 0x24), signextend(2, var_value2_2311))
                    revert(usr$fmp, 0x44)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5485
            /// @src 30:2184:3062  "function calculatePositionKey(address owner, int24 tickLower, int24 tickUpper, bytes32 salt)..."
            function fun_calculatePositionKey_5485(var_owner_5472, var_tickLower_5474, var_tickUpper_5476, var_salt_5478) -> var_positionKey_5481 {
                /// @src 30:2324:2343  "bytes32 positionKey"
                let zero_t_bytes32_1663 := zero_value_for_split_t_bytes32()
                var_positionKey_5481 := zero_t_bytes32_1663

                /// @src 30:2447:3056  "assembly (\"memory-safe\") {..."
                {
                    let usr$fmp := mload(0x40)
                    mstore(add(usr$fmp, 0x26), var_salt_5478)
                    mstore(add(usr$fmp, 0x06), var_tickUpper_5476)
                    mstore(add(usr$fmp, 0x03), var_tickLower_5474)
                    mstore(usr$fmp, var_owner_5472)
                    var_positionKey_5481 := keccak256(add(usr$fmp, 0x0c), 0x3a)
                    mstore(add(usr$fmp, 0x40), 0)
                    mstore(add(usr$fmp, 0x20), 0)
                    mstore(usr$fmp, 0)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function require_helper(condition) {
                if iszero(condition) { revert(0, 0) }
            }

            function cleanup_t_rational_3_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_3_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_3_by_1(value)))
            }

            /// @ast-id 8874
            /// @src 22:741:4882  "function mulDiv(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256 result) {..."
            function fun_mulDiv_8874(var_a_8751, var_b_8753, var_denominator_8755) -> var_result_8758 {
                /// @src 22:823:837  "uint256 result"
                let zero_t_uint256_1664 := zero_value_for_split_t_uint256()
                var_result_8758 := zero_t_uint256_1664

                /// @src 22:1212:1213  "a"
                let _1665 := var_a_8751
                let expr_8762 := _1665
                /// @src 22:1216:1217  "b"
                let _1666 := var_b_8753
                let expr_8763 := _1666
                /// @src 22:1212:1217  "a * b"
                let expr_8764 := wrapping_mul_t_uint256(expr_8762, expr_8763)

                /// @src 22:1196:1217  "uint256 prod0 = a * b"
                let var_prod0_8761 := expr_8764
                /// @src 22:1276:1289  "uint256 prod1"
                let var_prod1_8767
                let zero_t_uint256_1667 := zero_value_for_split_t_uint256()
                var_prod1_8767 := zero_t_uint256_1667
                /// @src 22:1347:1494  "assembly (\"memory-safe\") {..."
                {
                    let usr$mm := mulmod(var_a_8751, var_b_8753, not(0))
                    var_prod1_8767 := sub(sub(usr$mm, var_prod0_8761), lt(usr$mm, var_prod0_8761))
                }
                /// @src 22:1619:1630  "denominator"
                let _1668 := var_denominator_8755
                let expr_8771 := _1668
                /// @src 22:1633:1638  "prod1"
                let _1669 := var_prod1_8767
                let expr_8772 := _1669
                /// @src 22:1619:1638  "denominator > prod1"
                let expr_8773 := gt(cleanup_t_uint256(expr_8771), cleanup_t_uint256(expr_8772))
                /// @src 22:1611:1639  "require(denominator > prod1)"
                require_helper(expr_8773)
                /// @src 22:1720:1725  "prod1"
                let _1670 := var_prod1_8767
                let expr_8776 := _1670
                /// @src 22:1729:1730  "0"
                let expr_8777 := 0x00
                /// @src 22:1720:1730  "prod1 == 0"
                let expr_8778 := eq(cleanup_t_uint256(expr_8776), convert_t_rational_0_by_1_to_t_uint256(expr_8777))
                /// @src 22:1716:1893  "if (prod1 == 0) {..."
                if expr_8778 {
                    /// @src 22:1750:1848  "assembly (\"memory-safe\") {..."
                    {
                        var_result_8758 := div(var_prod0_8761, var_denominator_8755)
                    }
                    /// @src 22:1872:1878  "result"
                    let _1671 := var_result_8758
                    let expr_8780 := _1671
                    /// @src 22:1865:1878  "return result"
                    var_result_8758 := expr_8780
                    leave
                    /// @src 22:1716:1893  "if (prod1 == 0) {..."
                }
                /// @src 22:2193:2210  "uint256 remainder"
                let var_remainder_8785
                let zero_t_uint256_1672 := zero_value_for_split_t_uint256()
                var_remainder_8785 := zero_t_uint256_1672
                /// @src 22:2224:2319  "assembly (\"memory-safe\") {..."
                {
                    var_remainder_8785 := mulmod(var_a_8751, var_b_8753, var_denominator_8755)
                }
                /// @src 22:2391:2536  "assembly (\"memory-safe\") {..."
                {
                    var_prod1_8767 := sub(var_prod1_8767, gt(var_remainder_8785, var_prod0_8761))
                    var_prod0_8761 := sub(var_prod0_8761, var_remainder_8785)
                }
                /// @src 22:2717:2718  "0"
                let expr_8791 := 0x00
                /// @src 22:2721:2732  "denominator"
                let _1673 := var_denominator_8755
                let expr_8792 := _1673
                /// @src 22:2717:2732  "0 - denominator"
                let expr_8793 := wrapping_sub_t_uint256(convert_t_rational_0_by_1_to_t_uint256(expr_8791), expr_8792)

                /// @src 22:2716:2733  "(0 - denominator)"
                let expr_8794 := expr_8793
                /// @src 22:2736:2747  "denominator"
                let _1674 := var_denominator_8755
                let expr_8795 := _1674
                /// @src 22:2716:2747  "(0 - denominator) & denominator"
                let expr_8796 := and(expr_8794, expr_8795)

                /// @src 22:2701:2747  "uint256 twos = (0 - denominator) & denominator"
                let var_twos_8790 := expr_8796
                /// @src 22:2811:2905  "assembly (\"memory-safe\") {..."
                {
                    var_denominator_8755 := div(var_denominator_8755, var_twos_8790)
                }
                /// @src 22:2977:3059  "assembly (\"memory-safe\") {..."
                {
                    var_prod0_8761 := div(var_prod0_8761, var_twos_8790)
                }
                /// @src 22:3254:3350  "assembly (\"memory-safe\") {..."
                {
                    var_twos_8790 := add(div(sub(0, var_twos_8790), var_twos_8790), 1)
                }
                /// @src 22:3372:3377  "prod1"
                let _1675 := var_prod1_8767
                let expr_8802 := _1675
                /// @src 22:3380:3384  "twos"
                let _1676 := var_twos_8790
                let expr_8803 := _1676
                /// @src 22:3372:3384  "prod1 * twos"
                let expr_8804 := wrapping_mul_t_uint256(expr_8802, expr_8803)

                /// @src 22:3363:3384  "prod0 |= prod1 * twos"
                let _1677 := var_prod0_8761
                let expr_8805 := or(_1677, expr_8804)

                var_prod0_8761 := expr_8805
                /// @src 22:3757:3758  "3"
                let expr_8809 := 0x03
                /// @src 22:3761:3772  "denominator"
                let _1678 := var_denominator_8755
                let expr_8810 := _1678
                /// @src 22:3757:3772  "3 * denominator"
                let expr_8811 := wrapping_mul_t_uint256(convert_t_rational_3_by_1_to_t_uint256(expr_8809), expr_8810)

                /// @src 22:3756:3773  "(3 * denominator)"
                let expr_8812 := expr_8811
                /// @src 22:3776:3777  "2"
                let expr_8813 := 0x02
                /// @src 22:3756:3777  "(3 * denominator) ^ 2"
                let expr_8814 := xor(expr_8812, convert_t_rational_2_by_1_to_t_uint256(expr_8813))

                /// @src 22:3742:3777  "uint256 inv = (3 * denominator) ^ 2"
                let var_inv_8808 := expr_8814
                /// @src 22:4015:4016  "2"
                let expr_8817 := 0x02
                /// @src 22:4019:4030  "denominator"
                let _1679 := var_denominator_8755
                let expr_8818 := _1679
                /// @src 22:4033:4036  "inv"
                let _1680 := var_inv_8808
                let expr_8819 := _1680
                /// @src 22:4019:4036  "denominator * inv"
                let expr_8820 := wrapping_mul_t_uint256(expr_8818, expr_8819)

                /// @src 22:4015:4036  "2 - denominator * inv"
                let expr_8821 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8817), expr_8820)

                /// @src 22:4008:4036  "inv *= 2 - denominator * inv"
                let _1681 := var_inv_8808
                let expr_8822 := wrapping_mul_t_uint256(_1681, expr_8821)

                var_inv_8808 := expr_8822
                /// @src 22:4077:4078  "2"
                let expr_8825 := 0x02
                /// @src 22:4081:4092  "denominator"
                let _1682 := var_denominator_8755
                let expr_8826 := _1682
                /// @src 22:4095:4098  "inv"
                let _1683 := var_inv_8808
                let expr_8827 := _1683
                /// @src 22:4081:4098  "denominator * inv"
                let expr_8828 := wrapping_mul_t_uint256(expr_8826, expr_8827)

                /// @src 22:4077:4098  "2 - denominator * inv"
                let expr_8829 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8825), expr_8828)

                /// @src 22:4070:4098  "inv *= 2 - denominator * inv"
                let _1684 := var_inv_8808
                let expr_8830 := wrapping_mul_t_uint256(_1684, expr_8829)

                var_inv_8808 := expr_8830
                /// @src 22:4140:4141  "2"
                let expr_8833 := 0x02
                /// @src 22:4144:4155  "denominator"
                let _1685 := var_denominator_8755
                let expr_8834 := _1685
                /// @src 22:4158:4161  "inv"
                let _1686 := var_inv_8808
                let expr_8835 := _1686
                /// @src 22:4144:4161  "denominator * inv"
                let expr_8836 := wrapping_mul_t_uint256(expr_8834, expr_8835)

                /// @src 22:4140:4161  "2 - denominator * inv"
                let expr_8837 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8833), expr_8836)

                /// @src 22:4133:4161  "inv *= 2 - denominator * inv"
                let _1687 := var_inv_8808
                let expr_8838 := wrapping_mul_t_uint256(_1687, expr_8837)

                var_inv_8808 := expr_8838
                /// @src 22:4203:4204  "2"
                let expr_8841 := 0x02
                /// @src 22:4207:4218  "denominator"
                let _1688 := var_denominator_8755
                let expr_8842 := _1688
                /// @src 22:4221:4224  "inv"
                let _1689 := var_inv_8808
                let expr_8843 := _1689
                /// @src 22:4207:4224  "denominator * inv"
                let expr_8844 := wrapping_mul_t_uint256(expr_8842, expr_8843)

                /// @src 22:4203:4224  "2 - denominator * inv"
                let expr_8845 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8841), expr_8844)

                /// @src 22:4196:4224  "inv *= 2 - denominator * inv"
                let _1690 := var_inv_8808
                let expr_8846 := wrapping_mul_t_uint256(_1690, expr_8845)

                var_inv_8808 := expr_8846
                /// @src 22:4266:4267  "2"
                let expr_8849 := 0x02
                /// @src 22:4270:4281  "denominator"
                let _1691 := var_denominator_8755
                let expr_8850 := _1691
                /// @src 22:4284:4287  "inv"
                let _1692 := var_inv_8808
                let expr_8851 := _1692
                /// @src 22:4270:4287  "denominator * inv"
                let expr_8852 := wrapping_mul_t_uint256(expr_8850, expr_8851)

                /// @src 22:4266:4287  "2 - denominator * inv"
                let expr_8853 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8849), expr_8852)

                /// @src 22:4259:4287  "inv *= 2 - denominator * inv"
                let _1693 := var_inv_8808
                let expr_8854 := wrapping_mul_t_uint256(_1693, expr_8853)

                var_inv_8808 := expr_8854
                /// @src 22:4330:4331  "2"
                let expr_8857 := 0x02
                /// @src 22:4334:4345  "denominator"
                let _1694 := var_denominator_8755
                let expr_8858 := _1694
                /// @src 22:4348:4351  "inv"
                let _1695 := var_inv_8808
                let expr_8859 := _1695
                /// @src 22:4334:4351  "denominator * inv"
                let expr_8860 := wrapping_mul_t_uint256(expr_8858, expr_8859)

                /// @src 22:4330:4351  "2 - denominator * inv"
                let expr_8861 := wrapping_sub_t_uint256(convert_t_rational_2_by_1_to_t_uint256(expr_8857), expr_8860)

                /// @src 22:4323:4351  "inv *= 2 - denominator * inv"
                let _1696 := var_inv_8808
                let expr_8862 := wrapping_mul_t_uint256(_1696, expr_8861)

                var_inv_8808 := expr_8862
                /// @src 22:4827:4832  "prod0"
                let _1697 := var_prod0_8761
                let expr_8865 := _1697
                /// @src 22:4835:4838  "inv"
                let _1698 := var_inv_8808
                let expr_8866 := _1698
                /// @src 22:4827:4838  "prod0 * inv"
                let expr_8867 := wrapping_mul_t_uint256(expr_8865, expr_8866)

                /// @src 22:4818:4838  "result = prod0 * inv"
                var_result_8758 := expr_8867
                let expr_8868 := expr_8867
                /// @src 22:4859:4865  "result"
                let _1699 := var_result_8758
                let expr_8870 := _1699
                /// @src 22:4852:4865  "return result"
                var_result_8758 := expr_8870
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_79228162514264337593543950336_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_79228162514264337593543950336_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_79228162514264337593543950336_by_1(value)))
            }

            /// @src 21:303:362  "uint256 internal constant Q96 = 0x1000000000000000000000000"
            function constant_Q96_9030() -> ret {
                /// @src 21:335:362  "0x1000000000000000000000000"
                let expr_9029 := 0x01000000000000000000000000
                let _1703 := convert_t_rational_79228162514264337593543950336_by_1_to_t_uint256(expr_9029)

                ret := _1703
            }

            /// @ast-id 8027
            /// @src 33:11589:12527  "function getAmount1Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, uint128 liquidity, bool roundUp)..."
            function fun_getAmount1Delta_8027(var_sqrtPriceAX96_7986, var_sqrtPriceBX96_7988, var_liquidity_7990, var_roundUp_7992) -> var_amount1_7995 {
                /// @src 33:11740:11755  "uint256 amount1"
                let zero_t_uint256_1700 := zero_value_for_split_t_uint256()
                var_amount1_7995 := zero_t_uint256_1700

                /// @src 33:11799:11812  "sqrtPriceAX96"
                let _1701 := var_sqrtPriceAX96_7986
                let expr_8000 := _1701
                /// @src 33:11814:11827  "sqrtPriceBX96"
                let _1702 := var_sqrtPriceBX96_7988
                let expr_8001 := _1702
                /// @src 33:11791:11828  "absDiff(sqrtPriceAX96, sqrtPriceBX96)"
                let expr_8002 := fun_absDiff_7983(expr_8000, expr_8001)
                /// @src 33:11771:11828  "uint256 numerator = absDiff(sqrtPriceAX96, sqrtPriceBX96)"
                let var_numerator_7998 := expr_8002
                /// @src 33:11860:11872  "FixedPoint96"
                let expr_8006_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                /// @src 33:11860:11876  "FixedPoint96.Q96"
                let expr_8007 := constant_Q96_9030()
                /// @src 33:11838:11876  "uint256 denominator = FixedPoint96.Q96"
                let var_denominator_8005 := expr_8007
                /// @src 33:11915:11924  "liquidity"
                let _1704 := var_liquidity_7990
                let expr_8013 := _1704
                /// @src 33:11907:11925  "uint256(liquidity)"
                let expr_8014 := convert_t_uint128_to_t_uint256(expr_8013)
                /// @src 33:11886:11925  "uint256 _liquidity = uint256(liquidity)"
                let var__liquidity_8010 := expr_8014
                /// @src 33:12323:12331  "FullMath"
                let expr_8017_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                /// @src 33:12339:12349  "_liquidity"
                let _1705 := var__liquidity_8010
                let expr_8019 := _1705
                /// @src 33:12351:12360  "numerator"
                let _1706 := var_numerator_7998
                let expr_8020 := _1706
                /// @src 33:12362:12373  "denominator"
                let _1707 := var_denominator_8005
                let expr_8021 := _1707
                /// @src 33:12323:12374  "FullMath.mulDiv(_liquidity, numerator, denominator)"
                let expr_8022 := fun_mulDiv_8874(expr_8019, expr_8020, expr_8021)
                /// @src 33:12313:12374  "amount1 = FullMath.mulDiv(_liquidity, numerator, denominator)"
                var_amount1_7995 := expr_8022
                let expr_8023 := expr_8022
                /// @src 33:12384:12521  "assembly (\"memory-safe\") {..."
                {
                    var_amount1_7995 := add(var_amount1_7995, and(gt(mulmod(var__liquidity_8010, var_numerator_7998, var_denominator_8005), 0), var_roundUp_7992))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5720
            /// @src 32:1776:1927  "function toInt256(uint256 x) internal pure returns (int256 y) {..."
            function fun_toInt256_5720(var_x_5696) -> var_y_5699 {
                /// @src 32:1828:1836  "int256 y"
                let zero_t_int256_1708 := zero_value_for_split_t_int256()
                var_y_5699 := zero_t_int256_1708

                /// @src 32:1859:1860  "x"
                let _1709 := var_x_5696
                let expr_5704 := _1709
                /// @src 32:1852:1861  "int256(x)"
                let expr_5705 := convert_t_uint256_to_t_int256(expr_5704)
                /// @src 32:1848:1861  "y = int256(x)"
                var_y_5699 := expr_5705
                let expr_5706 := expr_5705
                /// @src 32:1875:1876  "y"
                let _1710 := var_y_5699
                let expr_5708 := _1710
                /// @src 32:1879:1880  "0"
                let expr_5709 := 0x00
                /// @src 32:1875:1880  "y < 0"
                let expr_5710 := slt(cleanup_t_int256(expr_5708), convert_t_rational_0_by_1_to_t_int256(expr_5709))
                /// @src 32:1871:1920  "if (y < 0) SafeCastOverflow.selector.revertWith()"
                if expr_5710 {
                    /// @src 32:1882:1907  "SafeCastOverflow.selector"
                    let expr_5714 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
                    /// @src 32:1882:1918  "SafeCastOverflow.selector.revertWith"
                    let expr_5715_self := expr_5714
                    fun_revertWith_2274(expr_5715_self)
                    /// @src 32:1871:1920  "if (y < 0) SafeCastOverflow.selector.revertWith()"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function convert_t_rational_96_by_1_to_t_uint8(value) -> converted {
                converted := cleanup_t_uint8(identity(cleanup_t_rational_96_by_1(value)))
            }

            /// @src 21:258:297  "uint8 internal constant RESOLUTION = 96"
            function constant_RESOLUTION_9027() -> ret {
                /// @src 21:295:297  "96"
                let expr_9026 := 0x60
                let _1717 := convert_t_rational_96_by_1_to_t_uint8(expr_9026)

                ret := _1717
            }

            /// @ast-id 7971
            /// @src 33:9398:10448  "function getAmount0Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, uint128 liquidity, bool roundUp)..."
            function fun_getAmount0Delta_7971(var_sqrtPriceAX96_7908, var_sqrtPriceBX96_7910, var_liquidity_7912, var_roundUp_7914) -> var__7917 {
                /// @src 33:9549:9556  "uint256"
                let zero_t_uint256_1711 := zero_value_for_split_t_uint256()
                var__7917 := zero_t_uint256_1711

                /// @src 33:9600:9613  "sqrtPriceAX96"
                let _1712 := var_sqrtPriceAX96_7908
                let expr_7919 := _1712
                /// @src 33:9616:9629  "sqrtPriceBX96"
                let _1713 := var_sqrtPriceBX96_7910
                let expr_7920 := _1713
                /// @src 33:9600:9629  "sqrtPriceAX96 > sqrtPriceBX96"
                let expr_7921 := gt(cleanup_t_uint160(expr_7919), cleanup_t_uint160(expr_7920))
                /// @src 33:9596:9694  "if (sqrtPriceAX96 > sqrtPriceBX96) (sqrtPriceAX96, sqrtPriceBX96) = (sqrtPriceBX96, sqrtPriceAX96)"
                if expr_7921 {
                    /// @src 33:9665:9678  "sqrtPriceBX96"
                    let _1714 := var_sqrtPriceBX96_7910
                    let expr_7925 := _1714
                    /// @src 33:9664:9694  "(sqrtPriceBX96, sqrtPriceAX96)"
                    let expr_7927_component_1 := expr_7925
                    /// @src 33:9680:9693  "sqrtPriceAX96"
                    let _1715 := var_sqrtPriceAX96_7908
                    let expr_7926 := _1715
                    /// @src 33:9664:9694  "(sqrtPriceBX96, sqrtPriceAX96)"
                    let expr_7927_component_2 := expr_7926
                    /// @src 33:9631:9694  "(sqrtPriceAX96, sqrtPriceBX96) = (sqrtPriceBX96, sqrtPriceAX96)"
                    var_sqrtPriceBX96_7910 := expr_7927_component_2
                    var_sqrtPriceAX96_7908 := expr_7927_component_1
                    /// @src 33:9596:9694  "if (sqrtPriceAX96 > sqrtPriceBX96) (sqrtPriceAX96, sqrtPriceBX96) = (sqrtPriceBX96, sqrtPriceAX96)"
                }
                /// @src 33:9783:10045  "assembly (\"memory-safe\") {..."
                {
                    if iszero(and(var_sqrtPriceAX96_7908, 0xffffffffffffffffffffffffffffffffffffffff))
                    {
                        mstore(0, 0x00bfc921)
                        revert(0x1c, 0x04)
                    }
                }
                /// @src 33:10088:10097  "liquidity"
                let _1716 := var_liquidity_7912
                let expr_7936 := _1716
                /// @src 33:10080:10098  "uint256(liquidity)"
                let expr_7937 := convert_t_uint128_to_t_uint256(expr_7936)
                /// @src 33:10102:10114  "FixedPoint96"
                let expr_7938_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                /// @src 33:10102:10125  "FixedPoint96.RESOLUTION"
                let expr_7939 := constant_RESOLUTION_9027()
                /// @src 33:10080:10125  "uint256(liquidity) << FixedPoint96.RESOLUTION"
                let expr_7940 :=
                shift_left_t_uint256_t_uint8(expr_7937, expr_7939)

                /// @src 33:10059:10125  "uint256 numerator1 = uint256(liquidity) << FixedPoint96.RESOLUTION"
                let var_numerator1_7933 := expr_7940
                /// @src 33:10160:10173  "sqrtPriceBX96"
                let _1718 := var_sqrtPriceBX96_7910
                let expr_7944 := _1718
                /// @src 33:10176:10189  "sqrtPriceAX96"
                let _1719 := var_sqrtPriceAX96_7908
                let expr_7945 := _1719
                /// @src 33:10160:10189  "sqrtPriceBX96 - sqrtPriceAX96"
                let expr_7946 := wrapping_sub_t_uint160(expr_7944, expr_7945)

                /// @src 33:10139:10189  "uint256 numerator2 = sqrtPriceBX96 - sqrtPriceAX96"
                let var_numerator2_7943 := convert_t_uint160_to_t_uint256(expr_7946)
                /// @src 33:10211:10218  "roundUp"
                let _1720 := var_roundUp_7914
                let expr_7948 := _1720
                /// @src 33:10211:10431  "roundUp..."
                let expr_7967
                switch expr_7948
                case 0 {
                    /// @src 33:10361:10369  "FullMath"
                    let expr_7959_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                    /// @src 33:10377:10387  "numerator1"
                    let _1721 := var_numerator1_7933
                    let expr_7961 := _1721
                    /// @src 33:10389:10399  "numerator2"
                    let _1722 := var_numerator2_7943
                    let expr_7962 := _1722
                    /// @src 33:10401:10414  "sqrtPriceBX96"
                    let _1723 := var_sqrtPriceBX96_7910
                    let expr_7963 := _1723
                    /// @src 33:10361:10415  "FullMath.mulDiv(numerator1, numerator2, sqrtPriceBX96)"
                    let _1724 := convert_t_uint160_to_t_uint256(expr_7963)
                    let expr_7964 := fun_mulDiv_8874(expr_7961, expr_7962, _1724)
                    /// @src 33:10418:10431  "sqrtPriceAX96"
                    let _1725 := var_sqrtPriceAX96_7908
                    let expr_7965 := _1725
                    /// @src 33:10361:10431  "FullMath.mulDiv(numerator1, numerator2, sqrtPriceBX96) / sqrtPriceAX96"
                    let expr_7966 := wrapping_div_t_uint256(expr_7964, convert_t_uint160_to_t_uint256(expr_7965))

                    /// @src 33:10211:10431  "roundUp..."
                    expr_7967 := expr_7966
                }
                default {
                    /// @src 33:10237:10247  "UnsafeMath"
                    let expr_7949_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                    /// @src 33:10262:10270  "FullMath"
                    let expr_7951_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                    /// @src 33:10288:10298  "numerator1"
                    let _1726 := var_numerator1_7933
                    let expr_7953 := _1726
                    /// @src 33:10300:10310  "numerator2"
                    let _1727 := var_numerator2_7943
                    let expr_7954 := _1727
                    /// @src 33:10312:10325  "sqrtPriceBX96"
                    let _1728 := var_sqrtPriceBX96_7910
                    let expr_7955 := _1728
                    /// @src 33:10262:10326  "FullMath.mulDivRoundingUp(numerator1, numerator2, sqrtPriceBX96)"
                    let _1729 := convert_t_uint160_to_t_uint256(expr_7955)
                    let expr_7956 := fun_mulDivRoundingUp_8912(expr_7953, expr_7954, _1729)
                    /// @src 33:10328:10341  "sqrtPriceAX96"
                    let _1730 := var_sqrtPriceAX96_7908
                    let expr_7957 := _1730
                    /// @src 33:10237:10342  "UnsafeMath.divRoundingUp(FullMath.mulDivRoundingUp(numerator1, numerator2, sqrtPriceBX96), sqrtPriceAX96)"
                    let _1731 := convert_t_uint160_to_t_uint256(expr_7957)
                    let expr_7958 := fun_divRoundingUp_8613(expr_7956, _1731)
                    /// @src 33:10211:10431  "roundUp..."
                    expr_7967 := expr_7958
                }
                /// @src 33:10204:10431  "return roundUp..."
                var__7917 := expr_7967
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_uint8() -> ret {
                ret := 0
            }

            /// @ast-id 8932
            /// @src 16:653:1317  "function mostSignificantBit(uint256 x) internal pure returns (uint8 r) {..."
            function fun_mostSignificantBit_8932(var_x_8919) -> var_r_8922 {
                /// @src 16:715:722  "uint8 r"
                let zero_t_uint8_1732 := zero_value_for_split_t_uint8()
                var_r_8922 := zero_t_uint8_1732

                /// @src 16:742:743  "x"
                let _1733 := var_x_8919
                let expr_8925 := _1733
                /// @src 16:746:747  "0"
                let expr_8926 := 0x00
                /// @src 16:742:747  "x > 0"
                let expr_8927 := gt(cleanup_t_uint256(expr_8925), convert_t_rational_0_by_1_to_t_uint256(expr_8926))
                /// @src 16:734:748  "require(x > 0)"
                require_helper(expr_8927)
                /// @src 16:759:1311  "assembly (\"memory-safe\") {..."
                {
                    var_r_8922 := shl(7, lt(0xffffffffffffffffffffffffffffffff, var_x_8919))
                    var_r_8922 := or(var_r_8922, shl(6, lt(0xffffffffffffffff, shr(var_r_8922, var_x_8919))))
                    var_r_8922 := or(var_r_8922, shl(5, lt(0xffffffff, shr(var_r_8922, var_x_8919))))
                    var_r_8922 := or(var_r_8922, shl(4, lt(0xffff, shr(var_r_8922, var_x_8919))))
                    var_r_8922 := or(var_r_8922, shl(3, lt(0xff, shr(var_r_8922, var_x_8919))))
                    var_r_8922 := or(var_r_8922, byte(and(0x1f, shr(shr(var_r_8922, var_x_8919), 0x8421084210842108cc6318c6db6d54be)), 0x0706060506020500060203020504000106050205030304010505030400000000))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8682
            /// @src 44:1792:2005  "function protocolFee(Slot0 _packed) internal pure returns (uint24 _protocolFee) {..."
            function fun_protocolFee_8682(var__packed_8675) -> var__protocolFee_8678 {
                /// @src 44:1851:1870  "uint24 _protocolFee"
                let zero_t_uint24_1734 := zero_value_for_split_t_uint24()
                var__protocolFee_8678 := zero_t_uint24_1734

                /// @src 44:1882:1999  "assembly (\"memory-safe\") {..."
                {
                    var__protocolFee_8678 := and(16777215, shr(184, var__packed_8675))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_uint16() -> ret {
                ret := 0
            }

            function cleanup_t_rational_12_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_12_by_1_to_t_uint8(value) -> converted {
                converted := cleanup_t_uint8(identity(cleanup_t_rational_12_by_1(value)))
            }

            function shift_right_t_uint24_t_uint8(value, bits) -> result {
                bits := cleanup_t_uint8(bits)
                result := cleanup_t_uint24(shift_right_unsigned_dynamic(bits, cleanup_t_uint24(value)))
            }

            function convert_t_uint24_to_t_uint16(value) -> converted {
                converted := cleanup_t_uint16(identity(cleanup_t_uint24(value)))
            }

            /// @ast-id 7433
            /// @src 31:769:881  "function getOneForZeroFee(uint24 self) internal pure returns (uint16) {..."
            function fun_getOneForZeroFee_7433(var_self_7420) -> var__7423 {
                /// @src 31:831:837  "uint16"
                let zero_t_uint16_1735 := zero_value_for_split_t_uint16()
                var__7423 := zero_t_uint16_1735

                /// @src 31:863:867  "self"
                let _1736 := var_self_7420
                let expr_7427 := _1736
                /// @src 31:871:873  "12"
                let expr_7428 := 0x0c
                /// @src 31:863:873  "self >> 12"
                let _1737 := convert_t_rational_12_by_1_to_t_uint8(expr_7428)
                let expr_7429 :=
                shift_right_t_uint24_t_uint8(expr_7427, _1737)

                /// @src 31:856:874  "uint16(self >> 12)"
                let expr_7430 := convert_t_uint24_to_t_uint16(expr_7429)
                /// @src 31:849:874  "return uint16(self >> 12)"
                var__7423 := expr_7430
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_4095_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_4095_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_4095_by_1(value)))
            }

            /// @ast-id 7418
            /// @src 31:649:763  "function getZeroForOneFee(uint24 self) internal pure returns (uint16) {..."
            function fun_getZeroForOneFee_7418(var_self_7405) -> var__7408 {
                /// @src 31:711:717  "uint16"
                let zero_t_uint16_1738 := zero_value_for_split_t_uint16()
                var__7408 := zero_t_uint16_1738

                /// @src 31:743:747  "self"
                let _1739 := var_self_7405
                let expr_7412 := _1739
                /// @src 31:750:755  "0xfff"
                let expr_7413 := 0x0fff
                /// @src 31:743:755  "self & 0xfff"
                let expr_7414 := and(expr_7412, convert_t_rational_4095_by_1_to_t_uint24(expr_7413))

                /// @src 31:736:756  "uint16(self & 0xfff)"
                let expr_7415 := convert_t_uint24_to_t_uint16(expr_7414)
                /// @src 31:729:756  "return uint16(self & 0xfff)"
                var__7408 := expr_7415
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_4194304_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_4194304_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_4194304_by_1(value)))
            }

            /// @src 24:776:827  "uint24 public constant OVERRIDE_FEE_FLAG = 0x400000"
            function constant_OVERRIDE_FEE_FLAG_3554() -> ret {
                /// @src 24:819:827  "0x400000"
                let expr_3553 := 0x400000
                let _1742 := convert_t_rational_4194304_by_1_to_t_uint24(expr_3553)

                ret := _1742
            }

            /// @ast-id 3645
            /// @src 24:2757:2872  "function isOverride(uint24 self) internal pure returns (bool) {..."
            function fun_isOverride_3645(var_self_3633) -> var__3636 {
                /// @src 24:2813:2817  "bool"
                let zero_t_bool_1740 := zero_value_for_split_t_bool()
                var__3636 := zero_t_bool_1740

                /// @src 24:2836:2840  "self"
                let _1741 := var_self_3633
                let expr_3638 := _1741
                /// @src 24:2843:2860  "OVERRIDE_FEE_FLAG"
                let expr_3639 := constant_OVERRIDE_FEE_FLAG_3554()
                /// @src 24:2836:2860  "self & OVERRIDE_FEE_FLAG"
                let expr_3640 := and(expr_3638, expr_3639)

                /// @src 24:2864:2865  "0"
                let expr_3641 := 0x00
                /// @src 24:2836:2865  "self & OVERRIDE_FEE_FLAG != 0"
                let expr_3642 := iszero(eq(cleanup_t_uint24(expr_3640), convert_t_rational_0_by_1_to_t_uint24(expr_3641)))
                /// @src 24:2829:2865  "return self & OVERRIDE_FEE_FLAG != 0"
                var__3636 := expr_3642
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8692
            /// @src 44:2011:2200  "function lpFee(Slot0 _packed) internal pure returns (uint24 _lpFee) {..."
            function fun_lpFee_8692(var__packed_8685) -> var__lpFee_8688 {
                /// @src 44:2064:2077  "uint24 _lpFee"
                let zero_t_uint24_1743 := zero_value_for_split_t_uint24()
                var__lpFee_8688 := zero_t_uint24_1743

                /// @src 44:2089:2194  "assembly (\"memory-safe\") {..."
                {
                    var__lpFee_8688 := and(16777215, shr(208, var__packed_8685))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 3678
            /// @src 24:3434:3593  "function removeOverrideFlagAndValidate(uint24 self) internal pure returns (uint24 fee) {..."
            function fun_removeOverrideFlagAndValidate_3678(var_self_3661) -> var_fee_3664 {
                /// @src 24:3509:3519  "uint24 fee"
                let zero_t_uint24_1744 := zero_value_for_split_t_uint24()
                var_fee_3664 := zero_t_uint24_1744

                /// @src 24:3537:3541  "self"
                let _1745 := var_self_3661
                let expr_3667 := _1745
                /// @src 24:3537:3560  "self.removeOverrideFlag"
                let expr_3668_self := expr_3667
                /// @src 24:3537:3562  "self.removeOverrideFlag()"
                let expr_3669 := fun_removeOverrideFlag_3658(expr_3668_self)
                /// @src 24:3531:3562  "fee = self.removeOverrideFlag()"
                var_fee_3664 := expr_3669
                let expr_3670 := expr_3669
                /// @src 24:3572:3575  "fee"
                let _1746 := var_fee_3664
                let expr_3672 := _1746
                /// @src 24:3572:3584  "fee.validate"
                let expr_3674_self := expr_3672
                fun_validate_3608(expr_3674_self)

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7454
            /// @src 31:1695:2110  "function calculateSwapFee(uint16 self, uint24 lpFee) internal pure returns (uint24 swapFee) {..."
            function fun_calculateSwapFee_7454(var_self_7445, var_lpFee_7447) -> var_swapFee_7450 {
                /// @src 31:1771:1785  "uint24 swapFee"
                let zero_t_uint24_1747 := zero_value_for_split_t_uint24()
                var_swapFee_7450 := zero_t_uint24_1747

                /// @src 31:1864:2104  "assembly (\"memory-safe\") {..."
                {
                    var_self_7445 := and(var_self_7445, 0xfff)
                    var_lpFee_7447 := and(var_lpFee_7447, 0xffffff)
                    let usr$numerator := mul(var_self_7445, var_lpFee_7447)
                    var_swapFee_7450 := sub(add(var_self_7445, var_lpFee_7447), div(usr$numerator, 1000000))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 2328
            /// @src 19:2423:2841  "function revertWith(bytes4 selector, uint160 value1, uint160 value2) internal pure {..."
            function fun_revertWith_2328(var_selector_2319, var_value1_2321, var_value2_2323) {

                /// @src 19:2516:2835  "assembly (\"memory-safe\") {..."
                {
                    let usr$fmp := mload(0x40)
                    mstore(usr$fmp, var_selector_2319)
                    mstore(add(usr$fmp, 0x04), and(var_value1_2321, 0xffffffffffffffffffffffffffffffffffffffff))
                    mstore(add(usr$fmp, 0x24), and(var_value2_2323, 0xffffffffffffffffffffffffffffffffffffffff))
                    revert(usr$fmp, 0x44)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function increment_wrapping_t_int24(value) -> ret {
                ret := cleanup_t_int24(add(value, 1))
            }

            function convert_t_rational_1_by_1_to_t_uint256(value) -> converted {
                converted := cleanup_t_uint256(identity(cleanup_t_rational_1_by_1(value)))
            }

            function convert_t_int16_to_t_int16(value) -> converted {
                converted := cleanup_t_int16(identity(cleanup_t_int16(value)))
            }

            function mapping_index_access_t_mapping$_t_int16_$_t_uint256_$_of_t_int16(slot , key) -> dataSlot {
                mstore(0, convert_t_int16_to_t_int16(key))
                mstore(0x20, slot)
                dataSlot := keccak256(0, 0x40)
            }

            function wrapping_sub_t_uint8(x, y) -> diff {
                diff := cleanup_t_uint8(sub(x, y))
            }

            function convert_t_uint8_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_uint8(value)))
            }

            function convert_t_uint24_to_t_int24(value) -> converted {
                converted := cleanup_t_int24(identity(cleanup_t_uint24(value)))
            }

            function wrapping_add_t_int24(x, y) -> sum {
                sum := cleanup_t_int24(add(x, y))
            }

            function wrapping_mul_t_int24(x, y) -> product {
                product := cleanup_t_int24(mul(x, y))
            }

            /// @ast-id 8597
            /// @src 35:4256:6263  "function nextInitializedTickWithinOneWord(..."
            function fun_nextInitializedTickWithinOneWord_8597(var_self_8421_slot, var_tick_8423, var_tickSpacing_8425, var_lte_8427) -> var_next_8430, var_initialized_8432 {
                /// @src 35:4440:4450  "int24 next"
                let zero_t_int24_1748 := zero_value_for_split_t_int24()
                var_next_8430 := zero_t_int24_1748
                /// @src 35:4452:4468  "bool initialized"
                let zero_t_bool_1749 := zero_value_for_split_t_bool()
                var_initialized_8432 := zero_t_bool_1749

                /// @src 35:4532:4536  "tick"
                let _1750 := var_tick_8423
                let expr_8437 := _1750
                /// @src 35:4538:4549  "tickSpacing"
                let _1751 := var_tickSpacing_8425
                let expr_8438 := _1751
                /// @src 35:4523:4550  "compress(tick, tickSpacing)"
                let expr_8439 := fun_compress_8390(expr_8437, expr_8438)
                /// @src 35:4504:4550  "int24 compressed = compress(tick, tickSpacing)"
                let var_compressed_8435 := expr_8439
                /// @src 35:4569:4572  "lte"
                let _1752 := var_lte_8427
                let expr_8441 := _1752
                /// @src 35:4565:6247  "if (lte) {..."
                switch expr_8441
                case 0 {
                    /// @src 35:5539:5551  "++compressed"
                    let _1754 := var_compressed_8435
                    let _1753 := increment_wrapping_t_int24(_1754)
                    var_compressed_8435 := _1753
                    let expr_8525 := _1753
                    /// @src 35:5530:5552  "position(++compressed)"
                    let expr_8526_component_1, expr_8526_component_2 := fun_position_8402(expr_8525)
                    /// @src 35:5498:5552  "(int16 wordPos, uint8 bitPos) = position(++compressed)"
                    let var_wordPos_8520 := expr_8526_component_1
                    let var_bitPos_8522 := expr_8526_component_2
                    /// @src 35:5650:5651  "1"
                    let expr_8530 := 0x01
                    /// @src 35:5655:5661  "bitPos"
                    let _1755 := var_bitPos_8522
                    let expr_8531 := _1755
                    /// @src 35:5650:5661  "1 << bitPos"
                    let _1756 := convert_t_rational_1_by_1_to_t_uint256(expr_8530)
                    let expr_8532 :=
                    shift_left_t_uint256_t_uint8(_1756, expr_8531)

                    /// @src 35:5649:5662  "(1 << bitPos)"
                    let expr_8533 := expr_8532
                    /// @src 35:5665:5666  "1"
                    let expr_8534 := 0x01
                    /// @src 35:5649:5666  "(1 << bitPos) - 1"
                    let expr_8535 := wrapping_sub_t_uint256(expr_8533, convert_t_rational_1_by_1_to_t_uint256(expr_8534))

                    /// @src 35:5648:5667  "((1 << bitPos) - 1)"
                    let expr_8536 := expr_8535
                    /// @src 35:5647:5667  "~((1 << bitPos) - 1)"
                    let expr_8537 := cleanup_t_uint256(not(expr_8536))
                    /// @src 35:5632:5667  "uint256 mask = ~((1 << bitPos) - 1)"
                    let var_mask_8529 := expr_8537
                    /// @src 35:5702:5706  "self"
                    let _1757_slot := var_self_8421_slot
                    let expr_8541_slot := _1757_slot
                    /// @src 35:5707:5714  "wordPos"
                    let _1758 := var_wordPos_8520
                    let expr_8542 := _1758
                    /// @src 35:5702:5715  "self[wordPos]"
                    let _1759 := mapping_index_access_t_mapping$_t_int16_$_t_uint256_$_of_t_int16(expr_8541_slot,expr_8542)
                    let _1760 := read_from_storage_split_offset_0_t_uint256(_1759)
                    let expr_8543 := _1760
                    /// @src 35:5718:5722  "mask"
                    let _1761 := var_mask_8529
                    let expr_8544 := _1761
                    /// @src 35:5702:5722  "self[wordPos] & mask"
                    let expr_8545 := and(expr_8543, expr_8544)

                    /// @src 35:5685:5722  "uint256 masked = self[wordPos] & mask"
                    let var_masked_8540 := expr_8545
                    /// @src 35:5869:5875  "masked"
                    let _1762 := var_masked_8540
                    let expr_8548 := _1762
                    /// @src 35:5879:5880  "0"
                    let expr_8549 := 0x00
                    /// @src 35:5869:5880  "masked != 0"
                    let expr_8550 := iszero(eq(cleanup_t_uint256(expr_8548), convert_t_rational_0_by_1_to_t_uint256(expr_8549)))
                    /// @src 35:5855:5880  "initialized = masked != 0"
                    var_initialized_8432 := expr_8550
                    let expr_8551 := expr_8550
                    /// @src 35:6019:6030  "initialized"
                    let _1763 := var_initialized_8432
                    let expr_8554 := _1763
                    /// @src 35:6019:6232  "initialized..."
                    let expr_8590
                    switch expr_8554
                    case 0 {
                        /// @src 35:6165:6175  "compressed"
                        let _1764 := var_compressed_8435
                        let expr_8572 := _1764
                        /// @src 35:6191:6206  "type(uint8).max"
                        let expr_8581 := 255
                        /// @src 35:6209:6215  "bitPos"
                        let _1765 := var_bitPos_8522
                        let expr_8582 := _1765
                        /// @src 35:6191:6215  "type(uint8).max - bitPos"
                        let expr_8583 := wrapping_sub_t_uint8(expr_8581, expr_8582)

                        /// @src 35:6184:6216  "uint24(type(uint8).max - bitPos)"
                        let expr_8584 := convert_t_uint8_to_t_uint24(expr_8583)
                        /// @src 35:6178:6217  "int24(uint24(type(uint8).max - bitPos))"
                        let expr_8585 := convert_t_uint24_to_t_int24(expr_8584)
                        /// @src 35:6165:6217  "compressed + int24(uint24(type(uint8).max - bitPos))"
                        let expr_8586 := wrapping_add_t_int24(expr_8572, expr_8585)

                        /// @src 35:6164:6218  "(compressed + int24(uint24(type(uint8).max - bitPos)))"
                        let expr_8587 := expr_8586
                        /// @src 35:6221:6232  "tickSpacing"
                        let _1766 := var_tickSpacing_8425
                        let expr_8588 := _1766
                        /// @src 35:6164:6232  "(compressed + int24(uint24(type(uint8).max - bitPos))) * tickSpacing"
                        let expr_8589 := wrapping_mul_t_int24(expr_8587, expr_8588)

                        /// @src 35:6019:6232  "initialized..."
                        expr_8590 := expr_8589
                    }
                    default {
                        /// @src 35:6054:6064  "compressed"
                        let _1767 := var_compressed_8435
                        let expr_8555 := _1767
                        /// @src 35:6080:6087  "BitMath"
                        let expr_8560_address := linkersymbol("src/libraries/BitMath.sol:BitMath")
                        /// @src 35:6108:6114  "masked"
                        let _1768 := var_masked_8540
                        let expr_8562 := _1768
                        /// @src 35:6080:6115  "BitMath.leastSignificantBit(masked)"
                        let expr_8563 := fun_leastSignificantBit_8948(expr_8562)
                        /// @src 35:6118:6124  "bitPos"
                        let _1769 := var_bitPos_8522
                        let expr_8564 := _1769
                        /// @src 35:6080:6124  "BitMath.leastSignificantBit(masked) - bitPos"
                        let expr_8565 := wrapping_sub_t_uint8(expr_8563, expr_8564)

                        /// @src 35:6073:6125  "uint24(BitMath.leastSignificantBit(masked) - bitPos)"
                        let expr_8566 := convert_t_uint8_to_t_uint24(expr_8565)
                        /// @src 35:6067:6126  "int24(uint24(BitMath.leastSignificantBit(masked) - bitPos))"
                        let expr_8567 := convert_t_uint24_to_t_int24(expr_8566)
                        /// @src 35:6054:6126  "compressed + int24(uint24(BitMath.leastSignificantBit(masked) - bitPos))"
                        let expr_8568 := wrapping_add_t_int24(expr_8555, expr_8567)

                        /// @src 35:6053:6127  "(compressed + int24(uint24(BitMath.leastSignificantBit(masked) - bitPos)))"
                        let expr_8569 := expr_8568
                        /// @src 35:6130:6141  "tickSpacing"
                        let _1770 := var_tickSpacing_8425
                        let expr_8570 := _1770
                        /// @src 35:6053:6141  "(compressed + int24(uint24(BitMath.leastSignificantBit(masked) - bitPos))) * tickSpacing"
                        let expr_8571 := wrapping_mul_t_int24(expr_8569, expr_8570)

                        /// @src 35:6019:6232  "initialized..."
                        expr_8590 := expr_8571
                    }
                    /// @src 35:6012:6232  "next = initialized..."
                    var_next_8430 := expr_8590
                    let expr_8591 := expr_8590
                    /// @src 35:4565:6247  "if (lte) {..."
                }
                default {
                    /// @src 35:4633:4643  "compressed"
                    let _1771 := var_compressed_8435
                    let expr_8447 := _1771
                    /// @src 35:4624:4644  "position(compressed)"
                    let expr_8448_component_1, expr_8448_component_2 := fun_position_8402(expr_8447)
                    /// @src 35:4592:4644  "(int16 wordPos, uint8 bitPos) = position(compressed)"
                    let var_wordPos_8443 := expr_8448_component_1
                    let var_bitPos_8445 := expr_8448_component_2
                    /// @src 35:4748:4765  "type(uint256).max"
                    let expr_8456 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                    /// @src 35:4778:4793  "type(uint8).max"
                    let expr_8463 := 255
                    /// @src 35:4770:4794  "uint256(type(uint8).max)"
                    let expr_8464 := convert_t_uint8_to_t_uint256(expr_8463)
                    /// @src 35:4797:4803  "bitPos"
                    let _1772 := var_bitPos_8445
                    let expr_8465 := _1772
                    /// @src 35:4770:4803  "uint256(type(uint8).max) - bitPos"
                    let expr_8466 := wrapping_sub_t_uint256(expr_8464, convert_t_uint8_to_t_uint256(expr_8465))

                    /// @src 35:4769:4804  "(uint256(type(uint8).max) - bitPos)"
                    let expr_8467 := expr_8466
                    /// @src 35:4748:4804  "type(uint256).max >> (uint256(type(uint8).max) - bitPos)"
                    let expr_8468 :=
                    shift_right_t_uint256_t_uint256(expr_8456, expr_8467)

                    /// @src 35:4733:4804  "uint256 mask = type(uint256).max >> (uint256(type(uint8).max) - bitPos)"
                    let var_mask_8451 := expr_8468
                    /// @src 35:4839:4843  "self"
                    let _1773_slot := var_self_8421_slot
                    let expr_8472_slot := _1773_slot
                    /// @src 35:4844:4851  "wordPos"
                    let _1774 := var_wordPos_8443
                    let expr_8473 := _1774
                    /// @src 35:4839:4852  "self[wordPos]"
                    let _1775 := mapping_index_access_t_mapping$_t_int16_$_t_uint256_$_of_t_int16(expr_8472_slot,expr_8473)
                    let _1776 := read_from_storage_split_offset_0_t_uint256(_1775)
                    let expr_8474 := _1776
                    /// @src 35:4855:4859  "mask"
                    let _1777 := var_mask_8451
                    let expr_8475 := _1777
                    /// @src 35:4839:4859  "self[wordPos] & mask"
                    let expr_8476 := and(expr_8474, expr_8475)

                    /// @src 35:4822:4859  "uint256 masked = self[wordPos] & mask"
                    let var_masked_8471 := expr_8476
                    /// @src 35:5014:5020  "masked"
                    let _1778 := var_masked_8471
                    let expr_8479 := _1778
                    /// @src 35:5024:5025  "0"
                    let expr_8480 := 0x00
                    /// @src 35:5014:5025  "masked != 0"
                    let expr_8481 := iszero(eq(cleanup_t_uint256(expr_8479), convert_t_rational_0_by_1_to_t_uint256(expr_8480)))
                    /// @src 35:5000:5025  "initialized = masked != 0"
                    var_initialized_8432 := expr_8481
                    let expr_8482 := expr_8481
                    /// @src 35:5164:5175  "initialized"
                    let _1779 := var_initialized_8432
                    let expr_8485 := _1779
                    /// @src 35:5164:5358  "initialized..."
                    let expr_8515
                    switch expr_8485
                    case 0 {
                        /// @src 35:5309:5319  "compressed"
                        let _1780 := var_compressed_8435
                        let expr_8503 := _1780
                        /// @src 35:5335:5341  "bitPos"
                        let _1781 := var_bitPos_8445
                        let expr_8508 := _1781
                        /// @src 35:5328:5342  "uint24(bitPos)"
                        let expr_8509 := convert_t_uint8_to_t_uint24(expr_8508)
                        /// @src 35:5322:5343  "int24(uint24(bitPos))"
                        let expr_8510 := convert_t_uint24_to_t_int24(expr_8509)
                        /// @src 35:5309:5343  "compressed - int24(uint24(bitPos))"
                        let expr_8511 := wrapping_sub_t_int24(expr_8503, expr_8510)

                        /// @src 35:5308:5344  "(compressed - int24(uint24(bitPos)))"
                        let expr_8512 := expr_8511
                        /// @src 35:5347:5358  "tickSpacing"
                        let _1782 := var_tickSpacing_8425
                        let expr_8513 := _1782
                        /// @src 35:5308:5358  "(compressed - int24(uint24(bitPos))) * tickSpacing"
                        let expr_8514 := wrapping_mul_t_int24(expr_8512, expr_8513)

                        /// @src 35:5164:5358  "initialized..."
                        expr_8515 := expr_8514
                    }
                    default {
                        /// @src 35:5199:5209  "compressed"
                        let _1783 := var_compressed_8435
                        let expr_8486 := _1783
                        /// @src 35:5225:5231  "bitPos"
                        let _1784 := var_bitPos_8445
                        let expr_8491 := _1784
                        /// @src 35:5234:5241  "BitMath"
                        let expr_8492_address := linkersymbol("src/libraries/BitMath.sol:BitMath")
                        /// @src 35:5261:5267  "masked"
                        let _1785 := var_masked_8471
                        let expr_8494 := _1785
                        /// @src 35:5234:5268  "BitMath.mostSignificantBit(masked)"
                        let expr_8495 := fun_mostSignificantBit_8932(expr_8494)
                        /// @src 35:5225:5268  "bitPos - BitMath.mostSignificantBit(masked)"
                        let expr_8496 := wrapping_sub_t_uint8(expr_8491, expr_8495)

                        /// @src 35:5218:5269  "uint24(bitPos - BitMath.mostSignificantBit(masked))"
                        let expr_8497 := convert_t_uint8_to_t_uint24(expr_8496)
                        /// @src 35:5212:5270  "int24(uint24(bitPos - BitMath.mostSignificantBit(masked)))"
                        let expr_8498 := convert_t_uint24_to_t_int24(expr_8497)
                        /// @src 35:5199:5270  "compressed - int24(uint24(bitPos - BitMath.mostSignificantBit(masked)))"
                        let expr_8499 := wrapping_sub_t_int24(expr_8486, expr_8498)

                        /// @src 35:5198:5271  "(compressed - int24(uint24(bitPos - BitMath.mostSignificantBit(masked))))"
                        let expr_8500 := expr_8499
                        /// @src 35:5274:5285  "tickSpacing"
                        let _1786 := var_tickSpacing_8425
                        let expr_8501 := _1786
                        /// @src 35:5198:5285  "(compressed - int24(uint24(bitPos - BitMath.mostSignificantBit(masked)))) * tickSpacing"
                        let expr_8502 := wrapping_mul_t_int24(expr_8500, expr_8501)

                        /// @src 35:5164:5358  "initialized..."
                        expr_8515 := expr_8502
                    }
                    /// @src 35:5157:5358  "next = initialized..."
                    var_next_8430 := expr_8515
                    let expr_8516 := expr_8515
                    /// @src 35:4565:6247  "if (lte) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8139
            /// @src 34:1141:2253  "function getSqrtPriceTarget(bool zeroForOne, uint160 sqrtPriceNextX96, uint160 sqrtPriceLimitX96)..."
            function fun_getSqrtPriceTarget_8139(var_zeroForOne_8128, var_sqrtPriceNextX96_8130, var_sqrtPriceLimitX96_8132) -> var_sqrtPriceTargetX96_8135 {
                /// @src 34:1286:1312  "uint160 sqrtPriceTargetX96"
                let zero_t_uint160_1787 := zero_value_for_split_t_uint160()
                var_sqrtPriceTargetX96_8135 := zero_t_uint160_1787

                /// @src 34:1328:2247  "assembly (\"memory-safe\") {..."
                {
                    var_sqrtPriceNextX96_8130 := and(var_sqrtPriceNextX96_8130, 0xffffffffffffffffffffffffffffffffffffffff)
                    var_sqrtPriceLimitX96_8132 := and(var_sqrtPriceLimitX96_8132, 0xffffffffffffffffffffffffffffffffffffffff)
                    let usr$nextOrLimit := xor(lt(var_sqrtPriceNextX96_8130, var_sqrtPriceLimitX96_8132), and(var_zeroForOne_8128, 0x1))
                    let usr$symDiff := xor(var_sqrtPriceNextX96_8130, var_sqrtPriceLimitX96_8132)
                    var_sqrtPriceTargetX96_8135 := xor(var_sqrtPriceLimitX96_8132, mul(usr$symDiff, usr$nextOrLimit))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8365
            /// @src 34:3514:6965  "function computeSwapStep(..."
            function fun_computeSwapStep_8365(var_sqrtPriceCurrentX96_8142, var_sqrtPriceTargetX96_8144, var_liquidity_8146, var_amountRemaining_8148, var_feePips_8150) -> var_sqrtPriceNextX96_8153, var_amountIn_8155, var_amountOut_8157, var_feeAmount_8159 {
                /// @src 34:3724:3748  "uint160 sqrtPriceNextX96"
                let zero_t_uint160_1788 := zero_value_for_split_t_uint160()
                var_sqrtPriceNextX96_8153 := zero_t_uint160_1788
                /// @src 34:3750:3766  "uint256 amountIn"
                let zero_t_uint256_1789 := zero_value_for_split_t_uint256()
                var_amountIn_8155 := zero_t_uint256_1789
                /// @src 34:3768:3785  "uint256 amountOut"
                let zero_t_uint256_1790 := zero_value_for_split_t_uint256()
                var_amountOut_8157 := zero_t_uint256_1790
                /// @src 34:3787:3804  "uint256 feeAmount"
                let zero_t_uint256_1791 := zero_value_for_split_t_uint256()
                var_feeAmount_8159 := zero_t_uint256_1791

                /// @src 34:3859:3866  "feePips"
                let _1792 := var_feePips_8150
                let expr_8163 := _1792
                /// @src 34:3840:3866  "uint256 _feePips = feePips"
                let var__feePips_8162 := convert_t_uint24_to_t_uint256(expr_8163)
                /// @src 34:3923:3942  "sqrtPriceCurrentX96"
                let _1793 := var_sqrtPriceCurrentX96_8142
                let expr_8167 := _1793
                /// @src 34:3946:3964  "sqrtPriceTargetX96"
                let _1794 := var_sqrtPriceTargetX96_8144
                let expr_8168 := _1794
                /// @src 34:3923:3964  "sqrtPriceCurrentX96 >= sqrtPriceTargetX96"
                let expr_8169 := iszero(lt(cleanup_t_uint160(expr_8167), cleanup_t_uint160(expr_8168)))
                /// @src 34:3905:3964  "bool zeroForOne = sqrtPriceCurrentX96 >= sqrtPriceTargetX96"
                let var_zeroForOne_8166 := expr_8169
                /// @src 34:3993:4008  "amountRemaining"
                let _1795 := var_amountRemaining_8148
                let expr_8173 := _1795
                /// @src 34:4011:4012  "0"
                let expr_8174 := 0x00
                /// @src 34:3993:4012  "amountRemaining < 0"
                let expr_8175 := slt(cleanup_t_int256(expr_8173), convert_t_rational_0_by_1_to_t_int256(expr_8174))
                /// @src 34:3978:4012  "bool exactIn = amountRemaining < 0"
                let var_exactIn_8172 := expr_8175
                /// @src 34:4031:4038  "exactIn"
                let _1796 := var_exactIn_8172
                let expr_8177 := _1796
                /// @src 34:4027:6949  "if (exactIn) {..."
                switch expr_8177
                case 0 {
                    /// @src 34:5746:5756  "zeroForOne"
                    let _1797 := var_zeroForOne_8166
                    let expr_8283 := _1797
                    /// @src 34:5746:5978  "zeroForOne..."
                    let expr_8298
                    switch expr_8283
                    case 0 {
                        /// @src 34:5890:5903  "SqrtPriceMath"
                        let expr_8291_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:5920:5939  "sqrtPriceCurrentX96"
                        let _1798 := var_sqrtPriceCurrentX96_8142
                        let expr_8293 := _1798
                        /// @src 34:5941:5959  "sqrtPriceTargetX96"
                        let _1799 := var_sqrtPriceTargetX96_8144
                        let expr_8294 := _1799
                        /// @src 34:5961:5970  "liquidity"
                        let _1800 := var_liquidity_8146
                        let expr_8295 := _1800
                        /// @src 34:5972:5977  "false"
                        let expr_8296 := 0x00
                        /// @src 34:5890:5978  "SqrtPriceMath.getAmount0Delta(sqrtPriceCurrentX96, sqrtPriceTargetX96, liquidity, false)"
                        let expr_8297 := fun_getAmount0Delta_7971(expr_8293, expr_8294, expr_8295, expr_8296)
                        /// @src 34:5746:5978  "zeroForOne..."
                        expr_8298 := expr_8297
                    }
                    default {
                        /// @src 34:5779:5792  "SqrtPriceMath"
                        let expr_8284_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:5809:5827  "sqrtPriceTargetX96"
                        let _1801 := var_sqrtPriceTargetX96_8144
                        let expr_8286 := _1801
                        /// @src 34:5829:5848  "sqrtPriceCurrentX96"
                        let _1802 := var_sqrtPriceCurrentX96_8142
                        let expr_8287 := _1802
                        /// @src 34:5850:5859  "liquidity"
                        let _1803 := var_liquidity_8146
                        let expr_8288 := _1803
                        /// @src 34:5861:5866  "false"
                        let expr_8289 := 0x00
                        /// @src 34:5779:5867  "SqrtPriceMath.getAmount1Delta(sqrtPriceTargetX96, sqrtPriceCurrentX96, liquidity, false)"
                        let expr_8290 := fun_getAmount1Delta_8027(expr_8286, expr_8287, expr_8288, expr_8289)
                        /// @src 34:5746:5978  "zeroForOne..."
                        expr_8298 := expr_8290
                    }
                    /// @src 34:5734:5978  "amountOut = zeroForOne..."
                    var_amountOut_8157 := expr_8298
                    let expr_8299 := expr_8298
                    /// @src 34:6008:6023  "amountRemaining"
                    let _1804 := var_amountRemaining_8148
                    let expr_8303 := _1804
                    /// @src 34:6000:6024  "uint256(amountRemaining)"
                    let expr_8304 := convert_t_int256_to_t_uint256(expr_8303)
                    /// @src 34:6028:6037  "amountOut"
                    let _1805 := var_amountOut_8157
                    let expr_8305 := _1805
                    /// @src 34:6000:6037  "uint256(amountRemaining) >= amountOut"
                    let expr_8306 := iszero(lt(cleanup_t_uint256(expr_8304), cleanup_t_uint256(expr_8305)))
                    /// @src 34:5996:6512  "if (uint256(amountRemaining) >= amountOut) {..."
                    switch expr_8306
                    case 0 {
                        /// @src 34:6317:6332  "amountRemaining"
                        let _1806 := var_amountRemaining_8148
                        let expr_8315 := _1806
                        /// @src 34:6309:6333  "uint256(amountRemaining)"
                        let expr_8316 := convert_t_int256_to_t_uint256(expr_8315)
                        /// @src 34:6297:6333  "amountOut = uint256(amountRemaining)"
                        var_amountOut_8157 := expr_8316
                        let expr_8317 := expr_8316
                        /// @src 34:6398:6411  "SqrtPriceMath"
                        let expr_8320_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:6439:6458  "sqrtPriceCurrentX96"
                        let _1807 := var_sqrtPriceCurrentX96_8142
                        let expr_8322 := _1807
                        /// @src 34:6460:6469  "liquidity"
                        let _1808 := var_liquidity_8146
                        let expr_8323 := _1808
                        /// @src 34:6471:6480  "amountOut"
                        let _1809 := var_amountOut_8157
                        let expr_8324 := _1809
                        /// @src 34:6482:6492  "zeroForOne"
                        let _1810 := var_zeroForOne_8166
                        let expr_8325 := _1810
                        /// @src 34:6398:6493  "SqrtPriceMath.getNextSqrtPriceFromOutput(sqrtPriceCurrentX96, liquidity, amountOut, zeroForOne)"
                        let expr_8326 := fun_getNextSqrtPriceFromOutput_7905(expr_8322, expr_8323, expr_8324, expr_8325)
                        /// @src 34:6355:6493  "sqrtPriceNextX96 =..."
                        var_sqrtPriceNextX96_8153 := expr_8326
                        let expr_8327 := expr_8326
                        /// @src 34:5996:6512  "if (uint256(amountRemaining) >= amountOut) {..."
                    }
                    default {
                        /// @src 34:6145:6163  "sqrtPriceTargetX96"
                        let _1811 := var_sqrtPriceTargetX96_8144
                        let expr_8308 := _1811
                        /// @src 34:6126:6163  "sqrtPriceNextX96 = sqrtPriceTargetX96"
                        var_sqrtPriceNextX96_8153 := expr_8308
                        let expr_8309 := expr_8308
                        /// @src 34:5996:6512  "if (uint256(amountRemaining) >= amountOut) {..."
                    }
                    /// @src 34:6540:6550  "zeroForOne"
                    let _1812 := var_zeroForOne_8166
                    let expr_8332 := _1812
                    /// @src 34:6540:6766  "zeroForOne..."
                    let expr_8347
                    switch expr_8332
                    case 0 {
                        /// @src 34:6681:6694  "SqrtPriceMath"
                        let expr_8340_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:6711:6730  "sqrtPriceCurrentX96"
                        let _1813 := var_sqrtPriceCurrentX96_8142
                        let expr_8342 := _1813
                        /// @src 34:6732:6748  "sqrtPriceNextX96"
                        let _1814 := var_sqrtPriceNextX96_8153
                        let expr_8343 := _1814
                        /// @src 34:6750:6759  "liquidity"
                        let _1815 := var_liquidity_8146
                        let expr_8344 := _1815
                        /// @src 34:6761:6765  "true"
                        let expr_8345 := 0x01
                        /// @src 34:6681:6766  "SqrtPriceMath.getAmount1Delta(sqrtPriceCurrentX96, sqrtPriceNextX96, liquidity, true)"
                        let expr_8346 := fun_getAmount1Delta_8027(expr_8342, expr_8343, expr_8344, expr_8345)
                        /// @src 34:6540:6766  "zeroForOne..."
                        expr_8347 := expr_8346
                    }
                    default {
                        /// @src 34:6573:6586  "SqrtPriceMath"
                        let expr_8333_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:6603:6619  "sqrtPriceNextX96"
                        let _1816 := var_sqrtPriceNextX96_8153
                        let expr_8335 := _1816
                        /// @src 34:6621:6640  "sqrtPriceCurrentX96"
                        let _1817 := var_sqrtPriceCurrentX96_8142
                        let expr_8336 := _1817
                        /// @src 34:6642:6651  "liquidity"
                        let _1818 := var_liquidity_8146
                        let expr_8337 := _1818
                        /// @src 34:6653:6657  "true"
                        let expr_8338 := 0x01
                        /// @src 34:6573:6658  "SqrtPriceMath.getAmount0Delta(sqrtPriceNextX96, sqrtPriceCurrentX96, liquidity, true)"
                        let expr_8339 := fun_getAmount0Delta_7971(expr_8335, expr_8336, expr_8337, expr_8338)
                        /// @src 34:6540:6766  "zeroForOne..."
                        expr_8347 := expr_8339
                    }
                    /// @src 34:6529:6766  "amountIn = zeroForOne..."
                    var_amountIn_8155 := expr_8347
                    let expr_8348 := expr_8347
                    /// @src 34:6864:6872  "FullMath"
                    let expr_8351_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                    /// @src 34:6890:6898  "amountIn"
                    let _1819 := var_amountIn_8155
                    let expr_8353 := _1819
                    /// @src 34:6900:6908  "_feePips"
                    let _1820 := var__feePips_8162
                    let expr_8354 := _1820
                    /// @src 34:6910:6922  "MAX_SWAP_FEE"
                    let expr_8355 := constant_MAX_SWAP_FEE_8125()
                    /// @src 34:6925:6933  "_feePips"
                    let _1821 := var__feePips_8162
                    let expr_8356 := _1821
                    /// @src 34:6910:6933  "MAX_SWAP_FEE - _feePips"
                    let expr_8357 := wrapping_sub_t_uint256(expr_8355, expr_8356)

                    /// @src 34:6864:6934  "FullMath.mulDivRoundingUp(amountIn, _feePips, MAX_SWAP_FEE - _feePips)"
                    let expr_8358 := fun_mulDivRoundingUp_8912(expr_8353, expr_8354, expr_8357)
                    /// @src 34:6852:6934  "feeAmount = FullMath.mulDivRoundingUp(amountIn, _feePips, MAX_SWAP_FEE - _feePips)"
                    var_feeAmount_8159 := expr_8358
                    let expr_8359 := expr_8358
                    /// @src 34:4027:6949  "if (exactIn) {..."
                }
                default {
                    /// @src 34:4111:4119  "FullMath"
                    let expr_8180_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                    /// @src 34:4136:4151  "amountRemaining"
                    let _1822 := var_amountRemaining_8148
                    let expr_8184 := _1822
                    /// @src 34:4135:4151  "-amountRemaining"
                    let expr_8185 := negate_wrapping_t_int256(expr_8184)
                    /// @src 34:4127:4152  "uint256(-amountRemaining)"
                    let expr_8186 := convert_t_int256_to_t_uint256(expr_8185)
                    /// @src 34:4154:4166  "MAX_SWAP_FEE"
                    let expr_8187 := constant_MAX_SWAP_FEE_8125()
                    /// @src 34:4169:4177  "_feePips"
                    let _1823 := var__feePips_8162
                    let expr_8188 := _1823
                    /// @src 34:4154:4177  "MAX_SWAP_FEE - _feePips"
                    let expr_8189 := wrapping_sub_t_uint256(expr_8187, expr_8188)

                    /// @src 34:4179:4191  "MAX_SWAP_FEE"
                    let expr_8190 := constant_MAX_SWAP_FEE_8125()
                    /// @src 34:4111:4192  "FullMath.mulDiv(uint256(-amountRemaining), MAX_SWAP_FEE - _feePips, MAX_SWAP_FEE)"
                    let expr_8191 := fun_mulDiv_8874(expr_8186, expr_8189, expr_8190)
                    /// @src 34:4058:4192  "uint256 amountRemainingLessFee =..."
                    let var_amountRemainingLessFee_8179 := expr_8191
                    /// @src 34:4221:4231  "zeroForOne"
                    let _1824 := var_zeroForOne_8166
                    let expr_8194 := _1824
                    /// @src 34:4221:4451  "zeroForOne..."
                    let expr_8209
                    switch expr_8194
                    case 0 {
                        /// @src 34:4364:4377  "SqrtPriceMath"
                        let expr_8202_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:4394:4413  "sqrtPriceCurrentX96"
                        let _1825 := var_sqrtPriceCurrentX96_8142
                        let expr_8204 := _1825
                        /// @src 34:4415:4433  "sqrtPriceTargetX96"
                        let _1826 := var_sqrtPriceTargetX96_8144
                        let expr_8205 := _1826
                        /// @src 34:4435:4444  "liquidity"
                        let _1827 := var_liquidity_8146
                        let expr_8206 := _1827
                        /// @src 34:4446:4450  "true"
                        let expr_8207 := 0x01
                        /// @src 34:4364:4451  "SqrtPriceMath.getAmount1Delta(sqrtPriceCurrentX96, sqrtPriceTargetX96, liquidity, true)"
                        let expr_8208 := fun_getAmount1Delta_8027(expr_8204, expr_8205, expr_8206, expr_8207)
                        /// @src 34:4221:4451  "zeroForOne..."
                        expr_8209 := expr_8208
                    }
                    default {
                        /// @src 34:4254:4267  "SqrtPriceMath"
                        let expr_8195_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:4284:4302  "sqrtPriceTargetX96"
                        let _1828 := var_sqrtPriceTargetX96_8144
                        let expr_8197 := _1828
                        /// @src 34:4304:4323  "sqrtPriceCurrentX96"
                        let _1829 := var_sqrtPriceCurrentX96_8142
                        let expr_8198 := _1829
                        /// @src 34:4325:4334  "liquidity"
                        let _1830 := var_liquidity_8146
                        let expr_8199 := _1830
                        /// @src 34:4336:4340  "true"
                        let expr_8200 := 0x01
                        /// @src 34:4254:4341  "SqrtPriceMath.getAmount0Delta(sqrtPriceTargetX96, sqrtPriceCurrentX96, liquidity, true)"
                        let expr_8201 := fun_getAmount0Delta_7971(expr_8197, expr_8198, expr_8199, expr_8200)
                        /// @src 34:4221:4451  "zeroForOne..."
                        expr_8209 := expr_8201
                    }
                    /// @src 34:4210:4451  "amountIn = zeroForOne..."
                    var_amountIn_8155 := expr_8209
                    let expr_8210 := expr_8209
                    /// @src 34:4473:4495  "amountRemainingLessFee"
                    let _1831 := var_amountRemainingLessFee_8179
                    let expr_8212 := _1831
                    /// @src 34:4499:4507  "amountIn"
                    let _1832 := var_amountIn_8155
                    let expr_8213 := _1832
                    /// @src 34:4473:4507  "amountRemainingLessFee >= amountIn"
                    let expr_8214 := iszero(lt(cleanup_t_uint256(expr_8212), cleanup_t_uint256(expr_8213)))
                    /// @src 34:4469:5438  "if (amountRemainingLessFee >= amountIn) {..."
                    switch expr_8214
                    case 0 {
                        /// @src 34:5032:5054  "amountRemainingLessFee"
                        let _1833 := var_amountRemainingLessFee_8179
                        let expr_8237 := _1833
                        /// @src 34:5021:5054  "amountIn = amountRemainingLessFee"
                        var_amountIn_8155 := expr_8237
                        let expr_8238 := expr_8237
                        /// @src 34:5095:5108  "SqrtPriceMath"
                        let expr_8241_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:5160:5179  "sqrtPriceCurrentX96"
                        let _1834 := var_sqrtPriceCurrentX96_8142
                        let expr_8243 := _1834
                        /// @src 34:5181:5190  "liquidity"
                        let _1835 := var_liquidity_8146
                        let expr_8244 := _1835
                        /// @src 34:5192:5214  "amountRemainingLessFee"
                        let _1836 := var_amountRemainingLessFee_8179
                        let expr_8245 := _1836
                        /// @src 34:5216:5226  "zeroForOne"
                        let _1837 := var_zeroForOne_8166
                        let expr_8246 := _1837
                        /// @src 34:5095:5248  "SqrtPriceMath.getNextSqrtPriceFromInput(..."
                        let expr_8247 := fun_getNextSqrtPriceFromInput_7874(expr_8243, expr_8244, expr_8245, expr_8246)
                        /// @src 34:5076:5248  "sqrtPriceNextX96 = SqrtPriceMath.getNextSqrtPriceFromInput(..."
                        var_sqrtPriceNextX96_8153 := expr_8247
                        let expr_8248 := expr_8247
                        /// @src 34:5392:5407  "amountRemaining"
                        let _1838 := var_amountRemaining_8148
                        let expr_8253 := _1838
                        /// @src 34:5391:5407  "-amountRemaining"
                        let expr_8254 := negate_wrapping_t_int256(expr_8253)
                        /// @src 34:5383:5408  "uint256(-amountRemaining)"
                        let expr_8255 := convert_t_int256_to_t_uint256(expr_8254)
                        /// @src 34:5411:5419  "amountIn"
                        let _1839 := var_amountIn_8155
                        let expr_8256 := _1839
                        /// @src 34:5383:5419  "uint256(-amountRemaining) - amountIn"
                        let expr_8257 := wrapping_sub_t_uint256(expr_8255, expr_8256)

                        /// @src 34:5371:5419  "feeAmount = uint256(-amountRemaining) - amountIn"
                        var_feeAmount_8159 := expr_8257
                        let expr_8258 := expr_8257
                        /// @src 34:4469:5438  "if (amountRemainingLessFee >= amountIn) {..."
                    }
                    default {
                        /// @src 34:4614:4632  "sqrtPriceTargetX96"
                        let _1840 := var_sqrtPriceTargetX96_8144
                        let expr_8216 := _1840
                        /// @src 34:4595:4632  "sqrtPriceNextX96 = sqrtPriceTargetX96"
                        var_sqrtPriceNextX96_8153 := expr_8216
                        let expr_8217 := expr_8216
                        /// @src 34:4666:4674  "_feePips"
                        let _1841 := var__feePips_8162
                        let expr_8220 := _1841
                        /// @src 34:4678:4690  "MAX_SWAP_FEE"
                        let expr_8221 := constant_MAX_SWAP_FEE_8125()
                        /// @src 34:4666:4690  "_feePips == MAX_SWAP_FEE"
                        let expr_8222 := eq(cleanup_t_uint256(expr_8220), cleanup_t_uint256(expr_8221))
                        /// @src 34:4666:4922  "_feePips == MAX_SWAP_FEE..."
                        let expr_8232
                        switch expr_8222
                        case 0 {
                            /// @src 34:4852:4860  "FullMath"
                            let expr_8224_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                            /// @src 34:4878:4886  "amountIn"
                            let _1842 := var_amountIn_8155
                            let expr_8226 := _1842
                            /// @src 34:4888:4896  "_feePips"
                            let _1843 := var__feePips_8162
                            let expr_8227 := _1843
                            /// @src 34:4898:4910  "MAX_SWAP_FEE"
                            let expr_8228 := constant_MAX_SWAP_FEE_8125()
                            /// @src 34:4913:4921  "_feePips"
                            let _1844 := var__feePips_8162
                            let expr_8229 := _1844
                            /// @src 34:4898:4921  "MAX_SWAP_FEE - _feePips"
                            let expr_8230 := wrapping_sub_t_uint256(expr_8228, expr_8229)

                            /// @src 34:4852:4922  "FullMath.mulDivRoundingUp(amountIn, _feePips, MAX_SWAP_FEE - _feePips)"
                            let expr_8231 := fun_mulDivRoundingUp_8912(expr_8226, expr_8227, expr_8230)
                            /// @src 34:4666:4922  "_feePips == MAX_SWAP_FEE..."
                            expr_8232 := expr_8231
                        }
                        default {
                            /// @src 34:4717:4725  "amountIn"
                            let _1845 := var_amountIn_8155
                            let expr_8223 := _1845
                            /// @src 34:4666:4922  "_feePips == MAX_SWAP_FEE..."
                            expr_8232 := expr_8223
                        }
                        /// @src 34:4654:4922  "feeAmount = _feePips == MAX_SWAP_FEE..."
                        var_feeAmount_8159 := expr_8232
                        let expr_8233 := expr_8232
                        /// @src 34:4469:5438  "if (amountRemainingLessFee >= amountIn) {..."
                    }
                    /// @src 34:5467:5477  "zeroForOne"
                    let _1846 := var_zeroForOne_8166
                    let expr_8263 := _1846
                    /// @src 34:5467:5695  "zeroForOne..."
                    let expr_8278
                    switch expr_8263
                    case 0 {
                        /// @src 34:5609:5622  "SqrtPriceMath"
                        let expr_8271_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:5639:5658  "sqrtPriceCurrentX96"
                        let _1847 := var_sqrtPriceCurrentX96_8142
                        let expr_8273 := _1847
                        /// @src 34:5660:5676  "sqrtPriceNextX96"
                        let _1848 := var_sqrtPriceNextX96_8153
                        let expr_8274 := _1848
                        /// @src 34:5678:5687  "liquidity"
                        let _1849 := var_liquidity_8146
                        let expr_8275 := _1849
                        /// @src 34:5689:5694  "false"
                        let expr_8276 := 0x00
                        /// @src 34:5609:5695  "SqrtPriceMath.getAmount0Delta(sqrtPriceCurrentX96, sqrtPriceNextX96, liquidity, false)"
                        let expr_8277 := fun_getAmount0Delta_7971(expr_8273, expr_8274, expr_8275, expr_8276)
                        /// @src 34:5467:5695  "zeroForOne..."
                        expr_8278 := expr_8277
                    }
                    default {
                        /// @src 34:5500:5513  "SqrtPriceMath"
                        let expr_8264_address := linkersymbol("src/libraries/SqrtPriceMath.sol:SqrtPriceMath")
                        /// @src 34:5530:5546  "sqrtPriceNextX96"
                        let _1850 := var_sqrtPriceNextX96_8153
                        let expr_8266 := _1850
                        /// @src 34:5548:5567  "sqrtPriceCurrentX96"
                        let _1851 := var_sqrtPriceCurrentX96_8142
                        let expr_8267 := _1851
                        /// @src 34:5569:5578  "liquidity"
                        let _1852 := var_liquidity_8146
                        let expr_8268 := _1852
                        /// @src 34:5580:5585  "false"
                        let expr_8269 := 0x00
                        /// @src 34:5500:5586  "SqrtPriceMath.getAmount1Delta(sqrtPriceNextX96, sqrtPriceCurrentX96, liquidity, false)"
                        let expr_8270 := fun_getAmount1Delta_8027(expr_8266, expr_8267, expr_8268, expr_8269)
                        /// @src 34:5467:5695  "zeroForOne..."
                        expr_8278 := expr_8270
                    }
                    /// @src 34:5455:5695  "amountOut = zeroForOne..."
                    var_amountOut_8157 := expr_8278
                    let expr_8279 := expr_8278
                    /// @src 34:4027:6949  "if (exactIn) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5408
            /// @src 29:29541:30032  "function crossTick(State storage self, int24 tick, uint256 feeGrowthGlobal0X128, uint256 feeGrowthGlobal1X128)..."
            function fun_crossTick_5408(var_self_5364_slot, var_tick_5366, var_feeGrowthGlobal0X128_5368, var_feeGrowthGlobal1X128_5370) -> var_liquidityNet_5373 {
                /// @src 29:29686:29705  "int128 liquidityNet"
                let zero_t_int128_1853 := zero_value_for_split_t_int128()
                var_liquidityNet_5373 := zero_t_int128_1853

                /// @src 29:29769:29773  "self"
                let _1854_slot := var_self_5364_slot
                let expr_5378_slot := _1854_slot
                /// @src 29:29769:29779  "self.ticks"
                let _1855 := add(expr_5378_slot, 4)
                let _1856_slot := _1855
                let expr_5379_slot := _1856_slot
                /// @src 29:29780:29784  "tick"
                let _1857 := var_tick_5366
                let expr_5380 := _1857
                /// @src 29:29769:29785  "self.ticks[tick]"
                let _1858 := mapping_index_access_t_mapping$_t_int24_$_t_struct$_TickInfo_$3845_storage_$_of_t_int24(expr_5379_slot,expr_5380)
                let _1859_slot := _1858
                let expr_5381_slot := _1859_slot
                /// @src 29:29745:29785  "TickInfo storage info = self.ticks[tick]"
                let var_info_5377_slot := convert_t_struct$_TickInfo_$3845_storage_to_t_struct$_TickInfo_$3845_storage_ptr(expr_5381_slot)
                /// @src 29:29828:29848  "feeGrowthGlobal0X128"
                let _1860 := var_feeGrowthGlobal0X128_5368
                let expr_5386 := _1860
                /// @src 29:29851:29855  "info"
                let _1861_slot := var_info_5377_slot
                let expr_5387_slot := _1861_slot
                /// @src 29:29851:29877  "info.feeGrowthOutside0X128"
                let _1862 := add(expr_5387_slot, 1)
                let _1863 := read_from_storage_split_offset_0_t_uint256(_1862)
                let expr_5388 := _1863
                /// @src 29:29828:29877  "feeGrowthGlobal0X128 - info.feeGrowthOutside0X128"
                let expr_5389 := wrapping_sub_t_uint256(expr_5386, expr_5388)

                /// @src 29:29799:29803  "info"
                let _1864_slot := var_info_5377_slot
                let expr_5383_slot := _1864_slot
                /// @src 29:29799:29825  "info.feeGrowthOutside0X128"
                let _1865 := add(expr_5383_slot, 1)
                /// @src 29:29799:29877  "info.feeGrowthOutside0X128 = feeGrowthGlobal0X128 - info.feeGrowthOutside0X128"
                update_storage_value_offset_0t_uint256_to_t_uint256(_1865, expr_5389)
                let expr_5390 := expr_5389
                /// @src 29:29920:29940  "feeGrowthGlobal1X128"
                let _1866 := var_feeGrowthGlobal1X128_5370
                let expr_5395 := _1866
                /// @src 29:29943:29947  "info"
                let _1867_slot := var_info_5377_slot
                let expr_5396_slot := _1867_slot
                /// @src 29:29943:29969  "info.feeGrowthOutside1X128"
                let _1868 := add(expr_5396_slot, 2)
                let _1869 := read_from_storage_split_offset_0_t_uint256(_1868)
                let expr_5397 := _1869
                /// @src 29:29920:29969  "feeGrowthGlobal1X128 - info.feeGrowthOutside1X128"
                let expr_5398 := wrapping_sub_t_uint256(expr_5395, expr_5397)

                /// @src 29:29891:29895  "info"
                let _1870_slot := var_info_5377_slot
                let expr_5392_slot := _1870_slot
                /// @src 29:29891:29917  "info.feeGrowthOutside1X128"
                let _1871 := add(expr_5392_slot, 2)
                /// @src 29:29891:29969  "info.feeGrowthOutside1X128 = feeGrowthGlobal1X128 - info.feeGrowthOutside1X128"
                update_storage_value_offset_0t_uint256_to_t_uint256(_1871, expr_5398)
                let expr_5399 := expr_5398
                /// @src 29:29998:30002  "info"
                let _1872_slot := var_info_5377_slot
                let expr_5402_slot := _1872_slot
                /// @src 29:29998:30015  "info.liquidityNet"
                let _1873 := add(expr_5402_slot, 0)
                let _1874 := read_from_storage_split_offset_16_t_int128(_1873)
                let expr_5403 := _1874
                /// @src 29:29983:30015  "liquidityNet = info.liquidityNet"
                var_liquidityNet_5373 := expr_5403
                let expr_5404 := expr_5403

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7983
            /// @src 33:10510:11131  "function absDiff(uint160 a, uint160 b) internal pure returns (uint256 res) {..."
            function fun_absDiff_7983(var_a_7974, var_b_7976) -> var_res_7979 {
                /// @src 33:10572:10583  "uint256 res"
                let zero_t_uint256_1875 := zero_value_for_split_t_uint256()
                var_res_7979 := zero_t_uint256_1875

                /// @src 33:10595:11125  "assembly (\"memory-safe\") {..."
                {
                    let usr$diff := sub(and(var_a_7974, 0xffffffffffffffffffffffffffffffffffffffff), and(var_b_7976, 0xffffffffffffffffffffffffffffffffffffffff))
                    let usr$mask := sar(255, usr$diff)
                    var_res_7979 := xor(usr$mask, add(usr$mask, usr$diff))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function increment_wrapping_t_uint256(value) -> ret {
                ret := cleanup_t_uint256(add(value, 1))
            }

            /// @ast-id 8912
            /// @src 22:5164:5460  "function mulDivRoundingUp(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256 result) {..."
            function fun_mulDivRoundingUp_8912(var_a_8877, var_b_8879, var_denominator_8881) -> var_result_8884 {
                /// @src 22:5256:5270  "uint256 result"
                let zero_t_uint256_1876 := zero_value_for_split_t_uint256()
                var_result_8884 := zero_t_uint256_1876

                /// @src 22:5322:5323  "a"
                let _1877 := var_a_8877
                let expr_8888 := _1877
                /// @src 22:5325:5326  "b"
                let _1878 := var_b_8879
                let expr_8889 := _1878
                /// @src 22:5328:5339  "denominator"
                let _1879 := var_denominator_8881
                let expr_8890 := _1879
                /// @src 22:5315:5340  "mulDiv(a, b, denominator)"
                let expr_8891 := fun_mulDiv_8874(expr_8888, expr_8889, expr_8890)
                /// @src 22:5306:5340  "result = mulDiv(a, b, denominator)"
                var_result_8884 := expr_8891
                let expr_8892 := expr_8891
                /// @src 22:5365:5366  "a"
                let _1880 := var_a_8877
                let expr_8895 := _1880
                /// @src 22:5368:5369  "b"
                let _1881 := var_b_8879
                let expr_8896 := _1881
                /// @src 22:5371:5382  "denominator"
                let _1882 := var_denominator_8881
                let expr_8897 := _1882
                /// @src 22:5358:5383  "mulmod(a, b, denominator)"
                let _1883 := expr_8897
                if iszero(_1883) { panic_error_0x12() }
                let expr_8898 := mulmod(expr_8895, expr_8896, _1883)
                /// @src 22:5387:5388  "0"
                let expr_8899 := 0x00
                /// @src 22:5358:5388  "mulmod(a, b, denominator) != 0"
                let expr_8900 := iszero(eq(cleanup_t_uint256(expr_8898), convert_t_rational_0_by_1_to_t_uint256(expr_8899)))
                /// @src 22:5354:5444  "if (mulmod(a, b, denominator) != 0) {..."
                if expr_8900 {
                    /// @src 22:5416:5424  "++result"
                    let _1885 := var_result_8884
                    let _1884 := increment_wrapping_t_uint256(_1885)
                    var_result_8884 := _1884
                    let expr_8903 := _1884
                    /// @src 22:5427:5428  "0"
                    let expr_8904 := 0x00
                    /// @src 22:5416:5428  "++result > 0"
                    let expr_8905 := gt(cleanup_t_uint256(expr_8903), convert_t_rational_0_by_1_to_t_uint256(expr_8904))
                    /// @src 22:5408:5429  "require(++result > 0)"
                    require_helper(expr_8905)
                    /// @src 22:5354:5444  "if (mulmod(a, b, denominator) != 0) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8613
            /// @src 37:469:650  "function divRoundingUp(uint256 x, uint256 y) internal pure returns (uint256 z) {..."
            function fun_divRoundingUp_8613(var_x_8604, var_y_8606) -> var_z_8609 {
                /// @src 37:537:546  "uint256 z"
                let zero_t_uint256_1886 := zero_value_for_split_t_uint256()
                var_z_8609 := zero_t_uint256_1886

                /// @src 37:558:644  "assembly (\"memory-safe\") {..."
                {
                    var_z_8609 := add(div(var_x_8604, var_y_8606), gt(mod(var_x_8604, var_y_8606), 0))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function cleanup_t_rational_12582911_by_1(value) -> cleaned {
                cleaned := value
            }

            function convert_t_rational_12582911_by_1_to_t_uint24(value) -> converted {
                converted := cleanup_t_uint24(identity(cleanup_t_rational_12582911_by_1(value)))
            }

            /// @src 24:929:983  "uint24 public constant REMOVE_OVERRIDE_MASK = 0xBFFFFF"
            function constant_REMOVE_OVERRIDE_MASK_3558() -> ret {
                /// @src 24:975:983  "0xBFFFFF"
                let expr_3557 := 0xbfffff
                let _1889 := convert_t_rational_12582911_by_1_to_t_uint24(expr_3557)

                ret := _1889
            }

            /// @ast-id 3658
            /// @src 24:3058:3181  "function removeOverrideFlag(uint24 self) internal pure returns (uint24) {..."
            function fun_removeOverrideFlag_3658(var_self_3648) -> var__3651 {
                /// @src 24:3122:3128  "uint24"
                let zero_t_uint24_1887 := zero_value_for_split_t_uint24()
                var__3651 := zero_t_uint24_1887

                /// @src 24:3147:3151  "self"
                let _1888 := var_self_3648
                let expr_3653 := _1888
                /// @src 24:3154:3174  "REMOVE_OVERRIDE_MASK"
                let expr_3654 := constant_REMOVE_OVERRIDE_MASK_3558()
                /// @src 24:3147:3174  "self & REMOVE_OVERRIDE_MASK"
                let expr_3655 := and(expr_3653, expr_3654)

                /// @src 24:3140:3174  "return self & REMOVE_OVERRIDE_MASK"
                var__3651 := expr_3655
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8390
            /// @src 35:636:1248  "function compress(int24 tick, int24 tickSpacing) internal pure returns (int24 compressed) {..."
            function fun_compress_8390(var_tick_8381, var_tickSpacing_8383) -> var_compressed_8386 {
                /// @src 35:708:724  "int24 compressed"
                let zero_t_int24_1890 := zero_value_for_split_t_int24()
                var_compressed_8386 := zero_t_int24_1890

                /// @src 35:846:1242  "assembly (\"memory-safe\") {..."
                {
                    var_tick_8381 := signextend(2, var_tick_8381)
                    var_tickSpacing_8383 := signextend(2, var_tickSpacing_8383)
                    var_compressed_8386 := sub(sdiv(var_tick_8381, var_tickSpacing_8383), slt(smod(var_tick_8381, var_tickSpacing_8383), 0))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function zero_value_for_split_t_int16() -> ret {
                ret := 0
            }

            /// @ast-id 8402
            /// @src 35:1584:1852  "function position(int24 tick) internal pure returns (int16 wordPos, uint8 bitPos) {..."
            function fun_position_8402(var_tick_8393) -> var_wordPos_8396, var_bitPos_8398 {
                /// @src 35:1637:1650  "int16 wordPos"
                let zero_t_int16_1891 := zero_value_for_split_t_int16()
                var_wordPos_8396 := zero_t_int16_1891
                /// @src 35:1652:1664  "uint8 bitPos"
                let zero_t_uint8_1892 := zero_value_for_split_t_uint8()
                var_bitPos_8398 := zero_t_uint8_1892

                /// @src 35:1676:1846  "assembly (\"memory-safe\") {..."
                {
                    var_wordPos_8396 := sar(8, signextend(2, var_tick_8393))
                    var_bitPos_8398 := and(var_tick_8393, 0xff)
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 8948
            /// @src 16:1659:2606  "function leastSignificantBit(uint256 x) internal pure returns (uint8 r) {..."
            function fun_leastSignificantBit_8948(var_x_8935) -> var_r_8938 {
                /// @src 16:1722:1729  "uint8 r"
                let zero_t_uint8_1893 := zero_value_for_split_t_uint8()
                var_r_8938 := zero_t_uint8_1893

                /// @src 16:1749:1750  "x"
                let _1894 := var_x_8935
                let expr_8941 := _1894
                /// @src 16:1753:1754  "0"
                let expr_8942 := 0x00
                /// @src 16:1749:1754  "x > 0"
                let expr_8943 := gt(cleanup_t_uint256(expr_8941), convert_t_rational_0_by_1_to_t_uint256(expr_8942))
                /// @src 16:1741:1755  "require(x > 0)"
                require_helper(expr_8943)
                /// @src 16:1766:2600  "assembly (\"memory-safe\") {..."
                {
                    var_x_8935 := and(var_x_8935, sub(0, var_x_8935))
                    var_r_8938 := shl(5, shr(252, shl(shl(2, shr(250, mul(var_x_8935, 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff))), 0x8040405543005266443200005020610674053026020000107506200176117077)))
                    var_r_8938 := or(var_r_8938, byte(and(div(0xd76453e0, shr(var_r_8938, var_x_8935)), 0x1f), 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405))
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7905
            /// @src 33:7938:8847  "function getNextSqrtPriceFromOutput(uint160 sqrtPX96, uint128 liquidity, uint256 amountOut, bool zeroForOne)..."
            function fun_getNextSqrtPriceFromOutput_7905(var_sqrtPX96_7877, var_liquidity_7879, var_amountOut_7881, var_zeroForOne_7883) -> var__7886 {
                /// @src 33:8094:8101  "uint160"
                let zero_t_uint160_1895 := zero_value_for_split_t_uint160()
                var__7886 := zero_t_uint160_1895

                /// @src 33:8211:8569  "assembly (\"memory-safe\") {..."
                {
                    if or(iszero(and(var_sqrtPX96_7877, 0xffffffffffffffffffffffffffffffffffffffff)), iszero(and(var_liquidity_7879, 0xffffffffffffffffffffffffffffffff)))
                    {
                        mstore(0, 0x4f2461b8)
                        revert(0x1c, 0x04)
                    }
                }
                /// @src 33:8646:8656  "zeroForOne"
                let _1896 := var_zeroForOne_7883
                let expr_7889 := _1896
                /// @src 33:8646:8840  "zeroForOne..."
                let expr_7902
                switch expr_7889
                case 0 {
                    /// @src 33:8802:8810  "sqrtPX96"
                    let _1897 := var_sqrtPX96_7877
                    let expr_7897 := _1897
                    /// @src 33:8812:8821  "liquidity"
                    let _1898 := var_liquidity_7879
                    let expr_7898 := _1898
                    /// @src 33:8823:8832  "amountOut"
                    let _1899 := var_amountOut_7881
                    let expr_7899 := _1899
                    /// @src 33:8834:8839  "false"
                    let expr_7900 := 0x00
                    /// @src 33:8764:8840  "getNextSqrtPriceFromAmount0RoundingUp(sqrtPX96, liquidity, amountOut, false)"
                    let expr_7901 := fun_getNextSqrtPriceFromAmount0RoundingUp_7752(expr_7897, expr_7898, expr_7899, expr_7900)
                    /// @src 33:8646:8840  "zeroForOne..."
                    expr_7902 := expr_7901
                }
                default {
                    /// @src 33:8711:8719  "sqrtPX96"
                    let _1900 := var_sqrtPX96_7877
                    let expr_7891 := _1900
                    /// @src 33:8721:8730  "liquidity"
                    let _1901 := var_liquidity_7879
                    let expr_7892 := _1901
                    /// @src 33:8732:8741  "amountOut"
                    let _1902 := var_amountOut_7881
                    let expr_7893 := _1902
                    /// @src 33:8743:8748  "false"
                    let expr_7894 := 0x00
                    /// @src 33:8671:8749  "getNextSqrtPriceFromAmount1RoundingDown(sqrtPX96, liquidity, amountOut, false)"
                    let expr_7895 := fun_getNextSqrtPriceFromAmount1RoundingDown_7843(expr_7891, expr_7892, expr_7893, expr_7894)
                    /// @src 33:8646:8840  "zeroForOne..."
                    expr_7902 := expr_7895
                }
                /// @src 33:8639:8840  "return zeroForOne..."
                var__7886 := expr_7902
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7874
            /// @src 33:6460:7369  "function getNextSqrtPriceFromInput(uint160 sqrtPX96, uint128 liquidity, uint256 amountIn, bool zeroForOne)..."
            function fun_getNextSqrtPriceFromInput_7874(var_sqrtPX96_7846, var_liquidity_7848, var_amountIn_7850, var_zeroForOne_7852) -> var__7855 {
                /// @src 33:6614:6621  "uint160"
                let zero_t_uint160_1903 := zero_value_for_split_t_uint160()
                var__7855 := zero_t_uint160_1903

                /// @src 33:6731:7089  "assembly (\"memory-safe\") {..."
                {
                    if or(iszero(and(var_sqrtPX96_7846, 0xffffffffffffffffffffffffffffffffffffffff)), iszero(and(var_liquidity_7848, 0xffffffffffffffffffffffffffffffff)))
                    {
                        mstore(0, 0x4f2461b8)
                        revert(0x1c, 0x04)
                    }
                }
                /// @src 33:7172:7182  "zeroForOne"
                let _1904 := var_zeroForOne_7852
                let expr_7858 := _1904
                /// @src 33:7172:7362  "zeroForOne..."
                let expr_7871
                switch expr_7858
                case 0 {
                    /// @src 33:7326:7334  "sqrtPX96"
                    let _1905 := var_sqrtPX96_7846
                    let expr_7866 := _1905
                    /// @src 33:7336:7345  "liquidity"
                    let _1906 := var_liquidity_7848
                    let expr_7867 := _1906
                    /// @src 33:7347:7355  "amountIn"
                    let _1907 := var_amountIn_7850
                    let expr_7868 := _1907
                    /// @src 33:7357:7361  "true"
                    let expr_7869 := 0x01
                    /// @src 33:7286:7362  "getNextSqrtPriceFromAmount1RoundingDown(sqrtPX96, liquidity, amountIn, true)"
                    let expr_7870 := fun_getNextSqrtPriceFromAmount1RoundingDown_7843(expr_7866, expr_7867, expr_7868, expr_7869)
                    /// @src 33:7172:7362  "zeroForOne..."
                    expr_7871 := expr_7870
                }
                default {
                    /// @src 33:7235:7243  "sqrtPX96"
                    let _1908 := var_sqrtPX96_7846
                    let expr_7860 := _1908
                    /// @src 33:7245:7254  "liquidity"
                    let _1909 := var_liquidity_7848
                    let expr_7861 := _1909
                    /// @src 33:7256:7264  "amountIn"
                    let _1910 := var_amountIn_7850
                    let expr_7862 := _1910
                    /// @src 33:7266:7270  "true"
                    let expr_7863 := 0x01
                    /// @src 33:7197:7271  "getNextSqrtPriceFromAmount0RoundingUp(sqrtPX96, liquidity, amountIn, true)"
                    let expr_7864 := fun_getNextSqrtPriceFromAmount0RoundingUp_7752(expr_7860, expr_7861, expr_7862, expr_7863)
                    /// @src 33:7172:7362  "zeroForOne..."
                    expr_7871 := expr_7864
                }
                /// @src 33:7165:7362  "return zeroForOne..."
                var__7855 := expr_7871
                leave

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            function checked_div_t_uint256(x, y) -> r {
                x := cleanup_t_uint256(x)
                y := cleanup_t_uint256(y)
                if iszero(y) { panic_error_0x12() }

                r := div(x, y)
            }

            /// @ast-id 7752
            /// @src 33:1535:3600  "function getNextSqrtPriceFromAmount0RoundingUp(uint160 sqrtPX96, uint128 liquidity, uint256 amount, bool add)..."
            function fun_getNextSqrtPriceFromAmount0RoundingUp_7752(var_sqrtPX96_7648, var_liquidity_7650, var_amount_7652, var_add_7654) -> var__7657 {
                /// @src 33:1692:1699  "uint160"
                let zero_t_uint160_1911 := zero_value_for_split_t_uint160()
                var__7657 := zero_t_uint160_1911

                /// @src 33:1831:1837  "amount"
                let _1912 := var_amount_7652
                let expr_7659 := _1912
                /// @src 33:1841:1842  "0"
                let expr_7660 := 0x00
                /// @src 33:1831:1842  "amount == 0"
                let expr_7661 := eq(cleanup_t_uint256(expr_7659), convert_t_rational_0_by_1_to_t_uint256(expr_7660))
                /// @src 33:1827:1859  "if (amount == 0) return sqrtPX96"
                if expr_7661 {
                    /// @src 33:1851:1859  "sqrtPX96"
                    let _1913 := var_sqrtPX96_7648
                    let expr_7662 := _1913
                    /// @src 33:1844:1859  "return sqrtPX96"
                    var__7657 := expr_7662
                    leave
                    /// @src 33:1827:1859  "if (amount == 0) return sqrtPX96"
                }
                /// @src 33:1898:1907  "liquidity"
                let _1914 := var_liquidity_7650
                let expr_7669 := _1914
                /// @src 33:1890:1908  "uint256(liquidity)"
                let expr_7670 := convert_t_uint128_to_t_uint256(expr_7669)
                /// @src 33:1912:1924  "FixedPoint96"
                let expr_7671_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                /// @src 33:1912:1935  "FixedPoint96.RESOLUTION"
                let expr_7672 := constant_RESOLUTION_9027()
                /// @src 33:1890:1935  "uint256(liquidity) << FixedPoint96.RESOLUTION"
                let expr_7673 :=
                shift_left_t_uint256_t_uint8(expr_7670, expr_7672)

                /// @src 33:1869:1935  "uint256 numerator1 = uint256(liquidity) << FixedPoint96.RESOLUTION"
                let var_numerator1_7666 := expr_7673
                /// @src 33:1950:1953  "add"
                let _1915 := var_add_7654
                let expr_7675 := _1915
                /// @src 33:1946:3594  "if (add) {..."
                switch expr_7675
                case 0 {
                    /// @src 33:2636:2642  "amount"
                    let _1916 := var_amount_7652
                    let expr_7728 := _1916
                    /// @src 33:2645:2653  "sqrtPX96"
                    let _1917 := var_sqrtPX96_7648
                    let expr_7729 := _1917
                    /// @src 33:2636:2653  "amount * sqrtPX96"
                    let expr_7730 := wrapping_mul_t_uint256(expr_7728, convert_t_uint160_to_t_uint256(expr_7729))

                    /// @src 33:2618:2653  "uint256 product = amount * sqrtPX96"
                    let var_product_7727 := expr_7730
                    /// @src 33:2951:3413  "assembly (\"memory-safe\") {..."
                    {
                        if iszero(and(eq(div(var_product_7727, var_amount_7652), and(var_sqrtPX96_7648, 0xffffffffffffffffffffffffffffffffffffffff)), gt(var_numerator1_7666, var_product_7727)))
                        {
                            mstore(0, 0xf5c787f1)
                            revert(0x1c, 0x04)
                        }
                    }
                    /// @src 33:3452:3462  "numerator1"
                    let _1918 := var_numerator1_7666
                    let expr_7735 := _1918
                    /// @src 33:3465:3472  "product"
                    let _1919 := var_product_7727
                    let expr_7736 := _1919
                    /// @src 33:3452:3472  "numerator1 - product"
                    let expr_7737 := wrapping_sub_t_uint256(expr_7735, expr_7736)

                    /// @src 33:3430:3472  "uint256 denominator = numerator1 - product"
                    let var_denominator_7734 := expr_7737
                    /// @src 33:3497:3505  "FullMath"
                    let expr_7739_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                    /// @src 33:3523:3533  "numerator1"
                    let _1920 := var_numerator1_7666
                    let expr_7741 := _1920
                    /// @src 33:3535:3543  "sqrtPX96"
                    let _1921 := var_sqrtPX96_7648
                    let expr_7742 := _1921
                    /// @src 33:3545:3556  "denominator"
                    let _1922 := var_denominator_7734
                    let expr_7743 := _1922
                    /// @src 33:3497:3557  "FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator)"
                    let _1923 := convert_t_uint160_to_t_uint256(expr_7742)
                    let expr_7744 := fun_mulDivRoundingUp_8912(expr_7741, _1923, expr_7743)
                    /// @src 33:3497:3567  "FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator).toUint160"
                    let expr_7745_self := expr_7744
                    /// @src 33:3497:3569  "FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator).toUint160()"
                    let expr_7746 := fun_toUint160_5612(expr_7745_self)
                    /// @src 33:3490:3569  "return FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator).toUint160()"
                    var__7657 := expr_7746
                    leave
                    /// @src 33:1946:3594  "if (add) {..."
                }
                default {
                    /// @src 33:2015:2021  "amount"
                    let _1924 := var_amount_7652
                    let expr_7678 := _1924
                    /// @src 33:2024:2032  "sqrtPX96"
                    let _1925 := var_sqrtPX96_7648
                    let expr_7679 := _1925
                    /// @src 33:2015:2032  "amount * sqrtPX96"
                    let expr_7680 := wrapping_mul_t_uint256(expr_7678, convert_t_uint160_to_t_uint256(expr_7679))

                    /// @src 33:1997:2032  "uint256 product = amount * sqrtPX96"
                    let var_product_7677 := expr_7680
                    /// @src 33:2054:2061  "product"
                    let _1926 := var_product_7677
                    let expr_7682 := _1926
                    /// @src 33:2064:2070  "amount"
                    let _1927 := var_amount_7652
                    let expr_7683 := _1927
                    /// @src 33:2054:2070  "product / amount"
                    let expr_7684 := wrapping_div_t_uint256(expr_7682, expr_7683)

                    /// @src 33:2074:2082  "sqrtPX96"
                    let _1928 := var_sqrtPX96_7648
                    let expr_7685 := _1928
                    /// @src 33:2054:2082  "product / amount == sqrtPX96"
                    let expr_7686 := eq(cleanup_t_uint256(expr_7684), convert_t_uint160_to_t_uint256(expr_7685))
                    /// @src 33:2050:2395  "if (product / amount == sqrtPX96) {..."
                    if expr_7686 {
                        /// @src 33:2128:2138  "numerator1"
                        let _1929 := var_numerator1_7666
                        let expr_7689 := _1929
                        /// @src 33:2141:2148  "product"
                        let _1930 := var_product_7677
                        let expr_7690 := _1930
                        /// @src 33:2128:2148  "numerator1 + product"
                        let expr_7691 := wrapping_add_t_uint256(expr_7689, expr_7690)

                        /// @src 33:2106:2148  "uint256 denominator = numerator1 + product"
                        let var_denominator_7688 := expr_7691
                        /// @src 33:2174:2185  "denominator"
                        let _1931 := var_denominator_7688
                        let expr_7693 := _1931
                        /// @src 33:2189:2199  "numerator1"
                        let _1932 := var_numerator1_7666
                        let expr_7694 := _1932
                        /// @src 33:2174:2199  "denominator >= numerator1"
                        let expr_7695 := iszero(lt(cleanup_t_uint256(expr_7693), cleanup_t_uint256(expr_7694)))
                        /// @src 33:2170:2377  "if (denominator >= numerator1) {..."
                        if expr_7695 {
                            /// @src 33:2293:2301  "FullMath"
                            let expr_7698_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                            /// @src 33:2319:2329  "numerator1"
                            let _1933 := var_numerator1_7666
                            let expr_7700 := _1933
                            /// @src 33:2331:2339  "sqrtPX96"
                            let _1934 := var_sqrtPX96_7648
                            let expr_7701 := _1934
                            /// @src 33:2341:2352  "denominator"
                            let _1935 := var_denominator_7688
                            let expr_7702 := _1935
                            /// @src 33:2293:2353  "FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator)"
                            let _1936 := convert_t_uint160_to_t_uint256(expr_7701)
                            let expr_7703 := fun_mulDivRoundingUp_8912(expr_7700, _1936, expr_7702)
                            /// @src 33:2285:2354  "uint160(FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator))"
                            let expr_7704 := convert_t_uint256_to_t_uint160(expr_7703)
                            /// @src 33:2278:2354  "return uint160(FullMath.mulDivRoundingUp(numerator1, sqrtPX96, denominator))"
                            var__7657 := expr_7704
                            leave
                            /// @src 33:2170:2377  "if (denominator >= numerator1) {..."
                        }
                        /// @src 33:2050:2395  "if (product / amount == sqrtPX96) {..."
                    }
                    /// @src 33:2488:2498  "UnsafeMath"
                    let expr_7713_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                    /// @src 33:2513:2523  "numerator1"
                    let _1937 := var_numerator1_7666
                    let expr_7715 := _1937
                    /// @src 33:2526:2536  "numerator1"
                    let _1938 := var_numerator1_7666
                    let expr_7716 := _1938
                    /// @src 33:2539:2547  "sqrtPX96"
                    let _1939 := var_sqrtPX96_7648
                    let expr_7717 := _1939
                    /// @src 33:2526:2547  "numerator1 / sqrtPX96"
                    let expr_7718 := checked_div_t_uint256(expr_7716, convert_t_uint160_to_t_uint256(expr_7717))

                    /// @src 33:2525:2548  "(numerator1 / sqrtPX96)"
                    let expr_7719 := expr_7718
                    /// @src 33:2551:2557  "amount"
                    let _1940 := var_amount_7652
                    let expr_7720 := _1940
                    /// @src 33:2525:2557  "(numerator1 / sqrtPX96) + amount"
                    let expr_7721 := checked_add_t_uint256(expr_7719, expr_7720)

                    /// @src 33:2488:2558  "UnsafeMath.divRoundingUp(numerator1, (numerator1 / sqrtPX96) + amount)"
                    let expr_7722 := fun_divRoundingUp_8613(expr_7715, expr_7721)
                    /// @src 33:2480:2559  "uint160(UnsafeMath.divRoundingUp(numerator1, (numerator1 / sqrtPX96) + amount))"
                    let expr_7723 := convert_t_uint256_to_t_uint160(expr_7722)
                    /// @src 33:2473:2559  "return uint160(UnsafeMath.divRoundingUp(numerator1, (numerator1 / sqrtPX96) + amount))"
                    var__7657 := expr_7723
                    leave
                    /// @src 33:1946:3594  "if (add) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 7843
            /// @src 33:4438:5888  "function getNextSqrtPriceFromAmount1RoundingDown(uint160 sqrtPX96, uint128 liquidity, uint256 amount, bool add)..."
            function fun_getNextSqrtPriceFromAmount1RoundingDown_7843(var_sqrtPX96_7755, var_liquidity_7757, var_amount_7759, var_add_7761) -> var__7764 {
                /// @src 33:4597:4604  "uint160"
                let zero_t_uint160_1941 := zero_value_for_split_t_uint160()
                var__7764 := zero_t_uint160_1941

                /// @src 33:4778:4781  "add"
                let _1942 := var_add_7761
                let expr_7766 := _1942
                /// @src 33:4774:5882  "if (add) {..."
                switch expr_7766
                case 0 {
                    /// @src 33:5152:5158  "amount"
                    let _1943 := var_amount_7759
                    let expr_7806 := _1943
                    /// @src 33:5162:5179  "type(uint160).max"
                    let expr_7811 := 0xffffffffffffffffffffffffffffffffffffffff
                    /// @src 33:5152:5179  "amount <= type(uint160).max"
                    let expr_7812 := iszero(gt(cleanup_t_uint256(expr_7806), convert_t_uint160_to_t_uint256(expr_7811)))
                    /// @src 33:5152:5357  "amount <= type(uint160).max..."
                    let expr_7828
                    switch expr_7812
                    case 0 {
                        /// @src 33:5295:5303  "FullMath"
                        let expr_7821_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                        /// @src 33:5321:5327  "amount"
                        let _1944 := var_amount_7759
                        let expr_7823 := _1944
                        /// @src 33:5329:5341  "FixedPoint96"
                        let expr_7824_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                        /// @src 33:5329:5345  "FixedPoint96.Q96"
                        let expr_7825 := constant_Q96_9030()
                        /// @src 33:5347:5356  "liquidity"
                        let _1945 := var_liquidity_7757
                        let expr_7826 := _1945
                        /// @src 33:5295:5357  "FullMath.mulDivRoundingUp(amount, FixedPoint96.Q96, liquidity)"
                        let _1946 := convert_t_uint128_to_t_uint256(expr_7826)
                        let expr_7827 := fun_mulDivRoundingUp_8912(expr_7823, expr_7825, _1946)
                        /// @src 33:5152:5357  "amount <= type(uint160).max..."
                        expr_7828 := expr_7827
                    }
                    default {
                        /// @src 33:5202:5212  "UnsafeMath"
                        let expr_7813_address := linkersymbol("src/libraries/UnsafeMath.sol:UnsafeMath")
                        /// @src 33:5227:5233  "amount"
                        let _1947 := var_amount_7759
                        let expr_7815 := _1947
                        /// @src 33:5237:5249  "FixedPoint96"
                        let expr_7816_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                        /// @src 33:5237:5260  "FixedPoint96.RESOLUTION"
                        let expr_7817 := constant_RESOLUTION_9027()
                        /// @src 33:5227:5260  "amount << FixedPoint96.RESOLUTION"
                        let expr_7818 :=
                        shift_left_t_uint256_t_uint8(expr_7815, expr_7817)

                        /// @src 33:5262:5271  "liquidity"
                        let _1948 := var_liquidity_7757
                        let expr_7819 := _1948
                        /// @src 33:5202:5272  "UnsafeMath.divRoundingUp(amount << FixedPoint96.RESOLUTION, liquidity)"
                        let _1949 := convert_t_uint128_to_t_uint256(expr_7819)
                        let expr_7820 := fun_divRoundingUp_8613(expr_7818, _1949)
                        /// @src 33:5152:5357  "amount <= type(uint160).max..."
                        expr_7828 := expr_7820
                    }
                    /// @src 33:5134:5371  "(..."
                    let expr_7829 := expr_7828
                    /// @src 33:5115:5371  "uint256 quotient = (..."
                    let var_quotient_7805 := expr_7829
                    /// @src 33:5468:5745  "assembly (\"memory-safe\") {..."
                    {
                        if iszero(gt(and(var_sqrtPX96_7755, 0xffffffffffffffffffffffffffffffffffffffff), var_quotient_7805))
                        {
                            mstore(0, 0x4323a555)
                            revert(0x1c, 0x04)
                        }
                    }
                    /// @src 33:5837:5845  "sqrtPX96"
                    let _1950 := var_sqrtPX96_7755
                    let expr_7834 := _1950
                    /// @src 33:5848:5856  "quotient"
                    let _1951 := var_quotient_7805
                    let expr_7835 := _1951
                    /// @src 33:5837:5856  "sqrtPX96 - quotient"
                    let expr_7836 := wrapping_sub_t_uint256(convert_t_uint160_to_t_uint256(expr_7834), expr_7835)

                    /// @src 33:5829:5857  "uint160(sqrtPX96 - quotient)"
                    let expr_7837 := convert_t_uint256_to_t_uint160(expr_7836)
                    /// @src 33:5822:5857  "return uint160(sqrtPX96 - quotient)"
                    var__7764 := expr_7837
                    leave
                    /// @src 33:4774:5882  "if (add) {..."
                }
                default {
                    /// @src 33:4834:4840  "amount"
                    let _1952 := var_amount_7759
                    let expr_7769 := _1952
                    /// @src 33:4844:4861  "type(uint160).max"
                    let expr_7774 := 0xffffffffffffffffffffffffffffffffffffffff
                    /// @src 33:4834:4861  "amount <= type(uint160).max"
                    let expr_7775 := iszero(gt(cleanup_t_uint256(expr_7769), convert_t_uint160_to_t_uint256(expr_7774)))
                    /// @src 33:4834:5006  "amount <= type(uint160).max..."
                    let expr_7790
                    switch expr_7775
                    case 0 {
                        /// @src 33:4954:4962  "FullMath"
                        let expr_7783_address := linkersymbol("src/libraries/FullMath.sol:FullMath")
                        /// @src 33:4970:4976  "amount"
                        let _1953 := var_amount_7759
                        let expr_7785 := _1953
                        /// @src 33:4978:4990  "FixedPoint96"
                        let expr_7786_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                        /// @src 33:4978:4994  "FixedPoint96.Q96"
                        let expr_7787 := constant_Q96_9030()
                        /// @src 33:4996:5005  "liquidity"
                        let _1954 := var_liquidity_7757
                        let expr_7788 := _1954
                        /// @src 33:4954:5006  "FullMath.mulDiv(amount, FixedPoint96.Q96, liquidity)"
                        let _1955 := convert_t_uint128_to_t_uint256(expr_7788)
                        let expr_7789 := fun_mulDiv_8874(expr_7785, expr_7787, _1955)
                        /// @src 33:4834:5006  "amount <= type(uint160).max..."
                        expr_7790 := expr_7789
                    }
                    default {
                        /// @src 33:4885:4891  "amount"
                        let _1956 := var_amount_7759
                        let expr_7776 := _1956
                        /// @src 33:4895:4907  "FixedPoint96"
                        let expr_7777_address := linkersymbol("src/libraries/FixedPoint96.sol:FixedPoint96")
                        /// @src 33:4895:4918  "FixedPoint96.RESOLUTION"
                        let expr_7778 := constant_RESOLUTION_9027()
                        /// @src 33:4885:4918  "amount << FixedPoint96.RESOLUTION"
                        let expr_7779 :=
                        shift_left_t_uint256_t_uint8(expr_7776, expr_7778)

                        /// @src 33:4884:4919  "(amount << FixedPoint96.RESOLUTION)"
                        let expr_7780 := expr_7779
                        /// @src 33:4922:4931  "liquidity"
                        let _1957 := var_liquidity_7757
                        let expr_7781 := _1957
                        /// @src 33:4884:4931  "(amount << FixedPoint96.RESOLUTION) / liquidity"
                        let expr_7782 := checked_div_t_uint256(expr_7780, convert_t_uint128_to_t_uint256(expr_7781))

                        /// @src 33:4834:5006  "amount <= type(uint160).max..."
                        expr_7790 := expr_7782
                    }
                    /// @src 33:4816:5020  "(..."
                    let expr_7791 := expr_7790
                    /// @src 33:4797:5020  "uint256 quotient = (..."
                    let var_quotient_7768 := expr_7791
                    /// @src 33:5051:5059  "sqrtPX96"
                    let _1958 := var_sqrtPX96_7755
                    let expr_7795 := _1958
                    /// @src 33:5043:5060  "uint256(sqrtPX96)"
                    let expr_7796 := convert_t_uint160_to_t_uint256(expr_7795)
                    /// @src 33:5063:5071  "quotient"
                    let _1959 := var_quotient_7768
                    let expr_7797 := _1959
                    /// @src 33:5043:5071  "uint256(sqrtPX96) + quotient"
                    let expr_7798 := checked_add_t_uint256(expr_7796, expr_7797)

                    /// @src 33:5042:5072  "(uint256(sqrtPX96) + quotient)"
                    let expr_7799 := expr_7798
                    /// @src 33:5042:5082  "(uint256(sqrtPX96) + quotient).toUint160"
                    let expr_7800_self := expr_7799
                    /// @src 33:5042:5084  "(uint256(sqrtPX96) + quotient).toUint160()"
                    let expr_7801 := fun_toUint160_5612(expr_7800_self)
                    /// @src 33:5035:5084  "return (uint256(sqrtPX96) + quotient).toUint160()"
                    var__7764 := expr_7801
                    leave
                    /// @src 33:4774:5882  "if (add) {..."
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

            /// @ast-id 5612
            /// @src 32:460:615  "function toUint160(uint256 x) internal pure returns (uint160 y) {..."
            function fun_toUint160_5612(var_x_5588) -> var_y_5591 {
                /// @src 32:513:522  "uint160 y"
                let zero_t_uint160_1960 := zero_value_for_split_t_uint160()
                var_y_5591 := zero_t_uint160_1960

                /// @src 32:546:547  "x"
                let _1961 := var_x_5588
                let expr_5596 := _1961
                /// @src 32:538:548  "uint160(x)"
                let expr_5597 := convert_t_uint256_to_t_uint160(expr_5596)
                /// @src 32:534:548  "y = uint160(x)"
                var_y_5591 := expr_5597
                let expr_5598 := expr_5597
                /// @src 32:562:563  "y"
                let _1962 := var_y_5591
                let expr_5600 := _1962
                /// @src 32:567:568  "x"
                let _1963 := var_x_5588
                let expr_5601 := _1963
                /// @src 32:562:568  "y != x"
                let expr_5602 := iszero(eq(convert_t_uint160_to_t_uint256(expr_5600), cleanup_t_uint256(expr_5601)))
                /// @src 32:558:608  "if (y != x) SafeCastOverflow.selector.revertWith()"
                if expr_5602 {
                    /// @src 32:570:595  "SafeCastOverflow.selector"
                    let expr_5606 := 0x93dafdf100000000000000000000000000000000000000000000000000000000
                    /// @src 32:570:606  "SafeCastOverflow.selector.revertWith"
                    let expr_5607_self := expr_5606
                    fun_revertWith_2274(expr_5607_self)
                    /// @src 32:558:608  "if (y != x) SafeCastOverflow.selector.revertWith()"
                }

            }
            /// @src 6:4791:17612  "contract PoolManager is IPoolManager, ProtocolFees, NoDelegateCall, ERC6909Claims, Extsload, Exttload {..."

        }

        data ".metadata" hex"a164736f6c634300081a000a"
    }

}

