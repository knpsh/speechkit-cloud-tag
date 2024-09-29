# Create service account for bucket
resource "yandex_iam_service_account" "sa" {
  folder_id       = var.folder_id
  name            = "stt-sa-${random_string.suffix.result}"
  description     = "stt-sa-${random_string.suffix.result}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa-stt-user" {
  folder_id       = var.folder_id
  member          = "serviceAccount:${yandex_iam_service_account.sa.id}"
  role            = "ai.speechkit-stt.user"
}

resource "yandex_resourcemanager_folder_iam_member" "sa-storage-editor" {
  folder_id       = var.folder_id
  member          = "serviceAccount:${yandex_iam_service_account.sa.id}"
  role            = "storage.editor"
}

# Create service account for function trigger
resource "yandex_iam_service_account" "sa-invoker" {
  folder_id       = var.folder_id
  name            = "stt-sa-invoker-${random_string.suffix.result}"
  description     = "stt-sa-invoker-${random_string.suffix.result}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa-invoker" {
  folder_id       = var.folder_id
  member          = "serviceAccount:${yandex_iam_service_account.sa-invoker.id}"
  role            = "functions.functionInvoker"
}

# Static access key
resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.sa.id
  description        = "stt-${random_string.suffix.result} static key"
}

# API key
resource "yandex_iam_service_account_api_key" "sa-api-key" {
  service_account_id = yandex_iam_service_account.sa.id
  description        = "stt-${random_string.suffix.result} API key"
}