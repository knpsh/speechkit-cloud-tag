# Tags bucket
resource "yandex_storage_bucket" "back" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket = "tags-${random_string.suffix.result}"

  website {
    index_document = "index.html"
  }
}

# Website bucket
resource "yandex_storage_bucket" "front" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket = "tags-front-${random_string.suffix.result}"
  acl    = "public-read"

  website {
    index_document = "index.html"
  }

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "yandex_storage_object" "index" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  
  bucket = yandex_storage_bucket.front.bucket
  key    = "index.html"
  source_hash = filemd5("static/index.html.tpl")
  content = templatefile("static/index.html.tpl",
    {
      url = "https://storage.yandexcloud.net/${yandex_storage_bucket.front.bucket}/words.tag1.json",
    }
  )

  depends_on = [
    yandex_iam_service_account_static_access_key.sa-static-key,
    yandex_resourcemanager_folder_iam_member.sa-storage-editor,
  ]
}