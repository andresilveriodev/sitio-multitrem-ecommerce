'use client'

import { Leaf, Egg, Carrot, ArrowDown } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui'
import { Badge } from '@/components/ui'
import styles from './Hero.module.css'

export function Hero() {
  const scrollToProducts = () => {
    const produtosSection = document.getElementById('produtos')
    produtosSection?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className={styles.hero}>
      {/* Elementos decorativos */}
      <div className={styles.hero__decorations}>
        <Leaf className={`${styles.hero__decoration} ${styles['hero__decoration--1']}`} />
        <Egg className={`${styles.hero__decoration} ${styles['hero__decoration--2']}`} />
        <Carrot className={`${styles.hero__decoration} ${styles['hero__decoration--3']}`} />
        <Leaf className={`${styles.hero__decoration} ${styles['hero__decoration--4']}`} />
      </div>

      {/* Conteúdo */}
      <div className={styles.hero__container}>
        <div className={styles.hero__content}>
          {/* Badge */}
          <div className={styles.hero__badge}>
            <Badge variant="organic" size="md">
              🌿 Direto do Produtor
            </Badge>
          </div>

          {/* Título */}
          <h1 className={styles.hero__title}>Sítio Multitrem</h1>

          {/* Subtítulo */}
          <p className={styles.hero__subtitle}>
            Hortaliças frescas e ovos caipiras, colhidos no dia para sua mesa
          </p>

          {/* Descrição */}
          <p className={styles.hero__description}>
            Produção familiar em Terezópolis de Goiás, com todo carinho e qualidade que sua
            família merece.
          </p>

          {/* CTAs */}
          <div className={styles.hero__ctas}>
            <Button
              variant="primary"
              size="lg"
              onClick={scrollToProducts}
              rightIcon={<ArrowDown className="h-5 w-5" />}
              className={styles.hero__cta}
            >
              Ver Produtos
            </Button>
            <Link href="https://wa.me/5562981225993" target="_blank" rel="noopener noreferrer" className={styles.hero__cta}>
              <Button variant="outline" size="lg" className="w-full">
                Fale Conosco
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className={styles.hero__scroll_indicator}>
        <ArrowDown className={styles.hero__scroll_indicator_icon} />
      </div>
    </section>
  )
}

