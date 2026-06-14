import SwiftUI

struct SettingsView: View {
    @Environment(AppState.self) private var state
    @State private var hypersaveKey = ""
    @State private var visionKey = ""
    @State private var analysisKey = ""
    @State private var modelAPIKey = ""
    @State private var keyStatus = ""

    var body: some View {
        @Bindable var state = state
        VStack(spacing: 0) {
            SettingsHeader(status: keyStatus)

            TabView {
                GeneralSettingsPane(
                    state: state,
                    hypersaveKey: $hypersaveKey,
                    visionKey: $visionKey,
                    analysisKey: $analysisKey,
                    modelAPIKey: $modelAPIKey,
                    keyStatus: $keyStatus
                )
                .tabItem { Label("General", systemImage: "gearshape") }

                SourceSettingsPane(state: state, keyStatus: $keyStatus)
                    .tabItem { Label("Sources", systemImage: "switch.2") }

                SafetySettingsPane()
                    .tabItem { Label("Safety", systemImage: "checkmark.shield") }
            }
            .padding(18)
        }
        .frame(width: 760, height: 660)
        .background(.regularMaterial)
        .onAppear {
            hypersaveKey = Keychain.read(service: "opensiri-ai", account: "hypersave-api-key") ?? ""
            visionKey = Keychain.read(service: "opensiri-ai", account: "vision-api-key") ?? ""
            analysisKey = Keychain.read(service: "opensiri-ai", account: "analysis-api-key") ?? ""
            modelAPIKey = Keychain.read(service: "opensiri-ai", account: "model-api-key") ?? ""
        }
    }
}

struct SettingsHeader: View {
    let status: String

    var body: some View {
        HStack(spacing: 12) {
            BrandMark(isRunning: false)
                .frame(width: 34, height: 34)
            VStack(alignment: .leading, spacing: 2) {
                Text("OpenSiri Settings")
                    .font(.title3.weight(.semibold))
                Text(status.isEmpty ? "Local runtime preferences" : status)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 16)
        .background(.bar.opacity(0.72))
    }
}

struct GeneralSettingsPane: View {
    var state: AppState
    @Binding var hypersaveKey: String
    @Binding var visionKey: String
    @Binding var analysisKey: String
    @Binding var modelAPIKey: String
    @Binding var keyStatus: String

    var body: some View {
        @Bindable var state = state
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                SettingsPanel(title: "Assistant", icon: "cpu") {
                    SettingsField(title: "Model URL") {
                        TextField("http://127.0.0.1:8081", text: $state.modelURL)
                    }
                    SettingsField(title: "Model") {
                        TextField("default_model", text: $state.modelName)
                    }
                    SettingsField(title: "Model Key") {
                        SecureField("Keychain item", text: $modelAPIKey)
                    }
                    SettingsField(title: "Repo root") {
                        TextField("Path", text: $state.repoRoot)
                    }
                    SettingsField(title: "Approval") {
                        Picker("Approval", selection: $state.approvalMode) {
                            Text("Deny").tag("deny")
                            Text("Ask in app").tag("app")
                            Text("Ask in console").tag("console")
                            Text("Auto").tag("yes")
                        }
                        .labelsHidden()
                        .pickerStyle(.menu)
                    }
                    HStack {
                        Spacer()
                        Button("Save") {
                            state.persist()
                            let savedModelKey = Keychain.save(service: "opensiri-ai", account: "model-api-key", value: modelAPIKey)
                            keyStatus = savedModelKey ? "Settings and key saved" : "Settings saved, key save failed"
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }

                SettingsPanel(title: "Vision", icon: "viewfinder") {
                    SettingsField(title: "URL") {
                        TextField("Vision model URL", text: $state.visionModelURL)
                    }
                    SettingsField(title: "Model") {
                        TextField("Vision model name", text: $state.visionModelName)
                    }
                    SettingsField(title: "API key") {
                        SecureField("Keychain item", text: $visionKey)
                    }
                    HStack {
                        Spacer()
                        Button("Save Key") {
                            keyStatus = Keychain.save(service: "opensiri-ai", account: "vision-api-key", value: visionKey) ? "Vision key saved" : "Vision key failed"
                        }
                    }
                }

                SettingsPanel(title: "Analysis", icon: "text.magnifyingglass") {
                    SettingsField(title: "URL") {
                        TextField("Analysis model URL", text: $state.analysisModelURL)
                    }
                    SettingsField(title: "Model") {
                        TextField("Analysis model name", text: $state.analysisModelName)
                    }
                    SettingsField(title: "API key") {
                        SecureField("Keychain item", text: $analysisKey)
                    }
                    HStack {
                        Spacer()
                        Button("Save Key") {
                            keyStatus = Keychain.save(service: "opensiri-ai", account: "analysis-api-key", value: analysisKey) ? "Analysis key saved" : "Analysis key failed"
                        }
                    }
                }

                SettingsPanel(title: "Hypersave", icon: "brain.head.profile") {
                    SettingsField(title: "Base URL") {
                        TextField("https://api.hypersave.io", text: $state.hypersaveBaseURL)
                    }
                    SettingsField(title: "API key") {
                        SecureField("Keychain item", text: $hypersaveKey)
                    }
                    HStack {
                        Spacer()
                        Button("Save Key") {
                            keyStatus = Keychain.save(service: "opensiri-ai", account: "hypersave-api-key", value: hypersaveKey) ? "Hypersave key saved" : "Hypersave key failed"
                        }
                    }
                }
            }
        }
    }
}

struct SourceSettingsPane: View {
    var state: AppState
    @Binding var keyStatus: String

