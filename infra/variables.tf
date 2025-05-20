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

variable "terminate_action" {
  type = string
  description = "Terminate EC2 instance"
}

variable "render_action" {
  type = string
  description = "Render HTML action"
}
