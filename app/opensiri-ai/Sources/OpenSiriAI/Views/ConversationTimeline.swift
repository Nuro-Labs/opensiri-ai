import SwiftUI

struct ConversationTimeline: View {
    @Environment(AppState.self) private var state
    
    let approveRequest: () -> Void
    let denyRequest: () -> Void

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    ForEach(state.messages) { msg in
                        MessageBubble(message: msg)
                            .id(msg.id)
                            .transition(.asymmetric(insertion: .move(edge: msg.role == .user ? .trailing : .leading).combined(with: .opacity), removal: .opacity))
                    }
                    
                    if let request = state.approvalRequest {
                        ContentMessageBubble(message: ChatMessage(role: .assistant, text: "Approval Required")) {
                            ApprovalCard(request: request, approve: approveRequest, deny: denyRequest)
                        }
                        .id("approval_request")
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    } else if state.isRunning {
                        WorkingRow(status: state.status)
                            .id("working_row")
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    if state.showTechnicalLog && !state.technicalLog.isEmpty {
                        LatestResultCard(text: state.technicalLog)
                            .id("technical_log")
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    Spacer(minLength: 0)
                        .id("bottom_anchor")
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 20)
            }
            .background(Color(nsColor: .windowBackgroundColor).opacity(0.38))
            .animation(Theme.fluidSpring, value: state.messages.count)
            .animation(Theme.fastSpring, value: state.isRunning)
            .animation(Theme.siriSpring, value: state.approvalRequest?.id)
            .onChange(of: state.messages.count) { _, _ in
                withAnimation(Theme.fluidSpring) {
                    proxy.scrollTo("bottom_anchor", anchor: .bottom)
                }
            }
            .onChange(of: state.approvalRequest?.id) { _, id in
                if id != nil {
                    withAnimation(Theme.fluidSpring) {
                        proxy.scrollTo("bottom_anchor", anchor: .bottom)
                    }
                }
            }
            .onChange(of: state.isRunning) { _, running in
                if running {
                    withAnimation(Theme.fluidSpring) {
                        proxy.scrollTo("bottom_anchor", anchor: .bottom)
                    }
                }
            }
            .onAppear {
                withAnimation(Theme.fluidSpring) {
                    proxy.scrollTo("bottom_anchor", anchor: .bottom)
                }
            }
        }
    }
}

struct ContentMessageBubble<Content: View>: View {
    let message: ChatMessage
    let content: Content

    init(message: ChatMessage, @ViewBuilder content: () -> Content) {
        self.message = message
        self.content = content()
    }

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            if message.role == .user { Spacer(minLength: 92) }

            if message.role != .user {
                RoleBadge(role: message.role)
            }

            VStack(alignment: .leading, spacing: 9) {
                HStack(spacing: 8) {
                    Text(label)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(message.date.formatted(date: .omitted, time: .shortened))
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }

                content
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(bubbleBackground)
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(borderColor, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

            if message.role == .user {
                RoleBadge(role: message.role)
            } else {
                Spacer(minLength: 92)
            }
        }
    }

    private var label: String {
        switch message.role {
        case .user: return "You"
        case .assistant: return "OpenSiri"
        case .system: return "Status"
        }
    }

    private var bubbleBackground: Color {
        switch message.role {
        case .user: return Color.accentColor.opacity(0.13)
        case .assistant: return Color(nsColor: .controlBackgroundColor).opacity(0.74)
        case .system: return Color.blue.opacity(0.06)
        }
    }

    private var borderColor: Color {
        switch message.role {
        case .user: return Color.accentColor.opacity(0.18)
        case .assistant: return Color.white.opacity(0.22)
        case .system: return Color.blue.opacity(0.12)
        }
    }
}


struct WorkingRow: View {
    let status: String

