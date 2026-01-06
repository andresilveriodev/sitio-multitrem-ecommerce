import Link from 'next/link'
import { Phone, Instagram, MapPin, Calendar, Clock } from 'lucide-react'
import styles from './Footer.module.css'

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footer__container}>
        <div className={styles.footer__grid}>
          {/* Coluna 1 - Sobre */}
          <div className={styles.footer__column}>
            <div className={styles.footer__logo}>
              <span className={styles.footer__logo_icon}>🌿</span>
              <h3 className={styles.footer__logo_text}>Sítio Multitrem</h3>
            </div>
            <p className={styles.footer__description}>
              Produtos frescos direto do produtor
            </p>
            <p className={styles.footer__description}>
              Produção familiar em Terezópolis de Goiás, com todo carinho e qualidade que sua
              família merece.
            </p>
          </div>

          {/* Coluna 2 - Contato */}
          <div className={styles.footer__column}>
            <h3 className={styles.footer__heading}>Contato</h3>
            <ul className={styles.footer__list}>
              <li>
                <Link
                  href="https://wa.me/5562981225993"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.footer__link}
                >
                  <Phone className={styles.footer__icon} />
                  <span>(62) 98122-5993</span>
                </Link>
              </li>
              <li>
                <Link
                  href="https://instagram.com/sitio.multitrem"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.footer__link}
                >
                  <Instagram className={styles.footer__icon} />
                  <span>@sitio.multitrem</span>
                </Link>
              </li>
              <li className={styles.footer__list_item}>
                <MapPin className={styles.footer__icon} />
                <span>Terezópolis de Goiás</span>
              </li>
            </ul>
          </div>

          {/* Coluna 3 - Entregas */}
          <div className={styles.footer__column}>
            <h3 className={styles.footer__heading}>Entregas</h3>
            <ul className={styles.footer__list}>
              <li className={styles.footer__list_item}>
                <Calendar className={styles.footer__icon} />
                <span>Quarta a Sábado</span>
              </li>
              <li className={styles.footer__list_item}>
                <Clock className={styles.footer__icon} />
                <span>Período: Manhã</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Barra inferior */}
        <div className={styles.footer__bottom}>
          <p className={styles.footer__copyright}>
            © {new Date().getFullYear()} Sítio Multitrem. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </footer>
  )
}

