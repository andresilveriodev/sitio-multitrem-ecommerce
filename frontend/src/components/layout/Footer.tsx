import Link from 'next/link'
import { Phone, Instagram, MapPin, Calendar, Clock } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-foreground/10 bg-background">
      <div className="container-custom">
        <div className="grid grid-cols-1 gap-8 py-12 md:grid-cols-3">
          {/* Coluna 1 - Sobre */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🌿</span>
              <h3 className="text-lg font-bold text-primary-600">
                Sítio Multitrem
              </h3>
            </div>
            <p className="text-sm text-foreground/80 mb-2">
              Produtos frescos direto do produtor
            </p>
            <p className="text-sm text-foreground/60">
              Produção familiar em Abadiânia-GO, com todo carinho e qualidade
              que sua família merece.
            </p>
          </div>

          {/* Coluna 2 - Contato */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Contato</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link
                  href="https://wa.me/5562981225993"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-foreground/80 hover:text-primary-600 transition-colors"
                >
                  <Phone className="h-4 w-4" />
                  <span>(62) 98122-5993</span>
                </Link>
              </li>
              <li>
                <Link
                  href="https://instagram.com/sitio.multitrem"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-foreground/80 hover:text-primary-600 transition-colors"
                >
                  <Instagram className="h-4 w-4" />
                  <span>@sitio.multitrem</span>
                </Link>
              </li>
              <li className="flex items-center gap-2 text-foreground/80">
                <MapPin className="h-4 w-4" />
                <span>Abadiânia - GO</span>
              </li>
            </ul>
          </div>

          {/* Coluna 3 - Entregas */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Entregas</h3>
            <ul className="space-y-3 text-sm text-foreground/80">
              <li className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span>Quarta a Sábado</span>
              </li>
              <li className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>Período: Manhã</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Barra inferior */}
        <div className="border-t border-foreground/10 py-6 text-center text-sm text-foreground/60">
          <p>
            © {new Date().getFullYear()} Sítio Multitrem. Todos os direitos
            reservados.
          </p>
        </div>
      </div>
    </footer>
  )
}

