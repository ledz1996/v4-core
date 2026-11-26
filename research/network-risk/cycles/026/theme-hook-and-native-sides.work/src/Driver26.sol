// SPDX-License-Identifier: UNLICENSED
// Read-only driver for theme-hook-and-native-sides (cycle 26). Extends the cycle 25 driver of theme-unexecuted-sides.
// It runs only inside eth_call with state overrides (or the Python reference EVM). Currencies are token doubles placed
// by override or the native currency, whose balances come from balance overrides. The hook double Hk is placed by
// override at addresses whose low 14 bits carry the permission flags under test. Nothing here is deployed.
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

struct C {
    uint256 kind;
    address t0;
    address t1;
    uint24 fee;
    int24 ts;
    address hooks;
    uint160 sqrtP;
    int24 tl;
    int24 tu;
    uint256 liq;
    bool zfo;
    int256 amt;
    uint160 lim;
    uint256[] p;
}

interface IH {
    function beforeInitialize(address, PoolKey calldata, uint160) external returns (bytes4);
    function afterInitialize(address, PoolKey calldata, uint160, int24) external returns (bytes4);
    function beforeAddLiquidity(address, PoolKey calldata, MLP calldata, bytes calldata) external returns (bytes4);
    function afterAddLiquidity(address, PoolKey calldata, MLP calldata, int256, int256, bytes calldata)
        external
        returns (bytes4, int256);
    function beforeRemoveLiquidity(address, PoolKey calldata, MLP calldata, bytes calldata) external returns (bytes4);
    function afterRemoveLiquidity(address, PoolKey calldata, MLP calldata, int256, int256, bytes calldata)
        external
        returns (bytes4, int256);
    function beforeSwap(address, PoolKey calldata, SP calldata, bytes calldata) external returns (bytes4, int256, uint24);
    function afterSwap(address, PoolKey calldata, SP calldata, int256, bytes calldata) external returns (bytes4, int128);
    function beforeDonate(address, PoolKey calldata, uint256, uint256, bytes calldata) external returns (bytes4);
    function afterDonate(address, PoolKey calldata, uint256, uint256, bytes calldata) external returns (bytes4);
}

interface IPM {
    function unlock(bytes calldata) external returns (bytes memory);
    function sync(address) external;
    function take(address, address, uint256) external;
    function settle() external payable returns (uint256);
    function settleFor(address) external payable returns (uint256);
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
}

/// Hook double. Per selector: mode 0 answers the correct selector with zero words at the length the PoolManager
/// expects, mode 1 returns the configured bytes as they are, mode 2 reverts with the configured bytes, mode 3 executes
/// INVALID (all forwarded gas is consumed). Before answering it runs the configured callbacks into the PoolManager and
/// records (success, first word) of each. Selector 0 is the plain value transfer.
contract Hk {
    address constant PM = 0xA11Ce5A11Ce5a11ce5A11cE5a11CE5A11CE5A11c; // replaced per network

    mapping(bytes4 => uint256) public mode;
    mapping(bytes4 => bytes) dat;
    mapping(bytes4 => bytes[]) cbs;
    uint256[] res;
    bytes4[] used;

    function hcfg(bytes4 s, uint256 m, bytes calldata d) external {
        mode[s] = m;
        dat[s] = d;
        used.push(s);
    }

    function hcb(bytes4 s, bytes calldata d) external {
        cbs[s].push(d);
        used.push(s);
    }

    function hreset() external {
        for (uint256 i = 0; i < used.length; i++) {
            bytes4 s = used[i];
            delete mode[s];
            delete dat[s];
            delete cbs[s];
        }
        delete used;
        delete res;
    }

    function hres() external view returns (uint256[] memory) {
        return res;
    }

    function hexec(address to, bytes calldata data) external payable returns (bytes memory) {
        (bool ok, bytes memory ret) = to.call{value: msg.value}(data);
        if (!ok) {
            assembly {
                revert(add(ret, 32), mload(ret))
            }
        }
        return ret;
    }

    function _default(bytes4 s) internal pure returns (bytes memory) {
        if (s == IH.beforeSwap.selector) return abi.encodePacked(bytes32(s), uint256(0), uint256(0));
        if (
            s == IH.afterSwap.selector || s == IH.afterAddLiquidity.selector || s == IH.afterRemoveLiquidity.selector
        ) return abi.encodePacked(bytes32(s), uint256(0));
        return abi.encodePacked(bytes32(s));
    }

    fallback(bytes calldata input) external payable returns (bytes memory) {
        bytes4 s = input.length >= 4 ? bytes4(input[:4]) : bytes4(0);
        bytes[] storage cb = cbs[s];
        for (uint256 i = 0; i < cb.length; i++) {
            (bool ok, bytes memory ret) = PM.call(cb[i]);
            uint256 w0;
            if (ret.length >= 32) {
                assembly {
                    w0 := mload(add(ret, 32))
                }
            } else if (ret.length >= 4) {
                assembly {
                    w0 := and(mload(add(ret, 32)), shl(224, 0xffffffff))
                }
            }
            res.push(ok ? 1 : 0);
            res.push(w0);
        }
        uint256 m = mode[s];
        if (m == 1) return dat[s];
        if (m == 2) {
            bytes memory d = dat[s];
            assembly {
                revert(add(d, 32), mload(d))
            }
        }
        if (m == 3) {
            assembly {
                invalid()
            }
        }
        return _default(s);
    }
}

