import SwiftUI

@main
struct OpenSiriAIApp: App {
    @StateObject private var state = AppState()

    init() {
        HotKeyManager.shared.register()
    }

    var body: some Scene {
        WindowGroup("opensiri-ai") {
            PaletteView().environmentObject(state).frame(minWidth: 760, minHeight: 520)
        }
        Settings { SettingsView().environmentObject(state) }
    }
}

extension Notification.Name {
    static let focusPalette = Notification.Name("OpenSiriFocusPalette")
}
