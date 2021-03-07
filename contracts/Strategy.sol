// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

interface ChefLike {
    function deposit(uint256 _pid, uint256 _amount) external;
    function withdraw(uint256 _pid, uint256 _amount) external;
    function emergencyWithdraw(uint256 _pid) external;
    function poolInfo(uint256 _pid) external view returns (address,uint,uint,uint);
    function userInfo(uint256 _pid, address user) external view returns (uint,uint);
}

// These are the core Yearn libraries
import "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";

// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public masterchef;
    address public reward;

    address private constant uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address private constant sushiswapRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F; 
    address public router;

    uint256 public pid;

    address[] public path;

    event Cloned(address indexed clone);

    constructor(address _vault, address _masterchef, address _reward, address _router, uint256 _pid) public BaseStrategy(_vault) {

        _initialize(_vault, msg.sender, msg.sender, msg.sender);
        _initializeStrat(_masterchef, _reward, _router, _pid);
    }

       
    function initializeStrat(address _vault, address _strategist, address _rewards, address _keeper, address _masterchef, address _reward, address _router, uint256 _pid) external {
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(_masterchef, _reward, _router, _pid);
    }

    function _initializeStrat(address _masterchef, address _reward, address _router, uint256 _pid) internal {
        
        require(router == uniswapRouter || router == sushiswapRouter, "incorrect router");

        // You can set these parameters on deployment to whatever you want
        maxReportDelay = 6300;
        profitFactor = 1500;
        debtThreshold = 1_000_000 * 1e18;
        masterchef = _masterchef;
        reward = _reward;
        router = _router;
        pid = _pid;

        want.safeApprove(_masterchef, uint256(-1));
        IERC20(reward).safeApprove(router, uint256(-1));
    }

    function clone(address _vault, address _masterchef, address _reward, address _router, uint256 _pid) external returns (address newStrategy) {
        newStrategy = this.clone(_vault, msg.sender, msg.sender, msg.sender, _masterchef, _reward, _router, _pid);
    }

    function clone(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper, address _masterchef, address _reward, address _router, uint256 _pid
    ) external returns (address newStrategy) {
        // Copied from https://github.com/optionality/clone-factory/blob/master/contracts/CloneFactory.sol
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(clone_code, 0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000)
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(add(clone_code, 0x28), 0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000)
            newStrategy := create(0, clone_code, 0x37)
        }

        Strategy(newStrategy).initializeStrat(_vault, _strategist, _rewards, _keeper, _masterchef, _reward, _router, _pid);

        emit Cloned(newStrategy);
    }

    function setRouter(address _router, address[] calldata _path) public onlyGovernance {
        router = _router;
        want.safeApprove(masterchef, uint256(-1));
        IERC20(reward).safeApprove(router, uint256(-1));
        path = _path;

        require(router == uniswapRouter || router == sushiswapRouter, "incorrect router");
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "StrategyMasterchefGeneric";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        (uint deposited,) = ChefLike(masterchef).userInfo(pid, address(this));
        return want.balanceOf(address(this)).add(deposited);
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        _debtPayment = _debtOutstanding;
        ChefLike(masterchef).deposit(pid, 0);

        _sell();

        uint256 assets = estimatedTotalAssets();
        uint256 wantBal = want.balanceOf(address(this));

        uint256 debt = vault.strategies(address(this)).totalDebt;

        if (assets > debt) {
            _profit = assets - debt;

            uint256 amountToFree = _profit.add(_debtPayment);

            if (amountToFree > 0 && wantBal < amountToFree) {
                liquidatePosition(amountToFree);

                uint256 newLoose = want.balanceOf(address(this));

                //if we dont have enough money adjust _debtOutstanding and only change profit if needed
                if (newLoose < amountToFree) {
                    if (_profit > newLoose) {
                        _profit = newLoose;
                        _debtPayment = 0;
                    } else {
                        _debtPayment = Math.min(newLoose - _profit, _debtPayment);
                    }
                }
            }
        }else{
            //serious loss should never happen but if it does lets record it accurately
            _loss = debt - assets;
        }

    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (emergencyExit) {
            return;
        }

        uint256 wantBalance = want.balanceOf(address(this));
        ChefLike(masterchef).deposit(pid, wantBalance);
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        
        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            uint256 amountToFree = _amountNeeded.sub(totalAssets);

            (uint deposited,) = ChefLike(masterchef).userInfo(pid, address(this));
            if(deposited < amountToFree){
                amountToFree = deposited;
            }
            if(deposited > 0){
                ChefLike(masterchef).withdraw(pid, amountToFree);
            }

            _liquidatedAmount = want.balanceOf(address(this));

        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        liquidatePosition(uint256(-1)); //withdraw all. does not matter if we ask for too much
        _sell();
    }

    //sell all function
    function _sell() internal {
        IUniswapV2Router02(router).swapExactTokensForETH(IERC20(reward).balanceOf(address(this)), uint256(0), path, address(this), now);

    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}
}