# Guia de Instalação e Configuração do PostgreSQL

Este guia mostra como instalar e configurar o PostgreSQL para o sistema Sítio Multitrem.

## 📥 Passo 1: Download e Instalação

### Opção 1: Instalador Oficial (Recomendado)

1. **Acesse o site oficial:**
   - https://www.postgresql.org/download/windows/
   - Ou diretamente: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

2. **Baixe a versão mais recente:**
   - Recomendado: PostgreSQL 15 ou 16
   - Escolha o instalador para Windows (x86-64)

3. **Execute o instalador:**
   - Clique duas vezes no arquivo `.exe` baixado
   - Siga o assistente de instalação

4. **Durante a instalação:**
   - **Porta:** Mantenha `5432` (padrão)
   - **Localização:** Escolha o diretório padrão ou personalizado
   - **Componentes:** Instale todos (PostgreSQL Server, pgAdmin 4, Command Line Tools, Stack Builder)
   - **Data Directory:** Mantenha o padrão

5. **Configure a senha do superusuário:**
   - **Usuário:** `postgres` (padrão)
   - **Senha:** Escolha uma senha segura (anote para usar nos `.env`)
   - ⚠️ **IMPORTANTE:** Anote esta senha! Você precisará dela.

6. **Finalize a instalação:**
   - Aguarde a conclusão
   - Marque a opção para abrir o Stack Builder (opcional)

---

## 🔧 Passo 2: Verificar Instalação

### Verificar se o PostgreSQL está rodando:

1. **Abra o PowerShell como Administrador**

2. **Verifique o serviço:**
```powershell
Get-Service -Name "*postgresql*"
```

3. **Se o serviço não estiver rodando, inicie:**
```powershell
Start-Service postgresql-x64-15  # Substitua pela versão instalada
```

4. **Verifique a versão:**
```powershell
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" --version
```

---

## 🗄️ Passo 3: Criar o Banco de Dados

### Método 1: Usando pgAdmin 4 (Interface Gráfica)

1. **Abra o pgAdmin 4:**
   - Procure "pgAdmin 4" no menu Iniciar
   - Ou acesse: http://localhost/pgadmin4

2. **Conecte ao servidor:**
   - Clique com botão direito em "Servers" → "Create" → "Server"
   - **General Tab:**
     - Name: `PostgreSQL 15` (ou sua versão)
   - **Connection Tab:**
     - Host: `localhost`
     - Port: `5432`
     - Username: `postgres`
     - Password: (a senha que você definiu)
   - Clique em "Save"

3. **Crie o banco de dados:**
   - Expanda o servidor → Clique com botão direito em "Databases"
   - Selecione "Create" → "Database"
   - **Database name:** `sitio_multitrem`
   - Clique em "Save"

### Método 2: Usando Command Line (PowerShell)

1. **Abra o PowerShell**

2. **Conecte ao PostgreSQL:**
```powershell
# Ajuste o caminho conforme sua versão instalada
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres
```

3. **Digite a senha quando solicitado**

4. **Crie o banco de dados:**
```sql
CREATE DATABASE sitio_multitrem;
```

5. **Verifique se foi criado:**
```sql
\l
```

6. **Saia do psql:**
```sql
\q
```

### Método 3: Script Automatizado (PowerShell)

Execute este script no PowerShell:

```powershell
# Configurações
$pgVersion = "15"  # Ajuste conforme sua versão
$pgPath = "C:\Program Files\PostgreSQL\$pgVersion\bin"
$dbName = "sitio_multitrem"
$dbUser = "postgres"

# Caminho completo do psql
$psqlPath = Join-Path $pgPath "psql.exe"

# Verificar se psql existe
if (-not (Test-Path $psqlPath)) {
    Write-Host "PostgreSQL não encontrado em: $psqlPath" -ForegroundColor Red
    Write-Host "Ajuste a variável `$pgVersion ou `$pgPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Criando banco de dados '$dbName'..." -ForegroundColor Yellow

# Criar banco de dados
$env:PGPASSWORD = Read-Host "Digite a senha do PostgreSQL" -AsSecureString | ConvertFrom-SecureString -AsPlainText
& $psqlPath -U $dbUser -c "CREATE DATABASE $dbName;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Banco de dados '$dbName' criado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "✗ Erro ao criar banco de dados. Pode já existir." -ForegroundColor Red
    Write-Host "Verificando se o banco já existe..." -ForegroundColor Yellow
    & $psqlPath -U $dbUser -lqt | Select-String $dbName
}
```

---

## ⚙️ Passo 4: Configurar Variáveis de Ambiente

