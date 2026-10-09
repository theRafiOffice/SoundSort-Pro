<div align="center">

# 🎧 SoundSort Pro

**A fast, accurate, and multi-format audio length organization tool built for audio engineers, sound designers, and content creators.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge)]()

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Supported Formats](#-supported-formats)
- [Requirements](#-requirements)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Building a Standalone Executable (.exe)](#-building-a-standalone-executable-exe)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Edge Case Handling & Safety](#-edge-case-handling--safety)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 💡 Overview

Managing large sound libraries, sample packs, podcasts, or voiceover recordings can be exhausting. **SoundSort Pro** solves this by scanning source directories, evaluating the exact floating-point metadata duration of every audio file, and organizing matching tracks into dedicated destination directories.

Whether you need to extract quick sound effects (<= 15 seconds) or filter out long audio clips, **SoundSort Pro** delivers pinpoint accuracy without freezing your computer or modifying your original files without permission.

---

## ✨ Key Features

- ⚡ **Multi-Engine Metadata Parsing:** Combines `mutagen` with a `tinytag` fallback mechanism for instant, zero-latency duration detection across formats.
- 🎯 **Floating-Point Accuracy:** Evaluates duration values down to millisecond precision (15.0001s > 15.0000s) rather than relying on rounded interface numbers.
- 🧵 **Responsive Threaded UI:** Built on a background worker thread and thread-safe queue system, ensuring the GUI remains responsive during large file operations.
- 🎨 **Modern Dark Aesthetic:** Native cross-platform interface using a custom dark theme (`#1e1e2e` Mocha palette) with zero external GUI library bloat.
- 🛡️ **Collision & Recurrence Protection:** Automatically appends incremental counters (`track_1.mp3`, `track_2.mp3`) when duplicate file names are encountered, and skips destination subdirectories to prevent infinite loops.
- 📊 **Real-Time Live Logs:** Color-coded status updates, execution progress bars, and clear post-run processing statistics.

---

## 🔄 How It Works

```text
  ┌──────────────────┐
  │  Source Folder   │  (e.g., D:\RawAudios)
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Duration Scanner │ ──> Reads metadata via Mutagen / TinyTag
  └────────┬─────────┘
           │
     Is Duration <= Limit?
      ├── YES ──> [Copy / Move] ──> ┌────────────────────────┐
      │                             │ Destination Folder     │
      │                             │  └── <= 15 Seconds/    │
      │                             └────────────────────────┘
      └── NO  ──> [Skip File]   ──> Logged in Live Terminal
