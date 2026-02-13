"""
Modelos Pydantic para estruturas de investimento
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FrontendAction(BaseModel):
    """Estrutura de frontend_action conforme especificação"""
    type: str = Field(..., description="Tipo de ação (add_investment, remove_investment, etc)")
    parameters: Dict[str, Any] = Field(..., description="Parâmetros da ação")
    command_id: str = Field(..., description="ID único do comando")


class InvestmentAddParameters(BaseModel):
    """Parâmetros para adicionar investimento"""
    categoryName: str = Field(..., description="Nome da categoria")
    ticker: Optional[str] = Field(None, description="Ticker do ativo")
    quantity: Optional[float] = Field(None, description="Quantidade (pode ser negativa para short selling)")
    price: Optional[float] = Field(None, description="Preço unitário (sempre positivo)")
    valor: Optional[float] = Field(None, description="Valor total (pode ser negativo se quantity for negativa)")
    isShort: bool = Field(False, description="Flag indicando operação vendida")
    dataAquisicao: Optional[str] = Field(None, description="Data de aquisição (YYYY-MM-DD)")
    rentabilidade: Optional[float] = Field(None, description="Rentabilidade em percentual")
    observacoes: Optional[str] = Field(None, description="Observações")
    planId: Optional[str] = Field(None, description="ID do plano")
    periodoId: Optional[str] = Field(None, description="ID do período")
    price_from_market: Optional[bool] = Field(None, description="Flag indicando se preço veio de mercado")


class InvestmentRemoveParameters(BaseModel):
    """Parâmetros para remover investimento"""
    investmentId: Optional[str] = Field(None, description="ID do investimento (se específico)")
    categoryName: Optional[str] = Field(None, description="Nome da categoria (se remover todos)")
    ticker: Optional[str] = Field(None, description="Ticker do ativo")
    allFromCategory: bool = Field(False, description="Remover todos da categoria")
    planId: Optional[str] = Field(None, description="ID do plano")
    periodoId: Optional[str] = Field(None, description="ID do período")


class InvestmentUpdateParameters(BaseModel):
    """Parâmetros para atualizar investimento"""
    investmentId: str = Field(..., description="ID do investimento")
    ticker: Optional[str] = Field(None, description="Ticker do ativo")
    quantity: Optional[float] = Field(None, description="Nova quantidade")
    price: Optional[float] = Field(None, description="Novo preço")
    valor: Optional[float] = Field(None, description="Novo valor total")
    rentabilidade: Optional[float] = Field(None, description="Nova rentabilidade")
    observacoes: Optional[str] = Field(None, description="Novas observações")
    planId: Optional[str] = Field(None, description="ID do plano")


class InvestmentCategoryParameters(BaseModel):
    """Parâmetros para operações com categorias"""
    categoryName: str = Field(..., description="Nome da categoria")
    categoryId: Optional[str] = Field(None, description="ID da categoria")
    percentual: Optional[float] = Field(None, description="Percentual da categoria")
    valor: Optional[float] = Field(None, description="Valor da categoria")
    cor: Optional[str] = Field(None, description="Cor da categoria")
    planId: Optional[str] = Field(None, description="ID do plano")
    periodoId: Optional[str] = Field(None, description="ID do período")


class InvestmentDistributionParameters(BaseModel):
    """Parâmetros para distribuição de investimentos"""
    planId: str = Field(..., description="ID do plano")
    periodoId: Optional[str] = Field(None, description="ID do período")
    distribution: Dict[str, float] = Field(..., description="Distribuição por categoria (nome: percentual)")
    total: Optional[float] = Field(None, description="Valor total (opcional, usa aporteInicial do plano se não fornecido)")


class ChatResponse(BaseModel):
    """Resposta do chat com frontend_action"""
    response: str = Field(..., description="Resposta textual")
    frontend_action: Optional[FrontendAction] = Field(None, description="Ação para o frontend")
    confirmation_required: bool = Field(False, description="Se requer confirmação")
    needs_user_input: bool = Field(False, description="Se precisa de input do usuário")
    missing_fields: list = Field(default_factory=list, description="Campos faltantes")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    warnings: Optional[list] = Field(None, description="Avisos (ex: preço de mercado)")


class ProcessMessageResponse(BaseModel):
    """Resposta completa do processamento de mensagem"""
    success: bool
    response: Optional[ChatResponse] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

