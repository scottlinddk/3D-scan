import Foundation

public enum DetailLevel: String, CaseIterable {
    case preview, reduced, medium, full, raw
}

public struct Options: Equatable {
    public let input: URL
    public let output: URL
    public let detail: DetailLevel

    public enum ParseError: Error, Equatable {
        case usage
        case unknownDetail(String)
        case outputMustBeUSDZ
    }

    /// `scan3d-object-capture <photos dir> <out.usdz> [--detail preview|reduced|medium|full|raw]`
    public static func parse(_ args: [String]) throws -> Options {
        var positional: [String] = []
        var detail = DetailLevel.full
        var i = 0
        while i < args.count {
            if args[i] == "--detail" {
                guard i + 1 < args.count else { throw ParseError.usage }
                guard let d = DetailLevel(rawValue: args[i + 1]) else {
                    throw ParseError.unknownDetail(args[i + 1])
                }
                detail = d
                i += 2
            } else {
                positional.append(args[i])
                i += 1
            }
        }
        guard positional.count == 2 else { throw ParseError.usage }
        let output = URL(fileURLWithPath: positional[1])
        guard output.pathExtension.lowercased() == "usdz" else { throw ParseError.outputMustBeUSDZ }
        return Options(
            input: URL(fileURLWithPath: positional[0], isDirectory: true),
            output: output,
            detail: detail
        )
    }
}
