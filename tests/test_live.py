import brownie
from brownie import Contract
from useful_methods import genericStateOfVault, genericStateOfStrat
import random

def test_migrate_live(accounts, Strategy, token, live_vault, live_strat, chain, strategist, whale, bdp_masterchef, bdp, router, pid):
    gov = accounts.at(live_vault.governance(), force=True)
    strategist = gov
    strategy = live_strat
    vault = live_vault

    before = strategy.estimatedTotalAssets()

    tx = strategy.cloneStrategy(vault, bdp_masterchef, bdp, router, pid, {"from": gov})
    
    # migrate to a new strategy
    new_strategy = Strategy.at(tx.return_value)
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    
    assert new_strategy.estimatedTotalAssets() >= before
    assert strategy.estimatedTotalAssets() == 0

def test_live_snapshot(accounts, token, RescueStrategy, Strategy, live_vault, live_strat, chain, strategist, whale,bdp_masterchef, bdp, router, pid):
    gov = accounts.at(live_vault.governance(), force=True)
    strategist = gov
    strategy = live_strat
    vault = live_vault

    #vault.addStrategy(strategy, 9500, 0, 2**256-1, 1000, {'from': gov})
    pid = strategy.pid()
    
    new_strategy = gov.deploy(RescueStrategy, vault)

    strategy.emergencyWithdrawal(pid,{'from': gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    vault.updateStrategyDebtRatio(new_strategy, 0, {'from': gov})
    new_strategy.harvest({'from': gov})

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    genericStateOfStrat(new_strategy, token, vault)
    genericStateOfVault(vault, token)

def test_apr_live(accounts, token, live_vault, live_strat, chain, strategist, whale):
    gov = accounts.at(live_vault.governance(), force=True)
    strategist = gov
    strategy = live_strat
    vault = live_vault

    #vault.addStrategy(strategy, 9500, 0, 2**256-1, 1000, {'from': gov})

    strategy.harvest({'from': gov})

    #genericStateOfStrat(strategy, token, vault)
    #genericStateOfVault(vault, token)
    strState = vault.strategies(strategy)
    startingBalance = vault.totalAssets()
    startingReturns = strState[7]
    for i in range(1):

        waitBlock = 50
        # print(f'\n----wait {waitBlock} blocks----')
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        # print(f'\n----harvest----')
        strategy.harvest({"from": strategist})

        # genericStateOfStrat(strategy, currency, vault)
        # genericStateOfVault(vault, currency)

        profit = (vault.totalAssets() - startingBalance) / 1e18
        strState = vault.strategies(strategy)
        totalReturns = strState[7] - startingReturns
        totaleth = totalReturns / 1e18
        # print(f'Real Profit: {profit:.5f}')
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0
        # print(apr)
        print(f"implied apr: {apr:.8%}")

    vault.revokeStrategy(strategy, {'from': gov})
    strategy.harvest({'from': gov})
    assert strategy.estimatedTotalAssets() == 0
    #genericStateOfStrat(strategy, token, vault)
    #genericStateOfVault(vault, token)


def test_apr_live_weth(accounts, Strategy, weth, live_vault_weth, live_strat_weth, chain, strategist, whale):
    vault = live_vault_weth
    strategy = live_strat_weth
    gov = accounts.at(vault.governance(), force=True)
    strategist = gov
    token = weth
    print(strategy.rewards())

    #gen_len = Strategy.at('0xeE697232DF2226c9fB3F02a57062c4208f287851')

    #vault.updateStrategyDebtRatio(gen_len, 500, {"from": gov})
    #vault.addStrategy(strategy, 7200, 0, 2**256-1, 1_000, {"from": gov})

    #gen_len.harvest({'from': gov})

    #vault.addStrategy(strategy, 9500, 0, 2**256-1, 1000, {'from': gov})

    strategy.harvest({'from': gov})

    #genericStateOfStrat(strategy, token, vault)
    #genericStateOfVault(vault, token)
    strState = vault.strategies(strategy)
    startingBalance = vault.totalAssets()
    startingReturns = strState[7]
    for i in range(1):

        waitBlock = 50
        # print(f'\n----wait {waitBlock} blocks----')
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        # print(f'\n----harvest----')
        strategy.harvest({"from": strategist})

        # genericStateOfStrat(strategy, currency, vault)
        # genericStateOfVault(vault, currency)

        profit = (vault.totalAssets() - startingBalance) / 1e18
        strState = vault.strategies(strategy)
        totalReturns = strState[7] - startingReturns
        totaleth = totalReturns / 1e18
        # print(f'Real Profit: {profit:.5f}')
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0
        # print(apr)
        print(f"implied apr: {apr:.8%}")

    vault.revokeStrategy(strategy, {'from': gov})
    strategy.harvest({'from': gov})
    assert strategy.estimatedTotalAssets() == 0
    #genericStateOfStrat(strategy, token, vault)
    #genericStateOfVault(vault, token)