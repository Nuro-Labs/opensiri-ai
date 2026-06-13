import AppKit
import SwiftUI

struct NativeInput: NSViewRepresentable {
    @Binding var text: String
    let placeholder: String
    let fontSize: CGFloat
    let focusToken: Int
    let onSubmit: () -> Void

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeNSView(context: Context) -> NSTextField {
        let field = NSTextField(string: text)
        field.placeholderString = placeholder
        field.isBordered = false
        field.isBezeled = false
        field.drawsBackground = false
        field.focusRingType = .none
        field.isEditable = true
        field.isSelectable = true
        field.usesSingleLineMode = true
        field.lineBreakMode = .byTruncatingTail
        field.font = .systemFont(ofSize: fontSize, weight: .medium)
        field.textColor = .labelColor
        field.delegate = context.coordinator
        return field
    }

    func updateNSView(_ field: NSTextField, context: Context) {
        context.coordinator.parent = self
        if !context.coordinator.isEditing && field.stringValue != text { field.stringValue = text }
        field.placeholderString = placeholder
        field.font = .systemFont(ofSize: fontSize, weight: .medium)
        if context.coordinator.lastFocusToken != focusToken {
            context.coordinator.lastFocusToken = focusToken
            DispatchQueue.main.async {
                guard let window = field.window else { return }
                window.makeKeyAndOrderFront(nil)
                window.makeFirstResponder(field)
                if let editor = window.fieldEditor(true, for: field) as? NSTextView {
                    editor.selectedRange = NSRange(location: field.stringValue.count, length: 0)
                }
            }
        }
    }

    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: NativeInput
        var isEditing = false
        var lastFocusToken = -1
        init(_ parent: NativeInput) { self.parent = parent }

        func controlTextDidBeginEditing(_ obj: Notification) { isEditing = true }

        func controlTextDidEndEditing(_ obj: Notification) { isEditing = false }

        func controlTextDidChange(_ obj: Notification) {
            guard let field = obj.object as? NSTextField else { return }
            parent.text = field.stringValue
        }

        func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
            if commandSelector == #selector(NSResponder.insertNewline(_:)) {
                parent.text = (control as? NSTextField)?.stringValue ?? parent.text
                parent.onSubmit()
                return true
            }
            return false
        }
    }
}
