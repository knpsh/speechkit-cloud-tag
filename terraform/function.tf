# Various
data "archive_file" "stt" {
  type        = "zip"
  source_dir  = "${path.module}/functions/stt"
  output_path = "${path.module}/function-stt.zip"
}

data "archive_file" "check" {
  type        = "zip"
  source_dir  = "${path.module}/functions/check"
  output_path = "${path.module}/function-check.zip"
}

data "archive_file" "sum" {
  type        = "zip"
  source_dir  = "${path.module}/functions/sum"
  output_path = "${path.module}/function-sum.zip"
}

# STT
resource "yandex_function" "stt" {
  folder_id          = var.folder_id
  name               = "tags-stt-${random_string.suffix.result}"
  runtime            = "python38"
  entrypoint         = "main.handler"
  memory             = "256"
  execution_timeout  = "300"
  service_account_id = yandex_iam_service_account.sa.id

  environment = {
    S3_BUCKET       = yandex_storage_bucket.back.id
    S3_PREFIX       = var.s3_prefix_input
    S3_PREFIX_LOG   = var.s3_prefix_log
    S3_PREFIX_OUT   = var.s3_prefix_out
    S3_KEY          = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    S3_SECRET       = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
    API_SECRET      = yandex_iam_service_account_api_key.sa-api-key.secret_key
  }

  user_hash = data.archive_file.stt.output_base64sha256
  content {
    zip_filename = data.archive_file.stt.output_path
  }
}

# Checker
resource "yandex_function" "check" {
  folder_id          = var.folder_id
  name               = "tags-check-${random_string.suffix.result}"
  runtime            = "python38"
  entrypoint         = "main.handler"
  memory             = "128"
  execution_timeout  = "300"
  service_account_id = yandex_iam_service_account.sa.id

  environment = {
    S3_BUCKET     = yandex_storage_bucket.back.id
    S3_PREFIX     = var.s3_prefix_input
    S3_PREFIX_LOG = var.s3_prefix_log
    S3_PREFIX_OUT = var.s3_prefix_out
    S3_KEY        = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    S3_SECRET     = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
    API_SECRET    = yandex_iam_service_account_api_key.sa-api-key.secret_key
  }

  user_hash = data.archive_file.check.output_base64sha256
  content {
    zip_filename = data.archive_file.check.output_path
  }
}

resource "yandex_function_trigger" "cron" {
  name        = "check-cron-${random_string.suffix.result}"
  description = "check-cron-${random_string.suffix.result}"
  timer {
    cron_expression = "* * * * ? *"
  }
  function {
    id = yandex_function.check.id
    service_account_id = yandex_iam_service_account.sa-invoker.id
  }
}

# Summarizer trigger
resource "yandex_function" "sum" {
  folder_id          = var.folder_id
  name               = "tags-sum-${random_string.suffix.result}"
  runtime            = "python38"
  entrypoint         = "main.handler"
  memory             = "256"
  execution_timeout  = "300"
  service_account_id = yandex_iam_service_account.sa.id

  environment = {
    S3_BUCKET       = yandex_storage_bucket.back.id
    S3_BUCKET_FRONT = yandex_storage_bucket.front.id
    S3_PREFIX_OUT   = var.s3_prefix_out
    S3_KEY          = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    S3_SECRET       = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  }

  user_hash = data.archive_file.sum.output_base64sha256
  content {
    zip_filename = data.archive_file.sum.output_path
  }
}

resource "yandex_function_trigger" "sum-s3" {
  name        = "sum-s3-${random_string.suffix.result}"
  description = "sum-s3-${random_string.suffix.result}"
  
  object_storage {
    bucket_id = yandex_storage_bucket.back.id
    prefix    = var.s3_prefix_out
    create    = true
    batch_cutoff = 1
  }

  function {
    id = yandex_function.sum.id
    service_account_id = yandex_iam_service_account.sa-invoker.id
  }
}

# API Gateway
resource "yandex_api_gateway" "gw" {
  name = "stt-${random_string.suffix.result}"
  spec = <<-EOT
    openapi: 3.0.0
    info:
      title: Terraform Cost Estimation API
      version: 1.0.0

    paths:
      /:
        post:
          x-yc-apigateway-integration:
            payload_format_version: '1.0'
            function_id: ${yandex_function.stt.id}
            tag: $latest
            type: cloud_functions
            service_account_id: ${yandex_iam_service_account.sa-invoker.id}
  EOT
}