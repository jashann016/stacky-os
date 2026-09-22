#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#import <Carbon/Carbon.h>
#import <AVFoundation/AVFoundation.h>
#import <Speech/Speech.h>

@interface FloatingNotchPanel : NSPanel
@end

@implementation FloatingNotchPanel
- (BOOL)canBecomeKeyWindow { return YES; }
- (BOOL)canBecomeMainWindow { return YES; }
@end

@interface AppDelegate : NSObject <NSApplicationDelegate, WKScriptMessageHandler>
@property (strong) FloatingNotchPanel *panel;
@property (strong) WKWebView *webView;
@property (assign) BOOL isVisible;
@property (assign) CGFloat topOffset;
@property (assign) NSTimeInterval lastCtrlPressTime;
@property (assign) BOOL wasCtrlDown;
@property (strong) id globalFlagsMonitor;
@property (strong) id localFlagsMonitor;
@property (strong) id globalKeyMonitor;
@property (strong) id localKeyMonitor;

// Native Audio & Speech Recognition Engine
@property (strong) AVAudioEngine *audioEngine;
@property (strong) SFSpeechRecognizer *speechRecognizer;
@property (strong) SFSpeechAudioBufferRecognitionRequest *recognitionRequest;
@property (strong) SFSpeechRecognitionTask *recognitionTask;
@property (strong) NSTimer *speechSilenceTimer;
@property (assign) BOOL isAudioCapturing;
@property (strong) AVSpeechSynthesizer *speechSynth;

- (void)showAndWake;
- (void)hideAndSleep;
- (void)toggle;
- (void)startAudioCapture;
- (void)stopAudioCapture;
- (void)sendSpokenCommandToStacky:(NSString *)spokenText;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification {
    [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];

    self.speechSynth = [[AVSpeechSynthesizer alloc] init];

    NSScreen *screen = [NSScreen mainScreen];
    if (!screen) {
        NSLog(@"Error: No main screen found.");
        exit(1);
    }

    NSRect screenFrame = screen.frame;

    // Detect exact hardware notch height (typically 32.0 pt on MacBook displays)
    CGFloat notchHeight = 32.0;
    if (@available(macOS 12.0, *)) {
        if (screen.safeAreaInsets.top > 0) {
            notchHeight = screen.safeAreaInsets.top;
        }
    }

    CGFloat gapBelowNotch = 6.0;
    CGFloat topOffset = notchHeight + gapBelowNotch; // 38.0 pt
    CGFloat width = 280.0;
    CGFloat capsuleHeight = 56.0;
    CGFloat shadowMargin = 26.0;
    CGFloat height = topOffset + capsuleHeight + shadowMargin; // 120.0 pt

    CGFloat xPos = screenFrame.origin.x + (screenFrame.size.width - width) / 2.0;
    CGFloat yPos = screenFrame.origin.y + screenFrame.size.height - height; // Top of window aligns with top of screen

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
    WKUserContentController *userContent = [[WKUserContentController alloc] init];
    [userContent addScriptMessageHandler:self name:@"stackyMic"];
    config.userContentController = userContent;

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
    self.topOffset = topOffset;

    NSString *jsSetOffset = [NSString stringWithFormat:@"document.documentElement.style.setProperty('--notch-offset', '%.1fpx');", topOffset];
    [self.webView evaluateJavaScript:jsSetOffset completionHandler:nil];

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
        [self showAndWake];
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

#pragma mark - WebKit Script Message Handler (Capsule Clicks)
- (void)userContentController:(WKUserContentController *)userContentController didReceiveScriptMessage:(WKScriptMessage *)message {
    if ([message.name isEqualToString:@"stackyMic"]) {
        if (self.isAudioCapturing) {
            [self stopAudioCapture];
            [self.webView evaluateJavaScript:@"setTask('listening', 'Mic Paused');" completionHandler:nil];
        } else {
            [self startAudioCapture];
            [self.webView evaluateJavaScript:@"setTask('listening', 'Listening...');" completionHandler:nil];
        }
    }
}

#pragma mark - Keyboard Event Handlers
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

#pragma mark - Window Visibility Lifecycle
- (void)showAndWake {
    if (self.isVisible) return;
    self.isVisible = YES;
    [self.panel orderFrontRegardless];
    [self.panel makeKeyWindow];
    [NSApp activateIgnoringOtherApps:YES];

    NSString *jsWake = [NSString stringWithFormat:@"document.documentElement.style.setProperty('--notch-offset', '%.1fpx'); if(window.wakeNotch){ window.wakeNotch(); }", self.topOffset];
    [self.webView evaluateJavaScript:jsWake completionHandler:nil];
    printf("[+] [WAKE] Notch Bar summoned -> Displaying below notch, arming mic.\n");
    fflush(stdout);

    // Turn ON the native microphone and speech recognizer (triggers orange indicator)
    [self startAudioCapture];
}

- (void)hideAndSleep {
    if (!self.isVisible) return;
    self.isVisible = NO;

    // Immediately stop microphone & cut audio stream
    [self stopAudioCapture];

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

#pragma mark - Native Microphone & Speech Recognition Engine
- (void)startAudioCapture {
    if (self.isAudioCapturing) return;

    AVAuthorizationStatus audioStatus = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeAudio];
    if (audioStatus == AVAuthorizationStatusNotDetermined) {
        [AVCaptureDevice requestAccessForMediaType:AVMediaTypeAudio completionHandler:^(BOOL granted) {
            if (granted) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self startAudioCapture];
                });
            } else {
                NSLog(@"[!] Microphone access denied by user.");
            }
        }];
        return;
    } else if (audioStatus != AVAuthorizationStatusAuthorized) {
        NSLog(@"[!] Microphone not authorized (status=%ld). Enable in System Settings -> Privacy & Security -> Microphone.", (long)audioStatus);
        dispatch_async(dispatch_get_main_queue(), ^{
            [self.webView evaluateJavaScript:@"setTask('listening', 'Mic Access Needed');" completionHandler:nil];
        });
        return;
    }

    if (!self.speechRecognizer) {
        self.speechRecognizer = [[SFSpeechRecognizer alloc] initWithLocale:[NSLocale localeWithLocaleIdentifier:@"en-US"]];
    }

    [SFSpeechRecognizer requestAuthorization:^(SFSpeechRecognizerAuthorizationStatus authStatus) {
        dispatch_async(dispatch_get_main_queue(), ^{
            [self beginRecordingSession];
        });
    }];
}

