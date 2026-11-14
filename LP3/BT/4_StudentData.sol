// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StudentData {
    struct Student {
        uint256 id;
        string name;
        uint256 marks;
    }

    Student[] public students;

    function addStudent(uint256 id, string calldata name, uint256 marks) external {
        students.push(Student(id, name, marks));
    }

    function studentCount() external view returns (uint256) {
        return students.length;
    }

    receive() external payable {}

    fallback() external payable {}
}
