# Voice input on the review pages

The pages cannot use the microphone (the artifact frame refuses it). Dictate with the system:

| System | How |
|---|---|
| iPhone, Android | The mic key on the keyboard |
| macOS | Dictation: press Fn twice (System Settings > Keyboard > Dictation) |
| Windows | Win+H |
| Linux (KDE Plasma, GNOME) | No system dictation. Free, offline options: **Speech Note** (`dsnote`, Flatpak `net.mkiol.SpeechNote`; Whisper or Vosk models, can type into the focused window) or **nerd-dictation** (Vosk, a hotkey types into any field). On NixOS, check `nix search nixpkgs dsnote` first; otherwise use the Flatpak. |

Whisper models are better with French; Vosk is lighter. Both run locally (no paid service).
Not verified on a real KDE Plasma 6 session: try Speech Note first and report what works.
