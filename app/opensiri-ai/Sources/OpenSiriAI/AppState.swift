import Foundation
import Observation

struct ChatMessage: Identifiable, Equatable {
    enum Role { case user, assistant, system }
    let id = UUID()
    let role: Role
    let text: String
    let date = Date()
}

struct ApprovalRequest: Identifiable, Equatable, Decodable {
    struct ActionPayload: Equatable, Decodable {
        let name: String
        let args: [String: String]

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            name = try container.decode(String.self, forKey: .name)
            let raw = try container.decodeIfPresent([String: AnyCodable].self, forKey: .args) ?? [:]
            args = raw.mapValues { $0.description }
        }

        enum CodingKeys: String, CodingKey { case name, args }
    }
    let id: String
    let action: ActionPayload
    let verdict: [String: AnyCodable]
}

struct AnyCodable: Decodable, CustomStringConvertible, Equatable {
    let description: String
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(String.self) { description = value }
        else if let value = try? container.decode(Int.self) { description = String(value) }
        else if let value = try? container.decode(Double.self) { description = String(value) }
        else if let value = try? container.decode(Bool.self) { description = String(value) }
        else { description = "" }
    }
}

struct SessionSummary: Identifiable, Equatable, Decodable {
    let session_id: String
    let task: String
    let started_at: Double
    var id: String { session_id }
}

@Observable
@MainActor
final class AppState {
    var task: String = ""
    var output: String = ""
    var technicalLog: String = ""
    var showTechnicalLog: Bool = false
    var messages: [ChatMessage] = [
        ChatMessage(role: .system, text: "Ask for a Mac action, file comparison, reminder, or personal-context question.")
    ]
    var status: String = "Idle"
    var modelURL: String = AppState.initialModelURL()
    var modelName: String = UserDefaults.standard.string(forKey: "modelName") ?? "default_model"
    var visionModelURL: String = UserDefaults.standard.string(forKey: "visionModelURL") ?? ""
    var visionModelName: String = UserDefaults.standard.string(forKey: "visionModelName") ?? ""
    var analysisModelURL: String = UserDefaults.standard.string(forKey: "analysisModelURL") ?? ""
    var analysisModelName: String = UserDefaults.standard.string(forKey: "analysisModelName") ?? ""
    var hypersaveBaseURL: String = UserDefaults.standard.string(forKey: "hypersaveBaseURL") ?? "https://api.hypersave.io"
    var repoRoot: String = AppState.initialRepoRoot()
    var approvalMode: String = UserDefaults.standard.string(forKey: "approvalMode") ?? "deny"
    var enableMemory: Bool = UserDefaults.standard.bool(forKey: "enableMemory")
    var enableMemoryWrite: Bool = UserDefaults.standard.bool(forKey: "enableMemoryWrite")
    var enableLocalIndex: Bool = UserDefaults.standard.bool(forKey: "enableLocalIndex")
    var enableFiles: Bool = UserDefaults.standard.bool(forKey: "enableFiles")
    var enableFinder: Bool = UserDefaults.standard.bool(forKey: "enableFinder")
    var enableFinderWrite: Bool = UserDefaults.standard.bool(forKey: "enableFinderWrite")
    var enableWeb: Bool = UserDefaults.standard.bool(forKey: "enableWeb")
    var enableVisual: Bool = UserDefaults.standard.bool(forKey: "enableVisual")
    var enableMail: Bool = UserDefaults.standard.bool(forKey: "enableMail")
    var enableMailWrite: Bool = UserDefaults.standard.bool(forKey: "enableMailWrite")
    var enableMessages: Bool = UserDefaults.standard.bool(forKey: "enableMessages")
    var enableMessagesWrite: Bool = UserDefaults.standard.bool(forKey: "enableMessagesWrite")
    var enableReminders: Bool = UserDefaults.standard.bool(forKey: "enableReminders")
    var enableRemindersWrite: Bool = UserDefaults.standard.bool(forKey: "enableRemindersWrite")
    var enableNotes: Bool = UserDefaults.standard.bool(forKey: "enableNotes")
    var enableNotesWrite: Bool = UserDefaults.standard.bool(forKey: "enableNotesWrite")
    var enablePhotos: Bool = UserDefaults.standard.bool(forKey: "enablePhotos")
    var enableCalendar: Bool = UserDefaults.standard.bool(forKey: "enableCalendar")
    var enableContacts: Bool = UserDefaults.standard.bool(forKey: "enableContacts")
    var enableBrowser: Bool = UserDefaults.standard.bool(forKey: "enableBrowser")
    var enableBrowserWrite: Bool = UserDefaults.standard.bool(forKey: "enableBrowserWrite")
    var enableSystem: Bool = UserDefaults.standard.bool(forKey: "enableSystem")
    var enableSystemWrite: Bool = UserDefaults.standard.bool(forKey: "enableSystemWrite")
    var enableMaps: Bool = UserDefaults.standard.bool(forKey: "enableMaps")
    var enableMusic: Bool = UserDefaults.standard.bool(forKey: "enableMusic")
    var enablePodcasts: Bool = UserDefaults.standard.bool(forKey: "enablePodcasts")
    var liveAX: Bool = true
    var isRunning: Bool = false
    var lastTranscript: String = ""
    var approvalRequest: ApprovalRequest? = nil
    var showHistory: Bool = false
    var sessionSummaries: [SessionSummary] = []
    var process: Process? = nil
    var approvalDir: URL? = nil

