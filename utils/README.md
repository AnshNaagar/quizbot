# 🤖 Advanced Telegram Quiz Bot

Welcome to the Advanced Telegram Quiz Bot! This bot is a fully-featured, high-volume quiz platform designed for Telegram. It supports advanced features like pre-set categories (UPSC, SSC, etc.), custom quiz set lengths, a 15-second timer using native Quiz Polls, and is built on a scalable MongoDB architecture.

## ✨ Features

- **Native Quiz Polls:** Uses Telegram's native Quiz Poll feature with a 15-second timer for engaging gameplay.
- **Dynamic Categories:** Supports a large volume of quizzes segmented by categories (e.g., General Science, Indian Polity).
- **Session Management:** Tracks user progress, score, and preferred quiz length (20 to 100 questions).
- **Scalable Database:** Uses MongoDB Atlas for flexible and high-volume data storage.
- **Heroku Ready:** Built with deployment in mind (includes Procfile, app.json, runtime.txt).

## 🚀 Deployment Guide (Deploy to Heroku)

Follow these steps to deploy your bot successfully.

### 1. Prerequisites (Zaroori Cheezein)

1.  **Bot Token:** Obtain your token from Telegram's **@BotFather**.
2.  **MongoDB Atlas:** Create a free cluster on MongoDB Atlas and get the **Connection String URL**.
3.  **Heroku Account:** A verified Heroku account.

### 2. Database Setup (Crucial!)

Before deploying, your MongoDB Atlas must be ready with initial data:

1.  **Create Database:** Ensure you have a database named `quiz` on Atlas.
2.  **Create Collections:** Create the following three collections:
    * `categories`
    * `questions`
    * `sessions`
3.  **Insert Initial Data:** Insert at least two documents into the **`categories`** collection and a few test questions into the **`questions`** collection (jaisa humne discussion mein kiya tha).

### 3. Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/AnshNaagar/quizbot)

The easiest way to deploy is by using the Heroku button (if you put this on a public repo) or by connecting your GitHub repo.

1.  **Connect Repo:** Log in to Heroku, go to the **Deploy** tab, and connect your GitHub repository.
2.  **Set Config Vars:** During deployment, Heroku will ask for configuration variables (secrets). You must set these two:

| Key | Value | Description |
| :--- | :--- | :--- |
| **`BOT_TOKEN`** | Your token from BotFather. | Bot ka secret key. |
| **`DATABASE_URL`**| Your full MongoDB Atlas connection string (`mongodb+srv://...`). | Database se connect hone ka link. |

3.  **Deploy Branch:** Deploy your `main` branch.

### 4. Enable Worker Process

Since this is a Telegram bot, it runs as a background process, not a web server.

1.  Go to the **Resources** tab of your Heroku app.
2.  Find the **`worker`** process (defined in the `Procfile`).
3.  Click the pencil icon, toggle the switch to **ON**, and save it.

### 5. Final Test

Once the worker is running, go to Telegram and send the command:

`/start`

The bot should respond with the category selection buttons!

---
## ⚙️ Tech Stack

- **Language:** Python
- **Framework:** `python-telegram-bot` (with JobQueue and ConversationHandler)
- **Database:** MongoDB Atlas
- **Hosting:** Heroku
