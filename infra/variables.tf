variable "telegram_bot_token" {
  type        = string
  description = "Telegram Bot token"
}

variable "users" {
  type = string
  description = "Users list"
}

variable "admin" {
  type = string
  description = "Admin Telegram ID"
}

variable "github_token" {
  type = string
  description = "Github token repo workflow"
}

variable "repo" {
  type = string
  description = "username/repo"
}

variable "workflow" {
  type = string
  description = "workflow.yml"
}
