import Foundation
import ObjectCaptureCLI
import RealityKit

// Runs Apple Object Capture (PhotogrammetrySession) on a folder of photos and writes a USDZ.
// Exit codes: 0 ok, 2 bad arguments, 3 unsupported hardware, 4 reconstruction failed.

func fail(_ message: String, code: Int32) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(code)
}

let options: Options
do {
    options = try Options.parse(Array(CommandLine.arguments.dropFirst()))
} catch {
    fail("usage: scan3d-object-capture <photos dir> <out.usdz> [--detail preview|reduced|medium|full|raw] (\(error))", code: 2)
}

guard PhotogrammetrySession.isSupported else {
    fail("Object Capture is not supported on this Mac", code: 3)
}

func requestDetail(_ d: DetailLevel) -> PhotogrammetrySession.Request.Detail {
    switch d {
    case .preview: return .preview
    case .reduced: return .reduced
    case .medium: return .medium
    case .full: return .full
    case .raw: return .raw
    }
}

let session: PhotogrammetrySession
do {
    session = try PhotogrammetrySession(input: options.input)
    try session.process(requests: [.modelFile(url: options.output, detail: requestDetail(options.detail))])
} catch {
    fail("could not start reconstruction: \(error)", code: 4)
}

// SIGTERM from the worker (cancel) stops the session cleanly.
signal(SIGTERM, SIG_IGN)
let term = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
term.setEventHandler { session.cancel() }
term.resume()

Task {
    do {
        for try await output in session.outputs {
            switch output {
            case .requestComplete:
                exit(0)
            case .requestError(_, let error):
                fail("reconstruction failed: \(error)", code: 4)
            case .processingCancelled:
                fail("cancelled", code: 4)
            case .invalidSample(let id, let reason):
                FileHandle.standardError.write(Data("skipped photo \(id): \(reason)\n".utf8))
            default:
                break
            }
        }
    } catch {
        fail("session error: \(error)", code: 4)
    }
}
dispatchMain()
