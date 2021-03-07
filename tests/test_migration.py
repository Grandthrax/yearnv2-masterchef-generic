# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!


def test_migration(token, vault, strategy, Strategy, strategist, whale, gov, bdp_masterchef, bdp, router, pid):
    # Deposit to the vault and harvest
    amount = 1 *1e18
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest()
    
    tx = strategy.cloneStrategy(vault, bdp_masterchef, bdp, router, pid)
    

    # migrate to a new strategy
    new_strategy = Strategy.at(tx.return_value)
    strategy.migrate(new_strategy.address, {"from": gov})
    
    assert new_strategy.estimatedTotalAssets() >= amount
    assert strategy.estimatedTotalAssets() == 0

    new_strategy.harvest({"from": gov})

    


