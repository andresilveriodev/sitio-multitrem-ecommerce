'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import type { Product, KitProduct, CartItem, Cart } from '@/types'

interface CartContextType {
  cart: Cart | null
  items: CartItem[]
  isOpen: boolean
  visitorId: string
  total: number
  itemCount: number
  isEmpty: boolean
  addItem: (
    product: Product | KitProduct,
    quantity?: number,
    selectedItems?: string[]
  ) => void
  removeItem: (productId: number) => void
  updateQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  openCart: () => void
  closeCart: () => void
  toggleCart: () => void
  refreshCart: () => Promise<void>
}

const CartContext = createContext<CartContextType | undefined>(undefined)

const CART_STORAGE_KEY = 'sitio-multitrem-cart'
const VISITOR_ID_KEY = 'sitio-multitrem-visitor-id'

function generateVisitorId(): string {
  return `visitor-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function getVisitorId(): string {
  if (typeof window === 'undefined') return generateVisitorId()

  let visitorId = localStorage.getItem(VISITOR_ID_KEY)
  if (!visitorId) {
    visitorId = generateVisitorId()
    localStorage.setItem(VISITOR_ID_KEY, visitorId)
  }
  return visitorId
}

function loadCartFromStorage(visitorId: string): Cart | null {
  if (typeof window === 'undefined') return null

  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY)
    if (!stored) return null

    const cart = JSON.parse(stored) as Cart
    if (cart.visitorId === visitorId) {
      return cart
    }
    return null
  } catch {
    return null
  }
}

function saveCartToStorage(cart: Cart) {
  if (typeof window === 'undefined') return
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart))
}

function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.subtotal, 0)
}

function calculateItemCount(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.quantity, 0)
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [visitorId] = useState<string>(getVisitorId)
  const [cart, setCart] = useState<Cart | null>(() =>
    loadCartFromStorage(visitorId)
  )
  const [isOpen, setIsOpen] = useState(false)

  // Carregar carrinho do localStorage na inicialização
  useEffect(() => {
    const loadedCart = loadCartFromStorage(visitorId)
    if (loadedCart) {
      setCart(loadedCart)
    } else {
      // Criar carrinho vazio
      const newCart: Cart = {
        id: `cart-${Date.now()}`,
        visitorId,
        items: [],
        total: 0,
        itemCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      setCart(newCart)
      saveCartToStorage(newCart)
    }
  }, [visitorId])

  // Escutar evento de atualização do carrinho (disparado pelo chat)
  useEffect(() => {
    const handleRefresh = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
        const response = await fetch(`${API_URL}/cart/${visitorId}`)
        
        if (response.ok) {
          const cartData = await response.json()
          // Converter formato do backend para formato do frontend
          const convertedCart: Cart = {
            id: cartData.id || `cart-${Date.now()}`,
            visitorId: cartData.visitorId || visitorId,
            items: (cartData.items || []).map((item: any) => ({
              productId: item.productId,
              productName: item.product?.name || 'Produto',
              unitPrice: item.product?.price || 0,
              quantity: item.quantity,
              subtotal: item.subtotal || (item.product?.price || 0) * item.quantity,
              selectedItems: item.selectedItems || [],
              imageUrl: item.product?.imageUrl || item.imageUrl,
            })),
            total: cartData.total || 0,
            itemCount: cartData.itemCount || 0,
            createdAt: cartData.createdAt || new Date().toISOString(),
            updatedAt: cartData.updatedAt || new Date().toISOString(),
          }
          setCart(convertedCart)
          saveCartToStorage(convertedCart)
        }
      } catch (error) {
        console.error('Error refreshing cart:', error)
      }
    }

    window.addEventListener('cart:refresh', handleRefresh)
    return () => {
      window.removeEventListener('cart:refresh', handleRefresh)
    }
  }, [visitorId])

  const addItem = useCallback(
    (
      product: Product | KitProduct,
      quantity: number = 1,
      selectedItems?: string[]
    ) => {
      setCart((currentCart) => {
        if (!currentCart) {
          const newCart: Cart = {
            id: `cart-${Date.now()}`,
            visitorId,
            items: [],
            total: 0,
            itemCount: 0,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
          return newCart
        }

        const existingItemIndex = currentCart.items.findIndex(
          (item) =>
            item.productId === product.id &&
            JSON.stringify(item.selectedItems || []) ===
              JSON.stringify(selectedItems || [])
        )

        let newItems: CartItem[]

        if (existingItemIndex >= 0) {
          // Item já existe, atualizar quantidade
          newItems = [...currentCart.items]
          const existingItem = newItems[existingItemIndex]
          const newQuantity = existingItem.quantity + quantity
          newItems[existingItemIndex] = {
            ...existingItem,
            quantity: newQuantity,
            subtotal: product.price * newQuantity,
          }
        } else {
          // Novo item
          const newItem: CartItem = {
            productId: product.id,
            visitorId,
            productName: product.name,
            quantity,
            unitPrice: product.price,
            selectedItems,
            subtotal: product.price * quantity,
            imageUrl: product.imageUrl,
          }
          newItems = [...currentCart.items, newItem]
        }

        const total = calculateTotal(newItems)
        const itemCount = calculateItemCount(newItems)

        const updatedCart: Cart = {
          ...currentCart,
          items: newItems,
          total,
          itemCount,
          updatedAt: new Date().toISOString(),
        }

        saveCartToStorage(updatedCart)
        return updatedCart
      })
    },
    [visitorId]
  )

  const removeItem = useCallback((productId: number) => {
    setCart((currentCart) => {
      if (!currentCart) return currentCart

      const newItems = currentCart.items.filter(
        (item) => item.productId !== productId
      )
      const total = calculateTotal(newItems)
      const itemCount = calculateItemCount(newItems)

      const updatedCart: Cart = {
        ...currentCart,
        items: newItems,
        total,
        itemCount,
        updatedAt: new Date().toISOString(),
      }

      saveCartToStorage(updatedCart)
      return updatedCart
    })
  }, [])

  const updateQuantity = useCallback((productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeItem(productId)
      return
    }

    setCart((currentCart) => {
      if (!currentCart) return currentCart

      const newItems = currentCart.items.map((item) => {
        if (item.productId === productId) {
          return {
            ...item,
            quantity,
            subtotal: item.unitPrice * quantity,
          }
        }
        return item
      })

      const total = calculateTotal(newItems)
      const itemCount = calculateItemCount(newItems)

      const updatedCart: Cart = {
        ...currentCart,
        items: newItems,
        total,
        itemCount,
        updatedAt: new Date().toISOString(),
      }

      saveCartToStorage(updatedCart)
      return updatedCart
    })
  }, [removeItem])

  const clearCart = useCallback(() => {
    const emptyCart: Cart = {
      id: `cart-${Date.now()}`,
      visitorId,
      items: [],
      total: 0,
      itemCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    setCart(emptyCart)
    saveCartToStorage(emptyCart)
  }, [visitorId])

  const openCart = useCallback(() => setIsOpen(true), [])
  const closeCart = useCallback(() => setIsOpen(false), [])
  const toggleCart = useCallback(() => setIsOpen((prev) => !prev), [])

  const refreshCart = useCallback(async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'
      const response = await fetch(`${API_URL}/cart/${visitorId}`)
      
      if (response.ok) {
        const cartData = await response.json()
        // Converter formato do backend para formato do frontend
        const convertedCart: Cart = {
          id: cartData.id || `cart-${Date.now()}`,
          visitorId: cartData.visitorId || visitorId,
          items: (cartData.items || []).map((item: any) => ({
            productId: item.productId,
            productName: item.product?.name || 'Produto',
            unitPrice: item.product?.price || 0,
            quantity: item.quantity,
            subtotal: item.subtotal || (item.product?.price || 0) * item.quantity,
            selectedItems: item.selectedItems || [],
          })),
          total: cartData.total || 0,
          itemCount: cartData.itemCount || 0,
          createdAt: cartData.createdAt || new Date().toISOString(),
          updatedAt: cartData.updatedAt || new Date().toISOString(),
        }
        setCart(convertedCart)
        saveCartToStorage(convertedCart)
      }
    } catch (error) {
      console.error('Error refreshing cart:', error)
    }
  }, [visitorId])

  const value: CartContextType = {
    cart,
    items: cart?.items || [],
    isOpen,
    visitorId,
    total: cart?.total || 0,
    itemCount: cart?.itemCount || 0,
    isEmpty: (cart?.items.length || 0) === 0,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    openCart,
    closeCart,
    toggleCart,
    refreshCart,
  }

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const context = useContext(CartContext)
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider')
  }
  return context
}

