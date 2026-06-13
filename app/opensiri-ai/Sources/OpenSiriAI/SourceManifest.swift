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
    .init(id: "messages", title: "Messages", sensitivity: "hyper", read: "opt-in local database", write: "draft/send with approval"),
    .init(id: "photos", title: "Photos", sensitivity: "hyper", read: "album metadata", write: "approval-only scaffold"),
    .init(id: "visual", title: "Visual OCR", sensitivity: "hyper", read: "interactive screenshot OCR", write: "none"),
    .init(id: "maps", title: "Maps", sensitivity: "medium", read: "directions/search", write: "open directions"),
    .init(id: "music", title: "Music", sensitivity: "medium", read: "library search", write: "play/pause"),
    .init(id: "podcasts", title: "Podcasts", sensitivity: "medium", read: "search", write: "open/play handoff"),
    .init(id: "safari", title: "Safari", sensitivity: "high", read: "tabs", write: "open URL"),
    .init(id: "photos", title: "Photos", sensitivity: "hyper", read: "not implemented", write: "not implemented"),
    .init(id: "web", title: "Web", sensitivity: "external", read: "bounded search", write: "none"),
]
