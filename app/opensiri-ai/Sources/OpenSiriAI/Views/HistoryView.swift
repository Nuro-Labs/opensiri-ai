import SwiftUI

struct HistoryView: View {
    let sessions: [SessionSummary]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("History")
                    .font(.title3.weight(.semibold))
                Spacer()
                Text("\(sessions.count)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(nsColor: .controlBackgroundColor))
                    .clipShape(Capsule())
            }

            if sessions.isEmpty {
                ContentUnavailableView("No sessions", systemImage: "clock")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 9) {
                        ForEach(sessions) { session in
                            HistoryRow(session: session)
                        }
                    }
                }
            }
        }
        .padding(22)
        .frame(width: 540, height: 460)
        .background(.regularMaterial)
    }
}

struct HistoryRow: View {
    let session: SessionSummary

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(session.task.isEmpty ? "Untitled session" : session.task)
                .font(.system(size: 14, weight: .semibold))
                .lineLimit(2)
            Text(Date(timeIntervalSince1970: session.started_at).formatted())
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(session.session_id)
                .font(.caption2.monospaced())
                .foregroundStyle(.tertiary)
                .lineLimit(1)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.72))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}
