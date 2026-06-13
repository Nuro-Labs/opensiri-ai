import Foundation

enum HarnessBridge {
    @MainActor
    static func run(task: String, state: AppState) throws {
        state.persist()
        let root = URL(fileURLWithPath: state.repoRoot)
        let candidates = [root.appendingPathComponent(".venv/bin/python").path, "/usr/bin/python3"]
        let python = candidates.first { FileManager.default.isExecutableFile(atPath: $0) } ?? "/usr/bin/python3"
        let transcriptDir = root.appendingPathComponent("results/app-transcripts")
        try FileManager.default.createDirectory(at: transcriptDir, withIntermediateDirectories: true)
        let transcript = transcriptDir.appendingPathComponent("latest.json").path
        state.lastTranscript = transcript

        var args = ["-m", "eliot_harness.cli", "--model-url", state.modelURL, "--model-name", state.modelName, "--task", task, "--approval", state.approvalMode, "--transcript", transcript, "--audit-log", root.appendingPathComponent("results/app-audit.jsonl").path]
        if state.enableMemory { args.append("--enable-memory") }
        if state.enableFiles { args.append("--enable-files") }
        if state.enableWeb { args.append("--enable-web") }
        if state.liveAX { args.append("--live-ax") }

        let p = Process()
        p.currentDirectoryURL = root
        p.executableURL = URL(fileURLWithPath: python)
        p.arguments = args
        var env = ProcessInfo.processInfo.environment
        env["PYTHONPATH"] = root.appendingPathComponent("src").path
        if state.enableMemory, env["HYPERSAVE_API_KEY"] == nil, let key = Keychain.read(service: "opensiri-ai", account: "hypersave-api-key") { env["HYPERSAVE_API_KEY"] = key }
        p.environment = env

        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor in state.output += "\n" + text }
        }
        p.terminationHandler = { proc in
            Task { @MainActor in
                state.status = "Exited \(proc.terminationStatus)"
                state.isRunning = false
                state.process = nil
            }
        }
        state.output = ""
        state.status = "Running"
        state.isRunning = true
        state.process = p
        try p.run()
    }
}
