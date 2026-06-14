// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "OpenSiriAI",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "OpenSiriAI", targets: ["OpenSiriAI"])],
    targets: [
        .executableTarget(
            name: "OpenSiriAI",
            resources: [.process("logo.svg"), .process("icon.svg")]
        )
    ]
)
