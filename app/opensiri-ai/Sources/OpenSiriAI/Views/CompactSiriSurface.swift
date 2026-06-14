import SwiftUI

struct CompactSiriSurface: View {
    @Environment(AppState.self) private var state
    
    var focused: FocusState<Bool>.Binding
    let focusToken: Int
    let expand: () -> Void
    let run: () -> Void

    private var trimmedTask: String { state.task.trimmingCharacters(in: .whitespacesAndNewlines) }

    var body: some View {
        @Bindable var state = state
        
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                BrandMark(isRunning: state.isRunning)
                    .frame(width: 34, height: 34)

                NativeInput(text: $state.task, placeholder: "Ask OpenSiri", fontSize: 23, focusToken: focusToken, onSubmit: run)
                    .frame(height: 34)

                StatusDot(running: state.isRunning, status: state.status)

                IconSurfaceButton(systemName: "arrow.up.left.and.arrow.down.right", action: expand)
                    .help("Expand")

                IconSurfaceButton(systemName: "arrow.up.circle.fill", prominent: true, action: run)
                    .disabled(trimmedTask.isEmpty || state.isRunning)
                    .opacity(trimmedTask.isEmpty || state.isRunning ? 0.36 : 1)
                    .help("Run")
            }

            if state.isRunning {
                SiriWaveformView(isRunning: state.isRunning)
                    .transition(.opacity.combined(with: .scale(scale: 0.95)))
            } else if !state.sourceChips.isEmpty {
                HStack(spacing: 7) {
                    StatusPill(status: state.status, running: state.isRunning)
                    ForEach(state.sourceChips.prefix(6), id: \.self) { SourceChip($0) }
                    Spacer(minLength: 0)
                }
                .transition(.opacity)
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 15)
        .frame(width: 690)
        .macPanel(cornerRadius: 22, strokeOpacity: 0.36)
        .siriGlowBorder(isRunning: state.isRunning, status: state.status)
        .shadow(color: .black.opacity(0.22), radius: 34, x: 0, y: 22)
    }
}
