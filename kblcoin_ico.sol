// Kblcoin ICO
pragma solidity 0.4.26;

contract kblocoin_ico {

    uint256 public max_kblcoins = 1000000;
    uint256 public usd_to_kblcoins = 100;
    uint256 public total_kblcoins_bought = 0;
    
    mapping(address => uint) equity_kblcoins;
    mapping(address => uint) equity_usd;
    
    modifier can_buy_kblcoins(uint usd_invested){
        require (usd_invested * usd_to_kblcoins + total_kblcoins_bought <= max_kblcoins);
        _;
    }
    
    function equity_in_kblcoins(address investor) external constant returns (uint) {
        return equity_kblcoins[investor];
    }

    function equity_in_usd(address investor) external constant returns (uint) {
        return equity_usd[investor];
    }
    
    function buy_kblcoins(address investor, uint usd_invested) external can_buy_kblcoins(usd_invested) {
        uint kblcoins_bought = usd_invested * usd_to_kblcoins;
        equity_kblcoins[investor] += kblcoins_bought;
        equity_usd[investor] = equity_kblcoins[investor] / usd_to_kblcoins;
        total_kblcoins_bought += kblcoins_bought;
    }

    function sell_kblcoins(address investor, uint kblcoims_sold) external {
        equity_kblcoins[investor] -= kblcoims_sold;
        equity_usd[investor] = equity_kblcoins[investor] / usd_to_kblcoins;
        total_kblcoins_bought -= kblcoims_sold;
    }

}