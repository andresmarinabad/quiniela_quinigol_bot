# Quiniela Quinigol Telegram Bot

This project is a Telegram bot designed for a private group of friends to manage and track football betting games — specifically **Quiniela** and **Quinigol** — in a fun and automated way. It handles everything from user bets to real-time result checking and even generates a colored HTML scoreboard, rendered to GitHub Pages. The entire infrastructure is managed via **Terraform**, deploying to **AWS EC2 with auto-scaling**.

---

## 📁 Project Structure


```commandline
├── html
│   └── index.html # Final rendered scoreboard (GitHub Pages)
├── infra
│   ├── locals.tf
│   ├── main.tf
│   ├── provider.tf
│   ├── terraform.tfvars
│   ├── user_data.tpl # EC2 bootstrap script
│   └── variables.tf
├── LICENSE
├── README.md # You're here!
└── src
    ├── api.py # Scraper/API layer for match results
    ├── bot.py # Main Telegram bot logic
    ├── config.py # Environment config and user list
    ├── requirements.txt
    └── utils.py # Betting and scoring logic
```


---

## 🚀 Infrastructure Overview

- **AWS EC2 (auto-scaled):**
  - Instances are launched via **Terraform** with a startup script (`user_data.tpl`) that:
    - Installs Python dependencies
    - Clones the repository
    - Runs the Telegram bot from the `src/` folder

- **Auto-scaling logic:**
  - Although designed for single-instance usage (per betting round), the EC2 configuration is ready for scaling horizontally.
  - A new instance is launched each week when a user triggers `/reiniciar`, and the previous instance is terminated.

- **Persistent State:**
  - Bets are stored **locally on the EC2 instance** in simple files or serialized structures (e.g., JSON).

- **GitHub Pages + Bulma CSS:**
  - When all users have submitted their bets, the bot renders an HTML scoreboard (`html/index.html`) styled with **Bulma**.
  - A **GitHub Action** commits and pushes the updated page to the `gh-pages` branch, making it publicly accessible.

---

## 🤖 Telegram Bot Functionality

### Commands Overview

| Command         | Description |
|----------------|-------------|
| `/hola`         | Sends the Telegram user ID in a private message. |
| `/nueva_jornada`| Starts a new betting round, assigning responsibility to the caller. |
| `/nueva_apuesta`| Lets users submit their predictions for the week. |
| `/puntuaciones` | Displays current user scores based on real match results. |
| `/reiniciar`    | Terminates the EC2 instance after confirmation. |

### User Restrictions

- Only users **in the allowed Telegram ID list** can interact with the bot.
- This list is stored in a Terraform-provisioned **environment variable**, making it secure and immutable per deployment.
- The `/hola` command is **publicly accessible** and sends a private message with the user’s Telegram ID. The admin can then add this ID to the list and redeploy.

---

## 👥 User Manual

### 1. **Get Your Telegram ID**
Any user wanting to join must send `/hola` to the bot. The bot replies in a private message with their Telegram ID. The admin adds this to the infrastructure config and redeploys.

### 2. **Starting a Betting Round**
A user sends `/nueva_jornada` to the bot. This:
- Assigns them as **responsible for the current round**.
- Prevents anyone else from starting a new round until the current one is finished.
- Retrieves the **match list** for the round and sends it to the responsible user, who must copy it to the group.

### 3. **Submitting Bets**
Each user submits their prediction via `/nueva_apuesta`, using the provided format. The bot:
- Verifies the user is authorized.
- Checks the round has been started.
- Ensures no user can send more than one prediction.

### 4. **Tracking Scores**
At any time, anyone can use `/puntuaciones` to:
- View the number of points each user has earned.
- Scoring is based on real match outcomes (retrieved automatically).
- The scoring logic is private and customizable in `utils.py`.

### 5. **Rendering the Scoreboard**
Once all users (typically 6) have submitted their bets, the bot:
- Computes potential outcomes and their impacts.
- Renders an HTML table (`index.html`) using **Bulma CSS**, with color codes showing how good each prediction is.
- Pushes the result to GitHub Pages via a **GitHub Action**.

### 6. **Restarting the Week**
To begin a new week:
- The current week’s responsible user sends `/reiniciar`.
- The bot asks for confirmation.
- Once confirmed, a GitHub Action triggers **termination of the EC2 instance** via AWS CLI or API.

---

## ✅ Example Output (HTML)

The final HTML scoreboard shows:

- Rows = Users
- Columns = Matches
- Cells = Predicted outcomes
- Cell colors = Reflect correctness or closeness to actual result

[Live Site](https://andresmarinabad.github.io/quiniela_quinigol_bot/)

---

## 🌐 Deployment Workflow

1. Add new user IDs to `terraform.tfvars` or `variables.tf`.
2. Run `terraform apply` in the `infra/` folder.
3. Terraform:
   - Provisions EC2 instance
   - Injects allowed user IDs as environment variable
   - Deploys bot via `user_data.tpl`

4. EC2 startup:
   - Installs Python & pip packages
   - Clones repo and launches `src/bot.py`

---

## 🔐 Security Notes

- Only known Telegram user IDs can send bets.
- The `/hola` command is public but only returns private info (ID) via DM.
- Terraform-managed environment variables make user control safe and reproducible.
- Bets are **not stored externally**; future versions may support S3 or RDS for persistence.

---

## 🛠 Tech Stack

- **Python 3**
- **Python Telegram Bot**
- **AWS EC2** with user data bootstrap
- **Terraform** for full infra-as-code
- **GitHub Actions** for rendering and termination
- **Bulma CSS** for clean UI

---

## 🔄 GitHub Actions

Two main workflows:

1. **Render HTML Table** – triggered after all users have submitted predictions.
2. **Terminate EC2** – triggered via `/reiniciar` confirmation, using GitHub token to trigger AWS shutdown.

---

## ⚠️ Limitations & Roadmap

- State is not persistent across EC2 restarts — betting data is stored locally.
- No admin dashboard yet — everything is command-line via bot.
- Security can be improved with secrets management (e.g., AWS SSM).

---

## 📄 License

MIT License – See [LICENSE](LICENSE)

---

## 🙋 Questions or Contributions?

This bot was made for a close-knit group, but the code is open and adaptable. Feel free to fork, suggest changes, or expand it for your league, pool, or club!
