<h1 align="center">
📬 dropcli
</h1>

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

</div>

<hr>

A robust, asynchronous script that uses httpx and beautifulsoup4 to generate a temporary email address from `dropmail.me`, monitors the inbox, and parses incoming emails in real-time.

## ✨ Core Features

- **Reliable Automation**: Uses Playwright to directly interact with the web page, making it more stable than manual request-based methods.
- **Real-time Monitoring**: After generating an email, the script actively watches the inbox for new messages.
- **Email Parsing**: Automatically extracts the sender, subject, and body from new emails.
- **Headless Operation**: Runs in the background without needing a visible browser window.
- **Resilient**: Gracefully handles partially loaded content, preventing crashes and ensuring continuous operation.

## 🛠️ Installation

### **Prerequisites**

- **Python 3.7+**

### **Setup**

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://github.com/Turtldeev/dropcli.git
    cd dropcli
    ```

2.  **Install Python dependencies:**
    The script requires the `playwright` library.
    ```bash
    pip install httpx beautifulsoup4
    ```

## 🚀 Usage

Once the setup is complete, you can run the script directly from your terminal:

```bash
python dropcli.py
```

The script will first fetch a new temporary email address and display it. Then, it will begin monitoring that inbox for new emails, printing a `.` every 5 seconds to show it's active.

### Example Output

```
===================================
  Temporary Email: ajndoldjqbphbp@dropmail.me
===================================

Waiting for new emails. Press Ctrl+C to exit.
....
--- New Email Found! ---
From: turtl <turtl@turtl.dev> <no-reply+ajndoldjqbphbp=dropmail.me@turtldev>
Subject: Hello world!
--------------------
Hello world!

[Proton](https://proton.me/)

Your verification code

Enter this code to finish the process:

845232

Stay secure,
The Turtldev

==============================
..
```

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE.md](LICENSE.md) file for details.
