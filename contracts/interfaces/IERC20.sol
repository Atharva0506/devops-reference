// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IERC20
/// @notice Minimal ERC-20 interface for token transfers.
interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}
