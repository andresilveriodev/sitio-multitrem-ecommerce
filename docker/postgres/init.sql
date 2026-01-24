-- Criar bancos de dados
SELECT 'CREATE DATABASE sitio_multitrem'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sitio_multitrem')\gexec

SELECT 'CREATE DATABASE evolution'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution')\gexec

-- Criar usuários
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sitio_user') THEN
      CREATE USER sitio_user WITH PASSWORD 'sitio_password';
   END IF;
   
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'evolution') THEN
      CREATE USER evolution WITH PASSWORD 'evolution123';
   END IF;
END
$$;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE sitio_multitrem TO sitio_user;
GRANT ALL PRIVILEGES ON DATABASE evolution TO evolution;

-- Extensões úteis
\c sitio_multitrem;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c evolution;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";