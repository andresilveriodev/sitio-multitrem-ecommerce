export interface Address {
  street: string
  number: string
  complement?: string
  neighborhood: string
  city: string
  state: string
  zipCode: string
}

export interface Customer {
  id: number
  visitorId: string
  keycloakId?: string
  name: string
  phone: string
  email?: string
  address: Address
  createdAt: string
}

