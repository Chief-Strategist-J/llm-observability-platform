// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Tracep",
    platforms: [
        .macOS(.v12),
    ],
    products: [
        .library(
            name: "Tracep",
            targets: ["Tracep"]
        ),
    ],
    dependencies: [
        .package(
            url: "https://github.com/open-telemetry/opentelemetry-swift",
            from: "1.9.1"
        ),
    ],
    targets: [
        .target(
            name: "Tracep",
            dependencies: [
                .product(name: "OpenTelemetryApi",       package: "opentelemetry-swift"),
                .product(name: "OpenTelemetrySdk",       package: "opentelemetry-swift"),
                .product(name: "OpenTelemetryProtocolExporterHTTP", package: "opentelemetry-swift"),
            ],
            path: "Sources/Tracep"
        ),
        .testTarget(
            name: "TracepTests",
            dependencies: ["Tracep"],
            path: "Tests/TracepTests"
        ),
    ]
)
