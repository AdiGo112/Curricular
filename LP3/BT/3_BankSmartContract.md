# Assignment 3: Smart Contract for a Bank Account (Deposit, Withdraw, Show Balance)

## Aim
Write a smart contract on a test network that lets each caller deposit, withdraw and view their own Ether balance held by the contract.

## Solidity Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BankAccount {
    mapping(address => uint256) private balances;

    event Deposit(address indexed account, uint256 amount, uint256 newBalance);
    event Withdraw(address indexed account, uint256 amount, uint256 newBalance);

    // Deposit Ether sent along with the call into the caller's balance.
    function deposit() external payable {
        require(msg.value > 0, "Deposit amount must be greater than zero");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value, balances[msg.sender]);
    }

    // Withdraw a specific amount from the caller's own balance.
    function withdraw(uint256 amount) external {
        require(amount > 0, "Withdraw amount must be greater than zero");
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        (bool sent, ) = payable(msg.sender).call{value: amount}("");
        require(sent, "Transfer failed");

        emit Withdraw(msg.sender, amount, balances[msg.sender]);
    }

    // Read-only: view the caller's current balance. No gas cost off-chain.
    function getBalance() external view returns (uint256) {
        return balances[msg.sender];
    }
}
```

Notes on the code:
- `balances` is a `mapping(address => uint256)` so each caller's funds are tracked separately inside one shared contract.
- `deposit()` is `payable` — it is the only way the contract can receive Ether attached to a call.
- `withdraw()` uses `require` to revert (undoing all state changes and refunding unused gas) if the amount is invalid or exceeds the caller's recorded balance, before any funds move (checks-effects-interactions pattern: balance is deducted before the external `call`, to avoid re-entrancy).
- `getBalance()` is `view` — it only reads state, never writes it.
- `Deposit` and `Withdraw` events let off-chain code (and MetaMask's activity log) show what happened without re-reading storage.

## Deployment Steps (Remix IDE, no local setup)

1. Open the Remix IDE (`remix.ethereum.org`) in a browser.
2. In the **File Explorer**, create a new file `BankAccount.sol` and paste the contract above.
3. Go to the **Solidity Compiler** tab, select a compiler version matching `^0.8.0` (e.g. 0.8.20), and click **Compile**.
4. Go to the **Deploy & Run Transactions** tab. Set **Environment** to **Injected Provider - MetaMask** (this connects Remix to MetaMask, which must be switched to a testnet like Sepolia and funded from a faucet).
5. Click **Deploy**. MetaMask pops up asking to confirm the deployment transaction (deployment itself costs gas, since it writes the contract's bytecode to the chain). Confirm.
6. Once mined, the deployed contract appears under **Deployed Contracts** in Remix, with buttons for `deposit`, `withdraw` and `getBalance`.
7. To deposit: expand the contract, enter a **Value** (e.g. `0.01` ether) next to the deploy/transact value field, then click `deposit`. MetaMask asks to confirm — this is a state-changing call, so it costs gas.
8. To withdraw: enter an amount (in wei) as the argument to `withdraw` and click it. MetaMask again asks to confirm.
9. To check balance: click `getBalance` (a blue "read" button in Remix) — this returns instantly with no MetaMask popup and no gas, because it is a `view` call simulated locally by the node rather than broadcast as a transaction.

## Interaction Flow

```mermaid
flowchart LR
    Caller["Caller (via MetaMask)"] -->|"deposit() + value"| C["BankAccount Contract"]
    C -->|require msg.value > 0| C
    C -->|balances[sender] += value| State1[("Contract Storage")]
    C -->|emit Deposit| Log1[Event Log]

    Caller -->|withdraw(amount)| C
    C -->|require balances[sender] >= amount| Check{Enough balance?}
    Check -->|No| Revert["Revert (state unchanged, gas still spent)"]
    Check -->|Yes| State2[("balances[sender] -= amount")]
    State2 --> Transfer["call{value: amount}(sender)"]
    Transfer --> Log2[Event Log: Withdraw]

    Caller -->|getBalance() - view, off-chain simulation| C
    C -->|read only, no state change| Caller
```

## Gas / Fee Behavior per Function

| Function | Type | Gas cost | Why |
| --- | --- | --- | --- |
| `getBalance()` | `view`, read-only | **0 gas** when called off-chain (e.g. via Remix's "call" / a node's `eth_call`) | No state is written, so there is nothing to agree on across the network — it just runs against the latest state on a single node and returns the answer. |
| `deposit()` | state-changing, `payable` | Gas for one `SSTORE` (balance update) plus base 21,000 for the transaction envelope, plus value transfer | Must be broadcast and mined, since contract storage changes. |
| `withdraw()` | state-changing | Similar `SSTORE` cost, plus the gas consumed by the internal `.call{value: amount}("")` forwarding ETH out of the contract | Slightly more than `deposit()` because of the extra external call. |

In short: any function marked `view`/`pure` is free when invoked as a read; any function that mutates `balances` must be sent as a real transaction and therefore always costs `gasUsed * gasPrice` ETH, as described in Assignment 1.

## Key Terms
- **`mapping(address => uint256)`**: per-caller balance storage.
- **`payable`**: marks a function able to receive ETH (`deposit`).
- **`require`**: reverts the transaction (and refunds unused gas) if a condition fails.
- **Checks-effects-interactions**: deduct balance before sending ETH out, to prevent re-entrancy.
- **`view` function**: read-only, no gas cost off-chain (`getBalance`).
- **Events**: `Deposit`/`Withdraw`, cheap way to log history off-chain.

## Viva Questions
1. **Why does `withdraw` check `balances[msg.sender] >= amount` before transferring?** To prevent withdrawing more than the caller actually deposited; `require` reverts cleanly if it fails.
2. **Why update `balances` before calling `.call{value: amount}("")`?** Checks-effects-interactions pattern — prevents a re-entrancy attack where the recipient's fallback could call `withdraw` again before the balance is updated.
3. **Why is `getBalance` free to call?** It's marked `view`; called off-chain it only reads state, never submitted as a mined transaction.
4. **What makes `deposit` able to receive ETH?** The `payable` modifier; `msg.value` is the ETH amount sent with the call.
5. **What happens on deployment, gas-wise?** Deploying writes the contract's bytecode to the chain, which itself costs gas, separate from any later function calls.
6. **Why use events instead of just storage for history?** Events are much cheaper than storage writes and are easily queried off-chain (e.g. by a UI), without bloating contract storage.
