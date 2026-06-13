import Foundation

enum HarnessBridge {
    @MainActor
    static func run(task: String, state: AppState) throws {
        state.persist()
        let codeRootPath = AppState.isRepoRoot(state.repoRoot) ? state.repoRoot : AppState.detectRepoRoot()
        guard AppState.isRepoRoot(codeRootPath) else {
            throw NSError(domain: "opensiri-ai", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not find opensiri-ai repo root. Set Repo root in Settings."])
        }
        state.repoRoot = codeRootPath
        state.persist()
        let root = URL(fileURLWithPath: codeRootPath)
        let dataRoot = state.dataRoot()
        let candidates = ["/usr/bin/python3", "/opt/homebrew/bin/python3", root.appendingPathComponent(".venv/bin/python").path]
        let python = candidates.first { FileManager.default.isExecutableFile(atPath: $0) } ?? "/usr/bin/python3"
        let transcriptDir = dataRoot.appendingPathComponent("results/app-transcripts")
        let approvalDir = dataRoot.appendingPathComponent("results/approvals")
        try FileManager.default.createDirectory(at: transcriptDir, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: approvalDir, withIntermediateDirectories: true)
        let transcript = transcriptDir.appendingPathComponent("latest.json").path
        state.lastTranscript = transcript
        state.approvalDir = approvalDir

        var args = ["-m", "eliot_harness.cli", "--model-url", state.modelURL, "--model-name", state.modelName, "--task", task, "--approval", state.approvalMode, "--transcript", transcript, "--audit-log", dataRoot.appendingPathComponent("results/app-audit.jsonl").path]
        args += ["--approval-dir", approvalDir.path]
        args += ["--config", FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".config/opensiri-ai/config.json").path]
        if state.enableMemory || state.enableMemoryWrite { args.append("--enable-memory") }
        if state.enableMemoryWrite { args.append("--enable-memory-write") }
        if state.enableLocalIndex { args.append("--enable-local-index") }
        if state.enableFiles { args.append("--enable-files") }
        if state.enableFinder { args.append("--enable-finder") }
        if state.enableFinderWrite { args.append("--enable-finder-write") }
        if state.enableWeb { args.append("--enable-web") }
        if state.enableVisual { args.append("--enable-visual") }
        if state.enableMail { args.append("--enable-mail") }
        if state.enableMailWrite { args.append("--enable-mail-write") }
        if state.enableMessages { args.append("--enable-messages") }
        if state.enableMessagesWrite { args.append("--enable-messages-write") }
        if state.enablePhotos { args.append("--enable-photos") }
        if state.enableCalendar { args.append("--enable-calendar") }
        if state.enableContacts { args.append("--enable-contacts") }
        if state.enableBrowser { args.append("--enable-browser") }
        if state.enableBrowserWrite { args.append("--enable-browser-write") }
        if state.enableSystem { args.append("--enable-system") }
        if state.enableSystemWrite { args.append("--enable-system-write") }
        if state.enableMaps { args.append("--enable-maps") }
        if state.enableMusic { args.append("--enable-music") }
        if state.enablePodcasts { args.append("--enable-podcasts") }
        if state.liveAX { args.append("--live-ax") }

        let p = Process()
        p.currentDirectoryURL = root
        p.executableURL = URL(fileURLWithPath: python)
        p.arguments = args
        var env = ProcessInfo.processInfo.environment
        env["PYTHONPATH"] = root.appendingPathComponent("src").path
        if !state.visionModelURL.isEmpty { env["OPENSIRI_VLM_URL"] = state.visionModelURL }
        if !state.visionModelName.isEmpty { env["OPENSIRI_VLM_MODEL"] = state.visionModelName }
        if !state.visionModelURL.isEmpty, env["OPENSIRI_VLM_API_KEY"] == nil, let key = Keychain.read(service: "opensiri-ai", account: "vision-api-key") { env["OPENSIRI_VLM_API_KEY"] = key }
        if !state.analysisModelURL.isEmpty { env["OPENSIRI_ANALYSIS_URL"] = state.analysisModelURL }
        if !state.analysisModelName.isEmpty { env["OPENSIRI_ANALYSIS_MODEL"] = state.analysisModelName }
        if !state.analysisModelURL.isEmpty, env["OPENSIRI_ANALYSIS_API_KEY"] == nil, let key = Keychain.read(service: "opensiri-ai", account: "analysis-api-key") { env["OPENSIRI_ANALYSIS_API_KEY"] = key }
        if (state.enableMemory || state.enableMemoryWrite), env["HYPERSAVE_API_KEY"] == nil, let key = Keychain.read(service: "opensiri-ai", account: "hypersave-api-key") { env["HYPERSAVE_API_KEY"] = key }
        if state.enableMemory || state.enableMemoryWrite { env["HYPERSAVE_BASE_URL"] = state.hypersaveBaseURL }
        p.environment = env

        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor in state.output += "\n" + text }
            Task { @MainActor in state.technicalLog += text }
        }
        p.terminationHandler = { proc in
            Task { @MainActor in
                state.status = proc.terminationStatus == 0 ? "Done" : "Error"
                state.isRunning = false
                state.process = nil
                let final = sanitize(state.technicalLog.trimmingCharacters(in: .whitespacesAndNewlines))
                state.messages.append(ChatMessage(role: .assistant, text: final.isEmpty ? "No response." : final))
            }
        }
        state.output = ""
        state.technicalLog = ""
        state.messages.append(ChatMessage(role: .user, text: task))
        state.status = "Running"
        state.isRunning = true
        state.process = p
        try p.run()
    }

    private static func sanitize(_ text: String) -> String {
        if text.contains("<tool_call") { return "I couldn't parse the model tool response. Try rephrasing or use an explicit backend tool." }
        if text.contains("blocked-by-guard") { return "Blocked by the safety guard." }
        if text.contains("blocked-by-policy") { return "Blocked by permission policy." }
        return text
    }
}