    private let columns = [GridItem(.adaptive(minimum: 210), spacing: 10)]

    var body: some View {
        @Bindable var state = state
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                SettingsPanel(title: "Context", icon: "display") {
                    LazyVGrid(columns: columns, spacing: 10) {
                        SourceToggleTile(icon: "brain.head.profile", title: "Memory", subtitle: "Hypersave", isOn: $state.enableMemory)
                        SourceToggleTile(icon: "square.and.pencil", title: "Memory write", subtitle: "Save facts", isOn: $state.enableMemoryWrite)
                            .onChange(of: state.enableMemoryWrite) { _, enabled in if enabled { state.enableMemory = true } }
                        SourceToggleTile(icon: "magnifyingglass.circle", title: "Local index", subtitle: "Files index", isOn: $state.enableLocalIndex)
                        SourceToggleTile(icon: "display", title: "Screen", subtitle: "Accessibility tree", isOn: $state.liveAX)
                    }
                }

                SettingsPanel(title: "Read Sources", icon: "tray.full") {
                    LazyVGrid(columns: columns, spacing: 10) {
                        SourceToggleTile(icon: "doc.text", title: "Files", subtitle: "Read", isOn: $state.enableFiles)
                        SourceToggleTile(icon: "folder", title: "Finder", subtitle: "Read", isOn: $state.enableFinder)
                        SourceToggleTile(icon: "envelope", title: "Mail", subtitle: "Read", isOn: $state.enableMail)
                        SourceToggleTile(icon: "message", title: "Messages", subtitle: "Read", isOn: $state.enableMessages)
                        SourceToggleTile(icon: "checklist", title: "Reminders", subtitle: "Read", isOn: $state.enableReminders)
                        SourceToggleTile(icon: "note.text", title: "Notes", subtitle: "Read", isOn: $state.enableNotes)
                        SourceToggleTile(icon: "calendar", title: "Calendar", subtitle: "Read", isOn: $state.enableCalendar)
                        SourceToggleTile(icon: "person.crop.circle", title: "Contacts", subtitle: "Lookup", isOn: $state.enableContacts)
                        SourceToggleTile(icon: "safari", title: "Browser", subtitle: "Tabs", isOn: $state.enableBrowser)
                        SourceToggleTile(icon: "photo", title: "Photos", subtitle: "Metadata", isOn: $state.enablePhotos)
                        SourceToggleTile(icon: "viewfinder", title: "Visual", subtitle: "OCR", isOn: $state.enableVisual)
                        SourceToggleTile(icon: "map", title: "Maps", subtitle: "Search", isOn: $state.enableMaps)
                        SourceToggleTile(icon: "music.note", title: "Music", subtitle: "Library", isOn: $state.enableMusic)
                        SourceToggleTile(icon: "waveform", title: "Podcasts", subtitle: "Library", isOn: $state.enablePodcasts)
                        SourceToggleTile(icon: "globe", title: "Web", subtitle: "Search", isOn: $state.enableWeb)
                        SourceToggleTile(icon: "gearshape", title: "System", subtitle: "Status", isOn: $state.enableSystem)
                    }
                }

                SettingsPanel(title: "Write Permissions", icon: "lock.shield") {
                    VStack(spacing: 9) {
                        PermissionToggle(title: "Finder Writes", subtitle: "Rename, copy, move, tag, compress, trash", isOn: $state.enableFinderWrite)
                        PermissionToggle(title: "Mail Send", subtitle: "Draft/send email after approval", isOn: $state.enableMailWrite)
                        PermissionToggle(title: "Message Send", subtitle: "Send iMessage/SMS after approval", isOn: $state.enableMessagesWrite)
                        PermissionToggle(title: "Reminders Write", subtitle: "Create and complete reminders after approval", isOn: $state.enableRemindersWrite)
                            .onChange(of: state.enableRemindersWrite) { _, enabled in if enabled { state.enableReminders = true } }
                        PermissionToggle(title: "Notes Write", subtitle: "Create, append, edit notes after approval", isOn: $state.enableNotesWrite)
                            .onChange(of: state.enableNotesWrite) { _, enabled in if enabled { state.enableNotes = true } }
                        PermissionToggle(title: "Browser Actions", subtitle: "Open URLs, YouTube, close tabs", isOn: $state.enableBrowserWrite)
                        PermissionToggle(title: "System Changes", subtitle: "Volume, display, dark mode, DND, lock", isOn: $state.enableSystemWrite)
                    }
                    HStack {
                        Spacer()
                        Button("Save Sources") {
                            state.persist()
                            keyStatus = "Sources saved"
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding(.top, 4)
                }
            }
        }
    }
}

struct SafetySettingsPane: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                SettingsPanel(title: "Boundary", icon: "checkmark.shield") {
                    SafetyLine(icon: "hand.raised.fill", title: "Approval required", detail: "Sends, destructive file actions, browser navigation, and system changes are intercepted before execution.")
                    SafetyLine(icon: "lock.shield.fill", title: "Private by default", detail: "Mail, Messages, Photos, Files, and local index access are opt-in.")
                    SafetyLine(icon: "doc.text.magnifyingglass", title: "Auditable", detail: "Tool calls, approvals, transcripts, and policy decisions are written to local audit files.")
                }

