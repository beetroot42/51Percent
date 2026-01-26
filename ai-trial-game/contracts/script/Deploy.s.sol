// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/JuryVoting.sol";

contract DeployScript is Script {
    function run() external {
        // TODO: 实现部署脚本
        // - 从环境变量读取私钥
        // - 设置陪审员数量
        // - 部署合约
        // - 输出合约地址

        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        uint256 totalJurors = 3; // MVP: 3个陪审员

        vm.startBroadcast(deployerPrivateKey);

        JuryVoting voting = new JuryVoting(totalJurors);

        vm.stopBroadcast();

        console.log("JuryVoting deployed at:", address(voting));
    }
}
