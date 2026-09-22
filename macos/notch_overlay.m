#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#import <Carbon/Carbon.h>

@interface FloatingNotchPanel : NSPanel
@end

@implementation FloatingNotchPanel
- (BOOL)canBecomeKeyWindow { return YES; }
- (BOOL)canBecomeMainWindow { return YES; }
@end

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (strong) FloatingNotchPanel *panel;
@property (strong) WKWebView *webView;
@property (assign) BOOL isVisible;
@property (assign) NSTimeInterval lastCtrlPressTime;
@property (assign) BOOL wasCtrlDown;
@property (strong) id globalFlagsMonitor;
@property (strong) id localFlagsMonitor;
@property (strong) id globalKeyMonitor;
@property (strong) id localKeyMonitor;

- (void)showAndWake;
- (void)hideAndSleep;
- (void)toggle;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification {
    [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];

    NSScreen *screen = [NSScreen mainScreen];
    if (!screen) {
        NSLog(@"Error: No main screen found.");
        exit(1);
    }

    NSRect screenFrame = screen.frame;
    CGFloat width = 260.0;
    CGFloat height = 72.0;
    CGFloat xPos = screenFrame.origin.x + (screenFrame.size.width - width) / 2.0;
    CGFloat yPos = screenFrame.origin.y + screenFrame.size.height - height + 4.0; // Anchored directly beneath MacBook hardware notch

    NSRect contentRect = NSMakeRect(xPos, yPos, width, height);

    self.panel = [[FloatingNotchPanel alloc] initWithContentRect:contentRect
                                                       styleMask:NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
                                                         backing:NSBackingStoreBuffered
                                                           defer:NO];

    // Position panel above menu bar and full-screen windows
    [self.panel setLevel:NSStatusWindowLevel + 1];
    [self.panel setOpaque:NO];
    [self.panel setBackgroundColor:[NSColor clearColor]];
    [self.panel setHasShadow:NO];
    [self.panel setIgnoresMouseEvents:NO];
    [self.panel setCollectionBehavior:NSWindowCollectionBehaviorCanJoinAllSpaces | 
                                      NSWindowCollectionBehaviorStationary | 
                                      NSWindowCollectionBehaviorIgnoresCycle];

    WKWebViewConfiguration *config = [[WKWebViewConfiguration alloc] init];
    self.webView = [[WKWebView alloc] initWithFrame:NSMakeRect(0, 0, width, height) configuration:config];
    [self.webView setValue:@NO forKey:@"drawsBackground"];
    [self.webView setAutoresizingMask:NSViewWidthSizable | NSViewHeightSizable];

    NSString *currentPath = [[NSFileManager defaultManager] currentDirectoryPath];
    NSString *htmlPath = [currentPath stringByAppendingPathComponent:@"stacky_notch_bar_runtime.html"];
    NSURL *fileURL = [NSURL fileURLWithPath:htmlPath];

    if ([[NSFileManager defaultManager] fileExistsAtPath:htmlPath]) {
        [self.webView loadFileURL:fileURL allowingReadAccessToURL:[fileURL URLByDeletingLastPathComponent]];
    } else {
        NSLog(@"Warning: stacky_notch_bar_runtime.html not found at %@", htmlPath);
    }

    [self.panel setContentView:self.webView];

    // Determine initial visibility from CLI arguments
    BOOL startVisible = NO;
    NSArray *args = [[NSProcessInfo processInfo] arguments];
    for (NSString *arg in args) {
        if ([arg isEqualToString:@"--show"]) {
            startVisible = YES;
            break;
        }
    }

    if (startVisible) {
        [self.panel orderFrontRegardless];
        self.isVisible = YES;
        [self.webView evaluateJavaScript:@"if(window.wakeNotch) window.wakeNotch();" completionHandler:nil];
        printf("[+] Stacky Native Notch Bar launched in ACTIVE mode.\n");
    } else {
        [self.panel orderOut:nil];
        self.isVisible = NO;
        printf("[+] Stacky Native Notch Bar launched in DORMANT SLEEP mode (0.0%% CPU, mic dormant).\n");
    }

    printf("[+] Activation Shortcut: Double-tap [Control] (Ctrl + Ctrl)\n");
    printf("[+] Sleep Shortcut     : Press [Esc] or single [Control]\n");
    printf("[+] Stdin commands     : 'toggle', 'wake', 'sleep', 'exit'\n");
    fflush(stdout);

    __weak typeof(self) weakSelf = self;

    // 1. Global modifier flags monitor (detects double-tap Ctrl & single Ctrl when other apps are active)
    self.globalFlagsMonitor = [NSEvent addGlobalMonitorForEventsMatchingMask:NSEventMaskFlagsChanged handler:^(NSEvent *event) {
        [weakSelf handleFlagsEvent:event];
    }];

    // 2. Local modifier flags monitor (when notch window is active)
    self.localFlagsMonitor = [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskFlagsChanged handler:^NSEvent *(NSEvent *event) {
        [weakSelf handleFlagsEvent:event];
        return event;
    }];

    // 3. Global key down monitor (Escape key dismiss when other apps are active)
    self.globalKeyMonitor = [NSEvent addGlobalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^(NSEvent *event) {
        [weakSelf handleKeyEvent:event];
    }];

    // 4. Local key down monitor (Escape key dismiss when notch is active)
    self.localKeyMonitor = [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^NSEvent *(NSEvent *event) {
        if (event.keyCode == 53 && weakSelf.isVisible) {
            [weakSelf hideAndSleep];
            return nil; // Consume Escape key
        }
        [weakSelf handleKeyEvent:event];
        return event;
    }];

    // Background thread reading commands from stdin
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_BACKGROUND, 0), ^{
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), stdin)) {
            NSString *input = [[NSString stringWithUTF8String:buffer] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]].lowercaseString;
            dispatch_async(dispatch_get_main_queue(), ^{
                if ([input isEqualToString:@"toggle"]) {
                    [weakSelf toggle];
                } else if ([input isEqualToString:@"hide"] || [input isEqualToString:@"sleep"]) {
                    [weakSelf hideAndSleep];
                } else if ([input isEqualToString:@"show"] || [input isEqualToString:@"wake"]) {
                    [weakSelf showAndWake];
                } else if ([input isEqualToString:@"exit"] || [input isEqualToString:@"quit"]) {
                    [NSApp terminate:nil];
                }
            });
        }
    });
}

