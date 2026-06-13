#!/usr/bin/env swift
import EventKit
import Foundation

let args = Array(CommandLine.arguments.dropFirst())
guard let command = args.first else {
    FileHandle.standardError.write(Data("usage: eventkit_bridge.swift COMMAND [ARGS...]\n".utf8))
    exit(2)
}

let store = EKEventStore()

func request(_ entity: EKEntityType) -> Bool {
    let sem = DispatchSemaphore(value: 0)
    var granted = false
    store.requestAccess(to: entity) { ok, _ in
        granted = ok
        sem.signal()
    }
    _ = sem.wait(timeout: .now() + 20)
    return granted
}

func printLines(_ lines: [String]) {
    print(lines.joined(separator: "\n"))
}

switch command {
case "calendar-today":
    guard request(.event) else { exit(3) }
    let calendar = Calendar.current
    let start = calendar.startOfDay(for: Date())
    let end = calendar.date(byAdding: .day, value: 1, to: start) ?? Date()
    let predicate = store.predicateForEvents(withStart: start, end: end, calendars: nil)
    let formatter = DateFormatter()
    formatter.timeStyle = .short
    formatter.dateStyle = .none
    let lines = store.events(matching: predicate)
        .sorted { $0.startDate < $1.startDate }
        .prefix(20)
        .map { "\(formatter.string(from: $0.startDate))-\(formatter.string(from: $0.endDate)): \($0.title ?? "Untitled")" }
    printLines(Array(lines))
case "create-event":
    guard args.count >= 2 else { exit(2) }
    guard request(.event) else { exit(3) }
    let event = EKEvent(eventStore: store)
    event.title = args[1]
    event.calendar = store.defaultCalendarForNewEvents
    event.startDate = Date()
    event.endDate = Date().addingTimeInterval(3600)
    try store.save(event, span: .thisEvent)
    print("created event: \(event.title ?? "Untitled")")
case "reminders":
    guard request(.reminder) else { exit(3) }
    let predicate = store.predicateForReminders(in: nil)
    let sem = DispatchSemaphore(value: 0)
    var lines: [String] = []
    store.fetchReminders(matching: predicate) { reminders in
        lines = (reminders ?? [])
            .filter { !$0.isCompleted }
            .prefix(20)
            .map { $0.title ?? "Untitled" }
        sem.signal()
    }
    _ = sem.wait(timeout: .now() + 20)
    printLines(lines)
case "add-reminder":
    guard args.count >= 2 else { exit(2) }
    guard request(.reminder) else { exit(3) }
    let reminder = EKReminder(eventStore: store)
    reminder.title = args[1]
    reminder.calendar = store.defaultCalendarForNewReminders()
    try store.save(reminder, commit: true)
    print("created reminder: \(reminder.title ?? "Untitled")")
default:
    FileHandle.standardError.write(Data("unknown command: \(command)\n".utf8))
    exit(2)
}
