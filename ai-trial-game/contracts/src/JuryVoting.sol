// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title JuryVoting - Blockchain Jury Voting Contract
/// @notice Jury voting system for the AI Trial game
contract JuryVoting {
    // ============ State Variables ============

    /// @notice Total number of jurors
    uint public totalJurors;

    /// @notice Juror whitelist
    mapping(address => bool) public isJuror;

    /// @notice Number of guilty votes
    uint public guiltyVotes;

    /// @notice Number of not guilty votes
    uint public notGuiltyVotes;

    /// @notice Whether voting has ended
    bool public votingClosed;

    /// @notice Record whether an address has voted
    mapping(address => bool) public hasVoted;

    /// @notice Record the vote choice of an address (true=guilty)
    mapping(address => bool) public votedGuilty;

    // ============ Events ============

    /// @notice Vote event
    event Voted(address indexed juror, bool guilty);

    /// @notice Voting closed event
    event VotingClosed(string verdict, uint guiltyVotes, uint notGuiltyVotes);

    // ============ Constructor ============

    /// @notice Initialize the contract
    /// @param _jurors Fixed juror whitelist (5 addresses)
    constructor(address[5] memory _jurors) {
        totalJurors = 5;
        for (uint i = 0; i < _jurors.length; i++) {
            address juror = _jurors[i];
            require(juror != address(0), "Invalid juror");
            require(!isJuror[juror], "Duplicate juror");
            isJuror[juror] = true;
        }
    }

    /// @notice Restrict to juror addresses only
    modifier onlyJuror() {
        require(isJuror[msg.sender], "Not juror");
        _;
    }

    // ============ External Functions ============

    /// @notice Juror votes
    /// @param guilty true for guilty, false for not guilty
    function vote(bool guilty) external onlyJuror {
        require(!hasVoted[msg.sender], "Already voted");
        require(!votingClosed, "Voting closed");

        hasVoted[msg.sender] = true;
        votedGuilty[msg.sender] = guilty;

        if (guilty) {
            guiltyVotes += 1;
        } else {
            notGuiltyVotes += 1;
        }

        emit Voted(msg.sender, guilty);

        if (guiltyVotes + notGuiltyVotes >= totalJurors) {
            votingClosed = true;
            string memory verdict = guiltyVotes > notGuiltyVotes
                ? "GUILTY"
                : "NOT_GUILTY";
            emit VotingClosed(verdict, guiltyVotes, notGuiltyVotes);
        }
    }

    /// @notice Get current voting state
    /// @return _guiltyVotes Number of guilty votes
    /// @return _notGuiltyVotes Number of not guilty votes
    /// @return _totalVoted Number of votes cast
    /// @return _closed Whether voting is closed
    function getVoteState() external view returns (
        uint _guiltyVotes,
        uint _notGuiltyVotes,
        uint _totalVoted,
        bool _closed
    ) {
        _guiltyVotes = guiltyVotes;
        _notGuiltyVotes = notGuiltyVotes;
        _totalVoted = guiltyVotes + notGuiltyVotes;
        _closed = votingClosed;
    }

    /// @notice Get final verdict
    /// @return verdict "GUILTY" or "NOT_GUILTY"
    function getVerdict() external view returns (string memory verdict) {
        require(votingClosed, "Voting not closed");
        if (guiltyVotes > notGuiltyVotes) {
            return "GUILTY";
        }
        return "NOT_GUILTY";
    }
}
