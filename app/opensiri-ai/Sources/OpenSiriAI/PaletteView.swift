import SwiftUI

struct PaletteView: View {
    @EnvironmentObject private var state: AppState
    @FocusState private var focused: Bool
    @State private var expanded = false

    var body: some View {
        ZStack {
            AuroraBackdrop()
            if expanded {
                ExpandedSiriSurface(
                    state: state,
                    focused: $focused,
                    collapse: { expanded = false },
                    run: run,
                    stop: stop,
                    openTranscript: openTranscript,
                    openAudit: openAudit,
                    openHistory: openHistory,
                    clearConversation: clearConversation,
                    approveRequest: approveRequest,
                    denyRequest: denyRequest
                )
                .transition(.scale(scale: 0.96).combined(with: .opacity))
            } else {
                CompactSiriSurface(state: state, focused: $focused, expand: { expanded = true }, run: run)
                    .transition(.scale(scale: 1.03).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.35, dampingFraction: 0.86), value: expanded)
        .onAppear { focused = true }
        .onReceive(NotificationCenter.default.publisher(for: .focusPalette)) { _ in focused = true }
        .task { await pollApprovals() }
        .sheet(isPresented: $state.showHistory) { HistoryView(sessions: state.sessionSummaries) }
    }

    func run() {
        guard !state.isRunning, !state.task.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        if state.enableMemoryWrite { state.enableMemory = true }
        expanded = true
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
        if state.approvalRequest?.id != req.id { state.approvalRequest = req; expanded = true }
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

    func openAudit() {
        let url = state.auditURL
        if FileManager.default.fileExists(atPath: url.path) { NSWorkspace.shared.activateFileViewerSelecting([url]) }
        else { NSWorkspace.shared.activateFileViewerSelecting([url.deletingLastPathComponent()]) }
    }

    func openHistory() {
        state.loadSessionSummaries()
        state.showHistory = true
    }

    func clearConversation() {
        state.messages = [ChatMessage(role: .system, text: "New conversation. Ask for a Mac action, file comparison, reminder, or personal-context question.")]
        state.output = ""
        state.technicalLog = ""
    }
}

struct CompactSiriSurface: View {
    @ObservedObject var state: AppState
    var focused: FocusState<Bool>.Binding
    let expand: () -> Void
    let run: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 12) {
                Image(systemName: state.isRunning ? "sparkles" : "magnifyingglass")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(state.isRunning ? .orange : .secondary)
                TextField("Ask OpenSiri…", text: $state.task)
                    .font(.system(size: 22, weight: .medium, design: .rounded))
                    .textFieldStyle(.plain)
                    .focused(focused)
                    .onSubmit(run)
                Button(action: expand) { Image(systemName: "arrow.up.left.and.arrow.down.right") }
                    .buttonStyle(.plain)
                    .foregroundStyle(.secondary)
                Button(action: run) { Image(systemName: "return") }
                    .buttonStyle(.plain)
                    .disabled(state.task.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || state.isRunning)
            }
            if state.isRunning || !state.sourceChips.isEmpty {
                HStack(spacing: 7) {
                    StatusPill(status: state.status, running: state.isRunning)
                    ForEach(state.sourceChips.prefix(5), id: \.self) { SourceChip($0) }
                }
            }
        }
        .padding(22)
        .frame(width: 640)
        .glassPanel(cornerRadius: 30)
        .shadow(color: .black.opacity(0.20), radius: 38, x: 0, y: 24)
    }
}

struct ExpandedSiriSurface: View {
    @ObservedObject var state: AppState
    var focused: FocusState<Bool>.Binding
    let collapse: () -> Void
    let run: () -> Void
    let stop: () -> Void
    let openTranscript: () -> Void
    let openAudit: () -> Void
    let openHistory: () -> Void
    let clearConversation: () -> Void
    let approveRequest: () -> Void
    let denyRequest: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            ConversationSidebar(state: state, clearConversation: clearConversation, openHistory: openHistory)
            Divider().opacity(0.35)
            VStack(spacing: 0) {
                TopSearchBar(state: state, focused: focused, collapse: collapse, run: run, stop: stop)
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(alignment: .leading, spacing: 18) {
                            if state.isRunning { WorkingRow(status: state.status) }
                            if let request = state.approvalRequest { ApprovalCard(request: request, approve: approveRequest, deny: denyRequest) }
                            ForEach(state.messages) { msg in MessageBubble(message: msg).id(msg.id) }
                            SourceStrip(chips: state.sourceChips)
                        }
                        .padding(26)
                    }
                    .onChange(of: state.messages.count) { _, _ in if let last = state.messages.last { proxy.scrollTo(last.id, anchor: .bottom) } }
                }
                BottomComposer(state: state, focused: focused, run: run, openTranscript: openTranscript, openAudit: openAudit)
            }
        }
        .frame(minWidth: 860, idealWidth: 920, maxWidth: 1080, minHeight: 620, idealHeight: 690)
        .glassPanel(cornerRadius: 24)
        .shadow(color: .black.opacity(0.22), radius: 48, x: 0, y: 30)
    }
}

