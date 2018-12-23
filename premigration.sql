CREATE DATABASE 'utscheduler';
CREATE USER 'ut'@'localhost' WITH mysql_native_password BY 'utp@ss';
ALTER USER 'ut'@'localhost' IDENTIFIED WITH mysql_native_password BY 'utp@ss';
GRANT ALL PRIVILEGES ON utscheduler . * TO 'ut'@'localhost';
