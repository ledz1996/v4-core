// SPDX-License-Identifier: MIT
// Cycle 16, theme-revert-rollback-mined, task 2. A read-only semantics probe, run only through eth_call
// with its code placed by state override. It moves no value. It asks one question per halt kind: after a
// frame that wrote transient storage (its own, and the PoolManager's through unlock, mint and sync) halts,
// does a later frame read any of those writes back?
pragma solidity 0.8.26;

interface IPM {
    function unlock(bytes calldata) external returns (bytes memory);
    function sync(address) external;
    function mint(address, uint256, uint256) external;
    function burn(address, uint256, uint256) external;
    function exttload(bytes32) external view returns (bytes32);
    function balanceOf(address, uint256) external view returns (uint256);
}

contract HaltProbe {
    bytes32 constant UNLOCKED = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23;
    bytes32 constant COUNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b;
    bytes32 constant CURRENCY = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9;
    bytes32 constant RESERVES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95;
    uint256 constant MY1 = 0x1111;
    uint256 constant MY2 = 0x2222;
    uint256 constant ATT = 0x3333;
    uint256 constant MAXD = 0x4444;

    // token face: the probe is its own currency, so sync calls back here
    function balanceOf(address) external view returns (uint256 v) {
        assembly { v := add(1000, tload(ATT)) }
    }

    function _halt(uint256 kind) internal {
        if (kind == 1) revert("r");
        if (kind == 2) assembly { invalid() }
        if (kind == 3) _rec(1);
        if (kind == 4) assembly { for {} 1 {} {} }
        if (kind == 5) assembly { tstore(MY2, 5) } // used under STATICCALL: the write itself is the fault
    }

    function _rec(uint256 x) internal returns (uint256) {
        return _rec(x + 1) + 1;
    }

    // variant 1: inside unlock (callback writes PoolManager deltas, count, claims, synced currency, then halts)
    // variant 2: outside unlock (sync only, then halts)
    function h(uint256 kind, uint256 variant, address pm) external {
        assembly { tstore(MY1, 7) }
        if (variant == 1) {
            IPM(pm).unlock(abi.encode(kind, pm));
        } else {
            IPM(pm).sync(address(this));
            _halt(kind);
        }
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        (uint256 kind, address pm) = abi.decode(data, (uint256, address));
        IPM(pm).mint(address(this), uint256(uint160(address(this))), 5);
        IPM(pm).sync(address(this));
        assembly { tstore(MY2, 9) }
        _halt(kind);
        IPM(pm).burn(address(this), uint256(uint160(address(this))), 5);
        return "";
    }

    function myT() external view returns (uint256 a, uint256 b) {
        assembly { a := tload(MY1) b := tload(MY2) }
    }

    function reads(address pm) public view returns (uint256[8] memory r) {
        bytes32 dslot = keccak256(abi.encode(address(this), address(this)));
        r[0] = uint256(IPM(pm).exttload(UNLOCKED));
        r[1] = uint256(IPM(pm).exttload(COUNT));
        r[2] = uint256(IPM(pm).exttload(dslot));
        r[3] = uint256(IPM(pm).exttload(CURRENCY));
        r[4] = uint256(IPM(pm).exttload(RESERVES));
        r[5] = IPM(pm).balanceOf(address(this), uint256(uint160(address(this))));
        (r[6], r[7]) = this.myT();
    }

    // one attempt per kind and variant, with all gas; kind 0 is the successful control
    function kinds(address pm) external returns (uint256[] memory out) {
        out = new uint256[](6 * 2 * 10 + 3 * 10);
        uint256 k;
        for (uint256 variant = 1; variant <= 2; variant++) {
            for (uint256 kind = 0; kind <= 5; kind++) {
                if (kind == 5) continue;
                assembly { tstore(ATT, add(mul(variant, 100), kind)) }
                (bool ok,) = address(this).call{gas: 3_000_000}(abi.encodeCall(this.h, (kind, variant, pm)));
                uint256[8] memory r = reads(pm);
                out[k++] = variant * 100 + kind; out[k++] = ok ? 1 : 0;
                for (uint256 i; i < 8; i++) out[k++] = r[i];
                if (ok) _reset(pm);
            }
        }
        // static context: the probe's own TSTORE, PoolManager.sync and PoolManager.unlock, each under STATICCALL
        bytes[3] memory sc = [abi.encodeCall(this.h, (5, 2, address(0))), abi.encodeCall(IPM.sync, (address(this))), abi.encodeCall(IPM.unlock, (abi.encode(uint256(0), pm)))];
        address[3] memory tg = [address(this), pm, pm];
        for (uint256 j; j < 3; j++) {
            (bool ok,) = tg[j].staticcall{gas: 3_000_000}(sc[j]);
            uint256[8] memory r = reads(pm);
            out[k++] = 900 + j; out[k++] = ok ? 1 : 0;
            for (uint256 i; i < 8; i++) out[k++] = r[i];
        }
    }

    function _reset(address pm) internal {
        IPM(pm).sync(address(0));
        assembly { tstore(MY1, 0) tstore(MY2, 0) }
    }

    // out of gas at every gas value in [g0, g1) with step s, ascending, stopping at the first success.
    // Returns: attempts, failures, failures with any nonzero read, first leaking gas, gas of first success, reads after success
    function sweep(address pm, uint256 variant, uint256 g0, uint256 g1, uint256 s) external returns (uint256[14] memory o) {
        o[3] = type(uint256).max; o[4] = type(uint256).max;
        for (uint256 g = g0; g < g1; g += s) {
            assembly { tstore(ATT, g) }
            (bool ok,) = address(this).call{gas: g}(abi.encodeCall(this.h, (0, variant, pm)));
            uint256[8] memory r = reads(pm);
            o[0]++;
            if (ok) { o[4] = g; for (uint256 i; i < 8; i++) o[6 + i] = r[i]; break; }
            o[1]++;
            bool any;
            for (uint256 i; i < 8; i++) if (r[i] != 0) any = true;
            if (any) { o[2]++; if (o[3] == type(uint256).max) { o[3] = g; o[5] = r[3] | (r[0] << 200); } }
        }
    }

    // call depth reachable with the gas the endpoint grants
    function depth(uint256 d) external {
        assembly { if gt(d, tload(MAXD)) { tstore(MAXD, d) } }
        address(this).call(abi.encodeCall(this.depth, (d + 1)));
    }

    function depthRun() external returns (uint256 m) {
        this.depth(1);
        assembly { m := tload(MAXD) }
    }
}
