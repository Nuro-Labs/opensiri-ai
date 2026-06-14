import SwiftUI

struct SiriWaveformView: View {
    let isRunning: Bool
    
    @State private var phase: CGFloat = 0.0
    @State private var waveAmplitude: CGFloat = 0.0

    var body: some View {
        TimelineView(.animation) { timeline in
            Canvas { context, size in
                let time = timeline.date.timeIntervalSinceReferenceDate
                let currentPhase = CGFloat(time * 6.0) // Animation speed
                
                // Draw multiple overlapping sine waves with taper envelopes
                drawWave(in: context, size: size, color: Theme.electricCyan.opacity(0.65), phase: currentPhase, frequency: 1.8, maxAmplitude: 24)
                drawWave(in: context, size: size, color: Theme.vibrantPurple.opacity(0.6), phase: currentPhase + 2.0, frequency: 2.5, maxAmplitude: 18)
                drawWave(in: context, size: size, color: Theme.neonPink.opacity(0.55), phase: currentPhase - 1.5, frequency: 1.2, maxAmplitude: 28)
                drawWave(in: context, size: size, color: Theme.electricBlue.opacity(0.5), phase: currentPhase + 3.5, frequency: 3.0, maxAmplitude: 14)
            }
        }
        .frame(height: 60)
        .onAppear {
            updateAmplitude()
        }
        .onChange(of: isRunning) { _, _ in
            updateAmplitude()
        }
    }
    
    private func updateAmplitude() {
        withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
            waveAmplitude = isRunning ? 1.0 : 0.08
        }
    }

    private func drawWave(in context: GraphicsContext, size: CGSize, color: Color, phase: CGFloat, frequency: CGFloat, maxAmplitude: CGFloat) {
        let midY = size.height / 2
        let width = size.width
        let activeAmplitude = maxAmplitude * waveAmplitude
        
        var path = Path()
        path.move(to: CGPoint(x: 0, y: midY))
        
        for x in stride(from: 0, to: width, by: 1) {
            let relativeX = x / width
            // Sine math
            let sine = sin(relativeX * frequency * 2 * .pi + phase)
            // Taper boundary envelope (fade at the edges)
            let envelope = sin(relativeX * .pi)
            let y = midY + sine * activeAmplitude * envelope
            path.addLine(to: CGPoint(x: x, y: y))
        }
        
        context.stroke(path, with: .color(color), lineWidth: isRunning ? 2.5 : 1.2)
    }
}