- (void)beginRecordingSession {
    if (self.isAudioCapturing) return;

    NSError *error = nil;

    if (self.recognitionTask) {
        [self.recognitionTask cancel];
        self.recognitionTask = nil;
    }

    self.audioEngine = [[AVAudioEngine alloc] init];
    self.recognitionRequest = [[SFSpeechAudioBufferRecognitionRequest alloc] init];
    self.recognitionRequest.shouldReportPartialResults = YES;

    AVAudioInputNode *inputNode = self.audioEngine.inputNode;
    AVAudioFormat *recordingFormat = [inputNode outputFormatForBus:0];

    __weak typeof(self) weakSelf = self;
    [inputNode installTapOnBus:0 bufferSize:1024 format:recordingFormat block:^(AVAudioPCMBuffer * _Nonnull buffer, AVAudioTime * _Nonnull when) {
        [weakSelf.recognitionRequest appendAudioPCMBuffer:buffer];
    }];

    [self.audioEngine prepare];
    if (![self.audioEngine startAndReturnError:&error]) {
        NSLog(@"AudioEngine start error: %@", error);
        return;
    }

    self.isAudioCapturing = YES;
    printf("[+] [MIC] Microphone is LIVE (Apple AudioEngine started, orange dot active).\n");
    fflush(stdout);

    dispatch_async(dispatch_get_main_queue(), ^{
        [self.webView evaluateJavaScript:@"setTask('listening', 'Listening to voice...');" completionHandler:nil];
    });

    self.recognitionTask = [self.speechRecognizer recognitionTaskWithRequest:self.recognitionRequest resultHandler:^(SFSpeechRecognitionResult * _Nullable result, NSError * _Nullable error) {
        if (result) {
            NSString *transcript = result.bestTranscription.formattedString;
            printf("[Voice Detected]: %s (final=%d)\n", [transcript UTF8String], result.isFinal);
            fflush(stdout);

            dispatch_async(dispatch_get_main_queue(), ^{
                NSString *escaped = [[transcript stringByReplacingOccurrencesOfString:@"\\" withString:@"\\\\"] stringByReplacingOccurrencesOfString:@"'" withString:@"\\'"];
                NSString *js = [NSString stringWithFormat:@"if(window.onVoiceRecognized){ window.onVoiceRecognized('%@', %d); }", escaped, result.isFinal];
                [weakSelf.webView evaluateJavaScript:js completionHandler:nil];

                // If speech pauses or completes, trigger Stacky thinking
                [weakSelf scheduleSpeechTimeoutForTranscript:transcript isFinal:result.isFinal];
            });
        }
        if (error) {
            // Task completed or ended
        }
    }];
}

