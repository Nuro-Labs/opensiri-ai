import SwiftUI
import AppKit

enum Theme {
    // Premium color palette
    static let electricBlue = Color(red: 0.12, green: 0.44, blue: 1.0)
    static let vibrantPurple = Color(red: 0.58, green: 0.22, blue: 1.0)
    static let electricCyan = Color(red: 0.0, green: 0.85, blue: 1.0)
    static let neonPink = Color(red: 1.0, green: 0.17, blue: 0.48)
    static let brightEmerald = Color(red: 0.0, green: 0.88, blue: 0.42)
    static let amberWarning = Color(red: 1.0, green: 0.55, blue: 0.0)
    
    // Core neutral colors
    static let glassBackground = Color.black.opacity(0.4)
    static let sidebarBackground = Color.black.opacity(0.18)
    static let surfaceBackground = Color(white: 0.15, opacity: 0.4)
    static let bubbleUser = Color(red: 0.12, green: 0.35, blue: 0.85).opacity(0.7)
    static let bubbleAssistant = Color(white: 0.18, opacity: 0.6)
    
    // Spring dynamics
    static let siriSpring = Animation.spring(response: 0.38, dampingFraction: 0.72)
    static let fastSpring = Animation.spring(response: 0.24, dampingFraction: 0.78)
    static let fluidSpring = Animation.spring(response: 0.45, dampingFraction: 0.68)
    
    // Design constants
    static let cardCornerRadius: CGFloat = 20
    static let bubbleCornerRadius: CGFloat = 14
    static let standardSpacing: CGFloat = 16
    static let standardPadding: CGFloat = 18
}

func sourceIcon(_ source: String) -> String {
    let value = source.lowercased()
    if value.contains("screen") { return "display" }
    if value.contains("memory") { return "brain.head.profile" }
    if value.contains("index") { return "magnifyingglass.circle" }
    if value.contains("finder") { return "folder" }
    if value.contains("file") { return "doc.text" }
    if value.contains("web") { return "globe" }
    if value.contains("visual") { return "viewfinder" }
    if value.contains("mail") { return "envelope" }
    if value.contains("message") { return "message" }
    if value.contains("notes") || value.contains("note") { return "note.text" }
    if value.contains("photo") { return "photo" }
    if value.contains("calendar") { return "calendar" }
    if value.contains("contact") { return "person.crop.circle" }
    if value.contains("browser") { return "safari" }
    if value.contains("system") { return "gearshape" }
    if value.contains("map") { return "map" }
    if value.contains("music") { return "music.note" }
    if value.contains("podcast") { return "waveform" }
    return "circle.grid.2x2"
}

extension View {
    func macPanel(cornerRadius: CGFloat, strokeOpacity: Double = 0.28) -> some View {
        self
            .background(Color(white: 0.11).opacity(0.96))
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}
