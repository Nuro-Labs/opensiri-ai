import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var task: String = ""
    @Published var output: String = "Ready. Start Eliot, then ask for a Mac action or personal context."
    @Published var status: String = "Idle"
    @Published var modelURL: String = UserDefaults.standard.string(forKey: "modelURL") ?? "http://localhost:8081"
    @Published var modelName: String = UserDefaults.standard.string(forKey: "modelName") ?? "default_model"
    @Published var repoRoot: String = UserDefaults.standard.string(forKey: "repoRoot") ?? FileManager.default.currentDirectoryPath
    @Published var approvalMode: String = UserDefaults.standard.string(forKey: "approvalMode") ?? "deny"
    @Published var enableMemory: Bool = UserDefaults.standard.bool(forKey: "enableMemory")
    @Published var liveAX: Bool = true
    @Published var isRunning: Bool = false
    @Published var lastTranscript: String = ""
    var process: Process?

    func persist() {
        UserDefaults.standard.set(modelURL, forKey: "modelURL")
        UserDefaults.standard.set(modelName, forKey: "modelName")
        UserDefaults.standard.set(repoRoot, forKey: "repoRoot")
        UserDefaults.standard.set(approvalMode, forKey: "approvalMode")
        UserDefaults.standard.set(enableMemory, forKey: "enableMemory")
    }
}
