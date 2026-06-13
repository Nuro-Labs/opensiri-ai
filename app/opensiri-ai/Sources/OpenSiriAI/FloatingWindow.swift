import AppKit
import SwiftUI

struct FloatingWindowConfigurator: NSViewRepresentable {
    let expanded: Bool

    func makeNSView(context: Context) -> NSView { NSView(frame: .zero) }

    func updateNSView(_ view: NSView, context: Context) {
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            configure(window)
        }
    }

    private func configure(_ window: NSWindow) {
        window.titleVisibility = .hidden
        window.titlebarAppearsTransparent = true
        window.isMovableByWindowBackground = true
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = true
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .transient]
        window.standardWindowButton(.closeButton)?.isHidden = true
        window.standardWindowButton(.miniaturizeButton)?.isHidden = true
        window.standardWindowButton(.zoomButton)?.isHidden = true

        let target = expanded ? NSSize(width: 940, height: 690) : NSSize(width: 680, height: 138)
        if abs(window.frame.width - target.width) > 8 || abs(window.frame.height - target.height) > 8 {
            var frame = window.frame
            frame.size = target
            if let screen = window.screen ?? NSScreen.main {
                let visible = screen.visibleFrame
                frame.origin.x = visible.midX - target.width / 2
                frame.origin.y = visible.maxY - target.height - 72
            }
            window.setFrame(frame, display: true, animate: true)
        }
    }
}

extension Notification.Name {
    static let centerOpenSiriWindow = Notification.Name("CenterOpenSiriWindow")
}
