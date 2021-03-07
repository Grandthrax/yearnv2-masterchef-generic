import pytest
import brownie
from brownie import Wei, accounts, Contract, config


@pytest.mark.require_network("mainnet-fork")
def test_clone(
    chain,
    gov,
    strategist,
    rewards,
    keeper,
    strategy,
    Strategy,
    vault,
    bdp_masterchef,
    bdp,
    router,
    pid
):
    # Shouldn't be able to call initialize again
    with brownie.reverts():
        strategy.initialize(
            vault,
            strategist,
            rewards,
            keeper,
            bdp_masterchef,
            bdp,
            router,
            pid,
            {"from": gov},
        )

    # Clone the strategy
    tx = strategy.cloneMasterchef(
        vault,
        strategist,
        rewards,
        keeper,
        bdp_masterchef,
        bdp,
        router,
        pid,
        {"from": gov},
    )
    new_strategy = Strategy.at(tx.return_value)

    # Shouldn't be able to call initialize again
    with brownie.reverts():
        new_strategy.initialize(
            vault,
            strategist,
            rewards,
            keeper,
            bdp_masterchef,
            bdp,
            router,
            pid,
            {"from": gov},
        )


    # TODO: do a migrate and test a harvest
