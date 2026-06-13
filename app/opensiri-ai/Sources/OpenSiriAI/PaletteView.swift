import SwiftUI

struct PaletteView: View {
    @EnvironmentObject private var state: AppState
    @FocusState private var focused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading) {
                    Text("opensiri-ai").font(.system(size: 30, weight: .semibold))
                    Text("Local Mac assistant harness powered by Eliot + Hypersave").foregroundStyle(.secondary)
                }
                Spacer()
                Text(state.status).font(.caption.weight(.semibold)).padding(.horizontal, 10).padding(.vertical, 6).background(state.isRunning ? Color.orange.opacity(0.2) : Color.green.opacity(0.2)).clipShape(Capsule())
            }
            TextField("Ask for a Mac action, file comparison, reminder, or memory question...", text: $state.task)
                .textFieldStyle(.roundedBorder).font(.system(size: 20)).focused($focused).onSubmit { run() }
            HStack {
                Picker("Approval", selection: $state.approvalMode) {
                    Text("Safe deny").tag("deny")
                    Text("Ask in console").tag("console")
                    Text("Auto yes").tag("yes")
                }.frame(width: 170)
                Toggle("Memory", isOn: $state.enableMemory)
                Toggle("Mem Write", isOn: $state.enableMemoryWrite)
                Toggle("Files", isOn: $state.enableFiles)
                Toggle("Web", isOn: $state.enableWeb)
                Toggle("Visual", isOn: $state.enableVisual)
                Toggle("Live AX", isOn: $state.liveAX)
                Spacer()
                Button("Stop") { stop() }.disabled(!state.isRunning)
                Button("Transcript") { openTranscript() }.disabled(state.lastTranscript.isEmpty)
                Button("Run") { run() }.keyboardShortcut(.return, modifiers: [.command]).disabled(state.task.isEmpty || state.isRunning)
            }
            HStack { Chip("Guarded"); Chip("AX Screen"); Chip("Hypersave"); Chip("Audit"); Chip("Permissions") }
            ScrollView { Text(state.output).font(.system(.body, design: .monospaced)).frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled).padding(12) }
                .background(Color(NSColor.textBackgroundColor)).clipShape(RoundedRectangle(cornerRadius: 12))
            if !state.lastTranscript.isEmpty { Text("Transcript: \(state.lastTranscript)").font(.caption).foregroundStyle(.secondary) }
        }
        .padding(24)
        .onAppear { focused = true }
        .onReceive(NotificationCenter.default.publisher(for: .focusPalette)) { _ in focused = true }
    }

    func run() {
        guard !state.isRunning, !state.task.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        do { try HarnessBridge.run(task: state.task, state: state) }
        catch { state.output = "Failed to start harness: \(error)"; state.status = "Error"; state.isRunning = false }
    }

    func stop() { state.process?.terminate(); state.process = nil; state.isRunning = false; state.status = "Stopped" }

    func openTranscript() {
        guard !state.lastTranscript.isEmpty else { return }
        NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: state.lastTranscript)])
    }
}

struct Chip: View {
    let text: String
    init(_ text: String) { self.text = text }
    var body: some View { Text(text).font(.caption).padding(.horizontal, 10).padding(.vertical, 5).background(Color.accentColor.opacity(0.12)).clipShape(Capsule()) }
}
