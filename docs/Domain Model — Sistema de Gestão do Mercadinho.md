# Domain Model — Sistema de Gestão do Mercadinho

Este documento descreve os conceitos fundamentais do domínio do Sistema de Gestão do Mercadinho e como eles se relacionam. Representa conceitos do negócio, não necessariamente tabelas do banco de dados.

## Visão geral dos relacionamentos

```text
Usuário (Operador / Gestor / Dono)
└── Operação
    ├── Produto
    │   └── Lote (validade)
    ├── Venda (PDV)
    │   └── Item de Venda
    ├── Movimentação de Estoque
    └── Alerta / Relatório
```

## Usuário

Representa a pessoa que interage com o sistema na loja, com permissões baseadas em seu papel operacional.

### Principais informações

- Nome.
- Papel ou cargo (Operador/Sobrinho, Gestora/Esposa, Dono/Sr. João).
- Permissões de acesso.

### Responsabilidade

Realizar ações no sistema de acordo com suas atribuições: cadastro e entradas (Operador), fechamento de caixa e relatórios (Gestora) ou consulta de alertas e dashboards estratégicos (Dono).

### Relacionamentos

Um usuário pode registrar vários produtos, movimentações de estoque e vendas.

## Produto

Representa uma mercadoria comercializada ou gerenciada pelo mercadinho.

### Principais informações

- Código de barras ou identificador.
- Nome do produto.
- Categoria.
- Preço de venda.
- Unidade de medida.
- Quantidade mínima para estoque baixo (regra de negócio).

### Responsabilidade

Manter o cadastro base das mercadorias vendidas na loja.

### Relacionamentos

- Um produto possui vários lotes de estoque.
- Um produto pode estar presente em vários itens de venda.
- Um produto pode ser associado a alertas de estoque baixo.

## Lote

Representa uma remessa específica de um produto recebida no estoque, com controle individual de validade.

### Principais informações

- Data de validade.
- Quantidade de itens no lote.
- Data de entrada ou recebimento.

### Responsabilidade

Garantir o rastreio e o controle de validade (FEFO — *First Expire, First Out*) para evitar perdas em perecíveis.

### Relacionamentos

- Um lote pertence a um único produto.
- Um lote pode gerar alertas de proximidade de vencimento.

## Venda (PDV)

Representa uma transação comercial realizada no balcão de atendimento da frente de caixa.

### Principais informações

- Data e horário da transação.
- Forma de pagamento (cartão, Pix ou dinheiro).
- Valor total.
- Status da venda (concluída ou cancelada).

### Responsabilidade

Registrar a compra do cliente, disparar a dedução automática do estoque em tempo real e gerar o comprovante de venda.

### Relacionamentos

- Uma venda é realizada por um usuário (operador).
- Uma venda contém um ou vários itens de venda.

## Item de Venda

Representa cada produto unitário ou quantidade de produto adicionada a uma venda.

### Principais informações

- Produto.
- Quantidade vendida.
- Preço unitário praticado.

### Responsabilidade

Vincular o produto à venda específica e calcular subtotais do atendimento.

### Relacionamentos

- Um item de venda pertence a uma única venda.
- Um item de venda está associado a um único produto.

## Movimentação de Estoque

Representa qualquer entrada, saída manual ou baixa automática que altera o saldo de produtos do mercado.

### Principais informações

- Tipo de movimentação (entrada por nota/compra, adição em massa, baixa automática de venda, avaria/perda).
- Quantidade.
- Data e hora da movimentação.

### Responsabilidade

Manter o saldo de estoque atualizado e confiável em tempo real.

### Relacionamentos

- Uma movimentação de estoque está associada a um produto ou lote.
- Uma movimentação pode ser disparada por uma venda no PDV.

## Alerta e Dashboard

Representa os avisos e indicadores consolidados em tempo real para tomada de decisões rápidas.

### Principais informações

- Tipo de alerta (estoque baixo, proximidade de vencimento em 5 ou 7 dias, anomalia de caixa).
- Mensagem e nível de prioridade.
- Relatórios consolidados (diário e semanal de vendas).

### Responsabilidade

Notificar problemas antes que gerem prejuízos (ruptura ou perda por validade) e fornecer visão financeira e operacional clara para os gestores.

### Relacionamentos

Um alerta se refere a um produto ou lote específico.

## Regras estruturais importantes

- Toda venda finalizada no PDV deve abater automaticamente o saldo do estoque no mesmo instante.
- O alerta de validade deve ser gerado prioritariamente para produtos perecíveis que estejam a 5 ou 7 dias do vencimento.
- O produto deve ser deduzido do estoque respeitando a ordem do lote com vencimento mais próximo (FEFO).