struct ConversationSidebar: View {
    @ObservedObject var state: AppState
    let clearConversation: () -> Void
    let openHistory: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(.red).frame(width: 12, height: 12)
                Circle().fill(.yellow).frame(width: 12, height: 12)
                Circle().fill(.green).frame(width: 12, height: 12)
                Spacer()
                Button(action: openHistory) { Image(systemName: "line.3.horizontal.decrease") }.buttonStyle(.plain)
                Button(action: clearConversation) { Image(systemName: "square.and.pencil") }.buttonStyle(.plain)
            }
            Text("Today").font(.caption.weight(.semibold)).foregroundStyle(.secondary)
            SidebarCard(title: "New Conversation", subtitle: state.task.isEmpty ? "Ready for a Mac action" : state.task)
            SidebarCard(title: "Mail & Messages", subtitle: "Backend search, citations, safe reads")
            SidebarCard(title: "Files & Finder", subtitle: "Receipts, PDFs, notes, spreadsheets")
            SidebarCard(title: "Actions", subtitle: "Notes, reminders, calendar, approvals")
            Spacer()
            VStack(alignment: .leading, spacing: 6) {
                StatusPill(status: state.status, running: state.isRunning)
                Text("Local index + Hypersave are used before screen reads.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(20)
        .frame(width: 278)
        .background(.ultraThinMaterial.opacity(0.75))
    }
}

struct SidebarCard: View {
    let title: String
    let subtitle: String
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title).font(.system(size: 14, weight: .semibold))
            Text(subtitle).font(.caption).foregroundStyle(.secondary).lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(.white.opacity(0.42))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct TopSearchBar: View {
    @ObservedObject var state: AppState
    var focused: FocusState<Bool>.Binding
    let collapse: () -> Void
    let run: () -> Void
    let stop: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button(action: collapse) { Image(systemName: "arrow.down.right.and.arrow.up.left") }.buttonStyle(.plain).foregroundStyle(.secondary)
            HStack(spacing: 9) {
                Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                TextField("Search or ask OpenSiri", text: $state.task)
                    .textFieldStyle(.plain)
                    .focused(focused)
                    .onSubmit(run)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(.white.opacity(0.62))
            .clipShape(Capsule())
            Picker("Approval", selection: $state.approvalMode) {
                Text("Deny").tag("deny")
                Text("Ask").tag("app")
                Text("Yes").tag("yes")
            }.frame(width: 110)
            Button("Stop", action: stop).disabled(!state.isRunning)
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 16)
    }
}

struct BottomComposer: View {
    @ObservedObject var state: AppState
    var focused: FocusState<Bool>.Binding
    let run: () -> Void
    let openTranscript: () -> Void
    let openAudit: () -> Void

