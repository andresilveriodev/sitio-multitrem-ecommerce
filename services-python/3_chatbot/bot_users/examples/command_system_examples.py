"""
Exemplos de uso do sistema de comandos seguros
"""

import asyncio
import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.commands import (
    CommandAnalyzer,
    CommandExecutor,
    CommandValidator,
    ALL_COMMANDS
)
from services.security import (
    permission_manager,
    PermissionLevel,
    confirmation_manager
)
from services.commands.types import CommandRequest
import structlog

# Configurar logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def example_1_basic_command_analysis():
    """Exemplo 1: Análise básica de comandos"""
    print("\n=== Exemplo 1: Análise Básica de Comandos ===")
    
    analyzer = CommandAnalyzer()
    
    # Simular permissões de usuário básico
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.BASIC)
    
    # Mensagens para testar
    test_messages = [
        "Mostre a posição da PETR4",
        "Adicione VALE3 ao watchlist",
        "Prepare uma ordem de compra de 100 PETR4 a 38.50",
        "Crie uma aba de análise para ITUB4",
        "Olá, como você está?"  # Não é um comando
    ]
    
    for message in test_messages:
        print(f"\nMensagem: '{message}'")
        
        analysis = await analyzer.analyze_message(message, user_permissions)
        
        if analysis.is_command:
            print(f"  ✅ É um comando!")
            print(f"  Comando: {analysis.command_id}")
            print(f"  Confiança: {analysis.confidence:.2f}")
            print(f"  Parâmetros: {analysis.parameters}")
            if analysis.suggestions:
                print(f"  Sugestões: {analysis.suggestions}")
        else:
            print(f"  ❌ Não é um comando")
            if analysis.suggestions:
                print(f"  Sugestões: {analysis.suggestions}")


async def example_2_command_execution():
    """Exemplo 2: Execução de comandos"""
    print("\n=== Exemplo 2: Execução de Comandos ===")
    
    executor = CommandExecutor()
    
    # Simular permissões de usuário trader
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.TRADER)
    
    # Testar comandos que não precisam confirmação
    view_commands = [
        CommandRequest(
            command_id="show_position",
            parameters={"symbol": "PETR4"},
            user_id="user123"
        ),
        CommandRequest(
            command_id="show_watchlist",
            parameters={},
            user_id="user123"
        )
    ]
    
    for request in view_commands:
        print(f"\nExecutando: {request.command_id}")
        
        success, message, result, confirmation = await executor.execute_command(
            request, user_permissions
        )
        
        if success:
            if confirmation:
                print(f"  ⏳ Aguardando confirmação: {confirmation.message}")
            else:
                print(f"  ✅ Executado: {result.message}")
                print(f"  Dados: {result.data}")
        else:
            print(f"  ❌ Erro: {message}")


async def example_3_confirmation_required():
    """Exemplo 3: Comandos que precisam confirmação"""
    print("\n=== Exemplo 3: Comandos que Precisam Confirmação ===")
    
    executor = CommandExecutor()
    
    # Simular permissões de usuário trader
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.TRADER)
    
    # Testar comando que precisa confirmação
    trade_request = CommandRequest(
        command_id="prepare_buy_order",
        parameters={
            "symbol": "PETR4",
            "quantity": 100,
            "price": 38.50
        },
        user_id="user123"
    )
    
    print(f"\nExecutando: {trade_request.command_id}")
    
    success, message, result, confirmation = await executor.execute_command(
        trade_request, user_permissions
    )
    
    if success and confirmation:
        print(f"  ⏳ Aguardando confirmação: {confirmation.message}")
        print(f"  ID da confirmação: {confirmation.execution_id}")
        print(f"  Nível de risco: {confirmation.risk_level}")
        
        # Simular confirmação do usuário
        print("\n  Simulando confirmação do usuário...")
        
        confirm_success, confirm_message, confirm_result = await executor.confirm_command(
            confirmation.execution_id,
            "user123",
            True  # Confirmar
        )
        
        if confirm_success:
            print(f"  ✅ Comando confirmado e executado: {confirm_result.message}")
            print(f"  Dados: {confirm_result.data}")
        else:
            print(f"  ❌ Erro na confirmação: {confirm_message}")
    else:
        print(f"  ❌ Erro: {message}")


async def example_4_permission_validation():
    """Exemplo 4: Validação de permissões"""
    print("\n=== Exemplo 4: Validação de Permissões ===")
    
    validator = CommandValidator()
    
    # Testar com diferentes níveis de permissão
    permission_levels = [
        PermissionLevel.BASIC,
        PermissionLevel.PREMIUM,
        PermissionLevel.TRADER,
        PermissionLevel.PROFESSIONAL
    ]
    
    test_command = CommandRequest(
        command_id="prepare_buy_order",
        parameters={"symbol": "PETR4", "quantity": 100},
        user_id="user123"
    )
    
    for level in permission_levels:
        print(f"\nTestando com permissões de nível: {level.value}")
        
        user_permissions = permission_manager.get_user_permissions(level)
        
        is_valid, error_message, command = await validator.validate_command_request(
            test_command, user_permissions, "user123"
        )
        
        if is_valid:
            print(f"  ✅ Comando válido: {command.name}")
        else:
            print(f"  ❌ Comando inválido: {error_message}")
            
            # Sugerir upgrade
            suggestion = permission_manager.suggest_permission_upgrade(
                user_permissions, test_command.command_id
            )
            if suggestion:
                print(f"  💡 Sugestão: Upgrade para {suggestion['suggested_level']}")


