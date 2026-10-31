import XCTest
@testable import ObjectCaptureCLI

final class OptionsTests: XCTestCase {
    func testDefaultsToFullDetail() throws {
        let o = try Options.parse(["/tmp/photos", "/tmp/out.usdz"])
        XCTAssertEqual(o.detail, .full)
        XCTAssertEqual(o.output.lastPathComponent, "out.usdz")
    }

    func testParsesDetailAnywhere() throws {
        let o = try Options.parse(["--detail", "medium", "/tmp/p", "/tmp/o.usdz"])
        XCTAssertEqual(o.detail, .medium)
    }

    func testRejectsBadInput() {
        XCTAssertThrowsError(try Options.parse(["/tmp/p"]))
        XCTAssertThrowsError(try Options.parse(["/tmp/p", "/tmp/o.usdz", "--detail", "ultra"])) {
            XCTAssertEqual($0 as? Options.ParseError, .unknownDetail("ultra"))
        }
        XCTAssertThrowsError(try Options.parse(["/tmp/p", "/tmp/o.obj"])) {
            XCTAssertEqual($0 as? Options.ParseError, .outputMustBeUSDZ)
        }
        XCTAssertThrowsError(try Options.parse(["/tmp/p", "/tmp/o.usdz", "--detail"]))
    }
}
