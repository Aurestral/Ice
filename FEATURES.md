## Key Features and Commands in Ice -1 IDE

Ice -1 (Minus One) IDE  is a dark-themed, AI-powered code editor with an embedded terminal, debugger, and multi-language support. Below is a comprehensive list of its core features and commands, grouped by category for clarity. Most are accessible via the topbar menus (File/Tools/Settings), keyboard shortcuts, or right-click context menus.

#### File and Project Management

| Feature/Command            | Description                                                                                                   | Access                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **New File**               | Create a new file (default: `.gust` for AI pseudocode).                                                       | File > New File or Ctrl+N (add via binding if needed). |
| **Open File**              | Open an existing file into a tab.                                                                             | File > Open File... or double-click in Explorer.       |
| **Save**                   | Save the current tab's content.                                                                               | File > Save or Ctrl+S.                                 |
| **Open Folder**            | Switch to a project directory (updates Explorer and terminal).                                                | File > Open Folder....                                 |
| **New Folder (Switch To)** | Create and switch to a new project folder.                                                                    | File > New Folder (Switch To)....                      |
| **Close Folder**           | Return to default `~/IceProjects` (closes tabs, resets terminal).                                             | File > Close Folder.                                   |
| **Close Tab**              | Close the active tab.                                                                                         | File > Close Tab or F4.                                |
| **Close All Tabs**         | Close all open tabs.                                                                                          | File > Close All Tabs.                                 |
| **Project Explorer**       | Tree view of files/folders with auto-refresh (every 1s), expand/collapse. Right-click: Open, Refresh, Delete. | Left pane (hidden venv by default).                    |
#### Code Editing and Syntax

| Feature/Command         | Description                                                                                   | Access                                     |
| ----------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **Syntax Highlighting** | Colors for keywords, strings, numbers, comments, functions, datatypes, booleans, parentheses. | Automatic on load/edit (KeyRelease event). |
| **Line Numbers**        | Gutter with line numbers, synced scrolling.                                                   | Built into editor (DarkScrolledText).      |
| **Tab Indent**          | Tab key inserts 4 spaces.                                                                     | Editor binding.                            |
| **Breakpoints**         | Visual toggle (red background) and functional (for debugger).                                 | Click line margin or F9 on current line.   |
#### Running and Execution

| Feature/Command               | Description                                                                                                                           | Access                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **Run Code**                  | Execute current file in embedded terminal. Supports Python, JS, Java, C/C++, Rust, Go, HTML (manual browser). Auto-saves first.       | Run button or F5.                                     |
| **Gust Files (.gust)**        | AI translates pseudocode to target language (e.g., `<python>` header). Extracts `ice.prompt()` for context. Saves as `.py`/`.js`/etc. | Run a `.gust` file (uses Groq API).                   |
| **AI Debugging (ice.gust())** | Auto-fixes bugs/syntax in code starting with `ice.gust()`. Replaces editor content and saves.                                         | Run file with `ice.gust()` on line 1.                 |
| **Multi-Language Support**    | Detects lang from extension; uses configured interpreters (e.g., `g++` for C++ compile+run).                                          | Run button; configure via Tools > Select Interpreter. |
#### Terminal

| Feature/Command       | Description                                                                              | Access                                      |
| --------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Embedded Terminal** | Real shell (cmd.exe on Windows, bash on Linux/Mac). No visible consoles; resizable pane. | Bottom pane; type commands + Enter.         |
| **Send Command**      | Programmatically send to terminal (e.g., for Run/Debug).                                 | Internal (e.g., via Run button).            |
| **Venv Creation**     | Creates/activates project venv; updates Python interpreter.                              | Tools > Create Venv (overwrites if exists). |
#### Debugging

| Feature/Command          | Description                                                  | Access                        |
| ------------------------ | ------------------------------------------------------------ | ----------------------------- |
| **Toggle Breakpoint**    | Add/remove breakpoint at line (F9 or click). Lists in panel. | F9 or click margin.           |
| **Start Debug**          | Run Python file with pdb.                                    | Debug Panel > Start Debug.    |
| **Step Over/Into/Out**   | Navigate code line-by-line.                                  | Debug Panel buttons.          |
| **Continue**             | Resume until next breakpoint.                                | Debug Panel > Continue.       |
| **Inspect Vars**         | Print args/locals.                                           | Debug Panel > Inspect Vars.   |
| **Call Stack**           | Show stack trace.                                            | Debug Panel > Call Stack.     |
| **Stop Debug**           | End session.                                                 | Debug Panel > Stop.           |
| **Toggle Debug Panel**   | Show/hide left-side debug UI (breakpoints, vars, stack).     | Tools > Toggle Debug Panel.   |
| **Advanced Debug Tools** | Activates panel + terminal message.                          | Tools > Advanced Debug Tools. |
#### Settings and Configurations

|Feature/Command|Description|Access|
|---|---|---|
|**Settings Dialog**|Set Groq API key and AI model; persists in `config.json` (`%APPDATA%\IceIDE`).|Settings button (topbar) or auto-opens if no key.|
|**Select Interpreter**|Per-language interpreter picker (e.g., Python: system/venv/custom). Tests availability.|Tools > Select Interpreter or interpreter button.|
|**Status Indicator**|Shows Python interp (system/venv) + version.|Topbar right.|
#### Keyboard Shortcuts

| Shortcut   | Action             |
| ---------- | ------------------ |
| **Ctrl+S** | Save current tab.  |
| **F5**     | Run code.          |
| **F4**     | Close current tab. |
| **F9**     | Toggle breakpoint. |
#### Other Features

- **AI Integration**: Groq API for translation/debugging (error handling for rate limits).
- **Themes/Styles**: Darkly theme with custom dark scrollbars/treeviews.
- **Resource Handling**: Icons bundled via resource_path (works in .exe).
- **Error Resilience**: Subprocess wrappers hide Windows consoles; graceful fallbacks for missing icons/API.