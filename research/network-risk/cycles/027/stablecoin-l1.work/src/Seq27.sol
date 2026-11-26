// SPDX-License-Identifier: UNLICENSED
// Cycle 27 copy of the cycle 26 driver (L-1126). Two changes only: step outputs are kept in the driver's transient
// storage instead of a storage array (Tempo charges 245,000 gas upfront for every zero to nonzero SSTORE, TIP-1060),
// and in mode 7 the second CREATE2 runs in a self-call with bounded gas, so its address collision does not consume
// the gas of the whole step. Everything the PoolManager is asked to do is unchanged.
// Read-only sequence driver for theme-stateful-interpreter (cycle 26). It runs only inside eth_call with state
// overrides, or in the reference interpreter. All currencies are token doubles (Tok behind a forwarder) placed by
// override; the driver mints them at will. Nothing here is deployed and no transaction is sent.
// One eth_call runs many unlock steps one after another, so interpreter state that lives for one EVM instance
// (a MULMOD memo, a per-frame read cache, a code cache) sees the whole history of the call.
pragma solidity 0.8.26;

struct PoolKey {
    address currency0;
    address currency1;
    uint24 fee;
    int24 tickSpacing;
    address hooks;
}

struct MLP {
    int24 tickLower;
    int24 tickUpper;
    int256 liquidityDelta;
    bytes32 salt;
}

struct SP {
    bool zeroForOne;
    int256 amountSpecified;
    uint160 sqrtPriceLimitX96;
}

interface IPM {
    function unlock(bytes calldata) external returns (bytes memory);
    function initialize(PoolKey memory, uint160) external returns (int24);
    function modifyLiquidity(PoolKey memory, MLP memory, bytes calldata) external returns (int256, int256);
    function swap(PoolKey memory, SP memory, bytes calldata) external returns (int256);
    function sync(address) external;
    function take(address, address, uint256) external;
    function settle() external payable returns (uint256);
    function mint(address, uint256, uint256) external;
    function burn(address, uint256, uint256) external;
    function extsload(bytes32) external view returns (bytes32);
    function exttload(bytes32) external view returns (bytes32);
}

interface ITok {
    function mint(address, uint256) external;
    function balanceOf(address) external view returns (uint256);
}

contract Tok {
    mapping(address => uint256) public balanceOf;

    function mint(address to, uint256 a) external {
        balanceOf[to] += a;
    }

    function transfer(address to, uint256 a) external returns (bool) {
        balanceOf[msg.sender] -= a;
        balanceOf[to] += a;
        return true;
    }

    function transferFrom(address f, address to, uint256 a) external returns (bool) {
        balanceOf[f] -= a;
        balanceOf[to] += a;
        return true;
    }
}

library L {
    IPM constant PM = IPM(0xA11Ce5A11Ce5a11ce5A11cE5a11CE5A11CE5A11c); // replaced in the bytecode per network
    int24 constant TL = -887220;
    int24 constant TU = 887220;
    uint256 constant I128 = uint256(uint128(type(int128).max));

    function slot(address target, address cur) internal pure returns (bytes32) {
        return keccak256(abi.encode(target, cur));
    }

    function delta(address target, address cur) internal view returns (int256) {
        return int256(uint256(PM.exttload(slot(target, cur))));
    }

    function pay(address cur, uint256 a) internal {
        while (a > 0) {
            uint256 k = a > I128 ? I128 : a;
            PM.sync(cur);
            ITok(cur).mint(address(PM), k);
            PM.settle();
            a -= k;
        }
    }

    function settleAll(address cur) internal {
        int256 d = delta(address(this), cur);
        if (d < 0) {
            pay(cur, uint256(-d));
        } else if (d > 0) {
            uint256 a = uint256(d);
            while (a > 0) {
                uint256 k = a > I128 ? I128 : a;
                PM.take(cur, address(this), k);
                a -= k;
            }
        }
    }

    function poolSlot(PoolKey memory key) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(keccak256(abi.encode(key)), bytes32(uint256(6))));
    }
}

/// Hook double for the nested write of sequence (c): its afterSwap swaps the same pool again in the opposite
/// direction by a fixed amount (a write to slot0 made inside the hook frame) and settles its own deltas.
contract Hk {
    function afterSwap(address sender, PoolKey calldata key, SP calldata p, int256, bytes calldata)
        external
        returns (bytes4, int128)
    {
        require(msg.sender == address(L.PM));
        if (sender != address(this)) {
            SP memory q = SP(!p.zeroForOne, -int256(1e18), p.zeroForOne ? 1461446703485210103287273052203988822378723970341 : 4295128740);
            L.PM.swap(key, q, "");
            _settle(key.currency0);
            _settle(key.currency1);
        }
        return (Hk.afterSwap.selector, 0);
    }

    function _settle(address cur) internal {
        int256 d = L.delta(address(this), cur);
        if (d < 0) L.pay(cur, uint256(-d));
        else if (d > 0) L.PM.take(cur, address(this), uint256(d));
    }
}

