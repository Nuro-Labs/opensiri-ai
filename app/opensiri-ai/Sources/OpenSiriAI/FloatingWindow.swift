import AppKit
import SwiftUI

struct FloatingWindowConfigurator: NSViewRepresentable {
    let expanded: Bool

    class Coordinator: NSObject { var lastExpandedState: Bool? = nil }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeNSView(context: Context) -> NSView { NSView(frame: .zero) }

    func updateNSView(_ view: NSView, context: Context) {
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            
            if expanded {
                window.styleMask.insert(.resizable)
            } else {
                window.styleMask.remove(.resizable)
            }
            
            configureWindow(window, coordinator: context.coordinator)
        }
    }

    private func configureWindow(_ window: NSWindow, coordinator: Coordinator) {
        window.title = "OpenSiri"
        window.titleVisibility = .visible
        window.titlebarAppearsTransparent = false
        window.styleMask.remove(.fullSizeContentView)
        window.isMovableByWindowBackground = false
        window.backgroundColor = NSColor.windowBackgroundColor
        window.isOpaque = true
        window.hasShadow = true
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window.standardWindowButton(.closeButton)?.isHidden = false
        window.standardWindowButton(.miniaturizeButton)?.isHidden = false
        window.standardWindowButton(.zoomButton)?.isHidden = false
        window.makeKeyAndOrderFront(nil)

        // Only transition size when expanded state actually shifts
        if coordinator.lastExpandedState != expanded {
            coordinator.lastExpandedState = expanded
            
            let target = expanded ? NSSize(width: 980, height: 720) : NSSize(width: 720, height: 128)
            var frame = window.frame
            frame.size = target
            if let screen = window.screen ?? NSScreen.main {
                let visible = screen.visibleFrame
                frame.origin.x = visible.midX - target.width / 2
                frame.origin.y = visible.maxY - target.height - 64
            }
            window.setFrame(frame, display: true, animate: true)
        }
    }
}

extension Notification.Name {
    static let centerOpenSiriWindow = Notification.Name("CenterOpenSiriWindow")
}
