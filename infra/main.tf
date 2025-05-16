
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "generated_key" {
  key_name   = "${local.default_tags.Project}-key"
  public_key = tls_private_key.ssh_key.public_key_openssh

  tags = {
    Name = "${local.default_tags.Project}-key"
  }
}

resource "local_file" "private_key" {
  content         = tls_private_key.ssh_key.private_key_pem
  filename        = "${path.module}/${local.default_tags.Project}-key.pem"
  file_permission = "0400"
}

data "template_file" "init" {
  template = file("${path.module}/user_data.tpl")

  vars = {
    telegram_bot_token = var.telegram_bot_token
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical (propietario oficial de Ubuntu)
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

resource "aws_launch_template" "telegram_bot_tpl" {
  name_prefix   = "${local.default_tags.Project}-launch-template"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  key_name      = aws_key_pair.generated_key.key_name
  user_data     = base64encode(data.template_file.init.rendered)

  vpc_security_group_ids = [aws_security_group.telegram_bot_sg.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_instance_profile.name
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${local.default_tags.Project}-launch-template"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "telegram_bot_asg" {
  name              = "${local.default_tags.Project}-autoscaling-group"
  max_size          = 1
  min_size          = 1
  desired_capacity  = 1
  health_check_type = "EC2"
  launch_template {
    id      = aws_launch_template.telegram_bot_tpl.id
    version = "$Latest"
  }

  vpc_zone_identifier = [aws_subnet.public.id]

  tag {
    key                 = "Name"
    value               = "${local.default_tags.Project}-autoscaling-group"
    propagate_at_launch = true
  }

}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "${local.default_tags.Project}-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.default_tags.Project}-public-subnet"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.default_tags.Project}-internet-gateway"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "${local.default_tags.Project}-route-table"
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "telegram_bot_sg" {
  name        = "${local.default_tags.Project}-security-group"
  description = "Allow HTTP"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.default_tags.Project}-security-group"
  }
}

resource "aws_iam_role" "ec2_cloudwatch_role" {
  name = "${local.default_tags.Project}-ec2-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${local.default_tags.Project}-ec2-cloudwatch-role"
  }
}

resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  name = "${local.default_tags.Project}-cloudwatch-logs-policy"
  role = aws_iam_role.ec2_cloudwatch_role.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "${local.default_tags.Project}-ec2-instance-profile"
  role = aws_iam_role.ec2_cloudwatch_role.name

  tags = {
    Name = "${local.default_tags.Project}-ec2-instance-profile"
  }
}