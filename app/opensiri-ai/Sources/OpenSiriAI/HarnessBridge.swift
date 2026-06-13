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
        let candidates = [root.appendingPathComponent(".venv/bin/python").path, "/usr/bin/python3"]
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
        if state.enableFiles { args.append("--enable-files") }
        if state.enableWeb { args.append("--enable-web") }
        if state.enableVisual { args.append("--enable-visual") }
        if state.enableMail { args.append("--enable-mail") }
        if state.enableMessages { args.append("--enable-messages") }
        if state.enablePhotos { args.append("--enable-photos") }
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
                state.status = "Exited \(proc.terminationStatus)"
                state.isRunning = false
                state.process = nil
                let final = state.technicalLog.trimmingCharacters(in: .whitespacesAndNewlines)
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
}
