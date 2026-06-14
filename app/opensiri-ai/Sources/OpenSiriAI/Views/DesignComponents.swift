import SwiftUI

struct BrandMark: View {
    let isRunning: Bool

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(Color.primary.opacity(0.88))
            Image(systemName: isRunning ? "wand.and.stars" : "sparkles")
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(.white)
                .symbolEffect(.pulse, options: .repeating, value: isRunning)
        }
        .scaleEffect(isRunning ? 1.03 : 1)
        .animation(.smooth(duration: 0.22, extraBounce: 0.08), value: isRunning)
    }
}

struct StatusDot: View {
    let running: Bool
    let status: String
    @State private var pulse = false

    var body: some View {
        Circle()
            .fill(running ? Theme.electricCyan : Theme.brightEmerald)
            .frame(width: 9, height: 9)
            .overlay {
                Circle()
                    .stroke((running ? Theme.electricCyan : Theme.brightEmerald).opacity(0.32), lineWidth: 1)
                    .scaleEffect(running && pulse ? 2.4 : 1)
                    .opacity(running && pulse ? 0 : 1)
            }
            .shadow(color: (running ? Theme.electricCyan : Theme.brightEmerald).opacity(0.42), radius: 5)
            .animation(running ? .easeOut(duration: 1.15).repeatForever(autoreverses: false) : .smooth(duration: 0.16), value: pulse)
            .onAppear { pulse = running }
            .onChange(of: running) { _, value in
                pulse = false
                if value {
                    DispatchQueue.main.async { pulse = true }
                }
            }
            .help(status)
    }
}

struct IconSurfaceButton: View {
    let systemName: String
    var prominent = false
    var small = false
    let action: () -> Void
    @State private var hovering = false

    init(systemName: String, prominent: Bool = false, small: Bool = false, action: @escaping () -> Void) {
        self.systemName = systemName
        self.prominent = prominent
        self.small = small
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: small ? 12 : 15, weight: .semibold))
                .foregroundStyle(prominent ? Color.white : Color.primary.opacity(0.78))
                .frame(width: small ? 26 : 32, height: small ? 24 : 32)
                .background(prominent ? Color.accentColor : Color(nsColor: .controlBackgroundColor).opacity(0.72))
                .clipShape(RoundedRectangle(cornerRadius: small ? 7 : 9, style: .continuous))
                .scaleEffect(hovering ? 1.055 : 1)
                .brightness(hovering ? 0.035 : 0)
                .contentShape(RoundedRectangle(cornerRadius: small ? 7 : 9, style: .continuous))
        }
        .buttonStyle(.plain)
        .onHover { hovering = $0 }
        .animation(.smooth(duration: 0.14, extraBounce: 0.04), value: hovering)
    }
}
