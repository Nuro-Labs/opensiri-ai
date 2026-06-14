import SwiftUI

struct CommandComposer: View {
    @Environment(AppState.self) private var state
    
    var focused: FocusState<Bool>.Binding
    let focusToken: Int
    let run: () -> Void
    let openTranscript: () -> Void
    let openAudit: () -> Void

    private var trimmedTask: String { state.task.trimmingCharacters(in: .whitespacesAndNewlines) }

    var body: some View {
        @Bindable var state = state
        
        VStack(spacing: 10) {
            HStack(spacing: 10) {
                IconSurfaceButton(systemName: state.liveAX ? "display" : "display.slash") {
                    state.liveAX.toggle()
                }
                .help(state.liveAX ? "Disable screen context" : "Enable screen context")

                HStack(spacing: 10) {
                    Image(systemName: "text.cursor")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.secondary)
                    NativeInput(text: $state.task, placeholder: "Ask for a task", fontSize: 15, focusToken: focusToken, onSubmit: run)
                        .frame(height: 24)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 9)
                .background(Color(nsColor: .textBackgroundColor).opacity(0.74))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                IconSurfaceButton(systemName: "arrow.up.circle.fill", prominent: true, action: run)
                    .disabled(trimmedTask.isEmpty || state.isRunning)
                    .opacity(trimmedTask.isEmpty || state.isRunning ? 0.36 : 1)
                    .help("Run")
            }

            HStack(spacing: 8) {
                Button(action: openTranscript) {
                    Label("Transcript", systemImage: "doc.text.magnifyingglass")
                }
                .disabled(state.lastTranscript.isEmpty)

                Button(action: openAudit) {
                    Label("Audit", systemImage: "list.bullet.clipboard")
                }

                Toggle(isOn: $state.showTechnicalLog) {
                    Label("Tool output", systemImage: "terminal")
                }
                .toggleStyle(.button)

                Spacer(minLength: 0)

                ForEach(state.sourceChips.prefix(4), id: \.self) { SourceChip($0) }
            }
            .font(.caption)
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 18)
        .padding(.top, 14)
        .padding(.bottom, 22)
        .background(.regularMaterial.opacity(0.72))
    }
}
