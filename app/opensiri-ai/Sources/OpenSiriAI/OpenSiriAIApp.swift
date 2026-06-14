import SwiftUI

@main
struct OpenSiriAIApp: App {
    @State private var state = AppState()

    init() {
        HotKeyManager.shared.register()
    }

    var body: some Scene {
        WindowGroup("opensiri-ai") {
            PaletteView()
                .environment(state)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        Settings {
            SettingsView()
                .environment(state)
        }
    }
}

extension Notification.Name {
    static let focusPalette = Notification.Name("OpenSiriFocusPalette")
}
