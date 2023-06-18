-- # compose/mysql/init/init.sql
CREATE DATABASE line;
Alter user 'telegram'@'%' IDENTIFIED WITH mysql_native_password BY '949389';
GRANT ALL PRIVILEGES ON *.* TO 'telegram'@'%';

FLUSH PRIVILEGES;