/// Hook double for sequence c2 (finding F-147 shape): its beforeSwap swaps the same pool in the opposite direction
/// (a slot0 write in a nested frame) after the PoolManager frame has already read slot0 at checkPoolInitialized and
/// before Pool.swap reads it again.
contract Hk2 {
    function beforeSwap(address sender, PoolKey calldata key, SP calldata p, bytes calldata)
        external
        returns (bytes4, int256, uint24)
    {
        require(msg.sender == address(L.PM));
        if (sender != address(this)) {
            SP memory q = SP(!p.zeroForOne, -int256(3e19), p.zeroForOne ? 1461446703485210103287273052203988822378723970341 : 4295128740);
            L.PM.swap(key, q, "");
            _settle(key.currency0);
            _settle(key.currency1);
        }
        return (Hk2.beforeSwap.selector, 0, 0);
    }

    function _settle(address cur) internal {
        int256 d = L.delta(address(this), cur);
        if (d < 0) L.pay(cur, uint256(-d));
        else if (d > 0) L.PM.take(cur, address(this), uint256(d));
    }
}

/// Two runtimes for sequence (e). Each records which one ran in the factory's storage.
contract HkA {
    function afterSwap(address, PoolKey calldata, SP calldata, int256, bytes calldata) external returns (bytes4, int128) {
        Seq(0x00000000000000000000000000000000d0d04000).mark(0xA);
        return (HkA.afterSwap.selector, 0);
    }

    function kill() external {
        selfdestruct(payable(msg.sender));
    }
}

contract HkB {
    function afterSwap(address, PoolKey calldata, SP calldata, int256, bytes calldata) external returns (bytes4, int128) {
        Seq(0x00000000000000000000000000000000d0d04000).mark(0xB);
        return (HkB.afterSwap.selector, 0);
    }
}

/// Constant init code whose runtime is whatever the factory hands out at that moment.
contract Meta {
    constructor() {
        bytes memory c = Seq(msg.sender).nextCode();
        assembly {
            return(add(c, 32), mload(c))
        }
    }
}

