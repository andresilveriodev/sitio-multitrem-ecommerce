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
      className="py-20 sm:py-24 md:py-32 bg-background"
    >
      <div className="container-custom">
        {/* Header */}
        <div className="text-center mb-12 sm:mb-16 md:mb-20">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-3 sm:mb-4 leading-tight">
            Como Funciona
          </h2>

        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 lg:gap-10">
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
                  className="h-full text-center relative overflow-hidden group"
                >
                  {/* Número de fundo */}
                  <div className="absolute -top-6 -right-6 text-7xl sm:text-8xl font-bold text-primary-50 group-hover:text-primary-100 transition-colors opacity-60">
                    {step.number}
                  </div>

                  {/* Conteúdo */}
                  <div className="relative z-10 p-6 sm:p-8">
                    {/* Ícone */}
                    <div className="flex justify-center mb-4 sm:mb-6">
                      <div className="rounded-full bg-primary-100 p-4 sm:p-5 group-hover:bg-primary-200 transition-colors">
                        <Icon className="h-8 w-8 sm:h-10 sm:w-10 text-primary-600" />
                      </div>
                    </div>

                    {/* Título */}
                    <h3 className="text-xl sm:text-2xl font-semibold text-foreground mb-3 sm:mb-4 leading-snug">
                      {step.title}
                    </h3>

                    {/* Descrição */}
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
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

