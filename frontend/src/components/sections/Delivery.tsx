import { Calendar, Clock, MapPin, Truck } from 'lucide-react'
import Link from 'next/link'
import { Card, Button } from '@/components/ui'

export function Delivery() {
  return (
    <section
      id="entregas"
      className="py-16 sm:py-20 md:py-24 bg-primary-50/30"
    >
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Coluna 1 - Informações */}
          <div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4">
              Entregas
            </h2>
            <p className="text-lg sm:text-xl text-foreground/70 mb-8">
              Fresquinho na sua porta
            </p>

            <div className="space-y-4">
              {/* Card Dias */}
              <Card variant="elevated" className="p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3">
                    <Calendar className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">Dias</h3>
                    <p className="text-sm text-foreground/70">
                      Quarta, Quinta, Sexta e Sábado
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Horário */}
              <Card variant="elevated" className="p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3">
                    <Clock className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">
                      Horário
                    </h3>
                    <p className="text-sm text-foreground/70">
                      Período da manhã (8h às 12h)
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Região */}
              <Card variant="elevated" className="p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3">
                    <MapPin className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">
                      Região
                    </h3>
                    <p className="text-sm text-foreground/70">
                      Abadiânia e região
                    </p>
                  </div>
                </div>
              </Card>

              {/* Card Frete */}
              <Card variant="elevated" className="p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-primary-100 p-3">
                    <Truck className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">
                      Frete
                    </h3>
                    <p className="text-sm text-foreground/70">
                      Consulte disponibilidade
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Coluna 2 - Destaque */}
          <div className="flex items-center">
            <Card variant="bordered" className="p-8 text-center w-full">
              <div className="mb-6 flex justify-center">
                <div className="rounded-full bg-primary-100 p-6">
                  <Truck className="h-12 w-12 text-primary-600" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">
                Entrega no mesmo dia!
              </h3>
              <p className="text-foreground/70 mb-6">
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
        <div className="mt-8 text-center">
          <p className="text-sm text-foreground/60">
            * Disponibilidade sujeita à região. Entre em contato para confirmar.
          </p>
        </div>
      </div>
    </section>
  )
}

