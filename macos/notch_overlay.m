#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

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
    CGFloat xPos = (screenFrame.size.width - width) / 2.0;
    CGFloat yPos = screenFrame.size.height - height + 4.0; // Anchored directly below hardware notch

    NSRect contentRect = NSMakeRect(xPos, yPos, width, height);

    self.panel = [[FloatingNotchPanel alloc] initWithContentRect:contentRect
                                                       styleMask:NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
                                                         backing:NSBackingStoreBuffered
                                                           defer:NO];

    [self.panel setLevel:NSFloatingWindowLevel];
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
    [self.panel orderFrontRegardless];
    self.isVisible = YES;

    printf("[+] Stacky Native macOS Notch Overlay running at (x: %.1f, y: %.1f)\n", xPos, yPos);
    printf("[+] Interactive commands: 'toggle', 'hide', 'show', 'exit'\n");
    fflush(stdout);

    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_BACKGROUND, 0), ^{
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), stdin)) {
            NSString *input = [[NSString stringWithUTF8String:buffer] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]].lowercaseString;
            dispatch_async(dispatch_get_main_queue(), ^{
                if ([input isEqualToString:@"toggle"]) {
                    [self toggle];
                } else if ([input isEqualToString:@"hide"]) {
                    [self.panel orderOut:nil];
                    self.isVisible = NO;
                    printf("[+] Notch overlay hidden.\n");
                    fflush(stdout);
                } else if ([input isEqualToString:@"show"]) {
                    [self.panel orderFrontRegardless];
                    self.isVisible = YES;
                    printf("[+] Notch overlay shown.\n");
                    fflush(stdout);
                } else if ([input isEqualToString:@"exit"] || [input isEqualToString:@"quit"]) {
                    [NSApp terminate:nil];
                }
            });
        }
    });
}

- (void)toggle {
    if (self.isVisible) {
        [self.panel orderOut:nil];
        self.isVisible = NO;
        printf("[+] Notch overlay hidden.\n");
    } else {
        [self.panel orderFrontRegardless];
        self.isVisible = YES;
        printf("[+] Notch overlay shown.\n");
    }
    fflush(stdout);
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
