terraform {
    required_providers {
        aws = {
        source  = "hashicorp/aws"
        version = "~> 5.92"
        }
    }

    required_version = ">= 1.12.0, < 2.0.0"
}

provider "aws" {
    region = "ap-southeast-2"
}

locals {
  application      = "operation-kino"
  artifacts_bucket = "allenmaygibson-artifacts"
}

resource "aws_dynamodb_table" "cinemas" {
    name         = "${local.application}_cinemas"
    billing_mode = "PAY_PER_REQUEST"
    
    hash_key  = "region"
    range_key = "id"

    attribute {
        name = "region"
        type = "S"
    }

    attribute {
        name = "id"
        type = "S"
    }
}

resource "aws_dynamodb_table" "movies" {
    name         = "${local.application}_movies"
    billing_mode = "PAY_PER_REQUEST"
    
    hash_key  = "region"
    range_key = "id"

    attribute {
        name = "region"
        type = "S"
    }

    attribute {
        name = "id"
        type = "S"
    }
}

data "aws_iam_policy_document" "dynamodb_access_policy" {
  statement {
    effect = "Allow"

    resources = [
      aws_dynamodb_table.cinemas.arn,
      aws_dynamodb_table.movies.arn,
    ]

    actions = [
      "dynamodb:Query",
      "dynamodb:BatchWriteItem",
    ]
  }
}

resource "aws_iam_policy" "dynamodb_access" {
  name   = "${local.application}_dynamodb_access"
  policy = data.aws_iam_policy_document.dynamodb_access_policy.json
}

data "aws_iam_policy_document" "lambda_role" {
  statement {
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.application}_lambda_exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "scrape_cinemas" {
  function_name    = "${local.application}_scrape_cinemas"

  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  memory_size      = 256
  timeout          = 30

  s3_bucket        = local.artifacts_bucket
  s3_key           = "${local.application}/scrape_cinemas.zip"

  source_code_hash = filebase64sha256("../build/scrape_cinemas.zip")

  environment {
    variables = {
      SCRAPE_HOST_NZ = var.scrape_host_nz
      SCRAPE_HOST_AU = var.scrape_host_au
    }
  }
}

resource "aws_lambda_function" "scrape_sessions" {
  function_name    = "${local.application}_scrape_sessions"

  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  memory_size      = 512
  timeout          = 60

  s3_bucket        = local.artifacts_bucket
  s3_key           = "${local.application}/scrape_sessions.zip"

  source_code_hash = filebase64sha256("../build/scrape_sessions.zip")

  environment {
    variables = {
      SCRAPE_HOST_NZ = var.scrape_host_nz
      SCRAPE_HOST_AU = var.scrape_host_au
    }
  }
}

resource "aws_lambda_function" "get_sessions" {
  function_name    = "${local.application}_get_sessions"

  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  memory_size      = 128
  timeout          = 15

  s3_bucket        = local.artifacts_bucket
  s3_key           = "${local.application}/get_sessions.zip"

  source_code_hash = filebase64sha256("../build/get_sessions.zip")
}
