# COVID-19 portal: PHP 8.3 + Apache with the mysqli extension
# Normally started by ../compose.yaml together with MySQL.
FROM php:8.3-apache
RUN docker-php-ext-install mysqli
COPY *.php *.css *.js regex_rules.json /var/www/html/
