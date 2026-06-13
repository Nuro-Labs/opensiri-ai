import Foundation

struct SourceManifest: Identifiable {
    let id: String
    let title: String
    let sensitivity: String
    let read: String
    let write: String
}

let sourceManifests: [SourceManifest] = [
    .init(id: "hypersave", title: "Hypersave Memory", sensitivity: "high", read: "search, ask, facts, profile", write: "save, remind"),
    .init(id: "files", title: "Files", sensitivity: "high", read: "list, read, compare", write: "create, copy, move"),
    .init(id: "calendar", title: "Calendar", sensitivity: "medium", read: "events, free/busy", write: "create/edit event"),
    .init(id: "contacts", title: "Contacts", sensitivity: "high", read: "scoped name lookup", write: "none"),
    .init(id: "notes", title: "Notes", sensitivity: "high", read: "list/read notes", write: "create note"),
    .init(id: "reminders", title: "Reminders", sensitivity: "medium", read: "list reminders", write: "create/complete"),
    .init(id: "mail", title: "Mail", sensitivity: "hyper", read: "subjects/selected", write: "draft/send with approval"),
    .init(id: "messages", title: "Messages", sensitivity: "hyper", read: "off by default", write: "draft/send with approval"),
    .init(id: "safari", title: "Safari", sensitivity: "high", read: "tabs", write: "open URL"),
    .init(id: "photos", title: "Photos", sensitivity: "hyper", read: "not implemented", write: "not implemented"),
    .init(id: "web", title: "Web", sensitivity: "external", read: "bounded search", write: "none"),
]
