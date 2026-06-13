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
            Section("Quick Source Toggles") {
                Toggle("Hypersave Memory", isOn: $state.enableMemory)
                Toggle("Files / Finder Selection", isOn: $state.enableFiles)
                Toggle("Web / World Knowledge", isOn: $state.enableWeb)
                Toggle("Visual / Screenshot", isOn: $state.enableVisual)
                Toggle("Live Accessibility Tree", isOn: $state.liveAX)
                Button("Save Source Settings") { state.persist() }
            }
            Section("Safety") {
                Text("Destructive, send, payment, credential, and network actions are intercepted before execution.").foregroundStyle(.secondary)
            }
            Section("Sources") {
                ForEach(sourceManifests) { source in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(source.title).font(.headline)
                            Spacer()
                            Text(source.sensitivity).font(.caption).padding(.horizontal, 8).padding(.vertical, 3).background(Color.secondary.opacity(0.12)).clipShape(Capsule())
                        }
                        Text("Read: \(source.read)").font(.caption).foregroundStyle(.secondary)
                        Text("Write: \(source.write)").font(.caption).foregroundStyle(.secondary)
                    }.padding(.vertical, 4)
                }
            }
        }.padding(24).frame(width: 560)
    }
}
