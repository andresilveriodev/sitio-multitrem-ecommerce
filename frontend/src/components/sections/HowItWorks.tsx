import { ShoppingBag, Package, Calendar, Truck } from 'lucide-react'
import { Card } from '@/components/ui'

const steps = [
  {
    number: '01',
    icon: ShoppingBag,
    title: 'Escolha seus produtos',
    description:
      'Navegue pelo nosso catálogo de hortaliças frescas, ovos caipiras e kits especiais',
  },
  {
    number: '02',
    icon: Package,
    title: 'Monte seu pedido',
    description:
      'Adicione ao carrinho e personalize seus kits escolhendo as hortaliças que preferir',
  },
  {
    number: '03',
    icon: Calendar,
    title: 'Agende a entrega',
    description:
      'Escolha o melhor dia (quarta a sábado) para receber tudo fresquinho pela manhã',
  },
  {
    number: '04',
    icon: Truck,
    title: 'Receba em casa',
    description:
      'Produtos colhidos no dia, entregues diretamente do sítio para sua mesa',
  },
]

export function HowItWorks() {
  return (
    <section
      id="como-funciona"
      className="py-16 sm:py-20 md:py-24 bg-background"
    >
      <div className="container-custom">
        {/* Header */}
        <div className="text-center mb-12 md:mb-16">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4">
            Como Funciona
          </h2>
          <p className="text-lg sm:text-xl text-foreground/70 max-w-2xl mx-auto">
            Receba produtos frescos em 4 passos simples
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <div key={step.number} className="relative">
                {/* Linha conectora (desktop) */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-primary-200 -z-10" />
                )}

                <Card
                  variant="elevated"
                  className="h-full text-center relative overflow-hidden group hover:shadow-xl transition-shadow"
                >
                  {/* Número de fundo */}
                  <div className="absolute -top-4 -right-4 text-8xl font-bold text-primary-50 group-hover:text-primary-100 transition-colors">
                    {step.number}
                  </div>

                  {/* Conteúdo */}
                  <div className="relative z-10 pt-8 pb-6">
                    {/* Ícone */}
                    <div className="flex justify-center mb-4">
                      <div className="rounded-full bg-primary-100 p-4 group-hover:bg-primary-200 transition-colors">
                        <Icon className="h-8 w-8 text-primary-600" />
                      </div>
                    </div>

                    {/* Título */}
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      {step.title}
                    </h3>

                    {/* Descrição */}
                    <p className="text-sm text-foreground/70 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </Card>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

