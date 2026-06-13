import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var state: AppState
    @State private var hypersaveKey = ""
    @State private var visionKey = ""
    @State private var keyStatus = ""

    var body: some View {
        TabView {
            Form {
                Section("Assistant") {
                    TextField("Model URL", text: $state.modelURL)
                    TextField("Model name", text: $state.modelName)
                    TextField("Repo root", text: $state.repoRoot)
                    Picker("Approval mode", selection: $state.approvalMode) {
                        Text("Safe deny").tag("deny")
                        Text("Ask in app").tag("app")
                        Text("Ask in console").tag("console")
                        Text("Auto approve").tag("yes")
                    }
                    Button("Save General Settings") { state.persist(); keyStatus = "Settings saved" }
                }
                Section("Vision Model") {
                    TextField("Vision model URL", text: $state.visionModelURL)
                    TextField("Vision model name", text: $state.visionModelName)
                    SecureField("Vision API key", text: $visionKey)
                    Button("Save Vision Key") { keyStatus = Keychain.save(service: "opensiri-ai", account: "vision-api-key", value: visionKey) ? "Vision key saved" : "Vision key failed" }
                }
                Section("Hypersave") {
                    TextField("Base URL", text: $state.hypersaveBaseURL)
                    SecureField("Hypersave API key", text: $hypersaveKey)
                    Button("Save Hypersave Key") { keyStatus = Keychain.save(service: "opensiri-ai", account: "hypersave-api-key", value: hypersaveKey) ? "Hypersave key saved" : "Hypersave key failed" }
                    Text(keyStatus).foregroundStyle(.secondary)
                }
            }
            .formStyle(.grouped)
            .tabItem { Label("General", systemImage: "gearshape") }

            Form {
                Section("Memory & Index") {
                    Toggle("Hypersave Memory", isOn: $state.enableMemory)
                    Toggle("Allow Memory Writes", isOn: $state.enableMemoryWrite)
                        .onChange(of: state.enableMemoryWrite) { _, enabled in if enabled { state.enableMemory = true } }
                    Toggle("Local Background Index", isOn: $state.enableLocalIndex)
                    Toggle("Live Accessibility Tree", isOn: $state.liveAX)
                }
                Section("Read Sources") {
                    Toggle("Files", isOn: $state.enableFiles)
                    Toggle("Finder", isOn: $state.enableFinder)
                    Toggle("Mail", isOn: $state.enableMail)
                    Toggle("Messages", isOn: $state.enableMessages)
                    Toggle("Calendar", isOn: $state.enableCalendar)
                    Toggle("Contacts", isOn: $state.enableContacts)
                    Toggle("Browser", isOn: $state.enableBrowser)
                    Toggle("Photos", isOn: $state.enablePhotos)
                    Toggle("Visual / Screenshot", isOn: $state.enableVisual)
                    Toggle("Maps", isOn: $state.enableMaps)
                    Toggle("Music", isOn: $state.enableMusic)
                    Toggle("Podcasts", isOn: $state.enablePodcasts)
                    Toggle("Web", isOn: $state.enableWeb)
                    Toggle("System Status", isOn: $state.enableSystem)
                }
                Section("Write Permissions") {
                    PermissionToggle(title: "Finder Writes", subtitle: "Rename, copy, move, tag, compress, trash", isOn: $state.enableFinderWrite)
                    PermissionToggle(title: "Mail Send", subtitle: "Draft/send email after approval", isOn: $state.enableMailWrite)
                    PermissionToggle(title: "Message Send", subtitle: "Send iMessage/SMS after approval", isOn: $state.enableMessagesWrite)
                    PermissionToggle(title: "Browser Actions", subtitle: "Open URLs, YouTube, close tabs", isOn: $state.enableBrowserWrite)
                    PermissionToggle(title: "System Changes", subtitle: "Volume, display, dark mode, DND, lock", isOn: $state.enableSystemWrite)
                }
                Button("Save Source Settings") { state.persist(); keyStatus = "Sources saved" }
            }
            .formStyle(.grouped)
            .tabItem { Label("Sources", systemImage: "switch.2") }

            Form {
                Section("Safety Boundary") {
                    SafetyLine(icon: "hand.raised.fill", title: "Approval required", detail: "Sends, destructive file actions, browser navigation, and system changes are intercepted before execution.")
                    SafetyLine(icon: "lock.shield.fill", title: "Private by default", detail: "Mail, Messages, Photos, Files, and local index access are opt-in.")
                    SafetyLine(icon: "doc.text.magnifyingglass", title: "Auditable", detail: "Tool calls, approvals, transcripts, and policy decisions are written to local audit files.")
                }
                Section("Source Manifest") {
                    ForEach(sourceManifests) { source in
                        VStack(alignment: .leading, spacing: 5) {
                            HStack {
                                Text(source.title).font(.headline)
                                Spacer()
                                Text(source.sensitivity).font(.caption.weight(.semibold)).padding(.horizontal, 8).padding(.vertical, 3).background(Color.secondary.opacity(0.12)).clipShape(Capsule())
                            }
                            Text("Read: \(source.read)").font(.caption).foregroundStyle(.secondary)
                            Text("Write: \(source.write)").font(.caption).foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .formStyle(.grouped)
            .tabItem { Label("Safety", systemImage: "checkmark.shield") }
        }
        .padding(18)
        .frame(width: 700, height: 620)
    }
}

struct PermissionToggle: View {
    let title: String
    let subtitle: String
    @Binding var isOn: Bool
    var body: some View {
        Toggle(isOn: $isOn) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                Text(subtitle).font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

struct SafetyLine: View {
    let icon: String
    let title: String
    let detail: String
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon).foregroundStyle(.blue).frame(width: 22)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.headline)
                Text(detail).font(.caption).foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}