async def example_5_command_suggestions():
    """Exemplo 5: Sugestões de comandos"""
    print("\n=== Exemplo 5: Sugestões de Comandos ===")
    
    validator = CommandValidator()
    
    # Simular permissões de usuário básico
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.BASIC)
    
    # Testar sugestões para diferentes inputs
    test_inputs = [
        "pos",
        "watch",
        "buy",
        "sell",
        "anal"
    ]
    
    for partial_input in test_inputs:
        print(f"\nSugestões para '{partial_input}':")
        
        suggestions = await validator.get_command_suggestions(partial_input, user_permissions)
        
        for suggestion in suggestions:
            print(f"  📋 {suggestion['name']} ({suggestion['id']})")
            print(f"     Descrição: {suggestion['description']}")
            print(f"     Categoria: {suggestion['category']}")
            print(f"     Risco: {suggestion['risk_level']}")
            if suggestion['examples']:
                print(f"     Exemplo: {suggestion['examples'][0]}")


async def example_6_available_commands():
    """Exemplo 6: Comandos disponíveis por categoria"""
    print("\n=== Exemplo 6: Comandos Disponíveis por Categoria ===")
    
    analyzer = CommandAnalyzer()
    
    # Simular permissões de usuário trader
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.TRADER)
    
    available_commands = await analyzer.get_available_commands(user_permissions)
    
    for category, commands in available_commands.items():
        print(f"\n📁 Categoria: {category.upper()}")
        
        for command in commands:
            print(f"  🔧 {command['name']} ({command['id']})")
            print(f"     Descrição: {command['description']}")
            print(f"     Confirmação: {'Sim' if command['requires_confirmation'] else 'Não'}")
            print(f"     Risco: {command['risk_level']}")
            if command['examples']:
                print(f"     Exemplo: {command['examples'][0]}")


async def example_7_execution_history():
    """Exemplo 7: Histórico de execuções"""
    print("\n=== Exemplo 7: Histórico de Execuções ===")
    
    executor = CommandExecutor()
    
    # Executar alguns comandos primeiro
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.TRADER)
    
    test_commands = [
        CommandRequest(command_id="show_position", parameters={"symbol": "PETR4"}, user_id="user123"),
        CommandRequest(command_id="show_watchlist", parameters={}, user_id="user123"),
        CommandRequest(command_id="add_watchlist", parameters={"symbol": "VALE3"}, user_id="user123")
    ]
    
    print("Executando comandos para gerar histórico...")
    
    for request in test_commands:
        success, message, result, confirmation = await executor.execute_command(
            request, user_permissions
        )
        
        if success and confirmation:
            # Confirmar automaticamente
            await executor.confirm_command(confirmation.execution_id, "user123", True)
    
    # Mostrar histórico
    history = await executor.get_execution_history("user123", limit=10)
    
    print(f"\n📊 Histórico de execuções (últimas {len(history)}):")
    
    for execution in history:
        print(f"  📅 {execution['created_at']}")
        print(f"     Comando: {execution['command_name']} ({execution['command_id']})")
        print(f"     Status: {execution['status']}")
        print(f"     Parâmetros: {execution['parameters']}")
        if execution['result']:
            print(f"     Resultado: {execution['result']['message']}")
    
    # Mostrar estatísticas
    stats = await executor.get_execution_stats("user123")
    
    print(f"\n📈 Estatísticas:")
    print(f"  Total de execuções: {stats['total_executions']}")
    print(f"  Execuções bem-sucedidas: {stats['successful_executions']}")
    print(f"  Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"  Execuções por categoria: {stats['category_stats']}")


async def example_8_security_validation():
    """Exemplo 8: Validação de segurança"""
    print("\n=== Exemplo 8: Validação de Segurança ===")
    
    validator = CommandValidator()
    
    # Simular permissões de usuário trader
    user_permissions = permission_manager.get_user_permissions(PermissionLevel.TRADER)
    
    # Testar comandos com diferentes níveis de segurança
    security_tests = [
        {
            "name": "Comando normal",
            "request": CommandRequest(
                command_id="show_position",
                parameters={"symbol": "PETR4"},
                user_id="user123"
            )
        },
        {
            "name": "Comando com símbolo inválido",
            "request": CommandRequest(
                command_id="show_position",
                parameters={"symbol": "INVALID"},
                user_id="user123"
            )
        },
        {
            "name": "Comando com parâmetros suspeitos",
            "request": CommandRequest(
                command_id="add_watchlist",
                parameters={"symbol": "PETR4; DROP TABLE users;"},
                user_id="user123"
            )
        }
    ]
    
    for test in security_tests:
        print(f"\n🔒 Teste: {test['name']}")
        
        is_valid, error_message, command = await validator.validate_command_request(
            test['request'], user_permissions, "user123"
        )
        
        if is_valid:
            print(f"  ✅ Válido: {command.name}")
        else:
            print(f"  ❌ Inválido: {error_message}")


async def main():
    """Função principal que executa todos os exemplos"""
    print("🚀 Sistema de Comandos Seguros - Exemplos de Uso")
    print("=" * 60)
    
    try:
        await example_1_basic_command_analysis()
        await example_2_command_execution()
        await example_3_confirmation_required()
        await example_4_permission_validation()
        await example_5_command_suggestions()
        await example_6_available_commands()
        await example_7_execution_history()
        await example_8_security_validation()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        logger.error("Erro ao executar exemplos", error=str(e))
        print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    asyncio.run(main())

