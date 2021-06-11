// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelin/contracts/math/Math.sol";

contract RescueStrategy is BaseStrategyInitializable {
    constructor(address _vault) public BaseStrategyInitializable(_vault) {}

    function cloneRescueStrategy(address _vault)
        external
        returns (address newStrategy)
    {
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStrategy := create(0, clone_code, 0x37)
        }

        RescueStrategy(newStrategy).initialize(
            _vault,
            msg.sender,
            msg.sender,
            msg.sender
        );
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "RescueMasterchef";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return want.balanceOf(address(this));
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
        uint256 wantBal = want.balanceOf(address(this));

        uint256 debt = vault.strategies(address(this)).totalDebt;
        _debtPayment = Math.min(wantBal, _debtOutstanding);

        if (wantBal > debt) {
            _profit = wantBal - debt;
        } else {
            _loss = debt - wantBal;
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {}

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 wantBal = want.balanceOf(address(this));
        _liquidatedAmount = Math.min(wantBal, _amountNeeded);
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {}

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}
}