    var body: some View {
        VStack(spacing: 10) {
            HStack(spacing: 8) {
                Button(action: {}) { Image(systemName: "plus") }.buttonStyle(.plain)
                TextField("Ask Siri-style…", text: $state.task)
                    .textFieldStyle(.plain)
                    .focused(focused)
                    .onSubmit(run)
                Button(action: run) { Image(systemName: "arrow.up.circle.fill").font(.title2) }.buttonStyle(.plain).disabled(state.task.isEmpty || state.isRunning)
                Button(action: {}) { Image(systemName: "mic.fill") }.buttonStyle(.plain)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 11)
            .background(.white.opacity(0.68))
            .clipShape(Capsule())
            HStack {
                Button("Transcript", action: openTranscript).disabled(state.lastTranscript.isEmpty)
                Button("Audit", action: openAudit)
                Toggle("AX", isOn: $state.liveAX).toggleStyle(.switch).scaleEffect(0.72)
                Spacer()
                if state.showTechnicalLog { Text(state.technicalLog.suffix(120)).font(.caption2.monospaced()).foregroundStyle(.secondary) }
                Button(state.showTechnicalLog ? "Hide Log" : "Log") { state.showTechnicalLog.toggle() }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(18)
    }
}

struct WorkingRow: View {
    let status: String
    var body: some View {
        HStack(spacing: 12) {
            ProgressView().controlSize(.small)
            Text(status == "Running" ? "Reviewing results" : status)
                .font(.system(size: 18, weight: .medium, design: .rounded))
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 18)
    }
}

struct ConversationView: View {
    let messages: [ChatMessage]
    var body: some View { VStack { ForEach(messages) { MessageBubble(message: $0) } } }
}

struct MessageBubble: View {
    let message: ChatMessage
    var body: some View {
        HStack(alignment: .top) {
            if message.role == .user { Spacer(minLength: 90) }
            VStack(alignment: .leading, spacing: 8) {
                Text(label).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                Text(message.text).font(.system(size: message.role == .assistant ? 16 : 14, weight: .regular)).textSelection(.enabled)
            }
            .padding(14)
            .background(background)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            if message.role != .user { Spacer(minLength: 90) }
        }
    }
    var label: String { switch message.role { case .user: "You"; case .assistant: "OpenSiri"; case .system: "Ready" } }
    var background: some ShapeStyle { switch message.role { case .user: return AnyShapeStyle(.white.opacity(0.72)); case .assistant: return AnyShapeStyle(.black.opacity(0.055)); case .system: return AnyShapeStyle(.green.opacity(0.10)) } }
}

struct ApprovalCard: View {
    let request: ApprovalRequest
    let approve: () -> Void
    let deny: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Approval Required", systemImage: "hand.raised.fill").font(.headline)
            Text(request.action.name).font(.system(.body, design: .monospaced))
            ForEach(request.action.args.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                Text("\(key): \(value)").font(.caption).foregroundStyle(.secondary).lineLimit(4)
            }
            HStack { Button("Deny", role: .cancel, action: deny); Button("Approve", action: approve).buttonStyle(.borderedProminent) }
        }
        .padding(16)
        .background(.orange.opacity(0.16))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct SourceStrip: View {
    let chips: [String]
    var body: some View { HStack(spacing: 7) { ForEach(chips, id: \.self) { SourceChip($0) } } }
}

struct SourceChip: View {
    let text: String
    init(_ text: String) { self.text = text }
    var body: some View { Text(text).font(.caption2.weight(.semibold)).padding(.horizontal, 9).padding(.vertical, 5).background(.white.opacity(0.58)).clipShape(Capsule()) }
}

struct StatusPill: View {
    let status: String
    let running: Bool
    var body: some View { Text(status).font(.caption2.weight(.bold)).padding(.horizontal, 9).padding(.vertical, 5).background((running ? Color.orange : Color.green).opacity(0.18)).clipShape(Capsule()) }
}

struct HistoryView: View {
    let sessions: [SessionSummary]
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Conversation History").font(.title2.weight(.semibold))
            if sessions.isEmpty { Text("No saved sessions yet.").foregroundStyle(.secondary) }
            else { ScrollView { VStack(alignment: .leading, spacing: 10) { ForEach(sessions) { session in HistoryRow(session: session) } } } }
        }
        .padding(24)
        .frame(width: 520, height: 460)
    }
}

struct HistoryRow: View {
    let session: SessionSummary
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(session.task.isEmpty ? "Untitled session" : session.task).font(.headline).lineLimit(2)
            Text(session.session_id).font(.caption.monospaced()).foregroundStyle(.secondary)
            Text(Date(timeIntervalSince1970: session.started_at).formatted()).font(.caption).foregroundStyle(.secondary)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.secondary.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

struct AuroraBackdrop: View {
    var body: some View {
        ZStack {
            LinearGradient(colors: [Color(nsColor: .windowBackgroundColor), .white.opacity(0.75)], startPoint: .topLeading, endPoint: .bottomTrailing)
            Circle().fill(.orange.opacity(0.14)).blur(radius: 42).offset(x: -250, y: -160)
            Circle().fill(.blue.opacity(0.12)).blur(radius: 55).offset(x: 280, y: 190)
        }
        .ignoresSafeArea()
    }
}

extension View {
    func glassPanel(cornerRadius: CGFloat) -> some View {
        self
            .background(.regularMaterial)
            .overlay(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous).stroke(.white.opacity(0.48), lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}
