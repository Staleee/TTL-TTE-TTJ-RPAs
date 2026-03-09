# Fonts folder (Arabic – in the code)

The Arabic phrase in the bottom-right ("بمرافقة العائلة") is handled **in the code**. You don't need to install anything.

- **Automatic:** On first run, the app downloads **Noto Sans Arabic** from Google's repo and saves it here as `NotoSansArabic-Regular.ttf`. After that, the font is used from this folder (local and on Railway).
- **Optional:** If you prefer no download (e.g. offline), you can add the font yourself: get [Noto Sans Arabic](https://fonts.google.com/noto/specimen/Noto+Sans+Arabic) and save the Regular .ttf as `NotoSansArabic-Regular.ttf` in this folder. Then commit it so Railway has it too.
- If the font can't be loaded, the app falls back to "Accompanied by family" in English so the field is never empty.
