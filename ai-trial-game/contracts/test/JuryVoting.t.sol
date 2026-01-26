// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/JuryVoting.sol";

contract JuryVotingTest is Test {
    JuryVoting voting;
    address juror1 = address(0x1);
    address juror2 = address(0x2);
    address juror3 = address(0x3);

    function setUp() public {
        voting = new JuryVoting(3);
    }

    // ============ Task 1.1 Tests ============

    function test_InitialState() public view {
        assertEq(voting.totalJurors(), 3);
        assertEq(voting.guiltyVotes(), 0);
        assertEq(voting.notGuiltyVotes(), 0);
        assertEq(voting.votingClosed(), false);
    }

    // ============ Task 1.2 Tests ============

    function test_Vote() public {
        vm.prank(juror1);
        voting.vote(true); // guilty

        assertEq(voting.guiltyVotes(), 1);
        assertEq(voting.hasVoted(juror1), true);
    }

    function test_VoteNotGuilty() public {
        vm.prank(juror1);
        voting.vote(false); // not guilty

        assertEq(voting.notGuiltyVotes(), 1);
    }

    function test_CannotVoteTwice() public {
        vm.prank(juror1);
        voting.vote(true);

        vm.prank(juror1);
        vm.expectRevert("Already voted");
        voting.vote(false);
    }

    function test_VotingCloses() public {
        vm.prank(juror1);
        voting.vote(true);
        vm.prank(juror2);
        voting.vote(true);
        vm.prank(juror3);
        voting.vote(false);

        assertEq(voting.votingClosed(), true);
    }

    // ============ Task 1.3 Tests ============

    function test_GetVoteState() public {
        vm.prank(juror1);
        voting.vote(true);

        (uint g, uint ng, uint total, bool closed) = voting.getVoteState();
        assertEq(g, 1);
        assertEq(ng, 0);
        assertEq(total, 1);
        assertEq(closed, false);
    }

    function test_GetVerdict_Guilty() public {
        vm.prank(juror1);
        voting.vote(true);
        vm.prank(juror2);
        voting.vote(true);
        vm.prank(juror3);
        voting.vote(false);

        string memory verdict = voting.getVerdict();
        assertEq(verdict, "GUILTY");
    }

    function test_GetVerdict_NotGuilty() public {
        vm.prank(juror1);
        voting.vote(false);
        vm.prank(juror2);
        voting.vote(false);
        vm.prank(juror3);
        voting.vote(true);

        string memory verdict = voting.getVerdict();
        assertEq(verdict, "NOT_GUILTY");
    }

    function test_GetVerdict_RevertsIfNotClosed() public {
        vm.expectRevert("Voting not closed");
        voting.getVerdict();
    }

    // ============ Boundary Tests ============

    function test_CannotVoteAfterClosed() public {
        vm.prank(juror1);
        voting.vote(true);
        vm.prank(juror2);
        voting.vote(true);
        vm.prank(juror3);
        voting.vote(false);

        // Voting is now closed
        address juror4 = address(0x4);
        vm.prank(juror4);
        vm.expectRevert("Voting closed");
        voting.vote(true);
    }
}
