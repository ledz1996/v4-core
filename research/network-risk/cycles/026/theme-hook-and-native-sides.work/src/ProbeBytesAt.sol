// SPDX-License-Identifier: UNLICENSED
// Probe for the Monad harness engine difference: the byte loop of Driver26._bytesAt on its own, and the same followed
// by an external call that reverts with 4 bytes and a low-level call record, as Driver26._call does.
pragma solidity 0.8.26;

contract ProbeBytesAt {
    function bytesAt(uint256[] memory p) public pure returns (bytes memory d) {
        uint256 k = 0;
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
    }
}
