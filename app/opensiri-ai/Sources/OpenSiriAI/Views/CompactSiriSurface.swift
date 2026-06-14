import SwiftUI

struct CompactSiriSurface: View {
    @Environment(AppState.self) private var state
    
    var focused: FocusState<Bool>.Binding
    let focusToken: Int
    let expand: () -> Void
    let run: () -> Void

    @State private var hoveringExpand = false
    @State private var hoveringSend = false

    private var trimmedTask: String { state.task.trimmingCharacters(in: .whitespacesAndNewlines) }

    var body: some View {
        @Bindable var state = state
        
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                BrandMark(isRunning: state.isRunning, showFullLogo: false)
                    .frame(width: 34, height: 34)

                NativeInput(text: $state.task, placeholder: "Ask OpenSiri", fontSize: 23, focusToken: focusToken, onSubmit: run)
                    .frame(height: 34)

                StatusDot(running: state.isRunning, status: state.status)

                Button(action: expand) {
                    Image(systemName: "arrow.up.left.and.arrow.down.right")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(Color.primary.opacity(hoveringExpand ? 0.95 : 0.62))
                        .scaleEffect(hoveringExpand ? 1.08 : 1.0)
                        .frame(width: 32, height: 32)
                }
                .buttonStyle(.plain)
                .onHover { hoveringExpand = $0 }
                .animation(.smooth(duration: 0.16), value: hoveringExpand)
                .help("Expand")

                Button(action: run) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 26, weight: .semibold))
                        .foregroundStyle(trimmedTask.isEmpty || state.isRunning ? Color.primary.opacity(0.36) : Color.accentColor)
                        .scaleEffect(hoveringSend ? 1.08 : 1.0)
                        .frame(width: 32, height: 32)
                }
                .buttonStyle(.plain)
                .disabled(trimmedTask.isEmpty || state.isRunning)
                .onHover { hoveringSend = $0 }
                .animation(.smooth(duration: 0.16), value: hoveringSend)
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