### Atualizar os arquivos `.env` dos serviços:

Os arquivos `.env` já foram criados, mas você precisa atualizar a senha do PostgreSQL:

#### Product Service (`services/product-service/.env`):
```env
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=SUA_SENHA_AQUI  # ← Altere aqui
DB_NAME=sitio_multitrem
```

#### Order Service (`services/order-service/.env`):
```env
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=SUA_SENHA_AQUI  # ← Altere aqui
DB_DATABASE=sitio_multitrem
```

#### Payment Service (`services/payment-service/.env`):
```env
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=SUA_SENHA_AQUI  # ← Altere aqui
DB_DATABASE=sitio_multitrem
```

---

## ✅ Passo 5: Testar Conexão

### Teste usando Node.js:

Crie um arquivo de teste `test-db-connection.js`:

```javascript
const { Client } = require('pg');

const client = new Client({
  host: 'localhost',
  port: 5432,
  user: 'postgres',
  password: 'SUA_SENHA_AQUI', // ← Altere aqui
  database: 'sitio_multitrem',
});

async function testConnection() {
  try {
    await client.connect();
    console.log('✅ Conexão com PostgreSQL estabelecida!');
    
    const result = await client.query('SELECT version()');
    console.log('Versão do PostgreSQL:', result.rows[0].version);
    
    await client.end();
    console.log('✅ Teste concluído com sucesso!');
  } catch (error) {
    console.error('❌ Erro ao conectar:', error.message);
  }
}

testConnection();
```

Execute:
```powershell
node test-db-connection.js
```

### Teste usando PowerShell:

```powershell
# Ajuste o caminho conforme sua versão
$pgPath = "C:\Program Files\PostgreSQL\15\bin"
$psqlPath = Join-Path $pgPath "psql.exe"

# Teste de conexão
& $psqlPath -U postgres -d sitio_multitrem -c "SELECT version();"
```

---

## 🚀 Passo 6: Iniciar os Serviços

Após configurar o PostgreSQL, inicie os serviços:

```powershell
# Product Service
cd services\product-service
npm run start:dev

# Order Service (em outro terminal)
cd services\order-service
npm run start:dev

# Payment Service (em outro terminal)
cd services\payment-service
npm run start:dev
```

Os serviços irão:
- Conectar automaticamente ao banco
- Criar as tabelas automaticamente (em modo desenvolvimento)
- Product Service executará o seed de produtos automaticamente

---

## 🔍 Solução de Problemas

### Erro: "password authentication failed"
- Verifique se a senha no `.env` está correta
- Tente redefinir a senha do usuário `postgres`

### Erro: "database does not exist"
- Certifique-se de que criou o banco `sitio_multitrem`
- Verifique o nome do banco nos arquivos `.env`

### Erro: "connection refused"
- Verifique se o serviço PostgreSQL está rodando:
```powershell
Get-Service -Name "*postgresql*"
Start-Service postgresql-x64-15  # Se não estiver rodando
```

### Erro: "port 5432 is already in use"
- Outro processo pode estar usando a porta
- Verifique com: `netstat -ano | findstr :5432`

### Redefinir senha do PostgreSQL:

1. **Edite o arquivo `pg_hba.conf`:**
   - Localização: `C:\Program Files\PostgreSQL\15\data\pg_hba.conf`
   - Altere a linha de `md5` para `trust` temporariamente:
   ```
   host    all             all             127.0.0.1/32            trust
   ```

2. **Reinicie o serviço PostgreSQL**

3. **Conecte sem senha e altere:**
```sql
ALTER USER postgres WITH PASSWORD 'nova_senha';
```

4. **Reverta o `pg_hba.conf` para `md5`**

5. **Reinicie o serviço novamente**

---

## 📚 Recursos Adicionais

- **Documentação oficial:** https://www.postgresql.org/docs/
- **pgAdmin 4:** Interface gráfica para gerenciar o banco
- **Comandos úteis do psql:**
  - `\l` - Listar bancos de dados
  - `\c nome_banco` - Conectar a um banco
  - `\dt` - Listar tabelas
  - `\q` - Sair

---

## ✅ Checklist Final

- [ ] PostgreSQL instalado
- [ ] Serviço PostgreSQL rodando
- [ ] Banco de dados `sitio_multitrem` criado
- [ ] Senha configurada nos arquivos `.env`
- [ ] Teste de conexão bem-sucedido
- [ ] Serviços iniciando sem erros de conexão

---

**Pronto!** Seu PostgreSQL está configurado e pronto para uso com o sistema Sítio Multitrem! 🎉

