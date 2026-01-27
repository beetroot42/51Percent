// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/JuryVoting.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        address juror1 = vm.envAddress("JUROR_1");
        address juror2 = vm.envAddress("JUROR_2");
        address juror3 = vm.envAddress("JUROR_3");
        address juror4 = vm.envAddress("JUROR_4");
        address juror5 = vm.envAddress("JUROR_5");
        address[5] memory jurors = [juror1, juror2, juror3, juror4, juror5];

        vm.startBroadcast(deployerPrivateKey);

        JuryVoting voting = new JuryVoting(jurors);

        vm.stopBroadcast();

        console.log("JuryVoting deployed at:", address(voting));
    }
}
