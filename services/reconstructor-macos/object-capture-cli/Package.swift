// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "object-capture-cli",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "scan3d-object-capture", targets: ["scan3d-object-capture"])],
    targets: [
        .target(name: "ObjectCaptureCLI"),
        .executableTarget(name: "scan3d-object-capture", dependencies: ["ObjectCaptureCLI"]),
        .testTarget(name: "ObjectCaptureCLITests", dependencies: ["ObjectCaptureCLI"]),
    ]
)
