import { Calendar, Clock, MapPin, Truck } from 'lucide-react'
import Link from 'next/link'
import { Card, Button } from '@/components/ui'

export function Delivery() {
  return (
    <section
      id="entregas"
      className="py-20 sm:py-24 md:py-32 bg-gray-50"
    >
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Coluna 1 - Informações */}
          <div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-3 sm:mb-4 leading-tight">
              Entregas
            </h2>
            <p className="text-lg sm:text-xl text-gray-700 mb-6 sm:mb-8 leading-relaxed">
              Fresquinho na sua porta
            </p>

            <div className="space-y-4 sm:space-y-6">
              {/* Card Dias */}
              <Card variant="elevated" className="p-5 sm:p-6">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3 sm:p-4 flex-shrink-0">
                    <Calendar className="h-6 w-6 sm:h-7 sm:w-7 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2 text-base sm:text-lg">Dias</h3>
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
                      Quarta, Quinta, Sexta e Sábado
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Horário */}
              <Card variant="elevated" className="p-5 sm:p-6">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3 sm:p-4 flex-shrink-0">
                    <Clock className="h-6 w-6 sm:h-7 sm:w-7 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2 text-base sm:text-lg">
                      Horário
                    </h3>
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
                      Período da manhã (8h às 12h)
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Região */}
              <Card variant="elevated" className="p-5 sm:p-6">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3 sm:p-4 flex-shrink-0">
                    <MapPin className="h-6 w-6 sm:h-7 sm:w-7 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2 text-base sm:text-lg">
                      Região
                    </h3>
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
                      Terezópolis de Goiás e região
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Frete */}
              <Card variant="elevated" className="p-5 sm:p-6">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3 sm:p-4 flex-shrink-0">
                    <Truck className="h-6 w-6 sm:h-7 sm:w-7 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2 text-base sm:text-lg">
                      Frete
                    </h3>
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
                      Consulte disponibilidade
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Coluna 2 - Destaque */}
          <div className="flex items-center">
            <Card variant="bordered" className="p-6 sm:p-8 md:p-10 text-center w-full">
              <div className="mb-6 sm:mb-8 flex justify-center">
                <div className="rounded-full bg-primary-100 p-6 sm:p-8">
                  <Truck className="h-12 w-12 sm:h-14 sm:w-14 text-primary-600" />
                </div>
              </div>
              <h3 className="text-2xl sm:text-3xl font-bold text-foreground mb-4 sm:mb-6 leading-tight">
                Entrega no mesmo dia!
              </h3>
              <p className="text-base sm:text-lg text-gray-700 mb-6 sm:mb-8 leading-relaxed">
                Pedidos feitos até 18h do dia anterior são entregues no próximo
                dia disponível pela manhã.
              </p>
              <Link
                href="https://wa.me/5562981225993?text=Olá! Gostaria de consultar se fazem entrega na minha região."
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block"
              >
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full sm:w-auto"
                >
                  Consultar minha região
                </Button>
              </Link>
            </Card>
          </div>
        </div>

        {/* Nota de rodapé */}
        <div className="mt-8 sm:mt-10 text-center">
          <p className="text-sm sm:text-base text-gray-600">
            * Disponibilidade sujeita à região. Entre em contato para confirmar.
          </p>
        </div>
      </div>
    </section>
  )
}

