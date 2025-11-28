import Link from 'next/link'
import { Phone, Instagram, MapPin, Calendar, Clock } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-background">
      <div className="container-custom">
        <div className="grid grid-cols-1 gap-8 sm:gap-10 py-12 sm:py-16 md:grid-cols-3">
          {/* Coluna 1 - Sobre */}
          <div>
            <div className="flex items-center gap-2 mb-4 sm:mb-6">
              <span className="text-2xl sm:text-3xl">🌿</span>
              <h3 className="text-lg sm:text-xl font-bold text-primary-600">
                Sítio Multitrem
              </h3>
            </div>
            <p className="text-sm sm:text-base text-gray-700 mb-2 sm:mb-3 leading-relaxed">
              Produtos frescos direto do produtor
            </p>
            <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
              Produção familiar em Terezópolis de Goiás, com todo carinho e qualidade
              que sua família merece.
            </p>
          </div>

          {/* Coluna 2 - Contato */}
          <div>
            <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6">Contato</h3>
            <ul className="space-y-3 sm:space-y-4 text-sm sm:text-base">
              <li>
                <Link
                  href="https://wa.me/5562981225993"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-gray-700 hover:text-primary-600 transition-colors"
                >
                  <Phone className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span>(62) 98122-5993</span>
                </Link>
              </li>
              <li>
                <Link
                  href="https://instagram.com/sitio.multitrem"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-gray-700 hover:text-primary-600 transition-colors"
                >
                  <Instagram className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span>@sitio.multitrem</span>
                </Link>
              </li>
              <li className="flex items-center gap-2 text-gray-700">
                <MapPin className="h-4 w-4 sm:h-5 sm:w-5" />
                <span>Terezópolis de Goiás</span>
              </li>
            </ul>
          </div>

          {/* Coluna 3 - Entregas */}
          <div>
            <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6">Entregas</h3>
            <ul className="space-y-3 sm:space-y-4 text-sm sm:text-base text-gray-700">
              <li className="flex items-center gap-2">
                <Calendar className="h-4 w-4 sm:h-5 sm:w-5" />
                <span>Quarta a Sábado</span>
              </li>
              <li className="flex items-center gap-2">
                <Clock className="h-4 w-4 sm:h-5 sm:w-5" />
                <span>Período: Manhã</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Barra inferior */}
        <div className="border-t border-gray-200 py-6 sm:py-8 text-center text-sm sm:text-base text-gray-600">
          <p>
            © {new Date().getFullYear()} Sítio Multitrem. Todos os direitos
            reservados.
          </p>
        </div>
      </div>
    </footer>
  )
}