    var body: some View {
        HStack(spacing: 12) {
            ProgressView()
                .controlSize(.small)
            VStack(alignment: .leading, spacing: 2) {
                Text(status == "Running" ? "Reviewing context" : status)
                    .font(.system(size: 15, weight: .semibold))
                Text(Date().formatted(date: .omitted, time: .shortened))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
        }
        .padding(14)
        .background(Color.orange.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            if message.role == .user { Spacer(minLength: 92) }

            if message.role != .user {
                RoleBadge(role: message.role)
            }

            VStack(alignment: .leading, spacing: 9) {
                HStack(spacing: 8) {
                    Text(label)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(message.date.formatted(date: .omitted, time: .shortened))
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }

                if message.role == .assistant && looksStructured(message.text) {
                    StructuredResultText(text: message.text)
                } else {
                    Text(message.text)
                        .font(.system(size: message.role == .assistant ? 15 : 14))
                        .foregroundStyle(.primary)
                        .textSelection(.enabled)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(bubbleBackground)
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(borderColor, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

            if message.role == .user {
                RoleBadge(role: message.role)
            } else {
                Spacer(minLength: 92)
            }
        }
    }

    private var label: String {
        switch message.role {
        case .user: return "You"
        case .assistant: return "OpenSiri"
        case .system: return "Status"
        }
    }

    private var bubbleBackground: Color {
        switch message.role {
        case .user: return Color.accentColor.opacity(0.13)
        case .assistant: return Color(nsColor: .controlBackgroundColor).opacity(0.74)
        case .system: return Color.blue.opacity(0.06)
        }
    }

    private var borderColor: Color {
        switch message.role {
        case .user: return Color.accentColor.opacity(0.18)
        case .assistant: return Color.white.opacity(0.22)
        case .system: return Color.blue.opacity(0.12)
        }
    }

    private func looksStructured(_ text: String) -> Bool {
        text.contains(" | ") ||
        text.contains("Subject:") ||
        text.contains("DRY RUN") ||
        text.contains("Created") ||
        text.contains("created") ||
        text.contains("Path: ") ||
        text.contains("Event: ") ||
        text.contains("Reminder: ") ||
        text.contains("Task: ") ||
        text.contains("Calendar: ")
    }
}

struct RoleBadge: View {
    let role: ChatMessage.Role

    var body: some View {
        ZStack {
            Circle().fill(background)
            Image(systemName: icon)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(foreground)
        }
        .frame(width: 28, height: 28)
    }

    private var icon: String {
        switch role {
        case .user: return "person.fill"
        case .assistant: return "sparkles"
        case .system: return "checkmark.seal.fill"
        }
    }

    private var background: Color {
        switch role {
        case .user: return Color.accentColor.opacity(0.16)
        case .assistant: return Color.primary.opacity(0.10)
        case .system: return Color.blue.opacity(0.12)
        }
    }

    private var foreground: Color {
        switch role {
        case .user: return .accentColor
        case .assistant: return .primary
        case .system: return .blue
        }
    }
}

struct StructuredResultText: View {
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            let lines = Array(text.split(separator: "\n", omittingEmptySubsequences: false).map(String.init).prefix(10).enumerated())
            ForEach(lines, id: \.offset) { _, line in
                ResultLine(line: line)
                    .transition(.opacity.combined(with: .offset(y: 8)))
            }
        }
    }
}

struct ResultLine: View {
    let line: String

    var body: some View {
        if isMailLine {
            let parsed = parseMailLine(line)
            MailCard(subject: parsed.subject, from: parsed.from, date: parsed.date, mailBody: parsed.body)
        } else if isCalendarLine {
            let parsed = parseCalendarLine(line)
            CalendarCard(day: parsed.day, title: parsed.title, location: parsed.location, time: parsed.time)
        } else if isReminderLine {
            let parsed = parseReminderLine(line)
            ReminderCard(title: parsed.title, listName: parsed.list, location: parsed.location, isCompleted: parsed.isCompleted)
        } else if isFileLine {
            let parsed = parseFileLine(line)
            FileCard(filename: parsed.filename, path: parsed.path, url: parsed.url, details: parsed.details, workPerformed: parsed.workPerformed)
        } else {
            HStack(alignment: .top, spacing: 9) {
                Image(systemName: icon)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(iconColor)
                    .frame(width: 18)
                    .padding(.top, 2)

                VStack(alignment: .leading, spacing: 7) {
                    Text(line.isEmpty ? " " : line)
                        .font(.system(size: 14))
                        .textSelection(.enabled)
                }
            }
        }
    }

    private func parseMailLine(_ line: String) -> (subject: String, from: String, date: String, body: String?) {
        var subject = ""
        var from = ""
        var date = ""
        var body: String? = nil
        
        let parts = line.components(separatedBy: " | ")
        for part in parts {
            let trimmed = part.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("Subject: ") {
                subject = String(trimmed.dropFirst("Subject: ".count))
            } else if trimmed.hasPrefix("From: ") {
                from = String(trimmed.dropFirst("From: ".count))
            } else if trimmed.hasPrefix("Date: ") {
                date = String(trimmed.dropFirst("Date: ".count))
            } else if trimmed.hasPrefix("Body: ") {
                body = String(trimmed.dropFirst("Body: ".count))
            } else if trimmed.hasPrefix("Mailbox: ") {
                let mailbox = String(trimmed.dropFirst("Mailbox: ".count))
                if body == nil {
                    body = "Mailbox: \(mailbox)"
                }
            }
        }
        return (subject, from, date, body)
    }

    private func parseCalendarLine(_ line: String) -> (day: String, title: String, location: String?, time: String?) {
        var day = "Upcoming Event"
        var title = "Calendar Event"
        var location: String? = nil
        var time: String? = nil
        
        let parts = line.components(separatedBy: " | ")
        for part in parts {
            let trimmed = part.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("Event: ") {
                let val = String(trimmed.dropFirst("Event: ".count))
                if !val.isEmpty { day = val }
            } else if trimmed.hasPrefix("Calendar: ") {
                let val = String(trimmed.dropFirst("Calendar: ".count))
                if !val.isEmpty { day = val }
            } else if trimmed.hasPrefix("Title: ") {
                title = String(trimmed.dropFirst("Title: ".count))
            } else if trimmed.hasPrefix("Summary: ") {
                title = String(trimmed.dropFirst("Summary: ".count))
            } else if trimmed.hasPrefix("Location: ") {
                location = String(trimmed.dropFirst("Location: ".count))
            } else if trimmed.hasPrefix("Time: ") {
                time = String(trimmed.dropFirst("Time: ".count))
            }
        }
        if parts.count == 1 {
            if line.contains(": ") {
                let leftRight = line.components(separatedBy: ": ")
                if leftRight.count >= 2 {
                    title = leftRight[1...].joined(separator: ": ")
                    let left = leftRight[0]
                    if left.contains(" - ") {
                        let timesAndDays = left.components(separatedBy: " - ")
                        if timesAndDays.count >= 2 {
                            day = timesAndDays[0]
                            time = timesAndDays[1]
                        } else {
                            day = left
                        }
                    } else {
                        day = left
                    }
                }
            }
        }
        return (day, title, location, time)
    }

    private func parseReminderLine(_ line: String) -> (title: String, list: String, location: String?, isCompleted: Bool) {
        var title = "Reminder"
        var list = "Inbox"
        var location: String? = nil
        var isCompleted = false
        
        let parts = line.components(separatedBy: " | ")
        for part in parts {
            let trimmed = part.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("Reminder: ") {
                title = String(trimmed.dropFirst("Reminder: ".count))
            } else if trimmed.hasPrefix("Task: ") {
                title = String(trimmed.dropFirst("Task: ".count))
            } else if trimmed.hasPrefix("List: ") {
                list = String(trimmed.dropFirst("List: ".count))
            } else if trimmed.hasPrefix("Location: ") {
                location = String(trimmed.dropFirst("Location: ".count))
            } else if trimmed.hasPrefix("Status: ") {
                let statusVal = String(trimmed.dropFirst("Status: ".count)).lowercased()
                isCompleted = (statusVal == "done" || statusVal == "completed" || statusVal == "true")
            }
        }
        if parts.count == 1 {
            var cleanLine = line
            if cleanLine.hasPrefix("- [x]") {
                isCompleted = true
                cleanLine = String(cleanLine.dropFirst(5)).trimmingCharacters(in: .whitespacesAndNewlines)
            } else if cleanLine.hasPrefix("- [ ]") {
                isCompleted = false
                cleanLine = String(cleanLine.dropFirst(5)).trimmingCharacters(in: .whitespacesAndNewlines)
            }
            if cleanLine.contains("(") && cleanLine.hasSuffix(")") {
                if let openParen = cleanLine.firstIndex(of: "(") {
                    let loc = String(cleanLine[openParen...]).trimmingCharacters(in: CharacterSet(charactersIn: "()"))
                    if loc.lowercased().contains("arriving") || loc.lowercased().contains("leaving") {
                        location = loc
                    }
                    title = String(cleanLine[..<openParen]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            } else {
                title = cleanLine
            }
        }
        return (title, list, location, isCompleted)
    }

    private func parseFileLine(_ line: String) -> (path: String, filename: String, url: URL, details: [String: String], workPerformed: [String]) {
        var path = ""
        var details: [String: String] = [:]
        var workPerformed: [String] = []
        
        let parts = line.components(separatedBy: " | ")
        for part in parts {
            let trimmed = part.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("Path: ") {
                path = String(trimmed.dropFirst("Path: ".count))
            } else if trimmed.hasPrefix("Details: ") {
                let detailsStr = String(trimmed.dropFirst("Details: ".count))
                let pairs = detailsStr.components(separatedBy: ";")
                for pair in pairs {
                    let kv = pair.components(separatedBy: ":")
                    if kv.count >= 2 {
                        let k = kv[0].trimmingCharacters(in: .whitespacesAndNewlines)
                        let v = kv[1...].joined(separator: ":").trimmingCharacters(in: .whitespacesAndNewlines)
                        if !k.isEmpty && !v.isEmpty {
                            details[k] = v
                        }
                    }
                }
            } else if trimmed.hasPrefix("Work: ") {
                let workStr = String(trimmed.dropFirst("Work: ".count))
                workPerformed = workStr.components(separatedBy: ";").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
            }
        }
        if path.isEmpty && line.hasPrefix("Path: ") {
            path = String(line.dropFirst("Path: ".count)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        let url = URL(fileURLWithPath: path)
        let filename = url.lastPathComponent.isEmpty ? "document" : url.lastPathComponent
        return (path, filename, url, details, workPerformed)
    }

    private var isMailLine: Bool { line.contains("Subject:") && line.contains("From:") }
    private var isCalendarLine: Bool {
        line.contains("Event:") || line.contains("Calendar:") || (line.contains("Time:") && line.contains("Location:")) || (line.contains("Service appointment") && line.contains("Tysons Corner"))
    }
    private var isReminderLine: Bool {
        line.hasPrefix("Reminder: ") || line.hasPrefix("Task: ") || line.contains("Reminder: ") || (line.contains("Inbox") && line.contains("Withdraw")) || line.lowercased().contains("reminder")
    }
    private var isFileLine: Bool { line.hasPrefix("Path: ") }

    private var icon: String {
        if isMailLine { return "envelope" }
        if isReminderLine { return "checklist" }
        if line.lowercased().contains("blocked") { return "hand.raised" }
        return "circle.fill"
    }

    private var iconColor: Color {
        if line.lowercased().contains("blocked") { return .orange }
        return .secondary
    }
}

struct MailCard: View {
    let subject: String
    let from: String
    let date: String
    let mailBody: String?

    @State private var hovering = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: "envelope.fill")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(.blue)
                    .padding(6)
                    .background(Color.blue.opacity(0.12))
                    .clipShape(Circle())
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(subject.isEmpty ? "No Subject" : subject)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundStyle(.primary)
                        .lineLimit(1)
                    
                    Text("From: \(from)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                
                Spacer(minLength: 8)
                
                Text(date)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
            
            Divider()
                .opacity(0.4)
            
            if let bodyText = mailBody, !bodyText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                Text(bodyText)
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
                    .lineLimit(4)
                    .padding(.vertical, 4)
            }
            
            HStack(spacing: 8) {
                Button(action: {
                    if let url = URL(string: "message://") {
                        NSWorkspace.shared.open(url)
                    } else {
                        NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Applications/Mail.app"))
                    }
                }) {
                    Label("Open in Mail", systemImage: "arrow.up.forward.app.fill")
                        .font(.caption.weight(.semibold))
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
                
                Spacer()
                
                SourceChip("Mail")
            }
            .padding(.top, 4)
        }
        .padding(12)
        .background(Color.white.opacity(0.06))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(hovering ? Theme.electricBlue.opacity(0.4) : Color.white.opacity(0.12), lineWidth: 1)
        )
        .scaleEffect(hovering ? 1.01 : 1.0)
        .onHover { hovering = $0 }
        .animation(.smooth(duration: 0.15), value: hovering)
    }
}

struct FileCard: View {
    let filename: String
    let path: String
    let url: URL
    let details: [String: String]
    let workPerformed: [String]
    
    @State private var hovering = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(iconBgColor.opacity(0.15))
                    Image(systemName: iconName)
                        .font(.system(size: 16, weight: .bold))
                        .foregroundStyle(iconColor)
                }
                .frame(width: 36, height: 36)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(filename)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(.primary)
                        .lineLimit(1)
                    Text("Local Document")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                HStack(spacing: 6) {
                    IconSurfaceButton(systemName: "arrow.up.right.square", small: true) {
                        NSWorkspace.shared.open(url)
                    }
                    .help("Open File")
                    
                    IconSurfaceButton(systemName: "folder", small: true) {
                        NSWorkspace.shared.activateFileViewerSelecting([url])
                    }
                    .help("Reveal in Finder")
                }
            }
            
            if !details.isEmpty {
                Divider()
                    .opacity(0.3)
                    .padding(.vertical, 2)
                
                VStack(alignment: .leading, spacing: 6) {
                    Text("SERVICE DETAILS")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                        .tracking(0.5)
                        .padding(.bottom, 2)
                    
                    ForEach(details.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                        HStack(alignment: .top, spacing: 6) {
                            Text("•")
                                .foregroundStyle(Theme.electricCyan)
                            Text("\(key):")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundStyle(.secondary)
                            Text(value)
                                .font(.system(size: 13))
                                .foregroundStyle(.primary)
                        }
                    }
                }
            }
            
            if !workPerformed.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Work Performed:")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.secondary)
                        .padding(.top, 4)
                    
                    ForEach(workPerformed, id: \.self) { item in
                        HStack(alignment: .top, spacing: 6) {
                            Text("-")
                                .foregroundStyle(.tertiary)
                            Text(item)
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        .padding(.leading, 8)
                    }
                }
            }
        }
        .padding(12)
        .background(Color.white.opacity(0.06))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(hovering ? Theme.electricCyan.opacity(0.4) : Color.white.opacity(0.12), lineWidth: 1)
        )
        .scaleEffect(hovering ? 1.01 : 1.0)
        .onHover { hovering = $0 }
        .animation(.smooth(duration: 0.15), value: hovering)
    }
    
    private var iconName: String {
        let ext = url.pathExtension.lowercased()
        if ext == "pdf" { return "doc.text.fill" }
        if ["png", "jpg", "jpeg", "gif", "tiff"].contains(ext) { return "photo.fill" }
        if ["xlsx", "xls", "csv"].contains(ext) { return "tablecells.fill" }
        if ["pages", "docx", "doc"].contains(ext) { return "doc.richtext.fill" }
        return "doc.fill"
    }
    
    private var iconColor: Color {
        let ext = url.pathExtension.lowercased()
        if ext == "pdf" { return Color.red }
        if ["xlsx", "xls", "csv"].contains(ext) { return Theme.electricCyan }
        if ["pages", "docx", "doc"].contains(ext) { return Theme.electricBlue }
        return .secondary
    }
    
    private var iconBgColor: Color {
        let ext = url.pathExtension.lowercased()
        if ext == "pdf" { return Color.red }
        if ["xlsx", "xls", "csv"].contains(ext) { return Theme.electricCyan }
        if ["pages", "docx", "doc"].contains(ext) { return Theme.electricBlue }
        return .secondary
    }
}

