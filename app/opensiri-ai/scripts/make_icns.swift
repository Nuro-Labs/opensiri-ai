import AppKit
import Foundation

let svgPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "Sources/OpenSiriAI/icon.svg"
let targetIcnsPath = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "AppIcon.icns"

guard let nsImage = NSImage(contentsOfFile: svgPath) else {
    print("Failed to load SVG at \(svgPath)")
    exit(1)
}

let fm = FileManager.default
let iconsetDir = URL(fileURLWithPath: "AppIcon.iconset")
try? fm.removeItem(at: iconsetDir)
try? fm.createDirectory(at: iconsetDir, withIntermediateDirectories: true)

let sizes = [16, 32, 64, 128, 256, 512]
for size in sizes {
    for scale in [1, 2] {
        let actualSize = CGFloat(size * scale)
        let imgSize = NSSize(width: actualSize, height: actualSize)
        
        // Render SVG to image at exact resolution
        let rep = NSCustomImageRep(size: imgSize, flipped: false) { rect in
            nsImage.draw(in: rect, from: .zero, operation: .copy, fraction: 1.0)
            return true
        }
        let targetImg = NSImage(size: imgSize)
        targetImg.addRepresentation(rep)
        
        guard let tiffData = targetImg.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData),
              let pngData = bitmap.representation(using: .png, properties: [:]) else {
            continue
        }
        
        let suffix = scale == 2 ? "@2x" : ""
        let filename = "icon_\(size)x\(size)\(suffix).png"
        let fileURL = iconsetDir.appendingPathComponent(filename)
        try? pngData.write(to: fileURL)
    }
}

// Run iconutil
let process = Process()
process.executableURL = URL(fileURLWithPath: "/usr/bin/iconutil")
process.arguments = ["-c", "icns", "AppIcon.iconset", "-o", targetIcnsPath]
try? process.run()
process.waitUntilExit()

// Cleanup iconset
try? fm.removeItem(at: iconsetDir)
print("Successfully generated \(targetIcnsPath) from \(svgPath)")
