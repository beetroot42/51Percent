// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title JuryVoting - 区块链陪审团投票合约
/// @notice 用于AI审判游戏的陪审员投票系统
contract JuryVoting {
    // ============ 状态变量 ============

    /// @notice 陪审员总数
    uint public totalJurors;

    /// @notice 有罪票数
    uint public guiltyVotes;

    /// @notice 无罪票数
    uint public notGuiltyVotes;

    /// @notice 投票是否结束
    bool public votingClosed;

    /// @notice 记录地址是否已投票
    mapping(address => bool) public hasVoted;

    /// @notice 记录地址的投票选择 (true=有罪)
    mapping(address => bool) public votedGuilty;

    // ============ 事件 ============

    /// @notice 投票事件
    event Voted(address indexed juror, bool guilty);

    /// @notice 投票结束事件
    event VotingClosed(string verdict, uint guiltyVotes, uint notGuiltyVotes);

    // ============ 构造函数 ============

    /// @notice 初始化合约
    /// @param _totalJurors 陪审员总数
    constructor(uint _totalJurors) {
        // TODO: 实现构造函数
        // - 设置totalJurors
        // - 验证_totalJurors > 0
    }

    // ============ 外部函数 ============

    /// @notice 陪审员投票
    /// @param guilty true表示投有罪，false表示投无罪
    function vote(bool guilty) external {
        // TODO: 实现投票逻辑
        // - 检查是否已投票 (require !hasVoted[msg.sender])
        // - 检查投票是否已结束 (require !votingClosed)
        // - 记录投票
        // - 更新票数
        // - 检查是否所有人都投票了，如果是则关闭投票
        // - 触发Voted事件
    }

    /// @notice 获取当前投票状态
    /// @return _guiltyVotes 有罪票数
    /// @return _notGuiltyVotes 无罪票数
    /// @return _totalVoted 已投票人数
    /// @return _closed 投票是否结束
    function getVoteState() external view returns (
        uint _guiltyVotes,
        uint _notGuiltyVotes,
        uint _totalVoted,
        bool _closed
    ) {
        // TODO: 实现状态查询
    }

    /// @notice 获取最终判决
    /// @return verdict "GUILTY" 或 "NOT_GUILTY"
    function getVerdict() external view returns (string memory verdict) {
        // TODO: 实现判决查询
        // - 检查投票是否已结束 (require votingClosed)
        // - 比较guiltyVotes和notGuiltyVotes
        // - 返回结果
    }

    /// @notice 强制结束投票（管理员功能）
    function closeVoting() external {
        // TODO: 实现强制结束
        // - 可选：添加onlyOwner修饰符
        // - 设置votingClosed = true
        // - 触发VotingClosed事件
    }
}
