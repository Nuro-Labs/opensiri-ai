import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var state: AppState
    @State private var hypersaveKey: String = ""
    @State private var keyStatus: String = ""

    var body: some View {
        Form {
            Section("Model") {
                TextField("Model URL", text: $state.modelURL)
                TextField("Model name", text: $state.modelName)
                TextField("Repo root", text: $state.repoRoot)
                Button("Save Settings") { state.persist() }
            }
            Section("Hypersave") {
                SecureField("Hypersave API key", text: $hypersaveKey)
                Button("Save to Keychain") { keyStatus = Keychain.save(service: "opensiri-ai", account: "hypersave-api-key", value: hypersaveKey) ? "Saved" : "Failed" }
                Text(keyStatus).foregroundStyle(.secondary)
            }
            Section("Safety") {
                Text("Destructive, send, payment, credential, and network actions are intercepted before execution.").foregroundStyle(.secondary)
            }
        }.padding(24).frame(width: 560)
    }
}
