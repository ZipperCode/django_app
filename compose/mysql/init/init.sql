# compose/mysql/init/init.sql
CREATE DATABASE line_upload;
Alter user 'line_upload'@'%' IDENTIFIED WITH mysql_native_password BY '949389';
GRANT ALL PRIVILEGES ON line_upload.* TO 'line_upload'@'%';
FLUSH PRIVILEGES;