'use client'

import { useState, useEffect } from 'react'
import { Menu, User } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { CartButton } from './CartButton'
import { MobileMenu } from './MobileMenu'
import { useCart } from '@/hooks/useCart'
import { useAuth } from '@/contexts/AuthContext'
import { LoginModal } from '@/components/auth/LoginModal'
import styles from './Header.module.css'

const navigation = [
  { name: 'Produtos', href: '#produtos' },
  { name: 'Como Funciona', href: '#como-funciona' },
  { name: 'Entregas', href: '#entregas' },
  { name: 'Contato', href: '#contato' },
]

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()
  const { itemCount, openCart } = useCart()

  // Detectar scroll
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleCartClick = () => {
    openCart()
  }

  return (
    <>
      <header className={cn(styles.header, isScrolled && styles['header--scrolled'])}>
        <div className={styles.header__container}>
          {/* Logo */}
          <Link href="/" className={styles.header__logo}>
            <span className={styles.header__logo_icon}>🌿</span>
            <span className={styles.header__logo_text}>Sítio Multitrem</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className={styles.header__nav}>
            {navigation.map((item) => (
              <Link key={item.name} href={item.href} className={styles.header__nav_link}>
                {item.name}
              </Link>
            ))}
          </nav>

          {/* Right Side */}
          <div className={styles.header__actions}>
            <CartButton
              itemCount={itemCount}
              onClick={handleCartClick}
              className={styles.hide_mobile}
            />

            {isAuthenticated ? (
              <div className={styles.header__actions}>
                <button
                  className={styles.header__user_button}
                  aria-label="Perfil do usuário"
                  title={user?.email || user?.preferred_username || 'Usuário'}
                >
                  <User className="h-5 w-5" />
                  <span className={styles.header__user_button_text}>
                    {user?.given_name || user?.preferred_username || 'Perfil'}
                  </span>
                </button>
                <Button variant="outline" size="sm" onClick={logout} className={styles.hide_mobile}>
                  Sair
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className={styles.hide_mobile}
                onClick={() => setIsLoginModalOpen(true)}
              >
                Entrar
              </Button>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className={styles.header__menu_button}
              aria-label="Abrir menu"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
      />

      {/* Mobile Menu */}
      <MobileMenu isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)}>
        <div className={styles.header__mobile_menu_content}>
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className={styles.header__mobile_nav_link}
            >
              {item.name}
            </Link>
          ))}
          <div className={styles.header__mobile_divider}>
            <CartButton
              itemCount={itemCount}
              onClick={() => {
                handleCartClick()
                setIsMobileMenuOpen(false)
              }}
              className="w-full justify-start"
            />
            {!isAuthenticated && (
              <Button
                variant="outline"
                size="sm"
                className={styles.header__mobile_button}
                onClick={() => {
                  setIsLoginModalOpen(true)
                  setIsMobileMenuOpen(false)
                }}
              >
                Entrar ou Cadastrar
              </Button>
            )}
            {isAuthenticated && (
              <Button
                variant="outline"
                size="sm"
                className={styles.header__mobile_button}
                onClick={() => {
                  logout()
                  setIsMobileMenuOpen(false)
                }}
              >
                Sair
              </Button>
            )}
          </div>
        </div>
      </MobileMenu>
    </>
  )
}

