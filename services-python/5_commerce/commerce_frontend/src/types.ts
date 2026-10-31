export type OrderItem = {
  produto: string;
  qtd: number;
  qtdEntregue?: number;
  qtdComprada?: number;
  quantidadeEmBranco?: boolean;
  valor: number;
  desconto?: number;
  descontoPercentual?: number;
  tipo?: string;
  conhecido?: boolean;
  preco_tabela?: boolean;
  reagendar?: boolean;
  qtdReagendada?: number;
  dataReagendada?: string;
  /** Quando já existe o produto na data destino: somar ou substituir a qtde. */
  reagendaConduta?: "somar" | "substituir";
  observacao?: string;
  origemId?: string;
  origemData?: string;
};

export type Order = {
  id?: string;
  tipo?: "venda" | "compra";
  cliente: string;
  clienteId?: number;
  data: string;
  endereco: string;
  desconto: number;
  tabela?: string;
  concluido?: boolean;
  pago?: boolean;
  observacao?: string;
  itens: OrderItem[];
};

export type ConvertResponse = {
  orders: Order[];
  catalog: string[];
};
