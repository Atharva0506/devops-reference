// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "./interfaces/IERC20.sol";

/// @title InvoiceManager
/// @notice Manages invoice creation, payment, and lifecycle tracking.
/// @dev Demo contract for StabilityNexus DevSecOps reference pipeline.
contract InvoiceManager {
    enum Status {
        Created,
        Paid,
        Cancelled
    }

    struct Invoice {
        address creator;
        address recipient;
        uint256 amount;
        address token;
        Status status;
        uint256 createdAt;
        uint256 paidAt;
    }

    mapping(bytes32 => Invoice) public invoices;
    uint256 public invoiceCount;

    event InvoiceCreated(
        bytes32 indexed invoiceId,
        address indexed creator,
        address indexed recipient,
        uint256 amount,
        address token
    );

    event InvoiceStatusChanged(
        bytes32 indexed invoiceId,
        Status oldStatus,
        Status newStatus
    );

    event PaymentReceived(
        bytes32 indexed invoiceId,
        address indexed payer,
        uint256 amount
    );

    error InvalidAmount();
    error InvalidRecipient();
    error InvoiceNotFound();
    error AlreadyPaid();
    error NotRecipient();

    /// @notice Creates a new invoice.
    /// @param recipient Address that will receive payment.
    /// @param amount Payment amount in token units.
    /// @param token ERC-20 token address. Use address(0) for native currency.
    /// @return invoiceId Unique identifier for the created invoice.
    function createInvoice(
        address recipient,
        uint256 amount,
        address token
    ) external returns (bytes32 invoiceId) {
        if (amount == 0) revert InvalidAmount();
        if (recipient == address(0)) revert InvalidRecipient();
        if (recipient == msg.sender) revert InvalidRecipient();

        invoiceCount++;
        invoiceId = keccak256(
            abi.encodePacked(msg.sender, recipient, amount, block.timestamp, invoiceCount)
        );

        invoices[invoiceId] = Invoice({
            creator: msg.sender,
            recipient: recipient,
            amount: amount,
            token: token,
            status: Status.Created,
            createdAt: block.timestamp,
            paidAt: 0
        });

        emit InvoiceCreated(invoiceId, msg.sender, recipient, amount, token);
    }

    /// @notice Pays an invoice using ERC-20 tokens.
    /// @param invoiceId The invoice to pay.
    /// @dev Critical payment path - follows checks-effects-interactions.
    function payInvoice(bytes32 invoiceId) external {
        Invoice storage invoice = invoices[invoiceId];
        if (invoice.creator == address(0)) revert InvoiceNotFound();
        if (invoice.status != Status.Created) revert AlreadyPaid();

        Status oldStatus = invoice.status;

        // Effects: update state BEFORE external call (checks-effects-interactions)
        invoice.status = Status.Paid;
        invoice.paidAt = block.timestamp;

        // Interactions: external call after state is finalized
        bool success = IERC20(invoice.token).transferFrom(
            msg.sender,
            invoice.recipient,
            invoice.amount
        );
        require(success, "Transfer failed");

        emit InvoiceStatusChanged(invoiceId, oldStatus, Status.Paid);
        emit PaymentReceived(invoiceId, msg.sender, invoice.amount);
    }

    /// @notice Cancels an unpaid invoice. Only the creator can cancel.
    /// @param invoiceId The invoice to cancel.
    function cancelInvoice(bytes32 invoiceId) external {
        Invoice storage invoice = invoices[invoiceId];
        if (invoice.creator == address(0)) revert InvoiceNotFound();
        if (invoice.status != Status.Created) revert AlreadyPaid();
        if (invoice.creator != msg.sender) revert NotRecipient();

        Status oldStatus = invoice.status;
        invoice.status = Status.Cancelled;

        emit InvoiceStatusChanged(invoiceId, oldStatus, Status.Cancelled);
    }

    /// @notice Returns the current status of an invoice.
    /// @param invoiceId The invoice to query.
    /// @return status Current status enum value.
    function getStatus(bytes32 invoiceId) external view returns (Status) {
        return invoices[invoiceId].status;
    }
}
