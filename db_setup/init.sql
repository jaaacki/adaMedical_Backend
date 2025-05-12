-- Ensure MySQL is using the native password authentication for the user
ALTER USER 'user'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
FLUSH PRIVILEGES;

-- Add any other initialization SQL here if needed