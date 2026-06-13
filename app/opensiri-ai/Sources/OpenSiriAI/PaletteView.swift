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
                    Text("Ask in app").tag("app")
                    Text("Ask in console").tag("console")
                    Text("Auto yes").tag("yes")
                }.frame(width: 170)
                Toggle("Memory", isOn: $state.enableMemory)
                Toggle("Mem Write", isOn: $state.enableMemoryWrite)
                Toggle("Files", isOn: $state.enableFiles)
                Toggle("Web", isOn: $state.enableWeb)
                Toggle("Visual", isOn: $state.enableVisual)
                Toggle("Mail", isOn: $state.enableMail)
                Toggle("Messages", isOn: $state.enableMessages)
                Toggle("Maps", isOn: $state.enableMaps)
                Toggle("Music", isOn: $state.enableMusic)
                Toggle("Live AX", isOn: $state.liveAX)
                Spacer()
                Button("Stop") { stop() }.disabled(!state.isRunning)
                Button("Transcript") { openTranscript() }.disabled(state.lastTranscript.isEmpty)
                Button("Clear") { clearConversation() }.disabled(state.isRunning)
                Button("Run") { run() }.keyboardShortcut(.return, modifiers: [.command]).disabled(state.task.isEmpty || state.isRunning)
            }
            HStack { ForEach(state.sourceChips, id: \.self) { Chip($0) } }
            if let request = state.approvalRequest { ApprovalCard(request: request, approve: approveRequest, deny: denyRequest) }
            ConversationView(messages: state.messages)
            if !state.lastTranscript.isEmpty { Text("Transcript: \(state.lastTranscript)").font(.caption).foregroundStyle(.secondary) }
            DisclosureGroup("Technical log", isExpanded: $state.showTechnicalLog) {
                ScrollView { Text(state.technicalLog.isEmpty ? "No technical output yet." : state.technicalLog).font(.system(.caption, design: .monospaced)).frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled).padding(10) }
                    .frame(height: 120)
                    .background(Color(NSColor.textBackgroundColor))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
        }
        .padding(24)
        .onAppear { focused = true }
        .onReceive(NotificationCenter.default.publisher(for: .focusPalette)) { _ in focused = true }
        .task { await pollApprovals() }
    }

    func run() {
        guard !state.isRunning, !state.task.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        if state.enableMemoryWrite { state.enableMemory = true }
        do { try HarnessBridge.run(task: state.task, state: state) }
        catch { state.output = "Failed to start harness: \(error)"; state.status = "Error"; state.isRunning = false }
    }

    func stop() { state.process?.terminate(); state.process = nil; state.isRunning = false; state.status = "Stopped" }

    func pollApprovals() async {
        while !Task.isCancelled {
            await MainActor.run { loadApprovalRequest() }
            try? await Task.sleep(for: .milliseconds(350))
        }
    }

    func loadApprovalRequest() {
        guard let dir = state.approvalDir else { return }
        let url = dir.appendingPathComponent("approval_request.json")
        guard let data = try? Data(contentsOf: url), let req = try? JSONDecoder().decode(ApprovalRequest.self, from: data) else {
            if !state.isRunning { state.approvalRequest = nil }
            return
        }
        if state.approvalRequest?.id != req.id { state.approvalRequest = req }
    }

    func approveRequest() { respondToApproval(approved: true) }
    func denyRequest() { respondToApproval(approved: false) }

    func respondToApproval(approved: Bool) {
        guard let req = state.approvalRequest, let dir = state.approvalDir else { return }
        let payload: [String: Any] = ["id": req.id, "approved": approved, "reason": approved ? "approved in app" : "denied in app"]
        if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]) {
            try? data.write(to: dir.appendingPathComponent("approval_response.json"))
        }
        state.approvalRequest = nil
    }

    func openTranscript() {
        guard !state.lastTranscript.isEmpty else { return }
        NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: state.lastTranscript)])
    }

    func clearConversation() {
        state.messages = [ChatMessage(role: .system, text: "New conversation. Ask for a Mac action, file comparison, reminder, or personal-context question.")]
        state.output = ""
        state.technicalLog = ""
    }
}

struct ConversationView: View {
    let messages: [ChatMessage]
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(messages) { msg in
                        MessageBubble(message: msg).id(msg.id)
                    }
                }
                .padding(12)
            }
            .background(Color(NSColor.textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .onChange(of: messages.count) { _, _ in
                if let last = messages.last { proxy.scrollTo(last.id, anchor: .bottom) }
            }
        }
    }
}

struct MessageBubble: View {
    let message: ChatMessage
    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 80) }
            VStack(alignment: .leading, spacing: 4) {
                Text(label).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                Text(message.text).textSelection(.enabled)
            }
            .padding(12)
            .background(background)
            .clipShape(RoundedRectangle(cornerRadius: 14))
            if message.role != .user { Spacer(minLength: 80) }
        }
    }
    var label: String {
        switch message.role { case .user: "You"; case .assistant: "opensiri-ai"; case .system: "Ready" }
    }
    var background: Color {
        switch message.role { case .user: Color.accentColor.opacity(0.18); case .assistant: Color.secondary.opacity(0.12); case .system: Color.green.opacity(0.10) }
    }
}

struct ApprovalCard: View {
    let request: ApprovalRequest
    let approve: () -> Void
    let deny: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Approval Required").font(.headline)
            Text(request.action.name).font(.system(.body, design: .monospaced))
            ForEach(request.action.args.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                Text("\(key): \(value)").font(.caption).foregroundStyle(.secondary).lineLimit(3)
            }
            HStack {
                Button("Deny", role: .cancel, action: deny)
                Button("Approve", action: approve).buttonStyle(.borderedProminent)
            }
        }
        .padding(14)
        .background(Color.orange.opacity(0.16))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

struct Chip: View {
    let text: String
    init(_ text: String) { self.text = text }
    var body: some View { Text(text).font(.caption).padding(.horizontal, 10).padding(.vertical, 5).background(Color.accentColor.opacity(0.12)).clipShape(Capsule()) }
}
