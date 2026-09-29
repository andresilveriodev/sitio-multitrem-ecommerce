export type OrderItem = {
  produto: string;
  qtd: number;
  qtdEntregue?: number;
  quantidadeEmBranco?: boolean;
  valor: number;
  desconto?: number;
  descontoPercentual?: number;
  tipo?: string;
  conhecido?: boolean;
  preco_tabela?: boolean;
};

export type Order = {
  id?: string;
  cliente: string;
  clienteId?: number;
  data: string;
  endereco: string;
  desconto: number;
  tabela?: string;
  itens: OrderItem[];
};

export type ConvertResponse = {
  orders: Order[];
  catalog: string[];
};