    var auditURL: URL { dataRoot().appendingPathComponent("results/app-audit.jsonl") }
    var sessionDir: URL { FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".local/share/opensiri-ai/sessions") }

    var sourceChips: [String] {
        var chips: [String] = []
        if liveAX { chips.append("Screen") }
        if enableMemory { chips.append("Memory") }
        if enableMemoryWrite { chips.append("Memory Write") }
        if enableLocalIndex { chips.append("Local Index") }
        if enableFiles { chips.append("Files") }
        if enableFinder { chips.append("Finder") }
        if enableFinderWrite { chips.append("Finder Write") }
        if enableWeb { chips.append("Web") }
        if enableVisual { chips.append("Visual") }
        if enableMail { chips.append("Mail") }
        if enableMailWrite { chips.append("Mail Send") }
        if enableMessages { chips.append("Messages") }
        if enableMessagesWrite { chips.append("Message Send") }
        if enableNotes { chips.append("Notes") }
        if enableNotesWrite { chips.append("Notes Write") }
        if enableReminders { chips.append("Reminders") }
        if enableRemindersWrite { chips.append("Reminder Write") }
        if enablePhotos { chips.append("Photos") }
        if enableCalendar { chips.append("Calendar") }
        if enableContacts { chips.append("Contacts") }
        if enableBrowser { chips.append("Browser") }
        if enableSystem { chips.append("System") }
        if !visionModelURL.isEmpty && !visionModelName.isEmpty { chips.append("Vision Model") }
        if !analysisModelURL.isEmpty && !analysisModelName.isEmpty { chips.append("Analysis Model") }
        if enableMaps { chips.append("Maps") }
        if enableMusic { chips.append("Music") }
        if enablePodcasts { chips.append("Podcasts") }
        return chips
    }

    static func isRepoRoot(_ path: String) -> Bool {
        FileManager.default.fileExists(atPath: path + "/src/eliot_harness")
    }

    static func initialRepoRoot() -> String {
        if let saved = UserDefaults.standard.string(forKey: "repoRoot"), isRepoRoot(saved) {
            return saved
        }
        return detectRepoRoot()
    }

    static func initialModelURL() -> String {
        guard let saved = UserDefaults.standard.string(forKey: "modelURL"), !saved.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return "http://127.0.0.1:8081"
        }
        return saved == "http://localhost:8081" ? "http://127.0.0.1:8081" : saved
    }

    static func detectRepoRoot() -> String {
        let fm = FileManager.default
        let cwd = fm.currentDirectoryPath
        let home = fm.homeDirectoryForCurrentUser.path
        var candidates = [
            cwd,
            Bundle.main.bundleURL.deletingLastPathComponent().path,
            home + "/Downloads/eliot-harness",
            home + "/Downloads/elliot/eliot-harness",
            home + "/Downloads/opensiri-ai",
            home + "/Projects/eliot-harness",
            home + "/Projects/opensiri-ai"
        ]

        var probe = Bundle.main.bundleURL
        for _ in 0..<10 {
            probe.deleteLastPathComponent()
            candidates.append(probe.path)
        }

        for path in candidates {
            if fm.fileExists(atPath: path + "/src/eliot_harness") {
                return path
            }
        }
        return home + "/Library/Application Support/opensiri-ai"
    }

    func dataRoot() -> URL {
        let fm = FileManager.default
        if fm.fileExists(atPath: repoRoot + "/src/eliot_harness") {
            return URL(fileURLWithPath: repoRoot)
        }
        let url = fm.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/opensiri-ai")
        try? fm.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    func persist() {
        UserDefaults.standard.set(modelURL, forKey: "modelURL")
        UserDefaults.standard.set(modelName, forKey: "modelName")
        UserDefaults.standard.set(visionModelURL, forKey: "visionModelURL")
        UserDefaults.standard.set(visionModelName, forKey: "visionModelName")
        UserDefaults.standard.set(analysisModelURL, forKey: "analysisModelURL")
        UserDefaults.standard.set(analysisModelName, forKey: "analysisModelName")
        UserDefaults.standard.set(hypersaveBaseURL, forKey: "hypersaveBaseURL")
        UserDefaults.standard.set(repoRoot, forKey: "repoRoot")
        UserDefaults.standard.set(approvalMode, forKey: "approvalMode")
        UserDefaults.standard.set(enableMemory, forKey: "enableMemory")
        UserDefaults.standard.set(enableMemoryWrite, forKey: "enableMemoryWrite")
        UserDefaults.standard.set(enableLocalIndex, forKey: "enableLocalIndex")
        UserDefaults.standard.set(enableFiles, forKey: "enableFiles")
        UserDefaults.standard.set(enableFinder, forKey: "enableFinder")
        UserDefaults.standard.set(enableFinderWrite, forKey: "enableFinderWrite")
        UserDefaults.standard.set(enableWeb, forKey: "enableWeb")
        UserDefaults.standard.set(enableVisual, forKey: "enableVisual")
        UserDefaults.standard.set(enableMail, forKey: "enableMail")
        UserDefaults.standard.set(enableMailWrite, forKey: "enableMailWrite")
        UserDefaults.standard.set(enableMessages, forKey: "enableMessages")
        UserDefaults.standard.set(enableMessagesWrite, forKey: "enableMessagesWrite")
        UserDefaults.standard.set(enableReminders, forKey: "enableReminders")
        UserDefaults.standard.set(enableRemindersWrite, forKey: "enableRemindersWrite")
        UserDefaults.standard.set(enableNotes, forKey: "enableNotes")
        UserDefaults.standard.set(enableNotesWrite, forKey: "enableNotesWrite")
        UserDefaults.standard.set(enablePhotos, forKey: "enablePhotos")
        UserDefaults.standard.set(enableCalendar, forKey: "enableCalendar")
        UserDefaults.standard.set(enableContacts, forKey: "enableContacts")
        UserDefaults.standard.set(enableBrowser, forKey: "enableBrowser")
        UserDefaults.standard.set(enableBrowserWrite, forKey: "enableBrowserWrite")
        UserDefaults.standard.set(enableSystem, forKey: "enableSystem")
        UserDefaults.standard.set(enableSystemWrite, forKey: "enableSystemWrite")
        UserDefaults.standard.set(enableMaps, forKey: "enableMaps")
        UserDefaults.standard.set(enableMusic, forKey: "enableMusic")
        UserDefaults.standard.set(enablePodcasts, forKey: "enablePodcasts")
        writeHarnessConfig()
    }

    func writeHarnessConfig() {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let configURL = home.appendingPathComponent(".config/opensiri-ai/config.json")
        let sources: [String: [String: Any]] = [
            "hypersave": ["read": enableMemory || enableMemoryWrite, "write": enableMemoryWrite, "max_sensitivity": "high"],
            "files": ["read": enableFiles, "write": false, "max_sensitivity": "high"],
            "finder": ["read": enableFinder || enableFinderWrite, "write": enableFinderWrite, "max_sensitivity": "high"],
            "web": ["read": enableWeb, "write": false, "max_sensitivity": "external"],
            "photos": ["read": enablePhotos, "write": false, "max_sensitivity": "hyper"],
            "visual": ["read": enableVisual, "write": false, "max_sensitivity": "hyper"],
            "calendar": ["read": enableCalendar, "write": false, "max_sensitivity": "medium"],
            "contacts": ["read": enableContacts, "write": false, "max_sensitivity": "high"],
            "notes": ["read": enableNotes || enableNotesWrite, "write": enableNotesWrite, "max_sensitivity": "high"],
            "reminders": ["read": enableReminders || enableRemindersWrite, "write": enableRemindersWrite, "max_sensitivity": "medium"],
            "maps": ["read": enableMaps, "write": false, "max_sensitivity": "medium"],
            "music": ["read": enableMusic, "write": false, "max_sensitivity": "medium"],
            "podcasts": ["read": enablePodcasts, "write": false, "max_sensitivity": "medium"],
            "mail": ["read": enableMail || enableMailWrite, "write": enableMailWrite, "max_sensitivity": "hyper"],
            "messages": ["read": enableMessages || enableMessagesWrite, "write": enableMessagesWrite, "max_sensitivity": "hyper"],
            "messages_index": ["read": enableMessages || enableMessagesWrite, "write": false, "max_sensitivity": "hyper"],
            "browser": ["read": enableBrowser || enableBrowserWrite, "write": enableBrowserWrite, "max_sensitivity": "high"],
            "system": ["read": enableSystem || enableSystemWrite, "write": enableSystemWrite, "max_sensitivity": "medium"],
            "safari": ["read": false, "write": false, "max_sensitivity": "high"]
        ]
        let data: [String: Any] = [
            "model_url": modelURL,
            "model_name": modelName,
            "audit_path": "~/.local/share/opensiri-ai/audit.jsonl",
            "transcript_dir": "~/.local/share/opensiri-ai/transcripts",
            "network_enabled": enableWeb,
            "sources": sources
        ]
        do {
            try FileManager.default.createDirectory(at: configURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            let json = try JSONSerialization.data(withJSONObject: data, options: [.prettyPrinted, .sortedKeys])
            try json.write(to: configURL)
        } catch {
            status = "Config save failed"
        }
    }

    func loadSessionSummaries() {
        let fm = FileManager.default
        guard let files = try? fm.contentsOfDirectory(at: sessionDir, includingPropertiesForKeys: [.contentModificationDateKey]) else {
            sessionSummaries = []
            return
        }
        let decoder = JSONDecoder()
        sessionSummaries = files
            .filter { $0.pathExtension == "json" }
            .sorted { (try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast > (try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast }
            .prefix(30)
            .compactMap { url in
                guard let data = try? Data(contentsOf: url) else { return nil }
                return try? decoder.decode(SessionSummary.self, from: data)
            }
    }
}
