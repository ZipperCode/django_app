# compose/mysql/init/init.sql
CREATE DATABASE line;
Alter user 'line'@'%' IDENTIFIED WITH mysql_native_password BY '949389';
GRANT ALL PRIVILEGES ON line.* TO 'line'@'%';
FLUSH PRIVILEGES;