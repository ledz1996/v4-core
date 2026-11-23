// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract MUPPETS is IERC20 {
    string public constant name = "MUPPETS";
    string public constant symbol = "MUPPETS";
    uint8 public constant decimals = 18;
    uint256 private _totalSupply = 1000000000 * 10**uint256(decimals);

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    mapping(address => bool) private _excludedFromDividends;

    uint256 public dividendPool;
    uint256 public constant DIVIDEND_PERCENTAGE = 1;

    address[] private holders;
    mapping(address => bool) private isHolder;

    event DividendsDistributed(uint256 amount);

    constructor() {
        _balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    function totalSupply() public view override returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) public view override returns (uint256) {
        return _balances[account];
    }

    function transfer(address recipient, uint256 amount) public override returns (bool) {
        require(recipient != address(0), "MUPPETS: transfer to the zero address");
        require(_balances[msg.sender] >= amount, "MUPPETS: insufficient balance");

        uint256 dividendFee = (amount * DIVIDEND_PERCENTAGE) / 100;
        uint256 amountAfterFee = amount - dividendFee;

        _balances[msg.sender] -= amount;
        _balances[recipient] += amountAfterFee;
        dividendPool += dividendFee;

        emit Transfer(msg.sender, recipient, amountAfterFee);

        if (!isHolder[recipient]) {
            holders.push(recipient);
            isHolder[recipient] = true;
        }

        distributeDividends();
        return true;
    }

    function allowance(address owner, address spender) public view override returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) public override returns (bool) {
        require(spender != address(0), "MUPPETS: approve to the zero address");
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool) {
        require(sender != address(0), "MUPPETS: transfer from the zero address");
        require(recipient != address(0), "MUPPETS: transfer to the zero address");
        require(_balances[sender] >= amount, "MUPPETS: insufficient balance");
        require(_allowances[sender][msg.sender] >= amount, "MUPPETS: transfer amount exceeds allowance");

        uint256 dividendFee = (amount * DIVIDEND_PERCENTAGE) / 100;
        uint256 amountAfterFee = amount - dividendFee;

        _balances[sender] -= amount;
        _balances[recipient] += amountAfterFee;
        _allowances[sender][msg.sender] -= amount;
        dividendPool += dividendFee;

        emit Transfer(sender, recipient, amountAfterFee);

        if (!isHolder[recipient]) {
            holders.push(recipient);
            isHolder[recipient] = true;
        }

        distributeDividends();
        return true;
    }

    function distributeDividends() private {
        if (dividendPool == 0) return;

        uint256 totalEligibleBalance = 0;
        for (uint256 i = 0; i < holders.length; i++) {
            if (!_excludedFromDividends[holders[i]]) {
                totalEligibleBalance += _balances[holders[i]];
            }
        }

        if (totalEligibleBalance == 0) return;

        for (uint256 i = 0; i < holders.length; i++) {
            address holder = holders[i];
            if (_excludedFromDividends[holder]) continue;

            uint256 share = (_balances[holder] * dividendPool) / totalEligibleBalance;
            if (share > 0) {
                _balances[holder] += share;
                emit Transfer(address(this), holder, share);
            }
        }

        dividendPool = 0;
        emit DividendsDistributed(dividendPool);
    }
}
