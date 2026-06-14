import SwiftUI

struct ExpandedSiriSurface: View {
    @Environment(AppState.self) private var state
    
    var focused: FocusState<Bool>.Binding
    let focusToken: Int
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
            SourceSidebar(
                clearConversation: clearConversation,
                openHistory: openHistory
            )

            Divider().opacity(0.42)

            VStack(spacing: 0) {
                CommandToolbar(
                    collapse: collapse,
                    stop: stop
                )
                ConversationTimeline(
                    approveRequest: approveRequest,
                    denyRequest: denyRequest
                )
                CommandComposer(
                    focused: focused,
                    focusToken: focusToken,
                    run: run,
                    openTranscript: openTranscript,
                    openAudit: openAudit
                )
            }
        }
        .frame(width: 980, height: 720)
        .macPanel(cornerRadius: 18, strokeOpacity: 0.32)
        .siriGlowBorder(isRunning: state.isRunning, status: state.status)
        .shadow(color: .black.opacity(0.24), radius: 52, x: 0, y: 28)
    }
}
