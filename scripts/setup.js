#!/usr/bin/env node

/**
 * Script de setup do projeto Sítio Multitrem
 * Verifica dependências e configura o ambiente
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🌿 Sítio Multitrem - Setup');
console.log('==========================\n');

// Verificar Node.js
console.log('Verificando Node.js... ');
try {
  const nodeVersion = execSync('node -v', { encoding: 'utf-8' }).trim();
  console.log(`✓ ${nodeVersion}\n`);
} catch (error) {
  console.error('✗ Node.js não encontrado. Instale Node.js 18+\n');
  process.exit(1);
}

// Verificar npm
console.log('Verificando npm... ');
try {
  const npmVersion = execSync('npm -v', { encoding: 'utf-8' }).trim();
  console.log(`✓ ${npmVersion}\n`);
} catch (error) {
  console.error('✗ npm não encontrado\n');
  process.exit(1);
}

// Verificar PostgreSQL
console.log('Verificando PostgreSQL... ');
try {
  execSync('psql --version', { stdio: 'ignore' });
  console.log('✓ PostgreSQL encontrado\n');
} catch (error) {
  console.log('⚠ PostgreSQL não encontrado. Você precisará instalá-lo.\n');
}

// Verificar Redis
console.log('Verificando Redis... ');
try {
  execSync('redis-cli --version', { stdio: 'ignore' });
  console.log('✓ Redis encontrado\n');
} catch (error) {
  console.log('⚠ Redis não encontrado. Você precisará instalá-lo.\n');
}

// Instalar dependências
console.log('📦 Instalando dependências...\n');
try {
  execSync('npm install', { stdio: 'inherit' });
} catch (error) {
  console.error('Erro ao instalar dependências\n');
  process.exit(1);
}

// Build shared package
console.log('\n🔨 Construindo shared package...\n');
try {
  process.chdir('shared');
  execSync('npm install', { stdio: 'inherit' });
  execSync('npm run build', { stdio: 'inherit' });
  process.chdir('..');
} catch (error) {
  console.error('Erro ao construir shared package\n');
  process.exit(1);
}

// Copiar arquivos .env.example
console.log('\n📋 Copiando arquivos .env.example...\n');
const services = [
  'product-service',
  'cart-service',
  'order-service',
  'payment-service',
  'auth-service',
  'whatsapp-service',
  'ai-service',
  'gateway',
];

services.forEach((service) => {
  const envExample = path.join('services', service, '.env.example');
  const envFile = path.join('services', service, '.env');

  if (fs.existsSync(envExample) && !fs.existsSync(envFile)) {
    fs.copyFileSync(envExample, envFile);
    console.log(`  ✓ Criado ${envFile}`);
  }
});

// Copiar .env.example do frontend
const frontendEnvExample = path.join('frontend', '.env.example');
const frontendEnv = path.join('frontend', '.env');

if (fs.existsSync(frontendEnvExample) && !fs.existsSync(frontendEnv)) {
  fs.copyFileSync(frontendEnvExample, frontendEnv);
  console.log(`  ✓ Criado ${frontendEnv}`);
}

console.log('\n✓ Setup concluído!\n');
console.log('Próximos passos:');
console.log('1. Configure as variáveis de ambiente nos arquivos .env');
console.log('2. Inicie PostgreSQL e Redis');
console.log('3. Execute: npm run dev\n');

