import XCTest
import CryptoKit

// Source-only test. It is absent from the retained compiled UIControl runner.
// The host collector independently brackets this test with exact own PID/path
// queries. This test itself cannot prove the native PID or imported game scene.
final class OwnWindowStillTests: XCTestCase {
    @MainActor
    func testOwnForegroundStill() throws {
        continueAfterFailure = false
        let env = ProcessInfo.processInfo.environment
        let raw = try XCTUnwrap(env["ANYPS5_STILL_CONTEXT_JSON"])
        let context = try JSONSerialization.jsonObject(with: Data(raw.utf8)) as? [String: Any]
        let expected = try XCTUnwrap(context)
        XCTAssertEqual(expected["bundle"] as? String, "com.buberlo.anyps5ipad")
        let generation = try XCTUnwrap(expected["generation"] as? String)
        XCTAssertNotNil(UUID(uuidString: generation))
        let pid = try XCTUnwrap(expected["ownedMainPID"] as? Int)
        XCTAssertGreaterThan(pid, 0)
        let identity = try XCTUnwrap(expected["contextSha256"] as? String)
        XCTAssertEqual(identity.count, 64)

        // No activate(), launch(), terminate(), touch, tree dump or state loop.
        let app = XCUIApplication(bundleIdentifier: "com.buberlo.anyps5ipad")
        let before = app.state
        XCTAssertEqual(before, .runningForeground)
        let screenshot = app.screenshot()
        let after = app.state
        XCTAssertEqual(after, .runningForeground)
        let png = screenshot.pngRepresentation
        XCTAssertFalse(png.isEmpty)
        XCTAssertLessThanOrEqual(png.count, 20 * 1024 * 1024)
        let image = try XCTUnwrap(screenshot.image.cgImage)
        XCTAssertGreaterThan(image.width, 0)
        XCTAssertGreaterThan(image.height, 0)
        XCTAssertLessThanOrEqual(image.width, 16384)
        XCTAssertLessThanOrEqual(image.height, 16384)

        let digest = SHA256.hash(data: png).map { String(format: "%02x", $0) }.joined()
        let row: [String: Any] = [
            "schema": 1, "status": "own_application_element_still_requires_visual_review",
            "bundle": "com.buberlo.anyps5ipad", "generation": generation,
            "ownedMainPID": pid, "contextSha256": identity,
            "stateBefore": before.rawValue, "stateAfter": after.rawValue,
            "pngBytes": png.count, "pngSha256": digest,
            "pixelWidth": image.width, "pixelHeight": image.height,
            "processIdentityCheckedInsideXCTest": false,
            "gpuQualified": false, "courseObserved": false, "gamePlayable": false
        ]
        let metadata = try JSONSerialization.data(withJSONObject: row, options: [.sortedKeys])
        print("ANYPS5_OWN_STILL " + String(decoding: metadata, as: UTF8.self))
        let attachment = XCTAttachment(data: png, uniformTypeIdentifier: "public.png")
        attachment.name = "own-application-still.png"
        attachment.lifetime = .keepAlways
        add(attachment)
        let details = XCTAttachment(data: metadata, uniformTypeIdentifier: "public.json")
        details.name = "own-application-still.json"
        details.lifetime = .keepAlways
        add(details)
    }
}