contract Driver {
    IPM constant PM = IPM(0xA11Ce5A11Ce5a11ce5A11cE5a11CE5A11CE5A11c); // replaced per network
    address constant S = 0x0000000000000000000000000000000055550000; // second actor, same code
    bytes32 constant COUNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b;

    struct Rec {
        uint256[] w;
        uint256 n;
    }

    receive() external payable {}

    function _push(Rec memory r, uint256 v) internal pure {
        r.w[r.n++] = v;
    }

    function _call(Rec memory r, address to, uint256 v, bytes memory data) internal returns (bool ok) {
        bytes memory ret;
        (ok, ret) = to.call{value: v}(data);
        uint256 w0;
        uint256 w1;
        if (ret.length >= 32) {
            assembly {
                w0 := mload(add(ret, 32))
            }
        } else if (ret.length >= 4) {
            assembly {
                w0 := and(mload(add(ret, 32)), shl(224, 0xffffffff))
            }
        }
        if (ret.length >= 64) {
            assembly {
                w1 := mload(add(ret, 64))
            }
        }
        _push(r, ok ? 1 : 0);
        _push(r, w0);
        _push(r, w1);
        _push(r, ret.length);
    }

    function _delta(address target, address cur) internal view returns (int256) {
        return int256(uint256(PM.exttload(keccak256(abi.encode(target, cur)))));
    }

    function _bal(address cur, address who) internal view returns (uint256) {
        if (cur == address(0)) return who.balance;
        return ITok(cur).balanceOf(who);
    }

    function _poolSlot(PoolKey memory key) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(keccak256(abi.encode(key)), bytes32(uint256(6))));
    }

    function exec(address to, bytes calldata data) external payable returns (bytes memory) {
        (bool ok, bytes memory ret) = to.call{value: msg.value}(data);
        if (!ok) {
            assembly {
                revert(add(ret, 32), mload(ret))
            }
        }
        return ret;
    }

    function run(bytes[] calldata cases) external returns (bytes[] memory out) {
        out = new bytes[](cases.length);
        for (uint256 i = 0; i < cases.length; i++) {
            (bool ok, bytes memory ret) = address(PM).call(abi.encodeCall(IPM.unlock, (cases[i])));
            out[i] = abi.encode(ok, ret);
        }
    }

    /// Settle the open delta of `who` in `cur`: pay a debt with settleFor (value for native), and have `who` take a
    /// credit to itself (the driver for itself, Hk.hexec for the hook, Driver.exec for S).
    function settleOne(address who, address cur, address hk) external {
        require(msg.sender == address(this));
        _settleOf(who, cur, hk);
    }

    function _settleOf(address who, address cur, address hk) internal {
        int256 d = _delta(who, cur);
        if (d < 0) {
            uint256 a = uint256(-d);
            PM.sync(cur);
            if (cur == address(0)) {
                PM.settleFor{value: a}(who);
            } else {
                ITok(cur).mint(address(PM), a);
                PM.settleFor(who);
            }
        } else if (d > 0) {
            bytes memory t = abi.encodeCall(IPM.take, (cur, who, uint256(d)));
            if (who == address(this)) {
                PM.take(cur, who, uint256(d));
            } else if (who == hk) {
                Hk(payable(hk)).hexec(address(PM), t);
            } else {
                Driver(payable(who)).exec(address(PM), t);
            }
        }
    }

    function _state(Rec memory r, PoolKey memory key) internal view {
        _push(r, uint256(PM.exttload(COUNT)));
        _push(r, uint256(PM.extsload(_poolSlot(key))));
    }

    function _deltas(Rec memory r, PoolKey memory key) internal view {
        address[3] memory who = [address(this), key.hooks, S];
        for (uint256 i = 0; i < 3; i++) {
            _push(r, uint256(_delta(who[i], key.currency0)));
            _push(r, uint256(_delta(who[i], key.currency1)));
        }
    }

    function _balances(Rec memory r, PoolKey memory key) internal view {
        address[4] memory who = [address(PM), address(this), key.hooks, S];
        for (uint256 i = 0; i < 4; i++) {
            _push(r, _bal(key.currency0, who[i]));
            _push(r, _bal(key.currency1, who[i]));
        }
    }

    /// p = [ncfg, cfg..., nact, act..., settle flag]
    /// cfg = [type (0 hcfg, 1 hcb), selector word, mode, length, words...]
    /// act = [to, value, length, words...]; to 1 = PoolManager, 2 = PoolManager through the hook (Hk.hexec),
    /// 3 = PoolManager through S (Driver.exec), any other value is a literal address.
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(PM));
        C memory c = abi.decode(data, (C));
        Rec memory r = Rec(new uint256[](400), 0);
        PoolKey memory key = PoolKey(c.t0, c.t1, c.fee, c.ts, c.hooks);
        Hk hk = Hk(payable(c.hooks));
        if (c.hooks.code.length > 0) hk.hreset();
        _balances(r, key);
        uint256 k = 0;
        uint256 ncfg = c.p[k++];
        for (uint256 j = 0; j < ncfg; j++) {
            uint256 typ = c.p[k++];
            bytes4 s = bytes4(bytes32(c.p[k++]));
            uint256 m = c.p[k++];
            bytes memory d;
            (d, k) = _bytesAt(c.p, k);
            if (typ == 0) hk.hcfg(s, m, d);
            else hk.hcb(s, d);
        }
        uint256 nact = c.p[k++];
        for (uint256 j = 0; j < nact; j++) {
            uint256 to = c.p[k++];
            uint256 v = c.p[k++];
            bytes memory d;
            (d, k) = _bytesAt(c.p, k);
            if (to == 1) {
                _call(r, address(PM), v, d);
            } else if (to == 2) {
                _call(r, address(hk), v, abi.encodeCall(Hk.hexec, (address(PM), d)));
            } else if (to == 3) {
                _call(r, S, v, abi.encodeCall(Driver.exec, (address(PM), d)));
            } else {
                _call(r, address(uint160(to)), v, d);
            }
            _state(r, key);
        }
        _deltas(r, key);
        if (c.hooks.code.length > 0) {
            uint256[] memory hr = hk.hres();
            _push(r, hr.length);
            for (uint256 j = 0; j < hr.length && j < 24; j++) {
                _push(r, hr[j]);
            }
        } else {
            _push(r, 0);
        }
        if (c.p[k] == 1) {
            address[3] memory who = [address(this), c.hooks, S];
            for (uint256 i = 0; i < 3; i++) {
                try this.settleOne(who[i], key.currency0, c.hooks) {
                    _push(r, 1);
                } catch {
                    _push(r, 0);
                }
                try this.settleOne(who[i], key.currency1, c.hooks) {
                    _push(r, 1);
                } catch {
                    _push(r, 0);
                }
            }
        }
        _state(r, key);
        _balances(r, key);
        uint256[] memory w = r.w;
        uint256 n = r.n;
        assembly {
            mstore(w, n)
        }
        if (PM.exttload(COUNT) != bytes32(0)) {
            // the unlock would fail: hand the record back as revert data behind a marker
            bytes memory e = abi.encodePacked(bytes4(0xdeadc0de), abi.encode(w));
            assembly {
                revert(add(e, 32), mload(e))
            }
        }
        return abi.encode(w);
    }

    function _bytesAt(uint256[] memory p, uint256 k) internal pure returns (bytes memory d, uint256 k2) {
        uint256 len = p[k++];
        d = new bytes(len);
        for (uint256 q = 0; q < (len + 31) / 32; q++) {
            uint256 v = p[k++];
            if (q * 32 + 32 <= len) {
                assembly {
                    mstore(add(add(d, 32), mul(q, 32)), v)
                }
            } else {
                for (uint256 b = 0; b < len - q * 32; b++) {
                    d[q * 32 + b] = bytes1(uint8(v >> (248 - 8 * b)));
                }
            }
        }
        k2 = k;
    }
}
