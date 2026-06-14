import AppKit
import SwiftUI

struct FloatingWindowConfigurator: NSViewRepresentable {
    let expanded: Bool

    class Coordinator: NSObject {
        var lastExpandedState: Bool? = nil
        var resignObserver: Any? = nil

        deinit {
            if let obs = resignObserver {
                NotificationCenter.default.removeObserver(obs)
            }
        }
    }

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
        window.titleVisibility = .hidden
        window.titlebarAppearsTransparent = true
        window.styleMask.insert(.fullSizeContentView)
        window.isMovableByWindowBackground = true
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = true
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .transient]
        window.standardWindowButton(.closeButton)?.isHidden = false
        window.standardWindowButton(.miniaturizeButton)?.isHidden = false
        window.standardWindowButton(.zoomButton)?.isHidden = false
        window.makeKeyAndOrderFront(nil)

        if coordinator.resignObserver == nil {
            coordinator.resignObserver = NotificationCenter.default.addObserver(
                forName: NSApplication.didResignActiveNotification,
                object: nil,
                queue: .main
            ) { [weak window] _ in
                DispatchQueue.main.async {
                    window?.orderOut(nil)
                }
            }
        }

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