- (void)stopAudioCapture {
    if (!self.isAudioCapturing) return;
    self.isAudioCapturing = NO;

    [self.speechSilenceTimer invalidate];
    self.speechSilenceTimer = nil;

    if (self.audioEngine) {
        if (self.audioEngine.isRunning) {
            [self.audioEngine stop];
            [self.audioEngine.inputNode removeTapOnBus:0];
        }
        self.audioEngine = nil;
    }

    if (self.recognitionRequest) {
        [self.recognitionRequest endAudio];
        self.recognitionRequest = nil;
    }

    if (self.recognitionTask) {
        [self.recognitionTask cancel];
        self.recognitionTask = nil;
    }

    printf("[+] [MIC] Microphone DISARMED & closed (orange dot OFF).\n");
    fflush(stdout);
}

- (void)scheduleSpeechTimeoutForTranscript:(NSString *)transcript isFinal:(BOOL)isFinal {
    [self.speechSilenceTimer invalidate];
    if (isFinal) {
        [self sendSpokenCommandToStacky:transcript];
        return;
    }
    if (transcript.length > 0) {
        __weak typeof(self) weakSelf = self;
        self.speechSilenceTimer = [NSTimer scheduledTimerWithTimeInterval:1.6 repeats:NO block:^(NSTimer * _Nonnull timer) {
            [weakSelf sendSpokenCommandToStacky:transcript];
        }];
    }
}

- (void)sendSpokenCommandToStacky:(NSString *)spokenText {
    if (spokenText.length == 0) return;
    printf("[+] Dispatching voice query to Stacky Cloud: %s\n", [spokenText UTF8String]);
    fflush(stdout);

    // Update UI to working mode
    dispatch_async(dispatch_get_main_queue(), ^{
        [self.webView evaluateJavaScript:@"setTask('working', 'Thinking...');" completionHandler:nil];
    });

    // Send HTTP POST to Render Cloud Backend
    NSURL *url = [NSURL URLWithString:@"https://stacky-os.onrender.com/api/chat"];
    NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:url];
    req.HTTPMethod = @"POST";
    [req setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    [req setValue:@"923352" forHTTPHeaderField:@"X-Stacky-Key"];

    NSDictionary *body = @{@"message": spokenText};
    req.HTTPBody = [NSJSONSerialization dataWithJSONObject:body options:0 error:nil];

    NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithRequest:req completionHandler:^(NSData * _Nullable data, NSURLResponse * _Nullable response, NSError * _Nullable error) {
        if (data) {
            NSDictionary *json = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
            NSString *reply = json[@"reply"] ?: json[@"response"] ?: @"System online, sir.";
            NSString *spokenText = json[@"spoken_summary"] ?: reply;
            BOOL isSplit = [json[@"is_split_mode"] boolValue];

            NSString *displayStatus = isSplit ? @"Sent briefing to Telegram" : reply;
            if (displayStatus.length > 28) {
                displayStatus = [[displayStatus substringToIndex:25] stringByAppendingString:@"..."];
            }
            dispatch_async(dispatch_get_main_queue(), ^{
                NSString *escaped = [[displayStatus stringByReplacingOccurrencesOfString:@"\\" withString:@"\\\\"] stringByReplacingOccurrencesOfString:@"'" withString:@"\\'"];
                NSString *js = [NSString stringWithFormat:@"setTask('explaining', '%@');", escaped];
                [self.webView evaluateJavaScript:js completionHandler:nil];

                // Speak reply using modern AVFoundation speech synthesizer
                [self.speechSynth stopSpeakingAtBoundary:AVSpeechBoundaryImmediate];
                AVSpeechUtterance *utterance = [AVSpeechUtterance speechUtteranceWithString:spokenText];
                utterance.voice = [AVSpeechSynthesisVoice voiceWithLanguage:@"en-US"];
                utterance.rate = AVSpeechUtteranceDefaultSpeechRate;
                [self.speechSynth speakUtterance:utterance];

                // Return to listening state after speaking
                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(6.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
                    if (self.isVisible) {
                        [self.webView evaluateJavaScript:@"setTask('listening', 'Listening...');" completionHandler:nil];
                    }
                });
            });
        }
    }];
    [task resume];
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
