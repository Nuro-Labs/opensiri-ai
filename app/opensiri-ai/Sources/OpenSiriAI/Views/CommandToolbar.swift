import SwiftUI

struct CommandToolbar: View {
    @Environment(AppState.self) private var state
    
    let collapse: () -> Void
    let stop: () -> Void

    var body: some View {
        @Bindable var state = state
        
        HStack(spacing: 12) {
            IconSurfaceButton(systemName: "arrow.down.right.and.arrow.up.left", action: collapse)
                .help("Collapse")

            VStack(alignment: .leading, spacing: 2) {
                Text(state.isRunning ? "Working" : "Ready")
                    .font(.system(size: 15, weight: .semibold))
                Text(toolbarDetail)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Spacer(minLength: 16)

            Picker("Approval", selection: $state.approvalMode) {
                Text("Deny").tag("deny")
                Text("Ask").tag("app")
                Text("Yes").tag("yes")
            }
            .pickerStyle(.segmented)
            .frame(width: 146)

            IconSurfaceButton(systemName: "stop.circle", action: stop)
                .disabled(!state.isRunning)
                .opacity(state.isRunning ? 1 : 0.38)
                .help("Stop")
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
        .background(.regularMaterial.opacity(0.62))
    }

    private var toolbarDetail: String {
        if state.isRunning { return state.status }
        if state.messages.count <= 1 { return "New session" }
        return "\(max(state.messages.count - 1, 0)) messages"
    }
}
