import SwiftUI

struct CommandToolbar: View {
    @Environment(AppState.self) private var state
    
    let collapse: () -> Void
    let stop: () -> Void
    let clearConversation: () -> Void
    let openHistory: () -> Void

    var body: some View {
        @Bindable var state = state
        
        HStack(spacing: 12) {
            // Left Side: Brand & Cohesive Navigation
            HStack(spacing: 8) {
                BrandMark(isRunning: state.isRunning)
                    .frame(width: 24, height: 24)
                
                Text("OpenSiri")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundStyle(.primary)
            }
            .padding(.trailing, 4)

            HStack(spacing: 6) {
                IconSurfaceButton(systemName: "square.and.pencil", action: clearConversation)
                    .help("New Conversation")
                
                IconSurfaceButton(systemName: "clock.arrow.circlepath", action: openHistory)
                    .help("History")
                
                IconSurfaceButton(systemName: "gearshape.fill", action: { state.showSettings = true })
                    .help("Settings")
            }

            Spacer(minLength: 12)

            // Center: Interactive Hypersave Connectivity Pill
            if !state.isHypersaveConnected {
                Button(action: { state.showSettings = true }) {
                    HStack(spacing: 5) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(Theme.amberWarning)
                            .font(.system(size: 10, weight: .bold))
                        Text("Hypersave Disconnected")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(.primary.opacity(0.85))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Theme.amberWarning.opacity(0.12))
                    .clipShape(Capsule())
                    .overlay(
                        Capsule()
                            .stroke(Theme.amberWarning.opacity(0.24), lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
                .help("Configure Hypersave memory in Settings")
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }

            Spacer(minLength: 12)

            // Right Side: Metrics & Panel Actions
            HStack(spacing: 12) {
                VStack(alignment: .trailing, spacing: 1) {
                    Text(state.isRunning ? "Working" : "Ready")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(state.isRunning ? Theme.electricCyan : .secondary)
                    Text(toolbarDetail)
                        .font(.system(size: 9))
                        .foregroundStyle(.tertiary)
                        .lineLimit(1)
                }
                .frame(width: 100, alignment: .trailing)

                Picker("Approval", selection: $state.approvalMode) {
                    Text("Deny").tag("deny")
                    Text("Ask").tag("app")
                    Text("Auto").tag("yes")
                }
                .pickerStyle(.segmented)
                .frame(width: 130)

                IconSurfaceButton(systemName: "stop.circle.fill", prominent: state.isRunning, action: stop)
                    .disabled(!state.isRunning)
                    .opacity(state.isRunning ? 1 : 0.38)
                    .help("Stop")

                IconSurfaceButton(systemName: "arrow.down.right.and.arrow.up.left", action: collapse)
                    .help("Collapse")
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 11)
        .background(.regularMaterial.opacity(0.62))
        .animation(.smooth(duration: 0.22), value: state.isHypersaveConnected)
    }

    private var toolbarDetail: String {
        if state.isRunning { return state.status }
        if state.messages.count <= 1 { return "New session" }
        return "\(max(state.messages.count - 1, 0)) messages"
    }
}
