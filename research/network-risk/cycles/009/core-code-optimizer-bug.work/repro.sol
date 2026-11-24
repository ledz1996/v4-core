// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
contract C {
    struct S { uint256 v; }
    S[20] public a;
    function g(uint256 max1, uint256 max2, uint256 aaaa, uint256 bbbb) external returns (uint256) {
        uint256 i;
        for (uint256 j; j < max1; j++) i++;
        uint256 k = i + 2;
        a[k].v = aaaa;
        for (uint256 j; j < max2; j++) i++;
        a[i].v = bbbb;
        return a[k].v;
    }
}
