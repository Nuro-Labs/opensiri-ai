import SwiftUI

@main
struct OpenSiriAIApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        WindowGroup("opensiri-ai") {
            PaletteView().environmentObject(state).frame(minWidth: 760, minHeight: 520)
        }
        Settings { SettingsView().environmentObject(state) }
    }
}