                SettingsPanel(title: "Manifest", icon: "list.bullet.rectangle") {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 280), spacing: 10)], spacing: 10) {
                        ForEach(sourceManifests) { source in
                            SourceManifestTile(source: source)
                        }
                    }
                }
            }
        }
    }
}

struct SettingsPanel<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .frame(width: 18)
                Text(title)
                    .font(.headline)
                Spacer()
            }
            content
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.64))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(Color.white.opacity(0.20), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct SettingsField<Content: View>: View {
    let title: String
    @ViewBuilder var content: Content

    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 92, alignment: .trailing)
            content
        }
    }
}

struct SourceToggleTile: View {
    let icon: String
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(isOn ? Color.accentColor : Color.secondary)
                .frame(width: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 13, weight: .semibold))
                Text(subtitle)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 4)
            Toggle("", isOn: $isOn)
                .labelsHidden()
                .toggleStyle(.switch)
        }
        .padding(10)
        .background(Color(nsColor: .textBackgroundColor).opacity(isOn ? 0.82 : 0.50))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

struct PermissionToggle: View {
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        Toggle(isOn: $isOn) {
            HStack(spacing: 10) {
                Image(systemName: isOn ? "lock.open.fill" : "lock.fill")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(isOn ? .orange : .secondary)
                    .frame(width: 22)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 13, weight: .semibold))
                    Text(subtitle)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .toggleStyle(.switch)
        .padding(10)
        .background(Color(nsColor: .textBackgroundColor).opacity(isOn ? 0.82 : 0.50))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

struct SafetyLine: View {
    let icon: String
    let title: String
    let detail: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(.blue)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.system(size: 13, weight: .semibold))
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
        .padding(.vertical, 4)
    }
}

struct SourceManifestTile: View {
    let source: SourceManifest

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: sourceIcon(source.title))
                    .foregroundStyle(.secondary)
                    .frame(width: 18)
                Text(source.title)
                    .font(.system(size: 13, weight: .semibold))
                    .lineLimit(1)
                Spacer()
                Text(source.sensitivity)
                    .font(.caption2.weight(.semibold))
                    .padding(.horizontal, 7)
                    .padding(.vertical, 3)
                    .background(Color.secondary.opacity(0.12))
                    .clipShape(Capsule())
            }
            Text("Read: \(source.read)")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            Text("Write: \(source.write)")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(11)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .textBackgroundColor).opacity(0.60))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}
