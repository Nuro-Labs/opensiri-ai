import SwiftUI

struct SiriGlowBorder: ViewModifier {
    let isRunning: Bool
    let status: String
    
    @State private var rotationAngle: Double = 0
    @State private var pulseScale: CGFloat = 1.0

    func body(content: Content) -> some View {
        content
            .overlay(
                Group {
                    if isRunning {
                        RoundedRectangle(cornerRadius: Theme.cardCornerRadius, style: .continuous)
                            .strokeBorder(strokeGradient, lineWidth: 2.0)
                            .blur(radius: 0.5)
                            .shadow(color: glowColor.opacity(0.65), radius: 14)
                    }
                }
                .animation(Theme.siriSpring, value: isRunning)
            )
            .scaleEffect(pulseScale)
            .onChange(of: isRunning) { _, active in
                if active {
                    withAnimation(.linear(duration: 4.5).repeatForever(autoreverses: false)) {
                        rotationAngle = 360
                    }
                } else {
                    withAnimation(.easeInOut(duration: 0.8)) {
                        rotationAngle = 0
                    }
                }
            }
            .onChange(of: status) { _, newStatus in
                if newStatus == "Approval" {
                    withAnimation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true)) {
                        pulseScale = 1.015
                    }
                } else {
                    withAnimation(.spring) {
                        pulseScale = 1.0
                    }
                }
            }
    }

    private var strokeGradient: some ShapeStyle {
        if status == "Done" {
            return AnyShapeStyle(
                LinearGradient(
                    colors: [Theme.electricCyan, Theme.electricBlue, Theme.vibrantPurple],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
        } else if status == "Error" {
            return AnyShapeStyle(Color.red)
        } else if status == "Approval" || status.contains("Requested") {
            return AnyShapeStyle(Theme.amberWarning)
        } else if isRunning {
            return AnyShapeStyle(
                AngularGradient(
                    colors: [Theme.electricCyan, Theme.vibrantPurple, Theme.neonPink, Theme.electricBlue, Theme.electricCyan],
                    center: .center,
                    angle: .degrees(rotationAngle)
                )
            )
        } else {
            return AnyShapeStyle(Color.white.opacity(0.18))
        }
    }

    private var glowColor: Color {
        if status == "Done" {
            return Theme.electricBlue
        } else if status == "Error" {
            return Color.red
        } else if status == "Approval" || status.contains("Requested") {
            return Theme.amberWarning
        } else if isRunning {
            return Theme.vibrantPurple
        } else {
            return Color.white
        }
    }
}

extension View {
    func siriGlowBorder(isRunning: Bool, status: String) -> some View {
        modifier(SiriGlowBorder(isRunning: isRunning, status: status))
    }
}
