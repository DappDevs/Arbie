pragma solidity ^0.4.24;

import "depends/openzeppelin/contracts/token/ERC20/ERC20.sol";
import "depends/openzeppelin/contracts/token/ERC20/ERC20Detailed.sol";

contract DemoERC20 is ERC20, ERC20Detailed {
    constructor (
        string name,
        string symbol,
        uint8 decimals,
        uint initialSupply
    )
        public
        ERC20Detailed(name, symbol, decimals)
    {
        _mint(msg.sender, initialSupply);
    }
}
