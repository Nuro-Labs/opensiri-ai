import SwiftUI

@main
struct OpenSiriAIApp: App {
    @StateObject private var state = AppState()

    init() {
        HotKeyManager.shared.register()
    }

    var body: some Scene {
        WindowGroup("opensiri-ai") {
            PaletteView().environmentObject(state)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        Settings { SettingsView().environmentObject(state) }
    }
}

extension Notification.Name {
    static let focusPalette = Notification.Name("OpenSiriFocusPalette")
}