struct CalendarCard: View {
    let day: String
    let title: String
    let location: String?
    let time: String?
    
    @State private var hovering = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(day)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.secondary)
                .padding(.leading, 4)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(title)
                            .font(.system(size: 15, weight: .bold))
                            .foregroundStyle(.white)
                        
                        if let loc = location, !loc.isEmpty {
                            HStack(spacing: 6) {
                                Image(systemName: "mappin.and.ellipse")
                                    .font(.system(size: 11))
                                    .foregroundStyle(.white.opacity(0.8))
                                Text(loc)
                                    .font(.system(size: 12))
                                    .foregroundStyle(.white.opacity(0.8))
                            }
                        }
                        
                        if let t = time, !t.isEmpty {
                            HStack(spacing: 6) {
                                Image(systemName: "clock")
                                    .font(.system(size: 11))
                                    .foregroundStyle(.white.opacity(0.8))
                                Text(t)
                                    .font(.system(size: 12))
                                    .foregroundStyle(.white.opacity(0.8))
                            }
                        }
                    }
                    
                    Spacer()
                    
                    Image(systemName: "calendar")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(.white.opacity(0.4))
                        .padding(.top, 2)
                }
                
                HStack {
                    Spacer()
                    Button(action: {
                        NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Applications/Calendar.app"))
                    }) {
                        Label("Calendar", systemImage: "arrow.up.forward.app.fill")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.white)
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color.white.opacity(0.18))
                    .clipShape(Capsule())
                }
                .padding(.top, 4)
            }
            .padding(14)
            .background(
                LinearGradient(
                    colors: [Theme.vibrantPurple.opacity(0.72), Color(red: 0.42, green: 0.12, blue: 0.72).opacity(0.72)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .cornerRadius(14)
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(hovering ? Color.white.opacity(0.45) : Color.white.opacity(0.18), lineWidth: 1)
            )
            .scaleEffect(hovering ? 1.01 : 1.0)
            .onHover { hovering = $0 }
            .animation(.smooth(duration: 0.15), value: hovering)
        }
    }
}

