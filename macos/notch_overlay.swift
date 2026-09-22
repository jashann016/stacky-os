import Cocoa
import WebKit

class FloatingNotchPanel: NSPanel {
    override var canBecomeKey: Bool { return true }
    override var canBecomeMain: Bool { return true }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var panel: FloatingNotchPanel!
    var webView: WKWebView!
    var isVisible: Bool = true

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory) // Runs as a menu/accessory floating app without dock icon clutter

        guard let screen = NSScreen.main else {
            NSLog("Error: No main screen detected.")
            exit(1)
        }

        let screenWidth = screen.frame.width
        let screenHeight = screen.frame.height

        let panelWidth: CGFloat = 260
        let panelHeight: CGFloat = 72
        let xPos = (screenWidth - panelWidth) / 2
        let yPos = screenHeight - panelHeight + 4 // Clings directly beneath hardware notch

        let contentRect = NSRect(x: xPos, y: yPos, width: panelWidth, height: panelHeight)

        panel = FloatingNotchPanel(
            contentRect: contentRect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        panel.level = .floating
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.ignoresMouseEvents = false
        panel.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]

        // WebKit Configuration
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")
        
        webView = WKWebView(frame: NSRect(x: 0, y: 0, width: panelWidth, height: panelHeight), configuration: config)
        webView.setValue(false, forKey: "drawsBackground") // 100% transparency
        webView.autoresizingMask = [.width, .height]

        // Locate runtime HTML file
        let currentDir = FileManager.default.currentDirectoryPath
        let htmlPath = URL(fileURLWithPath: currentDir).appendingPathComponent("stacky_notch_bar_runtime.html")

        if FileManager.default.fileExists(atPath: htmlPath.path) {
            webView.loadFileURL(htmlPath, allowingReadAccessTo: htmlPath.deletingLastPathComponent())
        } else {
            NSLog("Warning: Could not find stacky_notch_bar_runtime.html at \(htmlPath.path)")
        }

        panel.contentView = webView
        panel.orderFrontRegardless()

        print("[+] Stacky Native Notch Overlay running at (x: \(xPos), y: \(yPos))")
        print("[+] Send 'toggle', 'hide', 'show', or 'exit' via stdin.")

        // Listen on background thread for stdin commands to toggle or control
        DispatchQueue.global(qos: .background).async { [weak self] in
            while let line = readLine() {
                let cmd = line.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
                DispatchQueue.main.async {
                    switch cmd {
                    case "toggle":
                        self?.togglePanel()
                    case "hide":
                        self?.panel.orderOut(nil)
                        self?.isVisible = false
                    case "show":
                        self?.panel.orderFrontRegardless()
                        self?.isVisible = true
                    case "exit", "quit":
                        NSApp.terminate(nil)
                    default:
                        break
                    }
                }
            }
        }
    }

    func togglePanel() {
        if isVisible {
            panel.orderOut(nil)
            isVisible = false
            print("[+] Notch overlay hidden.")
        } else {
            panel.orderFrontRegardless()
            isVisible = true
            print("[+] Notch overlay visible.")
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
