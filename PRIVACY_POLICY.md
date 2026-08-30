# Privacy Policy — Gamepadla+

**Last updated:** 2026-08-30

**In short:** Gamepadla+ does not collect personal data. Test results are only sent to gamepadla.com if you explicitly choose to upload them.

---

## 1. Introduction

Gamepadla+ is an open-source desktop application that measures the polling rate and synthetic latency of gamepad controllers. This privacy policy explains what data the app handles, how it is used, and what choices you have.

## 2. Information We Collect

Gamepadla+ does **not** collect personal information such as your name, email address, IP address, or account details.

During a test run, the app gathers the following technical data to display your results:

- **Operating system** — OS name (e.g. "Windows") and version string
- **Gamepad/controller name** — the hardware name as reported by the OS
- **Test results** — minimum, average, and maximum latency; polling rate; jitter; and all raw timing samples
- **App version** — e.g. "gamepadla-plus@1.8.2"
- **Test date and time** — local date/time of the test
- **Test identifier** — a random UUID (v4) generated for each test run, not tied to any user identity

If you choose to upload a result, two additional fields are included:

- **Connection type** — "Cable", "Bluetooth", or "Dongle" (selected by you)
- **Gamepad name** — a name you enter for the controller

## 3. How Information Is Used

All test data is displayed locally in the app. Gamepadla+ does not send any data automatically or in the background.

If you explicitly click **"Upload Result"** (GUI) or pass the `--upload` flag (CLI), the test data described above is sent to [gamepadla.com](https://gamepadla.com) so that you can view and share your results online.

## 4. Data Transmission to Third Parties

When you choose to upload a result, your test data is sent to:

- **Recipient:** [gamepadla.com](https://gamepadla.com)
- **Endpoint:** `https://gamepadla.com/scripts/poster.php` (HTTPS POST)
- **Triggered by:** explicit user action only (button click or CLI flag)

**Disclaimer:** The developer of Gamepadla+ has no control over gamepadla.com's data handling practices. Please refer to [gamepadla.com](https://gamepadla.com) for information about how they process and store uploaded data.

No other third-party services, analytics, telemetry, or tracking are used.

## 5. Local Data Storage

Gamepadla+ does **not** persist any data to disk by default. There are no configuration files, databases, log files, or caches.

The only local file operations are:

- **Save to file** — you can choose to save test results as a JSON file to a location of your choice
- **License display** — the app reads its own license files from the installation directory

## 6. Hardware Access

Gamepadla+ reads analog stick input from connected gamepad controllers via [pygame](https://www.pygame.org/) / SDL. This is limited to reading axis positions (X/Y) to measure timing between input changes.

The app does **not** access the camera, microphone, location, contacts, or any other hardware.

## 7. Children's Privacy

Gamepadla+ is not directed at children under the age of 16. The app does not knowingly collect any data from children.

## 8. Your Rights Under GDPR

If you are in the European Economic Area, you have the following rights under the General Data Protection Regulation (GDPR):

- **Right of access** — request a copy of your data
- **Right to rectification** — request correction of inaccurate data
- **Right to erasure** — request deletion of your data
- **Right to restrict processing** — request limitation of data processing
- **Right to data portability** — request your data in a portable format
- **Right to object** — object to data processing

Since Gamepadla+ does not store any data about you, these rights apply primarily to data you may have uploaded to gamepadla.com. For requests related to uploaded data, please contact gamepadla.com directly.

For questions about this privacy policy or the app's data practices, contact:

**dev@mckellar.eu**

## 9. Changes to This Policy

Any changes to this privacy policy will be reflected in the [project repository](https://github.com/WyvernIXTL/gamepadla-plus) with an updated "Last updated" date.

## 10. Contact

If you have questions or concerns about this privacy policy, please contact:

**dev@mckellar.eu**