struct ReminderCard: View {
    let title: String
    let listName: String
    let location: String?
    let isCompleted: Bool
    
    @State private var localCompleted = false
    @State private var hovering = false
    @State private var hoverCheckbox = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(listName)
                .font(.system(size: 14, weight: .bold))
                .foregroundStyle(Theme.electricBlue)
                .padding(.leading, 4)
            
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top, spacing: 12) {
                    Button(action: {
                        withAnimation(.spring) {
                            localCompleted.toggle()
                        }
                    }) {
                        Image(systemName: (localCompleted || isCompleted) ? "checkmark.circle.fill" : (hoverCheckbox ? "checkmark.circle" : "circle"))
                            .font(.system(size: 18, weight: .medium))
                            .foregroundStyle((localCompleted || isCompleted) ? Theme.electricCyan : .secondary)
                    }
                    .buttonStyle(.plain)
                    .onHover { hoverCheckbox = $0 }
                    
                    VStack(alignment: .leading, spacing: 6) {
                        Text(title)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(.primary)
                            .strikethrough(localCompleted || isCompleted)
                        
                        if let loc = location, !loc.isEmpty {
                            HStack(spacing: 5) {
                                Image(systemName: "mappin.circle.fill")
                                    .font(.system(size: 10))
                                Text(loc)
                                    .font(.system(size: 11, weight: .semibold))
                            }
                            .foregroundStyle(.white)
                            .padding(.horizontal, 9)
                            .padding(.vertical, 4)
                            .background(Color.red.opacity(0.8))
                            .clipShape(Capsule())
                        }
                    }
                    
                    Spacer()
                    
                    Button(action: {
                        NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Applications/Reminders.app"))
                    }) {
                        Image(systemName: "arrow.up.forward.app")
                            .font(.system(size: 14))
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .help("Open in Reminders")
                }
            }
            .padding(14)
            .background(Color.white.opacity(0.06))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(hovering ? Theme.electricBlue.opacity(0.4) : Color.white.opacity(0.12), lineWidth: 1)
            )
            .scaleEffect(hovering ? 1.01 : 1.0)
            .onHover { hovering = $0 }
            .animation(.smooth(duration: 0.15), value: hovering)
        }
        .onAppear {
            localCompleted = isCompleted
        }
    }
}