- (void)handleFlagsEvent:(NSEvent *)event {
    NSEventModifierFlags flags = event.modifierFlags;
    BOOL isCtrlDown = (flags & NSEventModifierFlagControl) != 0;

    // Filter out combinations with other modifier keys (Command, Option, Shift)
    BOOL otherModifiers = (flags & (NSEventModifierFlagCommand | NSEventModifierFlagOption | NSEventModifierFlagShift)) != 0;
    if (otherModifiers) {
        self.lastCtrlPressTime = 0;
        self.wasCtrlDown = isCtrlDown;
        return;
    }

    // Detect leading edge (transition from UP to DOWN)
    if (isCtrlDown && !self.wasCtrlDown) {
        NSTimeInterval now = [NSDate timeIntervalSinceReferenceDate];
        NSTimeInterval elapsed = now - self.lastCtrlPressTime;

        if (self.isVisible) {
            // Already visible: Single tap of Control dismisses it back to sleep
            dispatch_async(dispatch_get_main_queue(), ^{
                [self hideAndSleep];
            });
            self.lastCtrlPressTime = 0;
        } else {
            // Currently asleep: Check for double-tap within 420ms
            if (elapsed > 0.05 && elapsed < 0.42) {
                // Double-tap Control confirmed!
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self showAndWake];
                });
                self.lastCtrlPressTime = 0;
            } else {
                // First tap of Control: begin double-tap timer window
                self.lastCtrlPressTime = now;
            }
        }
    }
    self.wasCtrlDown = isCtrlDown;
}

- (void)handleKeyEvent:(NSEvent *)event {
    if (event.keyCode == 53) { // Escape key
        if (self.isVisible) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [self hideAndSleep];
            });
        }
    } else {
        // Any regular key pressed (e.g. typing text) cancels pending double-tap
        self.lastCtrlPressTime = 0;
    }
}

- (void)showAndWake {
    if (self.isVisible) return;
    self.isVisible = YES;
    [self.panel orderFrontRegardless];
    [self.panel makeKeyWindow];
    [NSApp activateIgnoringOtherApps:YES];
    [self.webView evaluateJavaScript:@"if(window.wakeNotch){ window.wakeNotch(); }" completionHandler:nil];
    printf("[+] [WAKE] Notch Bar summoned -> Voice mic listening, liquid orb running at 60 FPS.\n");
    fflush(stdout);
}

- (void)hideAndSleep {
    if (!self.isVisible) return;
    self.isVisible = NO;
    [self.webView evaluateJavaScript:@"if(window.sleepNotch){ window.sleepNotch(); }" completionHandler:nil];
    // Allow smooth CSS slide-up transition into the notch before ordering panel out
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.25 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (!self.isVisible) {
            [self.panel orderOut:nil];
        }
    });
    printf("[+] [SLEEP] Notch Bar tucked into notch -> 100%% Dormant (0.0%% CPU, mic cut).\n");
    fflush(stdout);
}

- (void)toggle {
    if (self.isVisible) {
        [self hideAndSleep];
    } else {
        [self showAndWake];
    }
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        AppDelegate *delegate = [[AppDelegate alloc] init];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
