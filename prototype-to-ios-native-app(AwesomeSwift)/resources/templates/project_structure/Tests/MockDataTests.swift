import XCTest
@testable import {{project_name}}

/// 纯逻辑单测：不依赖网络与 UI，可直接 `Cmd+U` 运行
final class MockDataTests: XCTestCase {

    func testPaginationSlicesByPageSize() {
        let first = MockData.pageSkills(page: 0, pageSize: 10, keyword: nil)
        let second = MockData.pageSkills(page: 1, pageSize: 10, keyword: nil)

        XCTAssertEqual(first.count, 10)
        XCTAssertEqual(second.count, 2)

        let allIDs = Set(first.map(\.skillID) + second.map(\.skillID))
        XCTAssertEqual(allIDs.count, 12)
    }

    func testKeywordFiltersItems() {
        let result = MockData.pageSkills(page: 0, pageSize: 10, keyword: "吉他")

        XCTAssertFalse(result.isEmpty)
        XCTAssertTrue(result.allSatisfy { $0.title.contains("吉他") || $0.detail.contains("吉他") })
    }

    func testDetailLookup() {
        XCTAssertNotNil(MockData.skill(id: "1"))
        XCTAssertNil(MockData.skill(id: "not-exist"))
    }

    func testMockLoginRejectsShortPassword() {
        XCTAssertNil(MockData.login(username: "u", password: "123"))
        XCTAssertNotNil(MockData.login(username: "u", password: "123456"))
    }
}