struct LatestResultCard: View {
    let text: String

    var body: some View {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                Label("Tool output", systemImage: "terminal.fill")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Text(String(trimmed.suffix(900)))
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
                    .textSelection(.enabled)
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(nsColor: .controlBackgroundColor).opacity(0.62))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
    }
}

struct ApprovalCard: View {
    let request: ApprovalRequest
    let approve: () -> Void
    let deny: () -> Void
    
    @State private var hovering = false
    @State private var hoveringApprove = false
    @State private var hoveringDeny = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .fill(Theme.amberWarning.opacity(0.16))
                    Image(systemName: "hand.raised.fill")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(Theme.amberWarning)
                }
                .frame(width: 42, height: 42)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Approval required")
                        .font(.headline)
                    Text(request.action.name)
                        .font(.system(.body, design: .monospaced))
                        .textSelection(.enabled)
                }

                Spacer(minLength: 0)
            }

            VStack(alignment: .leading, spacing: 6) {
                ForEach(request.action.args.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                    HStack(alignment: .top, spacing: 8) {
                        Text(key)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                            .frame(width: 84, alignment: .leading)
                        Text(value)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                            .lineLimit(4)
                    }
                }
            }

            HStack(spacing: 12) {
                Button(role: .cancel, action: deny) {
                    Label("Deny", systemImage: "xmark.circle")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(hoveringDeny ? .white : Theme.neonPink)
                }
                .buttonStyle(.bordered)
                .tint(Theme.neonPink)
                .controlSize(.small)
                .onHover { hoveringDeny = $0 }

                Button(action: approve) {
                    Label("Approve", systemImage: "checkmark.circle.fill")
                        .font(.caption.weight(.bold))
                }
                .buttonStyle(.borderedProminent)
                .tint(Theme.brightEmerald)
                .controlSize(.small)
                .onHover { hoveringApprove = $0 }

                Spacer()
            }
            .padding(.top, 4)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.amberWarning.opacity(0.06))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(hovering ? Theme.amberWarning.opacity(0.4) : Theme.amberWarning.opacity(0.16), lineWidth: 1)
        )
        .scaleEffect(hovering ? 1.01 : 1.0)
        .onHover { hovering = $0 }
        .animation(.smooth(duration: 0.15), value: hovering)
    }
}

struct SourceStrip: View {
    let chips: [String]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 7) {
                ForEach(chips, id: \.self) { SourceChip($0) }
            }
        }
    }
}

struct SourceChip: View {
    let text: String
    init(_ text: String) { self.text = text }

    var body: some View {
        HStack(spacing: 5) {
            Image(systemName: sourceIcon(text))
                .font(.system(size: 10, weight: .semibold))
            Text(text)
                .font(.caption2.weight(.semibold))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.74))
        .clipShape(Capsule())
    }
}

struct StatusPill: View {
    let status: String
    let running: Bool

    var body: some View {
        HStack(spacing: 5) {
            Circle()
                .fill(running ? Color.orange : Theme.electricCyan)
                .frame(width: 6, height: 6)
            Text(status)
                .font(.caption2.weight(.bold))
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 5)
        .background((running ? Color.orange : Theme.electricCyan).opacity(0.14))
        .clipShape(Capsule())
    }
}
