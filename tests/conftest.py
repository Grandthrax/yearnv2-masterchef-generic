import pytest
from brownie import config
from brownie import Contract


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]

@pytest.fixture
def whale(accounts):
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0xBa37B002AbaFDd8E89a1995dA52740bbC013D992", force=True)

    # lots of weth account
    #wethAcc = accounts.at("0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b", force=True)
    #weth.approve(acc, 2 ** 256 - 1, {"from": wethAcc})
    #weth.transfer(acc, weth.balanceOf(wethAcc), {"from": wethAcc})

    #assert weth.balanceOf(acc) > 0
    yield acc
    

@pytest.fixture
def yfi(interface):
    yield interface.ERC20("0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e")

@pytest.fixture
def bdp_masterchef(interface):
    yield interface.ERC20("0x0De845955E2bF089012F682fE9bC81dD5f11B372")

@pytest.fixture
def bdp(interface):
    yield interface.ERC20("0xf3dcbc6D72a4E1892f7917b7C43b74131Df8480e")

@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def token(yfi):
    
    yield yfi


@pytest.fixture
def amount(accounts, token):
    amount = 10_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0xd551234ae421e3bcba99a0da6d736074f22192ff", force=True)
    token.transfer(accounts[0], amount, {"from": reserve})
    yield amount


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    yield Contract(token_address)


@pytest.fixture
def weth_amout(gov, weth):
    weth_amout = 10 ** weth.decimals()
    gov.transfer(weth, weth_amout)
    yield weth_amout


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(strategist, keeper, vault, token, weth, Strategy, gov, bdp_masterchef, bdp):
    pid = 8
    router = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    path = [bdp, weth, token]
    strategy = strategist.deploy(Strategy, vault, bdp_masterchef, bdp,router, pid)
    strategy.setRouter(router, path, {"from": gov})


    strategy.setKeeper(keeper)
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy
