# Imagens dos Produtos

## 📁 Estrutura de Pastas

Coloque as fotos dos produtos nesta pasta: `frontend/public/images/products/`

## 📝 Como Usar

### 1. Nomeie os arquivos de forma organizada:
- Use o slug do produto como nome do arquivo
- Exemplo: `alface-americana.jpg`, `alface-crespa.jpg`, `ovos-12-unidades.jpg`

### 2. Formatos recomendados:
- **JPG/JPEG**: Para fotos com muitas cores
- **PNG**: Para imagens com transparência
- **WebP**: Formato moderno e otimizado (recomendado)

### 3. Tamanho recomendado:
- **Largura**: 800px a 1200px
- **Proporção**: 1:1 (quadrado) para melhor visualização nos cards
- **Peso**: Máximo 500KB por imagem

## 🔗 Como Referenciar no Código

No Next.js, arquivos na pasta `public` são servidos diretamente na raiz do site.

### Exemplo de URL:
```
/imagens/produtos/alface-americana.jpg
```

### No código do produto:
```typescript
{
  id: 1,
  name: 'Alface Americana',
  imageUrl: '/images/products/alface-americana.jpg',
  // ...
}
```

## 📋 Checklist

- [ ] Imagens nomeadas com o slug do produto
- [ ] Formato otimizado (WebP ou JPG)
- [ ] Tamanho adequado (800-1200px, máximo 500KB)
- [ ] Proporção 1:1 (quadrado)
- [ ] URLs atualizadas no banco de dados ou mock-data

## 🎨 Dicas

- Use ferramentas como [TinyPNG](https://tinypng.com/) ou [Squoosh](https://squoosh.app/) para otimizar as imagens
- Mantenha nomes de arquivos em minúsculas e com hífens
- Evite espaços e caracteres especiais nos nomes dos arquivos
