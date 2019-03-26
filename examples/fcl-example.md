# FCL example

Here's a more advanced example to understand how to interact with contracts in Uplink.
Uplink workflows are very well documented [here](https://www.adjoint.io/docs/workflows.html)

### 0. Requirements

Make sure you have an Uplink node running and have all dependencies installed in this project.
We need to have at least two accounts, one asset and each party must hold some holdings
before we can work on this example. We recommend you to follow our guided example `basic-example`.

### 1. Mutually agreed amendment

Alice and Bob both commit their value, then we calculate the total. Either may
then choose to propose an amended total value, which will be accepted if the
counterparty agrees.

```python
amendment_script = """
global account alice;
global account bob;
global int valueAlice;
global int valueBob;
global int total;
global int proposedNewTotal;
global account counterparty;

@initial
init(account a, account b) {
  alice = a;
  bob = b;
  transitionTo(@{todoAlice, todoBob});
}

@todoAlice [role: alice]
setValueAlice(int val) {
  valueAlice = val;
  transitionTo(@doneAlice);
}

@todoBob [role: bob]
setValueBob(int val) {
  valueBob = val;
  transitionTo(@doneBob);
}

@{doneAlice, doneBob}
calculateTotal() {
  total = valueAlice + valueBob;
  transitionTo(@totalCalculated);
}

@totalCalculated
end() {
  terminate();
}

@totalCalculated [roles: {alice, bob}]
proposeNewTotal(int newTotal) {
  proposedNewTotal = newTotal;
  if (sender() == alice) {
    counterparty = bob;
    transitionTo(@agreeAmendment);
  } else {
    if (sender() == bob) {
    counterparty = alice;
    transitionTo(@agreeAmendment);
    } else {
      stay();
    }
  }

}

@agreeAmendment [role: counterparty]
agreeAmendment(bool agrees) {
  if (agrees) {
    total = proposedNewTotal;
  };
  transitionTo(@totalCalculated);
}
"""
```

### 3. Create a new contract with Alice's account
```python
contract_tx, contract_address = rpc.uplink_create_contract(
                                      alice_sk,
                                      alice_account_addr,
                                      amendment_script)
```

### 4. Check callable methods
A contract is a graph principally composed by states and methods.
The state of the contract determines the callable methods.
A contract always starts in the "init" state.
The RPC `uplink_get_contract_callable` function will return the callable methods of a specific contract,
depending on its state.

```python
rpc.uplink_get_contract_callable(contract_address)
```

We can see there's only one callable method, `init`, that requires two arguments:
the two account addresses of the parties involved.

### 5. Call contract methods
```python
init_call_contract_tx = rpc.uplink_call_contract(
                              bob_sk,
                              bob_account_addr,
                              contract_address,
                              "init",
                              [VAccount (alice_account_addr), VAccount (bob_account_addr)])
```

We can always check the status of a transaction. We should see that our transaction is "Accepted".

```python
rpc.uplink_get_transaction_status(init_call_contract_tx)

```

The contract should have now transitioned to `todoAlice` and `todoBob`.
We should now see that the new callable methods are `setValueAlice` and `setValueBob`.
Note that `setValueAlice` can only be called by Alice, whereas `setValueBob` can only be called by Bob.
To learn more about method preconditions see its [section](https://www.adjoint.io/docs/workflows.html?highlight=precondition#method-preconditions) in Adjoint docs.

```python
rpc.uplink_get_contract_callable(contract_address)
```

Alice now sets her value
```python
alice_value = 10
rpc.uplink_call_contract(
      alice_sk,
      alice_account_addr,
      contract_address,
      "setValueAlice",
      [VInt (alice_value)])
```

Bob sets his value, too
```python
bob_value = 5
rpc.uplink_call_contract(
      bob_sk,
      bob_account_addr,
      contract_address,
      "setValueBob",
      [VInt (bob_value)])
```

The contract should have now transitioned to `@{doneAlice, doneBob}`, where the only callable method is `calculateTotal`.
```
rpc.uplink_call_contract(
      alice_sk,
      alice_account_addr,
      contract_address,
      "calculateTotal",
      [])
```

### 6. Terminate

In our example, both Bob and Alice agree with the total value, so we can finally call `terminate` and set the workflow to its
`terminal` state.

```
rpc.uplink_call_contract(
      bob_sk,
      bob_account_addr,
      contract_address,
      "end",
      [])
```

There is another variant, `proposeNewTotal`, once we call `calculateTotal`, but we leave them as an exercise to the reader.
