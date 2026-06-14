import SwiftUI

struct SourceSidebar: View {
    @Environment(AppState.self) private var state
    
    let clearConversation: () -> Void
    let openHistory: () -> Void

    private var activeSources: [String] {
        state.sourceChips.filter { $0 != "Screen" }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(spacing: 10) {
                BrandMark(isRunning: state.isRunning)
                    .frame(width: 32, height: 32)
                VStack(alignment: .leading, spacing: 1) {
                    Text("OpenSiri")
                        .font(.system(size: 15, weight: .semibold))
                    Text(state.status)
                        .font(.caption2.weight(.medium))
                        .foregroundStyle(state.isRunning ? Theme.electricCyan : .secondary)
                }
                Spacer()
            }

            HStack(spacing: 8) {
                IconSurfaceButton(systemName: "clock.arrow.circlepath", action: openHistory)
                    .help("History")
                IconSurfaceButton(systemName: "square.and.pencil", action: clearConversation)
                    .help("New conversation")
            }

            SidebarSection(title: "Session") {
                SidebarMetric(icon: "display", title: "Screen", value: state.liveAX ? "Live" : "Off", accent: state.liveAX ? Theme.brightEmerald : .secondary)
                SidebarMetric(icon: "shield.lefthalf.filled", title: "Approval", value: approvalLabel(state.approvalMode), accent: state.approvalMode == "yes" ? Theme.amberWarning : Theme.electricBlue)
                SidebarMetric(icon: "cpu", title: "Model", value: state.modelName.isEmpty ? "default" : state.modelName, accent: .secondary)
            }

            SidebarSection(title: "Sources") {
                if activeSources.isEmpty {
                    EmptySidebarRow()
                } else {
                    ForEach(activeSources.prefix(10), id: \.self) { source in
                        SidebarSourceRow(source: source)
                    }
                }
            }

            Spacer(minLength: 0)

            VStack(alignment: .leading, spacing: 8) {
                Text("Last transcript")
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
                Text(state.lastTranscript.isEmpty ? "No run yet" : URL(fileURLWithPath: state.lastTranscript).lastPathComponent)
                    .font(.caption2.monospaced())
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(.horizontal, 18)
        .padding(.top, 18)
        .padding(.bottom, 26)
        .frame(width: 248)
        .background(.bar.opacity(0.72))
    }

    private func approvalLabel(_ mode: String) -> String {
        switch mode {
        case "app": return "Ask"
        case "console": return "Console"
        case "yes": return "Auto"
        default: return "Deny"
        }
    }
}

struct SidebarSection<Content: View>: View {
    let title: String
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title.uppercased())
                .font(.caption2.weight(.bold))
                .foregroundStyle(.secondary)
            VStack(spacing: 6) {
                content
            }
        }
    }
}

struct SidebarMetric: View {
    let icon: String
    let title: String
    let value: String
    let accent: Color

    var body: some View {
        HStack(spacing: 9) {
            Image(systemName: icon)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(accent)
                .frame(width: 18)
            Text(title)
                .font(.caption.weight(.medium))
            Spacer(minLength: 6)
            Text(value)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 8)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.58))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

struct SidebarSourceRow: View {
    let source: String

    var body: some View {
        HStack(spacing: 9) {
            Image(systemName: sourceIcon(source))
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
                .frame(width: 18)
            Text(source)
                .font(.caption.weight(.medium))
                .lineLimit(1)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 7)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.44))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

struct EmptySidebarRow: View {
    var body: some View {
        HStack(spacing: 9) {
            Image(systemName: "minus.circle")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
                .frame(width: 18)
            Text("Screen only")
                .font(.caption.weight(.medium))
                .foregroundStyle(.secondary)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 7)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.34))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}
