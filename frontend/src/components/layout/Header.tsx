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
      <header
        className={cn(
          'fixed top-0 z-50 w-full border-b border-gray-200 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 transition-all',
          isScrolled && 'shadow-sm'
        )}
      >
        <div className="container-custom">
          <div className="flex h-16 sm:h-20 items-center justify-between">
            {/* Logo */}
            <Link
              href="/"
              className="flex items-center gap-2 text-xl sm:text-2xl font-bold text-primary-600 hover:text-primary-700 transition-colors"
            >
              <span className="text-2xl sm:text-3xl">🌿</span>
              <span>Sítio Multitrem</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6 lg:gap-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="text-sm sm:text-base font-medium text-gray-700 hover:text-primary-600 transition-colors"
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

              {isAuthenticated ? (
                <div className="flex items-center gap-2">
                  <button
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm sm:text-base font-medium text-gray-700 hover:bg-primary-50 transition-colors"
                    aria-label="Perfil do usuário"
                    title={user?.email || user?.preferred_username || 'Usuário'}
                  >
                    <User className="h-5 w-5" />
                    <span className="hidden sm:inline">
                      {user?.given_name || user?.preferred_username || 'Perfil'}
                    </span>
                  </button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={logout}
                    className="hidden sm:flex"
                  >
                    Sair
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="hidden sm:flex"
                  onClick={() => setIsLoginModalOpen(true)}
                >
                  Boas vindas :) Entre ou Cadastre-se
                </Button>
              )}

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden rounded-lg p-2 text-gray-700 hover:bg-primary-50 transition-colors"
                aria-label="Abrir menu"
              >
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
      />

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
              className="text-base font-medium text-gray-700 hover:text-primary-600 transition-colors"
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
            {!isAuthenticated && (
              <Button
                variant="outline"
                size="sm"
                className="mt-2 w-full"
                onClick={() => {
                  setIsLoginModalOpen(true)
                  setIsMobileMenuOpen(false)
                }}
              >
                Boas vindas :) Entre ou Cadastre-se
              </Button>
            )}
            {isAuthenticated && (
              <Button
                variant="outline"
                size="sm"
                className="mt-2 w-full"
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

