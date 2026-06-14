import SwiftUI

struct PaletteView: View {
    @Environment(AppState.self) private var state
    @FocusState private var focused: Bool
    @State private var expanded = false
    @State private var focusToken = 0

    var body: some View {
        @Bindable var state = state
        Group {
            if expanded {
                ZStack {
                    DesktopBackdrop()
                    ExpandedSiriSurface(
                        focused: $focused,
                        focusToken: focusToken,
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
                    .transition(.scale(scale: 0.97).combined(with: .opacity))
                }
            } else {
                CompactSiriSurface(
                    focused: $focused,
                    focusToken: focusToken,
                    expand: { expanded = true },
                    run: run
                )
                .transition(.scale(scale: 1.02).combined(with: .opacity))
            }
        }
        .background(FloatingWindowConfigurator(expanded: expanded))
        .animation(.smooth(duration: 0.28, extraBounce: 0.08), value: expanded)
        .onAppear { focusSoon() }
        .onReceive(NotificationCenter.default.publisher(for: .focusPalette)) { _ in focusSoon() }
        .onReceive(NotificationCenter.default.publisher(for: .centerOpenSiriWindow)) { _ in recenterWindow(); focusSoon() }
        .task { await pollApprovals() }
        .sheet(isPresented: $state.showHistory) { HistoryView(sessions: state.sessionSummaries) }
    }

    func run() {
        let submitted = state.task.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !state.isRunning, !submitted.isEmpty else { return }
        if state.enableMemoryWrite { state.enableMemory = true }
        expanded = true
        do {
            try HarnessBridge.run(task: submitted, state: state)
            state.task = ""
        } catch {
            let message = "Failed to start OpenSiri: \(error.localizedDescription)"
            state.output = message
            if state.messages.last?.text != submitted {
                state.messages.append(ChatMessage(role: .user, text: submitted))
            }
            state.messages.append(ChatMessage(role: .assistant, text: message))
            state.status = "Error"
            state.isRunning = false
        }
    }

    func stop() {
        state.process?.terminate()
        state.process = nil
        state.isRunning = false
        state.status = "Stopped"
    }

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
        if state.approvalRequest?.id != req.id {
            state.approvalRequest = req
            expanded = true
        }
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
        if FileManager.default.fileExists(atPath: url.path) {
            NSWorkspace.shared.activateFileViewerSelecting([url])
        } else {
            NSWorkspace.shared.activateFileViewerSelecting([url.deletingLastPathComponent()])
        }
    }

    func openHistory() {
        state.loadSessionSummaries()
        state.showHistory = true
    }

    func clearConversation() {
        state.messages = [ChatMessage(role: .system, text: "Ready for a Mac action, file comparison, reminder, or personal-context question.")]
        state.output = ""
        state.technicalLog = ""
    }

    func recenterWindow() {
        guard let window = NSApp.keyWindow ?? NSApp.windows.first else { return }
        NSApp.activate(ignoringOtherApps: true)
        window.makeKeyAndOrderFront(nil)
        window.orderFrontRegardless()
        let target = expanded ? NSSize(width: 980, height: 720) : NSSize(width: 720, height: 128)
        if let screen = window.screen ?? NSScreen.main {
            let visible = screen.visibleFrame
            var frame = window.frame
            frame.size = target
            frame.origin.x = visible.midX - target.width / 2
            frame.origin.y = visible.maxY - target.height - 64
            window.setFrame(frame, display: true, animate: true)
        }
    }

    func focusSoon() {
        DispatchQueue.main.async { focused = true; focusToken += 1 }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.08) { focused = true; focusToken += 1 }
    }
}
