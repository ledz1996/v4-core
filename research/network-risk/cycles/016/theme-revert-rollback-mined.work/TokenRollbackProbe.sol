// SPDX-License-Identifier: MIT
// Cycle 16, theme-revert-rollback-mined. A read-only semantics probe, run only through eth_call with its code
// placed by state override at an address that holds a token the node implements natively (a precompile token or
// a native asset with an ERC-20 face). It asks whether a transfer made by such a token inside a frame that then
// reverts or halts is undone, and whether a transfer under STATICCALL is refused. No transaction is sent.
pragma solidity 0.8.26;

interface IT {
    function transfer(address, uint256) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

contract TokenRollbackProbe {
    function _halt(uint256 kind) internal {
        if (kind == 1) revert("r");
        if (kind == 2) assembly { invalid() }
        if (kind == 3) _rec(1);
        if (kind == 4) assembly { for {} 1 {} {} }
    }

    function _rec(uint256 x) internal returns (uint256) { return _rec(x + 1) + 1; }

    // mode 0: token.transfer; mode 1: native value transfer
    function inner(address token, address to, uint256 amt, uint256 kind, uint256 mode) external returns (bool ok) {
        require(msg.sender == address(this));
        if (mode == 0) { (ok,) = token.call(abi.encodeCall(IT.transfer, (to, amt))); }
        else { (ok,) = to.call{value: amt}(""); }
        _halt(kind);
    }

    function _bal(address token, address to) internal view returns (uint256[4] memory b) {
        b[0] = IT(token).balanceOf(address(this)); b[1] = IT(token).balanceOf(to);
        b[2] = address(this).balance; b[3] = to.balance;
    }

    // per kind: kind id, frame success, 4 balances before, 4 after; kinds 1-4 halt, 9 is STATICCALL, 0 is the control and runs last
    function run(address token, address to, uint256 amt, uint256 mode) external returns (uint256[] memory out) {
        out = new uint256[](6 * 10);
        uint256 k;
        uint256[6] memory order = [uint256(1), 2, 3, 4, 9, 0];
        for (uint256 j; j < 6; j++) {
            uint256 kind = order[j];
            uint256[4] memory a = _bal(token, to);
            bool ok;
            if (kind == 9) {
                if (mode == 0) (ok,) = token.staticcall{gas: 2_000_000}(abi.encodeCall(IT.transfer, (to, amt)));
                else (ok,) = address(this).staticcall{gas: 2_000_000}(abi.encodeCall(this.inner, (token, to, amt, 0, 1)));
            } else {
                bytes memory r;
                (ok, r) = address(this).call{gas: 2_000_000}(abi.encodeCall(this.inner, (token, to, amt, kind, mode)));
                if (ok && kind == 0) ok = abi.decode(r, (bool));
            }
            uint256[4] memory b = _bal(token, to);
            out[k++] = kind; out[k++] = ok ? 1 : 0;
            for (uint256 i; i < 4; i++) out[k++] = a[i];
            for (uint256 i; i < 4; i++) out[k++] = b[i];
        }
    }
}
