'use client'

import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { Input, Button, Spinner } from '@/components/ui'
import { useCheckout } from '@/hooks/useCheckout'
import { maskPhone, maskCEP, unmask } from '@/lib/masks'
import { fetchCEP } from '@/lib/viacep'
import type { Address } from '@/types'

export function CustomerDataStep() {
  const { customerData, setCustomerData, nextStep } = useCheckout()
  
  const [formData, setFormData] = useState({
    name: customerData?.name || '',
    phone: customerData?.phone || '',
    email: customerData?.email || '',
    cep: '',
    street: customerData?.address.street || '',
    number: customerData?.address.number || '',
    complement: customerData?.address.complement || '',
    neighborhood: customerData?.address.neighborhood || '',
    city: customerData?.address.city || '',
    state: customerData?.address.state || '',
    zipCode: customerData?.address.zipCode || '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loadingCEP, setLoadingCEP] = useState(false)

  // Buscar CEP quando completo
  useEffect(() => {
    const cepNumbers = unmask(formData.cep)
    if (cepNumbers.length === 8) {
      handleCEPBlur()
    }
  }, [formData.cep])

  const handleCEPBlur = async () => {
    const cepNumbers = unmask(formData.cep)
    if (cepNumbers.length !== 8) return

    setLoadingCEP(true)
    const cepData = await fetchCEP(cepNumbers)
    
    if (cepData) {
      setFormData((prev) => ({
        ...prev,
        street: cepData.logradouro || prev.street,
        neighborhood: cepData.bairro || prev.neighborhood,
        city: cepData.localidade || prev.city,
        state: cepData.uf || prev.state,
        zipCode: cepData.cep || prev.zipCode,
      }))
      setErrors((prev) => ({ ...prev, cep: '' }))
    } else {
      setErrors((prev) => ({
        ...prev,
        cep: 'CEP não encontrado',
      }))
    }
    
    setLoadingCEP(false)
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Nome é obrigatório'
    }

    const phoneNumbers = unmask(formData.phone)
    if (!phoneNumbers || phoneNumbers.length < 10) {
      newErrors.phone = 'Telefone inválido'
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido'
    }

    const cepNumbers = unmask(formData.cep)
    if (!cepNumbers || cepNumbers.length !== 8) {
      newErrors.cep = 'CEP inválido'
    }

    if (!formData.street.trim()) {
      newErrors.street = 'Rua é obrigatória'
    }

    if (!formData.number.trim()) {
      newErrors.number = 'Número é obrigatório'
    }

    if (!formData.neighborhood.trim()) {
      newErrors.neighborhood = 'Bairro é obrigatório'
    }

    if (!formData.city.trim()) {
      newErrors.city = 'Cidade é obrigatória'
    }

    if (!formData.state.trim()) {
      newErrors.state = 'Estado é obrigatório'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validate()) {
      return
    }

    const address: Address = {
      street: formData.street,
      number: formData.number,
      complement: formData.complement || undefined,
      neighborhood: formData.neighborhood,
      city: formData.city,
      state: formData.state,
      zipCode: unmask(formData.cep),
    }

    setCustomerData({
      name: formData.name,
      phone: unmask(formData.phone),
      email: formData.email || undefined,
      address,
    })

    nextStep()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Dados Pessoais */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Dados Pessoais</h3>
        <div className="space-y-4">
          <Input
            label="Nome completo *"
            value={formData.name}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, name: e.target.value }))
            }
            error={errors.name}
            required
            autoFocus
          />

          <Input
            label="WhatsApp *"
            type="tel"
            value={formData.phone}
            onChange={(e) => {
              const masked = maskPhone(e.target.value)
              setFormData((prev) => ({ ...prev, phone: masked }))
            }}
            error={errors.phone}
            required
            placeholder="(62) 98122-5993"
          />

          <Input
            label="Email (opcional)"
            type="email"
            value={formData.email}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, email: e.target.value }))
            }
            error={errors.email}
            placeholder="seu@email.com"
          />
        </div>
      </div>

      {/* Endereço */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Endereço de Entrega</h3>
        <div className="space-y-4">
          <div className="relative">
            <Input
              label="CEP *"
              value={formData.cep}
              onChange={(e) => {
                const masked = maskCEP(e.target.value)
                setFormData((prev) => ({ ...prev, cep: masked }))
              }}
              onBlur={handleCEPBlur}
              error={errors.cep}
              required
              placeholder="00000-000"
              maxLength={9}
            />
            {loadingCEP && (
              <div className="absolute right-3 top-9">
                <Spinner size="sm" />
              </div>
            )}
          </div>

          <Input
            label="Rua *"
            value={formData.street}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, street: e.target.value }))
            }
            error={errors.street}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Número *"
              value={formData.number}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, number: e.target.value }))
              }
              error={errors.number}
              required
            />

            <Input
              label="Complemento"
              value={formData.complement}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  complement: e.target.value,
                }))
              }
              placeholder="Apto, Bloco, etc."
            />
          </div>

          <Input
            label="Bairro *"
            value={formData.neighborhood}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                neighborhood: e.target.value,
              }))
            }
            error={errors.neighborhood}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Cidade *"
              value={formData.city}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, city: e.target.value }))
              }
              error={errors.city}
              required
            />

            <Input
              label="Estado *"
              value={formData.state}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, state: e.target.value }))
              }
              error={errors.state}
              required
              maxLength={2}
              placeholder="GO"
            />
          </div>
        </div>
      </div>

      {/* Botões */}
      <div className="flex justify-end gap-4 pt-4">
        <Button type="submit" variant="primary" size="lg">
          Continuar
        </Button>
      </div>
    </form>
  )
}

