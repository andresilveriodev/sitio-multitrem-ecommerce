import { Phone, Instagram, MapPin, Mail } from 'lucide-react'
import Link from 'next/link'
import { Card, Button, Input } from '@/components/ui'

export function Contact() {
  return (
    <>
      <section id="contato" className="py-16 sm:py-20 md:py-24 bg-background">
        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            {/* Coluna 1 - Fale Conosco */}
            <div>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4">
                Fale Conosco
              </h2>
              <p className="text-lg sm:text-xl text-foreground/70 mb-8">
                Estamos prontos para atender você
              </p>

              {/* Card WhatsApp */}
              <Card variant="elevated" className="p-6 mb-4 border-2 border-green-500/20">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-green-100 p-3">
                    <Phone className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-2">
                      WhatsApp
                    </h3>
                    <p className="text-lg font-medium text-foreground mb-2">
                      (62) 98122-5993
                    </p>
                    <p className="text-sm text-foreground/70 mb-4">
                      Atendimento de segunda a sábado, 7h às 18h
                    </p>
                    <Link
                      href="https://wa.me/5562981225993"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Button
                        variant="primary"
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Chamar no WhatsApp
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>

              {/* Card Instagram */}
              <Card variant="elevated" className="p-6">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-pink-100 p-3">
                    <Instagram className="h-6 w-6 text-pink-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-2">
                      Instagram
                    </h3>
                    <p className="text-lg font-medium text-foreground mb-4">
                      @sitio.multitrem
                    </p>
                    <Link
                      href="https://instagram.com/sitio.multitrem"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Button variant="outline" size="sm">
                        Seguir
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            </div>

            {/* Coluna 2 - Localização */}
            <div>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4">
                Onde Estamos
              </h2>
              <p className="text-lg sm:text-xl text-foreground/70 mb-8">
                Venha nos visitar ou receba em casa
              </p>

              <Card variant="elevated" className="p-6">
                <div className="flex items-start gap-4 mb-6">
                  <div className="rounded-full bg-primary-100 p-3">
                    <MapPin className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">
                      Endereço
                    </h3>
                    <p className="text-foreground/70">
                      Abadiânia - Goiás
                    </p>
                  </div>
                </div>

                {/* Mapa placeholder - pode ser substituído por Google Maps embed */}
                <div className="w-full h-64 rounded-lg bg-primary-100 flex items-center justify-center">
                  <div className="text-center">
                    <MapPin className="h-12 w-12 text-primary-400 mx-auto mb-2" />
                    <p className="text-sm text-foreground/60">
                      Mapa será adicionado aqui
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Newsletter */}
      <section className="py-12 bg-primary-600 text-white">
        <div className="container-custom">
          <div className="max-w-2xl mx-auto text-center">
            <h3 className="text-2xl font-bold mb-4">
              Quer receber novidades e promoções?
            </h3>
            <p className="text-primary-100 mb-6">
              Cadastre seu email e fique por dentro das ofertas especiais
            </p>
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <Input
                type="email"
                placeholder="Seu melhor email"
                className="flex-1 bg-white text-foreground"
              />
              <Button
                variant="secondary"
                size="lg"
                className="whitespace-nowrap"
              >
                Inscrever
              </Button>
            </div>
            <p className="text-xs text-primary-200 mt-4">
              * Por enquanto é apenas visual. Funcionalidade será implementada
              futuramente.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}

