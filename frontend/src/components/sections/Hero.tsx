'use client'

import { Leaf, Egg, Carrot, ArrowDown } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui'
import { Badge } from '@/components/ui'

export function Hero() {
  const scrollToProducts = () => {
    const produtosSection = document.getElementById('produtos')
    produtosSection?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary-50 via-primary-100 to-secondary-50">
      {/* Elementos decorativos */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <Leaf className="absolute top-20 left-10 text-primary-200/30 h-24 w-24 animate-pulse" />
        <Egg className="absolute top-40 right-20 text-secondary-200/30 h-16 w-16 animate-pulse delay-300" />
        <Carrot className="absolute bottom-20 left-1/4 text-accent-200/30 h-20 w-20 animate-pulse delay-700" />
        <Leaf className="absolute bottom-40 right-1/4 text-primary-200/30 h-28 w-28 animate-pulse delay-1000" />
      </div>

      {/* Conteúdo */}
      <div className="container-custom relative z-10">
        <div className="max-w-3xl mx-auto text-center space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-700">
          {/* Badge */}
          <div className="flex justify-center">
            <Badge variant="success" size="md" className="text-sm">
              🌿 Direto do Produtor
            </Badge>
          </div>

          {/* Título */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-foreground leading-tight">
            Sítio Multitrem
          </h1>

          {/* Subtítulo */}
          <p className="text-xl sm:text-2xl text-foreground/80 font-medium">
            Hortaliças frescas e ovos caipiras, colhidos no dia para sua mesa
          </p>

          {/* Descrição */}
          <p className="text-base sm:text-lg text-foreground/70 max-w-2xl mx-auto">
            Produção familiar em Abadiânia-GO, com todo carinho e qualidade que
            sua família merece.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Button
              variant="primary"
              size="lg"
              onClick={scrollToProducts}
              rightIcon={<ArrowDown className="h-5 w-5" />}
              className="w-full sm:w-auto"
            >
              Ver Produtos
            </Button>
            <Link
              href="https://wa.me/5562981225993"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto"
            >
              <Button variant="outline" size="lg" className="w-full">
                Fale Conosco
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <ArrowDown className="h-6 w-6 text-foreground/40" />
      </div>
    </section>
  )
}