contract Seq {
    bytes internal next;
    uint256 public lastMark;

    function mark(uint256 v) external {
        lastMark = v;
    }

    function nextCode() external view returns (bytes memory) {
        return next;
    }

    uint256 internal constant OUTN = 0xff00;

    function _p(uint256 v) internal {
        assembly {
            let n := tload(OUTN)
            tstore(add(add(OUTN, 1), n), v)
            tstore(OUTN, add(n, 1))
        }
    }

    function _outWords() internal view returns (uint256[] memory w) {
        uint256 n;
        assembly {
            n := tload(OUTN)
        }
        w = new uint256[](n);
        for (uint256 j = 0; j < n; j++) {
            uint256 v;
            assembly {
                v := tload(add(add(OUTN, 1), j))
            }
            w[j] = v;
        }
    }

    function create2Bounded(bytes memory init, bytes32 salt) external returns (address h) {
        require(msg.sender == address(this));
        assembly {
            h := create2(0, add(init, 32), mload(init), salt)
        }
    }

    /// Each step is abi.encode(uint256 mode, bytes args) and runs as one unlock. Returns abi.encode(ok, words or revert data).
    function run(bytes[] calldata steps) external returns (bytes[] memory res) {
        res = new bytes[](steps.length);
        for (uint256 i = 0; i < steps.length; i++) {
            assembly {
                tstore(OUTN, 0)
            }
            (bool ok, bytes memory ret) = address(L.PM).call(abi.encodeCall(IPM.unlock, (steps[i])));
            res[i] = ok ? abi.encode(true, _outWords()) : abi.encode(false, ret);
        }
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(L.PM));
        (uint256 mode, bytes memory a) = abi.decode(data, (uint256, bytes));
        if (mode == 1) _setup(a);
        else if (mode == 2) _swaps(a, false);
        else if (mode == 3) _swaps(a, true); // swaps then revert the whole unlock
        else if (mode == 4) _inner(a);
        else if (mode == 5) _slots(a);
        else if (mode == 6) _trans(a);
        else if (mode == 7) _meta(a);
        return "";
    }

    // mode 1: (t0, t1, uint24[] fee, int24[] ts, uint256[] liq, uint160 sqrtP, address hooks)
    function _setup(bytes memory a) internal {
        (address t0, address t1, uint24[] memory fee, int24[] memory ts, uint256[] memory liq, uint160 sp, address hk) =
            abi.decode(a, (address, address, uint24[], int24[], uint256[], uint160, address));
        for (uint256 i = 0; i < fee.length; i++) {
            PoolKey memory k = PoolKey(t0, t1, fee[i], ts[i], hk);
            int24 t = L.PM.initialize(k, sp);
            _p(uint256(int256(t)));
            int24 lo = (L.TL / ts[i]) * ts[i];
            int24 hi = (L.TU / ts[i]) * ts[i];
            (int256 d,) = L.PM.modifyLiquidity(k, MLP(lo, hi, int256(liq[i]), 0), "");
            _p(uint256(d));
        }
        L.settleAll(t0);
        L.settleAll(t1);
    }

    // mode 2/3: (t0, t1, uint24[] fee, int24[] ts, bool[] zfo, int256[] amt). Records each swap delta and slot0.
    function _swaps(bytes memory a, bool rev) internal {
        (address t0, address t1, uint24[] memory fee, int24[] memory ts, bool[] memory zfo, int256[] memory amt) =
            abi.decode(a, (address, address, uint24[], int24[], bool[], int256[]));
        for (uint256 i = 0; i < fee.length; i++) {
            PoolKey memory k = PoolKey(t0, t1, fee[i], ts[i], address(0));
            _p(uint256(_swap(k, zfo[i], amt[i])));
            _p(uint256(L.PM.extsload(L.poolSlot(k))));
        }
        L.settleAll(t0);
        L.settleAll(t1);
        if (rev) revert("rev");
    }

    function _swap(PoolKey memory k, bool z, int256 amt) internal returns (int256) {
        return L.PM.swap(k, SP(z, amt, z ? 4295128740 : 1461446703485210103287273052203988822378723970341), "");
    }

    /// Called through this.innerSwap from inside an unlock: swaps one pool and reverts, so the frame is rolled back.
    function innerSwap(PoolKey memory k, bool z, int256 amt) external {
        require(msg.sender == address(this));
        int256 d = _swap(k, z, amt);
        bytes32 s0 = L.PM.extsload(L.poolSlot(k));
        assembly {
            mstore(0, d)
            mstore(32, s0)
            revert(0, 64)
        }
    }

    // mode 4: (PoolKey A1, PoolKey A2, PoolKey B, bool z, int256 amt, bool zB, int256 amtB)
    // swap A1, inner reverted swap on B, swap A2 (A1 and A2 are identical pools on different currencies).
    function _inner(bytes memory a) internal {
        (PoolKey memory a1, PoolKey memory a2, PoolKey memory b, bool z, int256 amt, bool zb, int256 amtb) =
            abi.decode(a, (PoolKey, PoolKey, PoolKey, bool, int256, bool, int256));
        _p(uint256(_swap(a1, z, amt)));
        bytes32 bBefore = L.PM.extsload(L.poolSlot(b));
        (bool ok, bytes memory r) = address(this).call(abi.encodeCall(Seq.innerSwap, (b, zb, amtb)));
        _p(ok ? 1 : 0);
        _p(r.length >= 32 ? uint256(bytes32(r)) : 0);
        _p(uint256(L.PM.extsload(L.poolSlot(b))) == uint256(bBefore) ? 1 : 0);
        _p(uint256(_swap(a2, z, amt)));
        _p(L.delta(address(this), b.currency0) == 0 ? 1 : 0);
        L.settleAll(a1.currency0);
        L.settleAll(a1.currency1);
        L.settleAll(a2.currency0);
        L.settleAll(a2.currency1);
    }

    // mode 5: (PoolKey plain, PoolKey hooked) reads of pool words around writes.
    function _slots(bytes memory a) internal {
        (PoolKey memory k, PoolKey memory h) = abi.decode(a, (PoolKey, PoolKey));
        bytes32 ps = L.poolSlot(k);
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(ps) + j)))); // before
        _p(uint256(_swap(k, true, -1e20)));
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(ps) + j)))); // after write
        (, bytes memory r) = address(this).call(abi.encodeCall(Seq.innerSwap, (k, false, -3e20)));
        _p(r.length >= 64 ? uint256(bytes32(r)) : 0);
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(ps) + j)))); // after reverted write
        bytes32 hs = L.poolSlot(h);
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(hs) + j))));
        _p(uint256(_swap(h, true, -1e20))); // the hook swaps the same pool back inside afterSwap
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(hs) + j)))); // after nested write
        _p(uint256(_swap(k, false, -1e20)));
        for (uint256 j = 0; j < 4; j++) _p(uint256(L.PM.extsload(bytes32(uint256(ps) + j))));
        L.settleAll(k.currency0);
        L.settleAll(k.currency1);
        L.settleAll(h.currency0);
        L.settleAll(h.currency1);
    }

    /// Inside an unlock: mints claims of one currency (a transient write), reads it back, and reverts.
    function innerMint(address cur, uint256 amt) external {
        require(msg.sender == address(this));
        L.PM.mint(address(this), uint256(uint160(cur)), amt);
        bytes32 v = L.PM.exttload(L.slot(address(this), cur));
        bytes32 c = L.PM.exttload(0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b);
        assembly {
            mstore(0, v)
            mstore(32, c)
            revert(0, 64)
        }
    }

    // mode 6: (uint256 base, uint256 n, uint256 seed) transient deltas of n currencies.
    function _trans(bytes memory a) internal {
        (uint256 base, uint256 n, uint256 seed) = abi.decode(a, (uint256, uint256, uint256));
        bytes32 NZ = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b;
        uint256 bad;
        for (uint256 i = 0; i < n; i++) {
            address cur = address(uint160(base + i));
            uint256 amt = uint256(keccak256(abi.encode(seed, i))) % (1 << 120) + 1;
            L.PM.mint(address(this), uint256(uint160(cur)), amt);
            int256 d1 = L.delta(address(this), cur);
            (, bytes memory r) = address(this).call(abi.encodeCall(Seq.innerMint, (cur, amt + i)));
            int256 inner = r.length >= 64 ? int256(uint256(bytes32(r))) : int256(0);
            uint256 innerCount;
            assembly {
                innerCount := mload(add(r, 64))
            }
            int256 d2 = L.delta(address(this), cur);
            uint256 cnt = uint256(L.PM.exttload(NZ));
            if (d1 != -int256(amt) || inner != -int256(2 * amt + i) || d2 != d1 || cnt != i + 1 || innerCount != i + 1) bad++;
            if (i < 4 || i + 1 == n) {
                _p(uint256(d1));
                _p(uint256(inner));
                _p(uint256(d2));
                _p(cnt);
                _p(innerCount);
            }
        }
        for (uint256 i = 0; i < n; i++) {
            address cur = address(uint160(base + i));
            uint256 amt = uint256(keccak256(abi.encode(seed, i))) % (1 << 120) + 1;
            L.PM.burn(address(this), uint256(uint160(cur)), amt);
            if (L.delta(address(this), cur) != 0) bad++;
        }
        _p(uint256(L.PM.exttload(NZ)));
        _p(bad);
    }

    // mode 7: (t0, t1, bytes codeA, bytes codeB, bytes32 salt) hook code replaced at one address in one call.
    function _meta(bytes memory a) internal {
        (address t0, address t1, bytes memory ca, bytes memory cb, bytes32 salt) =
            abi.decode(a, (address, address, bytes, bytes, bytes32));
        bytes memory init = type(Meta).creationCode;
        next = ca;
        address h1;
        assembly {
            h1 := create2(0, add(init, 32), mload(init), salt)
        }
        _p(uint256(uint160(h1)));
        _p(uint256(h1.codehash));
        PoolKey memory k = PoolKey(t0, t1, 3000, 60, h1);
        L.PM.initialize(k, 1 << 96);
        L.PM.modifyLiquidity(k, MLP(-887220, 887220, 1e24, 0), "");
        lastMark = 0;
        _p(uint256(_swap(k, true, -1e18)));
        _p(lastMark);
        (bool ok,) = h1.call(abi.encodeCall(HkA.kill, ()));
        _p(ok ? 1 : 0);
        _p(h1.code.length);
        next = cb;
        address h2;
        try this.create2Bounded{gas: 2_000_000}(init, salt) returns (address a2) {
            h2 = a2;
        } catch {
            h2 = address(0);
        }
        _p(uint256(uint160(h2)));
        _p(uint256(h1.codehash));
        lastMark = 0;
        _p(uint256(_swap(k, false, -1e18)));
        _p(lastMark);
        L.settleAll(t0);
        L.settleAll(t1);
    }
}
