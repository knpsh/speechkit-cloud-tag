output "fqdn" {
  value = "https://${yandex_storage_bucket.front.bucket}.website.yandexcloud.net"
}

output "api" {
  value = "https://${yandex_api_gateway.gw.domain}"
}