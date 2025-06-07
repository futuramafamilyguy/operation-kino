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

resource "aws_dynamodb_table" "cinemas" {
    name         = "operationkino_cinemas"
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
    name         = "operationkino_movies"
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
