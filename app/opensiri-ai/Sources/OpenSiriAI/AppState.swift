import Foundation

struct ChatMessage: Identifiable, Equatable {
    enum Role { case user, assistant, system }
    let id = UUID()
    let role: Role
    let text: String
    let date = Date()
}

@MainActor
final class AppState: ObservableObject {
    @Published var task: String = ""
    @Published var output: String = ""
    @Published var technicalLog: String = ""
    @Published var showTechnicalLog: Bool = false
    @Published var messages: [ChatMessage] = [
        ChatMessage(role: .system, text: "Ask for a Mac action, file comparison, reminder, or personal-context question.")
    ]
    @Published var status: String = "Idle"
    @Published var modelURL: String = UserDefaults.standard.string(forKey: "modelURL") ?? "http://localhost:8081"
    @Published var modelName: String = UserDefaults.standard.string(forKey: "modelName") ?? "default_model"
    @Published var hypersaveBaseURL: String = UserDefaults.standard.string(forKey: "hypersaveBaseURL") ?? "https://api.hypersave.io"
    @Published var repoRoot: String = AppState.initialRepoRoot()
    @Published var approvalMode: String = UserDefaults.standard.string(forKey: "approvalMode") ?? "deny"
    @Published var enableMemory: Bool = UserDefaults.standard.bool(forKey: "enableMemory")
    @Published var enableMemoryWrite: Bool = UserDefaults.standard.bool(forKey: "enableMemoryWrite")
    @Published var enableFiles: Bool = UserDefaults.standard.bool(forKey: "enableFiles")
    @Published var enableWeb: Bool = UserDefaults.standard.bool(forKey: "enableWeb")
    @Published var enableVisual: Bool = UserDefaults.standard.bool(forKey: "enableVisual")
    @Published var enableMaps: Bool = UserDefaults.standard.bool(forKey: "enableMaps")
    @Published var enableMusic: Bool = UserDefaults.standard.bool(forKey: "enableMusic")
    @Published var enablePodcasts: Bool = UserDefaults.standard.bool(forKey: "enablePodcasts")
    @Published var liveAX: Bool = true
    @Published var isRunning: Bool = false
    @Published var lastTranscript: String = ""
    var process: Process?

    var sourceChips: [String] {
        var chips = ["Guarded", "Audit"]
        if liveAX { chips.append("Screen") }
        if enableMemory { chips.append("Memory") }
        if enableMemoryWrite { chips.append("Memory Write") }
        if enableFiles { chips.append("Files") }
        if enableWeb { chips.append("Web") }
        if enableVisual { chips.append("Visual") }
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

    static func detectRepoRoot() -> String {
        let fm = FileManager.default
        let cwd = fm.currentDirectoryPath
        let home = fm.homeDirectoryForCurrentUser.path
        let candidates = [
            cwd,
            home + "/Downloads/eliot-harness",
            home + "/Downloads/opensiri-ai",
            home + "/Projects/eliot-harness",
            home + "/Projects/opensiri-ai"
        ]
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
        UserDefaults.standard.set(hypersaveBaseURL, forKey: "hypersaveBaseURL")
        UserDefaults.standard.set(repoRoot, forKey: "repoRoot")
        UserDefaults.standard.set(approvalMode, forKey: "approvalMode")
        UserDefaults.standard.set(enableMemory, forKey: "enableMemory")
        UserDefaults.standard.set(enableMemoryWrite, forKey: "enableMemoryWrite")
        UserDefaults.standard.set(enableFiles, forKey: "enableFiles")
        UserDefaults.standard.set(enableWeb, forKey: "enableWeb")
        UserDefaults.standard.set(enableVisual, forKey: "enableVisual")
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
            "web": ["read": enableWeb, "write": false, "max_sensitivity": "external"],
            "photos": ["read": enableVisual, "write": false, "max_sensitivity": "hyper"],
            "calendar": ["read": false, "write": false, "max_sensitivity": "medium"],
            "contacts": ["read": false, "write": false, "max_sensitivity": "high"],
            "notes": ["read": false, "write": false, "max_sensitivity": "high"],
            "reminders": ["read": false, "write": false, "max_sensitivity": "medium"],
            "maps": ["read": enableMaps, "write": false, "max_sensitivity": "medium"],
            "music": ["read": enableMusic, "write": false, "max_sensitivity": "medium"],
            "podcasts": ["read": enablePodcasts, "write": false, "max_sensitivity": "medium"],
            "mail": ["read": false, "write": false, "max_sensitivity": "hyper"],
            "messages": ["read": false, "write": false, "max_sensitivity": "hyper"],
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
}
