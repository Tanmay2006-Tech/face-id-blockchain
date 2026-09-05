import { network } from "hardhat";

const { ethers } = await network.connect();

const faceRecord = await ethers.deployContract("FaceRecord");

await faceRecord.waitForDeployment();

console.log("FaceRecord deployed to:", await faceRecord.getAddress());