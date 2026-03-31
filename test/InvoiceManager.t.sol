// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {InvoiceManager} from "../contracts/InvoiceManager.sol";

/// @title InvoiceManagerTest
/// @notice Tests for InvoiceManager contract.
contract InvoiceManagerTest is Test {
    InvoiceManager public manager;
    address public alice;
    address public bob;

    function setUp() public {
        manager = new InvoiceManager();
        alice = makeAddr("alice");
        bob = makeAddr("bob");
    }

    function testCreateInvoice() public {
        vm.prank(alice);
        bytes32 id = manager.createInvoice(bob, 1000, address(0));
        assertEq(uint8(manager.getStatus(id)), uint8(InvoiceManager.Status.Created));
    }

    function testCreateInvoiceZeroAmount() public {
        vm.prank(alice);
        vm.expectRevert(InvoiceManager.InvalidAmount.selector);
        manager.createInvoice(bob, 0, address(0));
    }

    function testCreateInvoiceSelfInvoice() public {
        vm.prank(alice);
        vm.expectRevert(InvoiceManager.InvalidRecipient.selector);
        manager.createInvoice(alice, 1000, address(0));
    }

    function testCreateInvoiceZeroRecipient() public {
        vm.prank(alice);
        vm.expectRevert(InvoiceManager.InvalidRecipient.selector);
        manager.createInvoice(address(0), 1000, address(0));
    }

    function testCancelInvoice() public {
        vm.prank(alice);
        bytes32 id = manager.createInvoice(bob, 1000, address(0));

        vm.prank(alice);
        manager.cancelInvoice(id);
        assertEq(uint8(manager.getStatus(id)), uint8(InvoiceManager.Status.Cancelled));
    }

    function testCancelNotCreator() public {
        vm.prank(alice);
        bytes32 id = manager.createInvoice(bob, 1000, address(0));

        vm.prank(bob);
        vm.expectRevert(InvoiceManager.NotRecipient.selector);
        manager.cancelInvoice(id);
    }

    function testCancelNonExistent() public {
        vm.expectRevert(InvoiceManager.InvoiceNotFound.selector);
        manager.cancelInvoice(bytes32(0));
    }

    function testGetStatus() public {
        vm.prank(alice);
        bytes32 id = manager.createInvoice(bob, 1000, address(0));
        assertEq(uint8(manager.getStatus(id)), uint8(InvoiceManager.Status.Created));
    }

    function testInvoiceCount() public {
        vm.startPrank(alice);
        manager.createInvoice(bob, 1000, address(0));
        manager.createInvoice(bob, 2000, address(0));
        manager.createInvoice(bob, 3000, address(0));
        vm.stopPrank();
        assertEq(manager.invoiceCount(), 3);
    }
}
