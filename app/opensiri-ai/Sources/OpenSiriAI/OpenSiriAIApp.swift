import SwiftUI

@main
struct OpenSiriAIApp: App {
    @State private var state = AppState()

    init() {
        UserDefaults.standard.set(false, forKey: "NSQuitAlwaysKeepsWindows")
        HotKeyManager.shared.register()
    }

    var body: some Scene {
        Window("opensiri-ai", id: "main") {
            PaletteView()
                .environment(state)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .defaultSize(width: 720, height: 128)
        .commands {
            CommandGroup(replacing: .newItem) { }
        }
        Settings {
            SettingsView()
                .environment(state)
        }
    }
}

extension Notification.Name {
    static let focusPalette = Notification.Name("OpenSiriFocusPalette")
}
