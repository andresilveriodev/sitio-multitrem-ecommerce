const Redis = require('ioredis')

async function testRedis() {
  console.log('🧪 Testando conexão Redis...\n')
  
  const redis = new Redis({
    host: 'localhost',
    port: 6379,
    password: '',
    retryStrategy: (times) => {
      console.log(`⏳ Tentativa de reconexão ${times}...`)
      return Math.min(times * 50, 2000)
    },
  })

  redis.on('connect', () => {
    console.log('✅ Redis: conectado')
  })

  redis.on('ready', async () => {
    console.log('✅ Redis: pronto\n')
    
    try {
      // Teste 1: PING
      console.log('📤 Teste 1: PING')
      const pong = await redis.ping()
      console.log('📥 Resposta:', pong)
      
      // Teste 2: SET/GET
      console.log('\n📤 Teste 2: SET/GET')
      await redis.set('test:key', 'Hello Redis!')
      const value = await redis.get('test:key')
      console.log('📥 Valor recuperado:', value)
      
      // Teste 3: Lista (usado no chat)
      console.log('\n📤 Teste 3: LPUSH/LRANGE')
      await redis.lpush('test:chat', JSON.stringify({ msg: 'Olá!', timestamp: Date.now() }))
      await redis.lpush('test:chat', JSON.stringify({ msg: 'Como está?', timestamp: Date.now() }))
      const messages = await redis.lrange('test:chat', 0, 9)
      console.log('📥 Mensagens:', messages.map(m => JSON.parse(m)))
      
      // Teste 4: Hash (usado para metadata)
      console.log('\n📤 Teste 4: HSET/HGET')
      await redis.hset('test:user', 'name', 'João')
      await redis.hset('test:user', 'phone', '5511999999999')
      const userName = await redis.hget('test:user', 'name')
      const userPhone = await redis.hget('test:user', 'phone')
      console.log('📥 Usuário:', { name: userName, phone: userPhone })
      
      // Teste 5: TTL (expiração)
      console.log('\n📤 Teste 5: EXPIRE/TTL')
      await redis.set('test:temp', 'valor temporário')
      await redis.expire('test:temp', 5)
      const ttl = await redis.ttl('test:temp')
      console.log('📥 TTL restante:', ttl, 'segundos')
      
      // Teste 6: Keys pattern
      console.log('\n📤 Teste 6: KEYS (padrão test:*)')
      const keys = await redis.keys('test:*')
      console.log('📥 Chaves encontradas:', keys)
      
      // Limpar
      console.log('\n🧹 Limpando dados de teste...')
      await redis.del('test:key', 'test:chat', 'test:user', 'test:temp')
      console.log('✅ Limpeza concluída')
      
      console.log('\n🎉 Todos os testes passaram!')
      
      // Informações do servidor
      console.log('\n📊 Informações do Redis:')
      const info = await redis.info('server')
      const versionMatch = info.match(/redis_version:(.+)/)
      if (versionMatch) {
        console.log('   Versão:', versionMatch[1])
      }
      
      redis.disconnect()
      
    } catch (error) {
      console.error('\n❌ Erro nos testes:', error.message)
      redis.disconnect()
      process.exit(1)
    }
  })

  redis.on('error', (error) => {
    console.error('❌ Erro de conexão:', error.message)
    console.log('\n💡 Possíveis causas:')
    console.log('1. Docker não está rodando')
    console.log('2. Container Redis não foi criado')
    console.log('3. Porta 6379 não está exposta no host')
    console.log('\n🔧 Soluções:')
    console.log('1. Inicie o Docker Desktop')
    console.log('2. Execute: cd services/evolution-api && docker-compose up -d')
    console.log('3. Verifique se a porta está exposta: docker ps | Select-String "redis"')
    redis.disconnect()
    process.exit(1)
  })
}

testRedis()



