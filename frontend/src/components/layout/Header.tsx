'use client'

import { useState, useEffect } from 'react'
import { Menu, LogIn, User } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { CartButton } from './CartButton'
import { MobileMenu } from './MobileMenu'
import { useCart } from '@/hooks/useCart'

const navigation = [
  { name: 'Produtos', href: '#produtos' },
  { name: 'Como Funciona', href: '#como-funciona' },
  { name: 'Entregas', href: '#entregas' },
  { name: 'Contato', href: '#contato' },
]

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const isLoggedIn = false // TODO: Integrar com Keycloak
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
      <header
        className={cn(
          'fixed top-0 z-50 w-full border-b border-foreground/10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 transition-all',
          isScrolled && 'shadow-sm'
        )}
      >
        <div className="container-custom">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link
              href="/"
              className="flex items-center gap-2 text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors"
            >
              <span className="text-2xl">🌿</span>
              <span>Sítio Multitrem</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="text-sm font-medium text-foreground/80 hover:text-primary-600 transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </nav>

            {/* Right Side */}
            <div className="flex items-center gap-2">
              <CartButton
                itemCount={itemCount}
                onClick={handleCartClick}
                className="hidden sm:flex"
              />

              {isLoggedIn ? (
                <button
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-foreground hover:bg-primary-50 transition-colors"
                  aria-label="Perfil do usuário"
                >
                  <User className="h-5 w-5" />
                  <span className="hidden sm:inline">Perfil</span>
                </button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<LogIn className="h-4 w-4" />}
                  className="hidden sm:flex"
                >
                  Entrar
                </Button>
              )}

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden rounded-lg p-2 text-foreground hover:bg-primary-50 transition-colors"
                aria-label="Abrir menu"
              >
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      >
        <div className="flex flex-col gap-4">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-base font-medium text-foreground hover:text-primary-600 transition-colors"
            >
              {item.name}
            </Link>
          ))}
          <div className="mt-4 pt-4 border-t border-foreground/10">
            <CartButton
              itemCount={itemCount}
              onClick={() => {
                handleCartClick()
                setIsMobileMenuOpen(false)
              }}
              className="w-full justify-start"
            />
            {!isLoggedIn && (
              <Button
                variant="outline"
                size="sm"
                leftIcon={<LogIn className="h-4 w-4" />}
                className="mt-2 w-full"
              >
                Entrar
              </Button>
            )}
          </div>
        </div>
      </MobileMenu>
    </>
  )
}

